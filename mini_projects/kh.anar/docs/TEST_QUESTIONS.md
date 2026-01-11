# KB Ingestion Test Questions

Test questions to validate KB retrieval functionality after ingestion.

## Setup Questions (Basic Functionality)

1. **Q: Mi a ChromaDB?**
   - Expected: Should retrieve information about ChromaDB being a vector database

2. **Q: Hogyan működik a hybrid RAG rendszer?**
   - Expected: Should explain dense + sparse retrieval combination

3. **Q: Milyen fájlformátumokat támogat a KB rendszer?**
   - Expected: PDF, TXT, MD formats

## Technical Questions (Ingestion Pipeline)

4. **Q: Hogyan detektáljuk a megváltozott dokumentumokat?**
   - Expected: SHA256 hash-based change detection via version store

5. **Q: Mi történik amikor egy fájlt törölsz a kb-data mappából?**
   - Expected: Incremental ingestion removes chunks via delete_by_doc_id

6. **Q: Milyen chunking stratégiát használunk?**
   - Expected: Character-based chunking with overlap, deterministic

7. **Q: Hogyan indítható el a teljes újraindexelés?**
   - Expected: POST /admin/kb/reindex_full endpoint or full reindex method

## Architecture Questions (SOLID Principles)

8. **Q: Milyen modulokból áll az ingestion pipeline?**
   - Expected: scanner.py, pdf_parser.py, version_store.py, kb_indexer.py

9. **Q: Mi a scanner.py felelőssége?**
   - Expected: File discovery, SHA256 hashing, doc_id generation (SRP)

10. **Q: Hogyan biztosítjuk a tesztelhetőséget?**
    - Expected: Dependency injection (config, embedder, retrievers), fake implementations

## Configuration Questions

11. **Q: Melyik környezeti változó kapcsolja be az indítási ingestion-t?**
    - Expected: KB_INGEST_ON_STARTUP=true

12. **Q: Hol tárolja a verziókövetést a rendszer?**
    - Expected: .kb_versions.json (configurable via KB_VERSION_STORE)

13. **Q: Mi a default chunk méret?**
    - Expected: 800 characters (CHUNK_SIZE)

## Retrieval Questions

14. **Q: Milyen embedder-t használunk production-ben?**
    - Expected: Recommendation to switch from HashEmbedder to SentenceTransformer

15. **Q: Hogyan kombinálódnak a dense és sparse scores?**
    - Expected: Min-max normalization, weighted merge (w_dense=0.7, w_sparse=0.3)

16. **Q: Persistál-e a BM25 index?**
    - Expected: No, in-memory, rebuilt on restart (production consideration)

## Testing Questions

17. **Q: Hány teszt van összesen a KB rendszerben?**
    - Expected: 21 tests (scanner=6, version_store=6, pdf_parser=3, integration=5, golden=1)

18. **Q: Mi a golden retrieval test célja?**
    - Expected: Validate Recall@k for 10 queries against test documents

19. **Q: Milyen threshold-ot használunk a golden retrieval test-ben?**
    - Expected: 70% recall for hash-based embeddings (adjusted for determinism)

## Troubleshooting Questions

20. **Q: Mit tegyek ha nem indexelődnek a dokumentumok?**
    - Expected: Check KB_DATA_DIR path, file extensions, logs for parsing errors

21. **Q: Hogyan lehet a version store-t újraépíteni?**
    - Expected: Full reindex (clears version tracking) or manually delete .kb_versions.json

## API Questions

22. **Q: Mi a különbség az incremental és full reindex között?**
    - Expected: Incremental only processes changed files; full clears everything and reindexes

23. **Q: Milyen admin token-t használ a rendszer?**
    - Expected: ADMIN_TOKEN env var, default "changeme"

24. **Q: Melyik endpoint-on keresztül lehet incremental ingestion-t indítani?**
    - Expected: POST /admin/kb/ingest_incremental

## Production Considerations

25. **Q: Mik a production deployment ajánlások?**
    - Expected: Switch to semantic embeddings, persist BM25, async background jobs, monitoring, backup

26. **Q: Hogyan kell a ChromaDB-t backup-olni?**
    - Expected: Snapshot ChromaDB directory + version store regularly

27. **Q: Miért használunk atomic file operations a version store-ban?**
    - Expected: tempfile + rename pattern prevents corruption on crash

## Integration Questions

28. **Q: Hogyan fut a startup ingestion?**
    - Expected: FastAPI lifespan hook initializes indexer and calls ingest_incremental

29. **Q: Milyen metaadatokat mentünk el chunk-onként?**
    - Expected: doc_id, title, source, doc_type, version_hash, chunk_index, page (PDF)

30. **Q: Hogyan lehet új parser-t hozzáadni?**
    - Expected: Implement parse function, add extension to scanner, register in kb_indexer (OCP)

---

## Usage

Run these questions through the chat API after KB ingestion:

```bash
# Example
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "session_id": "test_session",
    "message": "Mi a ChromaDB?"
  }'
```

Expected: Agent response should cite relevant KB documents and provide accurate answers based on ingested content.

## Success Criteria

- ✅ Agent retrieves relevant chunks from KB
- ✅ Responses cite source documents (doc_id)
- ✅ Technical details match implementation
- ✅ No hallucination of non-existent features
- ✅ Recall@3 >= 70% for technical questions
