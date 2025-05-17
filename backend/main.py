"""Main entry point for the chatbot application."""
import os
from dotenv import load_dotenv
import uvicorn
import logging
from pathlib import Path

# Cargar variables de entorno PRIMERO
env_path = Path(__file__).resolve().parent / '.env' # .resolve() para mayor robustez
if env_path.exists():
    load_dotenv(env_path)
    # El logger aquí aún no está configurado con el formato de la app,
    # así que un print puede ser más fiable para este punto temprano.
    print(f"Variables de entorno cargadas desde: {env_path}")
else:
    print(f"Archivo .env no encontrado en: {env_path}. Asegúrate de que las variables de entorno están configuradas externamente si es necesario.")

# Importar create_app después de cargar .env, ya que config.py podría usar las variables.
from .api.app import create_app # Importar create_app desde la nueva ubicación centralizada
from .config import settings # settings puede seguir siendo útil aquí para uvicorn

# La configuración de logging, la verificación de API key y el registro de routers
# se han movido a api/app.py dentro de create_app().

# Inicializar el logger para este módulo después de que basicConfig haya sido llamado en create_app
# Esto significa que create_app() debe ser llamado antes de que este logger se use extensivamente.
# O, si es necesario loguear antes, el formato será el default de Python.

# Crear la aplicación FastAPI
# Cualquier error crítico de inicialización (como API keys faltantes) debería ocurrir dentro de create_app()
# y detener el proceso allí si es necesario.
try:
    app = create_app()
    # Solo ahora el logger de la aplicación está completamente configurado.
    logger = logging.getLogger(__name__) # Obtener logger después de la inicialización en create_app
    logger.info("Aplicación FastAPI creada exitosamente desde main.py.")
except ValueError as e:
    # Capturar errores de configuración críticos como ValueError de la API Key
    # El logger aquí podría no estar formateado como se espera si create_app falló muy temprano.
    print(f"Error CRÍTICO al crear la aplicación FastAPI: {e}. El servidor no puede iniciar.")
    # Salir si la app no se pudo crear debido a un error fatal de configuración.
    exit(1)
except Exception as e:
    print(f"Una excepción inesperada ocurrió al crear la aplicación FastAPI: {e}. El servidor no puede iniciar.")
    exit(1)

if __name__ == "__main__":
    # El logger aquí ya debería estar configurado por create_app()
    if 'logger' not in locals(): # En caso de que create_app falle antes de definir su logger
        logging.basicConfig(level=logging.INFO) # Fallback básico
        logger = logging.getLogger(__name__)
        
    logger.info(f"Iniciando servidor Uvicorn en http://{settings.host}:{settings.port}")
    uvicorn.run(
        app, # app ya es la instancia de FastAPI
        host=settings.host, 
        port=settings.port, 
        log_level=settings.log_level.lower() # Uvicorn usa lowercase para log level
    )