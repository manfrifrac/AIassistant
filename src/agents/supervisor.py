from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import analyze_intent
import logging

logger = logging.getLogger("SupervisorAgent")

def supervisor(state: MessagesState) -> Command[Literal["spotify_agent", "time_agent", "coder", "greeting_agent", "__end__"]]:
    """
    Analizza l'intento, smista la richiesta agli agenti e passa il risultato al GreetingAgent.
    """
    user_messages = [msg for msg in state["messages"] if msg.get("type") == "human"]
    if not user_messages:
        logger.warning("Nessun messaggio dell'utente trovato.")
        return Command(goto="__end__", update={})

    # Recupera l'ultimo messaggio dell'utente
    last_user_message = user_messages[-1]["content"]
    logger.debug(f"Messaggio ricevuto dall'utente: {last_user_message}")

    # Usa LLMTools per analizzare l'intento
    intent = analyze_intent(last_user_message)
    logger.debug(f"Intento analizzato: {intent}")

    valid_intents = {"spotify_agent", "time_agent", "coder", "greeting_agent"}
    if intent not in valid_intents:
        logger.warning(f"Intento non valido ({intent}). Passaggio al GreetingAgent.")
        state["last_agent_response"] = f"Non ho capito bene cosa intendi con '{last_user_message}'. Puoi riformulare?"
        return Command(goto="greeting_agent", update={})

    # Salva il contesto del comando
    state["original_message"] = last_user_message
    state["current_intent"] = intent
    logger.debug(f"Reindirizzamento all'agente: {intent}")
    return Command(goto=intent, update={})
