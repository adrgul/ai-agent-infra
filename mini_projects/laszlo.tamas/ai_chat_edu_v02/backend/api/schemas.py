from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user sending the message")
    tenant_id: int = Field(..., description="ID of the tenant")
    session_id: str = Field(..., description="UUID of the chat session")
    message: str = Field(..., description="User's message content")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant's response")


class RAGChatRequest(BaseModel):
    """Request for RAG-based chat endpoint."""
    user_id: int = Field(..., description="ID of the user sending the message")
    tenant_id: int = Field(..., description="ID of the tenant")
    query: str = Field(..., min_length=1, description="User's question")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")


class DocumentSource(BaseModel):
    """Source reference (document or long-term memory)."""
    id: Optional[int] = Field(None, description="Document ID (if type=document)")
    title: Optional[str] = Field(None, description="Document title (if type=document)")
    type: str = Field("document", description="Source type: 'document' or 'long_term_memory'")
    content: Optional[str] = Field(None, description="Memory content (if type=long_term_memory)")
    ltm_id: Optional[int] = Field(None, description="Long-term memory ID (if type=long_term_memory)")


class RAGParams(BaseModel):
    """RAG search parameters used for retrieval."""
    top_k: int = Field(..., description="Number of top results retrieved")
    min_score_threshold: float = Field(..., description="Minimum similarity score threshold")


class RAGChatResponse(BaseModel):
    """Response from RAG-based chat endpoint."""
    answer: str = Field(..., description="Generated answer from RAG pipeline")
    sources: List[DocumentSource] = Field(..., description="List of source documents with titles")
    error: Optional[str] = Field(None, description="Error message if any")
    session_id: str = Field(..., description="Session ID for the conversation")
    prompt_details: Optional[Dict[str, Any]] = Field(None, description="Debug info: prompt structure sent to LLM")
    rag_params: Optional[RAGParams] = Field(None, description="RAG parameters used (only when RAG was triggered)")


class MessageResponse(BaseModel):
    message_id: int
    session_id: str
    user_id: int
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")


class UserUpdateRequest(BaseModel):
    """Request for updating user data."""
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    default_lang: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class TenantUpdateRequest(BaseModel):
    """Request for updating tenant data."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


# ============================================================================
# P0.17 - Cache Control Schemas
# ============================================================================

class MemoryCacheStats(BaseModel):
    """In-memory cache statistics (Tier 1)."""
    enabled: bool = Field(..., description="Whether memory cache is enabled")
    size: int = Field(..., description="Number of cached entries")
    keys: List[str] = Field(..., description="List of cache keys")
    ttl_seconds: int = Field(..., description="Time-to-live in seconds")
    debug_mode: bool = Field(False, description="Whether cache debug mode is enabled")


class DBCacheStats(BaseModel):
    """PostgreSQL cache statistics (Tier 2)."""
    enabled: bool = Field(..., description="Whether DB cache is enabled")
    cached_users: int = Field(..., description="Number of users with cached prompts")
    total_entries: int = Field(..., description="Total number of cache entries")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")


class CacheConfig(BaseModel):
    """Cache configuration flags from system.ini."""
    memory_enabled: bool = Field(..., description="ENABLE_MEMORY_CACHE")
    db_enabled: bool = Field(..., description="ENABLE_DB_CACHE")
    browser_enabled: bool = Field(..., description="ENABLE_BROWSER_CACHE")
    llm_enabled: bool = Field(..., description="ENABLE_LLM_CACHE")


class CacheStatsResponse(BaseModel):
    """Comprehensive cache statistics for all layers."""
    memory_cache: MemoryCacheStats = Field(..., description="In-memory cache stats")
    db_cache: DBCacheStats = Field(..., description="PostgreSQL cache stats")
    config: CacheConfig = Field(..., description="Current cache configuration")
    timestamp: str = Field(..., description="ISO timestamp of stats collection")


class CacheInvalidateResponse(BaseModel):
    """Response from cache invalidation operations."""
    user_id: Optional[int] = Field(None, description="User ID that was invalidated")
    tenant_id: Optional[int] = Field(None, description="Tenant ID that was invalidated")
    memory_cleared: int = Field(0, description="Number of memory cache entries cleared")
    db_cleared: int = Field(0, description="Number of DB cache entries cleared")
    users_affected: Optional[int] = Field(None, description="Number of users affected (tenant invalidation)")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class CacheClearResponse(BaseModel):
    """Response from clear all caches operation."""
    memory_cleared: bool = Field(..., description="Whether memory cache was cleared")
    db_cleared: int = Field(..., description="Number of DB cache entries cleared")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class DevModeResponse(BaseModel):
    """Development mode configuration from system.ini."""
    dev_mode: bool = Field(..., description="Whether development mode is enabled (disables all caches)")
