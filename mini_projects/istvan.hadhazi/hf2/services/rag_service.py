"""RAG Service - Business Logic (SOLID: Single Responsibility)"""

import logging
from typing import List

from domain.interfaces import VectorStoreInterface, LLMClientInterface, DocumentLoaderInterface
from domain.models import Answer, SearchResult

logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) szolgáltatás"""
    
    def __init__(
        self,
        vector_store: VectorStoreInterface,
        llm_client: LLMClientInterface,
        document_loader: DocumentLoaderInterface
    ):
        """Dependency Injection a SOLID elvek szerint"""
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.document_loader = document_loader
        
        self.top_k = 5  # Top-K dokumentum keresése
        
        logger.info("RAG Service inicializálva")
    
    def load_domain_documents(self, domain_configs: List[dict]) -> dict:
        """Domain dokumentumok betöltése
        
        Args:
            domain_configs: [{"domain": "it", "path": "documents/it"}, ...]
            
        Returns:
            Statisztikák domain-enként
        """
        
        logger.info(f"Dokumentumok betöltése {len(domain_configs)} domain-ből...")
        
        stats = {}
        all_chunks = []
        
        for config in domain_configs:
            domain = config["domain"]
            path = config["path"]
            
            # Dokumentumok betöltése és chunkolása
            chunks = self.document_loader.load_documents(path, domain)
            
            stats[domain] = {
                "chunks": len(chunks),
                "files": len(set(c.source for c in chunks))
            }
            
            all_chunks.extend(chunks)
        
        # Vector store-ba töltés
        if all_chunks:
            logger.info(f"Összesen {len(all_chunks)} chunk hozzáadása a vector store-hoz...")
            self.vector_store.add_chunks(all_chunks)
        
        stats["total_chunks"] = len(all_chunks)
        return stats
    
    def ask_question(self, question: str) -> Answer:
        """Kérdés feldolgozása RAG-gal
        
        1. Vector search - releváns dokumentumok keresése
        2. LLM answer generation - válasz generálás kontextussal
        """
        
        logger.info(f"Kérdés: '{question}'")
        
        # 1. Keresés a vector store-ban
        search_results = self.vector_store.search(question, top_k=self.top_k)
        
        if not search_results:
            logger.warning("Nincs releváns dokumentum")
            return Answer(
                question=question,
                answer="Sajnálom, nem találtam releváns információt a kérdésedre a tudásbázisban.",
                sources=[],
                confidence=0.0
            )
        
        logger.info(f"Találatok: {len(search_results)} dokumentum")
        
        # 2. Válasz generálás LLM-mel
        answer_text = self.llm_client.generate_answer(question, search_results)
        
        # Confidence a legjobb score alapján
        confidence = max(r.score for r in search_results)
        
        return Answer(
            question=question,
            answer=answer_text,
            sources=search_results,
            confidence=confidence
        )
    
    def get_stats(self) -> dict:
        """Vector store statisztikák"""
        return self.vector_store.get_collection_stats()

