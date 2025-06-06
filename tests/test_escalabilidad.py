"""
Script para evaluar la escalabilidad del chatbot RAG.
Simula usuarios concurrentes, mide latencia en consultas a la base de datos,
monitorea recursos y realiza pruebas de estrés.
"""
import os
import sys
import time
import json
import psutil
import asyncio
import statistics
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import concurrent.futures
import requests
from typing import Dict, List, Any, Tuple

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_FILE = PROJECT_ROOT / "scalability_report.txt"
CHARTS_DIR = PROJECT_ROOT / "reports" / "charts"

# Asegurar que el directorio de gráficos existe
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de la prueba
API_URL = "http://localhost:8000"  # Ajustar según la configuración
MAX_CONCURRENT_USERS = [1, 5, 10, 20, 50]  # Niveles de concurrencia a probar
REQUESTS_PER_USER = 5  # Número de solicitudes por usuario
REQUEST_TIMEOUT = 30  # Tiempo máximo de espera por solicitud (segundos)

# Consultas de ejemplo para las pruebas
SAMPLE_QUERIES = [
    "¿Qué es un sistema RAG?",
    "Explica cómo funciona la recuperación de documentos",
    "¿Cuáles son las ventajas de usar embeddings?",
    "Dame un ejemplo de prompt engineering",
    "¿Cómo se implementa la memoria en un chatbot?"
]

def monitorear_recursos(duracion: int = 60, intervalo: float = 1.0) -> Dict[str, List[float]]:
    """
    Monitorea el uso de CPU y memoria durante un período específico.
    
    Args:
        duracion: Duración del monitoreo en segundos
        intervalo: Intervalo entre mediciones en segundos
    
    Returns:
        Diccionario con listas de mediciones de CPU y memoria
    """
    print(f"Monitoreando recursos durante {duracion} segundos...")
    
    cpu_uso = []
    memoria_uso = []
    tiempo_transcurrido = []
    
    inicio = time.time()
    fin = inicio + duracion
    
    while time.time() < fin:
        cpu_uso.append(psutil.cpu_percent(interval=None))
        memoria_uso.append(psutil.virtual_memory().percent)
        tiempo_transcurrido.append(time.time() - inicio)
        time.sleep(intervalo)
    
    return {
        "cpu": cpu_uso,
        "memoria": memoria_uso,
        "tiempo": tiempo_transcurrido
    }

async def realizar_solicitud(session, query: str) -> Tuple[float, Dict[str, Any]]:
    """
    Realiza una solicitud al API del chatbot y mide el tiempo de respuesta.
    
    Args:
        session: Sesión HTTP para realizar la solicitud
        query: Consulta a enviar al chatbot
    
    Returns:
        Tupla con el tiempo de respuesta y la respuesta del servidor
    """
    payload = {"query": query, "session_id": "test_session"}
    
    inicio = time.time()
    try:
        async with session.post(f"{API_URL}/chat", json=payload, timeout=REQUEST_TIMEOUT) as response:
            respuesta = await response.json()
            tiempo_respuesta = time.time() - inicio
            return tiempo_respuesta, respuesta
    except Exception as e:
        print(f"Error en solicitud: {e}")
        return time.time() - inicio, {"error": str(e)}

async def simular_usuario(user_id: int, num_requests: int) -> List[float]:
    """
    Simula un usuario realizando múltiples solicitudes al chatbot.
    
    Args:
        user_id: Identificador del usuario simulado
        num_requests: Número de solicitudes a realizar
    
    Returns:
        Lista con los tiempos de respuesta de cada solicitud
    """
    import aiohttp
    
    tiempos_respuesta = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            query = SAMPLE_QUERIES[i % len(SAMPLE_QUERIES)]
            tiempo, _ = await realizar_solicitud(session, query)
            tiempos_respuesta.append(tiempo)
            # Pequeña pausa entre solicitudes del mismo usuario
            await asyncio.sleep(0.5)
    
    return tiempos_respuesta

async def prueba_concurrencia(num_usuarios: int) -> Dict[str, Any]:
    """
    Ejecuta una prueba con un número específico de usuarios concurrentes.
    
    Args:
        num_usuarios: Número de usuarios concurrentes a simular
    
    Returns:
        Resultados de la prueba incluyendo estadísticas de tiempo de respuesta
    """
    print(f"Iniciando prueba con {num_usuarios} usuarios concurrentes...")
    
    # Iniciar monitoreo de recursos en un hilo separado
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_recursos = executor.submit(monitorear_recursos, 
                                         duracion=num_usuarios * REQUESTS_PER_USER * 2)  # Estimación de duración
        
        # Ejecutar simulaciones de usuarios
        tareas = [simular_usuario(i, REQUESTS_PER_USER) for i in range(num_usuarios)]
        resultados = await asyncio.gather(*tareas)
        
        # Recopilar resultados
        todos_tiempos = [tiempo for usuario_tiempos in resultados for tiempo in usuario_tiempos]
        
        # Esperar a que termine el monitoreo de recursos
        datos_recursos = future_recursos.result()
    
    # Calcular estadísticas
    estadisticas = {
        "usuarios": num_usuarios,
        "total_solicitudes": num_usuarios * REQUESTS_PER_USER,
        "tiempo_min": min(todos_tiempos),
        "tiempo_max": max(todos_tiempos),
        "tiempo_promedio": statistics.mean(todos_tiempos),
        "tiempo_mediana": statistics.median(todos_tiempos),
        "desviacion_estandar": statistics.stdev(todos_tiempos) if len(todos_tiempos) > 1 else 0,
        "percentil_90": sorted(todos_tiempos)[int(len(todos_tiempos) * 0.9)],
        "recursos": {
            "cpu_promedio": statistics.mean(datos_recursos["cpu"]),
            "memoria_promedio": statistics.mean(datos_recursos["memoria"]),
            "cpu_max": max(datos_recursos["cpu"]),
            "memoria_max": max(datos_recursos["memoria"])
        }
    }
    
    return {
        "estadisticas": estadisticas,
        "tiempos_respuesta": todos_tiempos,
        "datos_recursos": datos_recursos
    }

def generar_graficos(resultados: Dict[int, Dict[str, Any]]):
    """
    Genera gráficos a partir de los resultados de las pruebas.
    
    Args:
        resultados: Diccionario con resultados por nivel de concurrencia
    """
    # Preparar datos para gráficos
    usuarios = list(resultados.keys())
    tiempos_promedio = [r["estadisticas"]["tiempo_promedio"] for r in resultados.values()]
    tiempos_p90 = [r["estadisticas"]["percentil_90"] for r in resultados.values()]
    cpu_promedio = [r["estadisticas"]["recursos"]["cpu_promedio"] for r in resultados.values()]
    memoria_promedio = [r["estadisticas"]["recursos"]["memoria_promedio"] for r in resultados.values()]
    
    # Gráfico de tiempos de respuesta
    plt.figure(figsize=(10, 6))
    plt.plot(usuarios, tiempos_promedio, 'o-', label='Tiempo Promedio')
    plt.plot(usuarios, tiempos_p90, 's-', label='Percentil 90')
    plt.xlabel('Usuarios Concurrentes')
    plt.ylabel('Tiempo de Respuesta (s)')
    plt.title('Escalabilidad: Tiempos de Respuesta vs Concurrencia')
    plt.legend()
    plt.grid(True)
    plt.savefig(CHARTS_DIR / "tiempos_respuesta.png")
    
    # Gráfico de uso de recursos
    plt.figure(figsize=(10, 6))
    plt.plot(usuarios, cpu_promedio, 'o-', label='CPU Promedio (%)')
    plt.plot(usuarios, memoria_promedio, 's-', label='Memoria Promedio (%)')
    plt.xlabel('Usuarios Concurrentes')
    plt.ylabel('Uso de Recursos (%)')
    plt.title('Escalabilidad: Uso de Recursos vs Concurrencia')
    plt.legend()
    plt.grid(True)
    plt.savefig(CHARTS_DIR / "uso_recursos.png")
    
    # Para el último nivel de concurrencia, graficar la serie temporal
    ultimo_nivel = max(usuarios)
    datos_recursos = resultados[ultimo_nivel]["datos_recursos"]
    
    plt.figure(figsize=(12, 6))
    plt.plot(datos_recursos["tiempo"], datos_recursos["cpu"], label='CPU (%)')
    plt.plot(datos_recursos["tiempo"], datos_recursos["memoria"], label='Memoria (%)')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Uso de Recursos (%)')
    plt.title(f'Uso de Recursos durante Prueba con {ultimo_nivel} Usuarios')
    plt.legend()
    plt.grid(True)
    plt.savefig(CHARTS_DIR / "recursos_tiempo.png")

def generar_informe(resultados: Dict[int, Dict[str, Any]]):
    """
    Genera un informe detallado con los resultados de las pruebas.
    
    Args:
        resultados: Diccionario con resultados por nivel de concurrencia
    """
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"INFORME DE ESCALABILIDAD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Resumen ejecutivo
        f.write("RESUMEN EJECUTIVO\n")
        f.write("-" * 80 + "\n")
        
        # Tabla de resultados
        f.write("\nResultados por nivel de concurrencia:\n\n")
        f.write("| Usuarios | Solicitudes | Tiempo Promedio (s) | Percentil 90 (s) | CPU Promedio (%) | Memoria Promedio (%) |\n")
        f.write("|----------|-------------|---------------------|------------------|------------------|----------------------|\n")
        
        for usuarios, datos in sorted(resultados.items()):
            stats = datos["estadisticas"]
            f.write(f"| {usuarios:8d} | {stats['total_solicitudes']:11d} | {stats['tiempo_promedio']:19.3f} | {stats['percentil_90']:16.3f} | {stats['recursos']['cpu_promedio']:16.1f} | {stats['recursos']['memoria_promedio']:20.1f} |\n")
        
        # Punto de saturación
        tiempos = [r["estadisticas"]["tiempo_promedio"] for r in resultados.values()]
        usuarios = list(resultados.keys())
        
        # Detectar punto de saturación (cuando el tiempo aumenta más del 100% respecto al anterior)
        punto_saturacion = None
        for i in range(1, len(tiempos)):
            if tiempos[i] > tiempos[i-1] * 2:
                punto_saturacion = usuarios[i]
                break
        
        if punto_saturacion:
            f.write(f"\nPunto de saturación detectado: aproximadamente {punto_saturacion} usuarios concurrentes\n")
        else:
            f.write("\nNo se detectó un punto claro de saturación en los niveles probados\n")
        
        # Detalles por nivel de concurrencia
        for usuarios, datos in sorted(resultados.items()):
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"DETALLES PARA {usuarios} USUARIOS CONCURRENTES\n")
            f.write("=" * 80 + "\n\n")
            
            stats = datos["estadisticas"]
            
            f.write(f"Total de solicitudes: {stats['total_solicitudes']}\n")
            f.write(f"Tiempo mínimo de respuesta: {stats['tiempo_min']:.3f} s\n")
            f.write(f"Tiempo máximo de respuesta: {stats['tiempo_max']:.3f} s\n")
            f.write(f"Tiempo promedio de respuesta: {stats['tiempo_promedio']:.3f} s\n")
            f.write(f"Mediana de tiempo de respuesta: {stats['tiempo_mediana']:.3f} s\n")
            f.write(f"Desviación estándar: {stats['desviacion_estandar']:.3f} s\n")
            f.write(f"Percentil 90: {stats['percentil_90']:.3f} s\n\n")
            
            f.write("Uso de recursos:\n")
            f.write(f"  CPU promedio: {stats['recursos']['cpu_promedio']:.1f}%\n")
            f.write(f"  CPU máximo: {stats['recursos']['cpu_max']:.1f}%\n")
            f.write(f"  Memoria promedio: {stats['recursos']['memoria_promedio']:.1f}%\n")
            f.write(f"  Memoria máxima: {stats['recursos']['memoria_max']:.1f}%\n")
        
        # Recomendaciones
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMENDACIONES\n")
        f.write("=" * 80 + "\n\n")
        
        # Determinar recomendaciones basadas en los resultados
        ultimo_nivel = max(usuarios)
        ultimo_tiempo = resultados[ultimo_nivel]["estadisticas"]["tiempo_promedio"]
        ultimo_cpu = resultados[ultimo_nivel]["estadisticas"]["recursos"]["cpu_promedio"]
        ultimo_memoria = resultados[ultimo_nivel]["estadisticas"]["recursos"]["memoria_promedio"]
        
        if ultimo_tiempo > 2.0:
            f.write("- Optimizar tiempos de respuesta, actualmente son demasiado altos bajo carga\n")
        
        if ultimo_cpu > 80:
            f.write("- El uso de CPU es elevado, considerar escalar horizontalmente o optimizar algoritmos\n")
        
        if ultimo_memoria > 80:
            f.write("- El uso de memoria es elevado, revisar posibles fugas de memoria o optimizar el uso de recursos\n")
        
        if punto_saturacion and punto_saturacion < 20:
            f.write(f"- El sistema se satura con relativamente pocos usuarios ({punto_saturacion}), considerar implementar caching o mejorar la eficiencia\n")
        
        f.write("\nNota: Los gráficos de las pruebas se encuentran en el directorio 'reports/charts/'\n")

async def main():
    """Función principal que ejecuta todas las pruebas de escalabilidad."""
    print(f"Iniciando pruebas de escalabilidad para el chatbot RAG...")
    
    resultados = {}
    
    # Ejecutar pruebas para cada nivel de concurrencia
    for num_usuarios in MAX_CONCURRENT_USERS:
        resultados[num_usuarios] = await prueba_concurrencia(num_usuarios)
        print(f"Prueba con {num_usuarios} usuarios completada.")
    
    # Generar gráficos
    generar_graficos(resultados)
    
    # Generar informe
    generar_informe(resultados)
    
    print(f"Pruebas de escalabilidad completadas. Informe generado en {REPORT_FILE}")
    print(f"Gráficos generados en {CHARTS_DIR}")

if __name__ == "__main__":
    # Verificar si el servidor está en ejecución
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code != 200:
            print(f"Error: El servidor no está respondiendo correctamente. Código: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: No se puede conectar al servidor en {API_URL}. Asegúrate de que esté en ejecución.")
        print(f"Detalles: {e}")
        sys.exit(1)
    
    # Ejecutar pruebas de escalabilidad
    asyncio.run(main())