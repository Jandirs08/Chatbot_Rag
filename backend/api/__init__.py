"""API module for the chatbot application."""

# Importar la función create_app principal desde app.py
from .app import create_app

# Las siguientes importaciones de router son problemáticas y redundantes
# si app.py ya las maneja correctamente desde sus módulos específicos.
# from .routes import router as health_router # Para el health check, etc.
# from .routes.pdf import pdf_router
# from .routes.chat import chat_router
# from .routes.rag import rag_router

# Ya no es necesario definir create_app aquí, se importa desde .app
# from fastapi import FastAPI
# from .routes import router # El router de health_routes se importa arriba

# def create_app() -> FastAPI:
#     app = FastAPI(
#         title="Chatbot API",
#         description="API for interacting with the LangChain-powered chatbot",
#         version="1.0.0",
#     )
#     
#     # Include the routes
#     app.include_router(router, prefix="") # Los routers se incluyen en main.py
#     
#     return app

__all__ = [
    "create_app",
    # "health_router", 
    # "pdf_router",
    # "chat_router",
    # "rag_router"
] 