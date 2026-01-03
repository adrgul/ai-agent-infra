# Meeting Minutes Embedding CLI (Homework.02)

CLI app 1.0 creating OpenAI embeddings for Company meeting minutes/archives, storing them in a local ChromaDB vector store, and performing nearest-neighbor retrieval.

Quick overview
- Language: Python 3.11+
- Vector DB: ChromaDB (
- Embeddings: OpenAI Embeddings API (model configurable via `.env`)
- CLI: interactive terminal loop

Files
- `app/config.py` — loads `.env` and exposes typed configuration
- `app/embeddings.py` — `EmbeddingService` abstraction and `OpenAIEmbeddingService` implementation
- `app/vector_store.py` — `VectorStore` abstraction and `ChromaVectorStore` implementation
- `app/cli.py` — `EmbeddingApp` orchestration + `CLI` interactive loop
- `app/main.py` — application entrypoint wiring dependencies
- `requirements.txt` — Python dependencies
- `.env.example` — example environment variables


Getting started
---------------

1. Copy `.env.example` to `.env` and fill in your OpenAI API key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

2. Install dependencies (local development):

```bash
pip install -r requirements.txt
```

3. Run the CLI:

```bash
python -m app.main
```

Or build and run in Docker:

```bash
docker build -t embedding-demo .
docker run -it --env-file .env embedding-demo
```

Usage
-----

Type a free-text prompt and press Enter. The app will:
1. Create an embedding for your prompt using the configured OpenAI model.
2. Store the prompt + embedding in the local ChromaDB collection.
3. Run a nearest-neighbor search and display the top results with distances.

Example output:

```
Stored prompt id: 4f2a1b...
Retrieved nearest neighbors:
1. (distance=0.000123) "the current text itself..."
2. (distance=0.123456) "previous similar text..."
3. (distance=0.456789) "another somewhat related text..."
```

Hybrid search
--------------

This project includes a simple hybrid search that combines semantic similarity (OpenAI embeddings + ChromaDB) with classic lexical BM25 ranking using `rank-bm25`.

- Default mode: `hybrid` (weighted combination). Set the semantic weight with `/alpha 0.0..1.0` (1.0 = semantic only, 0.0 = BM25 only).
- You can switch modes at runtime using commands in the CLI:

	- `/mode hybrid` — Combine semantic + BM25 (default)
	- `/mode semantic` — Semantic search only (Chroma similarity)
	- `/mode bm25` — BM25-only lexical search

Example commands while running the CLI:

```text
/mode hybrid
/k 5
/alpha 0.7
What did we decide in the last planning meeting?
```

The hybrid implementation rebuilds an in-memory BM25 index from the stored documents on inserts. For small datasets this is efficient and practical for a demo. For larger datasets consider incremental BM25 updates or a persistent lexical index (Whoosh, Elasticsearch).


Testing
--------------

Unit tests use `pytest`. To run the tests locally:

```bash
pip install -r requirements.txt
pytest -q
```

Notes and next steps
- For teaching purposes the code follows small SOLID-aligned abstractions so different embedding providers or vector stores can be wired in.
- Consider adding `respx` or `pytest-mock` and tests that mock `openai` and `chromadb` for more isolated integration tests.
- Add a small caching layer or an embedding deduplication strategy to avoid repeated OpenAI calls for identical texts.
