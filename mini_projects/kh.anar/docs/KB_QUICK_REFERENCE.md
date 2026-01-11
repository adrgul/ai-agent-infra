# KB Ingestion Quick Reference

## 📁 Where to Put Documents
```
mini_projects/kh.anar/docs/kb-data/
```

Supported formats: `.pdf`, `.txt`, `.md`

## 🚀 How It Works

1. **Place files** in `docs/kb-data/`
2. **Auto-ingest** on startup (or manual trigger)
3. **Query** via chat - agent retrieves from KB
4. **Update/remove** files → auto-detected on next ingest

## 🔧 Quick Commands

### Test Ingestion Locally
```bash
cd backend
python3 verify_kb.py
```

### Run Tests
```bash
cd backend
python3 -m pytest tests/test_kb_*.py -v
```

### Manual API Triggers
```bash
# Incremental (only changed files)
curl -X POST "http://localhost:8000/admin/kb/ingest_incremental" \
  -H "token: changeme"

# Full reindex (all files)
curl -X POST "http://localhost:8000/admin/kb/reindex_full" \
  -H "token: changeme"
```

## ⚙️ Configuration

Set in `.env` or docker-compose:

```bash
KB_DATA_DIR=docs/kb-data          # KB folder path
KB_INGEST_ON_STARTUP=true         # Auto-ingest on startup
KB_VERSION_STORE=.kb_versions.json # Version tracking file
CHUNK_SIZE=800                     # Characters per chunk
CHUNK_OVERLAP=128                  # Overlap between chunks
```

## 📊 Example Output

```
INFO: Starting incremental KB ingestion
INFO: Scanned docs/kb-data: found 8 documents
INFO: KB scan: 8 new, 0 updated, 0 removed
INFO: Parsed PDF beton_bedolgozas.pdf: 3 pages, 15210 chars
...
INFO: KB ingestion complete: 211 chunks indexed in 0.12s
```

## 🧪 Test Coverage

- ✅ File scanning & hashing (6 tests)
- ✅ Version tracking (6 tests)
- ✅ PDF parsing (3 tests)
- ✅ End-to-end ingestion (5 tests)
- ✅ Golden retrieval (1 test)

**Total: 21 tests, all passing**

## 🔍 Verification

Run standalone verification:
```bash
cd backend
python3 verify_kb.py
```

Expected output:
```
🎉 All verification tests passed!
📚 KB contains 8 documents with 211 chunks
```

## 📝 Adding a New Document

```bash
# 1. Copy to KB folder
cp my_guide.pdf docs/kb-data/

# 2. Trigger ingestion (auto on restart, or manual)
curl -X POST http://localhost:8000/admin/kb/ingest_incremental \
  -H "token: changeme"

# 3. Query via chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "session_id": "s1", "message": "what does my_guide say about X?"}'
```

## 🐛 Troubleshooting

**No documents indexed:**
- Check `KB_DATA_DIR` path is correct
- Ensure files have supported extensions
- Check logs for parsing errors

**PDF parsing fails:**
- Verify `pypdf` installed: `pip install pypdf`
- Check PDF is not encrypted/corrupted

**Changes not detected:**
- Verify file content actually changed (hash must differ)
- Check version store file exists and is readable
- Try full reindex: `POST /admin/kb/reindex_full`

## 📚 Documentation

- Full guide: `docs/KB_INGESTION.md`
- Implementation summary: `docs/KB_IMPLEMENTATION_SUMMARY.md`
- Architecture: See SOLID comments in source files
