import logging
import speech_recognition as sr
import tempfile
from src.state.state_manager import StateManager
from src.audio.audio_handler import AudioHandler
from src.utils.error_handler import ErrorHandler
from src.stt import transcribe_audio
from src.langgraph_setup import graph

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self):
        self.listening = True
        self.state_manager = StateManager()
        self.audio_handler = AudioHandler()
        logger.debug("VoiceAssistant inizializzazione completata.")

    def process_command(self, command: str):
        """Elabora il comando trascritto."""
        try:
            state = self.state_manager.state

            # Log iniziale del comando ricevuto
            logger.debug(f"Comando ricevuto: {command}")

            # Aggiungi il messaggio dell'utente
            state["user_messages"].append({"content": command, "role": "user"})
            logger.debug(f"user_messages aggiornati: {state['user_messages']}")

            # Invoca il grafo
            command_response = graph.invoke(state)
            self.state_manager.update_state(command_response.get("update", {}))
            logger.debug(f"Stato aggiornato dopo il grafo: {self.state_manager.state}")

            # Recupera il messaggio dell'assistente
            assistant_message = self.state_manager.get_assistant_message()
            if not assistant_message:
                assistant_message = "Mi dispiace, non sono sicuro di aver capito. Puoi ripetere, per favore?"
                state["agent_messages"].append({"content": assistant_message, "role": "assistant"})

            logger.debug(f"Messaggio dell'assistente: {assistant_message}")
            logger.debug(f"agent_messages aggiornati: {state['agent_messages']}")

            # Riproduci il messaggio
            self.audio_handler.speak(assistant_message)

        except Exception as e:
            ErrorHandler.handle_error(e, "Errore durante l'elaborazione del comando")
            self.audio_handler.speak("Si è verificato un errore. Prova di nuovo.")


    def listen_and_process(self):
        """Ascolta il comando vocale e lo elabora."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Ascoltando...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio.get_wav_data())
                    temp_file_path = temp_file.name

                logger.debug(f"Audio salvato in {temp_file_path}")
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
