from typing import TypedDict, List, Dict, Any

class StateSchema(TypedDict, total=False):
    user_messages: List[Dict[str, Any]]
    agent_messages: List[Dict[str, Any]]  # Messaggi generati dall'agente
    should_research: bool
    terminate: bool
    collected_info: str
    current_node: str
    valid_query: bool
    query: str
