"""PDF-related schemas."""

from typing import List
from datetime import datetime
from pydantic import BaseModel

from .base import BaseResponse

class PDFListItem(BaseModel):
    """Model for PDF file information."""
    filename: str
    path: str
    size: int
    last_modified: datetime

class PDFListResponse(BaseModel):
    """Response model for PDF list endpoint."""
    pdfs: List[PDFListItem]

class PDFUploadResponse(BaseResponse):
    """Response model for PDF upload endpoint."""
    file_path: str
    pdfs_in_directory: List[str]

class PDFDeleteResponse(BaseResponse):
    """Response model for PDF delete endpoint."""
    pass 