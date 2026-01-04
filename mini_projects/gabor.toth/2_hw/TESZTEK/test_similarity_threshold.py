#!/usr/bin/env python3
"""Test the 0.6 similarity threshold for irrelevant queries."""
import asyncio
import os
import sys
sys.path.insert(0, 'backend')

from infrastructure.vector_store import ChromaVectorStore
from infrastructure.embedding import OpenAIEmbeddingService

async def test_threshold():
    """Test with irrelevant query."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv('.env')
        api_key = os.environ.get('OPENAI_API_KEY')
    
    embedding_service = OpenAIEmbeddingService(api_key=api_key)
    vector_store = ChromaVectorStore(persist_directory="data/chroma_db")
    
    # Get available collections
    collections = vector_store.client.list_collections()
    print(f"Available collections: {[c.name for c in collections]}")
    
    if not collections:
        print("\n⚠️  No collections found. Upload some documents first!")
        return
    
    collection_name = collections[0].name
    print(f"\n✅ Using collection: {collection_name}")
    
    # Test query
    test_queries = [
        "Mi India fővárosa?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("="*60)
        
        # Get embedding for query
        query_embedding = await embedding_service.embed_text(query)
        
        # Query with 0.6 threshold
        results = await vector_store.query(
            collection_name, 
            query_embedding, 
            top_k=5, 
            similarity_threshold=0.6
        )
        
        if not results:
            print("✅ NO DOCUMENTS FOUND (threshold filter working!)")
            print("   → RAG answerer should show: 'A mellékelt dokumentumok nem tartalmaznak...'")
        else:
            print(f"Found {len(results)} chunks:")
            for chunk in results:
                dist = chunk.metadata.get('distance', 'N/A')
                print(f"  - distance: {dist:.3f}")

if __name__ == "__main__":
    asyncio.run(test_threshold())
