"""Document Loader - Markdown files chunking"""

import os
import logging
from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from domain.interfaces import DocumentLoaderInterface
from domain.models import DocumentChunk

logger = logging.getLogger(__name__)


class MarkdownDocumentLoader(DocumentLoaderInterface):
    """Markdown dokumentum betöltő chunking-gal"""
    
    def __init__(self):
        # Chunking konfiguráció
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # Text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"Document loader inicializálva - chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def load_documents(self, directory: str, domain: str) -> List[DocumentChunk]:
        """Dokumentumok betöltése egy domain mappából"""
        
        doc_path = Path(directory)
        
        if not doc_path.exists():
            logger.warning(f"Mappa nem létezik: {directory}")
            return []
        
        all_chunks = []
        md_files = list(doc_path.glob("*.md"))
        
        logger.info(f"Dokumentumok betöltése: {domain} domain ({len(md_files)} fájl)")
        
        for md_file in md_files:
            try:
                chunks = self._load_single_file(md_file, domain)
                all_chunks.extend(chunks)
                logger.debug(f"  ✓ {md_file.name}: {len(chunks)} chunk")
            except Exception as e:
                logger.error(f"  ✗ {md_file.name}: {e}")
        
        logger.info(f"✓ {domain}: {len(all_chunks)} chunk összesen")
        return all_chunks
    
    def _load_single_file(self, file_path: Path, domain: str) -> List[DocumentChunk]:
        """Egy fájl betöltése és chunkolása"""
        
        # Fájl beolvasása
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chunkolás
        text_chunks = self.splitter.split_text(content)
        
        # DocumentChunk objektumok létrehozása
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                domain=domain,
                source=file_path.name,
                chunk_id=i,
                metadata={
                    "file_path": str(file_path),
                    "total_chunks": len(text_chunks)
                }
            )
            chunks.append(chunk)
        
        return chunks

