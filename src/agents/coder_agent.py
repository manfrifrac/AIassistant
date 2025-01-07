# src/agents/coder_agent.py

from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage  # Assicurati che AIMessage sia importato correttamente
from typing import Literal
from src.tools.custom_tools import python_repl_tool
from langgraph.prebuilt import create_react_agent
import logging
from langchain_openai import ChatOpenAI

logger = logging.getLogger("CoderAgent")

llm = ChatOpenAI(model="gpt-3.5-turbo")

coder_agent = create_react_agent(
    llm, tools=[python_repl_tool], state_modifier="Sei un programmatore. Esegui solo il codice Python fornito."
)

def coder_node(state: MessagesState) -> Command[Literal["supervisor", "__end__"]]:
    try:
        result = coder_agent.invoke(state)
        # Supponiamo che 'result' sia un AIMessage
        user_message = state.get_last_user_message().content.lower()
        if "fine" in user_message or "termina" in user_message:
            return Command(goto="__end__")
        else:
            return Command(goto="supervisor")
    except Exception as e:
        logger.error(f"Errore nel coder_node: {e}")
        return Command(goto="__end__")
