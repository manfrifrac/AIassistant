# src/agents/researcher_agent.py

from typing_extensions import Literal
from langchain_openai import ChatOpenAI
import logging
from langgraph.types import Command
from src.tools.llm_tools import perform_research
logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def researcher_node(state: dict) -> Command[Literal["greeting"]]:
    query = state.get("query", "")
    logger.debug(f"Researcher ha ricevuto la query: '{query}'")
    if not query:
        logger.debug("Nessuna query fornita.")
        return Command(goto="greeting", update={"terminate": True})

    logger.debug(f"Researcher sta eseguendo la ricerca per la query: {query}")
    research_result = perform_research(query)
    logger.debug(f"Researcher produce la risposta: {research_result}")
    return Command(
        goto="greeting",
        update={"collected_info": research_result}
    )
