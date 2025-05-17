"""API Schema for PDF routes."""
from typing import List
from pydantic import BaseModel
import datetime

class PDFListItem(BaseModel):
    filename: str
    path: str
    size: int
    last_modified: datetime.datetime

class PDFListResponse(BaseModel):
    pdfs: List[PDFListItem]

class PDFUploadResponse(BaseModel):
    status: str = "success"
    message: str
    file_path: str
    pdfs_in_directory: List[str]

class PDFDeleteResponse(BaseModel):
    status: str = "success"
    message: str 