import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import logging
from psycopg2.extras import RealDictCursor
from typing import Generator
from .exceptions import ConnectionError, QueryError

logger = logging.getLogger(__name__)

class DatabasePool:
    _pool = None
    _initialized = False

    @classmethod
    def initialize(cls, settings: dict) -> None:
        """Initialize the connection pool"""
        if cls._initialized:
            return
            
        try:
            pool_size = settings.pop('POOL_SIZE', 5)
            cls._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=pool_size,
                cursor_factory=RealDictCursor,
                **settings
            )
            cls._initialized = True
        except Exception as e:
            cls._pool = None
            cls._initialized = False
            logger.error(f"Failed to initialize database pool: {e}")
            raise ConnectionError(f"Failed to initialize pool: {str(e)}")

    @classmethod
    def cleanup(cls) -> None:
        """Safely close the connection pool"""
        if cls._pool is not None:
            try:
                if not cls._pool.closed:
                    cls._pool.closeall()
            except Exception:
                pass
            finally:
                cls._pool = None
                cls._initialized = False

    @classmethod
    def ensure_initialized(cls, settings: dict) -> None:
        """Ensure pool is initialized, reinitialize if closed"""
        if cls._pool is None or cls._pool.closed:
            cls.cleanup()
            cls.initialize(settings)

    @classmethod
    @contextmanager
    def get_connection(cls) -> Generator:
        if not cls._initialized or cls._pool is None:
            raise ConnectionError("Database pool not initialized")
        
        if cls._pool.closed:
            raise ConnectionError("Connection pool is closed")

        conn = None
        try:
            conn = cls._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise QueryError(f"Database operation failed: {str(e)}")
        finally:
            if conn and not cls._pool.closed:
                try:
                    cls._pool.putconn(conn)
                except Exception:
                    pass  # Pool might be closed during cleanup

def get_connection_string() -> str:
    return "postgresql+asyncpg://admin:Federico2024!@localhost:5432/AiAssistant"