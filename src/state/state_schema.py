# src/state_schema.py

from typing import TypedDict, List, Dict, Any, Annotated, Literal
import operator
from langgraph.types import Command
from typing_extensions import Annotated
import json  # Ensure json is imported if used elsewhere

def manage_list(old: list, new: list) -> list:
    """Combina due liste aggiungendo elementi senza duplicati."""
    combined = old + new
    unique = []
    seen = set()
    for item in combined:
        # Serialize dicts to JSON strings for hashing, keep other types as is
        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
        if item_key not in seen:
            seen.add(item_key)
            unique.append(item)
    return unique

def manage_short_term_memory(old: list, new: list) -> list:
    """Aggiorna la memoria a breve termine limitando il numero di messaggi."""
    combined = old + new
    # Mantiene solo gli ultimi 100 messaggi
    return combined[-100:]

def manage_long_term_memory(old: dict, new: dict) -> dict:
    """Aggiorna la memoria a lungo termine."""
    return {**old, **new}

class StateSchema(TypedDict, total=False):
    user_messages: List[Dict[str, Any]]
    agent_messages: Annotated[list, manage_list]  # Messaggi generati dall'agente con reducer
    processed_messages: Annotated[List[str], manage_list]  # Modificato per contenere solo testi
    should_research: bool
    terminate: bool
    valid_query: bool
    query: str
    last_agent: str
    next_agent: str  # Aggiungi il prossimo agente
    should_terminate: bool  # Nuova chiave per segnalare la terminazione
    research_result: str  # Aggiungi il risultato della ricerca
    last_user_message: str  # Aggiungi l'ultimo messaggio dell'utente
    relevant_messages: List[Dict[str, Any]]  # Aggiungi i messaggi rilevanti
    modified_response: str  # Aggiungi la risposta modificata
    short_term_memory: Annotated[list, manage_short_term_memory]
    long_term_memory: Annotated[dict, manage_long_term_memory]  # Added long_term_memory
    # Optional: Add fallback-related fields if necessary
