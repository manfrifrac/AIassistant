from backend.src.agents.base import BaseAgent, NodeType  # Fix import
from langgraph.graph import END
from langgraph.types import Command
from typing import Literal, Dict, Any, List, Optional
from uuid import uuid4, UUID  # Imported UUID
import logging
from backend.src.tools.llm_tools import vectorize_messages, semantic_search  # Re-add necessary imports
from backend.src.models import MessageResponse  # Import MessageResponse
import json

logger = logging.getLogger("SupervisorAgent")

# Definisci i membri (agenti) gestiti dal Supervisor
members = ["researcher", "greeting"]

class SupervisorAgent(BaseAgent):
    """
    The SupervisorAgent:
    Input:
      - {user_message}
      - {interaction_id}
      - {stm_data}
      - {ltm_data}
    Operations:
      - Determines selected_agent based on user_message
      - Builds context for the selected agent
    Output:
      - {selected_agent}
      - {context}
    """
    def __init__(self, agent_id, config, memory_store):
        super().__init__(agent_id, config)
        self.memory_store = memory_store
        self.system_prompt = """You are a sophisticated supervisor managing a conversation flow.
        Analyze the user's message carefully to determine whether to use the RESEARCHER or GREETING agent.

        Use RESEARCHER when:
        - The user asks a specific question
        - Requests factual information
        - Needs detailed explanations
        - Shows curiosity about a topic

        Use GREETING when:
        - The user makes casual conversation
        - Expresses emotions or personal statements
        - Responds to previous answers
        - Makes acknowledgments or confirmations
        - The message is primarily social/interactive

        Current conversation context and message history are important for making this decision.
        Respond ONLY with 'RESEARCHER' or 'GREETING' in uppercase.
        """

    def determine_next_agent(self, user_message: str, state: dict) -> str:
        if not user_message:
            logger.warning("Empty user message received")
            return "GREETING"
            
        try:
            logger.debug(f"[DETERMINE_AGENT] Input state: {state}")
            logger.debug(f"[DETERMINE_AGENT] User message: {user_message}")

            # Create context
            context = {
                "current_message": user_message,
                "previous_messages": [m.get("content", "") for m in state.get("user_messages", [])[-3:]],
                "previous_responses": [m.get("content", "") for m in state.get("agent_messages", [])[-3:]],
                "last_agent": state.get("last_agent", "")
            }
            logger.debug(f"[DETERMINE_AGENT] Created context: {context}")

            # Create model messages
            model_messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Previous context: {json.dumps(context)}\n\nUser message: {user_message}"}
            ]
            logger.debug(f"[DETERMINE_AGENT] Model input: {model_messages}")

            # Get model response
            response = self.llm.invoke(input=model_messages)
            next_agent = response.content
            logger.debug(f"[DETERMINE_AGENT] Raw model response: {response.content}")

            if next_agent not in {"RESEARCHER", "GREETING"}:
                logger.warning(f"[DETERMINE_AGENT] Invalid response: {next_agent}, defaulting to GREETING")
                return "GREETING"

            logger.debug(f"[DETERMINE_AGENT] Final decision: {next_agent}")
            return next_agent

        except Exception as e:
            logger.error(f"Error in determine_next_agent: {str(e)}", exc_info=True)
            return "ERROR"  # Changed from "GREETING"

    def process(self, state: Dict[str, Any]) -> Command[NodeType]:
        if not isinstance(state, dict):
            return Command(
                goto="error",
                output={
                    "error": True,
                    "error_message": "Invalid state type"
                }
            )

        try:
            if not self.validate_state(state):
                logger.error("Invalid state structure")
                return Command(
                    goto="error",
                    output={
                        "error": True,
                        "error_message": "Invalid state structure"
                    }
                )

            # Get user message from state
            user_message = state.get("content", "") if isinstance(state, dict) else ""
            if not user_message:
                user_message = state.get("last_user_message", "")

            logger.debug(f"Processing message: {user_message}")
            
            # Determine next agent
            next_agent = self.determine_next_agent(user_message, state)
            logger.debug(f"Determined next agent: {next_agent}")

            # Return command with state updates
            return Command(
                goto=next_agent.lower(),
                output={
                    "last_user_message": user_message,
                    "next_agent": next_agent.lower(),
                    "routing_message": f"Routing to {next_agent.lower()} agent"
                }
            )

        except Exception as e:
            logger.error(f"Error in supervisor process: {str(e)}", exc_info=True)
            return Command(
                goto="error",
                output={
                    "error": True,
                    "error_message": str(e)
                }
            )

    def validate_state(self, state: Dict[str, Any]) -> bool:
        return ("user_messages" in state and 
                isinstance(state["user_messages"], list) and 
                len(state["user_messages"]) > 0)

    def get_last_user_message(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Move this method inside the class"""
        if not isinstance(messages, list):
            logger.error("Invalid messages type")
            return None

        try:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    return msg.get("content", "")
            self.logger.warning("No valid user message found.")
            return ""
        except Exception as e:
            self.logger.error(f"Error extracting last user message: {e}")
            return None

    async def process_request(self, user_id: UUID, message: str, session_id: Optional[UUID], metadata: Dict[str, Any]) -> MessageResponse:
        """
        Process the incoming message and return a response.
        """
        # Implement the logic to process the message
        try:
            logger.debug(f"Processing request from user_id: {user_id}, message: {message}")
            # Example processing logic
            response_message = f"Received your message: {message}"
            return MessageResponse(
                message=response_message,
                session_id=session_id or uuid4(),
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise e

def _format_debug_state(state: dict) -> dict:
    """Formatta lo stato per debug log"""
    return {
        'last_message': state.get('last_user_message', ''),
        'next_agent': state.get('next_agent', ''),
        'processed_count': len(state.get('processed_messages', []))
    }

def create_supervisor_node(memory_store):
    agent = SupervisorAgent(uuid4(), {"model": "gpt-3.5-turbo"}, memory_store)
    return agent.process

def find_relevant_messages(state: dict, last_user_message: str) -> List[Dict[str, Any]]:
    """Trova i messaggi rilevanti basati sull'ultimo messaggio dell'utente."""
    try:
        # Vettorializza i messaggi precedenti
        previous_messages = state.get("user_messages", []) + state.get("agent_messages", [])
        if not previous_messages:
            logger.debug("Nessun messaggio precedente trovato.")
            return []
        vectors = vectorize_messages(previous_messages)
        #logger.debug(f"Vettori dei messaggi: {vectors}")

        # Trova i messaggi rilevanti utilizzando una ricerca semantica
        relevant_messages = semantic_search(vectors, last_user_message, previous_messages)
        logger.debug(f"Messaggi rilevanti trovati: {relevant_messages}")  # Added relevant_messages argument
        return relevant_messages
    except ValueError as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []
    except Exception as e:
        logger.error(f"Errore durante la ricerca dei messaggi rilevanti: {e}")
        return []