"""
Data models for the document parsing pipeline output.
These are plain Python dataclasses — no ORM dependency.
They are converted to SQLAlchemy models in the service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BlockType(str, Enum):
    HEADING1 = "heading1"
    HEADING2 = "heading2"
    HEADING3 = "heading3"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    MATH_INLINE = "math_inline"   # inline math inside a paragraph
    MATH_BLOCK = "math_block"     # standalone math expression (display)


@dataclass
class MathExpressionResult:
    """A single extracted math expression."""
    original_notation: str      # raw text as it appeared in the document
    latex_representation: str   # converted LaTeX (may be empty if conversion failed)
    position_order: int         # 1-based order within the document
    block_index: int            # which content block this belongs to
    conversion_confidence: float = 1.0  # 0.0–1.0, lower = needs human review


@dataclass
class ContentBlock:
    """A single block of content (heading, paragraph, table, etc.)."""
    block_type: BlockType
    text: str               # plain text content (math placeholders: {{MATH_1}})
    level: int = 0          # heading level (1–3), 0 for non-headings
    index: int = 0          # block order within document


@dataclass
class ParsedDocument:
    """
    Complete parsing result for a DOCX or PDF document.
    Produced by DocxParser or PdfParser, consumed by the AI service.
    """
    title: str
    file_type: str                          # 'docx' | 'pdf'
    content_blocks: list[ContentBlock] = field(default_factory=list)
    math_expressions: list[MathExpressionResult] = field(default_factory=list)
    raw_structure: dict = field(default_factory=dict)  # stored as JSONB in DB
    parse_error: str | None = None           # set if parsing partially failed
    ocr_used: str = "none"                  # 'none' | 'gcv' | 'mathpix'

    @property
    def has_math(self) -> bool:
        return len(self.math_expressions) > 0

    @property
    def math_count(self) -> int:
        return len(self.math_expressions)

    def to_raw_structure(self) -> dict:
        """Serialize to JSONB-friendly dict for DB storage."""
        return {
            "title": self.title,
            "file_type": self.file_type,
            "block_count": len(self.content_blocks),
            "math_count": self.math_count,
            "ocr_used": self.ocr_used,
            "blocks": [
                {
                    "type": b.block_type.value,
                    "text": b.text[:500],  # truncate for JSONB storage
                    "level": b.level,
                    "index": b.index,
                }
                for b in self.content_blocks
            ],
            "expressions": [
                {
                    "original_notation": e.original_notation,
                    "latex": e.latex_representation,
                    "position_order": e.position_order,
                    "confidence": e.conversion_confidence,
                }
                for e in self.math_expressions
            ],
        }
