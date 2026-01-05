"""Embedding CLI application entrypoint.

Usage:
1. Copy `.env.example` -> `.env` and set `OPENAI_API_KEY`.
2. Build (optional): `docker build -t embedding-demo .`
3. Run local (without Docker): `python -m app.main`
4. Run in Docker: `docker run -it --env-file .env embedding-demo`

The app starts an interactive CLI where you can enter prompts. Each prompt
is embedded with OpenAI, stored in ChromaDB and a nearest-neighbor search
is executed immediately.
"""
from __future__ import annotations

import logging
import sys

from .config import load_config
from .embeddings import OpenAIEmbeddingService
from .vector_store import ChromaVectorStore
from .cli import CLI
import os


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Load configuration (reads .env)
    try:
        cfg = load_config()
    except Exception as exc:
        logging.error("Configuration error: %s", exc)
        return 1

    # Instantiate services (dependencies injected)
    emb_service = OpenAIEmbeddingService(api_key=cfg.openai_api_key, model=cfg.embedding_model)
    vector_store = ChromaVectorStore(persist_dir=cfg.chroma_persist_dir)

    cli = CLI(emb_service=emb_service, vector_store=vector_store)
    # If a `data/` directory exists in the current working directory, process files in batch mode.
    data_dir = os.path.join(os.getcwd(), "data")
    try:
        if os.path.isdir(data_dir) and any(os.scandir(data_dir)):
            # batch processing from data directory
            cli.process_directory(data_dir)
        else:
            cli.run()
    except KeyboardInterrupt:
        print("\nExiting...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
