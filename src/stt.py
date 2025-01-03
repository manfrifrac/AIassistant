import requests
import os
from dotenv import load_dotenv

# Carica chiavi API
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

def transcribe_audio(file_path, language="it"):
    """
    Trascrive l'audio in testo usando le API OpenAI.
    Args:
        file_path (str): Percorso del file audio.
        language (str): Lingua dell'audio (ISO-639-1, es. "it").
    Returns:
        str: Testo trascritto.
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb")),
        "model": (None, "whisper-1"),
        "language": (None, language)
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    return response.json().get("text", "")
