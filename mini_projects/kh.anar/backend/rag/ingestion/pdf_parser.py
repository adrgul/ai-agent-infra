"""PDF Parser for KB ingestion

Design rationale:
- SRP: Isolate PDF parsing logic; return structured data (text + metadata).
- OCP: Could extend to support other parsers (DOCX, HTML) by introducing an interface.
- Deterministic: Page-by-page extraction ensures consistent chunking anchors.

Why pypdf:
- Pure Python, no external dependencies (unlike pdfplumber or camelot).
- Sufficient for text extraction; works well with most PDFs.
- Lightweight and fast.

Metadata preservation:
- Capture page numbers for citation and context.
- Include PDF metadata (title, author) when available.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    logger.warning("pypdf not installed; PDF parsing disabled")
    PYPDF_AVAILABLE = False


class PDFParseResult:
    """Structured result from PDF parsing.
    
    Why a class: encapsulates parsed data + metadata; easier to extend.
    """
    def __init__(self, text: str, pages: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.text = text  # Full text concatenated
        self.pages = pages  # List of {page_num, text}
        self.metadata = metadata  # PDF metadata (title, author, etc.)


def parse_pdf(file_path: Path) -> PDFParseResult:
    """Parse a PDF file and extract text + metadata.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        PDFParseResult with text, page-level data, and PDF metadata
    
    Raises:
        RuntimeError: If pypdf is not available
        Exception: If PDF cannot be parsed
    
    Design notes:
    - Page-by-page extraction allows page-aware chunking.
    - Metadata extraction enables richer context for retrieval.
    """
    if not PYPDF_AVAILABLE:
        raise RuntimeError("pypdf not available; install via: pip install pypdf")
    
    try:
        reader = PdfReader(str(file_path))
        
        # Extract PDF metadata
        pdf_metadata = {}
        if reader.metadata:
            pdf_metadata = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
            }
        
        # Extract text page by page
        pages = []
        all_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            pages.append({
                "page_num": i + 1,  # 1-indexed for human readability
                "text": page_text,
            })
            all_text.append(page_text)
        
        full_text = "\n".join(all_text)
        
        logger.info(f"Parsed PDF {file_path.name}: {len(reader.pages)} pages, {len(full_text)} chars")
        
        return PDFParseResult(
            text=full_text,
            pages=pages,
            metadata=pdf_metadata,
        )
    
    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        raise
