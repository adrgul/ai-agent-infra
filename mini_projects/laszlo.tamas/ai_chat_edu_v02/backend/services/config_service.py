"""Configuration service for system.ini."""

import os
import configparser
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for reading system.ini configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config service.
        
        Args:
            config_path: Path to system.ini file. If None, searches in backend directory.
        """
        if config_path is None:
            # Default: look for system.ini in backend/config directory
            backend_dir = Path(__file__).parent.parent
            config_path = backend_dir / "config" / "system.ini"
        
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        
        if not self.config_path.exists():
            logger.warning(f"system.ini not found at {self.config_path}, using defaults")
        else:
            self.config.read(self.config_path, encoding='utf-8')
            logger.info(f"Loaded system.ini from {self.config_path}")
    
    def get(self, section: str, key: str, default: str = "") -> str:
        """
        Get a string value from config.
        
        Args:
            section: Section name (e.g., 'rag', 'llm')
            key: Key name
            default: Default value if not found
        
        Returns:
            Configuration value as string
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.debug(f"Config {section}.{key} not found, using default: {default}")
            return default
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """Get an integer value from config."""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.debug(f"Config {section}.{key} not found, using default: {default}")
            return default
    
    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """Get a float value from config."""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.debug(f"Config {section}.{key} not found, using default: {default}")
            return default
    
    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """Get a boolean value from config."""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.debug(f"Config {section}.{key} not found, using default: {default}")
            return default
    
    # === APPLICATION ===
    
    def get_system_prompt(self) -> str:
        """Get global system prompt."""
        return self.get('application', 'system_prompt', 
                       'Te egy hasznos AI asszisztens vagy.')
    
    def is_dev_mode(self) -> bool:
        """Check if development mode is enabled (disables all caches)."""
        return self.get_bool('development', 'DEV_MODE', False)
    
    # === RAG SETTINGS ===
    
    def get_chunking_strategy(self) -> str:
        """Get chunking strategy (e.g., 'recursive')."""
        return self.get('rag', 'CHUNKING_STRATEGY', 'recursive')
    
    def get_chunk_size_tokens(self) -> int:
        """Get chunk size in tokens."""
        return self.get_int('rag', 'CHUNK_SIZE_TOKENS', 500)
    
    def get_chunk_overlap_tokens(self) -> int:
        """Get chunk overlap in tokens."""
        return self.get_int('rag', 'CHUNK_OVERLAP_TOKENS', 50)
    
    def get_embedding_model(self) -> str:
        """Get embedding model name from environment variable."""
        return os.getenv('OPENAI_MODEL_EMBEDDING', 'text-embedding-3-large')
    
    def get_embedding_dimensions(self) -> int:
        """Get embedding vector dimensions."""
        return self.get_int('rag', 'EMBEDDING_DIMENSIONS', 3072)
    
    def get_embedding_batch_size(self) -> int:
        """Get max batch size for embedding API calls."""
        return self.get_int('rag', 'EMBEDDING_BATCH_SIZE', 100)
    
    def get_top_k_documents(self) -> int:
        """Get top-K documents to retrieve."""
        return self.get_int('rag', 'TOP_K_DOCUMENTS', 5)
    
    def get_min_score_threshold(self) -> float:
        """Get minimum similarity score threshold."""
        return self.get_float('rag', 'MIN_SCORE_THRESHOLD', 0.7)
    
    def get_qdrant_search_limit(self) -> int:
        """Get Qdrant search limit (max results to fetch)."""
        return self.get_int('rag', 'QDRANT_SEARCH_LIMIT', 10)
    
    def get_qdrant_search_offset(self) -> int:
        """Get Qdrant search offset."""
        return self.get_int('rag', 'QDRANT_SEARCH_OFFSET', 0)
    
    def get_qdrant_upload_batch_size(self) -> int:
        """Get Qdrant upload batch size (to avoid payload size limit)."""
        return self.get_int('rag', 'QDRANT_UPLOAD_BATCH_SIZE', 50)
    
    # === LLM SETTINGS ===
    
    def get_chat_model(self) -> str:
        """Get chat model name from environment variable."""
        return os.getenv('OPENAI_MODEL_CHAT', 'gpt-3.5-turbo')
    
    def get_max_tokens(self) -> int:
        """Get max tokens for LLM response."""
        return self.get_int('llm', 'CHAT_MAX_TOKENS', 500)
    
    def get_temperature(self) -> float:
        """Get LLM temperature."""
        return self.get_float('llm', 'CHAT_TEMPERATURE', 0.7)
    
    # === MEMORY SETTINGS ===
    
    def is_longterm_chat_storage_enabled(self) -> bool:
        """Check if long-term chat memory storage is enabled."""
        return self.get_bool('memory', 'ENABLE_LONGTERM_CHAT_STORAGE', False)
    
    def is_longterm_chat_retrieval_enabled(self) -> bool:
        """Check if long-term chat memory retrieval is enabled."""
        return self.get_bool('memory', 'ENABLE_LONGTERM_CHAT_RETRIEVAL', False)
    
    def get_session_summary_max_tokens(self) -> int:
        """Get max tokens for session summary."""
        return self.get_int('memory', 'CHAT_SUMMARY_MAX_TOKENS', 200)
    
    def get_min_messages_for_consolidation(self) -> int:
        """Get minimum messages required for memory consolidation."""
        return self.get_int('memory', 'MIN_MESSAGES_FOR_CONSOLIDATION', 5)
    
    def get_consolidate_after_messages(self) -> int:
        """Get message threshold for consolidation trigger."""
        return self.get_int('memory', 'CONSOLIDATE_AFTER_MESSAGES', 50)
    
    def get_top_k_long_term_memories(self) -> int:
        """Get how many previous session summaries to retrieve."""
        return self.get_int('memory', 'TOP_K_LONG_TERM_MEMORIES', 3)
    
    def get_memory_score_threshold(self) -> float:
        """Get minimum similarity score for relevant memories."""
        return self.get_float('memory', 'MEMORY_SCORE_THRESHOLD', 0.5)
    
    # === LIMITS ===
    
    def get_max_file_size_mb(self) -> int:
        """Get max file upload size in MB."""
        return self.get_int('limits', 'MAX_FILE_SIZE_MB', 10)
    
    def get_max_chunks_per_document(self) -> int:
        """Get max chunks per document."""
        return self.get_int('limits', 'MAX_CHUNKS_PER_DOCUMENT', 1000)
    
    def get_max_documents_per_user(self) -> int:
        """Get max documents per user."""
        return self.get_int('limits', 'MAX_DOCUMENTS_PER_USER', 100)


# Singleton instance
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """Get singleton config service instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
