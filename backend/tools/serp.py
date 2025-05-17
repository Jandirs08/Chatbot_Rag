from typing import Optional

import asyncio # Añadido para run_in_executor
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import (
    CallbackManagerForToolRun,
    AsyncCallbackManagerForToolRun, # Añadido para _arun
)
from langchain_community.utilities.serpapi import SerpAPIWrapper
from ..config import settings # Corregido: ..config en lugar de ..common.config


class CustomSearchTool(BaseTool):
    name: str = "Custom search"
    description: str = (
        "Useful for when you need to answer questions about current or newest events, date, ..."
    )
    _search_instance: Optional[SerpAPIWrapper] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.serpapi_api_key:
            self._search_instance = SerpAPIWrapper(
                serpapi_api_key=settings.serpapi_api_key.get_secret_value(),
                params={
                    "engine": "google",
                    "gl": "us",
                    "hl": "en", # Cambiado de "vi" a "en" por consistencia, ajustar si es necesario
                },
            )
        else:
            print(
                "ADVERTENCIA: SERPAPI_API_KEY no está configurada. "\
                "La herramienta de búsqueda personalizada no funcionará."
            )

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        if not self._search_instance:
            return (
                "Error: La herramienta de búsqueda no está configurada. "
                "Falta SERPAPI_API_KEY."
            )
        return self._search_instance.run(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        if not self._search_instance:
            return (
                "Error: La herramienta de búsqueda no está configurada. "
                "Falta SERPAPI_API_KEY."
            )
        # Dado que SerpAPIWrapper.arun puede no existir o no ser completamente async,
        # es más seguro ejecutar la versión síncrona en un executor.
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_instance.run, query)
