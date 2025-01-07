from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import generate_response
import logging

logger = logging.getLogger("GreetingAgent")

def greeting_agent(state: MessagesState) -> Command[Literal["supervisor", "__end__"]]:
    """
    Prepara la risposta finale per l'utente.
    """
    # Recupera il contesto e la risposta dell'agente precedente
    user_message = state.get("original_message", "")
    agent_response = state.get("last_agent_response")
    logger.debug(f"Greeting Agent risponde con il risultato: {agent_response}")

    # Usa LLMTools per generare una risposta naturale
    response = generate_response(
        user_message=user_message,
        agent_feedback=agent_response
    )
    logger.debug(f"Risposta generata: {response}")

    return Command(
        update={"messages": [{"type": "assistant", "content": response}]},
        goto="supervisor"
    )
