from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from src.agents.supervisor_agent import supervisor_node
from src.agents.researcher_agent import researcher_node
from src.agents.greeting_agent import greeting_node
from src.state_schema import StateSchema
import logging

logger = logging.getLogger("LangGraphSetup")

# Initialize StateGraph
builder = StateGraph(state_schema=StateSchema)

# Add managed value
# builder.add_managed_value("next_agent", "greeting")
# builder.map_state_field("next_agent", "next_agent")

# Add nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("greeting", greeting_node)

# Define initial transition
builder.add_edge(START, "supervisor")

# Define conditional edges from supervisor
builder.add_conditional_edges(
    source="supervisor",
    path=lambda state: (
        END if state.get("terminate", False)
        else "greeting" if state.get("last_agent") == "researcher"
        else "researcher" if state.get("query")
        else "greeting"
    )
)

# Define conditional edges from researcher
builder.add_conditional_edges(
    source="researcher",
    path=lambda state: (
        END if state.get("terminate", False)
        else "supervisor"
    )
)

# Define edges from greeting
builder.add_edge("greeting", END)

# Add checkpointer
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Debug logging
logger.debug(f"Graph nodes: {builder.nodes}")
logger.debug(f"Graph edges: {builder.edges}")