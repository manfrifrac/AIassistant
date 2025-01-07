from langgraph.graph import StateGraph, MessagesState, START
from src.agents.supervisor import supervisor
from src.agents.spotify_agent import spotify_agent
from src.agents.time_agent import time_agent
from src.agents.greeting_agent import greeting_agent
from src.agents.coder_agent import coder

# Configura il LangGraph StateGraph
builder = StateGraph(MessagesState)

# Aggiungi tutti i nodi al grafo
builder.add_node("supervisor", supervisor)
builder.add_node("spotify_agent", spotify_agent)
builder.add_node("time_agent", time_agent)
builder.add_node("greeting_agent", greeting_agent)
builder.add_node("coder", coder)

# Definisci il flusso iniziale
builder.add_edge(START, "greeting_agent")  # Il Greeting Agent è il primo
builder.add_edge("greeting_agent", "supervisor")  # Reindirizza al supervisore
builder.add_edge("supervisor", "spotify_agent")
builder.add_edge("supervisor", "time_agent")
builder.add_edge("supervisor", "coder")
builder.add_edge("spotify_agent", "greeting_agent")
builder.add_edge("time_agent", "greeting_agent")
builder.add_edge("coder", "greeting_agent")

# Compila il grafo
app = builder.compile()
