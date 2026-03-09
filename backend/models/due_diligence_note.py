from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class DueDiligenceNote(Base):
    __tablename__ = "due_diligence_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    
    # Input
    insight_type = Column(String, default="general")  # site_visit, management_interview, observation, general
    credit_officer_notes = Column(Text, nullable=False)
    
    # AI Analysis
    ai_summary = Column(Text)
    risk_category = Column(String)  # Operational, Governance, Financial, Management, Compliance
    severity = Column(String)       # HIGH, MEDIUM, LOW
    score_adjustment = Column(Integer, default=0)
    sentiment = Column(String)      # POSITIVE, NEGATIVE, NEUTRAL
    confidence = Column(Float, default=0.0)
    
    # Extracted entities & flags
    risk_flags_json = Column(Text)  # JSON: list of extracted risk flags
    entities_json = Column(Text)    # JSON: extracted entities (people, orgs, locations)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
