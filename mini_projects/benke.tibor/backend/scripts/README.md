# Backend Scripts

Utility scripts for data management and ingestion.

## Setup Qdrant Collections

Creates vector database collections for each domain.

```bash
# Make sure Qdrant is running
docker run -p 6333:6333 qdrant/qdrant

# Create collections
python backend/scripts/create_collections.py
```

## Ingest Documents

Loads documents from `backend/data/files/{domain}/` and ingests them into Qdrant.

**Supported formats:** PDF, TXT, MD, DOCX

### Usage

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Ingest all domains
python backend/scripts/ingest_documents.py

# Ingest specific domain
python backend/scripts/ingest_documents.py --domain hr

# Clear and re-ingest
python backend/scripts/ingest_documents.py --domain it --clear
```

### Document Organization

Place your documents in domain-specific folders:

```
backend/data/files/
├── hr/              # HR policies, vacation, benefits
├── it/              # Tech docs, VPN guides, troubleshooting
├── finance/         # Budget policies, expense reports
├── legal/           # Contracts, compliance docs
├── marketing/       # Brand guidelines, campaign templates
└── general/         # Other company documents
```

### Process Flow

1. **Load documents** - Reads all supported files from domain folder
2. **Chunk text** - Splits into 500-token chunks with 50-token overlap
3. **Create embeddings** - Uses OpenAI text-embedding-3-small
4. **Upload to Qdrant** - Stores vectors with metadata

### Dependencies

Required packages (add to requirements.txt if missing):
- `qdrant-client`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `pypdf`
- `python-docx`
- `unstructured`
- `markdown`

## Environment Variables

```bash
OPENAI_API_KEY=sk-...              # Required for embeddings
QDRANT_HOST=localhost              # Default: localhost
QDRANT_PORT=6333                   # Default: 6333
EMBEDDING_MODEL=text-embedding-3-small  # Default
```
