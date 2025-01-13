from typing import List, Dict, Any, Union, Optional, Coroutine, Sequence, Awaitable
import logging

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='onnx_mini_lm_l6_v2')
from backend.src.tools.embedding import semantic_search, vectorize_messages
import numpy as np
from numpy.typing import NDArray
from backend.src.models.memory import Memory
from backend.src.database.repositories.memory_repository import MemoryRepository
from datetime import datetime

logger = logging.getLogger(__name__)

async def manage_long_term_memory(existing: Optional[Dict[str, Any]], new_items: Dict[str, Any]) -> Dict[str, Any]:
    """Merge existing and new memory items safely."""
    result = {} if existing is None else existing.copy()
    result.update(new_items)
    return result

class PersistentStore:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = psycopg2.connect(self.connection_string)
        self.create_table()

    def create_table(self):
        """Create table for long-term memory if it doesn't exist."""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    namespace VARCHAR(255),
                    key VARCHAR(255),
                    data JSONB,
                    PRIMARY KEY (namespace, key)
                );
            """)
            self.connection.commit()
            logger.debug("Table 'long_term_memory' ensured in PostgreSQL database.")

    def put(self, namespace: str, key: str, data: dict):
        """Insert or update a record in long-term memory."""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO long_term_memory (namespace, key, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (namespace, key) DO UPDATE
                SET data = EXCLUDED.data;
            """, (namespace, key, json.dumps(data)))
            self.connection.commit()
            logger.debug(f"Saved to long-term memory: {namespace}/{key}")
            # Store data in the long_term_memory table for persistence

    def get(self, namespace: str, key: str) -> dict:
        """Retrieve a record from long-term memory."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT data FROM long_term_memory
                WHERE namespace = %s AND key = %s;
            """, (namespace, key))
            result = cursor.fetchone()
            if result:
                logger.debug(f"Retrieved from long-term memory: {namespace}/{key}")
                return result['data']
            logger.debug(f"No data found in long-term memory for: {namespace}/{key}")
            return {}
            # Fetch data from the long_term_memory table based on namespace and key

    def search(self, namespace: str, query: str) -> list:
        """Perform a simple search in long-term memory."""
        # Implement a basic search or integrate with full-text search as needed
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT key, data FROM long_term_memory
                WHERE namespace = %s AND data::text ILIKE %s;
            """, (namespace, f"%{query}%"))
            results = cursor.fetchall()
            #logger.debug(f"Search results in long-term memory for '{query}': {results}")
            return results
            # Execute a text-based search within the long_term_memory table based on namespace and key

class LongTermStore:
    def __init__(self, store: PersistentStore, index: dict):
        self.store = store
        self.index = index  # {'embed': embed_function, 'dims': dimensions}

    def put(self, namespace: str, key: str, data: dict):
        self.store.put(namespace, key, data)

    def get(self, namespace: str, key: str) -> dict:
        return self.store.get(namespace, key)

    def search(self, namespace: str, query: str) -> list:
        return self.store.search(namespace, query)

class MemoryStore:
    def __init__(self):
        self.repository = MemoryRepository()
        self._model = None
        self.short_term_memory: List[Dict[str, Any]] = []
        
        try:
            # Initialize PersistentStore first
            self.persistent_store = PersistentStore(
                connection_string="postgresql://admin:Federico2024!@localhost:5432/AiAssistant"
            )
            logger.info("Connessione a PostgreSQL stabilita con successo")
            
            # Initialize LongTermStore after model is loaded
            self.long_term_store = LongTermStore(
                store=self.persistent_store,
                index={"embed": self.model.encode, "dims": 384}
            )
            
            # Create threads table
            with self.persistent_store.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS threads (
                        id SERIAL PRIMARY KEY,
                        thread_id VARCHAR(255) UNIQUE NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.persistent_store.connection.commit()
                logger.debug("Tabella 'threads' verificata/creata in PostgreSQL")
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del database: {e}")
            raise

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading del modello SentenceTransformer."""
        if self._model is None:
            logger.info("Caricamento del modello SentenceTransformer...")
            try:
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Modello SentenceTransformer caricato con successo")
            except Exception as e:
                logger.error(f"Errore nel caricamento del modello: {e}")
                raise
        return self._model

    def add_message(self, message: Dict[str, Any]):
        """Aggiungi un messaggio alla memoria a breve termine."""
        self.short_term_memory.append(message)
        logger.debug(f"Aggiunto messaggio alla memoria a breve termine: {message}")
        self.trim_short_term_memory()
        # Append message to short_term_memory and trim if necessary

    def trim_short_term_memory(self, max_length: int = 100):
        """Mantiene solo gli ultimi `max_length` messaggi nella memoria a breve termine."""
        if len(self.short_term_memory) > max_length:
            removed = self.short_term_memory[:-max_length]
            self.short_term_memory = self.short_term_memory[-max_length:]
            logger.debug(f"Memoria a breve termine trimmata. Rimosso: {removed}")

    def get_relevant_messages(self, query: str) -> List[Dict[str, Any]]:
        """Recupera i messaggi rilevanti dalla memoria a breve termine."""
        if not self.short_term_memory:
            logger.debug("Nessun messaggio nella memoria a breve termine.")
            return []
        
        vectors = self.process_embeddings(self.short_term_memory)
        relevant = semantic_search(np.array(vectors), query, self.short_term_memory)
        logger.debug(f"Messaggi rilevanti trovati: {relevant}")
        return relevant
        # Vectorize messages and perform semantic search to find relevant entries

    def save_to_long_term_memory(self, namespace: str, key: str, data: Dict[str, Any]) -> None:
        """Salva i dati nella memoria a lungo termine usando PostgreSQL."""
        try:
            if namespace == "threads":
                self.save_thread(key)  # key è l'id del thread
            else:
                self.persistent_store.put(namespace, key, data)
            logger.debug(f"Dati salvati in {namespace} con ID {key}")
        except Exception as e:
            logger.error(f"Errore nel salvataggio dei dati in memoria: {e}")
            raise
        # Persist data in the long-term memory storage

    def retrieve_from_long_term_memory(self, namespace: str, key: str) -> Dict[str, Any]:
        """Recupera i dati dalla memoria a lungo termine."""
        try:
            # Use persistent_store directly instead of long_term_store
            data = self.persistent_store.get(namespace, key)
            if data is None:
                logger.debug(f"Nessun dato trovato nella memoria a lungo termine per: {namespace}/{key}")
                return {}
            logger.debug(f"Recuperato dalla memoria a lungo termine: {namespace}/{key}")
            return data
        except Exception as e:
            logger.error(f"Errore nel recupero della memoria a lungo termine: {e}")
            return {}
        # Access data from persistent storage based on namespace and key

    def search_long_term_memory(self, namespace: str, query: str) -> List[Dict[str, Any]]:
        """Esegue una ricerca nella memoria a lungo termine."""
        try:
            results = self.long_term_store.search(namespace, query)
            if not results:
                logger.debug(f"Nessun risultato trovato nella memoria a lungo termine per: {query}")
                return []
            logger.debug(f"Risultati della ricerca nella memoria a lungo termine per '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Errore durante la ricerca nella memoria a lungo termine: {e}")
            return []
        # Perform search operation using LongTermStore

    def get_last_thread_id(self) -> int:
        """Recupera l'ultimo thread_id da PostgreSQL."""
        try:
            with self.persistent_store.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT thread_id FROM threads 
                    ORDER BY id DESC 
                    LIMIT 1;
                """)
                result = cursor.fetchone()
                if result:
                    # Estrae il numero dal thread_id (es. "thread-5" -> 5)
                    thread_num = int(result[0].split('-')[1])
                    logger.debug(f"Ultimo thread_id trovato: {thread_num}")
                    return thread_num
                logger.debug("Nessun thread trovato, partendo da 0")
                return 0
        except Exception as e:
            logger.error(f"Errore nel recupero dell'ultimo thread_id: {e}")
            return 0

    def save_thread(self, thread_id: str) -> bool:
        """Salva un nuovo thread_id in PostgreSQL."""
        try:
            with self.persistent_store.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO threads (thread_id) 
                    VALUES (%s) 
                    ON CONFLICT (thread_id) DO NOTHING;
                """, (thread_id,))
                self.persistent_store.connection.commit()
                logger.debug(f"Thread ID {thread_id} salvato con successo")
                return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio del thread_id: {e}")
            return False

    def manage_short_term(self, existing: list, new_items: list) -> list:
        """Manages short-term memory keeping only recent, unique items."""
        if not new_items:
            return existing[-100:] if existing else []  # Keep last 100 items
        return (existing + new_items)[-100:]  # Combine and keep last 100

    async def manage_long_term(self, existing: Optional[Dict[str, Any]], new_items: Dict[str, Any]) -> Dict[str, Any]:
        """Manages long-term memory ensuring proper merging of data."""
        return await manage_long_term_memory(existing, new_items)

    def extract_relevant_info(self, message_data: dict) -> dict:
        """Extracts information worth storing long-term."""
        relevant = {}
        
        # Store messages with specific keywords or patterns
        msg = message_data.get("user_message", "").lower()
        keywords = ["remember", "important", "save", "profile", "preference"]
        if any(key in msg for key in keywords):
            relevant["user_preferences"] = message_data
            
        # Store research results
        if message_data.get("context", {}).get("research_result"):
            relevant["research_history"] = {
                "query": message_data["context"]["query"],
                "result": message_data["context"]["research_result"]
            }
            
        return relevant

    def update_short_term(self, memory: list) -> list:
        """Trim short-term memory to the last 100 messages."""
        return self.manage_short_term(memory, [])

    def update_long_term(self, memory: dict, thread_id: str) -> dict:
        """Salva i dati rilevanti nella memoria a lungo termine."""
        try:
            relevant_data = extract_relevant_data(memory)
            if relevant_data:
                self.save_to_long_term_memory("session_logs", thread_id, relevant_data)
            return relevant_data
        except Exception as e:
            logger.error(f"Error updating long-term memory: {e}")
            return {}

    def process_embeddings(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process embeddings for semantic search"""
        try:
            # Extract messages content for vectorization
            messages = [msg["content"] if isinstance(msg, dict) else str(msg) for msg in data]
            
            # Get vector embeddings using the model and convert to numpy array
            vectors: NDArray = self.model.encode(messages, convert_to_numpy=True)
            
            if len(data) > 0:
                # Get query from last message
                query = data[-1]["content"]
                # Perform semantic search with properly typed vectors
                results = semantic_search(vectors, query, data)
                return results
            return []
            
        except Exception as e:
            logger.error(f"Error processing embeddings: {e}")
            return []

    async def merge_memories(self, existing: Optional[Dict[str, Any]], new_items: Dict[str, Any]) -> Dict[str, Any]:
        """Merge memory items safely handling None case"""
        return await manage_long_term_memory(existing, new_items)

    async def save_memory(self, memory_data: Dict[str, Any]) -> None:
        """Save memory with required fields"""
        memory = Memory(
            content=memory_data.get("content", ""),  # Required
            memory_type=memory_data.get("memory_type", "default"),  # Required
            user_id=memory_data.get("user_id"),
            timestamp=datetime.now()
        )
        await self.repository.create(memory)

    async def update_memory(self) -> Dict[str, Any]:
        """Update memory data and return results"""
        return await self.merge_memories(None, {})

    def dict_to_memory(self, data: Dict[str, Any]) -> Memory:
        """Convert dict to Memory instance with required fields"""
        return Memory(
            content=data.get("content", ""),  # Required
            memory_type=data.get("memory_type", "default"),  # Required
            user_id=data.get("user_id"),
            id=data.get("id"),
            key=data.get("key"),
            value=data.get("value"),
            timestamp=data.get("timestamp"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

def extract_relevant_data(memory: dict) -> dict:
    """Estrae i dati rilevanti dalla memoria."""
    relevant_data = {
        key: value for key, value in memory.items() if some_condition(key, value)
    }
    logger.debug(f"Dati rilevanti estratti: {relevant_data}")
    return relevant_data

def some_condition(key: str, value: Any) -> bool:
    """Definisce la condizione per filtrare i dati rilevanti nella memoria."""
    # Esempio: Filtra solo le query non vuote e i messaggi importanti
    if "query" in key:
        return bool(value.get("query"))
    if "important_message" in key:
        return bool(value.get("content"))
    return False