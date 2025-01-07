# src/agents/greeting_agent.py

from typing_extensions import Literal
from langchain_openai import ChatOpenAI
import logging
from langgraph.types import Command
from src.tools.llm_tools import generate_response

logger = logging.getLogger("GreetingAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

def greeting_node(state: dict) -> Command[Literal["__end__"]]:
    collected_info = state.get("collected_info", "")
    logger.debug(f"Informazioni raccolte per GreetingAgent: {collected_info}")
    if not collected_info:
        logger.warning("Nessuna informazione raccolta disponibile per GreetingAgent.")
        return Command(goto="__end__", update={})

    try:
        assistant_response = generate_response(collected_info)
        logger.debug(f"Risposta generata dal GreetingAgent: {assistant_response}")
        return Command(
            goto="__end__",
            update={"messages": [{"type": "assistant", "content": assistant_response}]}
        )
    except Exception as e:
        logger.error(f"Errore nel greeting_node: {e}")
        return Command(goto="__end__", update={})
