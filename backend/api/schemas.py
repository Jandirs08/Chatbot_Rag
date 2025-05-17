"""API models for chatbot requests and responses."""
from typing import Optional
from pydantic import BaseModel

# Modelo para Health Check (opcional, pero bueno para consistencia)
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: Optional[str] = None 