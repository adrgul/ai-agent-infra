import logging
import json
from typing import Optional, Dict, Any
from database.pg_connection import get_db_connection

logger = logging.getLogger(__name__)


def init_postgres_schema():
    """Initialize PostgreSQL database schema with all tables."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Create tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id BIGSERIAL PRIMARY KEY,
                    key TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    system_prompt TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            logger.info("Tenants table created or already exists")
            
            # Check if we need to seed tenant data
            cursor.execute("SELECT COUNT(*) as count FROM tenants")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            if count == 0:
                # Insert test tenant data
                test_tenants = [
                    ('acme_corp', 'ACME Corporation', True),
                    ('techstart_inc', 'TechStart Inc.', True),
                    ('global_solutions', 'Global Solutions Ltd.', True),
                    ('innovation_labs', 'Innovation Labs', False),  # Inactive tenant for testing
                ]
                
                cursor.executemany("""
                    INSERT INTO tenants (key, name, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, test_tenants)
                
                logger.info(f"Seeded {len(test_tenants)} test tenants")
            else:
                logger.info(f"Tenants table already has {count} records, skipping seed")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    firstname TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    default_lang TEXT NOT NULL DEFAULT 'en',
                    system_prompt TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_users_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE
                )
            """)
            logger.info("Users table created or already exists")
            
            # Check if we need to seed user data
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            if count == 0:
                # Get tenant IDs for seeding
                cursor.execute("SELECT id, key FROM tenants WHERE is_active = TRUE ORDER BY id")
                tenants = cursor.fetchall()
                
                if len(tenants) >= 2:
                    tenant1_id = tenants[0]['id']  # ACME
                    tenant2_id = tenants[1]['id']  # TechStart
                    
                    # Test users with tenant assignments
                    test_users = [
                        (tenant1_id, 'Alice', 'Johnson', 'alice_j', 'alice@acme.com', 'developer', True, 'hu'),
                        (tenant1_id, 'Bob', 'Smith', 'bob_s', 'bob@acme.com', 'manager', True, 'en'),
                        (tenant2_id, 'Charlie', 'Davis', 'charlie_d', 'charlie@techstart.com', 'analyst', True, 'en'),
                    ]
                    
                    cursor.executemany("""
                        INSERT INTO users (tenant_id, firstname, lastname, nickname, email, role, is_active, default_lang, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, test_users)
                    
                    logger.info(f"Seeded {len(test_users)} test users")
            else:
                logger.info(f"Users table already has {count} records, skipping seed")
            
            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    ended_at TIMESTAMPTZ,
                    processed_for_ltm BOOLEAN NOT NULL DEFAULT FALSE,
                    title TEXT,
                    last_message_at TIMESTAMPTZ,
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    CONSTRAINT fk_chat_sessions_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_chat_sessions_user
                        FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE CASCADE
                )
            """)
            logger.info("Chat sessions table created or already exists")
            
            # Create chat_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    session_id UUID NOT NULL,
                    user_id BIGINT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_chat_messages_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_chat_messages_session
                        FOREIGN KEY (session_id)
                        REFERENCES chat_sessions (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_chat_messages_user
                        FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE CASCADE
                )
            """)
            logger.info("Chat messages table created or already exists")
            
            # Create long_term_memories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    source_session_id UUID,
                    content TEXT NOT NULL,
                    qdrant_point_id UUID,
                    embedded_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_ltm_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_ltm_user
                        FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_ltm_session
                        FOREIGN KEY (source_session_id)
                        REFERENCES chat_sessions (id)
                        ON DELETE SET NULL
                )
            """)
            logger.info("Long-term memories table created or already exists")
            
            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    user_id BIGINT,
                    visibility TEXT NOT NULL CHECK (visibility IN ('private', 'tenant')),
                    source TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_documents_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_documents_user
                        FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE SET NULL,
                    CONSTRAINT documents_visibility_user_check
                        CHECK (
                            (visibility = 'private' AND user_id IS NOT NULL)
                            OR
                            (visibility = 'tenant' AND user_id IS NULL)
                        )
                )
            """)
            logger.info("Documents table created or already exists")
            
            # Create document_chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    document_id BIGINT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    source_title TEXT,
                    source_section TEXT,
                    source_page_from INTEGER,
                    source_page_to INTEGER,
                    qdrant_point_id UUID,
                    embedded_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_chunks_tenant
                        FOREIGN KEY (tenant_id)
                        REFERENCES tenants (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_chunks_document
                        FOREIGN KEY (document_id)
                        REFERENCES documents (id)
                        ON DELETE CASCADE,
                    CONSTRAINT uq_document_chunk
                        UNIQUE (document_id, chunk_index)
                )
            """)
            logger.info("Document chunks table created or already exists")
            
            # Create user_prompt_cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_prompt_cache (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    cached_prompt TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_prompt_cache_user
                        FOREIGN KEY (user_id)
                        REFERENCES users (user_id)
                        ON DELETE CASCADE
                )
            """)
            
            # Create index for fast user lookup (most recent prompt)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_prompt_cache_user_created 
                ON user_prompt_cache(user_id, created_at DESC)
            """)
            
            logger.info("User prompt cache table created or already exists")
            
            conn.commit()
            logger.info("PostgreSQL schema initialization complete")


def get_all_tenants():
    """Retrieve all tenants from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, key, name, is_active, created_at, updated_at
                FROM tenants
                ORDER BY name
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_active_tenants():
    """Retrieve only active tenants."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, key, name, is_active, created_at, updated_at
                FROM tenants
                WHERE is_active = TRUE
                ORDER BY name
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_tenant_by_id(tenant_id: int):
    """Retrieve a tenant by ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, key, name, is_active, system_prompt, created_at, updated_at
                FROM tenants
                WHERE id = %s
            """, (tenant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


def get_users_by_tenant(tenant_id: int):
    """Retrieve all users for a specific tenant."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, tenant_id, firstname, lastname, nickname, email, role, is_active, default_lang, created_at
                FROM users
                WHERE tenant_id = %s
                ORDER BY firstname, lastname
            """, (tenant_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_all_users_pg():
    """Retrieve all users from PostgreSQL (no tenant filter)."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, tenant_id, firstname, lastname, nickname, email, role, is_active, default_lang, created_at
                FROM users
                ORDER BY tenant_id, firstname, lastname
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_user_by_id_pg(user_id: int):
    """Retrieve a user by ID from PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, tenant_id, firstname, lastname, nickname, email, role, is_active, default_lang, system_prompt, created_at
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


def create_session_pg(session_id: str, tenant_id: int, user_id: int):
    """Create a new chat session in PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_sessions (id, tenant_id, user_id, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (session_id, tenant_id, user_id))
            conn.commit()
            logger.info(f"Created session {session_id} for tenant {tenant_id}, user {user_id}")


def insert_message_pg(session_id: str, tenant_id: int, user_id: int, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Insert a message into chat_messages table in PostgreSQL.
    
    Also updates session last_message_at and auto-generates title if needed.
    
    Args:
        metadata: Optional dict containing sources, rag_params, workflow_path, actions_taken
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_messages (tenant_id, session_id, user_id, role, content, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (tenant_id, session_id, user_id, role, content, json.dumps(metadata) if metadata else None))
            conn.commit()
            logger.info(f"Inserted {role} message for session {session_id}")
            
            # Update session last_message_at
            update_session_last_message_time(session_id)
            
            # Auto-update title if this is a user message
            if role == "user":
                # Get message count
                cursor.execute("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE session_id = %s AND role = 'user'
                """, (session_id,))
                result = cursor.fetchone()
                user_message_count = result['count'] if result else 0
                
                # Trigger auto-title logic
                auto_update_session_title(session_id, content, user_message_count)


def get_session_messages_pg(session_id: str, limit: int = 20):
    """Retrieve the last N messages for a session from PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT message_id, tenant_id, session_id, user_id, role, content, metadata, created_at
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (session_id, limit))
            rows = cursor.fetchall()
            # Return in chronological order, converting datetime to ISO string
            messages = []
            for row in reversed(rows):
                msg = dict(row)
                if msg.get('created_at'):
                    msg['created_at'] = msg['created_at'].isoformat()
                messages.append(msg)
            return messages


def get_last_messages_for_user_pg(user_id: int, limit: int = 20):
    """Retrieve the last N messages for a user across all sessions from PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT message_id, tenant_id, session_id, user_id, role, content, created_at
                FROM chat_messages
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            rows = cursor.fetchall()
            # Return in chronological order, converting datetime to ISO string
            messages = []
            for row in reversed(rows):
                msg = dict(row)
                if msg.get('created_at'):
                    msg['created_at'] = msg['created_at'].isoformat()
                messages.append(msg)
            return messages


def delete_user_conversation_history_pg(user_id: int):
    """Delete all conversation history (messages and sessions) for a user from PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # First delete messages (due to foreign key constraint)
            cursor.execute("""
                DELETE FROM chat_messages
                WHERE user_id = %s
            """, (user_id,))
            
            # Then delete sessions
            cursor.execute("""
                DELETE FROM chat_sessions
                WHERE user_id = %s
            """, (user_id,))
            
            conn.commit()
            logger.info(f"Deleted all conversation history for user {user_id}")


def create_long_term_memory(tenant_id: int, user_id: int, content: str, source_session_id: str = None):
    """Create a new long-term memory entry."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO long_term_memories (tenant_id, user_id, source_session_id, content, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
            """, (tenant_id, user_id, source_session_id, content))
            result = cursor.fetchone()
            conn.commit()
            memory_id = result['id'] if result else None
            logger.info(f"Created long-term memory {memory_id} for user {user_id}")
            return memory_id


def get_long_term_memories_for_user(user_id: int, limit: int = 10):
    """Retrieve long-term memories for a specific user."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, user_id, source_session_id, content, qdrant_point_id, embedded_at, created_at
                FROM long_term_memories
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def update_long_term_memory_embedding(memory_id: int, qdrant_point_id: str):
    """Update a long-term memory with Qdrant point ID after embedding."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE long_term_memories
                SET qdrant_point_id = %s, embedded_at = NOW()
                WHERE id = %s
            """, (qdrant_point_id, memory_id))
            conn.commit()
            logger.info(f"Updated long-term memory {memory_id} with Qdrant point ID")


def delete_long_term_memories_for_user(user_id: int):
    """Delete all long-term memories for a specific user."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM long_term_memories
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()
            logger.info(f"Deleted all long-term memories for user {user_id}")


# ==================== Document Functions ====================

def create_document(tenant_id: int, user_id: int, visibility: str, source: str, title: str, content: str):
    """
    Create a new document.
    
    Args:
        tenant_id: Tenant ID
        user_id: User ID (required for 'private', None for 'tenant')
        visibility: 'private' or 'tenant'
        source: Source of the document (e.g., 'upload', 'api', 'scrape')
        title: Document title
        content: Full document content
    
    Returns:
        Document ID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO documents (tenant_id, user_id, visibility, source, title, content)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (tenant_id, user_id, visibility, source, title, content))
            doc_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Created document {doc_id} for tenant {tenant_id}, visibility={visibility}")
            return doc_id


def get_documents_for_user(user_id: int, tenant_id: int):
    """
    Retrieve all documents accessible to a user.
    This includes:
    - Their private documents
    - Tenant-wide documents in their tenant
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, user_id, visibility, source, title, created_at
                FROM documents
                WHERE tenant_id = %s 
                  AND (
                      (visibility = 'private' AND user_id = %s)
                      OR
                      (visibility = 'tenant')
                  )
                ORDER BY created_at DESC
            """, (tenant_id, user_id))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_document_by_id(document_id: int):
    """Retrieve a document by ID including full content."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, user_id, visibility, source, title, content, created_at
                FROM documents
                WHERE id = %s
            """, (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


def delete_document(document_id: int):
    """Delete a document and all its chunks (CASCADE)."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM documents
                WHERE id = %s
            """, (document_id,))
            conn.commit()
            logger.info(f"Deleted document {document_id} and its chunks")


# ==================== Document Chunk Functions ====================

def create_document_chunk(
    tenant_id: int,
    document_id: int,
    chunk_index: int,
    start_offset: int,
    end_offset: int,
    content: str,
    source_title: str = None,
    source_section: str = None,
    source_page_from: int = None,
    source_page_to: int = None
):
    """
    Create a document chunk.
    
    Args:
        tenant_id: Tenant ID
        document_id: Parent document ID
        chunk_index: Sequential index of this chunk
        start_offset: Character offset in original document
        end_offset: Character offset in original document
        content: Chunk text content
        source_title: Original title for source attribution
        source_section: Section/heading for source attribution
        source_page_from: Starting page number
        source_page_to: Ending page number
    
    Returns:
        Chunk ID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO document_chunks 
                (tenant_id, document_id, chunk_index, start_offset, end_offset, 
                 content, source_title, source_section, source_page_from, source_page_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (tenant_id, document_id, chunk_index, start_offset, end_offset,
                  content, source_title, source_section, source_page_from, source_page_to))
            chunk_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Created chunk {chunk_id} for document {document_id}, index={chunk_index}")
            return chunk_id


def get_chunks_for_document(document_id: int):
    """Retrieve all chunks for a document ordered by chunk_index."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, document_id, chunk_index, start_offset, end_offset,
                       content, source_title, source_section, source_page_from, source_page_to,
                       qdrant_point_id, embedded_at, created_at
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index
            """, (document_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def update_chunk_embedding(chunk_id: int, qdrant_point_id: str):
    """Update a chunk with Qdrant point ID after embedding."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE document_chunks
                SET qdrant_point_id = %s, embedded_at = NOW()
                WHERE id = %s
            """, (qdrant_point_id, chunk_id))
            conn.commit()
            logger.info(f"Updated chunk {chunk_id} with Qdrant point ID")


def get_chunks_not_embedded(tenant_id: int = None):
    """
    Retrieve chunks that haven't been embedded yet.
    Optionally filter by tenant_id.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT id, tenant_id, document_id, chunk_index, content,
                       source_title, source_section, source_page_from, source_page_to
                FROM document_chunks
                WHERE qdrant_point_id IS NULL
            """
            params = []
            if tenant_id is not None:
                query += " AND tenant_id = %s"
                params.append(tenant_id)
            query += " ORDER BY created_at"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# ===== SESSION MEMORY FUNCTIONS =====

def get_session_by_id(session_id: str):
    """Get session by ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, user_id, created_at, 
                       COALESCE(processed_for_ltm, FALSE) as processed_for_ltm
                FROM chat_sessions
                WHERE id = %s
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


def insert_long_term_memory(
    tenant_id: int, 
    user_id: int, 
    session_id: str, 
    content: str, 
    memory_type: str,
    qdrant_point_id: str = None
) -> int:
    """
    Insert long-term memory record.
    
    Args:
        tenant_id: Tenant ID
        user_id: User ID
        session_id: Source session ID
        content: Full memory content
        memory_type: "session_summary" or "explicit_fact"
        qdrant_point_id: Qdrant point UUID (can be None initially)
    
    Returns:
        Inserted record ID (for Qdrant payload)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO long_term_memories 
                (tenant_id, user_id, source_session_id, content, memory_type, qdrant_point_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (tenant_id, user_id, session_id, content, memory_type, qdrant_point_id))
            conn.commit()
            result = cursor.fetchone()
            ltm_id = result['id']
            logger.info(f"Inserted long-term memory: id={ltm_id}, type={memory_type}")
            return ltm_id


def get_long_term_memories_by_ids(ltm_ids: list) -> list:
    """
    Batch load long-term memories by IDs.
    
    Used after Qdrant search to retrieve full content for LLM.
    
    Args:
        ltm_ids: List of long_term_memories.id
    
    Returns:
        List of memory records with FULL content
    """
    if not ltm_ids:
        return []
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, 
                    tenant_id, 
                    user_id, 
                    source_session_id, 
                    content,
                    memory_type,
                    created_at
                FROM long_term_memories
                WHERE id = ANY(%s)
                ORDER BY created_at DESC
            """, (ltm_ids,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def mark_session_processed_for_ltm(session_id: str):
    """Mark session as processed for long-term memory."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET processed_for_ltm = TRUE
                WHERE id = %s
            """, (session_id,))
            conn.commit()
            logger.info(f"Marked session {session_id} as processed for LTM")


def get_unprocessed_sessions(older_than_hours: int = 24):
    """Get sessions that haven't been processed for long-term memory."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tenant_id, user_id, created_at
                FROM chat_sessions
                WHERE COALESCE(processed_for_ltm, FALSE) = FALSE
                  AND created_at < NOW() - INTERVAL '%s hours'
                ORDER BY created_at
            """, (older_than_hours,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# ===== SESSION MANAGEMENT FUNCTIONS (ChatGPT-style) =====

def get_user_sessions(user_id: int, include_deleted: bool = False) -> list[dict]:
    """
    Get all sessions for a user, ordered by most recent activity.
    
    Args:
        user_id: User ID to fetch sessions for
        include_deleted: Whether to include soft-deleted sessions
    
    Returns:
        List of session dictionaries with title, message_count, last_message_at
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            where_clause = "WHERE cs.user_id = %s"
            if not include_deleted:
                where_clause += " AND COALESCE(cs.is_deleted, FALSE) = FALSE"
            
            cursor.execute(f"""
                SELECT 
                    cs.id,
                    cs.title,
                    cs.created_at,
                    cs.last_message_at,
                    cs.is_deleted,
                    cs.processed_for_ltm,
                    COUNT(cm.message_id) as message_count
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                {where_clause}
                GROUP BY cs.id
                ORDER BY cs.last_message_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def update_session_title(session_id: str, title: str) -> bool:
    """
    Update session title (user editing).
    
    Args:
        session_id: Session UUID
        title: New title (max 100 chars)
    
    Returns:
        True if updated successfully
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET title = %s
                WHERE id = %s
            """, (title[:100], session_id))
            conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated session {session_id} title to: {title[:50]}")
            return updated


def soft_delete_session(session_id: str) -> bool:
    """
    Soft delete a session (sets is_deleted = TRUE).
    
    Args:
        session_id: Session UUID
    
    Returns:
        True if deleted successfully
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET is_deleted = TRUE
                WHERE id = %s
            """, (session_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Soft deleted session: {session_id}")
            return deleted


def update_session_last_message_time(session_id: str) -> None:
    """
    Update last_message_at timestamp when new message is added.
    
    Args:
        session_id: Session UUID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET last_message_at = NOW()
                WHERE id = %s
            """, (session_id,))
            conn.commit()


def auto_update_session_title(session_id: str, message_content: str, message_count: int) -> None:
    """
    Auto-generate session title based on hybrid logic.
    
    Logic:
    - Message 1: If len >= 20 or contains '?', use as title
    - Message 3: If still NULL, find first meaningful message
    
    Args:
        session_id: Session UUID
        message_content: Current user message
        message_count: Total messages in session
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Get current title
            cursor.execute("SELECT title FROM chat_sessions WHERE id = %s", (session_id,))
            result = cursor.fetchone()
            if not result:
                return
            
            current_title = result['title']
            
            # Message 1 logic
            if message_count == 1:
                if len(message_content) >= 20 or '?' in message_content:
                    new_title = message_content[:50] + ("..." if len(message_content) > 50 else "")
                    cursor.execute("""
                        UPDATE chat_sessions SET title = %s WHERE id = %s
                    """, (new_title, session_id))
                    conn.commit()
                    logger.info(f"Auto-set title (msg 1): {new_title}")
                return
            
            # Message 3 logic (if still NULL)
            if message_count == 3 and current_title is None:
                # Find first meaningful message
                cursor.execute("""
                    SELECT content FROM chat_messages
                    WHERE session_id = %s AND role = 'user'
                    ORDER BY created_at
                    LIMIT 3
                """, (session_id,))
                messages = cursor.fetchall()
                
                for msg in messages:
                    content = msg['content']
                    if len(content) >= 30 or '?' in content:
                        new_title = content[:50] + ("..." if len(content) > 50 else "")
                        cursor.execute("""
                            UPDATE chat_sessions SET title = %s WHERE id = %s
                        """, (new_title, session_id))
                        conn.commit()
                        logger.info(f"Auto-set title (msg 3): {new_title}")
                        break


# ===== USER PROMPT CACHE FUNCTIONS =====

def get_latest_cached_prompt(user_id: int) -> str | None:
    """
    Get the most recent cached system prompt for a user.
    
    Args:
        user_id: User ID to fetch cached prompt for
    
    Returns:
        Cached prompt text or None if no cache exists
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT cached_prompt
                FROM user_prompt_cache
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                logger.info(f"[CACHE] Retrieved cached prompt for user_id={user_id}")
                return result['cached_prompt']
            else:
                logger.info(f"[CACHE] No cached prompt found for user_id={user_id}")
                return None


def save_cached_prompt(user_id: int, cached_prompt: str) -> int:
    """
    Save a new cached system prompt for a user.
    
    Args:
        user_id: User ID to save prompt for
        cached_prompt: Optimized system prompt text
    
    Returns:
        ID of inserted cache record
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_prompt_cache (user_id, cached_prompt, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (user_id, cached_prompt))
            
            result = cursor.fetchone()
            conn.commit()
            
            cache_id = result['id']
            logger.info(f"[CACHE] Saved cached prompt: user_id={user_id}, cache_id={cache_id}")
            return cache_id


def get_prompt_cache_history(user_id: int, limit: int = 10) -> list[dict]:
    """
    Get prompt cache history for a user (for debugging/rollback).
    
    Args:
        user_id: User ID to fetch history for
        limit: Maximum number of records to return
    
    Returns:
        List of cached prompts with metadata
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, cached_prompt, created_at
                FROM user_prompt_cache
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
