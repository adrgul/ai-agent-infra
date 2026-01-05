"""OpenAI LLM Client Implementation"""

import os
import logging
from typing import List
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from domain.interfaces import LLMClientInterface
from domain.models import SearchResult

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClientInterface):
    """OpenAI API client implementation"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY környezeti változó nincs beállítva!")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI client inicializálva - Model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_answer(
        self, 
        question: str, 
        context_chunks: List[SearchResult]
    ) -> str:
        """Válasz generálás RAG kontextussal"""
        
        # Kontextus összeállítása
        context = self._build_context(context_chunks)
        
        # System prompt
        system_prompt = """Te egy intelligens tudásbázis asszisztens vagy.
A felhasználó kérdéseire a rendelkezésre álló dokumentumok alapján válaszolsz.

Fontos szabályok:
1. Csak a megadott kontextus alapján válaszolj
2. Ha a válasz nem található a kontextusban, mondd hogy nem tudod
3. Hivatkozz a forrás dokumentumokra: [domain/file.md]
4. Adj tömör, pontos válaszokat
5. Magyar nyelven válaszolj"""
        
        # User prompt
        user_prompt = f"""Kontextus dokumentumok:

{context}

---

Kérdés: {question}

Válasz:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"Válasz generálva: {len(answer)} karakter")
            return answer
            
        except Exception as e:
            logger.error(f"Hiba a válaszgenerálásban: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """Text embedding generálás"""
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Embedding generálva: {len(embedding)} dimenzió")
            return embedding
            
        except Exception as e:
            logger.error(f"Hiba az embedding generálásban: {e}")
            raise
    
    def _build_context(self, results: List[SearchResult]) -> str:
        """Kontextus string építése search results-ból"""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            chunk = result.chunk
            score = result.score
            
            context_parts.append(
                f"[{i}] Forrás: {chunk.domain}/{chunk.source} (relevancia: {score:.2f})\n"
                f"{chunk.content}\n"
            )
        
        return "\n---\n\n".join(context_parts)

