"""
Configuration loader for system.ini settings
"""
import configparser
import os
from pathlib import Path

# Load system.ini
config = configparser.ConfigParser()
config_path = Path(__file__).parent / "system.ini"
config.read(config_path)

# [application]
DEFAULT_LANGUAGE = config.get("application", "DEFAULT_LANGUAGE", fallback="en")
MAX_CONTEXT_TOKENS = config.getint("application", "MAX_CONTEXT_TOKENS", fallback=8000)

# [llm]
CHAT_TEMPERATURE = config.getfloat("llm", "CHAT_TEMPERATURE", fallback=0.7)
CHAT_MAX_TOKENS = config.getint("llm", "CHAT_MAX_TOKENS", fallback=500)
EMBEDDING_BATCH_SIZE = config.getint("llm", "EMBEDDING_BATCH_SIZE", fallback=100)

# [chunking]
CHUNKING_STRATEGY = config.get("chunking", "CHUNKING_STRATEGY", fallback="recursive")
CHUNK_SIZE_TOKENS = config.getint("chunking", "CHUNK_SIZE_TOKENS", fallback=500)
CHUNK_OVERLAP_TOKENS = config.getint("chunking", "CHUNK_OVERLAP_TOKENS", fallback=50)

# [retrieval]
TOP_K_DOCUMENTS = config.getint("retrieval", "TOP_K_DOCUMENTS", fallback=5)
TOP_K_PRODUCTS = config.getint("retrieval", "TOP_K_PRODUCTS", fallback=10)
SIMILARITY_METRIC = config.get("retrieval", "SIMILARITY_METRIC", fallback="cosine")
MIN_SCORE_THRESHOLD = config.getfloat("retrieval", "MIN_SCORE_THRESHOLD", fallback=0.7)

# [memory]
ENABLE_LONGTERM_CHAT_STORAGE = config.getboolean("memory", "ENABLE_LONGTERM_CHAT_STORAGE", fallback=True)
ENABLE_LONGTERM_CHAT_RETRIEVAL = config.getboolean("memory", "ENABLE_LONGTERM_CHAT_RETRIEVAL", fallback=True)
CHAT_SUMMARY_MAX_TOKENS = config.getint("memory", "CHAT_SUMMARY_MAX_TOKENS", fallback=200)
CONSOLIDATE_AFTER_MESSAGES = config.getint("memory", "CONSOLIDATE_AFTER_MESSAGES", fallback=20)
MIN_MESSAGES_FOR_CONSOLIDATION = config.getint("memory", "MIN_MESSAGES_FOR_CONSOLIDATION", fallback=5)

# [rate_limiting]
REQUESTS_PER_MINUTE = config.getint("rate_limiting", "REQUESTS_PER_MINUTE", fallback=60)
MAX_CONCURRENT_REQUESTS = config.getint("rate_limiting", "MAX_CONCURRENT_REQUESTS", fallback=10)

# [cache]
ENABLE_RESPONSE_CACHE = config.getboolean("cache", "ENABLE_RESPONSE_CACHE", fallback=False)
CACHE_TTL_SECONDS = config.getint("cache", "CACHE_TTL_SECONDS", fallback=3600)

# [logging]
LOG_LLM_REQUESTS = config.getboolean("logging", "LOG_LLM_REQUESTS", fallback=True)
LOG_VECTOR_SEARCHES = config.getboolean("logging", "LOG_VECTOR_SEARCHES", fallback=True)
LOG_EMBEDDING_OPERATIONS = config.getboolean("logging", "LOG_EMBEDDING_OPERATIONS", fallback=True)

# Environment variables (from .env)
OPENAI_MODEL_CHAT = os.getenv("OPENAI_MODEL_CHAT", "gpt-3.5-turbo")
OPENAI_MODEL_EMBEDDING = os.getenv("OPENAI_MODEL_EMBEDDING", "text-embedding-3-large")

# Embedding dimensions mapping
EMBEDDING_MODEL_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}

def get_embedding_dimensions(model: str = None) -> int:
    """Get embedding dimensions for a model."""
    if model is None:
        model = OPENAI_MODEL_EMBEDDING
    return EMBEDDING_MODEL_DIMENSIONS.get(model, 1536)
