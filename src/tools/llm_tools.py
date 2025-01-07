# src/tools/llm_tools.py

import logging
from src.config import OPENAI_API_KEY
import openai

logger = logging.getLogger("LLMTools")

# Imposta la chiave API
openai.api_key = OPENAI_API_KEY

def analyze_intent(message: str) -> str:
    valid_intents = ["spotify_agent", "time_agent", "greeting_agent", "coder", "finish"]
    try:
        messages = [
            {"role": "system", "content": (
                "Sei un assistente per l'analisi dell'intento. Rispondi con uno dei seguenti intenti validi: "
                "spotify_agent, time_agent, greeting_agent, coder, finish."
            )},
            {"role": "user", "content": message}
        ]

        logger.debug(f"Invio messaggi a OpenAI: {messages}")

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=10,
            temperature=0
        )

        intent = response.choices[0].message.content.strip().lower()
        logger.debug(f"Intento analizzato: {intent}")

        if intent not in valid_intents:
            logger.warning(f"Intento non valido ricevuto: {intent}. Defaulting to 'finish'.")
            return "finish"

        return intent
    except Exception as e:
        logger.error(f"Errore durante l'analisi dell'intento: {e}")
        return "finish"

from openai import chat

def generate_response(user_message: str, agent_feedback: str) -> str:
    """
    Genera una risposta naturale basata sul messaggio dell'utente e il feedback degli agenti.
    """
    prompt = (
        f"L'utente ha detto: '{user_message}'.\n"
        f"Risultato degli agenti: '{agent_feedback}'.\n"
        f"Rispondi in modo naturale e cortese."
    )
    try:
        response = chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Errore durante la generazione della risposta: {e}")
        return "Mi dispiace, non sono riuscito a generare una risposta completa."
