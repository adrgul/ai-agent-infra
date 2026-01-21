"""
Mock LLM client for offline demo and testing.
Returns deterministic responses without requiring API keys.
"""
import asyncio
import hashlib
from app.llm.interfaces import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """
    Mock LLM implementation for demos and testing.
    
    - Returns deterministic responses based on prompt hash
    - Simulates realistic token counts and latency
    - No API key required
    - Demonstrates interface compliance (Liskov Substitution Principle)
    """
    
    def __init__(self, latency_ms: int = 100):
        """
        Initialize mock client.
        
        Args:
            latency_ms: Simulated latency in milliseconds
        """
        self.latency_ms = latency_ms
    
    async def complete(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock completion."""
        import time
        start = time.time()
        
        # Simulate network latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Generate deterministic response based on prompt
        response_content = self._generate_mock_response(prompt, model)
        
        # Simulate realistic token counts
        input_tokens = len(prompt.split())
        output_tokens = len(response_content.split())
        
        latency = time.time() - start
        
        return LLMResponse(
            content=response_content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_seconds=latency,
            metadata={"mock": True, "temperature": temperature}
        )
    
    def _generate_mock_response(self, prompt: str, model: str) -> str:
        """Generate deterministic mock response based on prompt."""
        # Hash prompt for determinism
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        
        # Different responses based on prompt keywords
        prompt_lower = prompt.lower()
        
        if "classify" in prompt_lower or "category" in prompt_lower or "triage" in prompt_lower:
            # Triage node response
            if "weather" in prompt_lower or "time" in prompt_lower or "hello" in prompt_lower:
                return "simple"
            elif "document" in prompt_lower or "search" in prompt_lower or "find" in prompt_lower:
                return "retrieval"
            else:
                return "complex"
        
        elif "retrieve" in prompt_lower or "search" in prompt_lower:
            # Retrieval node response
            return f"Retrieved context: Document about query topic (mock-{prompt_hash}). Contains relevant information for processing."
        
        elif "reason" in prompt_lower or "analyze" in prompt_lower:
            # Reasoning node response
            return f"After careful analysis of the complex problem, the solution involves considering multiple factors. The key insight is that {prompt_hash} represents the optimal approach given the constraints."
        
        else:
            # Summary/default response
            return f"Mock response for model {model}. This demonstrates the interface working without real API calls. Hash: {prompt_hash}"
