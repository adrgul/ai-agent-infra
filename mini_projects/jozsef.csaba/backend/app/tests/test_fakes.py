"""
Fake implementations for testing without external API calls.

Why this module exists:
- Provides fake embeddings and LLMs for testing
- Avoids OpenAI API calls during tests (no cost, no network dependency)
- Deterministic behavior for reproducible tests

Design decisions:
- FakeEmbeddings returns fixed-size random vectors (compatible with FAISS)
- FakeLLM returns constant string (for contract testing)
- Both implement LangChain interfaces for drop-in replacement
"""

from typing import List
import hashlib

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation, LLMResult


class FakeEmbeddings(Embeddings):
    """
    Fake embeddings for testing without OpenAI API calls.

    Why this class: Tests need embeddings to build FAISS index,
    but shouldn't make real API calls (slow, costs money, requires network).

    Why deterministic: Uses hash of text to generate consistent vectors,
    ensuring test reproducibility.

    Why 1536 dimensions: Matches text-embedding-3-small output dimension,
    ensuring compatibility with production code.
    """

    def __init__(self, dimension: int = 1536):
        """
        Initialize fake embeddings.

        Args:
            dimension: Vector dimension (default 1536 to match OpenAI)
        """
        # Assert: dimension must be positive
        assert dimension > 0, "Dimension must be positive"
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate fake embeddings for documents.

        Why deterministic: Hash text to generate consistent vectors.
        Same text always produces same vector (important for test reproducibility).

        Args:
            texts: List of text strings to embed

        Returns:
            List[List[float]]: List of fake embedding vectors
        """
        # Assert: texts must not be empty
        assert len(texts) > 0, "Must provide at least one text to embed"

        embeddings = []
        for text in texts:
            # Why hash: Deterministic mapping from text to numbers
            # MD5 is fine for testing (not used for security)
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()

            # Generate vector from hash bytes
            # Why normalize: Typical of real embeddings (roughly unit length)
            vector = []
            for i in range(self.dimension):
                # Use hash bytes cyclically to fill dimension
                byte_val = hash_bytes[i % len(hash_bytes)]
                # Normalize to [-1, 1] range
                normalized = (byte_val / 127.5) - 1.0
                vector.append(normalized)

            embeddings.append(vector)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Generate fake embedding for a query.

        Why same as embed_documents: In testing, queries and documents
        should use same embedding logic for consistent retrieval.

        Args:
            text: Query string to embed

        Returns:
            List[float]: Fake embedding vector
        """
        return self.embed_documents([text])[0]


class FakeLLM(BaseLLM):
    """
    Fake LLM for testing without OpenAI API calls.

    Why this class: Tests need LLM responses but shouldn't make real API calls.
    Returns constant string for predictable contract testing.

    Why track prompts: Allows tests to verify correct prompt construction.
    """

    def __init__(self, response: str = "This is a fake LLM response."):
        """
        Initialize fake LLM.

        Args:
            response: Constant string to return for all queries
        """
        # Assert: response must not be empty
        assert response.strip(), "Response must not be empty"

        super().__init__()
        self.response = response
        self.prompts: List[str] = []  # Track prompts for test assertions

    @property
    def _llm_type(self) -> str:
        """LLM type identifier."""
        return "fake"

    def _generate(
        self,
        prompts: List[str],
        stop: List[str] | None = None,
        **kwargs,
    ) -> LLMResult:
        """
        Generate fake responses.

        Why track prompts: Allows tests to inspect what was sent to LLM.

        Args:
            prompts: List of prompt strings
            stop: Stop sequences (ignored in fake)
            **kwargs: Additional parameters (ignored in fake)

        Returns:
            LLMResult: Fake generation result
        """
        # Assert: Must have at least one prompt
        assert len(prompts) > 0, "Must provide at least one prompt"

        # Track prompts for test inspection
        self.prompts.extend(prompts)

        # Return constant response for each prompt
        generations = [
            [Generation(text=self.response)] for _ in prompts
        ]

        return LLMResult(generations=generations)

    async def _agenerate(
        self,
        prompts: List[str],
        stop: List[str] | None = None,
        **kwargs,
    ) -> LLMResult:
        """Async version delegates to sync (fine for testing)."""
        return self._generate(prompts, stop, **kwargs)
