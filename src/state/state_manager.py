# src/state/state_manager.py

import logging
from src.state_schema import StateSchema

logger = logging.getLogger("StateManager")

class StateManager:
    def __init__(self):
        self.state = {
            "user_messages": [],
            "agent_messages": [],
            "should_research": False,
            "terminate": False,
            "collected_info": "",
            "valid_query": False,
            "query": "",
            "last_agent": "",
            "next_agent": "",  # Inizializza next_agent con un valore di default
            "should_terminate": False,
            "research_result": "",
            "last_user_message": "",
            "relevant_messages": [],
            "modified_response": ""
        }
        logger.debug("StateManager inizializzato con stato vuoto.")

    def update_state(self, updates: dict):
        """Aggiorna lo stato con i nuovi valori forniti."""
        self.state.update(updates)
        logger.debug(f"Stato aggiornato: {self.state}")

    def get_assistant_message(self) -> str:
        """Recupera l'ultimo messaggio generato dall'assistente."""
        agent_messages = self.state.get("agent_messages", [])
        if agent_messages:
            return agent_messages[-1].get("content", "")
        return ""
