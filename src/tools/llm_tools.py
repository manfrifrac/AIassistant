# src/tools/llm_tools.py
from langchain_openai import ChatOpenAI

import logging

logger = logging.getLogger("LLMTools")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def perform_research(query: str) -> str:
    try:
        logger.debug(f"Eseguendo ricerca per la query: {query}")
        response = llm.invoke(
            input=[
                {"role": "system", "content": f"Esegui una ricerca approfondita sulla seguente query: {query}. Fornisci i risultati in modo chiaro e conciso."}
            ],
            temperature=0.7
        )
        research_result = response.content.strip()
        logger.debug(f"Risultati della ricerca: {research_result}")
        return research_result
    except Exception as e:
        logger.error(f"Errore durante la ricerca: {e}")
        return "Errore durante la ricerca. Riprovare."



def generate_response(collected_info: str) -> str:
    try:
        logger.debug(f"Generando risposta basata sulle informazioni raccolte: {collected_info}")
        # Utilizza il metodo 'invoke' con 'input=messages'
        response = llm.invoke(
            input=[
                {"role": "system", "content": f"Hai raccolto le seguenti informazioni: {collected_info}. Formuli una risposta naturale e cordiale all'utente utilizzando queste informazioni."}
            ],
            temperature=0.7
        )
        # Estrai solo il contenuto della risposta
        generated_response = response.content.strip()
        logger.debug(f"Risposta generata: {generated_response}")
        return generated_response
    except Exception as e:
        logger.error(f"Errore durante la generazione della risposta: {e}")
        return "Mi dispiace, non sono riuscito a generare una risposta."
