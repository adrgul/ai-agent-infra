import uuid
import chromadb
from chromadb.config import Settings
from application.markdown_chunker import MarkdownRAGChunker

class VectorStore:
    def __init__(self, openai_gateway):
        self.openai_gateway = openai_gateway
        self.chroma_db_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
        ))
        self.collection = self.chroma_db_client.create_collection(name="in_memory_collection")
        self.chunker = MarkdownRAGChunker(chunk_size=800, overlap=150)

    def init(self, files):
        for file in files:
            chunks = self.chunker.process_file(file)
            for chunk in chunks:
                percentage = (chunks.index(chunk) + 1) / len(chunks) * 100
                print(f"\rGenerating embedding for the file... {percentage:.0f}%", end="")
                self.add_vector(chunk['text'], metadata={"source": file})
            print(" ✓ Done!\n")

    def add_vector(self, text, metadata):
        # Placeholder for adding vector to the store
        query_id = str(uuid.uuid4())
        vector = self.openai_gateway.get_embedding(text)
        self.collection.add(
            ids=[query_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata or {}]
        )

    def search(self, text, top_k=5):
        vector = self.openai_gateway.get_embedding(text)
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k)

        return {
            "texts": results['documents'][0],
            "sources": list(set([meta['source'] for meta in results['metadatas'][0]])),
        }