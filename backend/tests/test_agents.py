import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from backend.src.agents import (
    SupervisorAgent, 
    ResearcherAgent,
    GreetingAgent,
    MemoryAgent
)
from backend.src.agents.base import NodeType
from langgraph.types import Command
from typing import Dict, Any, Optional, cast
import logging

# Fixtures
@pytest.fixture
def memory_store():
    mock_store = MagicMock()
    mock_store.retrieve_from_long_term_memory.return_value = {"last_greeting": "Hello!"}
    mock_store.manage_short_term.return_value = []
    mock_store.manage_long_term.return_value = {}
    return mock_store

@pytest.fixture
def base_state():
    return {
        "user_messages": [{"role": "user", "content": "Hello there!"}],
        "agent_messages": [{"role": "assistant", "content": "Hi!"}],
        "processed_messages": [],
        "short_term_memory": [],
        "long_term_memory": {},
        "thread_id": "test-thread",
        "last_user_message": "Hello there!",
        "query": "test query"
    }

# Correzione del mock per ChatOpenAI
@pytest.fixture
def mock_llm():
    with patch('langchain_openai.ChatOpenAI') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.invoke.return_value.content = "Test response"
        yield mock_instance

# Test Base Agent Functionality
class TestBaseAgentBehavior:
    @pytest.mark.parametrize("agent_class", [
        SupervisorAgent, ResearcherAgent, GreetingAgent, MemoryAgent
    ])
    def test_return_type_compatibility(self, agent_class, memory_store, base_state):
        agent = agent_class(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process(base_state)
        assert isinstance(result, Command)
        assert isinstance(result.goto, str)
        assert result.goto in [
            "supervisor", "researcher", "greeting", 
            "manage_memory", "__end__"
        ]

    @pytest.mark.parametrize("agent_class", [
        SupervisorAgent, ResearcherAgent, GreetingAgent, MemoryAgent
    ])
    def test_error_handling(self, agent_class, memory_store):
        agent = agent_class(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process({})  # Invalid state
        assert isinstance(result, Command)
        assert result.goto == "__end__"
        assert isinstance(result.update, dict)
        assert "error" in result.update

def get_update_dict(cmd: Command[NodeType]) -> Dict[str, Any]:
    """Helper function to safely get update dictionary from Command"""
    return cmd.update if cmd.update is not None else {}

# Supervisor Agent Tests
class TestSupervisorAgent:
    def test_supervisor_initialization(self, memory_store):
        agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        assert agent.memory_store == memory_store
        assert hasattr(agent, 'llm')

    def test_determine_next_agent(self, memory_store, base_state, mock_llm):
        agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        agent.llm = mock_llm
        mock_llm.invoke.return_value.content = "GREETING"
        result = agent.determine_next_agent("Hello!", base_state)
        assert result == "GREETING"

    def test_validate_state(self, memory_store, base_state):
        agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        assert agent.validate_state(base_state) == True
        assert agent.validate_state({}) == False

    def test_invalid_state_handling(self, memory_store):
        agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process({"invalid": "state"})
        assert isinstance(result, Command)
        assert result.goto == "__end__"
        update_dict = get_update_dict(result)
        assert "error" in update_dict
        assert update_dict.get("terminate") is True

    def test_logging_behavior(self, memory_store, base_state, caplog):
        with caplog.at_level(logging.DEBUG):
            agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
            agent.process(base_state)
            assert any("Supervisor state" in record.message for record in caplog.records)

# Researcher Agent Tests
class TestResearcherAgent:
    def test_researcher_initialization(self, memory_store):
        agent = ResearcherAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        assert agent.memory_store == memory_store

    @patch('backend.src.agents.researcher_agent.perform_research')
    @patch('backend.src.agents.researcher_agent.modify_response')
    def test_process_valid_query(self, mock_modify, mock_research, memory_store, base_state):
        expected_result = "Research results"
        mock_research.return_value = expected_result
        mock_modify.return_value = f"Modified: {expected_result}"
        
        agent = ResearcherAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process(base_state)
        
        assert isinstance(result, Command)
        assert result.goto == "supervisor"  # Changed expectation from "__end__" to "supervisor"
        update_dict = get_update_dict(result)
        assert update_dict.get("research_result") == expected_result

    @patch('backend.src.agents.researcher_agent.perform_research', side_effect=Exception("Research failed"))
    def test_research_error_handling(self, mock_research, memory_store, base_state):
        agent = ResearcherAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process(base_state)

        assert isinstance(result, Command)
        assert result.goto == "__end__"
        update_dict = get_update_dict(result)
        assert update_dict.get("error") == "Research failed"
        assert update_dict.get("terminate") is True

# Greeting Agent Tests
class TestGreetingAgent:
    def test_greeting_initialization(self, memory_store):
        agent = GreetingAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        assert agent.memory_store == memory_store

    @patch('backend.src.agents.greeting_agent.generate_response')
    def test_process_greeting(self, mock_generate, memory_store, base_state):
        expected_response = "Hello user!"
        mock_generate.return_value = expected_response
        
        agent = GreetingAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        
        result = agent.process(base_state)
        assert isinstance(result, Command)
        update_dict = get_update_dict(result)
        agent_messages = update_dict.get("agent_messages", [])
        assert len(agent_messages) > 0
        assert agent_messages[-1]["content"] == expected_response  # Ensure response matches

    def test_greeting_with_invalid_message(self, memory_store, base_state):
        agent = GreetingAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        invalid_state = base_state.copy()
        invalid_state["last_user_message"] = 123  # Invalid type
        result = agent.process(invalid_state)
        assert isinstance(result, Command)
        assert result.goto == "__end__"
        update_dict = result.update if result.update is not None else {}
        assert "error" in update_dict

# Memory Agent Tests
class TestMemoryAgent:
    def test_memory_initialization(self, memory_store):
        agent = MemoryAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        assert agent.memory_store == memory_store

    def test_process_memory_update(self, memory_store, base_state):
        agent = MemoryAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        result = agent.process(base_state)
        assert isinstance(result, Command)
        update_dict = result.update if result.update is not None else {}
        assert "short_term_memory" in update_dict
        assert "long_term_memory" in update_dict

    def test_memory_error_handling(self, memory_store, base_state):
        agent = MemoryAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        memory_store.manage_short_term.side_effect = Exception("Memory error")
        result = agent.process(base_state)
        assert isinstance(result, Command)
        update_dict = result.update if result.update is not None else {}
        assert "error" in update_dict
        assert update_dict.get("memory_updated") is False

# Integration Tests
class TestAgentInteractions:
    def test_supervisor_to_researcher_flow(self, memory_store, base_state, mock_llm):
        supervisor = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        researcher = ResearcherAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        
        supervisor.llm = mock_llm
        mock_llm.invoke.return_value.content = "RESEARCHER"
        
        supervisor_result = supervisor.process(base_state)
        assert supervisor_result.goto == "researcher"

        researcher_state = base_state.copy()
        researcher_state.update(supervisor_result.update or {})
        researcher_result = researcher.process(researcher_state)
        assert researcher_result.goto == "supervisor"  # Changed expectation from "__end__" to "supervisor"

    def test_full_conversation_flow(self, memory_store, base_state, mock_llm):
        agents = {
            "supervisor": SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store),
            "greeting": GreetingAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store),
            "memory": MemoryAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        }

        agents["supervisor"].llm = mock_llm
        mock_llm.invoke.return_value.content = "GREETING"
        
        current_state = base_state.copy()
        for step in ["supervisor", "greeting", "memory"]:
            result = agents[step].process(current_state)
            assert isinstance(result, Command)
            current_state.update(result.update or {})

        assert "short_term_memory" in current_state

    def test_error_propagation(self, memory_store, base_state, mock_llm):
        supervisor = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
        supervisor.llm = mock_llm
        mock_llm.invoke.side_effect = Exception("LLM error")
        
        result = supervisor.process(base_state)
        assert isinstance(result, Command)
        assert result.goto == "__end__"
        update_dict = get_update_dict(result)
        assert "error" in update_dict
        assert update_dict.get("terminate") is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Ensure that all agent classes have implemented the `process` method correctly.
