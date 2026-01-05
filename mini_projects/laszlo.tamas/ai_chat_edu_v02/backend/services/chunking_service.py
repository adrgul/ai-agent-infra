"""Document chunking service using LangChain text splitters."""

import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)

# Character approximation
CHAR_PER_TOKEN = 4  # rough approximation: 1 token ≈ 4 characters


class ChunkingService:
    """Service for splitting documents into chunks."""
    
    def __init__(self):
        from services.config_service import get_config_service
        
        # Load from system.ini
        config = get_config_service()
        self.chunk_size = config.get_chunk_size_tokens()
        self.chunk_overlap = config.get_chunk_overlap_tokens()
        
        self.repository = DocumentChunkRepository()
        
        # Initialize RecursiveCharacterTextSplitter
        # Convert token size to character size (rough approximation)
        chunk_size_chars = self.chunk_size * CHAR_PER_TOKEN
        chunk_overlap_chars = self.chunk_overlap * CHAR_PER_TOKEN
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size_chars,
            chunk_overlap=chunk_overlap_chars,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(
            f"ChunkingService initialized: "
            f"chunk_size={chunk_size_chars} chars (~{self.chunk_size} tokens), "
            f"overlap={chunk_overlap_chars} chars (~{self.chunk_overlap} tokens)"
        )
    
    def chunk_document(
        self,
        document_id: int,
        tenant_id: int,
        content: str,
        source_title: str
    ) -> List[int]:
        """
        Split document content into chunks and store in database.
        
        Args:
            document_id: Document identifier (FK to documents.id)
            tenant_id: Tenant identifier
            content: Full document text content
            source_title: Document title for metadata
        
        Returns:
            List of created chunk IDs
        
        Raises:
            ValueError: If content is empty
        """
        if not content or not content.strip():
            raise ValueError("Document content is empty")
        
        logger.info(f"Chunking document_id={document_id}, content_length={len(content)} chars")
        
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(content)
        
        logger.info(f"Created {len(text_chunks)} chunks")
        
        # Calculate offsets and prepare chunk data
        chunks_data = []
        current_offset = 0
        
        for idx, chunk_text in enumerate(text_chunks):
            # Find chunk position in original text
            # Note: This is approximate due to overlap handling
            start_offset = content.find(chunk_text, current_offset)
            
            if start_offset == -1:
                # Fallback: use current offset
                start_offset = current_offset
            
            end_offset = start_offset + len(chunk_text)
            
            chunks_data.append({
                "chunk_index": idx,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "content": chunk_text,
                "source_title": source_title
            })
            
            # Move offset for next chunk
            current_offset = start_offset + len(chunk_text)
        
        # Insert chunks into database
        chunk_ids = self.repository.insert_chunks(
            tenant_id=tenant_id,
            document_id=document_id,
            chunks=chunks_data
        )
        
        logger.info(
            f"Document {document_id} chunked: {len(chunk_ids)} chunks, "
            f"avg_length={sum(len(c['content']) for c in chunks_data) / len(chunks_data):.0f} chars"
        )
        
        return chunk_ids
    
    def get_document_chunks(self, document_id: int) -> List[dict]:
        """
        Retrieve all chunks for a document.
        
        Args:
            document_id: Document identifier
        
        Returns:
            List of chunk dictionaries
        """
        return self.repository.get_chunks_by_document(document_id)
