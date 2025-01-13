from langgraph.store.memory import InMemoryStore  # Removed DBStore and LongTermStore
# from langgraph.store.db_store import DBStore, LongTermStore  # Removed as DBStore does not exist
from langgraph.graph import MessageGraph  # Only import MessageGraph
from langgraph.constants import START, END  # Use constants instead of graph imports
from backend.src.state.state_schema import StateSchema  # Assicurati che importi il StateSchema corretto
import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from typing import Literal, Dict, Any, AsyncIterator, Union, Annotated, TypeVar, Optional, Protocol, Sequence, Coroutine, cast, List, ClassVar, Type  # Add type hints
from backend.src.tools.embedding import model  # Import the model from embedding.py
import psycopg2  # Import psycopg2 for PostgreSQL interaction
from psycopg2.extras import RealDictCursor  # Optional: For dictionary-like cursor
import json  # Import json for data serialization
from langchain.schema.runnable import RunnableConfig

# Add imports for agent creation functions
from backend.src.agents.supervisor_agent import create_supervisor_node
from backend.src.agents.greeting_agent import create_greeting_node
from backend.src.agents.researcher_agent import create_researcher_node
from backend.src.agents.memory_agent import create_memory_node
from backend.src.memory_store import MemoryStore

# Remove the import of CoreComponents to prevent circular dependency
# from backend.src.core_components import CoreComponents  # Remove this line
# Remove MemoryStore import since it will be passed from CoreComponents

# Update Protocol definition to match langgraph types
class CompiledStateGraph(Protocol):
    def invoke(
        self, 
        input: Dict[str, Any], 
        config: Optional[RunnableConfig] = None,
        **kwargs: Any
    ) -> Dict[str, Any]: ...

    async def ainvoke(
        self, 
        input: Dict[str, Any],
        config: Optional[RunnableConfig] = None,
        **kwargs: Any
    ) -> Coroutine[Any, Any, Dict[str, Any]]: ...

logger = logging.getLogger("LangGraphSetup")

# Define the embed function if not already defined
def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts).tolist()

# Rimuovi l'inizializzazione non necessaria di InMemoryStore se non utilizzata
# store = InMemoryStore(index={"embed": embed, "dims": 2})  # Rimosso

# Remove direct instantiation of StateManager
# state_manager = StateManager()

# Modify functions to accept state_manager as a parameter if needed


def error_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle errors in the graph execution"""
    return {
        **state,
        "error": True,
        "error_message": "Error in processing flow",
        "terminate": True
    }

# Initialize graph variable
graph = None

# Add new function for message aggregation
def append_agent_messages(existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Combines existing and new agent messages
    Args:
        existing: Current list of messages
        new: New messages to add
    Returns:
        Combined list of messages
    """
    # Handle None cases
    if not existing:
        return new or []
    if not new:
        return existing
        
    # Combine messages and deduplicate
    all_messages = existing + new
    seen = set()
    unique_messages = []
    
    for msg in all_messages:
        msg_key = str(sorted(msg.items()))
        if msg_key not in seen:
            seen.add(msg_key)
            unique_messages.append(msg)
            
    return unique_messages

def get_graph(memory_store: Optional[MemoryStore] = None) -> Optional[CompiledStateGraph]:
    """Get the initialized graph instance"""
    global graph
    if graph is not None:
        return cast(Optional[CompiledStateGraph], graph)

    try:
        # Create workflow
        workflow = MessageGraph()
        
        # Check if memory_store is provided
        if memory_store is None:
            raise ValueError("MemoryStore is required")
            
        # Create nodes from imported functions
        supervisor_node = create_supervisor_node(memory_store)
        greeting_node = create_greeting_node(memory_store)
        researcher_node = create_researcher_node(memory_store)
        memory_handler_node = create_memory_node(memory_store)
        
        # Add nodes
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("greeting", greeting_node)
        workflow.add_node("researcher", researcher_node)
        workflow.add_node("memory_handler", memory_handler_node)
        workflow.add_node("error", error_handler)
        
        # Add edges
        workflow.add_edge(START, "supervisor")
        
        # Add conditional edges with proper routing
        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x.get("next_agent", "error"),
            {
                "greeting": "greeting",
                "researcher": "researcher", 
                "error": "error"
            }
        )
        
        workflow.add_edge("greeting", "memory_handler")
        workflow.add_edge("memory_handler", END)
        workflow.add_edge("researcher", END)
        workflow.add_edge("error", END)
        
        graph = workflow.compile()
        return cast(Optional[CompiledStateGraph], graph)
        
    except Exception as e:
        logger.error(f"Error creating graph: {e}", exc_info=True)
        return None

def set_graph(new_graph) -> None:
    """Set the graph instance"""
    global graph
    graph = new_graph

# Export functions
__all__ = ['initialize_graph', 'get_graph', 'set_graph', 'execute_graph']

def initialize_graph(memory_store: Optional[MemoryStore] = None):
    """Initialize and validate the graph"""
    try:
        graph = get_graph(memory_store)
        if not graph:
            raise ValueError("Graph initialization returned None")
            
        # Validate graph has required methods
        if not (hasattr(graph, 'invoke') or hasattr(graph, 'ainvoke')):
            raise ValueError("Graph missing required invoke/ainvoke methods")
            
        return graph
    except Exception as e:
        logger.error(f"Error initializing graph: {e}")
        raise RuntimeError(f"Failed to initialize graph: {e}")

async def execute_graph(graph: CompiledStateGraph, state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the graph with given state"""
    try:
        logger.debug(f"Executing graph with state: {state}")
        if not graph:
            logger.error("Graph not initialized")
            return {}
            
        # Format initial message
        initial_message = {
            "role": "user",
            "content": state.get("last_user_message", ""),
            "state": state
        }
            
        config = RunnableConfig(configurable={"debug": True})
        result = await graph.ainvoke(initial_message, config=config)
            
        # Handle async result properly
        if isinstance(result, dict):
            return result.get("state", state)
        else:
            # For Coroutine results, await them
            final_result = await result
            return final_result.get("state", state)
        
    except Exception as e:
        logger.error(f"Error executing graph: {e}", exc_info=True)
        return {
            **state,
            "error": True,
            "error_message": str(e)
        }

