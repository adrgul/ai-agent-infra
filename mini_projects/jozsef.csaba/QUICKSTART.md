# Quick Start Guide

Get the RAG chatbot running in under 5 minutes!

## Prerequisites

- Python 3.10+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Step 1: Set up the Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Edit `backend/.env`:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Step 2: Run the Backend

```bash
# Make sure you're in backend/ with venv activated
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test it: Open http://localhost:8000/docs in your browser to see the Swagger UI.

## Step 3: Run Tests (Optional but Recommended)

In a new terminal:

```bash
cd backend
source venv/bin/activate  # Activate venv
pytest -v
```

All tests should pass! They use fake embeddings/LLMs so no OpenAI API calls are made.

## Step 4: Add Your Documents

```bash
# From project root
cp your-docs/*.md data/
```

Or use the included sample:
```bash
# Sample doc is already in data/sample_doc.md
ls data/
```

## Step 5: Index Your Documents

You can either:

**Option A: Use the API directly**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_rebuild": true}'
```

**Option B: Use the Streamlit UI** (see Step 6)

## Step 6: Run the Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run streamlit_app.py
```

Your browser should automatically open to http://localhost:8501

## Step 7: Chat!

1. In the Streamlit UI sidebar, click **"🔄 Ingest Documents"**
   - This builds the FAISS index (only needed once, or when you add/update documents)
   - You should see "✅ Ingestion complete!"

2. Type a question in the chat input, for example:
   - "What is this project about?"
   - "How do I run the backend?"
   - "What API endpoints are available?"

3. View the answer and click **"📚 Sources"** to see which document chunks were used

## Troubleshooting

### Backend won't start
- Check that your OpenAI API key is set correctly in `backend/.env`
- Make sure you're in the correct directory and venv is activated
- Try: `pip install -e ".[dev]"` again

### "Vector store not found" error
- Click the "🔄 Ingest Documents" button in the Streamlit sidebar
- Or call the ingest endpoint: `curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"force_rebuild": true}'`

### Streamlit can't connect to backend
- Make sure backend is running on http://localhost:8000
- Check the "Backend URL" field in Streamlit sidebar matches your backend URL

### Tests failing
- Make sure you're in `backend/` directory
- Verify venv is activated
- Try: `pip install -e ".[dev]"` to ensure all test dependencies are installed

## Next Steps

- **Add more documents**: Drop `.md` files into `data/` and re-run ingestion
- **Tune RAG parameters**: Adjust `top_k` and `temperature` in the Streamlit sidebar
- **Enable LangSmith tracing**: Set `LANGSMITH_TRACING=true` in `.env` to see traces
- **Run evaluation**: `python -m app.eval.run_eval` (requires indexed documents)
- **Explore the API**: Check out http://localhost:8000/docs for interactive API docs
- **Import to Postman**: Import http://localhost:8000/openapi.json

## Architecture Overview

```
┌─────────────────┐
│   Streamlit UI  │  localhost:8501
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI Backend│  localhost:8000
│                 │
│  ┌───────────┐  │
│  │   /chat   │──┼──┐
│  └───────────┘  │  │
│                 │  │
│  ┌───────────┐  │  │
│  │  /ingest  │──┼──┤
│  └───────────┘  │  │
└─────────────────┘  │
                     ▼
              ┌─────────────┐
              │ FAISS Index │
              │  (local)    │
              └─────────────┘
                     ▲
                     │
              ┌─────────────┐
              │   data/     │
              │  *.md files │
              └─────────────┘
```

Enjoy your RAG chatbot! 🚀
