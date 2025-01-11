from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List, Dict, Any
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger("EmbeddingTools")

# Inizializza il modello di embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.debug("Modello SentenceTransformer inizializzato.")

def vectorize_messages(messages: List[Dict[str, Any]]) -> np.ndarray:
    """Vettorializza i contenuti dei messaggi."""
    try:
        texts = [msg['content'] for msg in messages]
        embeddings = model.encode(texts)
        logger.debug(f"Embeddings generati: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Errore nella vettorializzazione dei messaggi: {e}")
        return np.array([])

def semantic_search(vectors: np.ndarray, query: str, messages: List[Dict[str, Any]], top_k: int = 3, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Esegue una ricerca semantica per trovare i messaggi rilevanti."""
    try:
        if vectors.size == 0:
            logger.debug("Vettori vuoti forniti per la ricerca semantica.")
            return []
        
        query_vector = model.encode([query])
        nbrs = NearestNeighbors(n_neighbors=min(top_k, len(messages)), algorithm='ball_tree').fit(vectors)
        distances, indices = nbrs.kneighbors(query_vector)
        
        relevant_messages = []
        for idx, distance in zip(indices[0], distances[0]):
            if distance < similarity_threshold:
                relevant_messages.append(messages[idx])
        
        logger.debug(f"{len(relevant_messages)} messaggi rilevanti trovati con una soglia di similarità di {similarity_threshold}.")
        return relevant_messages
    except Exception as e:
        logger.error(f"Errore durante la ricerca semantica: {e}")
        return []