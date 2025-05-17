"""API Schema for Chat routes."""
from typing import Optional, List, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Chat request model."""
    input: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID, a new one will be generated if not provided")

class ChatResponse(BaseModel):
    """Chat response model (no streaming)."""
    output: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")

class StreamEventOp(BaseModel):
    op: str
    path: str
    value: Any

class StreamEventData(BaseModel):
    streamed_output: str
    ops: Optional[List[StreamEventOp]] = None

class ClearHistoryResponse(BaseModel):
    status: str = "success"
    message: str 