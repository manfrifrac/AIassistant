# src/audio/audio_handler.py

import simpleaudio as sa
from backend.src.audio.audio_cache import AudioCache
from backend.src.tts import generate_speech
import logging
import os
import speech_recognition as sr
import io

logger = logging.getLogger("AudioHandler")

class AudioHandler:
    def __init__(self):
        self.cache = AudioCache()
        self.recognizer = sr.Recognizer()

    def speak(self, text: str):
        """Riproduce l'audio del messaggio fornito."""
        try:
            wav_file = generate_speech(text)
            if wav_file:
                wave_obj = sa.WaveObject.from_wave_file(wav_file)
                play_obj = wave_obj.play()
                play_obj.wait_done()
                os.remove(wav_file)
        except Exception as e:
            logger.error(f"Errore nella riproduzione dell'audio: {e}")

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text using Whisper"""
        if not audio_bytes:
            raise ValueError("Empty audio data")
            
        try:
            with io.BytesIO(audio_bytes) as audio_file:
                # Validate audio file
                try:
                    with sr.AudioFile(audio_file) as source:
                        audio = self.recognizer.record(source)
                except Exception as e:
                    raise ValueError(f"Invalid audio format: {e}")

                # Transcribe using Whisper
                text = self.recognizer.recognize_whisper(
                    audio, 
                    language="italian", 
                    model="base"
                )
                
                if not text:
                    raise ValueError("No speech detected in audio")
                    
                return text
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
