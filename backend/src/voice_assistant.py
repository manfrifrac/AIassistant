# src/voice_assistant.py

import logging
import speech_recognition as sr
from src.state.state_manager import StateManager
from src.langgraph_setup import graph, END
from src.audio.audio_handler import AudioHandler
from src.utils.error_handler import ErrorHandler
from src.memory_store import MemoryStore  # Importa MemoryStore
from typing import Optional  # Import Optional
from src.tools.llm_tools import retrieve_from_long_term_memory, save_to_long_term_memory, should_update_profile  # Import necessary memory functions
import asyncio
from langchain.schema.runnable import RunnableConfig

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self, state_manager: StateManager):
        self.listening = True
        self.state_manager = state_manager
        self.audio_handler = AudioHandler()
        self.memory_store = MemoryStore()
        self.thread_id = self.generate_thread_id()
        self.is_web_mode = False  # Aggiungiamo un flag per il web mode
        logger.debug("VoiceAssistant initialization completed.")

    def generate_thread_id(self) -> str:
        """Genera un thread_id sequenziale basato sui thread esistenti."""
        try:
            last_id = self.memory_store.get_last_thread_id()
            new_id = last_id + 1
            thread_id = f"thread-{new_id}"
            logger.info(f"Generato nuovo thread_id: {thread_id}")
            
            # Salva il nuovo thread
            if self.memory_store.save_thread(thread_id):
                logger.debug(f"Thread ID {thread_id} salvato con successo")
            else:
                logger.warning(f"Impossibile salvare il thread ID {thread_id}")
            
            return thread_id
        except Exception as e:
            logger.error(f"Errore nella generazione del thread_id: {e}")
            fallback_id = "thread-1"
            logger.info(f"Usando thread_id di fallback: {fallback_id}")
            return fallback_id

    async def process_command(self, command: str):
        """Elabora il comando trascritto."""
        try:
            # Configura il RunnableConfig con il thread ID
            config = RunnableConfig(configurable={"thread_id": self.thread_id})

            # Log dello stato iniziale formattato
            formatted_state = {k: v for k, v in self.state_manager.state.items() if not isinstance(v, (list, dict)) or len(str(v)) < 100}
            logger.debug("Stato iniziale: %s", formatted_state)

            # Log del comando utente
            logger.debug("Aggiunto messaggio utente: %s", command)

            # Crea una copia dello stato corrente
            state = self.state_manager.state.copy()
            logger.debug("Stato iniziale: %s", state)  # Added state argument

            # Aggiungi il messaggio dell'utente
            if "user_messages" not in state:
                state["user_messages"] = []
            state["user_messages"].append({"role": "user", "content": command})
            logger.debug("Aggiunto messaggio utente: %s", command)

            # Esegui il grafo
            command_result = graph.invoke(state, config=config)
            logger.debug("Risultato dell'esecuzione del grafo: %s", command_result)  # Added command_result argument

            # **Update the entire state instead of extracting 'update'**
            if not isinstance(command_result, dict):
                logger.error("Risultato del comando non è un dizionario.")
                command_result = {}

            self.state_manager.update_state(command_result)
            
            # **Add logging for updated state**
            logger.debug("Stato dopo update_state: %s", self.state_manager.state)  # Added state_manager.state argument

            # Usa MemoryStore direttamente
            self.memory_store.save_to_long_term_memory("session_logs", self.thread_id, self.state_manager.to_dict())
            assistant_message = self.state_manager.get_assistant_message()
            logger.debug(f"Messaggio dell'assistente: {assistant_message}")

            # Salva il thread_id nel database
            self.memory_store.save_to_long_term_memory("threads", self.thread_id, {"thread_id": self.thread_id})
            logger.debug(f"Thread ID salvato nel database: {self.thread_id}")

            # Riproduci la risposta solo se c'è un messaggio e NON siamo in web mode
            if assistant_message:
                if not self.is_web_mode:
                    self.audio_handler.speak(assistant_message)
            else:
                logger.warning("Messaggio dell'assistente è vuoto. Nessun audio da riprodurre.")

        except Exception as e:
            logger.error(f"Errore nell'elaborazione del comando: {e}", exc_info=True)

    def update_state(self, last_user_message: str):
        """Aggiorna lo stato con la memoria a breve e lungo termine."""
        if last_user_message:
            # Aggiorna short_term_memory con l'ultimo messaggio
            if 'short_term_memory' not in self.state_manager.state:
                self.state_manager.state['short_term_memory'] = []
            self.state_manager.state['short_term_memory'].append({"message": last_user_message})

            # Mantieni solo gli ultimi 10 messaggi
            if len(self.state_manager.state['short_term_memory']) > 10:
                self.state_manager.state['short_term_memory'] = self.state_manager.state['short_term_memory'][-10:]

            # Estrai informazioni importanti e aggiorna long_term_memory
            important_info = self.extract_important_info(last_user_message)
            if important_info:
                if 'long_term_memory' not in self.state_manager.state:
                    self.state_manager.state['long_term_memory'] = {}
                if 'important_info' not in self.state_manager.state['long_term_memory']:
                    self.state_manager.state['long_term_memory']['important_info'] = []
                self.state_manager.state['long_term_memory']['important_info'].append(important_info)

    def extract_important_info(self, message: str) -> Optional[str]:
        """Estrai informazioni importanti dal messaggio."""
        keywords = ["preferenza", "importante", "informazione"]
        if any(keyword in message.lower() for keyword in keywords):
            return message
        return None

    def listen_and_process(self):
        """Ascolta il comando vocale e lo elabora."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("In ascolto...")
            audio = recognizer.listen(source)
            try:
                # Update the language parameter to match whisper's expected format
                command = recognizer.recognize_whisper(audio, language="italian", model="base")
                logger.info(f"Comando riconosciuto: {command}")
                asyncio.run(self.process_command(command))
            except sr.UnknownValueError:
                logger.warning("Whisper Recognition non ha capito l'audio.")
            except sr.RequestError as e:
                logger.error(f"Errore di richiesta a Whisper Recognition; {e}")

    def run(self):
        """Avvia il Voice Assistant."""
        logger.info("Voice Assistant avviato.")
        while self.listening:
            self.listen_and_process()
        logger.info("Voice Assistant terminato.")

def should_update_profile(command: str) -> bool:
    """Determina se aggiornare il profilo utente basato sul comando."""
    # Esempio: aggiorna il profilo se il comando contiene determinate parole chiave
    keywords = ["preferenze", "interessi", "profilo"]
    return any(keyword in command.lower() for keyword in command.lower())