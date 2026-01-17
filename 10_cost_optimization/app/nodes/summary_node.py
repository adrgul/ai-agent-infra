"""
Summary node: medium model for final response generation.
Balances quality and cost for user-facing output.
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


class SummaryNode:
    """
    Summary node using medium-tier model.
    
    Optimization strategies:
    1. Medium model (balanced cost/quality)
    2. Constrained output (max_tokens limit)
    3. Direct prompt (no unnecessary elaboration)
    
    This is the final user-facing output, so we use a better
    model than triage but cheaper than reasoning.
    """
    
    NODE_NAME = "summary"
    
    def __init__(
        self,
        llm_client: LLMClient,
        cost_tracker: CostTracker,
        model_selector: ModelSelector
    ):
        """Initialize summary node."""
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.model_selector = model_selector
        # GOOD PRACTICE: Use medium model for summary - balance quality and cost
        self.model_name = model_selector.get_model_name(ModelTier.MEDIUM)
    
    async def execute(self, state: AgentState) -> Dict:
        """Execute summary node."""
        logger.info(f"Executing {self.NODE_NAME} node")
        
        async with async_timer() as timer_ctx:
            # Build prompt based on available information
            prompt = self._build_prompt(state)
            
            try:
                # GOOD PRACTICE: Reasonable max_tokens for concise summary
                response = await self.llm_client.complete(
                    prompt=prompt,
                    model=self.model_name,
                    max_tokens=500,  # Enough for quality summary
                    temperature=0.5  # Balanced creativity
                )
                
                final_answer = response.content.strip()
                
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
                
                logger.info(f"Summary complete, cost: ${cost:.4f}")
                
            except Exception as e:
                logger.error(f"Error in {self.NODE_NAME}: {e}")
                metrics.agent_error_count_total.labels(
                    graph="agent",
                    node=self.NODE_NAME,
                    error_type=type(e).__name__
                ).inc()
                final_answer = "I apologize, but I encountered an error generating a response."
        
        elapsed = timer_ctx["elapsed"]
        metrics.node_execution_latency_seconds.labels(
            graph="agent",
            node=self.NODE_NAME
        ).observe(elapsed)
        
        return {
            "final_answer": final_answer,
            "nodes_executed": state.get("nodes_executed", []) + [self.NODE_NAME],
            "models_used": state.get("models_used", []) + [self.model_name],
            "timings": {**state.get("timings", {}), self.NODE_NAME: elapsed}
        }
    
    def _build_prompt(self, state: AgentState) -> str:
        """
        Build summary prompt from available state.
        
        Optimization: Keep prompt concise but informative.
        ""
        # Load optimized prompt template
        try:
            with open("prompts/summary_prompt.txt", "r") as f:
                template = f.read()
            
            # Build context strings
            retrieval_ctx = f"\n\nRelevant Information:\n{state['retrieval_context']}" if state.get("retrieval_context") else ""
            reasoning_out = f"\n\nAnalysis:\n{state['reasoning_output']}" if state.get("reasoning_output") else ""
            
            return template.replace("{user_input}", state['user_input']) \
                          .replace("{retrieval_context}", retrieval_ctx) \
                          .replace("{reasoning_output}", reasoning_out)
        except FileNotFoundError:
            # Fallback to inline prompt
            prompt = f"Provide a clear, concise answer.\n\nQuestion: {state['user_input']}\n"
            if state.get("retrieval_context"):
                prompt += f"\nRelevant Information:\n{state['retrieval_context']}\n"
            if state.get("reasoning_output"):
                prompt += f"\nAnalysis:\n{state['reasoning_output']}\n"
            prompt += "\nAnswer:"
            return prompt
