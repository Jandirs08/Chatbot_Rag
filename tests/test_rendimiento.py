"""
Script para evaluar el rendimiento del chatbot RAG.
Mide tiempos de respuesta, uso de memoria y eficiencia de las consultas.
"""
import time
import psutil
import statistics
from pathlib import Path
from typing import Dict, List, Any

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_FILE = PROJECT_ROOT / "performance_report.txt"

def medir_tiempo_ejecucion(func):
    """Decorador para medir el tiempo de ejecución de una función."""
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        tiempo_ejecucion = time.time() - inicio
        return resultado, tiempo_ejecucion
    return wrapper

def medir_uso_memoria():
    """Mide el uso actual de memoria del proceso."""
    proceso = psutil.Process()
    return proceso.memory_info().rss / 1024 / 1024  # Convertir a MB

@medir_tiempo_ejecucion
def ejecutar_consulta(query: str) -> Dict[str, Any]:
    """
    Simula la ejecución de una consulta al chatbot.
    En una implementación real, esto se conectaría al API del chatbot.
    """
    # Simulación de procesamiento
    time.sleep(0.1)  # Simular tiempo de procesamiento
    return {"respuesta": f"Respuesta simulada para: {query}"}

def ejecutar_pruebas_rendimiento():
    """Ejecuta una serie de pruebas de rendimiento."""
    print("Iniciando pruebas de rendimiento...")
    
    # Lista de consultas de prueba
    consultas = [
        "¿Qué es un sistema RAG?",
        "Explica cómo funciona la recuperación de documentos",
        "¿Cuáles son las ventajas de usar embeddings?",
        "Dame un ejemplo de prompt engineering",
        "¿Cómo se implementa la memoria en un chatbot?"
    ]
    
    resultados = []
    memoria_inicial = medir_uso_memoria()
    
    for i, consulta in enumerate(consultas, 1):
        print(f"Ejecutando consulta {i}/{len(consultas)}: {consulta}")
        
        # Ejecutar consulta y medir tiempo
        respuesta, tiempo = ejecutar_consulta(consulta)
        
        # Medir memoria después de cada consulta
        memoria_actual = medir_uso_memoria()
        
        resultados.append({
            "consulta": consulta,
            "tiempo_respuesta": tiempo,
            "memoria_uso": memoria_actual - memoria_inicial
        })
    
    return resultados

def generar_informe(resultados: List[Dict[str, Any]]):
    """Genera un informe con los resultados de las pruebas."""
    tiempos = [r["tiempo_respuesta"] for r in resultados]
    memoria = [r["memoria_uso"] for r in resultados]
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("INFORME DE RENDIMIENTO\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("RESUMEN ESTADÍSTICO\n")
        f.write("-" * 80 + "\n")
        f.write(f"Tiempo promedio de respuesta: {statistics.mean(tiempos):.3f} segundos\n")
        f.write(f"Tiempo mínimo de respuesta: {min(tiempos):.3f} segundos\n")
        f.write(f"Tiempo máximo de respuesta: {max(tiempos):.3f} segundos\n")
        f.write(f"Desviación estándar: {statistics.stdev(tiempos):.3f} segundos\n")
        f.write(f"Uso promedio de memoria: {statistics.mean(memoria):.2f} MB\n")
        f.write(f"Uso máximo de memoria: {max(memoria):.2f} MB\n\n")
        
        f.write("DETALLE POR CONSULTA\n")
        f.write("-" * 80 + "\n")
        for r in resultados:
            f.write(f"\nConsulta: {r['consulta']}\n")
            f.write(f"Tiempo de respuesta: {r['tiempo_respuesta']:.3f} segundos\n")
            f.write(f"Uso de memoria: {r['memoria_uso']:.2f} MB\n")

def main():
    """Función principal para ejecutar las pruebas de rendimiento."""
    try:
        resultados = ejecutar_pruebas_rendimiento()
        generar_informe(resultados)
        print(f"\nPruebas completadas. Informe generado en: {REPORT_FILE}")
    except Exception as e:
        print(f"Error durante las pruebas: {e}")
        raise

if __name__ == "__main__":
    main() 