from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.time_tools import get_structured_time
import logging

logger = logging.getLogger("TimeAgent")

def time_agent(state: MessagesState) -> Command[Literal["greeting", "__end__"]]:
    if "original_message" not in state or not state["original_message"]:
        logger.warning("'original_message' non trovato in time_agent. Aggiungendo valore predefinito.")
        state["original_message"] = "Messaggio non disponibile"

    time_info = get_structured_time()
    time_str = f"L'orario attuale è {time_info['hour']:02}:{time_info['minute']:02}:{time_info['second']:02}."
    logger.debug(f"Time Agent risponde con messaggio: {time_str}")

    state["last_agent_response"] = time_str

    return Command(goto="greeting", update={})  # Cambiato da "greeting_agent" a "greeting"
