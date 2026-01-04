import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

def setup_pinecone():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in environment variables.")
        return

    pc = Pinecone(api_key=api_key)
    
    index_name = "knowledge-router"
    
    # Check if index exists
    if index_name not in pc.list_indexes().names():
        print(f"Creating index '{index_name}'...")
        try:
            pc.create_index(
                name=index_name,
                dimension=1536, # OpenAI embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print("Index created successfully.")
            # Wait for index to be ready
            while not pc.describe_index(index_name).status['ready']:
                time.sleep(1)
        except Exception as e:
            print(f"Failed to create index: {e}")
            return
    else:
        print(f"Index '{index_name}' already exists.")

    # Initialize connection to index
    index = pc.Index(index_name)
    
    # Define namespaces to verify connection
    namespaces = ["hr", "it", "finance", "legal", "marketing", "general"]
    
    print(f"Pinecone setup complete. Namespaces ready to use: {namespaces}")
    print(f"Index stats: {index.describe_index_stats()}")

if __name__ == "__main__":
    setup_pinecone()
