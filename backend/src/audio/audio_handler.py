# src/audio/audio_handler.py

import simpleaudio as sa
from backend.src.audio.audio_cache import AudioCache
from backend.src.tts import generate_speech
import logging
import os

logger = logging.getLogger("AudioHandler")

class AudioHandler:
    def __init__(self):
        self.cache = AudioCache()

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
