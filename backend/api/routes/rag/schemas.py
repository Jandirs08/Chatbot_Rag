"""API Schema for RAG routes."""
from typing import List
from pydantic import BaseModel
from ..pdf.schemas import PDFListItem # Corregido: .pdf.schemas -> ..pdf.schemas

class RAGStatusPDFDetail(PDFListItem):
    pass

class RAGStatusVectorStoreDetail(BaseModel):
    path: str
    exists: bool
    size: int

class RAGStatusResponse(BaseModel):
    pdfs: List[RAGStatusPDFDetail]
    vector_store: RAGStatusVectorStoreDetail
    total_documents: int

class ClearRAGResponse(BaseModel):
    status: str
    message: str
    remaining_pdfs: int
    vector_store_size: int 