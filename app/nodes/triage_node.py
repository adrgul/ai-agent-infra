"""
Triage node: cheap model classification with node-level caching.
Demonstrates cost optimization through minimal prompts and caching.
"""
import logging
import time
from typing import Dict
from app.graph.state import AgentState
from app.llm.interfaces import LLMClient
from app.llm.models import ModelSelector, ModelTier
from app.llm.cost_tracker import CostTracker
from app.cache.interfaces import Cache
from app.cache.keys import generate_cache_key
from app.observability import metrics
from app.utils.timing import async_timer

logger = logging.getLogger(__name__)


class TriageNode:
    """
    Triage node using cheap model with aggressive caching.
    
    Optimization strategies:
    1. Uses cheapest model (gpt-3.5-turbo)
    2. Minimal prompt (reduces input tokens)
    3. Node-level cache (avoids repeated calls for same queries)
    4. Low max_tokens (reduces output cost)
    
    Dependencies injected via constructor (DIP).
    """
    
    NODE_NAME = "triage"
    CACHE_NAME = "node_cache"
    
    def __init__(
        self,
        llm_client: LLMClient,
        cost_tracker: CostTracker,
        model_selector: ModelSelector,
        cache: Cache
    ):
        """
        Initialize triage node.
        
        Args:
            llm_client: LLM client interface
            cost_tracker: Cost tracking service
            model_selector: Model selection service
            cache: Cache implementation
        """
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.model_selector = model_selector
        self.cache = cache
        # GOOD PRACTICE: Use cheapest model for simple classification
        self.model_name = model_selector.get_model_name(ModelTier.CHEAP)
    
    async def execute(self, state: AgentState) -> Dict:
        """
        Execute triage node.
        
        Returns:
            State updates
        """
        logger.info(f"Executing {self.NODE_NAME} node")
        
        # Track node execution
        async with async_timer() as timer_ctx:
            # Check cache first
            cache_key = generate_cache_key(self.NODE_NAME, state["user_input"])
            
            # GOOD PRACTICE: Enable node-level caching for triage
            cache_lookup_start = time.time()
            cached_result = await self.cache.get(cache_key)
            cache_lookup_time = time.time() - cache_lookup_start
            
            if cached_result is not None:
                # Cache hit
                logger.info(f"Cache hit for {self.NODE_NAME}")
                metrics.record_cache_lookup(
                    self.CACHE_NAME,
                    self.NODE_NAME,
                    hit=True,
                    latency=cache_lookup_time
                )
                
                classification = cached_result
            else:
                # Cache miss - call LLM
                logger.info(f"Cache miss for {self.NODE_NAME}")
                metrics.record_cache_lookup(
                    self.CACHE_NAME,
                    self.NODE_NAME,
                    hit=False,
                    latency=cache_lookup_time
                )
                
                # Load prompt
                prompt = self._build_prompt(state["user_input"])
                
                # Call LLM
                try:
                    # GOOD PRACTICE: Strict max_tokens limit for one-word classification
                    response = await self.llm_client.complete(
                        prompt=prompt,
                        model=self.model_name,
                        max_tokens=10,  # Only need one word
                        temperature=0.0  # Deterministic
                    )
                    
                    # Extract classification
                    classification = response.content.strip().lower()
                    
                    # Normalize to expected values
                    if "simple" in classification:
                        classification = "simple"
                    elif "retrieval" in classification or "search" in classification:
                        classification = "retrieval"
                    else:
                        classification = "complex"
                    
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
                    
                    # GOOD PRACTICE: Cache triage results for repeated queries
                    await self.cache.set(cache_key, classification)
                    
                except Exception as e:
                    logger.error(f"Error in {self.NODE_NAME}: {e}")
                    metrics.agent_error_count_total.labels(
                        graph="agent",
                        node=self.NODE_NAME,
                        error_type=type(e).__name__
                    ).inc()
                    classification = "simple"  # Fallback
        
        # Record node latency
        elapsed = timer_ctx["elapsed"]
        metrics.node_execution_latency_seconds.labels(
            graph="agent",
            node=self.NODE_NAME
        ).observe(elapsed)
        
        logger.info(f"Triage classification: {classification}")
        
        return {
            "classification": classification,
            "nodes_executed": state.get("nodes_executed", []) + [self.NODE_NAME],
            "models_used": state.get("models_used", []) + [self.model_name],
            "timings": {**state.get("timings", {}), self.NODE_NAME: elapsed},
            "cache_hits": {**state.get("cache_hits", {}), self.NODE_NAME: cached_result is not None}
        }
    
    def _build_prompt(self, user_input: str) -> str:
        """
        Build minimal classification prompt.
        
        Cost optimization: Very short prompt to minimize input tokens.
        """
        # Load optimized prompt from file
        try:
            with open("prompts/triage_prompt.txt", "r") as f:
                template = f.read()
            return template.replace("{user_input}", user_input)
        except FileNotFoundError:
            # Fallback to inline prompt
            return f"""Classify query type. Output ONE word only.

Types:
- simple: factual, direct answer
- retrieval: requires looking up information
- complex: needs reasoning or analysis

Query: {user_input}

Classification:"""
