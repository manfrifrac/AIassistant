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
        logger.debug("VoiceAssistant inizializzazione completata.")

    def process_command(self, command: str):
        """Elabora il comando trascritto."""
        try:
            # Crea una copia dello stato attuale
            state = self.state_manager.state.copy()
            logger.debug(f"Stato iniziale: {state}")

            # Aggiungi il messaggio dell'utente
            state["user_messages"].append({"content": command, "role": "user"})
            logger.debug(f"user_messages aggiornati: {state['user_messages']}")

            # Invoca il grafo e ottieni lo stato aggiornato
            updated_state = graph.invoke(state)
            logger.debug(f"Stato aggiornato dal grafo: {updated_state}")

            # Aggiorna lo stato interno con lo stato aggiornato
            self.state_manager.state = updated_state
            logger.debug(f"Stato dopo l'aggiornamento: {self.state_manager.state}")

            # Recupera il messaggio dell'assistente
            assistant_message = self.state_manager.get_assistant_message()
            logger.debug(f"Messaggio dell'assistente recuperato: {assistant_message}")

            if not assistant_message:
                # Se non c'è risposta, usa una risposta predefinita
                assistant_message = "Mi dispiace, non sono sicuro di aver capito. Puoi ripetere, per favore?"
                self.state_manager.state["agent_messages"].append({"content": assistant_message, "role": "assistant"})
                logger.debug(f"Messaggio predefinito aggiunto: {assistant_message}")
            else:
                # Aggiungi la risposta generata a `agent_messages`
                self.state_manager.state["agent_messages"].append({"content": assistant_message, "role": "assistant"})
                logger.debug(f"Messaggio dell'assistente aggiunto a agent_messages: {assistant_message}")

            logger.debug(f"Messaggio dell'assistente: {assistant_message}")
            logger.debug(f"agent_messages aggiornati: {self.state_manager.state['agent_messages']}")

            # Riproduci il messaggio
            self.audio_handler.speak(assistant_message)

            # Controlla se la conversazione deve terminare
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
