"""
LLM client interface following Dependency Inversion Principle.
Nodes depend on this abstraction, not concrete implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMClient(ABC):
    """
    Abstract LLM client interface.
    
    Implementations must provide a completion method that returns
    a standardized LLMResponse. This allows swapping between mock,
    OpenAI, Anthropic, or other providers without changing node code.
    """
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The input prompt
            model: Model identifier
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with standardized fields
        """
        pass
