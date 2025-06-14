"""Health check related schemas."""

from pydantic import BaseModel

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "ok"
    version: str
    environment: str 