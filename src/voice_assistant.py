# src/voice_assistant.py

import logging
from src.state.state_manager import StateManager
from src.langgraph_setup import graph, END
from src.audio.audio_handler import AudioHandler
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self):
        self.listening = True
        self.state_manager = StateManager()
        self.audio_handler = AudioHandler()
        self.thread_id = "default-thread"  # Identificativo del thread
        logger.debug("VoiceAssistant inizializzazione completata.")

    def set_thread_id(self, thread_id: str):
        """Imposta un nuovo thread ID per la conversazione."""
        self.thread_id = thread_id
        logger.info(f"Thread ID impostato su: {self.thread_id}")

    def process_command(self, command: str):
        """Elabora il comando trascritto."""
        try:
            # Configura il RunnableConfig con il thread ID
            config = {"configurable": {"thread_id": self.thread_id}}

            # Crea una copia dello stato corrente
            state = self.state_manager.state.copy()
            logger.debug(f"Stato iniziale: {state}")

            # Aggiungi il messaggio dell'utente
            state["user_messages"].append({"content": command, "role": "user"})

            # Invoca il grafo con MemorySaver
            updated_state = graph.invoke(state, config=config)
            logger.debug(f"Stato aggiornato dal grafo: {updated_state}")

            # Aggiorna lo stato interno
            self.state_manager.state = updated_state
            assistant_message = self.state_manager.get_assistant_message()

            # Genera una risposta se non disponibile
            if not assistant_message:
                assistant_message = "Mi dispiace, non sono sicuro di aver capito. Puoi ripetere?"
                self.state_manager.state["agent_messages"].append({"content": assistant_message, "role": "assistant"})

            # Riproduci il messaggio
            self.audio_handler.speak(assistant_message)

            # Termina la conversazione se richiesto
            if self.state_manager.state.get("terminate", False):
                logger.info("Terminazione della conversazione richiesta.")
                self.listening = False

        except Exception as e:
            ErrorHandler.handle_error(e, "Errore durante l'elaborazione del comando")
            self.audio_handler.speak("Si è verificato un errore. Prova di nuovo.")
    

    def listen_and_process(self):
        """Ascolta il comando vocale e lo elabora."""
        import speech_recognition as sr
        import tempfile
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Ascoltando...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio.get_wav_data())
                    temp_file_path = temp_file.name

                logger.debug(f"Audio salvato in {temp_file_path}")
                from src.stt import transcribe_audio
                command = transcribe_audio(temp_file_path)
                logger.debug(f"Comando trascritto: {command}")
                self.process_command(command)
            except Exception as e:
                ErrorHandler.handle_error(e, "Errore durante l'ascolto")

    def run(self):
        """Avvia il Voice Assistant."""
        logger.info("Voice Assistant avviato.")
        while self.listening:
            self.listen_and_process()
        logger.info("Voice Assistant terminato.")
