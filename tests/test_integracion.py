"""
Script para evaluar la integración del chatbot RAG con otros componentes.
Prueba la interacción entre diferentes módulos y servicios.
"""
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, List

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_FILE = PROJECT_ROOT / "integration_report.txt"

# Configuración
API_URL = "http://localhost:8000"  # Ajustar según la configuración
TIMEOUT = 30  # segundos

def probar_conexion_api() -> bool:
    """Prueba la conexión con el API del chatbot."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        return response.status_code == 200
    except requests.RequestException:
        return False

def probar_consulta_basica() -> Dict[str, Any]:
    """Prueba una consulta básica al chatbot."""
    query = "¿Qué es un sistema RAG?"
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": query, "session_id": "test_session"},
            timeout=TIMEOUT
        )
        return {
            "exitoso": response.status_code == 200,
            "respuesta": response.json() if response.status_code == 200 else None,
            "error": None if response.status_code == 200 else response.text
        }
    except requests.RequestException as e:
        return {
            "exitoso": False,
            "respuesta": None,
            "error": str(e)
        }

def probar_multiples_consultas() -> List[Dict[str, Any]]:
    """Prueba múltiples consultas en secuencia."""
    consultas = [
        "¿Qué es un sistema RAG?",
        "Explica cómo funciona la recuperación de documentos",
        "¿Cuáles son las ventajas de usar embeddings?",
        "Dame un ejemplo de prompt engineering",
        "¿Cómo se implementa la memoria en un chatbot?"
    ]
    
    resultados = []
    session_id = f"test_session_{int(time.time())}"
    
    for consulta in consultas:
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"query": consulta, "session_id": session_id},
                timeout=TIMEOUT
            )
            resultados.append({
                "consulta": consulta,
                "exitoso": response.status_code == 200,
                "respuesta": response.json() if response.status_code == 200 else None,
                "error": None if response.status_code == 200 else response.text
            })
        except requests.RequestException as e:
            resultados.append({
                "consulta": consulta,
                "exitoso": False,
                "respuesta": None,
                "error": str(e)
            })
    
    return resultados

def generar_informe(resultados: Dict[str, Any]):
    """Genera un informe con los resultados de las pruebas de integración."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("INFORME DE PRUEBAS DE INTEGRACIÓN\n")
        f.write("=" * 80 + "\n\n")
        
        # Estado de la conexión
        f.write("ESTADO DE LA CONEXIÓN\n")
        f.write("-" * 80 + "\n")
        f.write(f"API accesible: {'Sí' if resultados['conexion_api'] else 'No'}\n\n")
        
        # Prueba básica
        f.write("PRUEBA BÁSICA\n")
        f.write("-" * 80 + "\n")
        f.write(f"Consulta: {resultados['prueba_basica']['consulta']}\n")
        f.write(f"Exitosa: {'Sí' if resultados['prueba_basica']['exitoso'] else 'No'}\n")
        if not resultados['prueba_basica']['exitoso']:
            f.write(f"Error: {resultados['prueba_basica']['error']}\n")
        f.write("\n")
        
        # Pruebas múltiples
        f.write("PRUEBAS MÚLTIPLES\n")
        f.write("-" * 80 + "\n")
        for prueba in resultados['pruebas_multiples']:
            f.write(f"\nConsulta: {prueba['consulta']}\n")
            f.write(f"Exitosa: {'Sí' if prueba['exitoso'] else 'No'}\n")
            if not prueba['exitoso']:
                f.write(f"Error: {prueba['error']}\n")
        
        # Resumen
        f.write("\nRESUMEN\n")
        f.write("-" * 80 + "\n")
        total_pruebas = len(resultados['pruebas_multiples']) + 1  # +1 por la prueba básica
        pruebas_exitosas = sum(1 for p in resultados['pruebas_multiples'] if p['exitoso'])
        if resultados['prueba_basica']['exitoso']:
            pruebas_exitosas += 1
        
        f.write(f"Total de pruebas: {total_pruebas}\n")
        f.write(f"Pruebas exitosas: {pruebas_exitosas}\n")
        f.write(f"Pruebas fallidas: {total_pruebas - pruebas_exitosas}\n")
        f.write(f"Tasa de éxito: {(pruebas_exitosas/total_pruebas)*100:.1f}%\n")

def main():
    """Función principal para ejecutar las pruebas de integración."""
    print("Iniciando pruebas de integración...")
    
    # Realizar pruebas
    conexion_api = probar_conexion_api()
    if not conexion_api:
        print("Error: No se pudo conectar con el API del chatbot")
        return
    
    prueba_basica = probar_consulta_basica()
    pruebas_multiples = probar_multiples_consultas()
    
    # Generar informe
    resultados = {
        "conexion_api": conexion_api,
        "prueba_basica": prueba_basica,
        "pruebas_multiples": pruebas_multiples
    }
    
    generar_informe(resultados)
    print(f"\nPruebas completadas. Informe generado en: {REPORT_FILE}")

if __name__ == "__main__":
    main()