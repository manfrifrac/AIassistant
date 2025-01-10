# src/state/state_manager.py

import logging
from typing import Type, get_origin, get_args  # Importa Type, get_origin, get_args
from src.state.state_schema import StateSchema  # Importa StateSchema
from src.memory_store import MemoryStore  # Importa MemoryStore
from typing_extensions import Annotated  # Ensure Annotated is imported

logger = logging.getLogger("StateManager")

class StateManager:
    def __init__(self):
        self.memory_store = MemoryStore()  # Inizializza MemoryStore
        self.state: StateSchema = {
            "user_messages": [],
            "agent_messages": [],
            "should_research": False,
            "terminate": False,  # Ensure default is False
            "valid_query": False,
            "query": "",
            "last_agent": "",
            "next_agent": "",  # Inizializza next_agent con un valore di default
            "should_terminate": False,
            "research_result": "",
            "last_user_message": "",
            "relevant_messages": [],
            "modified_response": "",
            "processed_messages": [],
            "long_term_memory": {},  # Initialize long_term_memory
            "short_term_memory": [],  # Initialize as a list
            # ...existing code...
        }
        logger.debug("StateManager inizializzato con stato vuoto e StateSchema impostato.")

    def set_state_schema(self, schema: Type[StateSchema]):
        """Imposta un nuovo schema per lo stato."""
        self.state_schema = schema
        logger.debug("StateSchema aggiornato in StateManager.")

    def update_state(self, updates: dict):
        """Aggiorna lo stato con i nuovi valori forniti, validandoli contro StateSchema."""
        if not isinstance(updates, dict):
            logger.error("Aggiornamenti dello stato non sono un dizionario.")
            return

        for key, value in updates.items():
            if key in self.state_schema.__annotations__:
                annotation = self.state_schema.__annotations__[key]
                origin = get_origin(annotation)

                # Check if the annotation is Annotated
                if origin is Annotated:
                    args = get_args(annotation)
                    base_type = get_origin(args[0]) or args[0]
                    reducer = args[1] if len(args) > 1 else None
                else:
                    base_type = origin if origin else annotation
                    reducer = None

                if base_type is list:
                    if reducer:
                        self.state[key] = reducer(self.state.get(key, []), value)
                        logger.debug(f"Aggiornato '{key}' usando reducer. Nuovo valore: {self.state[key]}")
                    else:
                        self.state[key].extend(value)
                        logger.debug(f"Aggiunti elementi a '{key}' senza reducer. Nuovo valore: {self.state[key]}")
                elif base_type is dict:
                    if reducer:
                        self.state[key] = reducer(self.state.get(key, {}), value)
                        logger.debug(f"Aggiornato '{key}' usando reducer. Nuovo valore: {self.state[key]}")
                    else:
                        self.state[key].update(value)
                        logger.debug(f"Aggiornato '{key}' come dict senza reducer. Nuovo valore: {self.state[key]}")
                else:
                    self.state[key] = value
                    logger.debug(f"Aggiornato '{key}' con valore diretto. Nuovo valore: {self.state[key]}")
            else:
                logger.warning(f"Chiave non riconosciuta nello stato: {key}")

        # Validazione dello stato aggiornato
        self.validate_state()

        # Log before deduplication
        logger.debug(f"Pre-deduplication processed_messages: {self.state.get('processed_messages', [])}")

        # Ensure terminate remains False
        self.state["terminate"] = False  

        # Elimina duplicati mantenendo l'ordine in 'processed_messages'
        seen = set()
        unique_processed = []
        for msg in self.state.get("processed_messages", []):
            if msg not in seen:
                seen.add(msg)
                unique_processed.append(msg)
        self.state["processed_messages"] = unique_processed

        if "long_term_memory" in updates:
            # Merge long-term memory updates
            self.memory_store.save_to_long_term_memory("long_term_namespace", "memory_key", updates["long_term_memory"])
            logger.debug("Memoria a lungo termine aggiornata.")
        
        # Log after deduplication
        logger.debug(f"Post-deduplication processed_messages: {self.state['processed_messages']}")
        logger.debug(f"Stato aggiornato: {self.state}")
        
        # **Log current agent_messages**
        logger.debug(f"Current agent_messages: {self.state.get('agent_messages', [])}")

    def validate_state(self):
        """Valida lo stato attuale contro lo StateSchema."""
        try:
            for key, value in self.state.items():
                if key in self.state_schema.__annotations__:
                    expected_type = self.state_schema.__annotations__[key]
                    origin = get_origin(expected_type)
                    args = get_args(expected_type)
                    
                    if origin is not None:
                        if origin is list:
                            if not isinstance(value, list):
                                logger.warning(f"Tipo inatteso per '{key}': aspettato list, ottenuto {type(value)}")
                        elif origin is dict:
                            if not isinstance(value, dict):
                                logger.warning(f"Tipo inatteso per '{key}': aspettato dict, ottenuto {type(value)}")
                        # Add more origin checks if necessary
                    else:
                        if not isinstance(value, expected_type):
                            logger.warning(f"Tipo inatteso per '{key}': aspettato {expected_type}, ottenuto {type(value)}")
            logger.debug("Validazione dello stato completata con successo.")
        except Exception as e:
            logger.error(f"Errore durante la validazione dello stato: {e}")
    
    def get_assistant_message(self) -> str:
        """Recupera l'ultimo messaggio generato dall'assistente."""
        agent_messages = self.state.get("agent_messages", [])
        if agent_messages:
            return agent_messages[-1].get("content", "")
        return ""