# src/agents/greeting_agent.py

from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import generate_response
import logging
from langgraph.graph import END

logger = logging.getLogger("GreetingAgent")


def greeting_node(state: dict) -> Command[Literal["__end__"]]:
    logger.debug(f"Invoking greeting_node with state: {state}")

    collected_info = state.get("collected_info", "")
    logger.debug(f"Collected Info: {collected_info}")
    
    if not collected_info:
        logger.debug("Nessuna informazione raccolta. Termino la conversazione.")
        return Command(goto=END)

    try:
        assistant_response = generate_response(collected_info)
        logger.debug(f"Risposta generata dall'assistente: {assistant_response}")
        return Command(
            goto=END,
            update={
                "agent_messages": state.get("agent_messages", []) + [
                    {"content": assistant_response, "role": "assistant"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Errore nel greeting_node: {e}")
        return Command(goto=END)
