"""Script de prueba de carga para el sistema de caché."""

import os
import sys
import logging
import time
import asyncio
import platform
import statistics
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json
import random
from concurrent.futures import ThreadPoolExecutor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from backend.core.bot import Bot
from backend.config import Settings
from backend.utils.chain_cache import CacheTypes
from backend.memory import MemoryTypes

class LoadTestResults:
    """Clase para almacenar y analizar resultados de las pruebas de carga."""
    
    def __init__(self, cache_type: str):
        self.cache_type = cache_type
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.hits: int = 0
        self.misses: int = 0
        self.start_time = time.time()
        self.end_time = None
    
    def add_response_time(self, response_time: float):
        """Añade un tiempo de respuesta a las estadísticas."""
        self.response_times.append(response_time)
    
    def add_error(self, error: str):
        """Registra un error ocurrido durante la prueba."""
        self.errors.append(error)
    
    def update_cache_metrics(self, hits: int, misses: int):
        """Actualiza las métricas de caché."""
        self.hits = hits
        self.misses = misses
    
    def finalize(self):
        """Finaliza la prueba y calcula estadísticas finales."""
        self.end_time = time.time()
    
    @property
    def total_requests(self) -> int:
        """Retorna el número total de peticiones."""
        return len(self.response_times)
    
    @property
    def error_rate(self) -> float:
        """Calcula la tasa de error."""
        if self.total_requests == 0:
            return 0.0
        return (len(self.errors) / self.total_requests) * 100
    
    @property
    def hit_ratio(self) -> float:
        """Calcula el ratio de hits del caché."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100
    
    @property
    def avg_response_time(self) -> float:
        """Calcula el tiempo de respuesta promedio."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    @property
    def std_dev_response_time(self) -> float:
        """Calcula la desviación estándar de los tiempos de respuesta."""
        if len(self.response_times) < 2:
            return 0.0
        return statistics.stdev(self.response_times)
    
    @property
    def total_time(self) -> float:
        """Retorna el tiempo total de la prueba."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte los resultados a un diccionario."""
        return {
            "cache_type": self.cache_type,
            "total_requests": self.total_requests,
            "total_time": self.total_time,
            "avg_response_time": self.avg_response_time,
            "std_dev_response_time": self.std_dev_response_time,
            "error_rate": self.error_rate,
            "hit_ratio": self.hit_ratio,
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors
        }
    
    def save_to_file(self, filename: str):
        """Guarda los resultados en un archivo JSON."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

class LoadTest:
    """Clase principal para ejecutar pruebas de carga."""
    
    def __init__(self, num_users: int = 50, requests_per_user: int = 10):
        self.num_users = num_users
        self.requests_per_user = requests_per_user
        self.results: Dict[str, LoadTestResults] = {}
        self.questions = [
            "¿Cuál es la capital de Francia?",
            "¿Quién escribió Don Quijote?",
            "¿Cuál es el planeta más grande del sistema solar?",
            "¿En qué año comenzó la Primera Guerra Mundial?",
            "¿Cuál es el elemento químico con símbolo 'O'?",
            "¿Quién pintó la Mona Lisa?",
            "¿Cuál es el río más largo del mundo?",
            "¿En qué continente está Egipto?",
            "¿Cuál es el animal más rápido del mundo?",
            "¿Quién fue el primer presidente de Estados Unidos?"
        ]
    
    async def simulate_user(self, user_id: int, cache_type: CacheTypes, settings: Settings):
        """Simula un usuario realizando peticiones."""
        bot = Bot(
            settings=settings,
            cache=cache_type,
            memory_type=MemoryTypes.BASE_MEMORY
        )
        
        for i in range(self.requests_per_user):
            # Seleccionar una pregunta aleatoria
            question = random.choice(self.questions)
            
            try:
                start_time = time.time()
                await bot.predict(question)
                response_time = time.time() - start_time
                
                # Actualizar métricas
                self.results[cache_type.value].add_response_time(response_time)
                metrics = bot.cache.get_metrics()
                self.results[cache_type.value].update_cache_metrics(
                    metrics['hits'],
                    metrics['misses']
                )
                
            except Exception as e:
                self.results[cache_type.value].add_error(str(e))
                logger.error(f"Error en usuario {user_id}, petición {i}: {e}")
    
    async def run_test(self, cache_type: CacheTypes):
        """Ejecuta la prueba de carga para un tipo de caché."""
        logger.info(f"\nIniciando prueba de carga para {cache_type.value}")
        logger.info(f"Usuarios concurrentes: {self.num_users}")
        logger.info(f"Peticiones por usuario: {self.requests_per_user}")
        
        # Inicializar resultados
        self.results[cache_type.value] = LoadTestResults(cache_type.value)
        
        # Configuración para la prueba
        settings = Settings(
            enable_cache=True,
            redis_url="redis://localhost:6379" if cache_type == CacheTypes.RedisCache else None,
            cache_ttl=3600,
            memory_type="base-memory"
        )
        
        # Crear tareas para cada usuario
        tasks = [
            self.simulate_user(i, cache_type, settings)
            for i in range(self.num_users)
        ]
        
        # Ejecutar todas las tareas concurrentemente
        await asyncio.gather(*tasks)
        
        # Finalizar y guardar resultados
        self.results[cache_type.value].finalize()
        self._print_results(cache_type.value)
        
        # Guardar resultados en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{cache_type.value}_{timestamp}.json"
        self.results[cache_type.value].save_to_file(filename)
        logger.info(f"Resultados guardados en {filename}")
    
    def _print_results(self, cache_type: str):
        """Imprime los resultados de la prueba."""
        results = self.results[cache_type]
        logger.info(f"\nResultados para {cache_type}:")
        logger.info("="*50)
        logger.info(f"Total de peticiones: {results.total_requests}")
        logger.info(f"Tiempo total: {results.total_time:.2f}s")
        logger.info(f"Tiempo promedio de respuesta: {results.avg_response_time:.3f}s")
        logger.info(f"Desviación estándar: {results.std_dev_response_time:.3f}s")
        logger.info(f"Tasa de error: {results.error_rate:.1f}%")
        logger.info(f"Hit ratio: {results.hit_ratio:.1f}%")
        logger.info(f"Hits: {results.hits}")
        logger.info(f"Misses: {results.misses}")
        if results.errors:
            logger.info(f"Errores encontrados: {len(results.errors)}")
            for error in results.errors[:5]:  # Mostrar solo los primeros 5 errores
                logger.info(f"  - {error}")

async def main():
    """Función principal que ejecuta las pruebas de carga."""
    # Configurar el event loop para Windows si es necesario
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Crear y ejecutar pruebas de carga
    load_test = LoadTest(num_users=50, requests_per_user=10)
    
    # Probar InMemoryCache
    await load_test.run_test(CacheTypes.InMemoryCache)
    
    # Probar RedisCache
    await load_test.run_test(CacheTypes.RedisCache)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nPruebas interrumpidas por el usuario")
    except Exception as e:
        logger.error(f"Error durante las pruebas: {e}") 