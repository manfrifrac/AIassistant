import hashlib
import os

class AudioCache:
    def __init__(self):
        self.cache = {}

    def get_audio(self, text):
        """Recupera l'audio dalla cache se esiste."""
        key = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(key)

    def save_audio(self, text, path):
        """Salva l'audio nella cache."""
        key = hashlib.md5(text.encode()).hexdigest()
        self.cache[key] = path
