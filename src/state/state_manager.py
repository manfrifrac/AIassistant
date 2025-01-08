import logging

logger = logging.getLogger("StateManager")

class StateManager:
    def __init__(self):
        self.state = {
            "user_messages": [],
            "agent_messages": [],
            "should_research": False,
            "terminate": False,
            "collected_info": "",
            "current_node": ""
        }

    # src/state/state_manager.py

    def update_state(self, updates: dict):
        """Aggiorna lo stato."""
        logger.debug(f"Aggiornamenti ricevuti: {updates}")
        for key, value in updates.items():
            if key in ["user_messages", "agent_messages"]:
                self.state.setdefault(key, []).extend(value)
                logger.debug(f"Aggiornato '{key}' con {value}")
            else:
                self.state[key] = value
                logger.debug(f"Aggiornato '{key}' a '{self.state[key]}'")





    def get_assistant_message(self):
        """Recupera l'ultimo messaggio generato dall'assistente."""
        messages = self.state.get("agent_messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and "content" in msg:
                return msg["content"]
        return None

