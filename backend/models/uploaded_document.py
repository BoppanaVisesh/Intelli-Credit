"""
Uploaded Document Model - Track uploaded files and parsing status
"""
from sqlalchemy import Column, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from core.database import Base


class DocumentType(str, enum.Enum):
    """Document types that can be uploaded"""
    BANK_STATEMENT = "BANK_STATEMENT"
    GST_RETURN = "GST_RETURN"
    ITR = "ITR"
    ANNUAL_REPORT = "ANNUAL_REPORT"
    BALANCE_SHEET = "BALANCE_SHEET"
    ALM = "ALM"
    SHAREHOLDING_PATTERN = "SHAREHOLDING_PATTERN"
    BORROWING_PROFILE = "BORROWING_PROFILE"
    PORTFOLIO_DATA = "PORTFOLIO_DATA"
    OTHER = "OTHER"


class ParseStatus(str, enum.Enum):
    """Parsing status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UploadedDocument(Base):
    """Track uploaded documents and their parsing status"""
    
    __tablename__ = "uploaded_documents"
    
    # Primary identification
    id = Column(String, primary_key=True)  # UUID
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    
    # File details
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Relative path from uploads/
    file_size_bytes = Column(Float, nullable=False)
    content_type = Column(String)
    
    # Document classification
    document_type = Column(Enum(DocumentType), nullable=False)
    classification_confidence = Column(Float, default=0.0)
    
    # Parsing status
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.PENDING)
    parsed_data = Column(Text)  # JSON string of extracted data
    parse_error = Column(Text)  # Error message if parsing failed
    
# Human-in-the-loop classification review
    reviewed = Column(String, default="pending")  # pending | approved | edited
    reviewed_type = Column(String, nullable=True)  # user-corrected type if edited

    # Schema-based extraction
    extraction_schema_id = Column(String, nullable=True)
    extracted_fields_json = Column(Text, nullable=True)  # JSON of schema-mapped data

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsed_at = Column(DateTime)
    
    # Relationship to application
    application = relationship("Application", back_populates="documents")
    
    def __repr__(self):
        return f"<UploadedDocument {self.filename} ({self.document_type})>"
