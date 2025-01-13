# src/tools/llm_tools.py

from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
import os

# Rimuoviamo le importazioni non necessarie poiché vengono da embedding.py
from backend.src.tools.embedding import model, vectorize_messages, semantic_search

# Load environment variables
load_dotenv()

logger = logging.getLogger("LLMTools")

# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo")

def perform_research(query: str) -> str:
    """Perform research using LLM."""
    try:
        logger.debug(f"Executing research for query: {query}")
        if not query:
            raise ValueError("Empty query")
            
        response = llm.invoke(
            input=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": f"Research query: {query}"}
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)

    except Exception as e:
        logger.error(f"Research error: {e}")
        raise

def generate_response(conversation_text: str, last_user_message: str, modified_response: str = "") -> str:
    """Generate response based on conversation context and user message."""
    try:
        logger.debug(f"Generating response for: {last_user_message}")
        if not last_user_message:
            raise ValueError("Empty user message")
            
        response = llm.invoke(
            input=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {conversation_text}\nUser: {last_user_message}\nAdditional info: {modified_response}"}
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)

    except Exception as e:
        logger.error(f"Response generation error: {e}")
        raise

def modify_response(research_result: str) -> str:
    """Modify response using the research result."""
    try:
        logger.debug(f"Modifying response with research result")
        if not research_result:
            raise ValueError("Empty research result")
            
        return f"Modificata: {research_result}"
    except Exception as e:
        logger.error(f"Response modification error: {e}")
        raise

def save_to_long_term_memory(namespace: str, key: str, data: Dict[str, Any]) -> None:
    """Salva i dati nella memoria a lungo termine."""
    try:
        from backend.src.memory_store import MemoryStore  # Moved import inside the function
        memory_store = MemoryStore()
        memory_store.save_to_long_term_memory(namespace, key, data)
        logger.debug(f"Salvato nella memoria a lungo termine: {namespace}/{key}")
    except Exception as e:
        logger.error(f"Errore nel salvataggio della memoria a lungo termine: {e}")

def retrieve_from_long_term_memory(namespace: str, key: str) -> Dict[str, Any]:
    """Recupera i dati dalla memoria a lungo termine."""
    try:
        from backend.src.memory_store import MemoryStore  # Moved import inside the function
        memory_store = MemoryStore()
        item = memory_store.retrieve_from_long_term_memory(namespace, key)
        logger.debug(f"Recuperato dalla memoria a lungo termine: {namespace}/{key}")
        return item
    except Exception as e:
        logger.error(f"Errore nel recupero della memoria a lungo termine: {e}")
        return {}

def search_long_term_memory(namespace: str, query: str) -> List[Dict[str, Any]]:
    """Esegue una ricerca nella memoria a lungo termine."""
    try:
        from backend.src.memory_store import MemoryStore  # Moved import inside the function
        memory_store = MemoryStore()
        results = memory_store.search_long_term_memory(namespace, query)
        if not results:
            logger.debug(f"Nessun risultato trovato nella memoria a lungo termine per: {query}")
            return []
        logger.debug(f"Risultati della ricerca nella memoria a lungo termine per '{query}': {results}")
        return results
    except Exception as e:
        logger.error(f"Errore durante la ricerca nella memoria a lungo termine: {e}")
        return []

def some_condition(key: str, value: Any) -> bool:
    """Definisce la condizione per filtrare i dati rilevanti nella memoria."""
    # Esempio: Filtra solo le query non vuote
    return bool(value.get("query")) if "query" in key else False

def extract_relevant_data(memory: dict) -> dict:
    """Estrae i dati rilevanti dalla memoria."""
    relevant_data = {
        key: value for key, value in memory.items() if some_condition(key, value)
    }
    logger.debug(f"Dati rilevanti estratti: {relevant_data}")
    return relevant_data

def should_update_profile(command: str) -> bool:
    """Determina se aggiornare il profilo utente basato sul comando."""
    # Esempio: aggiorna il profilo se il comando contiene determinate parole chiave
    keywords = ["preferenze", "interessi", "profilo"]
    return any(keyword in command.lower() for keyword in keywords)

def extract_important_info(message: str) -> Optional[str]:
    """Estrai informazioni importanti dal messaggio."""
    keywords = ["preferenza", "importante", "informazione"]
    if any(keyword in message.lower() for keyword in keywords):
        return message
    return None

# Remove the placeholder duplicate functions
# def perform_research(query: str) -> str:
#     """Performs research based on the query."""
#     # ...existing implementation...
#     pass  # Implementation remains unchanged

# def modify_response(research_result: str) -> str:
#     """Modifies the research result before sending to the user."""
#     # ...existing implementation...
#     pass  # Implementation remains unchanged

# def generate_response(conversation_text: str, last_user_message: str, modified_response: str) -> str:
#     """Generates a response based on the conversation context."""
#     # ...existing implementation...
#     pass  # Implementation remains unchanged

__all__ = [
    'perform_research',
    'generate_response',
    'modify_response',
    'save_to_long_term_memory',
    'retrieve_from_long_term_memory',
    'search_long_term_memory',
    'some_condition',
    'extract_relevant_data',
    'should_update_profile',
    'extract_important_info',
    'vectorize_messages',  # Added export
    'semantic_search',     # Added export
    # ...other exports...
]
