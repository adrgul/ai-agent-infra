GitHub Copilot Prompt – Deep Observability for LangGraph AI Agent
🎯 Objective
Extend the existing LangGraph-based AI agent application with deep observability, focusing strictly on:
Prompt lineage
Agent decision tracing (LangGraph state snapshots)
Token-level cost tracking
Model fallback path visibility
Prometheus-based metrics
Grafana dashboards
⚠️ Do NOT introduce any features beyond what is explicitly listed below.

🧠 Context
Python backend
LangGraph used for agent workflows
LLM calls (multiple models with fallback)
Optional RAG (vector database)
Prometheus + Grafana already running via Docker
Backend, frontend, and monitoring stack are containerized

🧩 Observability Scope (STRICT)
A) Deep Observability Capabilities (MANDATORY)
Implement ALL of the following:
Prompt lineage
Track prompt versions / hashes per LLM invocation
Associate each prompt with:
request_id
agent_execution_id
model_name
Agent decision trace
Capture LangGraph state snapshots:
before execution
after each node
after completion
Store snapshots in memory or structured logs (NO full prompt content)
Token-level cost tracking
Input tokens
Output tokens
Cost calculated per model using configured pricing
Model fallback path visibility
Track:
primary model attempt
fallback model usage
retry exhaustion
Count and expose fallback paths explicitly

📊 Metrics to Implement (Prometheus)
1️⃣ LLM Inference Metrics
Implement exactly the following metrics:
llm_inference_count{model}
llm_inference_latency_seconds{model}
llm_inference_token_input_total{model}
llm_inference_token_output_total{model}
llm_cost_total_usd{model}
All metrics must be emitted only via a centralized LLM wrapper.

2️⃣ Agent Workflow Metrics (LangGraph)
Implement exactly the following metrics:
agent_execution_count
agent_execution_latency_seconds
node_execution_latency_seconds{node}
tool_invocation_count{tool}
rag_recall_rate (advanced – derived relevance metric)
Node-level metrics must use LangGraph node names as labels.

3️⃣ Error & Fallback Metrics
Implement exactly the following metrics:
agent_error_count
tool_failure_count{tool}
model_fallback_count{from_model,to_model}
max_retries_exceeded_count
Fallback metrics must reflect actual fallback paths, not retries.

4️⃣ Cost Metrics (REAL-TIME – REQUIRED)
Implement real-time cost accumulation:
llm_cost_total_usd{model="gpt-4o-mini"}
llm_cost_total_usd{model="gpt-4.1"}
Cost must be:
calculated per request
accumulated globally
derivable per model, per agent execution

5️⃣ RAG Metrics
Implement exactly the following:
rag_chunk_retrieval_count
rag_retrieved_chunk_relevance_score_avg
vector_db_query_latency_seconds
embedding_generation_count
Relevance score must be aggregated as average per query.

📡 Instrumentation Rules
All metrics must:
be defined in a dedicated observability module
use Prometheus primitives only (Counter, Histogram, Gauge)
Avoid high-cardinality labels
Do NOT use user_id as a metric label
Use:
model
node
tool
agent_execution_id (logs only, NOT metrics)

🌐 Metrics Exposure
Expose a single /metrics endpoint
Compatible with Prometheus scraping
No authentication
No business logic inside /metrics

📊 Grafana Dashboards (JSON REQUIRED)
Create exactly 4 dashboards, exported as JSON.

📘 Dashboard 1: LLM Dashboard
Panels:
inference count
tokens_in / tokens_out
cost (USD)
latency p50 / p95 / p99
error rate

🔁 Dashboard 2: Agent Workflow Dashboard
Panels:
agent execution latency
node latency:
retriever
parser
router
tool invocation count
model fallback count

📚 Dashboard 3: RAG Dashboard
Panels:
retrieval latency
top-k relevance score
vector DB load
embedding generation count

💰 Dashboard 4: Cost Dashboard
Panels:
cost per model
cost per user (derived, not label-based)
cost per agent workflow
daily burn rate

🐳 Docker Compatibility (MANDATORY)
Ensure:
Metrics are accessible from Prometheus container
No hardcoded hostnames
All ports configurable via env vars

🚫 Explicit Non-Goals (DO NOT IMPLEMENT)
❌ No tracing frameworks (Jaeger, Tempo, OpenTelemetry)
❌ No external SaaS observability tools
❌ No logging of raw prompts or PII
❌ No dashboard beyond the four specified
❌ No metric beyond the listed ones

✅ Final State Validation
After implementation, the system must allow:
Full visibility into:
prompt evolution
agent decision paths
model fallback behavior
real-time cost
Accurate Prometheus metrics
Ready-to-import Grafana dashboards
Zero impact on agent functional behavior

End of instructions.

