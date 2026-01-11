# KB Folder-Based Ingestion

Automatic document ingestion from the `docs/kb-data/` folder with incremental updates, PDF support, and comprehensive testing.

## Overview

This system automatically:
1. Scans `docs/kb-data/` for documents (PDF, TXT, MD)
2. Detects new, changed, or removed files via SHA256 hashing
3. Chunks, embeds, and indexes documents into ChromaDB + BM25
4. Runs on startup (configurable) and via API endpoints
5. Maintains version tracking for efficient incremental updates

## Architecture

```
docs/kb-data/           ← Place your knowledge documents here
    python_guide.md
    docker_guide.md
    tutorial.pdf

backend/rag/ingestion/
    scanner.py          ← File discovery & hashing
    pdf_parser.py       ← PDF text extraction
    version_store.py    ← Version tracking (JSON)
    kb_indexer.py       ← Orchestrator (scan → parse → chunk → embed → index)
```

## Usage

### 1. Add Documents to KB Folder

Place PDF, TXT, or MD files in `docs/kb-data/`:

```bash
cp my_guide.pdf docs/kb-data/
```

### 2. Automatic Ingestion on Startup

By default (`KB_INGEST_ON_STARTUP=true`), the app ingests KB documents when it starts:

```bash
docker-compose up
```

Logs will show:
```
INFO: KB ingest_on_startup enabled; initializing indexer
INFO: Scanned docs/kb-data: found 3 documents
INFO: KB scan: 3 new, 0 updated, 0 removed
INFO: Startup KB ingestion complete: {'new': 3, 'updated': 0, 'removed': 0, 'total_chunks': 42}
```

### 3. Manual Ingestion via API

#### Incremental Ingestion
Only processes changed documents:

```bash
curl -X POST "http://localhost:8000/admin/kb/ingest_incremental" \
  -H "token: $ADMIN_TOKEN"
```

#### Full Reindex
Clears version tracking and reindexes everything:

```bash
curl -X POST "http://localhost:8000/admin/kb/reindex_full" \
  -H "token: $ADMIN_TOKEN"
```

### 4. Update a Document

Modify a file in `kb-data/`, then trigger incremental ingestion. Only the changed file is reprocessed.

### 5. Remove a Document

Delete a file from `kb-data/`, then run incremental ingestion. Chunks are removed from the index.

## Configuration

Environment variables (`.env` or `docker-compose.yml`):

```bash
# KB folder path (relative to backend working dir)
KB_DATA_DIR=docs/kb-data

# Version tracking file
KB_VERSION_STORE=.kb_versions.json

# Auto-ingest on startup
KB_INGEST_ON_STARTUP=true

# Chunking config
CHUNK_SIZE=800
CHUNK_OVERLAP=128

# ChromaDB persistence
CHROMA_DIR=.chroma
CHROMA_PERSIST=true
```

## How It Works

### File Scanning
- Recursively scans `KB_DATA_DIR` for `.pdf`, `.txt`, `.md`
- Computes SHA256 hash for each file
- Derives stable `doc_id` from relative path (e.g., `subdir_file.pdf`)

### Change Detection
- Compares current file hash with `VersionStore` (JSON file)
- **New**: doc_id not tracked → index it
- **Updated**: hash changed → delete old chunks, reindex
- **Removed**: file gone → delete chunks

### Chunking
- Deterministic character-based chunking with overlap
- Metadata preserved: `doc_id`, `title`, `source`, `doc_type`, `version_hash`, `chunk_index`, `page` (PDF)

### Embedding & Indexing
- Embeddings: HashEmbedder (test) or SentenceTransformer (prod)
- Dense index: ChromaDB (persistent vector store)
- Sparse index: BM25 (in-memory, rebuilt on restart)
- Hybrid retrieval: weighted merge of dense + sparse scores

## Testing

### Unit Tests
```bash
pytest backend/tests/test_kb_scanner.py
pytest backend/tests/test_kb_version_store.py
pytest backend/tests/test_kb_pdf_parser.py
```

### Integration Tests
```bash
pytest backend/tests/test_kb_integration.py
```

Tests cover:
- File hashing determinism
- Change detection
- Incremental updates (new/changed/removed docs)
- Full reindex
- Canary document retrieval

### Golden Retrieval Test
```bash
pytest backend/tests/test_kb_golden_retrieval.py
```

Validates Recall@k for 10 golden queries against 3 test documents.

## Troubleshooting

### Documents not indexed
- Check `KB_DATA_DIR` path is correct
- Ensure files have supported extensions (`.pdf`, `.txt`, `.md`)
- Check logs for parsing errors
- Verify `KB_INGEST_ON_STARTUP=true` or trigger manual ingestion

### PDF parsing fails
- Ensure `pypdf` is installed: `pip install pypdf`
- Check PDF is not encrypted or corrupted
- Review logs for detailed error messages

### Chunks not appearing in retrieval
- Verify chunks indexed: check `dense.storage` or ChromaDB collection size
- Test with unique token (canary test pattern)
- Check embedding model consistency

### Version store out of sync
- Full reindex clears and rebuilds: `POST /admin/kb/reindex_full`
- Manually delete `.kb_versions.json` and restart

## Example: Add a New Guide

1. Create `docs/kb-data/api_tutorial.md`:
```markdown
# API Tutorial

This guide covers FastAPI endpoints...
```

2. Restart app or call `/admin/kb/ingest_incremental`

3. Query the agent: "How do I use the API?"

4. Response should cite `api_tutorial.md`

## Production Considerations

- **Embedder**: Switch from HashEmbedder to SentenceTransformer for semantic search
- **Sparse Index**: Persist BM25 index to disk or use Elasticsearch
- **Async Ingestion**: Offload large reindex jobs to background workers
- **Monitoring**: Track ingestion stats, chunk counts, retrieval latencies
- **Backup**: Snapshot ChromaDB and version store regularly

## SOLID Principles Applied

- **SRP**: Each module has one responsibility (scanner, parser, chunker, indexer)
- **OCP**: Parsers/chunkers extensible behind interfaces
- **DIP**: Dependencies injected (config, embedder, retrievers)
- **Comments**: Extensive "why" explanations throughout code
