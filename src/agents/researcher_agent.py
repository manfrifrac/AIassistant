# src/agents/researcher_agent.py

from langgraph.types import Command
from langchain_openai import ChatOpenAI
from src.tools.llm_tools import perform_research
import logging
from typing import Literal
from langgraph.graph import END

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")


def researcher_node(state: dict) -> Command[Literal["greeting"]]:
    query = state.get("query", "").strip()
    logger.debug(f"Researcher Agent riceve la query: {query}")
    
    if not query:
        logger.warning("La query è vuota. Termino la conversazione.")
        return Command(goto=END, update={"terminate": True})

    try:
        research_result = perform_research(query)
        logger.debug(f"Risultati della ricerca: {research_result}")
        return Command(
            goto="greeting",
            update={
                "agent_messages": state.get("agent_messages", []) + [
                    {"content": research_result, "role": "assistant"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Errore nel nodo Researcher: {e}")
        return Command(goto=END, update={"terminate": True})
