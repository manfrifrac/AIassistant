# src/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Chiavi API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Aggiungi questa linea

# Parametri Predefiniti
DEFAULT_VOICE = "alloy"
DEFAULT_LANGUAGE = "it"
LOG_FILE = "logs/app.log"
