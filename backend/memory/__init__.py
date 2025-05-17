from .base_memory import AbstractChatbotMemory, BaseChatbotMemory
from .mongo_memory import MongoChatbotMemory
from .custom_memory import CustomMongoChatbotMemory
from .memory_types import MemoryTypes  # <--- Añadir esta importación

# Asegurar que este diccionario coincida con el de memory_types.py
MEM_TO_CLASS = {
    MemoryTypes.BASE_MEMORY.value: BaseChatbotMemory,  # Usar BaseChatbotMemory para el tipo base
    MemoryTypes.MONGO_MEMORY.value: MongoChatbotMemory,
    MemoryTypes.CUSTOM_MEMORY.value: CustomMongoChatbotMemory,
}

__all__ = [
    "AbstractChatbotMemory",
    "BaseChatbotMemory",
    "MongoChatbotMemory",
    "CustomMongoChatbotMemory",
    "MemoryTypes",
    "MEM_TO_CLASS"
]
