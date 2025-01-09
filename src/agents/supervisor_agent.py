from langgraph.graph import END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
import logging
from typing import List, Dict, Any
from typing_extensions import Literal
from src.tools.llm_tools import vectorize_messages, semantic_search

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
            {"role": "user", "content": f"Previous context: {context}\n\nUser message: {user_message}"}
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
        return {next_agent}

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

def supervisor_node(state: dict) -> Command[Literal["researcher", "greeting", "__end__"]]:
    try:
        # Verifica se la conversazione deve terminare
        if state.get("terminate", False):
            logger.debug("Richiesta di terminazione rilevata.")
            return Command(goto=END, update={})

        # Verifica la presenza di messaggi dell'utente
        user_messages = state.get("user_messages", [])
        if not user_messages:
            logger.warning("Nessun messaggio dell'utente trovato nello stato.")
            return Command(goto=END, update={"terminate": True})

        # Recupera l'ultimo messaggio dell'utente
        last_user_message = get_last_user_message(user_messages)
        if not last_user_message:
            logger.warning("L'ultimo messaggio dell'utente è vuoto o non valido.")
            return Command(goto=END, update={"terminate": True})

        # Controlla se la query è già stata gestita
        if state.get("last_agent") == "researcher" and state.get("query") == last_user_message:
            logger.debug("La query è stata già gestita. Termino il ciclo.")
            relevant_messages = []
            if state.get("agent_messages"):
                relevant_messages = find_relevant_messages(state, last_user_message)
            modified_response = ""
            if state.get("research_result"):
                modified_response = modify_response(state.get("research_result", ""))
                relevant_messages.append({"role": "assistant", "content": state.get("research_result", "")})
            state_updates = {
                "last_user_message": last_user_message,
                "relevant_messages": relevant_messages,
                "modified_response": modified_response,
            }
            return Command(goto="greeting", update=state_updates)

        # Determina il prossimo agente con il nuovo contesto
        next_agent = determine_next_agent(last_user_message, state)
        
        # Prepara gli aggiornamenti di stato base
        state_updates = {
            "last_agent": str(next_agent).lower(),  # Aggiorna l'ultimo agente
            "next_agent": str(next_agent).lower(),  # Imposta il prossimo agente
        }

        # Se l'ultimo agente era researcher, passa sempre attraverso greeting per processare la risposta
        if state.get("last_agent") == "researcher":
            logger.debug("Ultimo agente era researcher, processo la risposta con greeting")
            relevant_messages = []
            if state.get("agent_messages"):
                relevant_messages = find_relevant_messages(state, last_user_message)
            
            modified_response = ""
            if state.get("research_result"):
                modified_response = modify_response(state.get("research_result", ""))
                # Aggiungi il risultato della ricerca ai messaggi rilevanti
                relevant_messages.append({"role": "assistant", "content": state.get("research_result", "")})
            
            state_updates.update({
                "last_user_message": last_user_message,
                "relevant_messages": relevant_messages,
                "modified_response": modified_response,
            })
            return Command(goto="greeting", update=state_updates)
        
        # Altrimenti, procedi normalmente in base all'agente determinato
        if next_agent == "RESEARCHER":
            state_updates["query"] = last_user_message
            return Command(goto="researcher", update=state_updates)
        
        # Se è GREETING, prepara le informazioni rilevanti
        relevant_messages = []
        if state.get("agent_messages"):
            relevant_messages = find_relevant_messages(state, last_user_message)
        
        modified_response = ""
        if state.get("research_result"):
            modified_response = modify_response(state.get("research_result", ""))
        
        state_updates.update({
            "last_user_message": last_user_message,
            "relevant_messages": relevant_messages,
            "modified_response": modified_response,
        })
        
        return Command(goto="greeting", update=state_updates)

    except Exception as e:
        logger.error(f"Errore nel supervisor_node: {e}")
        return Command(goto=END, update={"terminate": True})

def modify_response(research_result: str) -> str:
    """Modifica la risposta utilizzando un prompt e un LLM."""
    try:
        prompt = (
            "Hai raccolto le seguenti informazioni: "
            f"{research_result}. "
            "Estrapola le informazioni più importanti e fornisci una risposta concisa e chiara."
        )
        response = llm.invoke(input=[{"role": "system", "content": prompt}])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Errore durante la modifica della risposta: {e}")
        return research_result  # Fallback alla risposta originale

def find_relevant_messages(state: dict, last_user_message: str) -> List[Dict[str, Any]]:
    """Trova i messaggi rilevanti basati sull'ultimo messaggio dell'utente."""
    try:
        # Vettorializza i messaggi precedenti
        previous_messages = state.get("user_messages", []) + state.get("agent_messages", [])
        if not previous_messages:
            logger.debug("Nessun messaggio precedente trovato.")
            return []
        vectors = vectorize_messages(previous_messages)
        logger.debug(f"Vettori dei messaggi: {vectors}")

        # Trova i messaggi rilevanti utilizzando una ricerca semantica
        relevant_messages = semantic_search(vectors, last_user_message, previous_messages)
        logger.debug(f"Messaggi rilevanti trovati: {relevant_messages}")
        return relevant_messages
    except ValueError as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []
    except Exception as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []