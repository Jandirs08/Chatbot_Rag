# This file is intentionally left mostly empty to avoid circular imports
# Only import what's necessary for basic package initialization
"""LangChain Chatbot backend package."""

__version__ = "1.0.0"

# Expose key components for easier imports from the backend package root
from .config import settings, get_settings # Corregido de vuelta a .config
# from .common.config import settings, get_settings # Línea incorrecta comentada
from .chat.manager import ChatManager

__all__ = [
    "settings", 
    "get_settings", 
    "ChatManager"
]
