# src/agents/researcher_agent.py
from langgraph.graph import END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from src.tools.llm_tools import perform_research, modify_response
import logging
from typing import Literal

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")


# src/agents/researcher_agent.py

def researcher_node(state: dict) -> Command[Literal["supervisor", "__end__"]]:
    query = state.get("query", "").strip()
    if not query:
        return Command(goto=END, update={"terminate": True})

    try:
        # Recupera il risultato della ricerca
        research_result = perform_research(query)

        # Modifica la risposta
        modified_resp = modify_response(research_result)

        # Aggiorna lo stato senza perdere contesto
        updated_agent_messages = state.get("agent_messages", []) + [
            {"content": research_result, "role": "assistant"}
        ]

        return Command(
            goto="supervisor",
            update={
                "agent_messages": updated_agent_messages,
                "research_result": research_result,
                "modified_response": modified_resp,  # Added modified_response
                "query": "",  # Resetta la query dopo la ricerca
            },
        )

    except Exception as e:
        logger.error(f"Errore nel nodo researcher: {e}")
        return Command(goto=END, update={"terminate": True})
