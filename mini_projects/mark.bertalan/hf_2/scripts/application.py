"""
Orchestrator for embedding-based query processing.

This module coordinates embedding generation and vector storage operations
while adhering to dependency inversion principles through abstract interfaces.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from scripts.interfaces import Embedder, VectorDB


class EmbeddingApp:
    """
    Manages the complete workflow for text query processing using embeddings.

    Responsibilities:
    - Coordinate embedding generation through injected services
    - Manage vector storage operations
    - Execute similarity searches across multiple algorithms

    Architecture follows the Open/Closed Principle: extensible through
    different implementations of Embedder and VectorDB without
    modifying this orchestrator.
    """

    def __init__(self, embedding_service: Embedder, vector_store: VectorDB):
        """
        Construct processor with dependency-injected components.

        Args:
            embedding_service: Component responsible for text-to-vector transformation
            vector_store: Component handling vector persistence and retrieval
        """
        self._embedder = embedding_service
        self._vector_db = vector_store

    def _parse_domains_config(self) -> List[str]:
        """
        Extract domain list from environment configuration.

        Returns:
            List of domain identifiers from DOMAINS env variable
        """
        domains_config = os.getenv("DOMAINS", "hr,dev,support,management")
        return [domain.strip() for domain in domains_config.split(",") if domain.strip()]

    def _normalize_markdown_content(self, content: str) -> str:
        """
        Clean and normalize markdown text for processing.

        Args:
            content: Raw markdown string

        Returns:
            Normalized text with consolidated whitespace
        """
        return re.sub(r"\s+\n", "\n", content).strip()

    def _load_domain_documents(self, base_path: Path, domain: str) -> List[str]:
        """
        Load all markdown documents from a specific domain directory.

        Args:
            base_path: Root directory containing domain folders
            domain: Domain identifier

        Returns:
            List of markdown file contents
        """
        domain_path = base_path / domain
        if not domain_path.exists():
            return []

        documents = []
        for markdown_file in sorted(domain_path.glob("*.md")):
            raw_content = markdown_file.read_text(encoding="utf-8", errors="ignore")
            normalized = self._normalize_markdown_content(raw_content)
            documents.append(normalized)

        return documents

    def _store_document(self, document_text: str, source_doc_id: str, domain: str) -> None:
        """
        Generate embeddings for document chunks and persist to vector store.

        Args:
            document_text: Preprocessed document content
            source_doc_id: ID of the source document (for tracking chunks)
            domain: Domain name (e.g., 'hr', 'dev')
        """
        # Get list of (chunk_text, embedding_vector) tuples
        chunk_embeddings = self._embedder.get_embedding(document_text)

        # Store each chunk separately with metadata
        for chunk_idx, (chunk_text, embedding_vector) in enumerate(chunk_embeddings):
            chunk_id = f"{source_doc_id}_chunk_{chunk_idx}"
            metadata = {
                "source_document_id": source_doc_id,
                "chunk_index": chunk_idx,
                "total_chunks": len(chunk_embeddings),
                "domain": domain,
            }
            self._vector_db.add(chunk_id, chunk_text, embedding_vector, metadata)

    def store_and_embed_documents(self, root_dir: Path) -> None:
        """
        Process and store all documents from configured domains.

        Iterates through domain directories, loads markdown files,
        generates embeddings, and persists to vector database.

        Args:
            root_dir: Base directory containing domain subdirectories
        """
        configured_domains = self._parse_domains_config()

        for domain_name in configured_domains:
            domain_path = root_dir / domain_name
            if not domain_path.exists():
                continue

            # Process each markdown file in the domain
            for markdown_file in sorted(domain_path.glob("*.md")):
                # Generate unique document ID from file path
                source_doc_id = f"{domain_name}_{markdown_file.stem}"

                # Load and normalize document
                raw_content = markdown_file.read_text(encoding="utf-8", errors="ignore")
                normalized_content = self._normalize_markdown_content(raw_content)

                # Store document with metadata
                print(f"Processing: {markdown_file.name} (domain: {domain_name})")
                self._store_document(normalized_content, source_doc_id, domain_name)

    def process_query(self, text: str, k: int = 3) -> Tuple[str, Dict[str, List]]:
        """
        Execute full query processing pipeline.

        Generates embedding for input query and performs similarity
        searches using both cosine similarity and KNN algorithms.

        Args:
            text: User's search query
            k: Number of results to return per search method

        Returns:
            Tuple containing (query_identifier, search_results_dict)
            where search_results_dict has 'cosine' and 'knn' keys
        """
        query_identifier = str(uuid.uuid4())

        # get_embedding returns list of (chunk_text, embedding) tuples
        # For queries, we just use the first chunk's embedding
        chunk_embeddings = self._embedder.get_embedding(text)
        query_vector = chunk_embeddings[0][1]  # Get the embedding from first tuple

        cosine_matches = self._vector_db.similarity_search(query_vector, k=k)
        knn_matches = self._vector_db.knn_search(query_vector, k=k)

        search_results = {
            'cosine': cosine_matches,
            'knn': knn_matches
        }

        return query_identifier, search_results
