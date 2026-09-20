"""
PDF Document Parser.

Extracts document structure (headings, paragraphs, tables) and
math expressions from .pdf files using:
  - PyMuPDF (fitz): Primary text extraction + font-based heading detection
  - pdfplumber: Fallback for complex tables
  - Heuristic math detection: LaTeX patterns, Unicode math symbols

Pipeline (per TDD Section 11.2):
  PDF file
    │
    ├─ PyMuPDF (fitz.open) → Extract text
    │     │
    │     ├─ Text found? → Parse structure (headings, paragraphs)
    │     │                  │
    │     │                  ├─ Detect inline math patterns → LaTeX
    │     │                  │
    │     │                  └─ Detect math images → [Mathpix API → LaTeX]  # not yet
    │     │
    │     └─ Text empty? → PDF scan detected → set ocr_used='pending_ocr'
    │                       (OCR via GCV + Mathpix handled by separate service)
    │
    └─ Send to AI Clarifier (Gemini) → narasi verbal  # handled by AI service

Design decisions:
  - Font size heuristics: title > heading1 > heading2 > body
  - Math detection: regex patterns for LaTeX, Unicode symbols, common notation
  - Scanned PDFs: flagged with ocr_used='pending_ocr', not failed
  - pdfplumber used as fallback for table extraction only
  - No network calls in this module (OCR is a separate concern)
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
import pdfplumber

from app.services.parsing.models import (
    BlockType,
    ContentBlock,
    MathExpressionResult,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


# ── Math Detection Patterns ───────────────────────────────────────────────────

# Inline LaTeX: $...$ or $$...$$
_LATEX_INLINE = re.compile(r"\$\$(.+?)\$\$|\$([^$\n]+?)\$", re.DOTALL)

# Display LaTeX environments
_LATEX_ENV = re.compile(
    r"\\begin\{(equation|align|math|gather|multline)\*?\}(.*?)\\end\{\1\*?\}",
    re.DOTALL,
)

# Common LaTeX commands that strongly indicate math
_LATEX_CMD = re.compile(
    r"\\(?:frac|sqrt|sum|int|prod|lim|infty|alpha|beta|gamma|delta|theta|"
    r"pi|sigma|omega|Omega|lambda|mu|nu|epsilon|phi|psi|chi|rho|tau|"
    r"partial|nabla|cdot|times|div|pm|mp|leq|geq|neq|approx|equiv|"
    r"forall|exists|in|subset|cup|cap|vec|hat|bar|tilde|dot|ddot|"
    r"overline|underline|overbrace|underbrace|left|right|binom|"
    r"mathbb|mathrm|mathbf|mathit|text)\b"
)

# Unicode math symbols (common in copied-from-Word PDFs)
_UNICODE_MATH = re.compile(
    r"[∑∫∏√∂∇∞±∓×÷·≤≥≠≈≡∈∉⊂⊃⊆⊇∪∩∅∀∃¬∧∨→←↔⇒⇐⇔"
    r"αβγδεζηθικλμνξπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    r"²³¹⁰⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]"
)

# Fraction notation: a/b where a,b are not purely alphabetical words
_FRACTION_PATTERN = re.compile(
    r"(?<![a-zA-Z/])(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)(?![a-zA-Z/])"
)

# Power notation: x^2, x^{n}, x^n
_POWER_PATTERN = re.compile(r"[a-zA-Z0-9]\^(?:\{[^}]+\}|[a-zA-Z0-9]+)")

# Common math expressions: equations with =
_EQUATION_PATTERN = re.compile(
    r"[a-zA-Z0-9\(\)\[\]]+\s*[+\-×÷*/]\s*[a-zA-Z0-9\(\)\[\]]+\s*=\s*[a-zA-Z0-9\(\)\[\]+-]+"
)

# Min score (number of matches) for a span to be considered "math"
_MATH_SCORE_THRESHOLD = 1


# ── Font Analysis Helpers ─────────────────────────────────────────────────────

@dataclass
class _SpanInfo:
    """Aggregated info about a text span in a PDF block."""
    text: str
    font_size: float
    is_bold: bool
    page_number: int


def _is_bold(flags: int) -> bool:
    """PyMuPDF font flags: bit 4 = bold."""
    return bool(flags & (1 << 4))


def _classify_heading_level(
    font_size: float,
    is_bold: bool,
    body_size: float,
    title_size: float,
) -> tuple[BlockType, int] | None:
    """
    Classify a span as a heading level based on font size relative to body.
    Returns (BlockType, level) or None if it's a body paragraph.
    """
    ratio = font_size / body_size if body_size > 0 else 1.0

    if font_size >= title_size * 0.95:
        return BlockType.HEADING1, 1
    if ratio >= 1.35 or (ratio >= 1.2 and is_bold):
        return BlockType.HEADING1, 1
    if ratio >= 1.15 or (ratio >= 1.05 and is_bold):
        return BlockType.HEADING2, 2
    if is_bold and ratio >= 1.0:
        return BlockType.HEADING3, 3
    return None  # body paragraph


# ── Math Score ────────────────────────────────────────────────────────────────

def _math_score(text: str) -> int:
    """
    Return a score indicating how likely text contains math notation.
    Higher = more likely to be a math expression.
    """
    score = 0
    score += len(_LATEX_INLINE.findall(text)) * 3
    score += len(_LATEX_ENV.findall(text)) * 3
    score += len(_LATEX_CMD.findall(text)) * 2
    score += len(_UNICODE_MATH.findall(text)) * 1
    score += len(_FRACTION_PATTERN.findall(text)) * 1
    score += len(_POWER_PATTERN.findall(text)) * 1
    score += len(_EQUATION_PATTERN.findall(text)) * 1
    return score


def _extract_math_spans(text: str) -> list[str]:
    """
    Extract individual math expressions from a text string.
    Returns list of raw math expression strings.
    """
    found: list[str] = []

    # $...$ and $$...$$
    for m in _LATEX_INLINE.finditer(text):
        found.append(m.group(1) or m.group(2))

    # \begin{equation}...\end{equation}
    for m in _LATEX_ENV.finditer(text):
        found.append(m.group(2).strip())

    # If nothing explicit found but text looks like math, treat whole thing
    if not found and _math_score(text) >= _MATH_SCORE_THRESHOLD:
        found.append(text.strip())

    return found


def _clean_latex(raw: str) -> str:
    """
    Light cleanup for extracted math strings.
    - Normalize whitespace
    - Remove leading/trailing $
    """
    text = raw.strip().strip("$").strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ── Main Parser ───────────────────────────────────────────────────────────────

class PdfParser:
    """
    Parses a .pdf file to extract structured content and math expressions.

    Handles:
    - Digital PDFs: text extraction via PyMuPDF, structure via font heuristics
    - Scanned PDFs: detected by empty text layer, flagged for OCR (ocr_used='pending_ocr')

    Usage:
        parser = PdfParser()
        result: ParsedDocument = parser.parse(file_path_or_bytes, title="...")
    """

    def parse(self, source: str | Path | bytes, title: str = "") -> ParsedDocument:
        """
        Parse a PDF file.

        Args:
            source: File path (str/Path) or raw bytes of the .pdf file.
            title:  Human-readable title (falls back to first detected heading).

        Returns:
            ParsedDocument. If scanned, ocr_used='pending_ocr' and content_blocks is empty.
        """
        try:
            if isinstance(source, (str, Path)):
                file_bytes = Path(source).read_bytes()
                if not title:
                    title = Path(source).stem
            else:
                file_bytes = source

            return self._parse_bytes(file_bytes, title)

        except Exception as exc:
            logger.error("PDF parsing failed: %s", exc, exc_info=True)
            return ParsedDocument(
                title=title or "Unknown",
                file_type="pdf",
                parse_error=str(exc),
            )

    def _parse_bytes(self, file_bytes: bytes, title: str) -> ParsedDocument:
        """Internal: parse raw PDF bytes."""
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        try:
            total_chars = sum(
                len(page.get_text("text").strip()) for page in doc
            )

            if total_chars < 50:
                # Scanned PDF — no meaningful text layer
                logger.info(
                    "PDF appears to be scanned (%d chars). Flagging for OCR.", total_chars
                )
                return ParsedDocument(
                    title=title or "Dokumen Scan",
                    file_type="pdf",
                    ocr_used="pending_ocr",
                    parse_error=None,
                    raw_structure={
                        "title": title,
                        "file_type": "pdf",
                        "ocr_used": "pending_ocr",
                        "page_count": doc.page_count,
                        "total_chars": total_chars,
                        "block_count": 0,
                        "math_count": 0,
                        "blocks": [],
                        "expressions": [],
                    },
                )

            # Digital PDF — extract and parse
            font_stats = self._collect_font_stats(doc)
            spans = self._extract_spans(doc)
            content_blocks, math_expressions = self._build_structure(
                spans, font_stats
            )

            # Fallback: try pdfplumber for tables if PyMuPDF found none
            table_blocks = [b for b in content_blocks if b.block_type == BlockType.TABLE]
            if not table_blocks:
                plumber_tables = self._extract_tables_pdfplumber(file_bytes, len(content_blocks))
                content_blocks.extend(plumber_tables)

            # Derive title from first H1 if not provided
            if not title:
                for blk in content_blocks:
                    if blk.block_type == BlockType.HEADING1:
                        title = blk.text.strip()
                        break

            parsed = ParsedDocument(
                title=title or "Dokumen PDF",
                file_type="pdf",
                content_blocks=content_blocks,
                math_expressions=math_expressions,
            )
            parsed.raw_structure = parsed.to_raw_structure()
            return parsed

        finally:
            doc.close()

    # ── Font Statistics ───────────────────────────────────────────────────────

    def _collect_font_stats(self, doc: fitz.Document) -> dict:
        """
        Collect font size statistics across all pages to establish:
        - body_size: the modal (most common) font size
        - title_size: the largest font size seen
        """
        size_counts: dict[float, int] = {}
        max_size = 0.0

        for page in doc:
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            for block in blocks:
                if block.get("type") != 0:  # 0 = text block
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = round(span.get("size", 12), 1)
                        size_counts[size] = size_counts.get(size, 0) + len(span.get("text", ""))
                        if size > max_size:
                            max_size = size

        if not size_counts:
            return {"body_size": 12.0, "title_size": 24.0}

        # Body = most frequent font size
        body_size = max(size_counts, key=lambda s: size_counts[s])
        return {
            "body_size": body_size,
            "title_size": max_size,
        }

    # ── Span Extraction ───────────────────────────────────────────────────────

    def _extract_spans(self, doc: fitz.Document) -> list[_SpanInfo]:
        """
        Extract all text spans from a PDF document in reading order.
        Each span preserves font size, bold status, and page number.
        """
        spans: list[_SpanInfo] = []

        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text(
                "dict",
                flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP,
            )["blocks"]

            for block in blocks:
                if block.get("type") != 0:
                    continue

                block_lines: list[str] = []
                block_size = 12.0
                block_bold = False

                for line in block.get("lines", []):
                    line_text_parts: list[str] = []
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        size = round(span.get("size", 12), 1)
                        bold = _is_bold(span.get("flags", 0))
                        line_text_parts.append(text)
                        block_size = size
                        block_bold = block_bold or bold

                    if line_text_parts:
                        block_lines.append(" ".join(line_text_parts))

                if block_lines:
                    full_text = " ".join(block_lines)
                    spans.append(_SpanInfo(
                        text=full_text,
                        font_size=block_size,
                        is_bold=block_bold,
                        page_number=page_num,
                    ))

        return spans

    # ── Structure Building ────────────────────────────────────────────────────

    def _build_structure(
        self,
        spans: list[_SpanInfo],
        font_stats: dict,
    ) -> tuple[list[ContentBlock], list[MathExpressionResult]]:
        """
        Convert spans into ContentBlocks and extract MathExpressionResults.
        Uses font size heuristics for heading detection.
        """
        content_blocks: list[ContentBlock] = []
        math_expressions: list[MathExpressionResult] = []
        math_counter = 0
        body_size = font_stats["body_size"]
        title_size = font_stats["title_size"]

        for block_idx, span in enumerate(spans):
            text = span.text.strip()
            if not text:
                continue

            # Detect if this block contains math
            score = _math_score(text)

            # Classify block type
            heading_result = _classify_heading_level(
                span.font_size, span.is_bold, body_size, title_size
            )

            if heading_result:
                block_type, level = heading_result
            else:
                block_type = BlockType.PARAGRAPH
                level = 0

            # Extract math from this span
            span_math: list[MathExpressionResult] = []
            if score >= _MATH_SCORE_THRESHOLD:
                raw_expressions = _extract_math_spans(text)
                for raw in raw_expressions:
                    cleaned = _clean_latex(raw)
                    if not cleaned:
                        continue
                    math_counter += 1
                    span_math.append(MathExpressionResult(
                        original_notation=raw,
                        latex_representation=cleaned,
                        position_order=math_counter,
                        block_index=block_idx,
                        conversion_confidence=self._estimate_confidence(cleaned),
                    ))
                    # Replace in text with placeholder
                    placeholder = f"{{{{MATH_{math_counter}}}}}"
                    text = text.replace(raw, f" {placeholder} ", 1)

            content_blocks.append(ContentBlock(
                block_type=block_type,
                text=text,
                level=level,
                index=block_idx,
            ))
            math_expressions.extend(span_math)

        return content_blocks, math_expressions

    # ── Table Extraction (pdfplumber fallback) ────────────────────────────────

    def _extract_tables_pdfplumber(
        self, file_bytes: bytes, block_offset: int
    ) -> list[ContentBlock]:
        """
        Extract tables using pdfplumber as fallback.
        Returns ContentBlock list for each table found.
        """
        table_blocks: list[ContentBlock] = []

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue
                        # Render as pipe-separated text
                        lines: list[str] = []
                        for row_idx, row in enumerate(table):
                            cells = [str(cell or "").strip() for cell in row]
                            lines.append(" | ".join(cells))
                            if row_idx == 0:
                                lines.append(" | ".join("---" for _ in row))

                        table_blocks.append(ContentBlock(
                            block_type=BlockType.TABLE,
                            text="\n".join(lines),
                            level=0,
                            index=block_offset + len(table_blocks),
                        ))

        except Exception as exc:
            logger.warning("pdfplumber table extraction failed: %s", exc)

        return table_blocks

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _estimate_confidence(self, latex: str) -> float:
        """
        Estimate confidence that extracted text is valid LaTeX math.
        Returns 0.0–1.0.
        """
        if not latex:
            return 0.0
        if "\\" in latex:
            # Has LaTeX commands — likely real math
            return 0.9
        if _UNICODE_MATH.search(latex):
            return 0.85
        if _FRACTION_PATTERN.search(latex) or _POWER_PATTERN.search(latex):
            return 0.8
        if _EQUATION_PATTERN.search(latex):
            return 0.75
        # Generic text that triggered math threshold — lower confidence
        return 0.6
