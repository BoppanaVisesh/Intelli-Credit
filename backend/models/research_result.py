from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class ResearchResult(Base):
    __tablename__ = "research_results"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    
    # Common fields
    research_type = Column(String, nullable=False)  # news, litigation, promoter, sector, regulatory
    entity_name = Column(String)  # Company name, promoter name, sector name
    risk_level = Column(String)  # HIGH, MEDIUM, LOW
    source_url = Column(String)
    
    # Findings stored as JSON text
    findings_summary = Column(Text)
    findings_json = Column(Text)  # Full JSON data
    sentiment = Column(String)  # POSITIVE, NEGATIVE, NEUTRAL
    
    # Scoring
    severity_penalty = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
