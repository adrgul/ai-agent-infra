import os
from typing import List, Tuple
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

class RetrieverService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.index_name = "knowledge-router"
        
        # Domain-specifikus k értékek (hány dokumentumot kérünk vissza)
        self.domain_k_values = {
            "hr": 5,          # HR dokumentumok általában hosszabbak, több kontextust kérünk
            "it": 3,          # IT dokumentumok tömörebbek
            "finance": 4,
            "legal": 5,       # Jogi dokumentumok részletesebbek
            "marketing": 3,
            "general": 3
        }
        
    def get_vector_store(self, namespace: str):
        """Returns a VectorStore for a specific namespace."""
        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace,
            pinecone_api_key=os.getenv("PINECONE_API_KEY")
        )
    
    async def retrieve(self, query: str, domain: str, k: int = None) -> List[Document]:
        """
        Retrieves relevant documents from the specified domain (namespace).
        Returns documents sorted by relevance.
        """
        valid_namespaces = ["hr", "it", "finance", "legal", "marketing", "general"]
        
        # If domain is not valid, fallback to general or return empty
        if domain not in valid_namespaces:
            print(f"Warning: Domain '{domain}' not in known namespaces. Defaulting to general.")
            namespace = "general"
        else:
            namespace = domain
        
        # Use domain-specific k value if not provided
        if k is None:
            k = self.domain_k_values.get(domain, 3)
            
        vector_store = self.get_vector_store(namespace)
        
        # Async retrieval with scores
        # Note: asimilarity_search_with_score is not available in all versions,
        # so we use asimilarity_search and calculate scores separately if needed
        docs = await vector_store.asimilarity_search(query, k=k)
        return docs
    
    async def retrieve_with_scores(self, query: str, domain: str, k: int = None) -> List[Tuple[Document, float]]:
        """
        Retrieves relevant documents with similarity scores.
        Returns list of (Document, score) tuples.
        Higher score = more relevant.
        """
        valid_namespaces = ["hr", "it", "finance", "legal", "marketing", "general"]
        
        if domain not in valid_namespaces:
            print(f"Warning: Domain '{domain}' not in known namespaces. Defaulting to general.")
            namespace = "general"
        else:
            namespace = domain
        
        if k is None:
            k = self.domain_k_values.get(domain, 3)
            
        vector_store = self.get_vector_store(namespace)
        
        # Use similarity_search_with_score if available
        # Fallback to regular search if not
        try:
            # Try to get scores using Pinecone's native method
            results = await vector_store.asimilarity_search_with_score(query, k=k)
            return results
        except AttributeError:
            # Fallback: retrieve without scores
            docs = await vector_store.asimilarity_search(query, k=k)
            # Assign default score of 1.0 if scores not available
            return [(doc, 1.0) for doc in docs]
