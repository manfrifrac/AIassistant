# src/tools/llm_tools.py
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger("LLMTools")

llm = ChatOpenAI(model="gpt-3.5-turbo")
model = SentenceTransformer('all-MiniLM-L6-v2')

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

def generate_response(conversation_text: str, last_user_message: str, modified_response: str) -> str:
    try:
        logger.debug(f"Generando risposta basata sulle informazioni raccolte: {conversation_text}")
        # Utilizza il metodo 'invoke' con 'input=messages'
        response = llm.invoke(
            input=[
                {"role": "system", "content": f"Rispondi al seguente messaggio: {last_user_message}. Utilizza le seguenti informazioni rilevanti: {conversation_text}. Risposta modificata: {modified_response}"}
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

def vectorize_messages(messages: List[Dict[str, Any]]) -> np.ndarray:
    """Vettorializza i messaggi."""
    texts = [msg['content'] for msg in messages]
    embeddings = model.encode(texts)
    logger.debug(f"Embeddings generati: {embeddings}")
    return embeddings

def semantic_search(vectors: np.ndarray, query: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Esegue una ricerca semantica per trovare i messaggi rilevanti."""
    try:
        query_vector = model.encode([query])
        num_samples = len(messages)
        if num_samples == 0:
            logger.debug("Nessun messaggio da cercare")
            return []
        
        # Usa al massimo 3 vicini e comunque non più del numero di messaggi disponibili
        n_neighbors = min(3, num_samples)
        logger.debug(f"Cerco {n_neighbors} messaggi rilevanti tra {num_samples} messaggi disponibili")
        
        nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm='ball_tree').fit(vectors)
        distances, indices = nbrs.kneighbors(query_vector)
        
        # Filtra i messaggi per similarità
        relevant_messages = []
        for i, distance in zip(indices[0], distances[0]):
            if distance < 0.8:  # Solo messaggi abbastanza simili
                relevant_messages.append(messages[i])
                
        logger.debug(f"Trovati {len(relevant_messages)} messaggi rilevanti")
        return relevant_messages
    except Exception as e:
        logger.error(f"Errore durante la ricerca semantica: {e}")
        return []

def modify_response(research_result: str) -> str:
    """Modifica la risposta utilizzando un prompt e un LLM."""
    try:
        prompt = (
            "Hai raccolto le seguenti informazioni: "
            f"{research_result}. "
            "Estrapola le informazioni più importanti e fornisci una risposta concisa e chiara."
        )
        response = llm.invoke(input=[{"role": "system", "content": prompt}])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Errore durante la modifica della risposta: {e}")
        return research_result  # Fallback alla risposta originale
