from enum import Enum
from typing import Optional, Any, Dict

from langchain_community.cache import InMemoryCache, RedisCache
from langchain.globals import set_llm_cache
import hashlib
import redis
import json
import logging
from datetime import datetime, timedelta

from ..config import Settings, get_settings

try:
    from langchain_community.cache import GPTCache
    from gptcache import Cache as GPTCacheType
    from gptcache.adapter.api import init_similar_cache
    GPTCACHE_AVAILABLE = True
except ImportError:
    GPTCACHE_AVAILABLE = False
    GPTCacheType = Any

CACHE_TYPE: Dict[str, Any] = {
    "in_memory": InMemoryCache,
}

if GPTCACHE_AVAILABLE:
    CACHE_TYPE["GPTCache"] = GPTCache


class CacheTypes(str, Enum):
    GPTCache = "gptcache"
    InMemoryCache = "inmemorycache"
    RedisCache = "rediscache"


def get_hashed_name(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def init_gptcache(cache_obj: GPTCacheType, llm: str) -> None:
    if not GPTCACHE_AVAILABLE:
        raise ImportError("GPTCache is not available. Please install gptcache package.")
    hashed_llm = get_hashed_name(llm)
    init_similar_cache(cache_obj=cache_obj, data_dir=f"similar_cache_{hashed_llm}")


class ChatbotCache:
    def __init__(self, settings: Settings, cache_type: Optional[CacheTypes] = None, **kwargs):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache_type = cache_type or (CacheTypes[self.settings.cache_type] if self.settings.cache_type else None)
        self.cache_kwargs = kwargs
        self._init_cache()

    def _init_cache(self):
        if self.cache_type is None:
            self.logger.info("No cache type specified. LLM caching will be disabled.")
            set_llm_cache(None)
            return

        self.logger.info(f"Initializing LLM cache of type: {self.cache_type.value}")
        try:
            if self.cache_type == CacheTypes.GPTCache:
                # GPTCache specific initialization
                def pre_embedding_function(data, **_):
                    if isinstance(data, list) and len(data) > 0:
                        data_str = str(data[0])
                    else:
                        data_str = str(data)
                    return hashlib.sha256(data_str.encode()).hexdigest()

                cache_obj = GPTCache(pre_embedding_function)
            elif self.cache_type == CacheTypes.InMemoryCache:
                cache_obj = InMemoryCache()
            elif self.cache_type == CacheTypes.RedisCache:
                if not self.settings.redis_url:
                    self.logger.warning("RedisCache selected but REDIS_URL is not configured. Falling back to InMemoryCache.")
                    cache_obj = InMemoryCache()
                else:
                    try:
                        # Configurar Redis con timeout y reintentos
                        redis_client = redis.from_url(
                            self.settings.redis_url.get_secret_value(),
                            socket_timeout=2,  # 2 segundos de timeout
                            socket_connect_timeout=2,
                            retry_on_timeout=True,
                            health_check_interval=30
                        )
                        # Verificar conexión
                        redis_client.ping()
                        cache_obj = RedisCache(redis_client, **self.cache_kwargs)
                        self.logger.info(f"RedisCache initialized with TTL: {self.cache_kwargs.get('ttl')}")
                    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                        self.logger.warning(f"Failed to connect to Redis: {e}. Falling back to InMemoryCache.")
                        cache_obj = InMemoryCache()
                    except Exception as e:
                        self.logger.error(f"Unexpected error with Redis: {e}. Falling back to InMemoryCache.")
                        cache_obj = InMemoryCache()
            else:
                self.logger.warning(f"Unsupported cache type: {self.cache_type}. Falling back to InMemoryCache.")
                cache_obj = InMemoryCache()
            
            set_llm_cache(cache_obj)
            self.logger.info(f"Successfully set LLM cache to: {self.cache_type.value}")

        except ImportError as e:
            self.logger.error(f"Failed to import a caching library ({e}). Falling back to InMemoryCache.")
            set_llm_cache(InMemoryCache())
        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {e}. Falling back to InMemoryCache.")
            set_llm_cache(InMemoryCache())

    @staticmethod
    def create(cache_type: Optional[CacheTypes] = None, settings: Optional[Settings] = None, **kwargs) -> 'ChatbotCache':
        effective_settings = settings if settings is not None else get_settings()
        return ChatbotCache(settings=effective_settings, cache_type=cache_type, **kwargs)

    def get_cache_instance(self) -> Optional[Any]: # Reemplazar Any con el tipo base de Langchain Cache si es conocido
        # This method might be redundant if set_llm_cache is the primary way of interaction
        # but can be useful for direct cache operations if needed.
        if self.cache_type == CacheTypes.GPTCache:
            # Return instance or relevant part of GPTCache
            pass
        elif self.cache_type == CacheTypes.InMemoryCache:
            # Return instance of InMemoryCache
            pass
        elif self.cache_type == CacheTypes.RedisCache:
            # Return instance of RedisCache
            pass
        return None # Placeholder

    def clear_cache(self):
        # This would require specific implementations for each cache type
        # For global langchain cache, there isn't a single clear_cache() method
        # on set_llm_cache'd object directly in all cases.
        # We might need to re-initialize to clear.
        self.logger.info(f"Attempting to clear cache for type: {self.cache_type}")
        self._init_cache() # Re-initializing might be the simplest way to clear/reset
        self.logger.info(f"Cache re-initialized (effectively cleared).")
