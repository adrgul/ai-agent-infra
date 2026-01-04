import os
import re
from typing import List, Dict
from pathlib import Path

class MarkdownRAGChunker:
    """
    A production-ready chunking system for markdown documents in RAG pipelines.

    Features:
    - Header-aware chunking (respects markdown structure)
    - Configurable chunk size and overlap
    - Metadata preservation (headers, source files)
    - Smart paragraph-based splitting
    - Overlap for context continuity

    Example:
        >>> chunker = MarkdownRAGChunker(chunk_size=800, overlap=150)
        >>> chunks = chunker.process_documents(['doc1.md', 'doc2.md'])
        >>> print(f"Created {len(chunks)} chunks")
    """

    def __init__(self, chunk_size: int = 800, overlap: int = 150):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target maximum characters per chunk (default: 800)
            overlap: Characters to overlap between chunks (default: 150)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_markdown(self, filepath: str) -> str:
        """
        Load a markdown file.

        Args:
            filepath: Path to the markdown file

        Returns:
            String content of the file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def chunk_document(self, text: str, filepath: str) -> List[Dict]:
        """
        Chunk a markdown document while preserving structure.

        Args:
            text: Markdown content
            source_file: Source filename for metadata

        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = []

        # Split by headers (H1 and H2 are major section boundaries)
        sections = re.split(r'(^#{1,2}\s+.+$)', text, flags=re.MULTILINE)

        current_section = ""
        current_header = ""
        current_h1 = ""

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # Check if this is a header
            header_match = re.match(r'^(#{1,2})\s+(.+)$', section.strip())

            if header_match:
                # Process previous section if it exists
                if current_section:
                    chunks.extend(
                        self._split_section(
                            current_section,
                            current_header,
                            current_h1,
                            f"{filepath}_{i}"
                        )
                    )

                # Start new section
                level = len(header_match.group(1))
                header_text = header_match.group(2)

                if level == 1:
                    current_h1 = header_text
                    current_header = header_text
                else:  # level == 2
                    current_header = header_text

                current_section = section + "\n\n"
            else:
                current_section += section

        # Process final section
        if current_section:
            chunks.extend(
                self._split_section(
                    current_section,
                    current_header,
                    current_h1,
                    f"{filepath}_{i}"
                )
            )
        print(f"Generated {len(chunks)} chunks from document {filepath}")

        return chunks

    def _split_section(
        self,
        text: str,
        header: str,
        h1: str,
        id: str
    ) -> List[Dict]:
        """
        Split a section into appropriately-sized chunks.

        Args:
            text: Section text
            header: Current section header
            h1: Top-level (H1) header
            source: Source filename

        Returns:
            List of chunk dictionaries
        """
        chunks = []

        # If section is small enough, return as single chunk
        if len(text) <= self.chunk_size:
            return [{
                'text': text.strip(),
                'header': header,
                'h1': h1,
                'id': id,
                'metadata': {
                    'section_path': f"{h1} > {header}" if h1 != header else h1
                }
            }]

        # Split by paragraphs (double newlines)
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        current_chunk = ""

        for para in paragraphs:
            # Calculate potential new size
            potential_size = len(current_chunk) + len(para)

            # If adding this paragraph exceeds chunk size and we have content
            if potential_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'header': header,
                    'h1': h1,
                    'id': id,
                    'metadata': {
                        'section_path': f"{h1} > {header}" if h1 != header else h1
                    }
                })

                # Start new chunk with overlap
                # Take last 'overlap' characters from previous chunk
                if len(current_chunk) > self.overlap:
                    overlap_text = current_chunk[-self.overlap:]
                    # Try to start overlap at a word boundary
                    space_idx = overlap_text.find(' ')
                    if space_idx != -1:
                        overlap_text = overlap_text[space_idx+1:]
                else:
                    overlap_text = current_chunk

                current_chunk = overlap_text + "\n\n" + para + "\n\n"
            else:
                current_chunk += para + "\n\n"

        # Add final chunk if there's content
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'header': header,
                'h1': h1,
                'id': id,
                'metadata': {
                    'section_path': f"{h1} > {header}" if h1 != header else h1
                }
            })

        return chunks

    def process_documents(self, filepaths: List[str]) -> List[Dict]:
        """
        Process multiple markdown documents.

        Args:
            filepaths: List of paths to markdown files

        Returns:
            List of all chunks from all documents with unique IDs
        """
        all_chunks = []

        for filepath in filepaths:
            all_chunks.extend(self.process_file(filepath))

        return all_chunks

    def process_file(self, filepath: str) -> List[Dict]:
        try:
            text = self.load_markdown(filepath)
            print(f"✓ Loaded {os.path.basename(filepath)}")
            return self.chunk_document(text, Path(filepath).name)

        except Exception as e:
            print(f"✗ Error processing {filepath}: {e}")
            return []
