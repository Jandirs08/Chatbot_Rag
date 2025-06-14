"""Pruebas del sistema de caché."""
import os
import sys
import logging
import time
import asyncio
import platform
from pathlib import Path
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from backend.core.bot import Bot
from backend.config import Settings
from backend.utils.chain_cache import CacheTypes
from backend.memory import MemoryTypes

# Diccionario para almacenar resultados
test_results: Dict[str, Dict[str, Any]] = {
    "inmemorycache": {},
    "rediscache": {}
}

async def test_cache_performance(cache_type: CacheTypes, settings: Settings):
    """Prueba el rendimiento del caché."""
    logger.info(f"\nProbando rendimiento con {cache_type.value}")
    
    # Crear instancia del bot con el tipo de caché especificado
    bot = Bot(
        settings=settings,
        cache=cache_type,
        memory_type=MemoryTypes.BASE_MEMORY
    )
    
    # Primera llamada (sin caché)
    start_time = time.time()
    await bot.predict("¿Cuál es la capital de Francia?")
    first_call_time = time.time() - start_time
    logger.info(f"Primera llamada ({cache_type.value})...")
    logger.info(f"Tiempo de respuesta: {first_call_time:.3f}s")
    
    # Segunda llamada (con caché)
    start_time = time.time()
    await bot.predict("¿Cuál es la capital de Francia?")
    second_call_time = time.time() - start_time
    logger.info(f"Segunda llamada ({cache_type.value})...")
    logger.info(f"Tiempo de respuesta: {second_call_time:.3f}s")
    
    # Calcular reducción de tiempo
    if first_call_time > 0:
        reduction = ((first_call_time - second_call_time) / first_call_time) * 100
        logger.info(f"✓ ¡{cache_type.value} funcionando! Reducción de tiempo: {reduction:.1f}%")
        
        # Mostrar métricas
        metrics = bot.cache.get_metrics()
        logger.info("\nMétricas de Caché:")
        logger.info(f"  Hits: {metrics['hits']}")
        logger.info(f"  Misses: {metrics['misses']}")
        logger.info(f"  Hit Ratio: {metrics['hit_ratio']:.1f}%")
        logger.info(f"  Tiempo Promedio: {metrics['avg_response_time']:.3f}s")
        
        # Guardar resultados
        test_results[cache_type.value]["performance"] = {
            "first_call_time": first_call_time,
            "second_call_time": second_call_time,
            "reduction": reduction,
            "metrics": metrics
        }
        
        return reduction
    return 0

async def test_cache_clearance(settings: Settings, cache_type: CacheTypes):
    """Prueba la limpieza del caché."""
    try:
        # Crear instancia del bot con el tipo de caché especificado
        bot = Bot(
            settings=settings,
            cache=cache_type,
            memory_type=MemoryTypes.BASE_MEMORY
        )
        
        # Obtener métricas antes de limpiar
        metrics_before = bot.cache.get_metrics()
        
        # Limpiar caché usando la propiedad cache
        bot.cache.clear_cache()
        logger.info(f"✓ Limpieza de caché completada para {cache_type.value}")
        
        # Verificar que las métricas se reiniciaron
        metrics_after = bot.cache.get_metrics()
        logger.info("\nMétricas después de limpieza:")
        logger.info(f"  Hits: {metrics_after['hits']}")
        logger.info(f"  Misses: {metrics_after['misses']}")
        logger.info(f"  Hit Ratio: {metrics_after['hit_ratio']:.1f}%")
        
        # Guardar resultados
        test_results[cache_type.value]["clearance"] = {
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
            "success": metrics_after['hits'] == 0
        }
        
    except Exception as e:
        logger.error(f"✗ Error al limpiar caché: {e}")
        test_results[cache_type.value]["clearance"] = {
            "error": str(e),
            "success": False
        }

def print_summary():
    """Imprime un resumen detallado de las pruebas."""
    logger.info("\n" + "="*80)
    logger.info("RESUMEN FINAL DE PRUEBAS DE CACHÉ")
    logger.info("="*80)
    
    for cache_type, results in test_results.items():
        logger.info(f"\n{cache_type.upper()}:")
        logger.info("-"*40)
        
        # Resumen de rendimiento
        if "performance" in results:
            perf = results["performance"]
            logger.info("Rendimiento:")
            logger.info(f"  • Primera llamada: {perf['first_call_time']:.3f}s")
            logger.info(f"  • Segunda llamada: {perf['second_call_time']:.3f}s")
            logger.info(f"  • Reducción de tiempo: {perf['reduction']:.1f}%")
            logger.info(f"  • Hit Ratio: {perf['metrics']['hit_ratio']:.1f}%")
            logger.info(f"  • Tiempo promedio: {perf['metrics']['avg_response_time']:.3f}s")
        
        # Resumen de limpieza
        if "clearance" in results:
            clear = results["clearance"]
            if clear.get("success", False):
                logger.info("\nLimpieza:")
                logger.info("  • Estado: ✓ Exitosa")
                logger.info(f"  • Hits después de limpieza: {clear['metrics_after']['hits']}")
                logger.info(f"  • Misses después de limpieza: {clear['metrics_after']['misses']}")
            else:
                logger.info("\nLimpieza:")
                logger.info("  • Estado: ✗ Fallida")
                if "error" in clear:
                    logger.info(f"  • Error: {clear['error']}")
    
    logger.info("\n" + "="*80)
    logger.info("CONCLUSIONES:")
    logger.info("="*80)
    
    # Comparar rendimiento
    in_memory_perf = test_results["inmemorycache"]["performance"]
    redis_perf = test_results["rediscache"]["performance"]
    
    logger.info("\nComparación de Rendimiento:")
    logger.info(f"• InMemoryCache: {in_memory_perf['reduction']:.1f}% de reducción")
    logger.info(f"• RedisCache: {redis_perf['reduction']:.1f}% de reducción")
    
    # Determinar el mejor caché
    best_cache = "InMemoryCache" if in_memory_perf['reduction'] > redis_perf['reduction'] else "RedisCache"
    logger.info(f"\nMejor rendimiento: {best_cache}")
    
    # Verificar limpieza
    in_memory_clear = test_results["inmemorycache"]["clearance"]["success"]
    redis_clear = test_results["rediscache"]["clearance"]["success"]
    
    logger.info("\nEstado de Limpieza:")
    logger.info(f"• InMemoryCache: {'✓' if in_memory_clear else '✗'}")
    logger.info(f"• RedisCache: {'✓' if redis_clear else '✗'}")
    
    logger.info("\n" + "="*80)

async def run_cache_tests():
    """Ejecuta todas las pruebas de caché."""
    logger.info("\n=== Iniciando pruebas de caché ===\n")
    
    # Configuración para pruebas
    settings = Settings(
        enable_cache=True,
        redis_url=None,  # Forzar uso de InMemoryCache inicialmente
        cache_ttl=3600,
        memory_type="base-memory"  # Corregir el tipo de memoria
    )
    
    # 1. Probar InMemoryCache
    logger.info("1. Probando InMemoryCache...")
    await test_cache_performance(CacheTypes.InMemoryCache, settings)
    
    # 2. Probar RedisCache
    logger.info("\n2. Probando RedisCache...")
    settings.redis_url = "redis://localhost:6379"  # URL de ejemplo
    await test_cache_performance(CacheTypes.RedisCache, settings)
    
    # 3. Probar limpieza de caché para ambos tipos
    logger.info("\n3. Probando limpieza de caché...")
    await test_cache_clearance(settings, CacheTypes.InMemoryCache)
    await test_cache_clearance(settings, CacheTypes.RedisCache)
    
    # Imprimir resumen final
    print_summary()

def main():
    """Función principal que maneja el event loop."""
    if platform.system() == 'Windows':
        # Configurar el event loop para Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(run_cache_tests())
    except KeyboardInterrupt:
        logger.info("\nPruebas interrumpidas por el usuario")
    except Exception as e:
        logger.error(f"Error durante las pruebas: {e}")
    finally:
        # Asegurar que todas las tareas pendientes se completen
        pending = asyncio.all_tasks()
        if pending:
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*pending))

if __name__ == "__main__":
    main() 