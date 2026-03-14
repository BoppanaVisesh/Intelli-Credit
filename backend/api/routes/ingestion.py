from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime
import json

from api.dependencies import get_db
from core.config import get_settings
from models.uploaded_document import UploadedDocument, DocumentType, ParseStatus
from models.application import Application
from pillar1_ingestor.document_classifier import DocumentClassifier
from pillar1_ingestor.bank_statement_parser import BankStatementParser
from pillar1_ingestor.gst_parser import GSTParser
from pillar1_ingestor.itr_parser import ITRParser
from pillar1_ingestor.annual_report_parser import AnnualReportParser
from pillar1_ingestor.financial_statement_parser import FinancialStatementParser
from pillar1_ingestor.shareholding_parser import ShareholdingPatternParser
from pillar1_ingestor.liquidity_disclosure_parser import LiquidityDisclosureParser

router = APIRouter()

# Create uploads directory if not exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-documents")
async def upload_documents(
    application_id: str = Form(...),
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload documents for an application.
    Files are saved to disk, classified, parsed, and stored in database.
    """
    
    # Verify application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    # Create application-specific upload directory
    app_upload_dir = UPLOAD_DIR / application_id
    app_upload_dir.mkdir(exist_ok=True)
    
    uploaded_files = []
    settings = get_settings()
    classifier = DocumentClassifier(gemini_api_key=settings.GEMINI_API_KEY)
    
    for file in files:
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            unique_filename = f"{file_id}{file_extension}"
            file_path = app_upload_dir / unique_filename
            
            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            # Use explicit document_type if provided, otherwise classify
            if document_type and document_type in DocumentType.__members__:
                doc_type = document_type
                confidence = 1.0
                print(f"📄 Tagged: {file.filename} → {doc_type} (explicit)")
            else:
                print(f"📄 Classifying: {file.filename}")
                doc_type, confidence = classifier.classify(str(file_path), original_filename=file.filename)
                print(f"   → Type: {doc_type} (confidence: {confidence:.0%})")
            
            # Create database record
            upload_record = UploadedDocument(
                id=file_id,
                application_id=application_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path.relative_to(UPLOAD_DIR)),
                file_size_bytes=file_size,
                content_type=file.content_type,
                document_type=doc_type,
                classification_confidence=confidence,
                parse_status=ParseStatus.PENDING
            )
            
            db.add(upload_record)
            db.commit()
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "document_type": doc_type,
                "classification_confidence": confidence,
                "size_bytes": file_size,
                "parse_status": "PENDING"
            })
            
        except Exception as e:
            print(f"❌ Error uploading {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    return {
        "application_id": application_id,
        "uploaded_files": uploaded_files,
        "total_files": len(uploaded_files),
        "status": "uploaded_successfully"
    }


@router.post("/parse-documents/{application_id}")
async def parse_documents(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger document parsing for all pending documents of an application.
    """
    
    # Get all pending documents for this application
    pending_docs = db.query(UploadedDocument).filter(
        UploadedDocument.application_id == application_id,
        UploadedDocument.parse_status == ParseStatus.PENDING
    ).all()
    
    if not pending_docs:
        return {
            "application_id": application_id,
            "message": "No pending documents to parse",
            "parsed_count": 0
        }
    
    # Initialize parsers with API keys
    settings = get_settings()
    bank_parser = BankStatementParser()
    gst_parser = GSTParser()
    itr_parser = ITRParser(gemini_api_key=settings.GEMINI_API_KEY)
    annual_report_parser = AnnualReportParser(api_key=settings.GEMINI_API_KEY)
    financial_statement_parser = FinancialStatementParser(gemini_api_key=settings.GEMINI_API_KEY)
    shareholding_parser = ShareholdingPatternParser(gemini_api_key=settings.GEMINI_API_KEY)
    liquidity_parser = LiquidityDisclosureParser(gemini_api_key=settings.GEMINI_API_KEY)
    
    parsed_count = 0
    results = []
    
    for doc in pending_docs:
        try:
            # Update status to IN_PROGRESS
            doc.parse_status = ParseStatus.IN_PROGRESS
            db.commit()
            
            file_path = UPLOAD_DIR / doc.file_path
            parsed_data = None
            
            print(f"\n🔍 Parsing {doc.original_filename} ({doc.document_type})...")
            
            # Parse based on document type
            if doc.document_type == DocumentType.BANK_STATEMENT:
                parsed_data = bank_parser.parse_bank_statement(str(file_path))
                
            elif doc.document_type == DocumentType.GST_RETURN:
                parsed_data = gst_parser.parse_gst_file(str(file_path))
                
            elif doc.document_type == DocumentType.ITR:
                parsed_data = itr_parser.parse(str(file_path))
                
            elif doc.document_type == DocumentType.ANNUAL_REPORT:
                parsed_data = annual_report_parser.parse_annual_report(str(file_path))
            
            elif doc.document_type == DocumentType.BALANCE_SHEET:
                parsed_data = financial_statement_parser.parse(str(file_path))

            elif doc.document_type == DocumentType.SHAREHOLDING_PATTERN:
                parsed_data = shareholding_parser.parse(str(file_path))

            elif doc.document_type == DocumentType.ALM:
                parsed_data = liquidity_parser.parse(str(file_path))

            else:
                print(f"⚠️ No parser available for {doc.document_type}")
                parsed_data = {"note": f"No parser for {doc.document_type}"}
            
            # Save parsed data
            doc.parsed_data = json.dumps(parsed_data)
            doc.parse_status = ParseStatus.COMPLETED
            doc.parsed_at = datetime.utcnow()
            parsed_count += 1
            
            print(f"✅ Parsed {doc.original_filename} successfully")
            
            results.append({
                "file_id": doc.id,
                "filename": doc.original_filename,
                "document_type": doc.document_type,
                "parse_status": "COMPLETED",
                "parsed_data": parsed_data
            })
            
        except Exception as e:
            print(f"❌ Parsing failed for {doc.original_filename}: {str(e)}")
            doc.parse_status = ParseStatus.FAILED
            doc.parse_error = str(e)
            
            results.append({
                "file_id": doc.id,
                "filename": doc.original_filename,
                "document_type": doc.document_type,
                "parse_status": "FAILED",
                "error": str(e)
            })
        
        finally:
            db.commit()
    
    return {
        "application_id": application_id,
        "status": "parsing_completed",
        "parsed_count": parsed_count,
        "total_documents": len(pending_docs),
        "results": results
    }


@router.get("/documents/{application_id}")
async def get_documents(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get all uploaded documents for an application"""
    
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.application_id == application_id
    ).all()
    
    return {
        "application_id": application_id,
        "documents": [
            {
                "file_id": doc.id,
                "filename": doc.original_filename,
                "document_type": doc.document_type,
                "classification_confidence": doc.classification_confidence,
                "parse_status": doc.parse_status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "parsed_at": doc.parsed_at.isoformat() if doc.parsed_at else None,
                "parsed_data": json.loads(doc.parsed_data) if doc.parsed_data else None,
                "parse_error": doc.parse_error
            }
            for doc in documents
        ],
        "total_documents": len(documents)
    }

