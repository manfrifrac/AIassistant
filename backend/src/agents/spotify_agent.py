from langgraph.graph import MessagesState
from langgraph.types import Command
from typing import Literal
from src.tools.spotify_tools import search_and_analyze_tracks
import logging

logger = logging.getLogger("SpotifyAgent")

def spotify_agent(state: MessagesState) -> Command[Literal["greeting", "__end__"]]:
    """
    Gestisce la ricerca e analisi di tracce su Spotify.
    """
    last_message = state.get("original_message", "").strip()
    logger.debug(f"Spotify Agent ricevuto messaggio: {last_message}")

    if not last_message:
        response_message = "La query di ricerca è vuota. Fornisci un titolo o un artista."
        logger.warning(response_message)
        state["last_agent_response"] = response_message
        return Command(goto="greeting", update={})  # Cambiato da "greeting_agent" a "greeting"

    # Ricerca tracce su Spotify
    try:
        results = search_and_analyze_tracks(last_message)
        if not results:
            response_message = f"Nessun brano trovato per '{last_message}'."
        else:
            response_message = f"Trovati {len(results)} brani. Primo brano: {results[0]['name']} di {results[0]['artist']}."
    except Exception as e:
        response_message = f"Errore durante la ricerca su Spotify: {e}"

    logger.debug(f"Spotify Agent aggiorna il messaggio: {response_message}")
    state["last_agent_response"] = response_message
    return Command(goto="greeting", update={})  # Cambiato da "greeting_agent" a "greeting"
