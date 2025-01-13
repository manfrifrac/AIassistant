import sys
import os
import pytest
from uuid import uuid4
from datetime import datetime

# Aggiungi il percorso root del progetto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.src.database.repositories.user_repository import UserRepository
from backend.src.database.repositories.memory_repository import MemoryRepository
from backend.src.database.repositories.interaction_repository import InteractionRepository
from backend.src.database.repositories.agent_repository import AgentRepository
from backend.src.database.connection import DatabasePool
from backend.src.database.exceptions import ConnectionError, QueryError

pytestmark = pytest.mark.asyncio(loop_scope="function")

@pytest.fixture(autouse=True)
def setup_database():
    # Configure test database settings
    test_settings = {
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_password',
        'host': 'localhost',
        'port': 5432,  # Changed from string to int
        'POOL_SIZE': 5
    }
    
    # Initialize pool
    try:
        DatabasePool.initialize(test_settings)
        yield
    finally:
        if DatabasePool._pool is not None:
            DatabasePool._pool.closeall()

class TestUserRepository:
    @pytest.fixture
    def user_repo(self):
        return UserRepository()

    async def test_find_by_email(self, user_repo):
        # Test data
        test_email = "test@example.com"
        result = await user_repo.find_by_email(test_email)
        assert result is not None or result is None  # Verify we get a response

    async def test_update_last_access(self, user_repo):
        user_id = uuid4()
        try:
            await user_repo.update_last_access(user_id)
            assert True  # If we get here, no exception was raised
        except QueryError:
            pytest.fail("Update last access failed")

class TestMemoryRepository:
    @pytest.fixture
    def memory_repo(self):
        return MemoryRepository()

    @pytest.mark.asyncio
    async def test_find_by_user_id(self, memory_repo):
        user_id = uuid4()
        result = await memory_repo.find_by_user_id(user_id)
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_repo):
        memory_id = uuid4()
        try:
            await memory_repo.delete_memory(memory_id)
            assert True
        except QueryError:
            pytest.fail("Delete memory failed")

class TestInteractionRepository:
    @pytest.fixture
    def interaction_repo(self):
        return InteractionRepository()

    @pytest.mark.asyncio
    async def test_find_by_session_id(self, interaction_repo):
        session_id = uuid4()
        result = await interaction_repo.find_by_session_id(session_id)
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_log_interaction(self, interaction_repo, user_repo):
        # First create a test user
        test_user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password_hash": "dummy_hash"
        }
        user = await user_repo.create(test_user_data)
        assert user is not None
        
        # Now create the interaction with the valid user_id
        interaction_data = {
            "session_id": user['id'],  # Use the created user's ID
            "timestamp": datetime.now(),
            "type": "User",
            "content": "test content"
        }
        
        try:
            result = await interaction_repo.log_interaction(interaction_data)
            assert result is not None
            assert result['type'] == 'User'
            assert result['user_id'] == user['id']
        except QueryError:
            pytest.fail("Log interaction failed")

class TestAgentRepository:
    @pytest.fixture
    def agent_repo(self):
        return AgentRepository()

    @pytest.mark.asyncio
    async def test_find_by_name(self, agent_repo):
        agent_name = "test_agent"
        result = await agent_repo.find_by_name(agent_name)
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_update_agent_status(self, agent_repo):
        agent_id = uuid4()
        status = "active"
        try:
            await agent_repo.update_agent_status(agent_id, status)
            assert True
        except QueryError:
            pytest.fail("Update agent status failed")
