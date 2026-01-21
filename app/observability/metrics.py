"""
Prometheus metrics registry and helpers.
Defines all metrics used throughout the application.
"""
from prometheus_client import Counter, Histogram, REGISTRY
import logging

logger = logging.getLogger(__name__)

# Define bucket ranges for latency histograms
LATENCY_BUCKETS = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]

# ============================================================================
# LLM METRICS
# ============================================================================

llm_inference_count_total = Counter(
    'llm_inference_count_total',
    'Total number of LLM inference calls',
    ['model', 'node', 'status']
)

llm_inference_latency_seconds = Histogram(
    'llm_inference_latency_seconds',
    'LLM inference latency in seconds',
    ['model', 'node'],
    buckets=LATENCY_BUCKETS
)

llm_inference_token_input_total = Counter(
    'llm_inference_token_input_total',
    'Total input tokens consumed',
    ['model', 'node']
)

llm_inference_token_output_total = Counter(
    'llm_inference_token_output_total',
    'Total output tokens generated',
    ['model', 'node']
)

llm_cost_total_usd = Counter(
    'llm_cost_total_usd',
    'Total LLM cost in USD',
    ['model', 'node']
)

# ============================================================================
# AGENT/WORKFLOW METRICS
# ============================================================================

agent_execution_count_total = Counter(
    'agent_execution_count_total',
    'Total agent execution count',
    ['graph']
)

agent_execution_latency_seconds = Histogram(
    'agent_execution_latency_seconds',
    'Agent execution latency in seconds',
    ['graph'],
    buckets=LATENCY_BUCKETS
)

node_execution_latency_seconds = Histogram(
    'node_execution_latency_seconds',
    'Node execution latency in seconds',
    ['graph', 'node'],
    buckets=LATENCY_BUCKETS
)

# ============================================================================
# CACHE METRICS
# ============================================================================

cache_hit_total = Counter(
    'cache_hit_total',
    'Total cache hits',
    ['cache', 'node']
)

cache_miss_total = Counter(
    'cache_miss_total',
    'Total cache misses',
    ['cache', 'node']
)

cache_lookup_latency_seconds = Histogram(
    'cache_lookup_latency_seconds',
    'Cache lookup latency in seconds',
    ['cache'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# ============================================================================
# RETRIEVAL/RAG METRICS
# ============================================================================

rag_retrieval_count_total = Counter(
    'rag_retrieval_count_total',
    'Total RAG retrieval operations',
    ['graph']
)

rag_docs_returned = Histogram(
    'rag_docs_returned',
    'Number of documents returned from retrieval',
    ['graph'],
    buckets=[1, 2, 3, 5, 10, 20, 50]
)

rag_context_bytes = Histogram(
    'rag_context_bytes',
    'Size of context in bytes',
    ['graph'],
    buckets=[100, 500, 1000, 2000, 5000, 10000, 20000]
)

# ============================================================================
# TOOL METRICS
# ============================================================================

tool_invocation_count_total = Counter(
    'tool_invocation_count_total',
    'Total tool invocations',
    ['tool', 'status']
)

tool_latency_seconds = Histogram(
    'tool_latency_seconds',
    'Tool invocation latency in seconds',
    ['tool'],
    buckets=LATENCY_BUCKETS
)

# ============================================================================
# ERROR/FALLBACK METRICS
# ============================================================================

agent_error_count_total = Counter(
    'agent_error_count_total',
    'Total agent errors',
    ['graph', 'node', 'error_type']
)

model_fallback_count_total = Counter(
    'model_fallback_count_total',
    'Total model fallback events',
    ['from_model', 'to_model', 'node']
)

max_retries_exceeded_count_total = Counter(
    'max_retries_exceeded_count_total',
    'Total max retries exceeded',
    ['node']
)

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['path', 'method', 'status']
)

http_request_latency_seconds = Histogram(
    'http_request_latency_seconds',
    'HTTP request latency in seconds',
    ['path', 'method'],
    buckets=LATENCY_BUCKETS
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_llm_call(
    model: str,
    node: str,
    latency: float,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    status: str = "success"
):
    """
    Record LLM call metrics.
    
    Args:
        model: Model identifier
        node: Node name
        latency: Call latency in seconds
        input_tokens: Input token count
        output_tokens: Output token count
        cost: Cost in USD
        status: Call status (success/error)
    """
    llm_inference_count_total.labels(model=model, node=node, status=status).inc()
    llm_inference_latency_seconds.labels(model=model, node=node).observe(latency)
    llm_inference_token_input_total.labels(model=model, node=node).inc(input_tokens)
    llm_inference_token_output_total.labels(model=model, node=node).inc(output_tokens)
    llm_cost_total_usd.labels(model=model, node=node).inc(cost)


def record_cache_lookup(cache_name: str, node: str, hit: bool, latency: float):
    """
    Record cache lookup metrics.
    
    Args:
        cache_name: Cache identifier
        node: Node name
        hit: Whether cache hit occurred
        latency: Lookup latency in seconds
    """
    if hit:
        cache_hit_total.labels(cache=cache_name, node=node).inc()
    else:
        cache_miss_total.labels(cache=cache_name, node=node).inc()
    
    cache_lookup_latency_seconds.labels(cache=cache_name).observe(latency)


logger.info("Prometheus metrics initialized")
