import speech_recognition as sr
import pygame
import os
import uuid

from langchain_core.messages import HumanMessage
from src.stt import transcribe_audio
from src.tts import generate_speech
# Importa l'agente app da langgraph_setup
from src.langgraph_setup import app

def play_audio(file):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        print("Riproduzione audio in corso...")
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except pygame.error as e:
        print(f"Errore durante la riproduzione dell'audio: {e}")
    finally:
        pygame.mixer.quit()

def listen_and_process():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Parla ora. Sto ascoltando...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Audio catturato. Sto trascrivendo...")

            temp_audio = f"temp_audio_{uuid.uuid4()}.wav"
            with open(temp_audio, "wb") as f:
                f.write(audio.get_wav_data())

            # Trascrizione STT
            command = transcribe_audio(temp_audio)
            print(f"Comando trascritto: {command}")

            if not command.strip():
                print("Nessun comando rilevato.")
                return

            # Invocazione dell'agente
            thread_id = uuid.uuid4()
            config = {"configurable": {"thread_id": str(thread_id)}}
            final_state = app.invoke({"messages": [HumanMessage(content=command)]}, config=config)

            # Risposta generata
            messages = final_state["messages"]
            agent_response = messages[-1].content
            print("Risposta agente:", agent_response)

            # Converto in audio e riproduco
            output_file = f"response_{uuid.uuid4()}.mp3"
            generate_speech(agent_response, output_file=output_file)
            play_audio(output_file)

            # Pulisce file temporanei
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(temp_audio):
                os.remove(temp_audio)

        except sr.UnknownValueError:
            print("Non ho capito il comando. Riprova.")
        except sr.RequestError as e:
            print(f"Errore nel riconoscimento vocale: {e}")
        except Exception as e:
            print(f"Errore generico: {e}")

if __name__ == "__main__":
    print("Assistente vocale con ToolNode e Spotify. Premi Ctrl+C per uscire.")
    try:
        while True:
            listen_and_process()
    except KeyboardInterrupt:
        print("Assistente vocale terminato.")
