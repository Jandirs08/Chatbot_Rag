import requests
import json
import asyncio

# Constantes para colores en la terminal
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"

BASE_URL = "http://localhost:8080/api/v1"

async def get_rag_status():
    """Obtiene y muestra el estado actual del RAG con detalles."""
    print(f"\n{BOLD}{BLUE}--- PASO 1: Verificando el estado actual del RAG ---{RESET}")
    print("Realizando una solicitud GET a /api/v1/rag/rag-status para obtener información sobre los PDFs y el Vector Store.\n")
    try:
        response = requests.get(f"{BASE_URL}/rag/rag-status")
        response.raise_for_status() # Lanza excepción para códigos de estado 4xx/5xx
        status_data = response.json()
        
        print(f"{BOLD}{GREEN}✅ Solicitud exitosa. Respuesta recibida:{RESET}")
        print(json.dumps(status_data, indent=2))

        pdfs_count = len(status_data.get("pdfs", []))
        vector_store_exists = status_data.get("vector_store", {}).get("exists", False)
        vector_store_size = status_data.get("vector_store", {}).get("size", 0)
        total_documents_in_vector_store = status_data.get("total_documents", 0)
        
        print(f"\n{BOLD}{CYAN}Análisis del estado del RAG:{RESET}")
        print(f"  - PDFs detectados en el almacenamiento: {pdfs_count}")
        print(f"  - Vector Store existe: {'Sí' if vector_store_exists else 'No'}")
        print(f"  - Tamaño del Vector Store: {vector_store_size / (1024*1024):.2f} MB")
        print(f"  - {BOLD}Fragmentos (chunks) en el Vector Store:{RESET} {total_documents_in_vector_store}")

        if pdfs_count > 0 and total_documents_in_vector_store > 0 and vector_store_exists:
            print(f"{BOLD}{GREEN}  Conclusión: El RAG parece estar funcionando y contiene documentos procesados.{RESET}")
        else:
            print(f"{BOLD}{YELLOW}  Conclusión: El RAG no tiene documentos procesados en el Vector Store o hay un problema.{RESET}")

        return status_data
    except requests.exceptions.RequestException as e:
        print(f"{BOLD}{RED}❌ ERROR al obtener el estado del RAG: {e}{RESET}")
        print(f"{YELLOW}Asegúrate de que tu servidor FastAPI esté corriendo en {BASE_URL.replace('/api/v1', '')}{RESET}")
        return None

async def test_rag_chat_query(query: str, conversation_id: str = "test_rag_conversation"):
    """Realiza una consulta de chat y muestra la respuesta, indicando si RAG fue utilizado."""
    print(f"\n{BOLD}{BLUE}--- PASO 2: Realizando una consulta de chat RAG ---{RESET}")
    print(f"Realizando una consulta al endpoint /api/v1/chat/stream_log para ' {BOLD}\'{query}\'{RESET}{BLUE} '.")
    print("Se espera que el bot utilice el contexto RAG de tus PDFs para responder si los documentos están procesados.\n")
    try:
        payload = {
            "input": query,
            "conversation_id": conversation_id
        }
        response = requests.post(f"{BASE_URL}/chat/stream_log", json=payload)
        response.raise_for_status()
        
        full_response_content = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    try:
                        json_data = json.loads(decoded_line[len("data:"):].strip())
                        if "streamed_output" in json_data:
                            full_response_content += json_data["streamed_output"]
                    except json.JSONDecodeError:
                        pass

        if full_response_content:
            print(f"{BOLD}{GREEN}✅ Respuesta del Bot recibida:{RESET}")
            print(f"{CYAN}{full_response_content.strip()}{RESET}")
            print(f"{BOLD}{GREEN}\nAnálisis de la respuesta del bot: La respuesta indica que el bot pudo generar una respuesta. Verifica si la información es específica de tus PDFs.{RESET}")
        else:
            print(f"{BOLD}{YELLOW}⚠️ No se recibió respuesta del bot o el formato no es el esperado.{RESET}")

    except requests.exceptions.RequestException as e:
        print(f"{BOLD}{RED}❌ ERROR al realizar la consulta de chat: {e}{RESET}")
        print(f"{YELLOW}Asegúrate de que tu servidor FastAPI esté corriendo en {BASE_URL.replace('/api/v1', '')}{RESET}")
    except Exception as e:
        print(f"{BOLD}{RED}❌ Un error inesperado ocurrió durante la consulta de chat: {e}{RESET}")

async def main():
    print(f"{BOLD}{CYAN}===== INICIANDO PRUEBAS DE FUNCIONALIDAD RAG ====={RESET}")

    # Paso 1: Obtener estado del RAG y verificar PDFs y Vector Store
    rag_status_data = await get_rag_status()

    # Paso 2: Realizar una consulta de chat RAG para verificar la recuperación de documentos
    query_text = "¿Qué tipos de becas existen?"
    await test_rag_chat_query(query_text)
    
    print(f"\n{BOLD}{CYAN}===== PRUEBAS DE FUNCIONALIDAD RAG COMPLETADAS ====={RESET}")
    print(f"{BOLD}Revisa los logs del servidor para ver si el RAGRetriever recuperó documentos durante la consulta de chat.{RESET}")
    print(f"{BOLD}Si el bot respondió con información de tus PDFs, significa que el RAG está funcionando.{RESET}")

if __name__ == "__main__":
    asyncio.run(main()) 