

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Literal, Dict, Any


class Embedder(ABC):

    @abstractmethod
    def get_embedding(
        self,
        text: str,
    ) -> List[Tuple[str, List[float]]]:
        """
        Transform the given text to vector embeddings (chunked).

        Args:
            text: Input text.

        Returns:
            List of (chunk_text, embedding_vector) tuples.
        """
        pass


class VectorDB(ABC):

    @abstractmethod
    def add(self, id: str, text: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Persist the given text and embedded vector into the vector database.

        Args:
            id: Unique id.
            text: Text chunk.
            embedding: The vector which represents the text.
            metadata: Optional metadata to store with the vector (e.g., source document, chunk index).
        """
        pass

    @abstractmethod
    def similarity_search(
            self,
            embedding: List[float],
            k: int = 3
    ) -> List[Tuple[str, float, float, str, Optional[Dict[str, Any]]]]:
        """
        Find the k most similar entries to the given embedding.

        Args:
            embedding: The query embedding vector.
            k: Number of nearest neighbors to return.

        Returns:
            List of tuples (id, distance, similarity, text, metadata) ordered by similarity.
            Distance is the cosine distance (lower is better).
            Similarity is cosine similarity (higher is better, range 0-1).
            Metadata is optional dict containing chunk information.
        """
        pass

    @abstractmethod
    def knn_search(
            self,
            embedding: List[float],
            k: int = 3
    ) -> List[Tuple[str, float, str, Optional[Dict[str, Any]]]]:
        """
        Find the k nearest neighbors using Euclidean distance.

        Args:
            embedding: The query embedding vector.
            k: Number of nearest neighbors to return.

        Returns:
            List of tuples (id, euclidean_distance, text, metadata) ordered by distance.
            Lower distance means higher similarity.
            Metadata is optional dict containing chunk information.
        """
        pass
