# src/agents/researcher_agent.py
from langgraph.graph import END
from langgraph.types import Command
from backend.src.tools.llm_tools import perform_research, modify_response
from backend.src.memory_store import MemoryStore
import logging
from typing import Literal, Dict, Any, Optional
from backend.src.agents.base import BaseAgent, NodeType  # Fix import
from uuid import uuid4

logger = logging.getLogger("ResearcherAgent")

class ResearcherAgent(BaseAgent):
    """
    The ResearcherAgent:
    Input:
      - {user_message}
      - {context} (stm_data, ltm_data, etc.)
    Operations:
      - Performs research or query resolution
    Output:
      - {assistant_message}
    """
    def __init__(self, agent_id, config, memory_store):
        super().__init__(agent_id, config)
        self.memory_store = memory_store
        self.logger = logger

    def validate_state(self, state: Dict[str, Any]) -> bool:
        if not isinstance(state, dict):
            logger.error("Invalid state type")
            return False
            
        if "query" not in state or not isinstance(state["query"], str):
            logger.error("Missing or invalid query in state")
            return False
            
        return bool(state["query"].strip())

    def process(self, state: Dict[str, Any]) -> Command[NodeType]:
        if not self.validate_state(state):
            return Command(goto="__end__", update={
                "error": "Invalid state",
                "terminate": True
            })

        try:
            # Retrieve context
            context = {
                "stm_data": state.get("stm_data", []),
                "ltm_data": state.get("ltm_data", {}),
            }
            research_result = perform_research(state["query"])
            modified_resp = modify_response(research_result)
            
            if self.memory_store:
                self.memory_store.save_to_long_term_memory(
                    "research_results", 
                    state["query"], 
                    {"result": research_result}
                )

            return Command(
                goto="supervisor",  # Changed from "__end__" to "supervisor"
                update={
                    "research_result": research_result,
                    "modified_response": modified_resp,
                    "query": "",
                    "next_agent": "supervisor"  # Explicitly set next_agent to supervisor
                }
            )

        except Exception as e:
            logger.error(f"Research error: {str(e)}", exc_info=True)
            return Command(goto="__end__", update={  # Ensure 'error' is included
                "error": str(e),
                "terminate": True
            })

def create_researcher_node(memory_store):
    agent = ResearcherAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
    return agent.process
