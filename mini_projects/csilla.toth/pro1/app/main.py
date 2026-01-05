from __future__ import annotations

import openai

from .config import load_config
from .summarizer import OpenAISummarizer
from .lister import OpenAIListParticipants
from .embeddings import OpenAIEmbeddingService
from .vectorstore import ChromaVectorStore, InMemoryVectorStore
from .cli import EmbeddingApp, CLI


def main() -> int:
    cfg = load_config()
    openai.api_key = cfg.openai_api_key

    summarizer = OpenAISummarizer(model=cfg.openai_model)
    lister = OpenAIListParticipants(model=cfg.openai_model)
    embedding_service = OpenAIEmbeddingService(model=cfg.embedding_model)

    try:
        vector_store = ChromaVectorStore(
            persist_directory=cfg.chroma_dir, collection_name=cfg.chroma_collection
        )
    except Exception:
        print("Warning: ChromaVectorStore unavailable, falling back to in-memory store.")
        vector_store = InMemoryVectorStore()

    app = EmbeddingApp(embedding_service=embedding_service, vector_store=vector_store)
    cli = CLI(app=app, summarizer=summarizer, lister=lister)
    cli.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
