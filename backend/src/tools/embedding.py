from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List, Dict, Any, Union
from numpy.typing import NDArray
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger("EmbeddingTools")

# Inizializza il modello di embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.debug("Modello SentenceTransformer inizializzato.")

def vectorize_messages(messages: List[str]) -> NDArray:
    """Convert messages to vector embeddings"""
    if not messages:
        return np.array([])
    vectors = model.encode(messages)
    return np.array(vectors)

def semantic_search(
    vectors: NDArray,
    query: str,
    messages: List[Dict[str, Any]],
    k: int = 5
) -> List[Dict[str, Any]]:
    """Perform semantic search using vector embeddings"""
    if len(vectors) == 0:
        return []
        
    # Get query embedding
    query_vector = model.encode([query])[0]
    
    # Calculate cosine similarities
    similarities = np.dot(vectors, query_vector) / (
        np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector)
    )
    
    # Get top k similar messages
    top_k_indices = np.argsort(similarities)[-k:][::-1]
    
    return [messages[i] for i in top_k_indices if similarities[i] > 0.5]

def embedding_function(data):
    from backend.src.memory_store import MemoryStore  # Moved import inside the function
    memory_store = MemoryStore()
    # ...use memory_store...
    # ...existing code...