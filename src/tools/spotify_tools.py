# src/tools/spotify_tools.py

import logging
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from src.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

logger = logging.getLogger("SpotifyTools")

def get_spotify_client():
    try:
        sp = Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-modify-playback-state user-read-playback-state"
        ))
        return sp
    except Exception as e:
        logger.error(f"Errore durante l'autenticazione con Spotify: {e}")
        return None

def search_and_analyze_tracks(query: str):
    sp = get_spotify_client()
    if not sp:
        return []
    try:
        logger.debug(f"Ricerca su Spotify per: {query}")
        results = sp.search(q=query, type="track", limit=5)
        tracks = [{"name": track["name"], "artist": track["artists"][0]["name"], "uri": track["uri"]}
                  for track in results["tracks"]["items"]]
        logger.debug(f"Tracce trovate: {tracks}")
        return tracks
    except Exception as e:
        logger.error(f"Errore durante la ricerca su Spotify: {e}")
        return []

def play_spotify_on_device(track_uri: str, device_name: str = None):
    sp = get_spotify_client()
    if not sp:
        logger.error("Cliente Spotify non disponibile.")
        return False
    try:
        devices = sp.devices()["devices"]
        device_id = None

        if device_name:
            device_id = next((d["id"] for d in devices if d["name"].lower() == device_name.lower()), None)
            if not device_id:
                logger.warning(f"Dispositivo '{device_name}' non trovato. Seleziono un dispositivo attivo predefinito.")
        
        if not device_id:
            # Se non specificato o non trovato, seleziona il primo dispositivo attivo
            active_devices = [d for d in devices if d["is_active"]]
            device_id = active_devices[0]["id"] if active_devices else None
            if not device_id:
                logger.warning("Nessun dispositivo attivo trovato.")

        if device_id:
            sp.start_playback(device_id=device_id, uris=[track_uri])
            logger.debug(f"Riproduzione iniziata su dispositivo: {device_name if device_name else 'dispositivo attivo predefinito'}")
            return True
        else:
            logger.warning("Impossibile trovare un dispositivo valido per la riproduzione.")
            return False
    except Exception as e:
        logger.error(f"Errore durante la riproduzione su Spotify: {e}")
        return False
