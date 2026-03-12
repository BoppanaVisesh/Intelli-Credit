"""
Extraction Schema Model — User-defined schemas for structuring extracted document data
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class ExtractionSchema(Base):
    """
    Stores user-defined (or system-default) schemas that describe
    which fields should be extracted from a given document type.
    """

    __tablename__ = "extraction_schemas"

    id = Column(String, primary_key=True)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    document_type = Column(String, nullable=False)  # e.g. ANNUAL_REPORT, ALM …
    schema_name = Column(String, nullable=False)     # human label
    fields_json = Column(Text, nullable=False)       # JSON array of field definitions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application")

    def __repr__(self):
        return f"<ExtractionSchema {self.schema_name} ({self.document_type})>"
