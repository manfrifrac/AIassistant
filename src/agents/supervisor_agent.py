# src/agents/supervisor_agent.py

from typing import Literal, TypedDict
from langchain_openai import ChatOpenAI  # Import corretto
import logging

logger = logging.getLogger("SupervisorAgent")

members = ["researcher"]
options = members + ["FINISH"]

system_prompt = (
    "Sei un supervisore incaricato di gestire una conversazione tra i seguenti agenti: "
    f"{', '.join(members)}. "
    "Quando ricevi un comando dall'utente, determina quale agente deve agire successivamente. "
    "Rispondi esclusivamente con il nome dell'agente appropriato (es. 'researcher') oppure con 'FINISH' se il lavoro è completato. "
    "Non fornire ulteriori spiegazioni o testo aggiuntivo. "
    "Esempi:\n"
    "- Se l'utente dice 'Quali sono le ultime notizie sul cambiamento climatico?', rispondi con 'researcher'.\n"
    "- Se l'utente dice 'Grazie, hai finito il lavoro', rispondi con 'FINISH'."
)

class Router(TypedDict):
    """Definisce l'agente successivo o la fine del processo."""
    next: Literal["researcher", "FINISH"]

llm = ChatOpenAI(model="gpt-3.5-turbo")

def supervisor_node(state: dict) -> dict:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state.get("messages", [])

    try:
        response = llm.invoke(input=messages)
        next_agent = response.content.strip().lower()

        logger.debug(f"Supervisor ha ricevuto 'next_agent': {next_agent}")

        if next_agent == "finish":
            logger.debug("Supervisor ha scelto di terminare la conversazione.")
            return {
                "update": {"terminate": True},
                "goto": "greeting"
            }
        elif next_agent in members:
            # Estrai la query dall'ultimo messaggio dell'utente
            user_message = state["messages"][-1]["content"]
            query = user_message  # Puoi applicare ulteriori elaborazioni se necessario
            logger.debug(f"Supervisor sta passando la query: {query}")
            return {
                "update": {"should_research": True, "query": query},
                "goto": next_agent
            }
        else:
            logger.warning(f"Opzione sconosciuta: {next_agent}. Terminazione della conversazione.")
            return {
                "update": {"terminate": True},
                "goto": "greeting"
            }
    except Exception as e:
        logger.error(f"Errore nel supervisor_node: {e}")
        return {
            "update": {"terminate": True},
            "goto": "greeting"
        }
