import speech_recognition as sr
import logging
from src.stt import transcribe_audio
from src.tts import generate_speech
from src.langgraph_setup import graph
import tempfile
from langgraph.types import Command
import pygame

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self):
        self.listening = True
        pygame.mixer.init()  # Inizializza il mixer di pygame
        logger.debug("VoiceAssistant inizializzazione completata.")

        self.state = {
            "messages": [
                {"type": "system", "content": "Avvio del Voice Assistant"}
            ],
            "should_research": False,
            "terminate": False,
            "collected_info": "",
            "current_node": "supervisor"
        }

    def speak(self, text: str):
        """
        Converte il testo in parlato e lo riproduce direttamente con pygame.
        """
        try:
            tts_file = generate_speech(text)
            if tts_file:
                logger.debug(f"Riproduzione audio: {tts_file}")
                pygame.mixer.music.load(tts_file)
                pygame.mixer.music.play()

                # Aspetta che l'audio finisca
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            else:
                logger.error("Errore durante la generazione o riproduzione dell'audio.")
        except Exception as e:
            logger.error(f"Errore nella funzione speak: {e}")

    def process_command(self, command: str):
        """
        Elabora il comando ricevuto.
        """
        logger.debug(f"Comando ricevuto: {command}")
        try:
            # Aggiungi il messaggio dell'utente allo stato
            self.state["messages"].append({"type": "user", "content": command, "name": "user"})
            logger.debug(f"Stato prima dell'invocazione: {self.state}")

            # Invoca il grafo con lo stato attuale
            command_response = graph.invoke(self.state)
            logger.debug(f"Risposta ricevuta dal grafo: {command_response}")

            # Converti il risultato in un oggetto Command se necessario
            if not isinstance(command_response, Command):
                logger.warning("Risultato non è un'istanza di Command, interpretato come dizionario.")
                command_response = Command(
                    goto=command_response.get("current_node", "__end__"),
                    update=command_response
                )

            # Applica gli aggiornamenti di stato
            updates = command_response.update
            logger.debug(f"Aggiornamenti applicati: {updates}")
            for key, value in updates.items():
                if key == "messages":
                    self.state["messages"].extend(value)
                else:
                    self.state[key] = value

            # Riproduci i messaggi generati dall'assistente
            for msg in self.state.get("messages", []):
                if msg.get("type") == "assistant" and msg.get("content"):
                    self.speak(msg["content"])

            # Gestisci il comando di terminazione
            goto = command_response.goto
            logger.debug(f"Comando di goto: {goto}")
            if goto in ["__end__", "END", "FINISH"]:
                logger.info("Ricevuto comando di terminazione. Chiusura Voice Assistant.")
                self.listening = False
            else:
                self.state["current_node"] = goto
                logger.debug(f"Nodo corrente aggiornato a: {self.state['current_node']}")
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione del comando: {e}")

    def listen_and_process(self):
        """
        Ascolta il comando vocale, lo trascrive e lo elabora.
        """
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
        """
        Avvia il Voice Assistant.
        """
        logger.info("Voice Assistant avviato.")
        while self.listening:
            self.listen_and_process()
        logger.info("Voice Assistant terminato.")
