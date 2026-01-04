from typing import List

# httpx is used for Google Custom Search calls. If it's not installed in the
# runtime (e.g., local dev environment without dependencies installed), we
# gracefully handle that and surface a clear message when Google is selected.
try:
    import httpx
    _HTTPX_AVAILABLE = True
except Exception:
    httpx = None
    _HTTPX_AVAILABLE = False

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from ..core.config import settings


class WebSearchService:
    """Removed web search service.

    The project no longer supports web search. This stub remains for
    compatibility but always reports that search is unavailable.
    """

    def __init__(self) -> None:
        self.google_enabled = False
        self.openai_enabled = False

    @property
    def enabled(self) -> bool:
        return False

    def search(self, query: str):
        return ["Web search has been removed from this project."]
