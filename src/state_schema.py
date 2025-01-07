# src/state_schema.py

from typing import TypedDict, List, Dict, Any

class StateSchema(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    should_research: bool
    terminate: bool
    collected_info: str
    current_node: str  # Aggiungi questa chiave per tracciare il nodo corrente
