"""
Base parser class for document parsing
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from langchain.schema import Document


class BaseParser(ABC):
    """Abstract base class for document parsers"""

    def __init__(self):
        self.supported_extensions = []

    @abstractmethod
    def parse(self, file_path: str) -> Document:
        """
        Parse a document file

        Args:
            file_path: Path to the document file

        Returns:
            LangChain Document object
        """
        pass

    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the file

        Args:
            file_path: Path to the file

        Returns:
            True if this parser can handle the file
        """
        path = Path(file_path)
        return path.suffix.lower().lstrip('.') in self.supported_extensions

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from file

        Args:
            file_path: Path to the file

        Returns:
            Metadata dictionary
        """
        path = Path(file_path)
        stat = path.stat()

        return {
            "file_path": str(path),
            "file_name": path.name,
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "extension": path.suffix,
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        return text.strip()