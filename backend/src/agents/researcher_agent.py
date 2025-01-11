# src/agents/researcher_agent.py
from langgraph.graph import END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from backend.src.tools.llm_tools import perform_research, modify_response
from backend.src.memory_store import MemoryStore
import logging
from typing import Literal

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def create_researcher_node(memory_store: MemoryStore):
    """Create researcher node with injected memory_store"""
    def researcher_node(state: dict) -> Command[Literal["supervisor", "__end__"]]:
        query = state.get("query", "").strip()
        if not query:
            return Command(goto=END, update={"terminate": False})

        try:
            research_result = perform_research(query)
            modified_resp = modify_response(research_result)
            memory_store.save_to_long_term_memory("research_results", query, {"result": research_result})
            
            return Command(
                goto="supervisor",
                update={
                    "research_result": research_result,
                    "modified_response": modified_resp,
                    "query": "",
                },
            )
        except Exception as e:
            logger.error(f"Errore nel nodo researcher: {e}")
            return Command(goto=END, update={"terminate": False})
            
    return researcher_node
