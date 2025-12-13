"""
Document re-ranking for SupportAI.

Re-ranks retrieved documents for better relevance using Cohere or LLM.
"""

import json
from typing import List, Dict, Any

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..utils.config import settings
from ..utils.logger import get_logger
from ..templates.prompts import get_prompt_template

logger = get_logger(__name__)


class Reranker:
    """Document re-ranking service."""

    def __init__(self, method: str = "cohere"):
        self.method = method

        if method == "cohere":
            if not COHERE_AVAILABLE:
                raise ImportError("Cohere client not available. Install with: pip install cohere")
            self.cohere_client = cohere.Client(api_key=settings.cohere_api_key)
        elif method == "llm":
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.0,  # Deterministic scoring
                api_key=settings.openai_api_key
            )
        else:
            raise ValueError(f"Unsupported reranking method: {method}")

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents by relevance to query.

        Args:
            query: Search query
            documents: List of document dictionaries
            top_k: Number of top documents to return

        Returns:
            Re-ranked documents with relevance scores
        """
        if not documents:
            return []

        try:
            logger.info(f"Re-ranking {len(documents)} documents using {self.method}")

            if self.method == "cohere":
                reranked = await self._rerank_cohere(query, documents, top_k)
            elif self.method == "llm":
                reranked = await self._rerank_llm(query, documents, top_k)
            else:
                reranked = documents[:top_k]  # Fallback to original order

            # Add relevance scores and filter
            scored_docs = []
            for doc in reranked:
                score = doc.get("relevance_score", doc.get("score", 0.5))
                if score >= 0.3:  # Minimum relevance threshold
                    doc["score"] = score
                    scored_docs.append(doc)

            logger.info(f"Re-ranked to {len(scored_docs)} relevant documents")
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"Re-ranking failed: {str(e)}")
            # Return original documents with default scores
            for doc in documents[:top_k]:
                doc["score"] = 0.5
            return documents[:top_k]

    async def _rerank_cohere(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Re-rank using Cohere Rerank API."""
        # Prepare documents for Cohere
        doc_texts = []
        doc_mapping = []

        for doc in documents:
            content = doc.get("content", "")
            title = doc.get("title", "")
            text = f"{title}\n{content}" if title else content

            if text.strip():
                doc_texts.append(text[:5000])  # Cohere limit
                doc_mapping.append(doc)

        if not doc_texts:
            return []

        # Call Cohere API
        response = self.cohere_client.rerank(
            query=query,
            documents=doc_texts,
            top_n=top_k,
            model="rerank-english-v2.0"
        )

        # Reconstruct documents with scores
        reranked = []
        for result in response.results:
            original_doc = doc_mapping[result.index].copy()
            original_doc["relevance_score"] = result.relevance_score
            reranked.append(original_doc)

        return reranked

    async def _rerank_llm(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Re-rank using LLM scoring."""
        # Prepare prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("reranking"))

        # Format documents for prompt
        docs_text = "\n\n".join([
            f"Document {i+1}:\n{doc.get('title', 'Untitled')}\n{doc.get('content', '')[:1000]}..."
            for i, doc in enumerate(documents)
        ])

        chain = prompt | self.llm

        # Get rankings
        response = await chain.ainvoke({
            "query": query,
            "documents": docs_text
        })

        # Parse JSON response
        try:
            rankings = json.loads(response.content.strip())
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM reranking response")
            # Fallback: assign equal scores
            for doc in documents:
                doc["relevance_score"] = 0.5
            return documents

        # Apply scores to documents
        scored_docs = []
        for ranking in rankings:
            doc_id = ranking.get("doc_id")
            score = ranking.get("score", 0)

            # Find matching document
            for doc in documents:
                if str(doc.get("doc_id", "")) == str(doc_id):
                    doc_copy = doc.copy()
                    doc_copy["relevance_score"] = min(max(score / 10.0, 0.0), 1.0)  # Normalize 0-10 to 0-1
                    scored_docs.append(doc_copy)
                    break

        # Sort by score descending
        scored_docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return scored_docs[:top_k]


# Global reranker instance
reranker = Reranker(method="cohere" if settings.cohere_api_key else "llm")