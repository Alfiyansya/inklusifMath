"""
Unit tests for DOCX parsing pipeline.

Tests:
  - OMML → LaTeX converter (omml_to_latex.py)
  - DOCX parser with synthetic fixtures (docx_parser.py)
  - Edge cases: empty docs, no math, math-only, nested structures
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET

import pytest
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from app.services.parsing.omml_to_latex import omml_element_to_latex, omml_xml_to_latex
from app.services.parsing.models import BlockType, ParsedDocument
from app.services.parsing.docx_parser import DocxParser

# ── Helpers ──────────────────────────────────────────────────────────────────

_MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _omml(xml_body: str) -> str:
    """Wrap OMML body in a proper <m:oMath> root element."""
    return (
        f'<m:oMath xmlns:m="{_MATH_NS}">'
        f"{xml_body}"
        f"</m:oMath>"
    )


def _make_docx(paragraphs: list[dict]) -> bytes:
    """
    Create an in-memory .docx with the given paragraphs.

    Each paragraph dict:
        {"text": str, "style": str}  — style e.g. "Normal", "Heading 1"
    """
    doc = docx.Document()
    # Remove default empty paragraph
    for para in list(doc.paragraphs):
        p = para._element
        p.getparent().remove(p)

    for info in paragraphs:
        style = info.get("style", "Normal")
        text = info.get("text", "")
        doc.add_paragraph(text, style=style)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── OMML → LaTeX Tests ───────────────────────────────────────────────────────

class TestOmmlToLatex:
    """Tests for the OMML-to-LaTeX converter."""

    def test_simple_text(self):
        xml = _omml('<m:r><m:t>x</m:t></m:r>')
        result = omml_xml_to_latex(xml)
        assert result == "x"

    def test_fraction(self):
        xml = _omml(
            "<m:f>"
            "  <m:num><m:r><m:t>a</m:t></m:r></m:num>"
            "  <m:den><m:r><m:t>b</m:t></m:r></m:den>"
            "</m:f>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"\frac{a}{b}"

    def test_fraction_numeric(self):
        xml = _omml(
            "<m:f>"
            "  <m:num><m:r><m:t>1</m:t></m:r></m:num>"
            "  <m:den><m:r><m:t>2</m:t></m:r></m:den>"
            "</m:f>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"\frac{1}{2}"

    def test_superscript(self):
        xml = _omml(
            "<m:sSup>"
            "  <m:e><m:r><m:t>x</m:t></m:r></m:e>"
            "  <m:sup><m:r><m:t>2</m:t></m:r></m:sup>"
            "</m:sSup>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"x^{2}"

    def test_subscript(self):
        xml = _omml(
            "<m:sSub>"
            "  <m:e><m:r><m:t>a</m:t></m:r></m:e>"
            "  <m:sub><m:r><m:t>n</m:t></m:r></m:sub>"
            "</m:sSub>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"a_{n}"

    def test_square_root(self):
        xml = _omml(
            "<m:rad>"
            "  <m:radPr><m:degHide m:val='1'/></m:radPr>"
            "  <m:deg/>"
            "  <m:e><m:r><m:t>x</m:t></m:r></m:e>"
            "</m:rad>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"\sqrt{x}"

    def test_nth_root(self):
        xml = _omml(
            "<m:rad>"
            "  <m:deg><m:r><m:t>3</m:t></m:r></m:deg>"
            "  <m:e><m:r><m:t>8</m:t></m:r></m:e>"
            "</m:rad>"
        )
        result = omml_xml_to_latex(xml)
        assert r"\sqrt[3]{8}" == result

    def test_delimiter_parentheses(self):
        xml = _omml(
            "<m:d>"
            "  <m:dPr>"
            '    <m:begChr m:val="("/>'
            '    <m:endChr m:val=")"/>'
            "  </m:dPr>"
            "  <m:e><m:r><m:t>x+1</m:t></m:r></m:e>"
            "</m:d>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"\left(x+1\right)"

    def test_symbol_mapping_pi(self):
        xml = _omml('<m:r><m:t>π</m:t></m:r>')
        result = omml_xml_to_latex(xml)
        assert result == r"\pi"

    def test_symbol_mapping_times(self):
        xml = _omml('<m:r><m:t>×</m:t></m:r>')
        result = omml_xml_to_latex(xml)
        assert result == r"\times"

    def test_nested_fraction_with_superscript(self):
        """Test: (x²) / (y³)"""
        xml = _omml(
            "<m:f>"
            "  <m:num>"
            "    <m:sSup>"
            "      <m:e><m:r><m:t>x</m:t></m:r></m:e>"
            "      <m:sup><m:r><m:t>2</m:t></m:r></m:sup>"
            "    </m:sSup>"
            "  </m:num>"
            "  <m:den>"
            "    <m:sSup>"
            "      <m:e><m:r><m:t>y</m:t></m:r></m:e>"
            "      <m:sup><m:r><m:t>3</m:t></m:r></m:sup>"
            "    </m:sSup>"
            "  </m:den>"
            "</m:f>"
        )
        result = omml_xml_to_latex(xml)
        assert result == r"\frac{x^{2}}{y^{3}}"

    def test_invalid_xml_returns_empty(self):
        result = omml_xml_to_latex("<bad xml>")
        assert result == ""

    def test_empty_math_element(self):
        xml = _omml("")
        result = omml_xml_to_latex(xml)
        assert result == ""

    def test_summation_nary(self):
        xml = _omml(
            "<m:nary>"
            "  <m:naryPr><m:chr m:val='∑'/></m:naryPr>"
            "  <m:sub><m:r><m:t>i=1</m:t></m:r></m:sub>"
            "  <m:sup><m:r><m:t>n</m:t></m:r></m:sup>"
            "  <m:e><m:r><m:t>i</m:t></m:r></m:e>"
            "</m:nary>"
        )
        result = omml_xml_to_latex(xml)
        assert r"\sum_{" in result
        assert "i=1" in result
        assert "n" in result


# ── DocxParser Tests ─────────────────────────────────────────────────────────

class TestDocxParser:
    """Tests for the main DocxParser."""

    def setup_method(self):
        self.parser = DocxParser()

    def test_empty_document(self):
        doc_bytes = _make_docx([])
        result = self.parser.parse(doc_bytes, title="Empty")
        assert isinstance(result, ParsedDocument)
        assert result.file_type == "docx"
        assert result.title == "Empty"
        assert result.parse_error is None

    def test_simple_paragraph(self):
        doc_bytes = _make_docx([
            {"text": "Ini adalah paragraf biasa.", "style": "Normal"},
        ])
        result = self.parser.parse(doc_bytes, title="Test")
        assert len(result.content_blocks) == 1
        assert result.content_blocks[0].block_type == BlockType.PARAGRAPH
        assert "paragraf biasa" in result.content_blocks[0].text

    def test_heading_detection(self):
        doc_bytes = _make_docx([
            {"text": "Bab 1: Bilangan Bulat", "style": "Heading 1"},
            {"text": "Pengantar", "style": "Heading 2"},
            {"text": "Bilangan bulat adalah...", "style": "Normal"},
        ])
        result = self.parser.parse(doc_bytes, title="Test")
        assert result.content_blocks[0].block_type == BlockType.HEADING1
        assert result.content_blocks[1].block_type == BlockType.HEADING2
        assert result.content_blocks[2].block_type == BlockType.PARAGRAPH

    def test_heading_level_values(self):
        doc_bytes = _make_docx([
            {"text": "H1", "style": "Heading 1"},
            {"text": "H2", "style": "Heading 2"},
            {"text": "H3", "style": "Heading 3"},
        ])
        result = self.parser.parse(doc_bytes, title="Test")
        assert result.content_blocks[0].level == 1
        assert result.content_blocks[1].level == 2
        assert result.content_blocks[2].level == 3

    def test_no_math_document(self):
        doc_bytes = _make_docx([
            {"text": "Halo, ini dokumen tanpa matematika.", "style": "Normal"},
        ])
        result = self.parser.parse(doc_bytes, title="No Math")
        assert result.has_math is False
        assert result.math_count == 0
        assert result.parse_error is None

    def test_parse_from_bytes(self):
        doc_bytes = _make_docx([{"text": "Test dari bytes", "style": "Normal"}])
        result = self.parser.parse(doc_bytes, title="Bytes Test")
        assert result.title == "Bytes Test"
        assert len(result.content_blocks) >= 1

    def test_raw_structure_serialization(self):
        doc_bytes = _make_docx([
            {"text": "Bab 1", "style": "Heading 1"},
            {"text": "Isi paragraf.", "style": "Normal"},
        ])
        result = self.parser.parse(doc_bytes, title="Structure Test")
        raw = result.raw_structure
        assert "blocks" in raw
        assert "math_count" in raw
        assert raw["file_type"] == "docx"
        assert raw["block_count"] >= 1

    def test_invalid_bytes_returns_error(self):
        result = self.parser.parse(b"not a valid docx file", title="Bad File")
        assert result.parse_error is not None
        assert result.file_type == "docx"

    def test_multiple_paragraphs_order(self):
        paragraphs = [
            {"text": f"Paragraf {i}", "style": "Normal"}
            for i in range(5)
        ]
        doc_bytes = _make_docx(paragraphs)
        result = self.parser.parse(doc_bytes, title="Order Test")
        assert len(result.content_blocks) == 5
        for i, block in enumerate(result.content_blocks):
            assert str(i) in block.text

    def test_table_extraction(self):
        """Test that tables in .docx are extracted as TABLE blocks."""
        doc = docx.Document()
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Nama"
        table.cell(0, 1).text = "Nilai"
        table.cell(1, 0).text = "Ani"
        table.cell(1, 1).text = "85"
        buf = io.BytesIO()
        doc.save(buf)
        doc_bytes = buf.getvalue()

        result = self.parser.parse(doc_bytes, title="Table Test")
        table_blocks = [b for b in result.content_blocks if b.block_type == BlockType.TABLE]
        assert len(table_blocks) == 1
        assert "Nama" in table_blocks[0].text
        assert "Nilai" in table_blocks[0].text


# ── Integration: ParsedDocument ───────────────────────────────────────────────

class TestParsedDocumentModel:
    """Tests for the ParsedDocument dataclass."""

    def test_has_math_false_when_empty(self):
        doc = ParsedDocument(title="Test", file_type="docx")
        assert doc.has_math is False
        assert doc.math_count == 0

    def test_to_raw_structure_keys(self):
        doc = ParsedDocument(title="Test", file_type="docx")
        raw = doc.to_raw_structure()
        assert set(raw.keys()) == {
            "title", "file_type", "block_count", "math_count",
            "ocr_used", "blocks", "expressions"
        }

    def test_ocr_used_default(self):
        doc = ParsedDocument(title="Test", file_type="docx")
        assert doc.ocr_used == "none"
