"""Document chunking implementation using tiktoken."""

from typing import List
import tiktoken

from domain.interfaces import Chunker


class TiktokenChunker(Chunker):
    """Chunker using tiktoken for token-based splitting."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding = tiktoken.get_encoding(encoding_name)

    def chunk_text(
        self, text: str, chunk_size_tokens: int = 900,
        overlap_tokens: int = 150
    ) -> List[str]:
        """Split text into chunks based on token count."""
        tokens = self.encoding.encode(text)
        chunks = []

        i = 0
        while i < len(tokens):
            # Take chunk_size_tokens
            chunk_tokens = tokens[i : i + chunk_size_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move forward by (chunk_size - overlap)
            i += chunk_size_tokens - overlap_tokens

        return chunks
