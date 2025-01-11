from langgraph.store.memory import InMemoryStore  # Removed DBStore and LongTermStore
# from langgraph.store.db_store import DBStore, LongTermStore  # Removed as DBStore does not exist
from langgraph.graph import StateGraph, START, END
from backend.src.state.state_schema import StateSchema  # Assicurati che importi il StateSchema corretto
import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from typing import Literal, Dict, Any, AsyncIterator, Union  # Add type hints
from backend.src.tools.embedding import model  # Import the model from embedding.py
import psycopg2  # Import psycopg2 for PostgreSQL interaction
from psycopg2.extras import RealDictCursor  # Optional: For dictionary-like cursor
import json  # Import json for data serialization
# Remove the import of CoreComponents to prevent circular dependency
# from backend.src.core_components import CoreComponents  # Remove this line
# Remove MemoryStore import since it will be passed from CoreComponents

logger = logging.getLogger("LangGraphSetup")

# Define the embed function if not already defined
def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts).tolist()

# Rimuovi l'inizializzazione non necessaria di InMemoryStore se non utilizzata
# store = InMemoryStore(index={"embed": embed, "dims": 2})  # Rimosso

# Remove direct instantiation of StateManager
# state_manager = StateManager()

# Modify functions to accept state_manager as a parameter if needed

def initialize_graph(memory_store):  # Type hint removed to avoid import
    """Initialize the graph with the provided memory_store instance"""
    # Import the factory functions
    from backend.src.agents import (
        create_supervisor_node,
        create_researcher_node,
        create_greeting_node,
        create_memory_node
    )

    builder = StateGraph(state_schema=StateSchema)

    # Convert AsyncIterator to dict and ensure synchronous execution
    def wrap_node(func):
        async def wrapped(state: Union[Dict, AsyncIterator[Dict[str, Any]]], **kwargs):
            try:
                # Handle both dict and AsyncIterator inputs
                if isinstance(state, dict):
                    state_dict = state
                else:
                    # Convert AsyncIterator to dict
                    state_list = []
                    async for item in state:
                        state_list.append(item)
                    state_dict = {k: v for d in state_list for k, v in d.items()}
                
                # Execute the node function
                result = func(state_dict)
                return result

            except Exception as e:
                logger.error(f"Error in node wrapper: {e}")
                raise

        return wrapped

    # Create nodes with memory_store
    supervisor_node = create_supervisor_node(memory_store)
    researcher_node = create_researcher_node(memory_store)
    greeting_node = create_greeting_node(memory_store)
    memory_node = create_memory_node(memory_store)

    # Add nodes
    builder.add_node("supervisor", wrap_node(supervisor_node))
    builder.add_node("researcher", wrap_node(researcher_node))
    builder.add_node("greeting", wrap_node(greeting_node))
    builder.add_node("manage_memory", wrap_node(memory_node))

    # Add a fallback node to handle cases where no assistant message is generated
    def fallback_node(state: dict) -> Command[Literal["__end__"]]:
        fallback_message = {"role": "assistant", "content": "Mi dispiace, non sono sicuro di aver capito. Puoi ripetere?"}
        return Command(
            goto=END,
            update={
                "agent_messages": state.get("agent_messages", []) + [fallback_message],  # Assicurati di aggiungere solo un messaggio
            },
        )
    
    builder.add_node("fallback", fallback_node)

    # Define edges including memory transitions
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        source="supervisor",
        path=lambda state: "greeting" if state.get("last_agent") in {"researcher", "greeting"} else "researcher"
    )
    builder.add_edge("manage_memory", END)
    builder.add_edge("researcher", "manage_memory")
    builder.add_edge("greeting", "manage_memory")

    # Add checkpointer
    checkpointer = MemorySaver()
    compiled_graph = builder.compile(checkpointer=checkpointer)

    # Debug logging
    logger.debug(f"Graph nodes: {builder.nodes}")
    logger.debug(f"Graph edges: {builder.edges}")
    logger.debug("Graph compilation completed")
    
    return compiled_graph

# Initialize graph variable
graph = None

def get_graph():
    """Get the initialized graph instance"""
    global graph
    return graph

def set_graph(new_graph):
    """Set the graph instance"""
    global graph
    graph = new_graph

