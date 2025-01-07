import speech_recognition as sr
import pygame
import uuid
import logging
from src.stt import transcribe_audio
from src.tts import generate_speech
from src.langgraph_setup import app
import os
from playsound import playsound
from pydub import AudioSegment
from langchain_core.messages import HumanMessage, AIMessage
import tempfile
from pydub import AudioSegment
import os

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self):
        self.listening = True
        pygame.mixer.init()
        logger.debug("VoiceAssistant inizializzazione completata.")

    def play_audio(self, file: str):
        try:
            logger.debug(f"Tentativo di riproduzione file audio: {file}")

            # Verifica che il file esista
            if not os.path.exists(file):
                logger.error(f"Il file audio {file} non esiste.")
                return

            # Prova a riprodurre con pygame
            try:
                pygame.mixer.music.load(file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                logger.debug("Riproduzione audio completata con pygame.")
            except Exception as e:
                logger.warning(f"Errore con pygame: {e}. Uso playsound come fallback.")
                playsound(file)
        except Exception as e:
            logger.error(f"Errore durante la riproduzione dell'audio: {e}")

    def speak(self, message: str):
        try:
            logger.debug(f"Generazione audio per il messaggio: {message}")

            # Usa file temporanei per evitare problemi di permessi
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
                temp_mp3_path = temp_mp3.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                temp_wav_path = temp_wav.name

            # Genera l'audio in formato MP3
            generate_speech(message, output_file=temp_mp3_path)

            # Converti MP3 in WAV
            sound = AudioSegment.from_mp3(temp_mp3_path)
            sound.export(temp_wav_path, format="wav")

            logger.info(f"File audio generato: {temp_mp3_path}, {temp_wav_path}")

            # Prova a riprodurre il file WAV
            self.play_audio(temp_wav_path)

        except Exception as e:
            logger.error(f"Errore durante la generazione o riproduzione dell'audio: {e}")

        finally:
            # Rimuovi i file temporanei
            if os.path.exists(temp_mp3_path):
                os.remove(temp_mp3_path)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)


    def process_command(self, command: str):
        if not self.listening:
            logger.debug("Ascolto disabilitato durante l'elaborazione.")
            return

        try:
            logger.debug(f"Comando ricevuto: {command}")
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}

            # Invoca il grafo
            final_state = app.invoke(
                {"messages": [{"type": "human", "content": command}]},
                config=config
            )

            logger.debug(f"Stato finale ricevuto: {final_state}")

            if "messages" in final_state:
                for msg in final_state["messages"]:
                    logger.debug(f"Tipo di messaggio: {type(msg)}, Contenuto: {msg}")

                    # Gestione di HumanMessage
                    if isinstance(msg, HumanMessage):
                        logger.debug(f"Messaggio umano ricevuto: {msg.content}")

                    # Gestione di AIMessage
                    elif isinstance(msg, AIMessage):
                        content = msg.content
                        if content:
                            logger.info(f"Risposta AI: {content}")
                            self.speak(content)
                        else:
                            logger.warning("Risposta AI vuota.")

                    # Messaggio sconosciuto
                    else:
                        logger.warning(f"Formato del messaggio non riconosciuto: {msg}")
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione del comando: {e}")





    def listen_and_process(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Ascoltando...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

                # Salva l'audio temporaneo
                temp_file = "temp_audio.wav"
                with open(temp_file, "wb") as f:
                    f.write(audio.get_wav_data())
                logger.debug(f"Audio salvato in {temp_file}")

                # Trascrivi il comando
                command = transcribe_audio(temp_file)
                logger.debug(f"Comando trascritto: {command}")
                self.process_command(command)
            except Exception as e:
                logger.error(f"Errore durante l'ascolto: {e}")

    def run(self):
        logger.info("Voice Assistant avviato.")
        while True:
            self.listen_and_process()
