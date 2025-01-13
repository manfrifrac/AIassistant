from backend.src.agents import SupervisorAgent  # Ensure SupervisorAgent is correctly imported
from backend.src.database.repositories import UserRepository
from backend.src.memory_store import MemoryStore
from uuid import uuid4  # Add this import

def get_supervisor() -> SupervisorAgent:
    user_repo = UserRepository()
    memory_store = MemoryStore()
    supervisor = SupervisorAgent(agent_id=uuid4(), config={"model": "gpt-3.5-turbo"}, memory_store=memory_store)
    return supervisor