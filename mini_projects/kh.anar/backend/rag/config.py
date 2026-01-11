from dataclasses import dataclass
import os

# Configuration for RAG components. Values are loaded from env or defaulted.
# We use a dataclass to keep configuration immutable-ish and easy to pass around
# adhering to DIP (dependancy injection of config).

@dataclass
class RAGConfig:
    chroma_dir: str = os.getenv("CHROMA_DIR", ".chroma")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "kb_collection")
    embed_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    k: int = int(os.getenv("RAG_TOP_K", "5"))
    threshold: float = float(os.getenv("RAG_THRESHOLD", "0.25"))
    w_dense: float = float(os.getenv("RAG_W_DENSE", "0.7"))
    w_sparse: float = float(os.getenv("RAG_W_SPARSE", "0.3"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "128"))
    persist: bool = os.getenv("CHROMA_PERSIST", "true").lower() == "true"
    
    # KB folder ingestion config
    kb_data_dir: str = os.getenv("KB_DATA_DIR", "docs/kb-data")
    kb_version_store: str = os.getenv("KB_VERSION_STORE", ".kb_versions.json")
    ingest_on_startup: bool = os.getenv("KB_INGEST_ON_STARTUP", "true").lower() == "true"


# Export a single config instance to be used by default. Tests may inject another.
default_config = RAGConfig()  # type: ignore
