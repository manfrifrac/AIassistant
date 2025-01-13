import pytest
import asyncio
from pathlib import Path
from backend.src.database.connection import DatabasePool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Remove the event_loop fixture and instead mark tests with loop_scope
pytestmark = pytest.mark.asyncio(loop_scope="function")

@pytest.fixture(scope="session")
def db_settings():
    """Database settings for testing"""
    return {
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_password',
        'host': 'localhost',
        'port': 5432,
        'POOL_SIZE': 5
    }

@pytest.fixture(scope="session")
def db_pool(db_settings):
    """Create and manage the database pool for the test session"""
    # Ensure clean state
    DatabasePool.cleanup()
    
    # Initialize pool
    DatabasePool.initialize(db_settings)
    
    # Setup schema
    with DatabasePool.get_connection() as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            # Create schema
            schema_path = Path(__file__).parent.parent / 'src' / 'database' / 'init_schema.sql'
            with open(schema_path, 'r') as f:
                cur.execute(f.read())
    
    yield DatabasePool
    
    # Cleanup after all tests
    DatabasePool.cleanup()

@pytest.fixture(autouse=True)
def setup_test_tables(db_pool, db_settings):
    """Reset tables before each test"""
    # Ensure pool is initialized
    db_pool.ensure_initialized(db_settings)
    
    with db_pool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                TRUNCATE users, interactions, memory, agents RESTART IDENTITY CASCADE;
            """)
    yield

@pytest.fixture
def user_repo():
    """User repository fixture"""
    from backend.src.database.repositories.user_repository import UserRepository
    return UserRepository()
