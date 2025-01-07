# src/agents/researcher_agent.py
from langchain_openai import ChatOpenAI

from src.tools.llm_tools import perform_research
import logging

logger = logging.getLogger("ResearcherAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def researcher_node(state: dict) -> dict:
    try:
        # Estrai la query dell'utente
        user_query = state.get("user_query", "Nessuna query fornita.")
        logger.debug(f"Researcher riceve la query: {user_query}")

        # Esegui la ricerca basata sulla query
        research_result = perform_research(user_query)
        response = f"Ecco i risultati della tua ricerca: {research_result}"
        logger.debug(f"Researcher produce la risposta: {response}")

        # Aggiorna lo stato con le informazioni raccolte
        return {
            "update": {
                "messages": [{"type": "assistant", "content": response}],
                "collected_info": research_result,
                "should_research": False  # Reset della flag
            },
            "goto": "supervisor"
        }
    except Exception as e:
        logger.error(f"Errore nel researcher_node: {e}")
        return {
            "update": {"terminate": True},
            "goto": "greeting"
        }
