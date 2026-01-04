"""LangGraph agent for RAG orchestration."""

from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph
import asyncio
import unicodedata

from domain.models import CategoryDecision, Message, MessageRole, RetrievedChunk
from domain.interfaces import (
    CategoryRouter, EmbeddingService, VectorStore,
    RAGAnswerer, ActivityCallback
)


def _slugify_collection_name(text: str) -> str:
    """
    Convert category name to valid ChromaDB collection slug.
    Only alphanumeric, underscore, hyphen allowed.
    Must be 3-63 chars, start/end with alphanumeric.
    Matches the implementation in upload_service.py
    """
    # Normalize unicode chars to ASCII (é -> e, etc.)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Lowercase and replace spaces/slashes with underscore
    text = text.lower().replace(" ", "_").replace("/", "_")
    
    # Remove non-alphanumeric except underscore and hyphen
    text = ''.join(c if c.isalnum() or c in '_-' else '' for c in text)
    
    # Trim underscores/hyphens from start/end
    text = text.strip('_-')
    
    # Ensure minimum 3 chars
    if len(text) < 3:
        text = text + 'x' * (3 - len(text))
    
    # Truncate if too long
    if len(text) > 63:
        text = text[:63]
    
    return text


def create_rag_agent(
    category_router: CategoryRouter,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    rag_answerer: RAGAnswerer,
):
    """
    Create LangGraph agent with nodes:
    1. category_decide: Route question to category
    2. retrieve: Get context from vector DB
    3. generate: Generate answer with citations
    """

    def category_decide_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 1: LLM-based category decision (sync wrapper)."""
        question = state["question"]
        available_categories = state["available_categories"]

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            decision = loop.run_until_complete(
                category_router.decide_category(question, available_categories)
            )
        finally:
            loop.close()

        state["routed_category"] = decision.category
        state["category_reason"] = decision.reason

        return state

    def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 2: Retrieve context from vector DB (sync wrapper)."""
        routed_category = state.get("routed_category")
        question = state["question"]
        available_categories = state["available_categories"]

        # If no category matched, return empty context
        if not routed_category or routed_category not in available_categories:
            state["context_chunks"] = []
            state["retrieve_status"] = "no_category"
            return state

        # Embed question
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            question_embedding = loop.run_until_complete(
                embedding_service.embed_text(question)
            )
        finally:
            loop.close()

        # Query category collection using proper slugification (matches upload_service)
        category_slug = _slugify_collection_name(routed_category)
        collection_name = f"cat_{category_slug}"

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                chunks = loop.run_until_complete(
                    vector_store.query(
                        collection_name, question_embedding, top_k=5
                    )
                )
            finally:
                loop.close()
            
            state["context_chunks"] = chunks
            state["retrieve_status"] = "success"
        except Exception as e:
            state["context_chunks"] = []
            state["retrieve_status"] = f"error: {str(e)}"

        return state

    def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 3: Generate answer with citations (sync wrapper)."""
        question = state["question"]
        context_chunks = state.get("context_chunks", [])
        routed_category = state.get("routed_category")
        activity_callback = state.get("activity_callback")

        # If no context in routed category, try all categories as fallback
        if not context_chunks or not routed_category:
            # Try searching in all categories instead of just the routed one
            available_categories = state.get("available_categories", [])
            
            fallback_chunks = []
            
            # Log: Fallback search
            if activity_callback:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        activity_callback.log_activity(
                            f"🔄 Fallback keresés: összes kategóriában",
                            activity_type="processing"
                        )
                    )
                finally:
                    loop.close()
            
            # Search across all categories
            for category in available_categories:
                if category.lower() != (routed_category or "").lower():
                    category_slug = _slugify_collection_name(category)
                    collection_name = f"cat_{category_slug}"
                    
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            # Embed question for search
                            question_embedding = loop.run_until_complete(
                                embedding_service.embed_text(question)
                            )
                            # Query this category
                            chunks = loop.run_until_complete(
                                vector_store.query(
                                    collection_name, question_embedding, top_k=3
                                )
                            )
                            fallback_chunks.extend(chunks)
                        finally:
                            loop.close()
                    except Exception:
                        # Skip categories with errors
                        pass
            
            # If we found chunks in other categories, use them
            if fallback_chunks:
                context_chunks = fallback_chunks
                state["context_chunks"] = fallback_chunks
                state["fallback_search"] = True
            else:
                # No documents found anywhere
                state["final_answer"] = (
                    "Nincs ilyen kategóriájú dokumentum feltöltve, "
                    "nem tudok a feltöltött dokumentumok alapján válaszolni."
                )
                state["fallback_search"] = False
                return state

        # Log: Document search completed
        if activity_callback:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    activity_callback.log_activity(
                        f"📚 Dokumentumok lekérése: {len(context_chunks)} chunk",
                        activity_type="success",
                        metadata={
                            "chunk_count": len(context_chunks),
                            "average_distance": sum(c.distance for c in context_chunks) / len(context_chunks) if context_chunks else 0
                        }
                    )
                )
            finally:
                loop.close()

        # Deduplicate near-duplicate chunks (simple: keep first)
        unique_chunks = []
        seen_contents = set()
        for chunk in context_chunks:
            # Simple dedup: if content hash seen, skip
            content_hash = hash(chunk.content[:100])
            if content_hash not in seen_contents:
                unique_chunks.append(chunk)
                seen_contents.add(content_hash)

        # Log: Answer generation start
        if activity_callback:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    activity_callback.log_activity(
                        f"🤖 Válasz generálása OpenAI API-val...",
                        activity_type="processing"
                    )
                )
            finally:
                loop.close()

        # Generate answer
        # If fallback search was used, indicate to LLM that search was across all documents
        category_for_prompt = routed_category if not state.get("fallback_search") else "Keresés az összes dokumentumban"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            answer = loop.run_until_complete(
                rag_answerer.generate_answer(question, unique_chunks, category_for_prompt)
            )
        finally:
            loop.close()
        
        state["final_answer"] = answer

        return state

    # Build graph
    workflow = StateGraph(dict)

    workflow.add_node("category_decide", category_decide_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("category_decide")
    workflow.add_edge("category_decide", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.set_finish_point("generate")

    return workflow.compile()


class RAGAgent:
    """High-level RAG agent interface."""

    def __init__(self, compiled_graph):
        self.graph = compiled_graph

    async def answer_question(
        self,
        user_id: str,
        question: str,
        available_categories: List[str],
        activity_callback: Optional[ActivityCallback] = None,
    ) -> Dict[str, Any]:
        """
        Run agent to answer question.
        Returns final_answer, routed_category, context_chunks, etc.
        """
        initial_state = {
            "user_id": user_id,
            "question": question,
            "available_categories": available_categories,
            "routed_category": None,
            "context_chunks": [],
            "final_answer": "",
            "fallback_search": False,
            "activity_callback": activity_callback,  # Pass callback through state
        }

        # Invoke graph (sync invoke since nodes are sync wrappers)
        result = self.graph.invoke(initial_state)

        return {
            "final_answer": result.get("final_answer", ""),
            "routed_category": result.get("routed_category"),
            "context_chunks": result.get("context_chunks", []),
            "fallback_search": result.get("fallback_search", False),
            "memory_snapshot": {
                "routed_category": result.get("routed_category"),
                "available_categories": available_categories,
            }
        }
