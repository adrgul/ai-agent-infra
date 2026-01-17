"""
Retrieval node: RAG simulation with embedding cache.
Demonstrates retrieval optimization and context management.
"""
import logging
import hashlib
import time
from typing import Dict, List
from app.graph.state import AgentState
from app.llm.interfaces import LLMClient
from app.llm.models import ModelSelector, ModelTier
from app.llm.cost_tracker import CostTracker
from app.cache.interfaces import Cache
from app.cache.keys import generate_cache_key
from app.observability import metrics
from app.utils.timing import async_timer
from app.utils.text_norm import truncate_text

logger = logging.getLogger(__name__)


# Simulated knowledge base
KNOWLEDGE_BASE = [
    "Python is a high-level programming language known for its simplicity and readability.",
    "Docker is a platform for developing, shipping, and running applications in containers.",
    "Kubernetes is an open-source container orchestration platform for automating deployment.",
    "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
    "Prometheus is an open-source monitoring and alerting toolkit designed for reliability.",
    "Grafana is an open-source analytics and monitoring solution for time-series data.",
    "FastAPI is a modern, fast web framework for building APIs with Python.",
    "Redis is an in-memory data structure store used as a database and cache.",
]


class RetrievalNode:
    """
    Retrieval node with embedding cache simulation.
    
    Optimization strategies:
    1. Embedding cache (avoid re-computing embeddings)
    2. Top-k filtering (limit context size)
    3. Document truncation (control token usage)
    4. Cheap model for retrieval (if LLM-based reranking)
    
    This demonstrates RAG cost optimization principles.
    """
    
    NODE_NAME = "retrieval"
    CACHE_NAME = "embedding_cache"
    TOP_K = 3
    MAX_DOC_LENGTH = 200
    
    def __init__(
        self,
        llm_client: LLMClient,
        cost_tracker: CostTracker,
        model_selector: ModelSelector,
        embedding_cache: Cache
    ):
        """Initialize retrieval node."""
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.model_selector = model_selector
        self.embedding_cache = embedding_cache
        # GOOD PRACTICE: Use cheap model for retrieval/embedding tasks
        self.model_name = model_selector.get_model_name(ModelTier.CHEAP)
    
    async def execute(self, state: AgentState) -> Dict:
        """Execute retrieval node."""
        logger.info(f"Executing {self.NODE_NAME} node")
        
        # GOOD PRACTICE: Only run retrieval when classification indicates it's needed
        if state.get("classification") not in ["retrieval", "complex"]:
            logger.info("Skipping retrieval - not needed for this query type")
            return {
                "nodes_executed": state.get("nodes_executed", []) + [f"{self.NODE_NAME}_skipped"],
            }
        
        async with async_timer() as timer_ctx:
            # Get query embedding (cached)
            query_embedding = await self._get_embedding(state["user_input"])
            
            # Retrieve documents (simulate similarity search)
            docs = await self._retrieve_documents(state["user_input"], query_embedding)
            
            # Format context with length constraints
            context = self._format_context(docs)
            
            # Record RAG metrics
            metrics.rag_retrieval_count_total.labels(graph="agent").inc()
            metrics.rag_docs_returned.labels(graph="agent").observe(len(docs))
            metrics.rag_context_bytes.labels(graph="agent").observe(len(context.encode('utf-8')))
        
        elapsed = timer_ctx["elapsed"]
        metrics.node_execution_latency_seconds.labels(
            graph="agent",
            node=self.NODE_NAME
        ).observe(elapsed)
        
        logger.info(f"Retrieved {len(docs)} documents, context size: {len(context)} chars")
        
        return {
            "retrieved_docs": docs,
            "retrieval_context": context,
            "nodes_executed": state.get("nodes_executed", []) + [self.NODE_NAME],
            "timings": {**state.get("timings", {}), self.NODE_NAME: elapsed}
        }
    
    async def _get_embedding(self, text: str) -> str:
        """
        Get embedding for text (simulated with caching).
        
        In production, this would call an embedding model.
        Cache prevents recomputing embeddings for the same text.
        """
        cache_key = generate_cache_key(self.CACHE_NAME, text)
        
        # GOOD PRACTICE: Enable embedding cache to avoid recomputation
        cache_lookup_start = time.time()
        cached_embedding = await self.embedding_cache.get(cache_key)
        cache_lookup_time = time.time() - cache_lookup_start
        
        if cached_embedding is not None:
            logger.info(f"Embedding cache hit")
            metrics.record_cache_lookup(
                self.CACHE_NAME,
                self.NODE_NAME,
                hit=True,
                latency=cache_lookup_time
            )
            return cached_embedding
        
        # Cache miss - compute embedding (simulated)
        logger.info(f"Embedding cache miss")
        metrics.record_cache_lookup(
            self.CACHE_NAME,
            self.NODE_NAME,
            hit=False,
            latency=cache_lookup_time
        )
        
        # Simulate embedding as deterministic hash
        embedding = hashlib.sha256(text.encode()).hexdigest()
        
        # GOOD PRACTICE: Cache embeddings for reuse
        await self.embedding_cache.set(cache_key, embedding)
        
        return embedding
    
    async def _retrieve_documents(self, query: str, query_embedding: str) -> List[str]:
        """
        Retrieve documents (simulated similarity search).
        
        In production, this would query a vector database.
        """
        # Simulate relevance scoring (based on keyword overlap)
        query_lower = query.lower()
        scored_docs = []
        
        for doc in KNOWLEDGE_BASE:
            # Simple relevance: count matching words
            doc_words = set(doc.lower().split())
            query_words = set(query_lower.split())
            overlap = len(doc_words & query_words)
            scored_docs.append((overlap, doc))
        
        # Sort by relevance and take top-k
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        top_docs = [doc for _, doc in scored_docs[:self.TOP_K]]
        
        return top_docs
    
    def _format_context(self, docs: List[str]) -> str:
        """
        Format retrieved documents into context string.
        
        Optimization: Truncate each document to control token usage.
        """
        if not docs:
            return ""
        
        # Truncate each document
        truncated_docs = [
            truncate_text(doc, self.MAX_DOC_LENGTH)
            for doc in docs
        ]
        
        # Format as numbered list
        context_parts = [
            f"{i+1}. {doc}"
            for i, doc in enumerate(truncated_docs)
        ]
        
        return "\n".join(context_parts)
