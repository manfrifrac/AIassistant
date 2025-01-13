from backend.src.agents.base import BaseAgent, NodeType
from langgraph.graph import END
from langgraph.types import Command
from typing import Literal, Dict, Any
from backend.src.tools.llm_tools import generate_response
import logging
from uuid import uuid4

logger = logging.getLogger("GreetingAgent")

class GreetingAgent(BaseAgent):
    """
    The GreetingAgent:
    Input:
      - {user_message}
      - {context} (stm_data, ltm_data, etc.)
    Operations:
      - Generates a personalized greeting message
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

        required_keys = ["last_user_message", "agent_messages"]
        missing_keys = [k for k in required_keys if k not in state]
        
        if missing_keys:
            logger.error(f"Missing required keys: {missing_keys}")
            return False
            
        if not isinstance(state["last_user_message"], str):
            logger.error("Invalid last_user_message type")
            return False
            
        if not isinstance(state["agent_messages"], list):
            logger.error("Invalid agent_messages type")
            return False
            
        return True

    def process(self, state: Dict[str, Any]) -> Command[NodeType]:
        if not self.validate_state(state):
            return Command(goto="__end__", update={
                "error": "State validation failed",
                "terminate": True
            })

        try:
            # Use the mock response directly
            conversation_text = state.get("conversation_text", "")
            last_user_message = state.get("last_user_message", "")
            modified_response = state.get("modified_response", "")
            
            # Retrieve context
            context = {
                "stm_data": state.get("stm_data", []),
                "ltm_data": state.get("ltm_data", {}),
            }
            
            assistant_response = generate_response(
                conversation_text,
                last_user_message,
                modified_response
            )
            logger.debug(f"Assistant response: {assistant_response}")  # Optional debug

            current_messages = state.get("agent_messages", []).copy()
            current_messages.append({
                "role": "assistant",
                "content": assistant_response
            })

            # Optional: insert assistant_message into Interazioni here

            return Command(
                goto="supervisor",  # Changed from "__end__" to "supervisor"
                update={
                    "agent_messages": current_messages,
                    "next_agent": "supervisor"  # Explicitly set next_agent to supervisor
                },
            )

        except Exception as e:
            logger.error(f"Greeting error: {str(e)}", exc_info=True)
            return Command(goto="__end__", update={
                "error": str(e),
                "terminate": True
            })

def create_greeting_node(memory_store):
    agent = GreetingAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
    return agent.process
