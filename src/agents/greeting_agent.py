# src/agents/greeting_agent.py
from langchain_openai import ChatOpenAI

from src.tools.llm_tools import generate_response
import logging

logger = logging.getLogger("GreetingAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def greeting_agent(state: dict) -> dict:
    logger.debug(f"Stato ricevuto dal greeting_agent: {state}")

    # Estrai le informazioni raccolte dal SupervisorAgent
    collected_info = state.get("collected_info", "Nessuna informazione disponibile.")
    logger.debug(f"Informazioni raccolte per GreetingAgent: {collected_info}")

    # Genera una risposta naturale basata sulle informazioni raccolte
    response = generate_response(collected_info)
    logger.debug(f"Risposta generata dal GreetingAgent: {response}")

    # Logica di terminazione basata sull'input dell'utente
    terminate = state.get("terminate", False)
    logger.debug(f"Flag di terminazione: {terminate}")

    if terminate:
        final_message = "Grazie per aver utilizzato il Voice Assistant. Arrivederci!"
        return {
            "update": {
                "messages": [{"type": "assistant", "content": final_message}],
                "last_agent_response": final_message
            },
            "goto": "__end__"
        }
    else:
        return {
            "update": {
                "messages": [{"type": "assistant", "content": response}],
                "last_agent_response": response
            },
            "goto": "__end__"  # Termina dopo aver risposto; il ciclo di ascolto è gestito nel VoiceAssistant
        }
