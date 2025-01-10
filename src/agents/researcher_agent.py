# src/agents/researcher_agent.py
from langgraph.graph import END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from src.tools.llm_tools import perform_research, modify_response, save_to_long_term_memory
import logging
from typing import Literal

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def researcher_node(state: dict) -> Command[Literal["supervisor", "__end__"]]:
    query = state.get("query", "").strip()
    if not query:
        return Command(goto=END, update={"terminate": False})  # Ensure terminate remains False

    try:
        # Recupera il risultato della ricerca
        research_result = perform_research(query)

        # Modifica la risposta
        modified_resp = modify_response(research_result)

        # Salva il risultato della ricerca nella memoria a lungo termine
        save_to_long_term_memory("research_results", query, {"result": research_result})

        return Command(
            goto="supervisor",
            update={
                "research_result": research_result,
                "modified_response": modified_resp,
                "query": "",  # Resetta la query dopo la ricerca
            },
        )

    except Exception as e:
        logger.error(f"Errore nel nodo researcher: {e}")
        return Command(goto=END, update={"terminate": False})  # Ensure terminate remains False
