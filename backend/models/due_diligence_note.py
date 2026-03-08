from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class DueDiligenceNote(Base):
    __tablename__ = "due_diligence_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    
    credit_officer_notes = Column(Text, nullable=False)
    risk_category = Column(String)
    severity = Column(String)
    score_adjustment = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
