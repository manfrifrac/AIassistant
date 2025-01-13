# src/voice_assistant.py

import logging
import speech_recognition as sr
from backend.src.state.state_manager import StateManager
from backend.src.langgraph_setup import get_graph, END, execute_graph, initialize_graph
from backend.src.audio.audio_handler import AudioHandler
from backend.src.utils.error_handler import ErrorHandler
from typing import Optional, Dict, Any, List, cast, Protocol, Coroutine
from backend.src.tools.llm_tools import retrieve_from_long_term_memory, save_to_long_term_memory, should_update_profile
import asyncio
from langchain.schema.runnable import RunnableConfig
from backend.src.langgraph_setup import CompiledStateGraph as LangGraphCompiledStateGraph  # Import the Protocol

# Define local Protocol for CompiledStateGraph
class CompiledStateGraph(LangGraphCompiledStateGraph):
    """Local type alias for CompiledStateGraph"""
    pass

logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self, state_manager: StateManager):
        self.listening = True
        self.state_manager = state_manager
        self.audio_handler = AudioHandler()
        self.thread_id = self.generate_thread_id()
        self.is_web_mode = False
        self.graph = cast(CompiledStateGraph, initialize_graph(state_manager.memory_store))
        self._initialize_graph()
        logger.debug("VoiceAssistant initialization completed.")

    def _initialize_graph(self) -> None:
        """Initialize the graph with proper error handling"""
        try:
            # Pass memory_store from state_manager
            self.graph = initialize_graph(memory_store=self.state_manager.memory_store)
            if not self.graph:
                raise ValueError("Graph initialization returned None")
            logger.info("Graph initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize graph: {e}")
            raise RuntimeError(f"Graph initialization failed: {e}")

    def generate_thread_id(self) -> str:
        """Genera un thread_id sequenziale basato sui thread esistenti."""
        try:
            last_id = self.state_manager.memory_store.get_last_thread_id()  # Updated
            new_id = last_id + 1
            thread_id = f"thread-{new_id}"
            logger.info(f"Generato nuovo thread_id: {thread_id}")
            
            # Salva il nuovo thread
            if self.state_manager.memory_store.save_thread(thread_id):  
                logger.debug(f"Thread ID {thread_id} salvato con successo")
            else:
                logger.error(f"Fallito nel salvare il thread ID {thread_id}")
            
            return thread_id
        except Exception as e:
            logger.error(f"Errore nella generazione del thread_id: {e}")
            fallback_id = "thread-1"
            logger.info(f"Usando thread_id di fallback: {fallback_id}")
            return fallback_id

    async def process_command(self, command: str) -> Dict[str, Any]:
        """Elabora il comando trascritto."""
        try:
            if not self.graph:
                logger.error("Graph not initialized")
                self._initialize_graph()
                if not self.graph:
                    raise RuntimeError("Failed to initialize graph")

            logger.debug(f"Processing command: {command}")
            current_state = self.state_manager.get_state()
            state = dict(current_state)
            
            # Ensure required state fields exist
            if "user_messages" not in state:
                state["user_messages"] = []
            if "agent_messages" not in state:
                state["agent_messages"] = []
            if "processed_messages" not in state:
                state["processed_messages"] = []
                
            # Add new message and update last_user_message
            state["user_messages"].append({"role": "user", "content": command})
            state["last_user_message"] = command  # Add this line
            
            # Configure and execute graph
            config = RunnableConfig(configurable={
                "thread_id": self.thread_id,
                "debug": True
            })
            
            try:
                logger.debug("Executing graph...")
                if hasattr(self.graph, 'ainvoke'):
                    result = await self.graph.ainvoke(state, config=config)
                else:
                    result = self.graph.invoke(state, config=config)
                
                if not isinstance(result, dict):
                    raise TypeError(f"Graph returned invalid type: {type(result)}")
                
                logger.debug(f"Graph execution successful. Updating state with result")
                await self.state_manager.update_state(result)
                await self.save_conversation_state(result)
                await self.handle_assistant_message(result)
                
            except Exception as e:
                logger.error(f"Graph execution failed: {e}", exc_info=True)
                raise RuntimeError(f"Graph execution failed: {e}")
                
        except Exception as e:
            logger.error(f"Command processing failed: {e}", exc_info=True)
            raise

    async def save_conversation_state(self, result: Dict[str, Any]) -> None:
        """Save conversation state to memory"""
        try:
            self.state_manager.memory_store.save_to_long_term_memory(
                "session_logs", 
                self.thread_id, 
                self.state_manager.to_dict()
            )
        except Exception as e:
            logger.error(f"Error saving conversation state: {e}")

    async def handle_assistant_message(self, result: Dict[str, Any]) -> None:
        """Handle assistant message output"""
        try:
            assistant_message = self.state_manager.get_assistant_message()
            if assistant_message and not self.is_web_mode:
                self.audio_handler.speak(assistant_message)
        except Exception as e:
            logger.error(f"Error handling assistant message: {e}")

    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process a user message and return the response"""
        try:
            logger.debug(f"Stato iniziale: {self.state_manager.get_state()}")
            logger.debug(f"Aggiunto messaggio utente: {user_message}")
            
            # Update state with user message
            self.state_manager.add_user_message({"role": "user", "content": user_message})
            
            # Execute graph with current state using the execute_graph function
            if self.graph:
                # Await the graph result
                graph_result = await execute_graph(self.graph, self.state_manager.get_state())
                logger.debug(f"Risultato dell'esecuzione del grafo: {graph_result}")
                
                if not graph_result:
                    logger.error("Graph execution returned no result")
                    return {}
                    
                # Ensure we have a dict before updating state
                if isinstance(graph_result, dict):
                    await self.state_manager.update_state(graph_result)  # Added await here
                else:
                    logger.error(f"Invalid graph result type: {type(graph_result)}")
                    return {}
            
            # Get agent response
            agent_message = self.get_last_agent_message()
            if agent_message:
                logger.debug(f"Messaggio dell'assistente: {agent_message}")
                
            # Save conversation to long-term memory
            self.save_conversation()
            
            return self.state_manager.get_state() or {}  # Ensure we always return a dict
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e)}  # Return error dict instead of None

    def get_last_agent_message(self) -> Optional[str]:
        """Get the last agent message from state"""
        try:
            agent_messages = self.state_manager.get_state().get("agent_messages", [])
            if (agent_messages):
                return agent_messages[-1].get("content")
            return None
        except Exception as e:
            logger.error(f"Error getting last agent message: {e}")
            return None

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming chat message"""
        try:
            await self.process_command(message["message"])
            return {
                "message": self.state_manager.get_assistant_message() or "Message processed",
                "audio_response": None  # Add audio response if needed
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise Exception(f"Error processing message: {str(e)}")

    async def handle_audio(self, audio_bytes: bytes, 
                         user_id: str, 
                         session_id: str = "", 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process an incoming audio file"""
        try:
            metadata_dict = metadata or {}
            command = self.audio_handler.transcribe_audio(audio_bytes)
            await self.process_command(command)
            return {
                "status": "success",
                "message": self.state_manager.get_assistant_message() or "Audio processed"
            }
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise Exception(f"Error processing audio: {str(e)}")

    def update_state(self, last_user_message: str):
        """Aggiorna lo stato con la memoria a breve e lungo termine."""
        if last_user_message:
            # Aggiorna short_term_memory con l'ultimo messaggio
            if 'short_term_memory' not in self.state_manager.state:
                self.state_manager.state['short_term_memory'] = []
            self.state_manager.state['short_term_memory'].append({"message": last_user_message})

            # Mantieni solo gli ultimi 10 messaggi
            if len(self.state_manager.state['short_term_memory']) > 10:
                self.state_manager.state['short_term_memory'] = self.state_manager.state['short_term_memory'][-10:]

            # Estrai informazioni importanti e aggiorna long_term_memory
            important_info = self.extract_important_info(last_user_message)
            if important_info:
                if 'long_term_memory' not in self.state_manager.state:
                    self.state_manager.state['long_term_memory'] = {}
                if 'important_info' not in self.state_manager.state['long_term_memory']:
                    self.state_manager.state['long_term_memory']['important_info'] = []
                self.state_manager.state['long_term_memory']['important_info'].append(important_info)

    def extract_important_info(self, message: str) -> Optional[str]:
        """Estrai informazioni importanti dal messaggio."""
        keywords = ["preferenza", "importante", "informazione"]
        if any(keyword in message.lower() for keyword in keywords):
            return message
        return None

    def listen_and_process(self):
        """Ascolta il comando vocale e lo elabora."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("In ascolto...")
            audio = recognizer.listen(source)
            try:
                # Update the language parameter to match whisper's expected format
                command = recognizer.recognize_whisper(audio, language="italian", model="base")
                logger.info(f"Comando riconosciuto: {command}")
                asyncio.run(self.process_command(command))
            except sr.UnknownValueError:
                logger.warning("Whisper Recognition non ha capito l'audio.")
            except sr.RequestError as e:
                logger.error(f"Errore di richiesta a Whisper Recognition; {e}")

    def run(self):
        """Avvia il Voice Assistant."""
        logger.info("Voice Assistant avviato.")
        while self.listening:
            self.listen_and_process()
        logger.info("Voice Assistant terminato.")

    def save_conversation(self) -> None:
        """Save current conversation to memory"""
        try:
            state = self.state_manager.get_current_state()
            self.state_manager.memory_store.save_to_long_term_memory(
                "session_logs", 
                self.thread_id, 
                state
            )
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

def should_update_profile(command: str) -> bool:
    """Determina se aggiornare il profilo utente basato sul comando."""
    # Esempio: aggiorna il profilo se il comando contiene determinate parole chiave
    keywords = ["preferenze", "interessi", "profilo"]
    return any(keyword in command.lower() for keyword in command.lower())