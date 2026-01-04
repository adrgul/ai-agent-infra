from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from services.llm import get_llm
from domain.models import Citation

class ResponseGenerator:
    def __init__(self):
        self.llm = get_llm(model="gpt-4o", temperature=0.3)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful corporate assistant.
Answer the user's question based ONLY on the provided context.
If the answer is not in the context, say "I don't have enough information in the {domain} knowledge base to answer that."

When referencing information from the context, mention the source document in your answer.

Context:
{context}

Domain: {domain}
"""),
            ("user", "{query}")
        ])
        
    async def generate_response(self, query: str, docs: List[Document], domain: str) -> str:
        """Generates an answer based on retrieved documents."""
        
        # Format context with source information
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'unknown')
            content = doc.page_content
            context_parts.append(f"[Source {i}: {source}]\n{content}")
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        chain = self.prompt | self.llm
        
        response = await chain.ainvoke({
            "query": query,
            "context": context_text,
            "domain": domain.upper()
        })
        
        return response.content
    
    def extract_citations(self, docs: List[Document], scores: List[float] = None) -> List[Citation]:
        """
        Extracts citation information from retrieved documents.
        
        Args:
            docs: List of retrieved documents
            scores: Optional list of relevance scores (same order as docs)
        
        Returns:
            List of Citation objects
        """
        citations = []
        
        for i, doc in enumerate(docs):
            metadata = doc.metadata
            score = scores[i] if scores and i < len(scores) else 1.0
            
            # Normalize score to 0.0-1.0 range if needed
            # Pinecone scores are typically 0.0-1.0, but check if they need normalization
            normalized_score = min(max(score, 0.0), 1.0)
            
            # Extract document ID (use source + chunk index if available)
            doc_id = metadata.get('id', f"doc_{i}")
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', source) or source
            
            # Get snippet (first 200 characters of content)
            snippet = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            
            citation = Citation(
                doc_id=doc_id,
                title=title,
                score=normalized_score,
                snippet=snippet,
                url=metadata.get('url'),
                source=source
            )
            citations.append(citation)
        
        return citations
