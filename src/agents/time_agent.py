from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.time_tools import get_structured_time
import logging

logger = logging.getLogger("TimeAgent")

def time_agent(state: MessagesState) -> Command[Literal["greeting_agent"]]:
    """
    Fornisce l'orario attuale.
    """
    time_info = get_structured_time()
    time_str = f"L'orario attuale è {time_info['hour']:02}:{time_info['minute']:02}:{time_info['second']:02}."
    logger.debug(f"Time Agent risponde con messaggio: {time_str}")
    
    # Salva il risultato per il Greeting Agent
    state["last_agent_response"] = time_str

    # Reindirizza al Greeting Agent per comunicare il risultato
    return Command(goto="greeting_agent", update={})
