"""Base schemas for the API."""

from pydantic import BaseModel

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    status: str = "success"
    message: str 