class StateManager:
    def __init__(self):
        self.state = {
            "user_messages": [],
            "agent_messages": [],
            "should_research": False,
            "terminate": False,
            "collected_info": "",
            "current_node": "supervisor"
        }

    def update_state(self, updates: dict):
        """Aggiorna lo stato."""
        logger.debug(f"Aggiornamenti ricevuti: {updates}")
        self.state.update(updates)
        logger.debug(f"Stato aggiornato: {self.state}")


    def get_assistant_message(self):
        """Recupera l'ultimo messaggio generato dall'assistente."""
        return next(
            (msg["content"] for msg in reversed(self.state.get("agent_messages", [])) if msg.get("role") == "assistant"),
            None
        )

