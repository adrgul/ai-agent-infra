"""
OpenAI embedding client implementation.

Purpose:
- Convert raw text into vector embeddings
- Communicate directly with OpenAI via HTTP
- Return a numeric vector usable by vector databases

Design notes:
- Implements the Embedder interface
- Keeps HTTP, parsing, and logging concerns separated
- Raises exceptions instead of swallowing errors
"""

from typing import Sequence, List, Literal, Optional
import requests
import json

from scripts.interfaces import Embedder


class OpenAIEmbeddingClient(Embedder):
    """
    Concrete Embedder implementation using OpenAI's Embeddings API.
    """

    # Default OpenAI embeddings endpoint
    DEFAULT_ENDPOINT = "https://api.openai.com/v1/embeddings"

    def __init__(
        self,
        token: str,
        model_name: str = "text-embedding-3-small",
        endpoint: str | None = None,
        chunk_size: Optional[int] = None,
        overlap: int = 0
    ) -> None:
        """
        Create a new embedding client.

        Args:
            token:
                OpenAI API key used for authentication.
            model_name:
                Name of the embedding model.
            endpoint:
                Optional override for the embeddings endpoint.
                Useful for testing or proxying.
        """
        # Store credentials and configuration
        self._token = token
        self._model = model_name
        self._endpoint = endpoint or self.DEFAULT_ENDPOINT
        self._chunk_size = chunk_size
        self._overlap = overlap


    def get_embedding(
            self,
            text: str,
        ) -> List[tuple[str, List[float]]]:
            """
            Generate embeddings using OpenAI's API.
            Chunks the input text and returns individual chunk embeddings.

            Args:
                text: Input text to embed.

            Returns:
                List of (chunk_text, embedding_vector) tuples.
            """

            def chunk_text(text: str) -> List[str]:
                if self._chunk_size is None or self._chunk_size <= 0:
                    return [text]

                chunks = []
                start = 0
                while start < len(text):
                    end = start + self._chunk_size
                    chunks.append(text[start:end])
                    start = end - self._overlap
                    if start < 0:
                        start = 0
                return chunks

            def call_openai(input_text: str) -> List[float]:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._token}",
                }

                payload = {
                    "model": self._model,
                    "input": input_text,
                }

                response = requests.post(
                    self._endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()

                data = response.json()
                return data["data"][0]["embedding"]

            try:
                chunks = chunk_text(text)
                print(f"  → Embedding {len(chunks)} chunk(s)")

                # Return list of (chunk_text, embedding_vector) tuples
                chunk_embeddings = [
                    (chunk, call_openai(chunk))
                    for chunk in chunks
                ]

                return chunk_embeddings

            except requests.exceptions.RequestException as e:
                print(f"Error generating embedding (HTTP request failed): {e}")
                if hasattr(e, "response") and e.response is not None:
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response body: {e.response.text}")
                raise
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                print(f"Error parsing API response: {e}")
                raise
            except Exception as e:
                print(f"Unexpected error generating embedding: {e}")
                raise


    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict:
        """
        Construct HTTP headers for the API request.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            # Bearer token authentication
            "Authorization": f"Bearer {self._token}",

            # Inform server that JSON is being sent
            "Content-Type": "application/json",
        }

    def _build_payload(self, text: str) -> dict:
        """
        Construct JSON payload for embedding request.

        Args:
            text:
                Input text to embed.

        Returns:
            Dictionary representing JSON request body.
        """
        return {
            "model": self._model,
            "input": text,
        }

    def _extract_embedding(self, payload: dict) -> list[float]:
        """
        Extract embedding vector from OpenAI response.

        Expected response structure:
        {
            "data": [
                {
                    "embedding": [...],
                    "index": 0
                }
            ],
            "model": "...",
            "usage": {...}
        }

        Args:
            payload:
                Parsed JSON response from OpenAI.

        Returns:
            Embedding vector as list of floats.
        """
        return payload["data"][0]["embedding"]

    def _handle_http_error(self, error: requests.RequestException) -> None:
        """
        Log details of HTTP-related failures.

        Args:
            error:
                Exception raised by requests.
        """
        print("[embedding] Request failed")

        # Print the root error
        print(f"[embedding] Error: {error}")

        # If response exists, log HTTP details
        response = getattr(error, "response", None)
        if response is not None:
            print(f"[embedding] Status code: {response.status_code}")
            print(f"[embedding] Response body: {response.text}")

    def _log_request(self, text: str) -> None:
        """
        Log basic request metadata.

        Args:
            text:
                Input text being embedded.
        """
        print("[embedding] Sending request")
        print(f"[embedding] Endpoint: {self._endpoint}")
        print(f"[embedding] Model: {self._model}")
        print(f"[embedding] Input length: {len(text)} characters")

    def _log_success(self, vector: Sequence[float], payload: dict) -> None:
        """
        Log metadata for a successful embedding request.

        Args:
            vector:
                Returned embedding vector.
            payload:
                Full API response payload.
        """
        print("[embedding] Request succeeded")
        print(f"[embedding] Vector dimension: {len(vector)}")
        print(f"[embedding] Usage info: {payload.get('usage', {})}")