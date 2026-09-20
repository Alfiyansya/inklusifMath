"""
Document parsing services.

Exports:
    DocxParser     — Parse .docx files (python-docx + OMML extraction)
    PdfParser      — Parse .pdf files (PyMuPDF + pdfplumber table fallback)
    ParsedDocument — Result dataclass returned by parsers
    ContentBlock   — Single block of content
    MathExpressionResult — Single extracted math expression
"""

from app.services.parsing.docx_parser import DocxParser
from app.services.parsing.pdf_parser import PdfParser
from app.services.parsing.models import (
    BlockType,
    ContentBlock,
    MathExpressionResult,
    ParsedDocument,
)

__all__ = [
    "DocxParser",
    "PdfParser",
    "ParsedDocument",
    "ContentBlock",
    "MathExpressionResult",
    "BlockType",
]
