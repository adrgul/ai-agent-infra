"""RAG answer generator implementation."""

from typing import List
import openai

from domain.models import RetrievedChunk
from domain.interfaces import RAGAnswerer


class OpenAIRAGAnswerer(RAGAnswerer):
    """RAG answer generator using OpenAI Chat Completions."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_answer(
        self, question: str, context_chunks: List[RetrievedChunk],
        category: str
    ) -> str:
        """Generate answer from context chunks with citations."""
        # Handle case when no relevant documents found
        has_documents = context_chunks and len(context_chunks) > 0
        
        if not has_documents:
            # No documents - return the specific message
            return "A mellékelt dokumentumok nem tartalmaznak információt erről a témáról. Kérlek, kérdezz valami mást, amire a dokumentumok alapján tudok válaszolni!"
        
        # Build context string with citations - IMPORTANT: use numbered format [1], [2] etc. to set proper pattern
        context_text = ""
        num_docs = len(context_chunks)
        for i, chunk in enumerate(context_chunks, 1):
            # Use full content, not just snippet
            content = chunk.content if chunk.content else (chunk.snippet or "")
            source = chunk.metadata.get("source_file", "ismeretlen")
            context_text += f"\n[{i}] {source} (chunk: {chunk.chunk_id}):\n{content}\n"

        system_prompt = f"""Te egy magyar dokumentum-alapú AI asszisztens vagy.

⚠️⚠️⚠️ KRITIKUS - HIVATKOZÁSI FORMAT KÖTELEZŐEN: ⚠️⚠️⚠️

MINDEN VÁLASZODBAN EZZEL A FORMÁTUMMAL hivatkozz:
[1. forrás]
[2. forrás]
[3. forrás]

Ez SZÓ SZERINT így néz ki a válaszban:
"A RAG adatbázisban az első forrás [1. forrás] szerint... A második forrás [2. forrás] mutatja, hogy..."

❌ TILOS FORMÁTUMOK (ezeket SOHA ne használd):
- [i. forrás] - ROSSZ!
- [forrás i] - ROSSZ!
- [1] - HIÁNYOS!
- forrás 1 - ROSSZ!
- (1. forrás) - ROSSZ!

✅ EGYETLEN HELYES FORMAT:
[1. forrás], [2. forrás], [3. forrás]

SZABÁLYOK:
1. CSAK az alábbi {num_docs} dokumentumból válaszolj
2. MINDEN mondatod után KÖTELEZŐEN egy [N. forrás] hivatkozás
3. N = a dokumentum sorszáma (1, 2, 3, ... stb.)
4. Rövid, 2-4 mondatos válasz
5. Magyaros nyelvezet

Kategória: {category}
"""

        prompt = f"""📚 {num_docs} DOKUMENTUM:
{context_text}

❓ FELHASZNÁLÓ KÉRDÉSE: {question}

📋 VÁLASZADÁS:
- Csak az {num_docs} dokumentumból dolgozz
- Minden hivatkozás formátuma: [1. forrás], [2. forrás], stb.
- Nem lehet [i. forrás], csak [1. forrás], [2. forrás]
- Rövid válasz

Válaszod kezdje azonnal a választ, ne jelöléssel:"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()
