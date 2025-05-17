from abc import ABC, abstractmethod
from typing import Optional, Dict
import logging

from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory # MODIFIED
from langchain_core.chat_history import BaseChatMessageHistory # MODIFIED

from ..common.objects import MessageTurn
from ..config import Settings, get_settings


class AbstractChatbotMemory(ABC):
    def __init__(self, settings: Optional[Settings] = None, session_id: Optional[str] = None, k: Optional[int] = None, **kwargs):
        self.settings = settings if settings is not None else get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session_id = session_id
        self.k_history = k if k is not None else (self.settings.memory_window_size if hasattr(self.settings, 'memory_window_size') else 5)
        # Guardar otros kwargs para subclases si los necesitan
        self._additional_kwargs = kwargs

    @abstractmethod
    def add_message(self, message_turn: MessageTurn):
        """Añade un turno de mensajes (humano y AI) a la memoria."""
        pass

    @abstractmethod
    def load_history(self, conversation_id: str) -> str:
        """Carga el historial de la conversación como un string formateado."""
        pass

    @abstractmethod
    def clear(self, conversation_id: str):
        """Limpia el historial de la conversación especificada."""
        pass

    # Opcional: Método para obtener la instancia de Langchain si es aplicable
    # @abstractmethod
    # def get_langchain_memory_instance(self, conversation_id: str) -> Optional[ConversationBufferWindowMemory]:
    #     pass


class BaseChatbotMemory(AbstractChatbotMemory): # Modificado para heredar
    def __init__(
            self,
            settings: Optional[Settings] = None,
            chat_history_class: type[BaseChatMessageHistory] = ChatMessageHistory, # type hint más específico
            memory_class=ConversationBufferWindowMemory,
            chat_history_kwargs: Optional[dict] = None,
            session_id: Optional[str] = None,
            k: Optional[int] = None,
            **kwargs
    ):
        """
        Base chatbot_backend memory
        :param settings: Application settings object
        :param chat_history_class: LangChain's chat history class (e.g., ChatMessageHistory, MongoDBChatMessageHistory)
        :param memory_class: LangChain's memory class (typically ConversationBufferWindowMemory)
        :param chat_history_kwargs: Kwargs for chat_history_class (e.g., connection_string for MongoDB)
        :param session_id: Session ID, primarily for DB-backed history. If MongoDBChatMessageHistory is used,
                           this session_id will be passed to it if not already in chat_history_kwargs.
                           It is also used by BaseChatbotMemory to manage multiple conversation histories if needed.
        :param k: Window size for ConversationBufferWindowMemory
        :param kwargs: Memory class kwargs (passed to memory_class)
        """
        super().__init__(settings=settings, session_id=session_id, k=k, **kwargs) # Llamar al __init__ de AbstractChatbotMemory
        
        self.chat_history_kwargs = chat_history_kwargs or {}
        
        # Si se proporciona un session_id global y la clase de historial es MongoDBChatMessageHistory (o similar que lo use)
        # y no se ha especificado un session_id en chat_history_kwargs, lo usamos.
        # Sin embargo, la lógica de _get_or_create_conversation_memory priorizará conversation_id para Mongo.
        if self.session_id and 'session_id' not in self.chat_history_kwargs and hasattr(chat_history_class, 'session_id'):
             self.chat_history_kwargs['session_id'] = self.session_id
        
        self._base_memory_class = chat_history_class
        
        memory_params = {
            "ai_prefix": self.settings.ai_prefix,
            "human_prefix": self.settings.human_prefix,
            "memory_key": "history",
            "k": self.k_history # Usar el k del __init__ de la clase abstracta
        }
        # kwargs pasados al init de BaseChatbotMemory (que no son session_id, k, etc.)
        # se pasan a memory_class (ConversationBufferWindowMemory)
        memory_params.update(self._additional_kwargs) 

        self._memory_class_instance_template = memory_class(**memory_params)
        self._user_memory_histories: Dict[str, BaseChatMessageHistory] = dict() # type hint más específico

    @property
    def memory_template(self):
        return self._memory_class_instance_template

    def _get_or_create_conversation_memory(self, conversation_id: str) -> ConversationBufferWindowMemory:
        if conversation_id not in self._user_memory_histories:
            current_chat_history_kwargs = self.chat_history_kwargs.copy()
            
            # Para MongoDBChatMessageHistory, el conversation_id DEBE ser el session_id.
            # Esta lógica asegura que cada conversación tenga su propio historial aislado en Mongo.
            # Importar aquí para evitar dependencia cíclica o error si no se usa
            from langchain_community.chat_message_histories.mongodb import MongoDBChatMessageHistory
            if issubclass(self._base_memory_class, MongoDBChatMessageHistory):
                if current_chat_history_kwargs.get('session_id') != conversation_id:
                    self.logger.debug(f"Forcing session_id to conversation_id ('{conversation_id}') for MongoDBChatMessageHistory.")
                current_chat_history_kwargs['session_id'] = conversation_id
            elif self.session_id and 'session_id' not in current_chat_history_kwargs and hasattr(self._base_memory_class, 'session_id'):
                # Para otras clases de historial que usan session_id, pero no son MongoDBChatMessageHistory
                # (aunque es raro), usamos el session_id global si está disponible.
                current_chat_history_kwargs['session_id'] = self.session_id

            chat_history_instance = self._base_memory_class(**current_chat_history_kwargs)
            self._user_memory_histories[conversation_id] = chat_history_instance
        
        specific_memory_instance = ConversationBufferWindowMemory(
            chat_memory=self._user_memory_histories[conversation_id],
            ai_prefix=self.memory_template.ai_prefix,
            human_prefix=self.memory_template.human_prefix,
            memory_key=self.memory_template.memory_key,
            k=self.memory_template.k,
            input_key=self.memory_template.input_key if hasattr(self.memory_template, 'input_key') else None,
            output_key=self.memory_template.output_key if hasattr(self.memory_template, 'output_key') else None
        )
        return specific_memory_instance

    def clear(self, conversation_id: str):
        if conversation_id in self._user_memory_histories:
            history_instance = self._user_memory_histories.pop(conversation_id)
            if hasattr(history_instance, 'clear'): # MongoDBChatMessageHistory tiene clear()
                try:
                    history_instance.clear()
                    self.logger.info(f"Cleared history for conversation_id: {conversation_id} from underlying ChatMessageHistory.")
                except Exception as e:
                    self.logger.error(f"Error clearing history from ChatMessageHistory for {conversation_id}: {e}")
            else:
                 self.logger.info(f"ChatMessageHistory for {conversation_id} does not have a clear method. Removed from in-memory cache.")
        else:
            self.logger.info(f"No history found to clear for conversation_id: {conversation_id}")

    def load_history(self, conversation_id: str) -> str:
        specific_memory = self._get_or_create_conversation_memory(conversation_id)
        loaded_vars = specific_memory.load_memory_variables({})
        history_str = loaded_vars.get(specific_memory.memory_key, "")
        self.logger.debug(f"Loaded history for {conversation_id}: {history_str[:200]}...")
        return history_str

    def add_message(self, message_turn: MessageTurn):
        if not message_turn or not message_turn.conversation_id:
            self.logger.error("Cannot add message: MessageTurn or conversation_id is missing.")
            return

        conversation_id = message_turn.conversation_id
        specific_memory = self._get_or_create_conversation_memory(conversation_id)
        
        # Accedemos a chat_memory (que es una instancia de BaseChatMessagesHistory) para añadir mensajes
        if message_turn.human_message and hasattr(message_turn.human_message, 'message') and message_turn.human_message.message:
            specific_memory.chat_memory.add_user_message(message_turn.human_message.message)
        
        if message_turn.ai_message and hasattr(message_turn.ai_message, 'message') and message_turn.ai_message.message:
            specific_memory.chat_memory.add_ai_message(message_turn.ai_message.message)
        
        self.logger.debug(f"Added message turn to conversation {conversation_id}")

    def get_langchain_memory_instance(self, conversation_id: str) -> Optional[ConversationBufferWindowMemory]:
        """Devuelve la instancia de Langchain ConversationBufferWindowMemory para un conversation_id específico."""
        if not conversation_id:
            self.logger.warning("get_langchain_memory_instance called without conversation_id")
            return None
        return self._get_or_create_conversation_memory(conversation_id)

    def get_chat_history_instance(self, conversation_id: str) -> Optional[BaseChatMessageHistory]: # type hint más específico
        """Devuelve la instancia subyacente de BaseChatMessagesHistory (ej. MongoDBChatMessageHistory)."""
        if conversation_id in self._user_memory_histories:
            return self._user_memory_histories[conversation_id]
        self.logger.debug(f"No underlying chat history instance found for conversation_id: {conversation_id}")
        return None

# Ejemplo de cómo podría ser una clase de historial muy simple para pruebas (no para producción)
# from langchain.schema import BaseMessage, HumanMessage, AIMessage
# class SimpleChatMessageHistory(BaseChatMessagesHistory):
#     def __init__(self):
#         self.messages: List[BaseMessage] = []
#     @property
#     def messages(self) -> List[BaseMessage]:
#         return self._messages
#     @messages.setter
#     def messages(self, messages_list: List[BaseMessage]):
#         self._messages = messages_list
#     def add_message(self, message: BaseMessage) -> None:
#         self.messages.append(message)
#     def add_user_message(self, message: str) -> None:
#         self.add_message(HumanMessage(content=message))
#     def add_ai_message(self, message: str) -> None:
#         self.add_message(AIMessage(content=message))
#     def clear(self) -> None:
#         self.messages = []
