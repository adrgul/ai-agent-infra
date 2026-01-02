"""Document text extractors."""

import os
from abc import ABC, abstractmethod

from domain.interfaces import DocumentTextExtractor


class MarkdownExtractor(DocumentTextExtractor):
    """Extract text from Markdown files."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from a .md file."""
        if not file_path.lower().endswith(".md"):
            raise ValueError(f"Expected .md file, got {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


class PDFExtractor(DocumentTextExtractor):
    """Extract text from PDF files."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from a .pdf file."""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")

        if not file_path.lower().endswith(".pdf"):
            raise ValueError(f"Expected .pdf file, got {file_path}")

        text = []
        try:
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")


class DocxExtractor(DocumentTextExtractor):
    """Extract text from DOCX files."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from a .docx file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")

        if not file_path.lower().endswith(".docx"):
            raise ValueError(f"Expected .docx file, got {file_path}")

        text = []
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text.append(para.text)
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


def get_extractor(filename: str) -> DocumentTextExtractor:
    """Get appropriate extractor based on file extension."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".md":
        return MarkdownExtractor()
    elif ext == ".pdf":
        return PDFExtractor()
    elif ext == ".docx":
        return DocxExtractor()
    else:
        raise ValueError(f"Unsupported file type: {ext}")
