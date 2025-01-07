# src/langgraph_setup.py

from langgraph.graph import StateGraph, START, END
from src.agents.supervisor_agent import supervisor_node
from src.agents.researcher_agent import researcher_node
from src.agents.greeting_agent import greeting_agent
from src.state_schema import StateSchema  # Importa lo schema di stato
import logging

logger = logging.getLogger("LangGraphSetup")

# Inizializza il StateGraph con state_schema
builder = StateGraph(state_schema=StateSchema)

# Aggiungi i nodi
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("greeting", greeting_agent)

# Definisci le transizioni tra i nodi
builder.add_edge(START, "supervisor")       # Aggiungi questo collegamento
builder.add_edge("supervisor", "researcher")
builder.add_edge("supervisor", "greeting")
builder.add_edge("researcher", "supervisor")
builder.add_edge("greeting", "__end__")

# Compila il grafo
graph = builder.compile()
