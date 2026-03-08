from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class ResearchResult(Base):
    __tablename__ = "research_results"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    
    # Promoter research
    promoter_name = Column(String)
    promoter_finding = Column(Text)
    promoter_sentiment = Column(String)
    
    # Litigation
    litigation_source = Column(String)
    litigation_summary = Column(Text)
    severity_penalty = Column(Integer)
    
    # Sector
    sector_headwinds = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
