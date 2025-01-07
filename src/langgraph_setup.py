# src/langgraph_setup.py

from langgraph.graph import StateGraph, START, END
from src.agents.supervisor_agent import supervisor_node
from src.agents.researcher_agent import researcher_node
from src.agents.greeting_agent import greeting_node
from src.state_schema import StateSchema
import logging

logger = logging.getLogger("LangGraphSetup")

# Inizializza il StateGraph con state_schema
builder = StateGraph(state_schema=StateSchema)

# Aggiungi i nodi
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("greeting", greeting_node)

# Definisci le transizioni tra i nodi
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "researcher")
builder.add_edge("supervisor", "greeting")
builder.add_edge("researcher", "greeting")  # Evita il ciclo tornando a "greeting"
builder.add_edge("greeting", END)  # Punta a END per terminare

# Compila il grafo
graph = builder.compile()
