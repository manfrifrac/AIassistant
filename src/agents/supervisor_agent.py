# src/agents/supervisor_agent.py

from typing import List, Dict, Any
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
import logging
from src.tools.custom_tools import make_handoff_tool
from langgraph.types import Command
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger("SupervisorAgent")

# Definisci i membri (agenti) gestiti dal Supervisor
members = ["researcher"]
options = members + ["FINISH"]

# Crea strumenti di handoff
handoff_to_researcher = make_handoff_tool("researcher")
handoff_to_greeting = make_handoff_tool("greeting")

system_prompt = (
    "Sei un supervisore incaricato di gestire una conversazione tra i seguenti agenti: "
    f"{', '.join(members)}. "
    "Quando ricevi un comando dall'utente, determina quale agente deve agire successivamente. "
    "Se l'utente fornisce una domanda o una richiesta di informazioni specifiche, passa la query al researcher. "
    "Se l'utente fa una dichiarazione generale o desidera terminare la conversazione, rispondi con 'FINISH'. "
    "Rispondi esclusivamente con il nome dell'agente appropriato (es. 'researcher') oppure con 'FINISH'. "
    "Non fornire ulteriori spiegazioni o testo aggiuntivo. "
    "Esempi:\n"
    "- Se l'utente dice 'Quali sono le ultime notizie sul cambiamento climatico?', rispondi con 'researcher'.\n"
    "- Se l'utente dice 'Grazie, hai finito il lavoro', rispondi con 'FINISH'.\n"
    "- Se l'utente dice 'Ciò mi sta ascoltando', rispondi con 'FINISH'."
)

llm = ChatOpenAI(model="gpt-3.5-turbo")


def determine_next_agent(user_message: str) -> str:
    # Messaggi al modello
    model_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    # Chiamata al modello
    response = llm.invoke(input=model_messages)
    next_agent = response.content.strip().upper()

    # Debug della risposta
    logger.debug(f"Supervisor ha ricevuto 'next_agent': {next_agent}")

    # Validazione
    if next_agent in ["RESEARCHER", "FINISH"]:
        return next_agent
    else:
        logger.warning(f"Risposta non valida dal modello: {next_agent}. Default a 'FINISH'.")
        return "FINISH"


def get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """Estrae l'ultimo messaggio dell'utente."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return "Nessun messaggio valido trovato."


def supervisor_node(state: dict) -> Command[Literal["researcher", "greeting", "__end__"]]:
    try:
        last_user_message = get_last_user_message(state.get("user_messages", []))
        if not last_user_message:
            logger.warning("Nessun messaggio dell'utente trovato.")
            return Command(goto="__end__", update={"terminate": True})

        next_agent = determine_next_agent(last_user_message)
        logger.debug(f"Supervisor ha determinato il prossimo agente: {next_agent}")

        if next_agent == "FINISH":
            return Command(
                goto="__end__",
                update={
                    "terminate": True,
                    "collected_info": last_user_message,
                    "agent_messages": state.get("agent_messages", []) + [{"role": "assistant", "content": "Conversazione terminata."}]
                }
            )

        elif next_agent.lower() == "researcher":
            return Command(
                goto="researcher",
                update={
                    "query": last_user_message, 
                    "valid_query": True, 
                    "agent_messages": state.get("agent_messages", []) + [{"role": "assistant", "content": "Sto cercando informazioni..."}]
                }
            )
        elif next_agent.lower() == "greeting":
            return Command(
                goto="greeting",
                update={
                    "collected_info": last_user_message, 
                    "agent_messages": state.get("agent_messages", []) + [{"role": "assistant", "content": "Ciao! Come posso aiutarti?"}]
                }
            )
        else:
            return Command(goto="__end__", update={"terminate": True})
    except Exception as e:
        logger.error(f"Errore nel supervisor_node: {e}")
        return Command(goto="__end__", update={"terminate": True})
