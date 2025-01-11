from langgraph.types import Command
from typing import Literal
from backend.src.tools.llm_tools import generate_response, retrieve_from_long_term_memory, save_to_long_term_memory  # Import necessary memory functions
import logging
from langgraph.graph import END  # Importa END se necessario

logger = logging.getLogger("GreetingAgent")

def greeting_node(state: dict) -> Command[Literal["__end__"]]:
    logger.debug(f"Invoking greeting_node with state: {state}")  # Added state argument

    # Recupera l'ultimo messaggio dell'utente, i messaggi rilevanti e la risposta modificata
    last_user_message = state.get("last_user_message", "")
    relevant_messages = state.get("relevant_messages", [])
    modified_response = state.get("modified_response", "")

    logger.debug(f"Last user message: {last_user_message}")
    logger.debug(f"Messaggi rilevanti trovati: {relevant_messages}")  # Added relevant_messages argument
    logger.debug(f"Modified response: {modified_response}")

    # Genera una risposta contestuale basata sui messaggi rilevanti
    try:
        # Combina i messaggi rilevanti in ordine cronologico
        conversation_history = relevant_messages + [{"role": "user", "content": last_user_message}]
        conversation_text = "\n".join(
            [f"{msg['role']}:{msg['content']}" for msg in conversation_history if isinstance(msg, dict)]
        )
        logger.debug(f"Conversation history:\n{conversation_text}")  # Added conversation_text argument

        # Recupera il profilo utente dalla memoria a lungo termine
        thread_id = state.get("thread_id", "default-thread")
        user_profile = retrieve_from_long_term_memory("user_profiles", thread_id)
        if user_profile:
            conversation_text += f"\nUser preferences: {user_profile.get('last_greeting', 'N/A')}"
            logger.debug(f"Preferenze utente aggiunte al contesto: {user_profile.get('last_greeting', 'N/A')}")

        # Genera una risposta utilizzando lo storico completo
        assistant_response = generate_response(conversation_text, last_user_message, modified_response)
        logger.debug(f"Assistant response: {assistant_response}")  # Added assistant_response argument

        return Command(
            goto=END,
            update={
                "agent_messages": state.get("agent_messages", []) + [
                    {"role": "assistant", "content": assistant_response}
                ],
            },
        )

    except Exception as e:
        logger.error(f"Errore nel greeting_node: {e}", exc_info=True)
        return Command(goto=END, update={"terminate": False})  # Ensure terminate remains False
