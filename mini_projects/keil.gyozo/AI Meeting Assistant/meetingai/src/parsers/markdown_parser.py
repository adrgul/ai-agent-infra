"""
Markdown document parser
"""

import logging
import re
from pathlib import Path

import markdown
from langchain.schema import Document

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Parser for Markdown files"""

    def __init__(self):
        super().__init__()
        self.supported_extensions = ["md", "markdown"]

    def parse(self, file_path: str) -> Document:
        """
        Parse a Markdown file

        Args:
            file_path: Path to the Markdown file

        Returns:
            LangChain Document object
        """
        try:
            path = Path(file_path)

            # Read file content
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract structured information
            title = self._extract_title(content)
            headers = self._extract_headers(content)
            links = self._extract_links(content)

            # Convert to plain text (remove markdown formatting)
            plain_text = self._markdown_to_text(content)

            # Clean the text
            cleaned_content = self._clean_text(plain_text)

            # Extract metadata
            metadata = self.extract_metadata(file_path)
            metadata.update({
                "parser": "MarkdownParser",
                "content_type": "text/markdown",
                "title": title,
                "headers": headers,
                "links": links,
                "word_count": len(cleaned_content.split()),
                "line_count": len(cleaned_content.split('\n')),
            })

            logger.info(f"Successfully parsed Markdown file: {file_path}")

            return Document(
                page_content=cleaned_content,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to parse Markdown file {file_path}: {str(e)}")
            raise RuntimeError(f"Markdown parsing failed: {str(e)}")

    def _extract_title(self, content: str) -> str:
        """Extract title from Markdown content"""
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith('# '):
                return line[2:].strip()
        return ""

    def _extract_headers(self, content: str) -> list:
        """Extract headers from Markdown content"""
        headers = []
        lines = content.split('\n')
        for line in lines:
            if re.match(r'^#{1,6}\s+', line):
                headers.append(line.strip())
        return headers

    def _extract_links(self, content: str) -> list:
        """Extract links from Markdown content"""
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)
        return [match[1] for match in matches]

    def _markdown_to_text(self, content: str) -> str:
        """Convert Markdown to plain text"""
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '', content)
        content = re.sub(r'`[^`]*`', '', content)

        # Remove headers markers
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)

        # Remove link formatting
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # Remove emphasis
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)

        # Remove lists markers
        content = re.sub(r'^[\s]*[-\*\+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)

        return content