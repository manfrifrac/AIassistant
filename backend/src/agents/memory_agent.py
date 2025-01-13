from langgraph.types import Command
from langgraph.graph import END
from typing import Literal, Any, Dict, List
from backend.src.memory_store import MemoryStore
import logging
from uuid import uuid4
from backend.src.agents.base import BaseAgent, NodeType

logger = logging.getLogger("MemoryAgent")

class MemoryAgent(BaseAgent):
    """
    The MemoryAgent:
    Input:
      - {user_message}
      - {context}
      - {assistant_message}
      - {session_id}
    Operations:
      - Updates short-term memory (stm_data)
      - Updates long-term memory (ltm_data)
      - Logs the interaction
    Output:
      - {updated_stm}, {updated_ltm}, {interaction_log}
    """
    def __init__(self, agent_id, config, memory_store):
        super().__init__(agent_id, config)
        self.memory_store = memory_store
        self.logger = logger

    def validate_state(self, state: Dict[str, Any]) -> bool:
        if not isinstance(state, dict):
            logger.error("Invalid state type")
            return False

        required_keys = ["user_messages", "agent_messages"]
        missing_keys = [k for k in required_keys if k not in state]
        
        if missing_keys:
            logger.error(f"Missing required keys: {missing_keys}")
            return False

        return True

    def process(self, state: dict) -> Command[NodeType]:
        """Process the current state and update memory."""
        try:
            # Update long-term memory
            thread_id = state.get("thread_id", "default-thread")
            messages = {
                "user_messages": state.get("user_messages", []),
                "agent_messages": state.get("agent_messages", [])
            }
            
            updated_long_term = self.memory_store.manage_long_term(thread_id, messages)
            
            # Return command without name parameter
            return Command(
                goto=END,
                update={
                    **state,
                    "long_term_memory": updated_long_term
                }
            )
        except Exception as e:
            logger.error(f"Error in memory management: {e}", exc_info=True)
            return Command(goto=END, update=state)

def create_memory_node(memory_store: MemoryStore):
    agent = MemoryAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
    return agent.process

# Keep the reducer function as is
def manage_memory_reducer(existing: Any, new: Any) -> Any:
    """
    Combine existing memory with new memory entries.

    Args:
        existing (Any): The existing memory.
        new (Any): The new memory to be added.

    Returns:
        Any: The combined memory.
    """
    try:
        if isinstance(existing, list) and isinstance(new, list):
            # Combine short-term memory lists while maintaining order
            combined = existing + new
            logger.debug(f"Reducer combinato per list: {len(combined)} elementi.")
            return combined
        elif isinstance(existing, dict) and isinstance(new, dict):
            # Merge long-term memory dictionaries
            combined = {**existing, **new}
            logger.debug(f"Reducer combinato per dict: {len(combined)} chiavi.")
            return combined
        else:
            logger.warning("Incompatible data types for reducer.")
            return new  # Fallback
    except Exception as e:
        logger.error(f"Errore nel reducer: {e}")
        return existing  # Fallback in caso di errore