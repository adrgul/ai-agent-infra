"""
Infrastructure - Qdrant-based RAG client for production use.
"""
import logging
import os
from typing import List

from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings

from domain.models import Citation, DomainType
from domain.interfaces import IRAGClient

logger = logging.getLogger(__name__)


class QdrantRAGClient(IRAGClient):
    """
    Production Qdrant RAG client.
    Retrieves relevant documents from Qdrant vector database.
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6334",
        collection_name: str = "marketing",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize Qdrant RAG client.
        
        Args:
            qdrant_url: Qdrant server URL
            collection_name: Qdrant collection name
            embedding_model: OpenAI embedding model
        """
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info(f"QdrantRAGClient initialized: {qdrant_url}, collection={collection_name}")

    async def retrieve_for_domain(
        self, domain: str, query: str, top_k: int = 5
    ) -> List[Citation]:
        """
        Retrieve relevant documents for a domain from Qdrant.
        
        Args:
            domain: Domain type (hr, it, finance, legal, marketing, general)
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            List of citations with relevance scores
        """
        try:
            domain_enum = DomainType(domain.lower())
        except ValueError:
            domain_enum = DomainType.GENERAL
            logger.warning(f"Invalid domain '{domain}', using GENERAL")

        # Marketing domain uses Qdrant
        if domain_enum == DomainType.MARKETING:
            return await self._retrieve_from_qdrant(query, top_k)
        
        # Other domains fall back to mock data (for now)
        return await self._retrieve_mock_data(domain_enum, query, top_k)

    async def _retrieve_from_qdrant(self, query: str, top_k: int) -> List[Citation]:
        """
        Retrieve documents from Qdrant using semantic search.
        
        Args:
            query: User query
            top_k: Number of results
            
        Returns:
            List of citations from Qdrant
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )
            
            # Convert to Citations
            citations = []
            for point in search_results:
                payload = point.payload
                citations.append(
                    Citation(
                        doc_id=payload.get("file_id", "UNKNOWN"),
                        title=payload.get("file_name", "Unknown Document"),
                        score=float(point.score),
                        url=None,
                        content=payload.get("text", "")  # Include chunk text for generation
                    )
                )
            
            logger.info(f"Retrieved {len(citations)} docs from Qdrant for query: {query[:50]}...")
            return citations
            
        except Exception as e:
            logger.error(f"Qdrant retrieval error: {e}", exc_info=True)
            return []

    async def _retrieve_mock_data(self, domain: DomainType, query: str, top_k: int) -> List[Citation]:
        """
        Fallback mock data for non-marketing domains.
        TODO: Implement Qdrant collections for other domains.
        """
        mock_kb = {
            DomainType.HR: [
                Citation(
                    doc_id="HR-POL-001",
                    title="Vacation Policy",
                    score=0.94,
                    url=None,
                    content="Szabadságkérés minimum 2 héttel előre kell jelezni. Éves szabadság: 25 munkanap."
                ),
                Citation(
                    doc_id="HR-POL-002",
                    title="Benefits Package",
                    score=0.88,
                    url=None,
                    content="Egészségügyi biztosítás, cafeteria rendszer, home office lehetőség."
                ),
            ],
            DomainType.IT: [
                Citation(
                    doc_id="IT-KB-234",
                    title="VPN Troubleshooting Guide",
                    score=0.91,
                    url=None,
                    content="VPN problémák: 1. Ellenőrizd a kliens fut-e 2. Újraindítás 3. IT helpdesk"
                ),
                Citation(
                    doc_id="IT-KB-189",
                    title="VPN Client Installation",
                    score=0.87,
                    url=None,
                    content="VPN kliens telepítés: Cisco AnyConnect letöltése, telepítés, konfiguráció."
                ),
            ],
            DomainType.FINANCE: [
                Citation(
                    doc_id="FIN-POL-010",
                    title="Expense Report Guidelines",
                    score=0.92,
                    url=None,
                    content="Költségelszámolás: számla szükséges, jóváhagyás 5 munkanapon belül."
                ),
            ],
        }
        
        docs = mock_kb.get(domain, [])
        logger.info(f"Retrieved {len(docs[:top_k])} mock docs for domain={domain.value}")
        return docs[:top_k]
