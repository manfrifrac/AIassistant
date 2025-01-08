# src/agents/greeting_agent.py

from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import logging
from typing import Literal

from src.tools.llm_tools import generate_response

logger = logging.getLogger("GreetingAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

# Creazione del greeting agent
greeting_agent = create_react_agent(
    llm, tools=[], state_modifier="Sei un assistente che fornisce risposte cordiali e riassuntive."
)

def greeting_node(state: dict) -> Command[Literal["__end__"]]:
    collected_info = state.get("collected_info", "")
    if not collected_info:
        return Command(goto="__end__")

    try:
        assistant_response = generate_response(collected_info)
        return Command(
            goto="__end__",
            update={
                "agent_messages": state.get("agent_messages", []) + [
                    {"content": assistant_response, "role": "assistant"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Errore nel greeting_node: {e}")
        return Command(goto="__end__")
