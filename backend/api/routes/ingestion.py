from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import uuid

router = APIRouter()


@router.post("/upload-documents")
async def upload_documents(
    application_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload documents for an application.
    Files are temporarily stored and queued for processing.
    """
    uploaded_files = []
    
    for file in files:
        file_id = str(uuid.uuid4())
        uploaded_files.append({
            "file_id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else 0
        })
    
    return {
        "application_id": application_id,
        "uploaded_files": uploaded_files,
        "status": "queued_for_processing"
    }


@router.post("/parse-documents")
async def parse_documents(application_id: str):
    """
    Trigger document parsing for an application.
    This will be connected to Pillar 1 processors.
    """
    return {
        "application_id": application_id,
        "status": "parsing_started",
        "message": "Document parsing initiated"
    }
