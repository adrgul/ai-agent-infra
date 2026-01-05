from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import uuid

from .embeddings import EmbeddingService
from .vectorstore import VectorStore
from .summarizer import Summarizer
from .lister import ParticipantLister


@dataclass
class EmbeddingApp:
    embedding_service: EmbeddingService
    vector_store: VectorStore

    def process_query(self, text: str, k: int = 3) -> dict:
        """Process a user query: get embedding, store it, search for neighbors.

        Returns a dict with the stored id and neighbor list.
        """
        emb = self.embedding_service.get_embedding(text)
        generated_id = str(uuid.uuid4())
        self.vector_store.add(generated_id, text, emb)
        neighbors = self.vector_store.similarity_search(emb, k=k)
        return {"id": generated_id, "neighbors": neighbors}


class CLI:
    def __init__(self, app: EmbeddingApp, summarizer: Summarizer, lister: ParticipantLister):
        self.app = app
        self.summarizer = summarizer
        self.lister = lister

    def run(self) -> None:
       # print("Embedding demo — stores prompts and retrieves nearest neighbors.")
        print("Type 'exit' or 'quit' to end.")
        while True:
            try:
                text = input("Enter a prompt (or 'exit' to quit): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                return
            if text.lower() in ("exit", "quit"):
                print("Goodbye.")
                return
            if not text:
                continue

            summary = self.summarizer.summarize(text, max_words=50)
            names = self.lister.list_names(text)
            result = self.app.process_query(text, k=3)

            print("\nSummary (<=20 words):")
            print(summary)
            print("\nNames found:")
            if names:
                for n in names:
                    print(f"- {n}")
            else:
                print("(no names have been found)")
'''
            print("\nStored prompt and retrieved nearest neighbors:")
            for idx, (nid, dist, ntext) in enumerate(result.get("neighbors", []), start=1):
                print(f"{idx}. (distance={dist:.6f}) \"{ntext}\"")
            print("\n---\n")

'''