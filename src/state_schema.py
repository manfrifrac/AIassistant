# src/state_schema.py

from typing import TypedDict, List, Dict, Any

class StateSchema(TypedDict, total=False):
    user_messages: List[Dict[str, Any]]
    agent_messages: List[Dict[str, Any]]  # Messaggi generati dall'agente
    should_research: bool
    terminate: bool
    collected_info: str
    valid_query: bool
    query: str
    last_agent: str
    next_agent: str  # Aggiungi il prossimo agente
    should_terminate: bool  # Nuova chiave per segnalare la terminazione
    research_result: str  # Aggiungi il risultato della ricerca
    last_user_message: str  # Aggiungi l'ultimo messaggio dell'utente
    relevant_messages: List[Dict[str, Any]]  # Aggiungi i messaggi rilevanti
    modified_response: str  # Aggiungi la risposta modificata
    # Rimuovi 'current_node' se presente
