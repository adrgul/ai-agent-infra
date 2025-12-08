"""HTTP client utilities."""
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class HTTPClient:
    """HTTP client with retry logic and proper resource management."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "HTTPClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        Perform GET request with retry logic.

        Args:
            url: URL to request
            params: Query parameters
            headers: Request headers

        Returns:
            JSON response as dict

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")

        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
