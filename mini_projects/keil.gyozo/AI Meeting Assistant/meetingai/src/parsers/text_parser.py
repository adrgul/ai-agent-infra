"""
Plain text document parser
"""

import logging
from pathlib import Path

from langchain.schema import Document

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """Parser for plain text files"""

    def __init__(self):
        super().__init__()
        self.supported_extensions = ["txt"]

    def parse(self, file_path: str) -> Document:
        """
        Parse a plain text file

        Args:
            file_path: Path to the text file

        Returns:
            LangChain Document object
        """
        try:
            path = Path(file_path)

            # Read file content
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Clean the text
            cleaned_content = self._clean_text(content)

            # Extract metadata
            metadata = self.extract_metadata(file_path)
            metadata.update({
                "parser": "TextParser",
                "content_type": "text/plain",
                "word_count": len(cleaned_content.split()),
                "line_count": len(cleaned_content.split('\n')),
            })

            logger.info(f"Successfully parsed text file: {file_path}")

            return Document(
                page_content=cleaned_content,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {str(e)}")
            raise RuntimeError(f"Text parsing failed: {str(e)}")