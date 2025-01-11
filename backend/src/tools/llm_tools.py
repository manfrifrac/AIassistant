# src/tools/llm_tools.py

from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from src.tools.embedding import model  # Import llm and model from embedding.py
from src.memory_store import MemoryStore  # Updated import

logger = logging.getLogger("LLMTools")

llm = ChatOpenAI(model="gpt-3.5-turbo")

memory_store = MemoryStore()

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
        logger.error(f"Errore nella generazione della risposta: {e}")
        return "Errore nella generazione della risposta. Riprovare."

def vectorize_messages(messages: List[Dict[str, Any]]) -> np.ndarray:
    """Vettorializza i messaggi."""
    try:
        texts = [msg['content'] for msg in messages]
        embeddings = model.encode(texts)
        logger.debug(f"Embeddings generati: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Errore nella vettorializzazione dei messaggi: {e}")
        return np.array([])

def semantic_search(vectors: np.ndarray, query: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Esegue una ricerca semantica per trovare i messaggi rilevanti."""
    try:
        query_vector = model.encode([query])
        num_samples = len(messages)
        if num_samples == 0:
            logger.debug("Nessun messaggio disponibile per la ricerca semantica.")
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
        logger.debug(f"Modificando la risposta con il risultato della ricerca: {research_result}")
        # Implementa la logica di modifica della risposta
        modified = f"Modificata: {research_result}"
        logger.debug(f"Risposta modificata: {modified}")
        return modified
    except Exception as e:
        logger.error(f"Errore nella modifica della risposta: {e}")
        return "Errore nella modifica della risposta."

def save_to_long_term_memory(namespace: str, key: str, data: Dict[str, Any]) -> None:
    """Salva i dati nella memoria a lungo termine."""
    try:
        memory_store.save_to_long_term_memory(namespace, key, data)
        logger.debug(f"Salvato nella memoria a lungo termine: {namespace}/{key}")
    except Exception as e:
        logger.error(f"Errore nel salvataggio della memoria a lungo termine: {e}")

def retrieve_from_long_term_memory(namespace: str, key: str) -> Dict[str, Any]:
    """Recupera i dati dalla memoria a lungo termine."""
    try:
        item = memory_store.retrieve_from_long_term_memory(namespace, key)
        logger.debug(f"Recuperato dalla memoria a lungo termine: {namespace}/{key}")
        return item
    except Exception as e:
        logger.error(f"Errore nel recupero della memoria a lungo termine: {e}")
        return {}

def search_long_term_memory(namespace: str, query: str) -> List[Dict[str, Any]]:
    """Esegue una ricerca nella memoria a lungo termine."""
    try:
        results = memory_store.search_long_term_memory(namespace, query)
        if not results:
            logger.debug(f"Nessun risultato trovato nella memoria a lungo termine per: {query}")
            return []
        logger.debug(f"Risultati della ricerca nella memoria a lungo termine per '{query}': {results}")
        return results
    except Exception as e:
        logger.error(f"Errore durante la ricerca nella memoria a lungo termine: {e}")
        return []

def some_condition(key: str, value: Any) -> bool:
    """Definisce la condizione per filtrare i dati rilevanti nella memoria."""
    # Esempio: Filtra solo le query non vuote
    return bool(value.get("query")) if "query" in key else False

def extract_relevant_data(memory: dict) -> dict:
    """Estrae i dati rilevanti dalla memoria."""
    relevant_data = {
        key: value for key, value in memory.items() if some_condition(key, value)
    }
    logger.debug(f"Dati rilevanti estratti: {relevant_data}")
    return relevant_data

def should_update_profile(command: str) -> bool:
    """Determina se aggiornare il profilo utente basato sul comando."""
    # Esempio: aggiorna il profilo se il comando contiene determinate parole chiave
    keywords = ["preferenze", "interessi", "profilo"]
    return any(keyword in command.lower() for keyword in keywords)

def extract_important_info(message: str) -> Optional[str]:
    """Estrai informazioni importanti dal messaggio."""
    keywords = ["preferenza", "importante", "informazione"]
    if any(keyword in message.lower() for keyword in keywords):
        return message
    return None
