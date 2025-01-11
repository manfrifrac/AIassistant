from langgraph.types import Command
from langgraph.graph import END
from typing import Literal, Any, Dict, List
from backend.src.memory_store import MemoryStore  # Replace CoreComponents import
import logging

logger = logging.getLogger("MemoryAgent")

def create_memory_node(memory_store: MemoryStore):
    """Create memory node with injected memory_store"""
    def memory_node(state: dict) -> Command[Literal["__end__"]]:
        try:
            # Extract current memories
            short_term = state.get("short_term_memory", [])
            long_term = state.get("long_term_memory", {})
            
            # Get latest message info
            latest_message = {
                "user_message": state.get("last_user_message", ""),
                "agent_response": state.get("agent_messages", [])[-1]["content"] if state.get("agent_messages") else "",
                "context": {
                    "last_agent": state.get("last_agent"),
                    "query": state.get("query", ""),
                    "research_result": state.get("research_result", "")
                }
            }
            
            # Update short-term memory with the latest message
            updated_short_term = memory_store.manage_short_term(short_term, [latest_message])
            
            # Extract and update long-term memory if important information is present
            important_info = memory_store.extract_relevant_info(latest_message)
            updated_long_term = long_term  # Initialize updated_long_term
            if important_info:
                updated_long_term = memory_store.manage_long_term(long_term, important_info)
                memory_store.save_to_long_term_memory(
                    "conversation_history", 
                    state.get("thread_id", "default"), 
                    updated_long_term
                )
            
            return Command(
                goto=END,
                update={
                    "short_term_memory": updated_short_term,
                    "long_term_memory": updated_long_term if important_info else long_term,
                    "user_messages": state.get("user_messages", []),
                    "processed_messages": state.get("processed_messages", [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in memory management: {e}")
            return Command(goto=END, update={})

    return memory_node

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