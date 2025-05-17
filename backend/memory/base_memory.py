from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
import logging
import re
from datetime import datetime, timezone, timedelta
import json
import threading
from functools import wraps
import spacy
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_community.chat_message_histories.mongodb import MongoDBChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from ..common.objects import MessageTurn
from ..config import Settings, get_settings

# Patrones regex para extraer información del usuario
NAME_PATTERNS = [
    r'me llamo (\w+)',
    r'mi nombre es (\w+)',
    r'soy (\w+)',
    r'me llaman (\w+)'
]

PREFERENCE_PATTERNS = [
    r'me gusta (?:el|la|los|las) (\w+)',
    r'prefiero (?:el|la|los|las) (\w+)',
    r'me interesa (?:el|la|los|las) (\w+)'
]

def log_execution(logger: logging.Logger):
    """Decorador para logging de ejecución de métodos."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Ejecutando {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completado exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator


class SessionContext:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.user_info: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.last_updated: datetime = datetime.now(timezone.utc)
        self.session_start: datetime = datetime.now(timezone.utc)
        self.is_active: bool = True
        self.topics: List[str] = []
        self.preferences: Dict[str, Any] = {}

    def update_user_info(self, key: str, value: Any) -> None:
        self.user_info[key] = value
        self.last_updated = datetime.now(timezone.utc)
        logging.debug(f"Información de usuario actualizada - {key}: {value}")

    def add_to_history(self, role: str, content: str) -> None:
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        })
        self.last_updated = datetime.now(timezone.utc)

    def get_context_data(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_info": self.user_info,
            "last_updated": self.last_updated.isoformat(),
            "session_start": self.session_start.isoformat(),
            "is_active": self.is_active,
            "topics": self.topics,
            "preferences": self.preferences
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_info": self.user_info,
            "conversation_history": self.conversation_history,
            "last_updated": self.last_updated.isoformat(),
            "session_start": self.session_start.isoformat(),
            "is_active": self.is_active,
            "topics": self.topics,
            "preferences": self.preferences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        session = cls(data["session_id"])
        session.user_info = data["user_info"]
        session.conversation_history = data["conversation_history"]
        session.last_updated = datetime.fromisoformat(data["last_updated"])
        session.session_start = datetime.fromisoformat(data["session_start"])
        session.is_active = data["is_active"]
        session.topics = data.get("topics", [])
        session.preferences = data.get("preferences", {})
        return session


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


class BaseChatbotMemory(AbstractChatbotMemory):
    def __init__(
            self,
            settings: Optional[Settings] = None,
            chat_history_class: type[BaseChatMessageHistory] = ChatMessageHistory,
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
        super().__init__(settings=settings, session_id=session_id, k=k, **kwargs)
        self.chat_history_kwargs = chat_history_kwargs or {}
        self._base_memory_class = chat_history_class
        self._sessions: Dict[str, SessionContext] = {}
        
        # Inicializar NLP (opcional)
        self._nlp = None
        try:
            self._nlp = spacy.load("es_core_news_sm")
            logging.info("Modelo spaCy cargado exitosamente")
        except OSError:
            logging.warning("Modelo spaCy no encontrado. Usando regex como fallback")
        
        # Configuración de MongoDB
        try:
            mongo_uri = self.settings.mongo_uri.get_secret_value()
            self.mongo_client = MongoClient(mongo_uri)
            self.db = self.mongo_client[self.settings.mongo_database_name]
            self.sessions_collection = self.db["chat_sessions"]
        except Exception as e:
            logging.error(f"Error al conectar con MongoDB: {str(e)}")
            raise
        
        # Configuración de memoria
        memory_params = {
            "ai_prefix": self.settings.ai_prefix,
            "human_prefix": self.settings.human_prefix,
            "memory_key": "history",
            "k": self.k_history,
            "return_messages": True
        }
        memory_params.update(self._additional_kwargs)
        self._memory_class_instance_template = memory_class(**memory_params)
        self._user_memory_histories: Dict[str, BaseChatMessageHistory] = dict()
        
        # Iniciar limpieza de sesiones inactivas
        self._start_session_cleanup()

    def _start_session_cleanup(self):
        """Inicia el proceso de limpieza de sesiones inactivas."""
        def cleanup_task():
            while True:
                self._clean_inactive_sessions()
                threading.Event().wait(1800)  # Esperar 30 minutos
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def _clean_inactive_sessions(self):
        """Limpia sesiones inactivas."""
        try:
            inactive_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
            for session_id, session in list(self._sessions.items()):
                if session.last_updated < inactive_threshold:
                    self.clear(session_id)
                    logging.info(f"Sesión inactiva limpiada: {session_id}")
        except Exception as e:
            logging.error(f"Error al limpiar sesiones inactivas: {str(e)}")

    def _extract_user_info(self, message: str) -> Dict[str, Any]:
        """Extrae información del usuario usando NLP o regex como fallback."""
        info = {}
        
        if self._nlp:
            # Usar NLP si está disponible
            doc = self._nlp(message.lower())
            
            # Extraer nombres
            for ent in doc.ents:
                if ent.label_ == "PER":
                    info["nombre"] = ent.text
                    break
            
            # Extraer preferencias
            for token in doc:
                if token.dep_ == "dobj" and token.head.pos_ == "VERB":
                    if token.head.lemma_ in ["gustar", "preferir", "interesar"]:
                        info["preferencias"] = token.text
            
            # Extraer temas
            for token in doc:
                if token.pos_ == "NOUN" and token.dep_ in ["nsubj", "dobj"]:
                    if "topics" not in info:
                        info["topics"] = []
                    info["topics"].append(token.text)
        else:
            # Usar regex como fallback
            message_lower = message.lower()
            
            # Extraer nombre
            for pattern in NAME_PATTERNS:
                if match := re.search(pattern, message_lower):
                    info["nombre"] = match.group(1)
                    break
            
            # Extraer preferencias
            for pattern in PREFERENCE_PATTERNS:
                if match := re.search(pattern, message_lower):
                    info["preferencias"] = match.group(1)
                    break
        
        return info

    @log_execution(logging.getLogger(__name__))
    def store_message_in_memory(self, conversation_id: str, role: str, content: str) -> None:
        """Almacena un mensaje en la memoria."""
        try:
            session = self._get_or_create_session(conversation_id)
            specific_memory = self._get_or_create_conversation_memory(conversation_id)
            
            if role == "user":
                specific_memory.chat_memory.add_user_message(content)
                user_info = self._extract_user_info(content)
                for key, value in user_info.items():
                    if key == "topics":
                        session.topics.extend(value)
                    elif key == "preferencias":
                        session.preferences[key] = value
                    else:
                        session.update_user_info(key, value)
            else:
                specific_memory.chat_memory.add_ai_message(content)
            
            session.add_to_history(role, content)
            self._save_session_to_db(session)
            
        except Exception as e:
            logging.error(f"Error al almacenar mensaje: {str(e)}")
            raise

    @log_execution(logging.getLogger(__name__))
    def add_message(self, message_turn: MessageTurn):
        """Añade un mensaje a la conversación."""
        if not self._validate_message_turn(message_turn):
            return

        try:
            if message_turn.human_message and hasattr(message_turn.human_message, 'message'):
                self.store_message_in_memory(
                    message_turn.conversation_id,
                    "user",
                    message_turn.human_message.message
                )
            
            if message_turn.ai_message and hasattr(message_turn.ai_message, 'message'):
                self.store_message_in_memory(
                    message_turn.conversation_id,
                    "assistant",
                    message_turn.ai_message.message
                )
                
        except Exception as e:
            logging.error(f"Error al procesar mensaje: {str(e)}")
            raise

    def _validate_message_turn(self, message_turn: MessageTurn) -> bool:
        """Valida la estructura del mensaje."""
        if not message_turn or not message_turn.conversation_id:
            logging.error("MessageTurn inválido o sin conversation_id")
            return False
        return True

    @log_execution(logging.getLogger(__name__))
    def load_history(self, conversation_id: str) -> str:
        """Carga el historial de la conversación."""
        try:
            specific_memory = self._get_or_create_conversation_memory(conversation_id)
            session = self._get_or_create_session(conversation_id)
            
            loaded_vars = specific_memory.load_memory_variables({})
            history_str = loaded_vars.get(specific_memory.memory_key, "")
            
            context_data = session.get_context_data()
            if context_data:
                history_str = f"{json.dumps(context_data, ensure_ascii=False)}\n\n{history_str}"
            
            return history_str
            
        except Exception as e:
            logging.error(f"Error al cargar historial: {str(e)}")
            return ""

    def _save_session_to_db(self, session: SessionContext) -> None:
        """Guarda la sesión en la base de datos."""
        try:
            self.sessions_collection.update_one(
                {"session_id": session.session_id},
                {"$set": session.to_dict()},
                upsert=True
            )
        except PyMongoError as e:
            logging.error(f"Error al guardar sesión en DB: {str(e)}")
            raise

    def _load_session_from_db(self, session_id: str) -> Optional[SessionContext]:
        """Carga una sesión desde la base de datos."""
        try:
            session_data = self.sessions_collection.find_one({"session_id": session_id})
            if session_data:
                return SessionContext.from_dict(session_data)
        except PyMongoError as e:
            logging.error(f"Error al cargar sesión desde DB: {str(e)}")
            raise
        return None

    def _get_or_create_session(self, conversation_id: str) -> SessionContext:
        """Obtiene o crea una sesión."""
        if conversation_id not in self._sessions:
            # Intentar cargar desde DB
            session = self._load_session_from_db(conversation_id)
            if not session:
                session = SessionContext(conversation_id)
            self._sessions[conversation_id] = session
        return self._sessions[conversation_id]

    @log_execution(logging.getLogger(__name__))
    def clear(self, conversation_id: str):
        """Limpia la memoria y sesión."""
        try:
            # Limpiar memoria
            if conversation_id in self._user_memory_histories:
                history_instance = self._user_memory_histories.pop(conversation_id)
                if hasattr(history_instance, 'clear'):
                    history_instance.clear()
            
            # Limpiar sesión
            if conversation_id in self._sessions:
                del self._sessions[conversation_id]
            
            # Eliminar de DB
            self.sessions_collection.delete_one({"session_id": conversation_id})
            
        except Exception as e:
            logging.error(f"Error al limpiar conversación: {str(e)}")
            raise

    def get_langchain_memory_instance(self, conversation_id: str) -> Optional[ConversationBufferWindowMemory]:
        return self._get_or_create_conversation_memory(conversation_id)

    def get_chat_history_instance(self, conversation_id: str) -> Optional[BaseChatMessageHistory]:
        return self._user_memory_histories.get(conversation_id)

    def get_context_data(self, conversation_id: str) -> Dict[str, Any]:
        session = self._get_or_create_session(conversation_id)
        return session.get_context_data()

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

