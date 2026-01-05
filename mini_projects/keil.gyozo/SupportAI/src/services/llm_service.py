"""LLM service for getting configured language models."""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None
) -> ChatOpenAI:
    """Get a configured ChatOpenAI instance.

    Args:
        model: Model name (default: from settings)
        temperature: Sampling temperature (0.0 for deterministic)
        api_key: OpenAI API key (default: from settings)

    Returns:
        Configured ChatOpenAI instance
    """
    model_name = model or settings.OPENAI_MODEL
    openai_api_key = api_key or settings.OPENAI_API_KEY

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=openai_api_key,
        max_retries=settings.OPENAI_MAX_RETRIES,
        timeout=settings.OPENAI_TIMEOUT,
    )

    logger.debug(f"Created LLM instance: {model_name} (temp={temperature})")
    return llm
