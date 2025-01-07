# src/voice_assistant.py

import speech_recognition as sr
import pygame
import logging
from src.stt import transcribe_audio
from src.tts import generate_speech
from src.langgraph_setup import graph
import os
from pydub import AudioSegment
import tempfile

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self):
        self.listening = True
        pygame.mixer.init()
        logger.debug("VoiceAssistant inizializzazione completata.")
        
        # Inizializza lo stato come dizionario conforme a StateSchema
        self.state = {
            "messages": [
                {"type": "system", "content": "Avvio del Voice Assistant"}
            ],
            # Inizialmente, nessuna ricerca o terminazione
            "should_research": False,
            "terminate": False,
            "collected_info": "",
            "current_node": "supervisor"  # Imposta il nodo corrente iniziale
        }

    def play_audio(self, file: str):
        try:
            logger.debug(f"Tentativo di riproduzione file audio: {file}")

            if not os.path.exists(file):
                logger.error(f"Il file audio {file} non esiste.")
                return

            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            logger.debug("Riproduzione audio completata con pygame.")
        except Exception as e:
            logger.error(f"Errore durante la riproduzione dell'audio: {e}")

    def speak(self, message: str):
        try:
            logger.debug(f"Generazione audio per il messaggio: {message}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
                temp_mp3_path = temp_mp3.name

            temp_wav_path = temp_mp3_path.replace(".mp3", ".wav")

            generate_speech(message, output_file=temp_mp3_path)
            sound = AudioSegment.from_mp3(temp_mp3_path)
            sound.export(temp_wav_path, format="wav")

            logger.info(f"File audio generato: {temp_mp3_path}, {temp_wav_path}")
            self.play_audio(temp_wav_path)
        except Exception as e:
            logger.error(f"Errore durante la generazione o riproduzione dell'audio: {e}")
        finally:
            for temp_file in [temp_mp3_path, temp_wav_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def process_command(self, command: str):
        logger.debug(f"Comando ricevuto: {command}")
        try:
            # Aggiungi il messaggio dell'utente allo stato persistente
            self.state["messages"].append({"type": "user", "content": command, "name": "user"})
            logger.debug(f"Stato prima dell'invocazione: {self.state}")

            # Invoca il grafo degli agenti con lo stato persistente
            command_response = graph.invoke(self.state)
            logger.debug(f"Received Command: {command_response}")

            if isinstance(command_response, dict):
                # Applica gli aggiornamenti dallo stato del Command
                updates = command_response.get("update", {})
                logger.debug(f"Applying updates: {updates}")
                for key, value in updates.items():
                    if key == "messages":
                        self.state["messages"].extend(value)
                    else:
                        self.state[key] = value
                
                # Gestisci il comando 'goto'
                goto = command_response.get("goto")
                logger.debug(f"Comando di goto: {goto}")
                if goto in ["__end__", "END"]:
                    logger.info("Ricevuto comando di terminazione. Chiusura Voice Assistant.")
                    self.listening = False

                # Aggiorna il nodo corrente
                self.state["current_node"] = goto

                # Controlla se ci sono nuovi messaggi da AI
                if "messages" in updates:
                    for msg in updates["messages"]:
                        if msg.get("type") == "assistant" and msg.get("content"):
                            logger.info(f"Risposta AI: {msg['content']}")
                            self.speak(msg["content"])
            else:
                logger.error("Expected a dict object from graph.invoke.")
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione del comando: {e}")

    def listen_and_process(self):
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
                logger.error(f"Errore durante l'ascolto: {e}")

    def run(self):
        logger.info("Voice Assistant avviato.")
        max_iterations = 100  # Limite per evitare loop infiniti
        iteration = 0
        while self.listening and iteration < max_iterations:
            self.listen_and_process()
            iteration += 1
        if iteration >= max_iterations:
            logger.warning("Raggiunto il numero massimo di iterazioni. Chiusura Voice Assistant.")
        logger.info("Voice Assistant terminato.")
