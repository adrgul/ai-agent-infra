"""
Reasoning node: expensive model for complex tasks.
Demonstrates when expensive models are justified.
"""
import logging
from typing import Dict
from app.graph.state import AgentState
from app.llm.interfaces import LLMClient
from app.llm.models import ModelSelector, ModelTier
from app.llm.cost_tracker import CostTracker
from app.observability import metrics
from app.utils.timing import async_timer

logger = logging.getLogger(__name__)


class ReasoningNode:
    """
    Reasoning node using expensive model for complex queries.
    
    This demonstrates when it's worth paying for an expensive model:
    - Complex reasoning required
    - Higher quality needed
    - Larger context window needed
    
    Note the higher max_tokens and more detailed prompt compared to triage.
    """
    
    NODE_NAME = "reasoning"
    
    def __init__(
        self,
        llm_client: LLMClient,
        cost_tracker: CostTracker,
        model_selector: ModelSelector
    ):
        """Initialize reasoning node."""
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.model_selector = model_selector
        self.model_name = model_selector.get_model_name(ModelTier.EXPENSIVE)
    
    async def execute(self, state: AgentState) -> Dict:
        """Execute reasoning node."""
        logger.info(f"Executing {self.NODE_NAME} node")
        
        # BAD PRACTICE: Always run reasoning, even for simple queries
        # Removed: if state.get("classification") != "complex": return {}
        
        async with async_timer() as timer_ctx:
            # Build detailed reasoning prompt
            prompt = self._build_prompt(state["user_input"], state.get("retrieval_context"))
            
            try:
                # BAD PRACTICE: Unnecessarily high max_tokens
                response = await self.llm_client.complete(
                    prompt=prompt,
                    model=self.model_name,
                    max_tokens=3000,  # Wastefully high
                    temperature=0.3  # Lower for more focused reasoning
                )
                
                reasoning_output = response.content.strip()
                
                # Track cost
                self.cost_tracker.track_usage(
                    self.NODE_NAME,
                    self.model_name,
                    response.input_tokens,
                    response.output_tokens
                )
                
                # Record metrics
                input_price, output_price = self.model_selector.get_pricing(self.model_name)
                cost = (response.input_tokens / 1000.0) * input_price + \
                       (response.output_tokens / 1000.0) * output_price
                
                metrics.record_llm_call(
                    model=self.model_name,
                    node=self.NODE_NAME,
                    latency=response.latency_seconds,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost=cost,
                    status="success"
                )
                
                logger.info(f"Reasoning complete, tokens: {response.input_tokens}+{response.output_tokens}, cost: ${cost:.4f}")
                
            except Exception as e:
                logger.error(f"Error in {self.NODE_NAME}: {e}")
                metrics.agent_error_count_total.labels(
                    graph="agent",
                    node=self.NODE_NAME,
                    error_type=type(e).__name__
                ).inc()
                reasoning_output = "Error occurred during reasoning. Falling back to simple response."
        
        elapsed = timer_ctx["elapsed"]
        metrics.node_execution_latency_seconds.labels(
            graph="agent",
            node=self.NODE_NAME
        ).observe(elapsed)
        
        return {
            "reasoning_output": reasoning_output,
            "nodes_executed": state.get("nodes_executed", []) + [self.NODE_NAME],
            "models_used": state.get("models_used", []) + [self.model_name],
            "timings": {**state.get("timings", {}), self.NODE_NAME: elapsed}
        }
    
    def _build_prompt(self, user_input: str, context: str = None) -> str:
        """
        Build detailed reasoning prompt.
        
        Note: This is longer than triage prompt, justifying the expensive model.
        """
        prompt = f"""You are an expert analyst. Provide a thorough, well-reasoned response to the following complex question.

Use step-by-step reasoning and consider multiple perspectives.

Question: {user_input}
"""
        
        if context:
            prompt += f"\nContext:\n{context}\n"
        
        prompt += "\nDetailed Analysis:"
        
        return prompt
