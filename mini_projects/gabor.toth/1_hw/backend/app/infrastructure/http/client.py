import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class AsyncHttpClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get(self, url: str, params: dict = None, headers: dict = None):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return await self.client.get(url, params=params, headers=headers)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def post(self, url: str, json: dict = None, data: str = None, headers: dict = None, **kwargs):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return await self.client.post(url, json=json, data=data, headers=headers, **kwargs)
