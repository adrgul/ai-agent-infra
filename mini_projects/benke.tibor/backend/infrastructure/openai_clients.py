"""
Centralized OpenAI client management.
Singleton pattern for LLM and Embeddings clients with error handling.
"""
import os
import logging
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from infrastructure.error_handling import (
    retry_with_exponential_backoff,
    usage_tracker,
    check_token_limit,
)

logger = logging.getLogger(__name__)


class OpenAIClientFactory:
    """
    Factory for creating and caching OpenAI clients.
    Uses singleton pattern to avoid multiple client instances.
    """
    
    _llm_instance: Optional[ChatOpenAI] = None
    _embeddings_instance: Optional[OpenAIEmbeddings] = None
    
    @classmethod
    def get_llm(
        cls,
        model: str = None,
        temperature: float = None,
        api_key: str = None,
        max_retries: int = 3,
        request_timeout: int = 60,
    ) -> ChatOpenAI:
        """
        Get or create ChatOpenAI instance (singleton) with error handling.
        
        Args:
            model: OpenAI model name (default: from env)
            temperature: LLM temperature (default: from env)
            api_key: OpenAI API key (default: from env)
            max_retries: Max retry attempts for failed requests
            request_timeout: Request timeout in seconds
            
        Returns:
            ChatOpenAI instance with retry logic
        """
        if cls._llm_instance is None:
            model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            temperature = temperature if temperature is not None else float(os.getenv('LLM_TEMPERATURE', '0.7'))
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            
            cls._llm_instance = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key,
                max_retries=max_retries,
                request_timeout=request_timeout,
            )
            logger.info(
                f"OpenAI LLM initialized: {model} (temp={temperature}, "
                f"max_retries={max_retries}, timeout={request_timeout}s)"
            )
        
        return cls._llm_instance
    
    @classmethod
    def get_embeddings(
        cls,
        model: str = None,
        api_key: str = None,
        max_retries: int = 3,
    ) -> OpenAIEmbeddings:
        """
        Get or create OpenAIEmbeddings instance (singleton) with error handling.
        
        Args:
            model: Embedding model name (default: from env)
            api_key: OpenAI API key (default: from env)
            max_retries: Max retry attempts for failed requests
            
        Returns:
            OpenAIEmbeddings instance with retry logic
        """
        if cls._embeddings_instance is None:
            model = model or os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            
            cls._embeddings_instance = OpenAIEmbeddings(
                model=model,
                openai_api_key=api_key,
                max_retries=max_retries,
            )
            logger.info(f"OpenAI Embeddings initialized: {model} (max_retries={max_retries})")
        
        return cls._embeddings_instance
    
    @classmethod
    def get_usage_stats(cls) -> dict:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        return usage_tracker.get_summary()
    
    @classmethod
    def reset_usage_stats(cls) -> None:
        """Reset usage tracker."""
        usage_tracker.reset()
        logger.info("Usage stats reset")
    
    @classmethod
    def reset(cls):
        """Reset singleton instances (useful for testing)."""
        cls._llm_instance = None
        cls._embeddings_instance = None
        logger.info("OpenAI clients reset")
