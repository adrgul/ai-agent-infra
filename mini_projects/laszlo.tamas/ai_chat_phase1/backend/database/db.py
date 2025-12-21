import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATABASE_PATH = "chat_app.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database schema and seed data."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                nickname TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                default_lang TEXT DEFAULT 'en',
                created_at DATETIME NOT NULL
            )
        """)
        
        # Check if default_lang column exists, if not, add it
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'default_lang' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN default_lang TEXT DEFAULT 'en'")
            logger.info("Added default_lang column to users table")
        
        # Create chat_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create chat_messages table (event log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]
        
        if count == 0:
            # Insert exactly 3 predefined test users
            now = datetime.utcnow().isoformat()
            test_users = [
                (1, "Alice", "Johnson", "alice_j", "alice@example.com", "developer", True, "hu", now),
                (2, "Bob", "Smith", "bob_s", "bob@example.com", "manager", True, "en", now),
                (3, "Charlie", "Davis", "charlie_d", "charlie@example.com", "analyst", False, "en", now),
            ]
            cursor.executemany("""
                INSERT INTO users (user_id, firstname, lastname, nickname, email, role, is_active, default_lang, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, test_users)
            logger.info("Seeded 3 test users into database")
        else:
            # Update existing users with default_lang if not set
            cursor.execute("UPDATE users SET default_lang = 'hu' WHERE user_id = 1 AND (default_lang IS NULL OR default_lang = '')")
            cursor.execute("UPDATE users SET default_lang = 'en' WHERE user_id = 2 AND (default_lang IS NULL OR default_lang = '')")
            cursor.execute("UPDATE users SET default_lang = 'en' WHERE user_id = 3 AND (default_lang IS NULL OR default_lang = '')")
            logger.info("Updated existing users with default_lang")
        
        conn.commit()
        logger.info("Database initialized successfully")


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_users() -> List[Dict[str, Any]]:
    """Retrieve all users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY user_id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def create_session(session_id: str, user_id: int) -> None:
    """Create a new chat session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_sessions (id, user_id, created_at)
            VALUES (?, ?, ?)
        """, (session_id, user_id, datetime.utcnow().isoformat()))


def insert_message(session_id: str, user_id: int, role: str, content: str) -> None:
    """Insert a message into the chat_messages event log."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (session_id, user_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_id, role, content, datetime.utcnow().isoformat()))


def get_session_messages(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve the last N messages for a session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, session_id, user_id, role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        # Reverse to get chronological order
        return [dict(row) for row in reversed(rows)]


def get_last_messages_for_user(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve the last N messages for a user across all sessions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, session_id, user_id, role, content, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit * 2))  # Get more to ensure we have enough pairs
        rows = cursor.fetchall()
        # Reverse to get chronological order
        return [dict(row) for row in reversed(rows)]


def delete_user_conversation_history(user_id: int) -> None:
    """Delete all conversation history for a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Delete all messages for this user
        cursor.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        # Delete all sessions for this user
        cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
        logger.info(f"Deleted all conversation history for user_id={user_id}")
