# src/agents/__init__.py

from .greeting_agent import greeting_agent
from .time_agent import time_agent
from .spotify_agent import spotify_agent
from .supervisor import supervisor
from .coder_agent import coder

# Esporta tutti gli agenti
__all__ = [
    "greeting_agent",
    "time_agent",
    "spotify_agent",
    "supervisor",
    "coder",
]
