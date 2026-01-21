"""
OpenAI client implementation (optional, requires API key).
"""
import asyncio
from typing import Optional
from openai import AsyncOpenAI
from app.llm.interfaces import LLMClient, LLMResponse
from app.config import settings
import time


class OpenAIClient(LLMClient):
    """
    OpenAI client implementation.
    
    Only used when OPENAI_API_KEY is set in environment.
    Demonstrates Open/Closed Principle: extends functionality without
    modifying the interface or existing mock implementation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def complete(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        start = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            latency = time.time() - start
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                latency_seconds=latency,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "temperature": temperature
                }
            )
        except Exception as e:
            # Re-raise with context
            raise RuntimeError(f"OpenAI API call failed: {str(e)}") from e
