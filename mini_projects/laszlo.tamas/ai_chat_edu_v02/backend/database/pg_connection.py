import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator

logger = logging.getLogger(__name__)

# PostgreSQL connection configuration from environment variables
# NO DEFAULT VALUES - must be set in .env file
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD_RAW = os.getenv("POSTGRES_PASSWORD")

if not all([POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD_RAW]):
    raise ValueError("PostgreSQL configuration missing! Check .env file for: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")

# Remove quotes (single or double) from password if present
POSTGRES_PASSWORD = POSTGRES_PASSWORD_RAW.strip("'\"")


def get_connection_params() -> dict:
    """Get PostgreSQL connection parameters from environment variables."""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "client_encoding": "UTF8",  # Force UTF-8 encoding
    }


@contextmanager
def get_db_connection() -> Generator:
    """Context manager for PostgreSQL database connections.
    
    Returns a connection with RealDictCursor for dictionary-like row access.
    Automatically commits on success, rolls back on error, and closes connection.
    """
    conn = None
    try:
        params = get_connection_params()
        conn = psycopg2.connect(**params, cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def check_db_connection() -> tuple[bool, str]:
    """Check PostgreSQL database connection health.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as check_value")
                result = cursor.fetchone()
                # RealDictCursor returns dict, not tuple
                if result and result.get('check_value') == 1:
                    return True, "Adatbázis kapcsolódás sikeres"
                return False, "Adatbázis válasz hibás"
    except psycopg2.OperationalError as e:
        error_msg = f"Adatbázis kapcsolódás sikertelen! Hiba: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Adatbázis kapcsolódás sikertelen! Hiba: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
