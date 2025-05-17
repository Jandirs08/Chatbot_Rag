import asyncio
import logging
from queue import Queue
from typing import Optional, Dict, Union, List, Any
from operator import itemgetter

from langchain.agents import AgentExecutor
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableMap, Runnable
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
# from langchain_core.tracers.context import wait_for_all_tracers # COMMENTED OUT

from .memory import MemoryTypes, MEM_TO_CLASS, AbstractChatbotMemory
from .models import ModelTypes
from .common.objects import Message, MessageTurn
from .common.constants import *
from .chain import ChainManager
from . import prompt as prompt_module
from .utils import BotAnonymizer, CacheTypes, ChatbotCache
from .tools import CustomSearchTool
from .config import Settings, get_settings


class Bot:
    def __init__(
            self,
            settings: Optional[Settings] = None,
            memory_type: Optional[MemoryTypes] = None,
            cache: Optional[CacheTypes] = None,
            model_type: Optional[ModelTypes] = None,
            memory_kwargs: Optional[dict] = None,
            custom_bot_personality_str: Optional[str] = None,
            tools_list: Optional[List[Any]] = None
    ):
        self.settings = settings if settings is not None else get_settings()
        self.tools = tools_list if tools_list is not None else [CustomSearchTool()]
        
        self.chain_manager = ChainManager(
            settings=self.settings,
            model_type=model_type,
            tools_list=self.tools,
            custom_bot_personality_str=custom_bot_personality_str
        )
        
        self.input_queue = Queue(maxsize=6)
        self._memory: AbstractChatbotMemory = self.get_memory(memory_type=memory_type, parameters=memory_kwargs)
        if cache == CacheTypes.GPTCache and (model_type or ModelTypes[self.settings.model_type.upper()]) != ModelTypes.OPENAI:
            self.logger.warning("GPTCache solo es compatible con modelos OpenAI. Desactivando caché.")
            cache = None
        self._cache = ChatbotCache.create(cache_type=cache)
        self.anonymizer = BotAnonymizer(settings=self.settings)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_executor: Optional[AgentExecutor] = None
        self.start_agent()

    @property
    def memory(self) -> AbstractChatbotMemory:
        return self._memory

    def start_agent(self):
        agent_runnable_core: Runnable = self.chain_manager.runnable_chain

        history_loader = RunnableMap({
            "input": itemgetter("input"),
            "agent_scratchpad": itemgetter("intermediate_steps") | RunnableLambda(format_log_to_str),
            "history": RunnableLambda(
                lambda x: self._format_history_to_string(
                    self.memory.load_history(x["conversation_id"])
                )
            )
        }).with_config(run_name="LoadHistoryAndPrepareAgentInput")

        agent_chain_with_history = history_loader | agent_runnable_core

        if self.settings.enable_anonymizer:
            anonymizer_runnable = self.anonymizer.get_runnable_anonymizer().with_config(run_name="AnonymizeSentence")
            de_anonymizer = RunnableLambda(self.anonymizer.anonymizer.deanonymize).with_config(run_name="DeAnonymizeResponse")
            self.logger.warning("La integración del anonimizador con AgentExecutor necesita revisión. Omitiéndolo por ahora del ensamblaje del agente.")
            runnable_for_agent = agent_chain_with_history
        else:
            runnable_for_agent = agent_chain_with_history

        self.agent_executor = AgentExecutor(
            agent=runnable_for_agent | ReActSingleInputOutputParser(),
            tools=self.tools,
            verbose=True,
            max_iterations=self.settings.agent_max_iterations if hasattr(self.settings, 'agent_max_iterations') else 3,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )

    def get_memory(
            self,
            parameters: dict = None,
            memory_type: Optional[MemoryTypes] = None
    ) -> AbstractChatbotMemory:
        parameters = parameters or {}
        if memory_type is None:
            try:
                memory_type_str = self.settings.memory_type.upper()
                memory_type = MemoryTypes[memory_type_str]
                self.logger.info(f"Usando tipo de memoria de settings: {memory_type_str}")
            except (AttributeError, KeyError):
                self.logger.warning("memory_type no en settings o inválido. Defaulting a BASE_MEMORY.")
                memory_type = MemoryTypes.BASE_MEMORY
        if memory_type not in MEM_TO_CLASS:
            raise ValueError(
                f"Got unknown memory type: {memory_type}. "
                f"Valid types are: {MEM_TO_CLASS.keys()}."
            )
        memory_class = MEM_TO_CLASS[memory_type]
        
        mem_kwargs = parameters.copy()
        if 'k' not in mem_kwargs and hasattr(self.settings, 'memory_window_size'):
            mem_kwargs['k'] = self.settings.memory_window_size
        
        return memory_class(settings=self.settings, **mem_kwargs)

    @property
    def streaming_model_kwargs(self):
        base_kwargs = self.chain_manager._base_model.dict()
        
        valid_llm_kwargs = ["model_name", "temperature", "max_tokens", "top_p", "top_k", "model_kwargs", "max_output_tokens"]
        
        filtered_base_kwargs = {k: v for k, v in base_kwargs.items() if k in valid_llm_kwargs}
        if "model_kwargs" in filtered_base_kwargs and isinstance(filtered_base_kwargs["model_kwargs"], dict):
            filtered_base_kwargs.update(filtered_base_kwargs.pop("model_kwargs"))

        llm_provider = getattr(self.chain_manager._base_model, "_llm_type", "").lower()
        if "vertex" in llm_provider and "max_tokens" in filtered_base_kwargs:
            filtered_base_kwargs["max_output_tokens"] = filtered_base_kwargs.pop("max_tokens")
            
        return {
            **filtered_base_kwargs, 
            "streaming": True,
        }

    def reset_history(self, conversation_id: str):
        self.memory.clear(conversation_id=conversation_id)

    def add_message_to_memory(
            self,
            human_message: Union[Message, str],
            ai_message: Union[Message, str],
            conversation_id: str
    ):
        if isinstance(human_message, str):
            human_message = Message(message=human_message, role=self.settings.human_prefix)
        if isinstance(ai_message, str):
            ai_message = Message(message=ai_message, role=self.settings.ai_prefix)

        turn = MessageTurn(
            human_message=human_message,
            ai_message=ai_message,
            conversation_id=conversation_id
        )
        self.memory.add_message(turn)

    async def __call__(self, message: Message, conversation_id: str) -> Message:
        if not self.agent_executor:
            self.logger.error("AgentExecutor no inicializado. Llamar a start_agent() primero.")
            return Message(message="Error: Agente no inicializado.", role=self.settings.ai_prefix)
        try:
            input_msg_content = message.message if hasattr(message, 'message') else str(message)
            
            if self.settings.enable_anonymizer:
                anonymized_data = self.anonymizer.anonymize_func({"input": input_msg_content})
                input_msg_content = anonymized_data.get("input", input_msg_content)

            agent_input = {"input": input_msg_content, "conversation_id": conversation_id}
            
            response_data = await self.agent_executor.ainvoke(agent_input)
            output = response_data.get('output', "No se pudo obtener respuesta del agente.")
            
            if self.settings.enable_anonymizer:
                output = self.anonymizer.anonymizer.deanonymize(output)

            return Message(message=str(output), role=self.settings.ai_prefix)
        except Exception as e:
            self.logger.error(f"Error durante la ejecución del agente: {e}", exc_info=True)
            return Message(message=f"Lo siento, ocurrió un error al procesar tu solicitud: {e}", role=self.settings.ai_prefix)
        finally:
            pass # wait_for_all_tracers() # COMMENTED OUT

    def predict(self, sentence: str, conversation_id: str = None) -> Message:
        message = Message(message=sentence, role=self.settings.human_prefix)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.logger.warning("predict() llamado en un loop de asyncio ya activo. Esto puede no funcionar como se espera.")
                raise NotImplementedError("Llamar a predict() desde un loop de asyncio activo no está soportado directamente. Use el método async __call__.")
            else:
                output = asyncio.run(self(message, conversation_id=conversation_id))
        except RuntimeError as e:
            self.logger.error(f"Error en asyncio.run dentro de predict(): {e}. Considere llamar al bot de forma asíncrona.")
            output = Message(message=f"Error de concurrencia al procesar: {e}", role=self.settings.ai_prefix)
        
        return output

    def call(self, input_data: dict) -> Message:
        sentence = input_data.get("input") or input_data.get("sentence")
        if not sentence:
            raise ValueError("El diccionario de entrada debe contener la clave 'input' o 'sentence'.")
        conversation_id = input_data.get("conversation_id")
        return self.predict(sentence=sentence, conversation_id=conversation_id)

    def _format_history_to_string(self, history_messages: List[Any]) -> str:
        """Formatea una lista de mensajes de historial en una sola cadena."""
        if not history_messages:
            return "No hay historial de conversación previo."
        
        formatted_history = []
        # Determinar el nombre del AI basado en la plantilla de prompt actual para consistencia
        # Esto es una heurística; una mejor manera sería tener un campo "bot_display_name" en settings.
        ai_display_name = "Asesor Virtual Académico" # Default al nuevo nombre
        if self.settings.main_prompt_name == "SHELDON_REACT_PROMPT":
            ai_display_name = "Sheldon"
            
        for msg in history_messages:
            # Para el rol, verificamos el tipo de mensaje LangChain o el campo 'role' si es nuestro BotMessage
            is_human = False
            if hasattr(msg, 'type') and isinstance(msg.type, str):
                 is_human = msg.type.lower() == 'human'
            elif hasattr(msg, 'role') and isinstance(msg.role, str):
                 is_human = msg.role.lower() == 'user' # settings.human_prefix ahora es 'user'

            is_ai = False
            if hasattr(msg, 'type') and isinstance(msg.type, str):
                is_ai = msg.type.lower() == 'ai' or msg.type.lower() == 'aimessage' or msg.type.lower() == 'aimessagechunk'
            elif hasattr(msg, 'role') and isinstance(msg.role, str):
                is_ai = msg.role.lower() == 'assistant' # settings.ai_prefix ahora es 'assistant'

            role_display = "Humano" if is_human else \
                           ai_display_name if is_ai else \
                           "Desconocido"
            
            content = getattr(msg, 'content', getattr(msg, 'message', ''))
            formatted_history.append(f"{role_display}: {content}")
        
        return "\n".join(formatted_history)
