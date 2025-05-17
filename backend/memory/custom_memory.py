import json
from typing import List, Optional
from pymongo import MongoClient, errors
import logging
import datetime

from .base_memory import AbstractChatbotMemory
from ..common.objects import MessageTurn, messages_from_dict
from ..config import Settings, get_settings


class _CustomMongoPersistence:
    """Clase interna para manejar la lógica de persistencia directa con MongoDB."""
    def __init__(
            self,
            settings: Settings,
            # session_id es el identificador de la "sesión" general de esta instancia de persistencia.
            # conversation_id se usará para referirse a hilos de chat específicos dentro de esta sesión.
            session_id: str, 
            k: int
    ):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection_string = self.settings.mongo_uri
        self.session_id = session_id # Este es el session_id de la instancia _CustomMongoPersistence
        self.k = k

        try:
            temp_client = MongoClient(self.connection_string)
            # Intentar obtener el nombre de la BD de la URI, si no, usar el de settings, si no, default.
            parsed_db_name = temp_client.get_default_database().name
            self.database_name = parsed_db_name if parsed_db_name else getattr(self.settings, 'mongo_database_name', "chatbot_db")
            if not parsed_db_name:
                 self.logger.warning(f"MongoDB URI no especifica una BD. Usando: {self.database_name}")
            temp_client.close()
        except Exception as e:
            self.logger.error(f"Error al parsear nombre de BD de URI MongoDB '{self.connection_string}': {e}. Usando default.")
            self.database_name = getattr(self.settings, 'mongo_database_name', "chatbot_db")
            
        self.collection_name = self.settings.mongo_collection_name

        try:
            self.client: MongoClient = MongoClient(self.connection_string)
        except errors.ConnectionFailure as error:
            self.logger.error(f"Fallo al conectar a MongoDB: {error}")
            raise

        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]
        try:
            # El índice debe incluir SessionId y ConversationId para búsquedas eficientes
            self.collection.create_index([("SessionId", 1), ("ConversationId", 1)])
        except errors.OperationFailure as e:
            self.logger.error(f"Fallo al crear índice en (SessionId, ConversationId): {e}")

    def add_message_turn(self, message_turn: MessageTurn):
        # Aquí, message_turn.conversation_id es el ID específico del chat.
        # self.session_id es el ID de la sesión de esta instancia de _CustomMongoPersistence.
        if not message_turn.conversation_id:
            self.logger.error("No se puede añadir mensaje: conversation_id falta en MessageTurn.")
            return
        if not self.session_id:
             self.logger.error("No se puede añadir mensaje: session_id no está configurado en _CustomMongoPersistence.")
             return

        try:
            self.logger.info(f"Guardando 1 turno de mensaje para conversation_id <{message_turn.conversation_id}> en session_id <{self.session_id}>")
            document_to_insert = {
                "SessionId": self.session_id, # session_id de la instancia de memoria
                "ConversationId": message_turn.conversation_id, # conversation_id del MessageTurn
                "History": json.dumps(message_turn.dict(), ensure_ascii=False),
                "timestamp": datetime.datetime.utcnow() # Añadir timestamp para posible ordenación o TTL
            }
            self.collection.insert_one(document_to_insert)
        except errors.WriteError as err:
            self.logger.error(f"MongoDB WriteError: {err}")
        except Exception as e:
            self.logger.error(f"Error inesperado añadiendo mensaje a MongoDB: {e}")

    def clear_conversation_history(self, conversation_id: str):
        # Limpia una conversación específica DENTRO de la sesión de esta instancia de persistencia.
        if not self.session_id:
            self.logger.error("No se puede limpiar: session_id no está configurado.")
            return 0
        try:
            filter_query = {"SessionId": self.session_id, "ConversationId": conversation_id}
            self.logger.info(f"Eliminando historial para conversation_id <{conversation_id}> en session_id <{self.session_id}>")
            result = self.collection.delete_many(filter_query)
            self.logger.info(f"Eliminados {result.deleted_count} turnos de mensajes.")
            return result.deleted_count
        except errors.WriteError as err:
            self.logger.error(f"MongoDB WriteError durante clear_conversation_history: {err}")
        except Exception as e:
            self.logger.error(f"Error inesperado durante clear_conversation_history: {e}")
        return 0

    def load_conversation_history(self, conversation_id: str) -> str:
        if not self.session_id:
            self.logger.error("No se puede cargar: session_id no está configurado.")
            return ""
        
        cursor = None
        try:
            # Ordenar por timestamp para obtener los más recientes si k es relevante.
            # El límite k se aplica después de la carga si es necesario mantener la compatibilidad
            # de `messages_from_dict` que procesa una lista.
            cursor = self.collection.find(
                {"SessionId": self.session_id, "ConversationId": conversation_id}
            ).sort("timestamp", -1).limit(self.k)
        except errors.OperationFailure as error:
            self.logger.error(f"MongoDB OperationFailure durante load_conversation_history: {error}")

        items = []
        if cursor:
            try:
                # Los documentos ya vienen ordenados por timestamp descendente (más nuevo primero)
                # Para un historial cronológico, necesitamos invertirlos.
                loaded_documents = list(cursor)
                items = [json.loads(document["History"]) for document in reversed(loaded_documents)] 
            except json.JSONDecodeError as e:
                self.logger.error(f"JSONDecodeError cargando historial para conv <{conversation_id}>: {e}")
            except Exception as e:
                self.logger.error(f"Error inesperado procesando documentos para conv <{conversation_id}>: {e}")
        
        if not items:
            self.logger.info(f"No se encontró historial para conversation_id <{conversation_id}> en session_id <{self.session_id}>")
            return ""

        message_strings: List[str] = []
        for item_idx, item_content in enumerate(items):
            try:
                message_strings.append(messages_from_dict(item_content))
            except Exception as e:
                self.logger.error(f"Error convirtiendo dict a string para item {item_idx} en conv <{conversation_id}>: {e}. Item: {item_content}")
        
        return "\n".join(message_strings)


class CustomMongoChatbotMemory(AbstractChatbotMemory):
    def __init__(self, settings: Optional[Settings] = None, session_id: str = "default_custom_session", k: Optional[int] = None, **kwargs):
        # session_id aquí es el ID para la instancia _CustomMongoPersistence.
        # k se pasa a AbstractChatbotMemory que lo almacena en self.k_history.
        super().__init__(settings=settings, session_id=session_id, k=k, **kwargs)
        
        if not self.session_id:
            self.logger.warning("session_id no provisto a CustomMongoChatbotMemory. Usando default. El historial podría ser compartido o no guardado correctamente si no es único donde se espera.")
            # El __init__ de AbstractChatbotMemory ya asigna self.session_id.

        self._persistence = _CustomMongoPersistence(
            settings=self.settings,
            session_id=self.session_id, # Usar el session_id de la instancia de memoria
            k=self.k_history # Usar k_history de la clase base abstracta
        )

    def clear(self, conversation_id: str):
        """Limpia el historial de la conversación especificada DENTRO de la sesión de esta memoria."""
        if not conversation_id:
            self.logger.error("No se puede limpiar historial: conversation_id no fue provisto.")
            return
        self._persistence.clear_conversation_history(conversation_id=conversation_id)

    def load_history(self, conversation_id: str) -> str:
        """Carga el historial para el conversation_id especificado DENTRO de la sesión de esta memoria."""
        if not conversation_id:
            self.logger.warning("load_history llamado sin conversation_id.")
            return ""
        return self._persistence.load_conversation_history(conversation_id)

    def add_message(self, message_turn: MessageTurn):
        """Añade un MessageTurn. El message_turn.conversation_id identifica la conversación específica."""
        # message_turn.conversation_id es crucial aquí.
        # El self.session_id de esta instancia de memoria agrupa estas conversaciones en MongoDB.
        if not message_turn or not message_turn.conversation_id:
             self.logger.error("No se puede añadir mensaje: MessageTurn inválido o conversation_id faltante.")
             return
        self._persistence.add_message_turn(message_turn)

    # Este método no es parte de la interfaz AbstractChatbotMemory mínima,
    # pero puede ser útil si se quiere acceder directamente a la capa de persistencia.
    def get_persistence_layer(self) -> _CustomMongoPersistence:
        return self._persistence
