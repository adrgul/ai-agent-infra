# Meeting Minutes Embedding CLI (Homework.02)

CLI app 1.0 that creates OpenAI embeddings for company meeting minutes (or any text files), stores them in a local ChromaDB vector store, and performs nearest-neighbor retrieval. The project supports two modes of operation:

- Batch mode (default when a `data/` directory exists): reads `.md`/`.txt` files from `./data`, embeds and indexes them, and prints nearest neighbors for each file.
- Interactive mode: when no `data/` folder is present, the app starts an interactive prompt where you can enter free-text queries which are embedded, stored and searched immediately.

Quick overview
- Language: Python 3.11+
- Vector DB: ChromaDB (duckdb+parquet persistence)
- Embeddings: OpenAI Embeddings API (model configurable via `.env`)
- CLI: interactive terminal loop and batch `data/` processing

Files
- `app/config.py` — loads `.env` and exposes typed configuration
- `app/embeddings.py` — `EmbeddingService` abstraction and `OpenAIEmbeddingService` implementation
- `app/vector_store.py` — `VectorStore` abstraction and `ChromaVectorStore` implementation (semantic + hybrid search)
- `app/cli.py` — `EmbeddingApp` orchestration, interactive CLI and `process_directory` for batch processing
- `app/main.py` — application entrypoint wiring dependencies and auto-detecting `data/` folder
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

3. Prepare data (batch mode):

Place your meeting minute files under `data/` in the project root. Supported file extensions: `.md`, `.txt`.

Example:

```
mini_projects/szlavi.domonkos/Homework.02/data/meeting01.md
mini_projects/szlavi.domonkos/Homework.02/data/meeting02.txt
```

4a. Run in batch mode (auto-detects `./data`):

```bash
python -m app.main
```

4b. Run interactive mode (no `data/` present):

```bash
python -m app.main
```

Or build and run in Docker (mount data dir):

```bash
docker build -t embedding-demo .
docker run -it --env-file .env -v "$PWD/data":/app/data embedding-demo
```

Usage
-----

Batch mode (default when `./data` exists): the app will process each `.md`/`.txt` file in `data/`, embed its contents, store the document and run the configured retrieval (semantic/hybrid/BM25) for that document. Results are printed per file.

Interactive mode: type a free-text prompt and press Enter. The app will:
1. Create an embedding for your prompt using the configured OpenAI model.
2. Store the prompt + embedding in the local ChromaDB collection.
3. Run a nearest-neighbor search and display the top results with scores.

Example output:

```
Stored prompt id: 4f2a1b...
Retrieved nearest neighbors:
1. (score=0.987654) "the current text itself..."
2. (score=0.712345) "previous similar text..."
3. (score=0.456789) "another somewhat related text..."
```

Hybrid & search modes
--------------

This project includes a hybrid search that combines semantic similarity (OpenAI embeddings + ChromaDB) with lexical BM25 ranking using `rank-bm25`.

- Default mode: `hybrid` (weighted combination).
- You can switch modes at runtime using CLI commands (interactive mode):

	- `/mode hybrid` — Combine semantic + BM25 (default)
	- `/mode semantic` — Semantic search only (Chroma similarity)
	- `/mode bm25` — BM25-only lexical search
	- `/k N` — set number of returned neighbors
	- `/alpha X` — set hybrid semantic weight (0.0..1.0)

Example commands while running the interactive CLI:

```text
/mode hybrid
/k 5
/alpha 0.7
What did we decide in the last planning meeting?
```

For batch mode, hybrid parameters are applied to each file using the defaults (mode=`hybrid`, k=3, alpha=0.5). If you need per-file control, consider running interactive mode or extending the batch API.

Testing
--------------

Unit and integration tests use `pytest`. To run the tests locally:

```bash
pip install -r requirements.txt
pytest -q
```

Notes and next steps
- The code follows SOLID-aligned abstractions so different embedding providers or vector stores can be swapped in.
- The BM25 index is maintained incrementally in memory for demo-sized datasets; for large corpora, use a dedicated lexical index (Whoosh/Elasticsearch) or persist BM25 between runs.
- Consider adding CLI flags to configure batch behavior (e.g., `--mode`, `--k`, `--alpha`) or support recursive directory traversal.
