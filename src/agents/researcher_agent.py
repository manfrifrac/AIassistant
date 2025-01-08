# src/agents/researcher_agent.py

from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from src.tools.llm_tools import perform_research
import logging
from typing import Literal

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

# Creazione del researcher agent
researcher_agent = create_react_agent(
    llm, tools=[], state_modifier="Sei un ricercatore. Analizza e rispondi con informazioni utili."
)

def researcher_node(state: dict) -> Command[Literal["greeting"]]:
    query = state.get("query", "").strip()
    if not query:
        return Command(goto="__end__", update={"terminate": True})

    try:
        research_result = perform_research(query)
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
        return Command(goto="__end__", update={"terminate": True})
