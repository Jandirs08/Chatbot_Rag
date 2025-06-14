"""RAG-related schemas."""

from typing import List
from pydantic import BaseModel

from .base import BaseResponse
from .pdf import PDFListItem

class RAGStatusPDFDetail(PDFListItem):
    """Model for PDF details in RAG status."""
    pass

class RAGStatusVectorStoreDetail(BaseModel):
    """Model for vector store details in RAG status."""
    path: str
    exists: bool
    size: int

class RAGStatusResponse(BaseModel):
    """Response model for RAG status endpoint."""
    pdfs: List[RAGStatusPDFDetail]
    vector_store: RAGStatusVectorStoreDetail
    total_documents: int

class ClearRAGResponse(BaseResponse):
    """Response model for clear RAG endpoint."""
    remaining_pdfs: int
    vector_store_size: int 