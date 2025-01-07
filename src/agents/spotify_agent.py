from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.spotify_tools import search_and_analyze_tracks
import logging

logger = logging.getLogger("SpotifyAgent")

def spotify_agent(state: MessagesState) -> Command[Literal["greeting_agent"]]:
    """
    Gestisce la ricerca e analisi di tracce su Spotify.
    """
    last_message = state.get("original_message", "")
    logger.debug(f"Spotify Agent ricevuto messaggio: {last_message}")

    # Ricerca tracce su Spotify
    results = search_and_analyze_tracks(last_message)
    if not results:
        response_message = f"Nessun brano trovato per '{last_message}'."
    else:
        response_message = f"Trovati {len(results)} brani. Primo brano: {results[0]['name']} di {results[0]['artist']}."

    logger.debug(f"Spotify Agent aggiorna il messaggio: {response_message}")
    state["last_agent_response"] = response_message
    return Command(goto="greeting_agent", update={})
