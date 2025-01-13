
import pytest
from unittest.mock import MagicMock, patch
from backend.src.agents.supervisor_agent import SupervisorAgent
from backend.src.core_components import CoreComponents
from backend.src.memory_store import MemoryStore
from uuid import uuid4

@pytest.fixture
def supervisor_agent():
    agent_id = uuid4()
    config = {"model": "gpt-3.5-turbo"}
    memory_store = MemoryStore()
    supervisor = SupervisorAgent(agent_id, config, memory_store)
    supervisor.llm = MagicMock()
    return supervisor

def test_determine_next_agent_greeting(supervisor_agent):
    user_message = "Hello, how are you?"
    state = {}
    next_agent = supervisor_agent.determine_next_agent(user_message, state)
    assert next_agent == "GREETING"

def test_determine_next_agent_research(supervisor_agent):
    user_message = "Can you explain quantum physics?"
    state = {}
    supervisor_agent.llm.invoke.return_value.content = "RESEARCHER"
    next_agent = supervisor_agent.determine_next_agent(user_message, state)
    assert next_agent == "RESEARCHER"

def test_determine_next_agent_invalid_response(supervisor_agent):
    user_message = "Invalid message"
    state = {}
    supervisor_agent.llm.invoke.return_value.content = "UNKNOWN_AGENT"
    next_agent = supervisor_agent.determine_next_agent(user_message, state)
    assert next_agent == "GREETING"

def test_determine_next_agent_exception(supervisor_agent):
    user_message = "Test message"
    state = {}
    supervisor_agent.llm.invoke.side_effect = Exception("LLM Error")
    next_agent = supervisor_agent.determine_next_agent(user_message, state)
    assert next_agent == "ERROR"

@patch('backend.src.agents.supervisor_agent.find_relevant_messages')
def test_process_research_agent(mock_find_relevant, supervisor_agent):
    mock_find_relevant.return_value = []
    state = {
        "user_messages": [{"role": "user", "content": "Tell me about AI."}],
        "agent_messages": [],
        "last_agent": ""
    }
    supervisor_agent.determine_next_agent = MagicMock(return_value="RESEARCHER")
    command = supervisor_agent.process(state)
    assert command.goto == "researcher"
    assert command.update["last_agent"] == "researcher"

@patch('backend.src.agents.supervisor_agent.find_relevant_messages')
def test_process_greeting_agent(mock_find_relevant, supervisor_agent):
    mock_find_relevant.return_value = []
    state = {
        "user_messages": [{"role": "user", "content": "Hi there!"}],
        "agent_messages": [],
        "last_agent": ""
    }
    supervisor_agent.determine_next_agent = MagicMock(return_value="GREETING")
    command = supervisor_agent.process(state)
    assert command.goto == "greeting"
    assert command.update["last_agent"] == "greeting"

def test_get_last_user_message(supervisor_agent):
    messages = [
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "Hi!"},
        {"role": "user", "content": "How can you help me?"}
    ]
    last_message = supervisor_agent.get_last_user_message(messages)
    assert last_message == "How can you help me?"