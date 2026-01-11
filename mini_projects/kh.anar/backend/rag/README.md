Hybrid RAG module (Chroma + BM25)

Overview
- Provides deterministic chunking, ingestion, embeddings, dense (Chroma) and
  sparse (BM25) retrieval, hybrid merging and citation mapping.
- KB-first routing: Agent calls RAGService.route_and_retrieve(query) which
  returns telemetry and top-k hits. If hit decision is false, the agent will
  fall back to other sources (configurable policy).

Components
- chunking: DeterministicChunker (configurable chunk_size/overlap)
- ingestion: Ingester (converts Document -> chunks, computes embeddings)
- embeddings: TransformerEmbedder (prod) / HashEmbedder (test)
- retrieval/dense.py: DenseRetriever (Chroma wrapper with persistence)
- retrieval/sparse.py: SparseRetriever (BM25 or simple lexical fallback)
- retrieval/hybrid.py: HybridRetriever (normalizes scores, computes final score)
- service.py: RAGService (route, embed, retrieve, telemetry)
- citations.py: map_citations (map hits to answer citations)
- persistence/store.py: DocumentStore persists documents under DATA_DIR/rag_documents for durable reindexing and audit

Design notes / tradeoffs
- Chunking by character is deterministic and simple; sentence-aware chunking
  could be added but complicates determinism for tests.
- Min-max normalization is used for score merging for interpretability; a
  learned re-ranker could replace this for higher quality.
- Chroma chosen for persistent vector store; it's isolated behind DenseRetriever
  so it can be swapped in future.

Testing
- Unit tests for chunker, sparse retriever, hybrid merging and citations
- Integration tests for ingestion->retrieval and canary/golden retrieval
- Chromadb persistence test is skipped unless `chromadb` is installed
