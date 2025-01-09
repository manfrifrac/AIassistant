from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import generate_response
import logging
from langgraph.graph import END  # Importa END se necessario

logger = logging.getLogger("GreetingAgent")

def greeting_node(state: dict) -> Command[Literal["supervisor", "__end__"]]:
    logger.debug(f"Invoking greeting_node with state: {state}")

    # Recupera l'ultimo messaggio dell'utente, i messaggi rilevanti e la risposta modificata
    last_user_message = state.get("last_user_message", "")
    relevant_messages = state.get("relevant_messages", [])
    modified_response = state.get("modified_response", "")

    logger.debug(f"Last user message: {last_user_message}")
    logger.debug(f"Relevant messages: {relevant_messages}")
    logger.debug(f"Modified response: {modified_response}")

    # Genera una risposta contestuale basata sui messaggi rilevanti
    try:
        # Combina i messaggi rilevanti in ordine cronologico
        conversation_history = relevant_messages + [{"role": "user", "content": last_user_message}]
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history if isinstance(msg, dict)]
        )
        logger.debug(f"Conversation history:\n{conversation_text}")

        # Genera una risposta utilizzando lo storico completo
        assistant_response = generate_response(conversation_text, last_user_message, modified_response)
        logger.debug(f"Assistant response: {assistant_response}")

        # Aggiungi la risposta al contesto
        updated_agent_messages = state.get("agent_messages", []) + [
            {"role": "assistant", "content": assistant_response}
        ]

        return Command(
            goto=END,  # Termina dopo la risposta
            update={"agent_messages": updated_agent_messages},
        )

    except Exception as e:
        logger.error(f"Errore nel greeting_node: {e}")
        return Command(goto=END, update={"terminate": True})
