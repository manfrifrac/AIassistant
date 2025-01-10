from langgraph.store.memory import InMemoryStore  # Removed DBStore and LongTermStore
# from langgraph.store.db_store import DBStore, LongTermStore  # Removed as DBStore does not exist
from langgraph.graph import StateGraph, START, END
from src.agents.supervisor_agent import supervisor_node
from src.agents.researcher_agent import researcher_node
from src.agents.greeting_agent import greeting_node
from src.state.state_schema import StateSchema  # Assicurati che importi il StateSchema corretto
import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from typing import Literal
from src.agents.memory_agent import manage_memory_node  # Aggiungi questa importazione
from src.tools.embedding import model  # Import the model from embedding.py
import psycopg2  # Import psycopg2 for PostgreSQL interaction
from psycopg2.extras import RealDictCursor  # Optional: For dictionary-like cursor
import json  # Import json for data serialization
from src.memory_store import MemoryStore  # Importa MemoryStore direttamente
from src.state.state_manager import StateManager  # Importa StateManager

logger = logging.getLogger("LangGraphSetup")

# Define the embed function if not already defined
def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts).tolist()

# Rimuovi l'inizializzazione non necessaria di InMemoryStore se non utilizzata
# store = InMemoryStore(index={"embed": embed, "dims": 2})  # Rimosso

# Inizializza MemoryStore
memory_store = MemoryStore()

# Inizializza StateManager con StateSchema
state_manager = StateManager()
state_manager.set_state_schema(StateSchema)  # Passa il tipo, non un'istanza

# Initialize StateGraph senza 'memory_store' e 'long_term_store'
builder = StateGraph(
    state_schema=StateSchema,  # Passa il tipo
    # memory_store=memory_store,  # Rimosso
    # long_term_store=memory_store.long_term_store  # Rimosso
)

# Add nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("greeting", greeting_node)

# Add memory nodes
builder.add_node("manage_memory", manage_memory_node)

# Add a fallback node to handle cases where no assistant message is generated
def fallback_node(state: dict) -> Command[Literal["__end__"]]:
    fallback_message = {"role": "assistant", "content": "Mi dispiace, non sono sicuro di aver capito. Puoi ripetere?"}
    return Command(
        goto=END,
        update={
            "agent_messages": state.get("agent_messages", []) + [fallback_message],  # Assicurati di aggiungere solo un messaggio
        },
    )

# Add the fallback node to the graph
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

# Add long-term memory management if necessary
# Example: builder.add_node("long_term_memory_manager", long_term_memory_manager_node)

# Add checkpointer
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Debug logging
logger.debug(f"Graph nodes: {builder.nodes}")
logger.debug(f"Graph edges: {builder.edges}")

