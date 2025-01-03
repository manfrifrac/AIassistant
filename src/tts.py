import requests
import os
from dotenv import load_dotenv

# Carica chiavi API
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

def generate_speech(text, voice="alloy", speed=1.0, output_file="output.mp3"):
    """
    Genera audio dal testo usando le API OpenAI.
    Args:
        text (str): Testo da convertire in audio.
        voice (str): Voce da utilizzare (es. "alloy").
        speed (float): Velocità dell'audio (default 1.0).
        output_file (str): Nome del file di output.
    Returns:
        str: Percorso del file audio generato.
    """
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "speed": speed
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(response.content)
    return output_file
