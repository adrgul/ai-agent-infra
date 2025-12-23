# Streamlit + FastAPI RAG Chatbot Demo

A production-shaped demo RAG chatbot with:
- **Frontend**: Streamlit chat UI
- **Backend**: FastAPI REST API with auto-generated OpenAPI docs
- **LLM**: OpenAI via LangChain (gpt-4.1-mini)
- **RAG**: FAISS vector store indexing local Markdown files
- **Observability**: LangSmith tracing + evaluation

## Architecture

```
┌─────────────┐      HTTP      ┌──────────────┐
│  Streamlit  │ ────────────▶  │   FastAPI    │
│     UI      │                │   Backend    │
└─────────────┘                └──────┬───────┘
                                      │
                                      ▼
                               ┌──────────────┐
                               │ FAISS Vector │
                               │    Store     │
                               └──────────────┘
```

## Key Features

- **No conversation history**: Each question is answered independently
- **Markdown-only**: Indexes `data/**/*.md` files
- **Pydantic schemas**: Type-safe request/response contracts
- **Comprehensive tests**: Pytest with fake embeddings/LLM (no network calls)
- **LangSmith integration**: Tracing and evaluation support

## Project Structure

```
repo/
  backend/
    app/
      main.py                 # FastAPI app entry point
      api/                    # API route handlers
        health.py
        ingest.py
        chat.py
      core/                   # Configuration & utilities
        config.py
        logging.py
      rag/                    # RAG pipeline components
        loaders.py
        chunking.py
        embeddings.py
        vectorstore.py
        prompts.py
        chain.py
      schemas/                # Pydantic models
        common.py
        ingest.py
        chat.py
      tests/                  # Pytest tests
        test_health.py
        test_ingest_smoke.py
        test_chat_requires_ingest.py
        test_chat_contract.py
      eval/                   # Evaluation scripts
        run_eval.py
    pyproject.toml
    .env.example
  frontend/
    streamlit_app.py
    .streamlit/
      secrets.toml.example
  data/                       # Put your .md files here
  .vectorstore/               # Generated FAISS index (gitignored)
```

## Local Development

### Prerequisites

- Python 3.10+
- OpenAI API key
- (Optional) LangSmith API key for tracing

### Setup

1. **Clone and install backend dependencies**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Add Markdown documents**:
   ```bash
   # Place your .md files in the data/ directory
   cp your-docs/*.md ../data/
   ```

4. **Run backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The API will be available at http://localhost:8000
   - Swagger docs: http://localhost:8000/docs
   - OpenAPI spec: http://localhost:8000/openapi.json

5. **Run frontend** (in a new terminal):
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```
   The UI will open at http://localhost:8501

### First Time Usage

1. Open the Streamlit UI
2. Click "Ingest docs" in the sidebar to build the FAISS index
3. Start asking questions!

## API Endpoints

### `GET /health`
Check API health status.

**Response**:
```json
{
  "status": "ok"
}
```

### `POST /ingest`
Build or rebuild the FAISS vector index from Markdown files.

**Request**:
```json
{
  "force_rebuild": false  // Optional, default: false
}
```

**Response**:
```json
{
  "indexed_files": 3,
  "chunk_count": 42,
  "vectorstore_dir": "../.vectorstore/faiss_index",
  "filenames": ["a.md", "notes/b.md", "notes/c.md"]
}
```

**Errors**:
- `400`: No markdown files found or DOCS_PATH missing

### `POST /chat`
Ask a question using RAG retrieval.

**Request**:
```json
{
  "session_id": "optional-string",  // Optional, for UI correlation only
  "message": "What does the doc say about X?",
  "top_k": 4,           // Optional, default: 4, range: 1-20
  "temperature": 0.2    // Optional, default: 0.2, range: 0-1
}
```

**Response**:
```json
{
  "session_id": "optional-string",
  "answer": "According to the documentation...",
  "sources": [
    {
      "source_id": "a.md:0",
      "filename": "a.md",
      "snippet": "First ~240 chars of chunk content..."
    }
  ],
  "model": "gpt-4.1-mini"
}
```

**Errors**:
- `409`: Vector store not found (call `/ingest` first)
- `422`: Validation error

## Testing

Run tests with pytest:

```bash
cd backend
pytest
```

Tests use fake embeddings and fake LLMs (no network calls or OpenAI costs).

Key tests:
- `test_health.py`: Health endpoint validation
- `test_ingest_smoke.py`: End-to-end ingest with temp files
- `test_chat_requires_ingest.py`: Ensures 409 when index missing
- `test_chat_contract.py`: Contract validation with mocked LLM

## LangSmith Integration

### Tracing

Enable runtime tracing by setting environment variables:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your-api-key
export LANGSMITH_PROJECT=streamlit-fastapi-faiss-demo
```

Traces will appear in your LangSmith project dashboard.

### Evaluation

Run the evaluation script:

```bash
cd backend
python -m app.eval.run_eval
```

This runs 5-10 test questions against the RAG pipeline and scores answers based on keyword presence.

## Postman Testing

Import the OpenAPI spec into Postman:
1. Open Postman
2. Import → Link: `http://localhost:8000/openapi.json`
3. Test all endpoints with auto-generated request schemas

## Deployment

### Backend
Deploy on any service that runs a Python web server:
- Render
- Fly.io
- Google Cloud Run
- Railway

Example for Cloud Run:
```bash
gcloud run deploy rag-backend \
  --source backend \
  --set-env-vars OPENAI_API_KEY=your-key
```

### Frontend
Deploy on Streamlit Community Cloud:

1. Push to GitHub
2. Connect repo in Streamlit Cloud
3. Set secrets in dashboard:
   ```toml
   BACKEND_URL = "https://your-backend-url.com"
   ```

**Important**: Streamlit Cloud does not run FastAPI alongside the Streamlit app. Deploy them separately.

## Configuration

All configuration is managed via `backend/app/core/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_CHAT_MODEL` | `gpt-4.1-mini` | Chat completion model |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `DOCS_PATH` | `../data` | Path to markdown files |
| `VECTORSTORE_DIR` | `../.vectorstore/faiss_index` | FAISS index storage |
| `LANGSMITH_TRACING` | `false` | Enable LangSmith tracing |
| `LANGSMITH_API_KEY` | `None` | LangSmith API key |
| `LANGSMITH_PROJECT` | `streamlit-fastapi-faiss-demo` | LangSmith project name |

## Design Decisions

### No Conversation History
Each `/chat` request is stateless. `session_id` is accepted for UI correlation but not used for memory.

**Why**: Keeps demo simple and avoids complexity of conversation state management.

### Markdown Only
Only `**/*.md` files are indexed.

**Why**: Constrains scope for demo; easy to extend to other formats later.

### FAISS with Pickle Warning
Uses `allow_dangerous_deserialization=True` when loading FAISS.

**Why**: Safe for self-generated indexes. Never use with untrusted files (pickle can execute code).

### One Assert Per Function
Each function has one assertion validating its core invariant.

**Why**: Forces clarity about what each function guarantees; aids debugging.

### Heavy Comments
Every module has extensive "why" comments.

**Why**: Makes codebase educational and maintainable for demo purposes.

## License

MIT
