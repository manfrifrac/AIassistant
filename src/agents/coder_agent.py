from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.python_repl_tool import execute_code
import logging

logger = logging.getLogger("CoderAgent")

def coder(state: MessagesState) -> Command[Literal["greeting_agent"]]:
    """
    Agente per gestire richieste di codifica ed eseguire codice Python.
    """
    last_message = state.get("original_message", "")
    logger.debug(f"Coder Agent ricevuto messaggio: {last_message}")

    try:
        # Esegui il codice Python ricevuto
        result = execute_code(last_message)
        response_message = f"Risultato del codice:\n{result}"
    except Exception as e:
        response_message = f"Errore nell'esecuzione del codice: {e}"

    logger.debug(f"Coder Agent aggiorna il messaggio: {response_message}")
    state["last_agent_response"] = response_message  # Salva il risultato per il Greeting Agent

    return Command(goto="greeting_agent", update={})
