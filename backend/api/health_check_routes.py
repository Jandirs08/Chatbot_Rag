from fastapi import APIRouter, status

# Importar modelo Pydantic
from .schemas import HealthResponse

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check():
    """Health check endpoint for the API."""
    return HealthResponse(status="healthy", service="chatbot-backend") 