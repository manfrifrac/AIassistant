from langgraph.types import Command
from langgraph.graph import END
from typing import Literal, Any, Dict, List
from src.memory_store import MemoryStore  # Importa MemoryStore
import logging  # Import logging module

logger = logging.getLogger("MemoryAgent")  # Initialize logger

# Inizializza un'istanza di MemoryStore
memory_store = MemoryStore()

def manage_memory_node(state: dict) -> Command[Literal["__end__"]]:
    # Logic to handle short-term and long-term memory
    short_term = state.get("short_term_memory", [])
    long_term = state.get("long_term_memory", {})

    # Gestisci la memoria a lungo termine
    long_term_memory_updates = {
        "long_term_memory": memory_store.update_long_term(long_term)
    }

    # Update state with short-term and long-term memory
    state = memory_store.manage_short_term(short_term, state.get("last_user_message", ""))

    return Command(
        goto=END,
        update={
            "short_term_memory": memory_store.update_short_term(short_term),
            **long_term_memory_updates,
        },
    )

def manage_memory_reducer(existing: Any, new: Any) -> Any:
    """
    Combina la memoria esistente con la nuova memoria.
    
    Args:
        existing (Any): La memoria esistente.
        new (Any): La nuova memoria da aggiungere.
    
    Returns:
        Any: La memoria combinata.
    """
    try:
        if isinstance(existing, list) and isinstance(new, list):
            # Per short_term_memory: unisci le liste mantenendo l'ordine
            combined = existing + new
            logger.debug(f"Reducer combinato per list: {len(combined)} elementi.")
            return combined
        elif isinstance(existing, dict) and isinstance(new, dict):
            # Per long_term_memory: aggiorna il dizionario con i nuovi dati
            combined = {**existing, **new}
            logger.debug(f"Reducer combinato per dict: {len(combined)} chiavi.")
            return combined
        else:
            logger.warning("Tipi di dati incompatibili per il reducer.")
            return new  # Fallback
    except Exception as e:
        logger.error(f"Errore nel reducer: {e}")
        return existing  # Fallback in caso di errore