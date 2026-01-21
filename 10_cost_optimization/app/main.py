"""
FastAPI application with /run, /metrics, and /healthz endpoints.
Serves as the entry point for the agent demo.
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.logging_conf import setup_logging
from app.llm.interfaces import LLMClient
from app.llm.mock_client import MockLLMClient
from app.llm.models import ModelSelector
from app.llm.cost_tracker import CostTracker
from app.cache.memory_cache import MemoryCache
from app.graph.agent_graph import create_agent_graph
from app.graph.state import AgentState
from app.observability.middleware import MetricsMiddleware
from app.observability import metrics

# Setup logging
logger = setup_logging()


# Global dependencies (initialized in lifespan)
llm_client: Optional[LLMClient] = None
model_selector: Optional[ModelSelector] = None
node_cache: Optional[MemoryCache] = None
embedding_cache: Optional[MemoryCache] = None
agent_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes dependencies on startup, cleanup on shutdown.
    """
    global llm_client, model_selector, node_cache, embedding_cache, agent_graph
    
    logger.info("Starting agent demo application...")
    
    # Initialize model selector
    model_selector = ModelSelector()
    logger.info(f"Models configured: cheap={settings.model_cheap}, medium={settings.model_medium}, expensive={settings.model_expensive}")
    
    # Initialize LLM client (Mock by default, OpenAI if key present)
    if settings.openai_api_key:
        logger.info("Using OpenAI client (API key found)")
        from app.llm.openai_client import OpenAIClient
        llm_client = OpenAIClient(api_key=settings.openai_api_key)
    else:
        logger.info("Using Mock client (no API key)")
        llm_client = MockLLMClient(latency_ms=100)
    
    # Initialize caches
    node_cache = MemoryCache(
        default_ttl_seconds=settings.cache_ttl_seconds,
        max_size=settings.cache_max_size
    )
    embedding_cache = MemoryCache(
        default_ttl_seconds=settings.cache_ttl_seconds,
        max_size=settings.cache_max_size
    )
    logger.info(f"Caches initialized (TTL={settings.cache_ttl_seconds}s)")
    
    # Create agent graph (single instance, stateless)
    cost_tracker = CostTracker(model_selector)
    agent_graph = create_agent_graph(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,
        embedding_cache=embedding_cache
    )
    logger.info("Agent graph created")
    
    logger.info(f"Application ready on http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Cost Optimization Demo",
    description="Educational LangGraph demo with Prometheus observability",
    version="1.0.0",
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RunRequest(BaseModel):
    """Request model for /run endpoint."""
    user_input: str = Field(..., description="User query")
    scenario: Optional[str] = Field(None, description="Optional scenario hint: simple/retrieval/complex")


class CostBreakdown(BaseModel):
    """Cost breakdown for response."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    by_node: Dict[str, Dict[str, Any]]
    by_model: Dict[str, Dict[str, Any]]


class BenchmarkSummary(BaseModel):
    """Benchmark summary for repeated runs."""
    repeat: int
    total_time_seconds: float
    avg_time_per_run_seconds: float
    cache_hits: Dict[str, int]
    cache_misses: Dict[str, int]


class RunResponse(BaseModel):
    """Response model for /run endpoint."""
    answer: str
    debug: Dict[str, Any]
    benchmark: Optional[BenchmarkSummary] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for ALB/ECS health checks.
    Returns 200 OK if the service is running.
    """
    return {"status": "healthy", "service": "ai-agent-api"}


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agent-demo",
        "llm_client": "mock" if isinstance(llm_client, MockLLMClient) else "openai"
    }


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus exposition format.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/run", response_model=RunResponse)
async def run_agent(
    request: RunRequest,
    repeat: Optional[int] = Query(None, ge=1, le=1000, description="Number of times to repeat the agent execution for benchmarking")
):
    """
    Run the agent workflow.
    
    This is the main endpoint that executes the LangGraph workflow
    and returns the result with full observability data.
    
    When repeat=N is provided, executes the agent N times sequentially
    and returns benchmark statistics along with the last run's answer.
    """
    logger.info(f"Received request: {request.user_input[:50]}...")
    
    if repeat and repeat > 1:
        logger.info(f"Benchmark mode: will execute {repeat} times")
        return await _run_benchmark(request, repeat)
    else:
        return await _run_single(request)


async def _run_single(request: RunRequest) -> RunResponse:
    """Execute a single agent run."""
    # Create fresh cost tracker for this run
    cost_tracker = CostTracker(model_selector)
    
    # Create agent graph with new cost tracker
    graph = create_agent_graph(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,
        embedding_cache=embedding_cache
    )
    
    # Create initial state as dict
    initial_state: AgentState = {
        "user_input": request.user_input,
        "scenario": request.scenario,
        "classification": None,
        "retrieved_docs": [],
        "retrieval_context": None,
        "reasoning_output": None,
        "final_answer": None,
        "nodes_executed": [],
        "models_used": [],
        "timings": {},
        "cache_hits": {}
    }
    
    # Execute workflow with timing
    start_time = time.time()
    
    try:
        # Run the graph
        final_state = await graph.ainvoke(initial_state)
        
        elapsed_time = time.time() - start_time
        
        # Record agent-level metrics
        metrics.agent_execution_count_total.labels(graph="agent").inc()
        metrics.agent_execution_latency_seconds.labels(graph="agent").observe(elapsed_time)
        
        # Get cost report
        cost_report = cost_tracker.get_report()
        
        # Build response
        response = RunResponse(
            answer=final_state.get("final_answer", "No answer generated"),
            debug={
                "nodes_executed": final_state.get("nodes_executed", []),
                "models_used": final_state.get("models_used", []),
                "cost_report": {
                    "total_input_tokens": cost_report.total_input_tokens,
                    "total_output_tokens": cost_report.total_output_tokens,
                    "total_cost_usd": round(cost_report.total_cost_usd, 6),
                    "by_node": {
                        node: {
                            "input_tokens": nc.input_tokens,
                            "output_tokens": nc.output_tokens,
                            "cost_usd": round(nc.cost_usd, 6),
                            "calls": nc.call_count
                        }
                        for node, nc in cost_report.by_node.items()
                    },
                    "by_model": {
                        model: {
                            "input_tokens": mc.input_tokens,
                            "output_tokens": mc.output_tokens,
                            "cost_usd": round(mc.cost_usd, 6),
                            "calls": mc.call_count
                        }
                        for model, mc in cost_report.by_model.items()
                    }
                },
                "cache": final_state.get("cache_hits", {}),
                "timings": final_state.get("timings", {}),
                "total_time_seconds": round(elapsed_time, 3),
                "classification": final_state.get("classification")
            }
        )
        
        logger.info(f"Request completed in {elapsed_time:.2f}s, cost: ${cost_report.total_cost_usd:.6f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error executing agent: {e}", exc_info=True)
        metrics.agent_error_count_total.labels(
            graph="agent",
            node="runtime",
            error_type=type(e).__name__
        ).inc()
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


async def _run_benchmark(request: RunRequest, repeat: int) -> RunResponse:
    """
    Execute the agent multiple times for benchmarking.
    
    Runs the same agent input N times sequentially, tracking cache performance
    and returning only the last run's answer along with benchmark statistics.
    """
    benchmark_start = time.time()
    
    # Track cache stats across all runs
    total_node_cache_hits = 0
    total_node_cache_misses = 0
    total_embedding_cache_hits = 0
    total_embedding_cache_misses = 0
    
    final_state = None
    last_cost_report = None
    
    try:
        for run_idx in range(1, repeat + 1):
            run_start = time.time()
            
            # Create fresh cost tracker for this run
            cost_tracker = CostTracker(model_selector)
            
            # Create agent graph with new cost tracker
            graph = create_agent_graph(
                llm_client=llm_client,
                model_selector=model_selector,
                cost_tracker=cost_tracker,
                node_cache=node_cache,
                embedding_cache=embedding_cache
            )
            
            # Create initial state
            initial_state: AgentState = {
                "user_input": request.user_input,
                "scenario": request.scenario,
                "classification": None,
                "retrieved_docs": [],
                "retrieval_context": None,
                "reasoning_output": None,
                "final_answer": None,
                "nodes_executed": [],
                "models_used": [],
                "timings": {},
                "cache_hits": {}
            }
            
            # Execute the agent
            final_state = await graph.ainvoke(initial_state)
            
            run_elapsed = time.time() - run_start
            
            # Record agent-level metrics (each run increments counters)
            metrics.agent_execution_count_total.labels(graph="agent").inc()
            metrics.agent_execution_latency_seconds.labels(graph="agent").observe(run_elapsed)
            
            # Accumulate cache stats from this run
            cache_stats = final_state.get("cache_hits", {})
            node_cache_hit = cache_stats.get("node_cache", 0)
            embedding_cache_hit = cache_stats.get("embedding_cache", 0)
            
            # Determine hits vs misses
            # If a node executed, it's either a hit (cached) or miss (computed)
            # We can infer misses from nodes_executed that didn't result in cache hits
            if node_cache_hit > 0:
                total_node_cache_hits += node_cache_hit
            else:
                # First run or cache miss
                if run_idx == 1:
                    total_node_cache_misses += 1
                else:
                    total_node_cache_misses += 1
            
            if embedding_cache_hit > 0:
                total_embedding_cache_hits += embedding_cache_hit
            else:
                if run_idx == 1:
                    total_embedding_cache_misses += 1
                else:
                    total_embedding_cache_misses += 1
            
            # Get cost report for logging
            last_cost_report = cost_tracker.get_report()
            
            # Log progress
            cache_status = "cache hit" if (node_cache_hit > 0 or embedding_cache_hit > 0) else "cache miss"
            logger.info(f"Benchmark run {run_idx}/{repeat} – {cache_status} – {run_elapsed:.3f}s")
        
        # Calculate benchmark summary
        total_time = time.time() - benchmark_start
        avg_time = total_time / repeat
        
        benchmark_summary = BenchmarkSummary(
            repeat=repeat,
            total_time_seconds=round(total_time, 3),
            avg_time_per_run_seconds=round(avg_time, 3),
            cache_hits={
                "node_cache": total_node_cache_hits,
                "embedding_cache": total_embedding_cache_hits
            },
            cache_misses={
                "node_cache": total_node_cache_misses,
                "embedding_cache": total_embedding_cache_misses
            }
        )
        
        # Build response using last run's data
        response = RunResponse(
            answer=final_state.get("final_answer", "No answer generated"),
            debug={
                "nodes_executed": final_state.get("nodes_executed", []),
                "models_used": final_state.get("models_used", []),
                "cost_report": {
                    "total_input_tokens": last_cost_report.total_input_tokens,
                    "total_output_tokens": last_cost_report.total_output_tokens,
                    "total_cost_usd": round(last_cost_report.total_cost_usd, 6),
                    "by_node": {
                        node: {
                            "input_tokens": nc.input_tokens,
                            "output_tokens": nc.output_tokens,
                            "cost_usd": round(nc.cost_usd, 6),
                            "calls": nc.call_count
                        }
                        for node, nc in last_cost_report.by_node.items()
                    },
                    "by_model": {
                        model: {
                            "input_tokens": mc.input_tokens,
                            "output_tokens": mc.output_tokens,
                            "cost_usd": round(mc.cost_usd, 6),
                            "calls": mc.call_count
                        }
                        for model, mc in last_cost_report.by_model.items()
                    }
                },
                "cache": final_state.get("cache_hits", {}),
                "timings": final_state.get("timings", {}),
                "total_time_seconds": round(avg_time, 3),
                "classification": final_state.get("classification")
            },
            benchmark=benchmark_summary
        )
        
        logger.info(
            f"Benchmark completed: {repeat} runs in {total_time:.2f}s "
            f"(avg {avg_time:.3f}s/run), "
            f"node_cache hits={total_node_cache_hits}, "
            f"embedding_cache hits={total_embedding_cache_hits}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error during benchmark: {e}", exc_info=True)
        metrics.agent_error_count_total.labels(
            graph="agent",
            node="runtime",
            error_type=type(e).__name__
        ).inc()
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
