from langgraph.graph import END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
import logging
from typing import List, Dict, Any
from typing_extensions import Literal
from src.tools.llm_tools import vectorize_messages, semantic_search, save_to_long_term_memory, retrieve_from_long_term_memory, extract_relevant_data  # Ensure extract_relevant_data is defined
import json  # Ensure json is imported if needed
from src.memory_store import MemoryStore  # Updated import

logger = logging.getLogger("SupervisorAgent")

# Definisci i membri (agenti) gestiti dal Supervisor
members = ["researcher", "greeting"]

system_prompt = """You are a sophisticated supervisor managing a conversation flow.
Analyze the user's message carefully to determine whether to use the RESEARCHER or GREETING agent.

Use RESEARCHER when:
- The user asks a specific question
- Requests factual information
- Needs detailed explanations
- Shows curiosity about a topic

Use GREETING when:
- The user makes casual conversation
- Expresses emotions or personal statements
- Responds to previous answers
- Makes acknowledgments or confirmations
- The message is primarily social/interactive

Current conversation context and message history are important for making this decision.
Respond ONLY with 'RESEARCHER' or 'GREETING' in uppercase.
"""

llm = ChatOpenAI(model="gpt-3.5-turbo")

# Inizializza un'istanza di MemoryStore se necessario
memory_store = MemoryStore()

def determine_next_agent(user_message: str, state: dict) -> str:
    try:
        logger.debug(f"[DETERMINE_AGENT] Input state: {state}")
        logger.debug(f"[DETERMINE_AGENT] User message: {user_message}")

        # Create context
        context = {
            "current_message": user_message,
            "previous_messages": [m.get("content", "") for m in state.get("user_messages", [])[-3:]],
            "previous_responses": [m.get("content", "") for m in state.get("agent_messages", [])[-3:]],
            "last_agent": state.get("last_agent", "")
        }
        logger.debug(f"[DETERMINE_AGENT] Created context: {context}")

        # Create model messages
        model_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Previous context: {json.dumps(context)}\n\nUser message: {user_message}"}
        ]
        logger.debug(f"[DETERMINE_AGENT] Model input: {model_messages}")

        # Get model response
        response = llm.invoke(input=model_messages)
        next_agent = response.content.strip().upper()
        logger.debug(f"[DETERMINE_AGENT] Raw model response: {response.content}")

        if next_agent not in {"RESEARCHER", "GREETING"}:
            logger.warning(f"[DETERMINE_AGENT] Invalid response: {next_agent}, defaulting to GREETING")
            return "GREETING"

        logger.debug(f"[DETERMINE_AGENT] Final decision: {next_agent}")
        return next_agent

    except Exception as e:
        logger.error(f"[DETERMINE_AGENT] Error: {str(e)}", exc_info=True)
        return "GREETING"

def get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """Estrae l'ultimo messaggio dell'utente."""
    try:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        logger.warning("Nessun messaggio valido trovato nei messaggi dell'utente.")
        return ""
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dell'ultimo messaggio utente: {e}")
        return ""

def _format_debug_state(state: dict) -> dict:
    """Formatta lo stato per debug log"""
    return {
        'last_message': state.get('last_user_message', ''),
        'next_agent': state.get('next_agent', ''),
        'processed_count': len(state.get('processed_messages', []))
    }

def supervisor_node(state: dict) -> Command[Literal["researcher", "greeting", "manage_memory", "__end__"]]:
    try:
        logger.debug(f"Supervisor state: {state}")  # Added state argument
        # Initialize 'processed_messages' if not present
        if "processed_messages" not in state:
            state["processed_messages"] = []
            logger.debug("Initialized 'processed_messages' in state.")

        # Check for user messages
        user_messages = state.get("user_messages", [])
        if not user_messages:
            logger.warning("No user messages found in state.")
            return Command(goto="manage_memory", update={"terminate": False})

        # Retrieve the last user message
        last_user_message = get_last_user_message(user_messages)
        if not last_user_message:
            logger.warning("The last user message is empty or invalid.")
            return Command(goto="manage_memory", update={"terminate": False})

        logger.debug(f"Last user message: {last_user_message}")  # Added last_user_message argument

        # Check if the message has already been processed
        if last_user_message in state["processed_messages"]:
            logger.debug("The user message has already been processed. No action needed.")
            return Command(goto="manage_memory", update={})

        # Retrieve information from long-term memory
        thread_id = state.get("thread_id", "default-thread")
        
        # Rimuovi eventuali riferimenti a builder.memory_store se presenti
        # Usa direttamente l'istanza di memory_store
        user_profile = memory_store.retrieve_from_long_term_memory("user_profiles", thread_id)
        if user_profile:
            context = {}  # Initialize context
            context.update({"user_profile": user_profile})
            logger.debug(f"User profile added to context: {user_profile}")

        # Determine the next agent with the new context
        next_agent = determine_next_agent(last_user_message, state)
        logger.debug(f"Determined agent type: {next_agent}")  # Added next_agent argument
        
        state_updates = {
            "last_user_message": last_user_message,
            "relevant_messages": find_relevant_messages(state, last_user_message),
            "processed_messages": state.get("processed_messages", []) + [last_user_message]
        }

        if next_agent == "RESEARCHER":
            state_updates.update({
                "last_agent": "researcher",
                "query": last_user_message,
                "next_agent": "manage_memory"  # Set next transition
            })
            logger.debug("Moving to researcher node")
            return Command(goto="researcher", update=state_updates)
            
        elif next_agent == "GREETING":
            state_updates.update({
                "last_agent": "greeting",
                "next_agent": "manage_memory"  # Set next transition
            })
            logger.debug("Moving to greeting node")
            return Command(goto="greeting", update=state_updates)
            
        else:
            logger.warning(f"Unrecognized agent type: {next_agent}")
            state_updates["next_agent"] = "manage_memory"
            return Command(goto="manage_memory", update=state_updates)

    except Exception as e:
        logger.error(f"Error in supervisor: {e}", exc_info=True)
        return Command(goto="manage_memory", update={"terminate": False})

def find_relevant_messages(state: dict, last_user_message: str) -> List[Dict[str, Any]]:
    """Trova i messaggi rilevanti basati sull'ultimo messaggio dell'utente."""
    try:
        # Vettorializza i messaggi precedenti
        previous_messages = state.get("user_messages", []) + state.get("agent_messages", [])
        if not previous_messages:
            logger.debug("Nessun messaggio precedente trovato.")
            return []
        vectors = vectorize_messages(previous_messages)
        #logger.debug(f"Vettori dei messaggi: {vectors}")

        # Trova i messaggi rilevanti utilizzando una ricerca semantica
        relevant_messages = semantic_search(vectors, last_user_message, previous_messages)
        logger.debug(f"Messaggi rilevanti trovati: {relevant_messages}")  # Added relevant_messages argument
        return relevant_messages
    except ValueError as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []
    except Exception as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []