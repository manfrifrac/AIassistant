# src/state_schema.py

from typing import TypedDict, List, Dict, Any, Annotated, Literal
import operator
from langgraph.types import Command
from typing_extensions import Annotated
import json  # Ensure json is imported if used elsewhere

def manage_list(old: list, new: list) -> list:
    """Combines lists without duplicates, maintaining order."""
    combined = old + new
    unique = []
    seen = set()
    for item in combined:
        item_key = str(item) if not isinstance(item, dict) else str(sorted(item.items()))
        if item_key not in seen:
            seen.add(item_key)
            unique.append(item)
    return unique

# Fix reducer signatures to match (a, b) -> c pattern
def manage_short_term_memory(old: list, new: list) -> list:
    """Updates short-term memory maintaining only recent messages."""
    combined = manage_list(old, new)
    # Keep only last 10 items internally
    return combined[-10:]

def manage_long_term_memory(old: dict, new: dict) -> dict:
    """Updates long-term memory by merging dictionaries."""
    updated = old.copy()
    for key, value in new.items():
        if key in updated and isinstance(updated[key], list):
            updated[key] = manage_list(updated[key], [value])
        else:
            updated[key] = value
    return updated

class StateSchema(TypedDict, total=False):
    user_messages: Annotated[List[Dict[str, Any]], manage_list]
    agent_messages: Annotated[List[Dict[str, Any]], manage_list]
    processed_messages: Annotated[List[str], manage_list]
    short_term_memory: Annotated[List[Dict[str, Any]], manage_short_term_memory]
    long_term_memory: Annotated[Dict[str, Any], manage_long_term_memory]
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
    # Optional: Add fallback-related fields if necessary
