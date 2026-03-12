from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    mca_cin = Column(String, nullable=False, index=True)
    pan = Column(String)
    sector = Column(String, nullable=False)
    incorporation_date = Column(String)
    registered_address = Column(Text)
    annual_turnover_cr = Column(Float)
    employee_count = Column(Integer)
    promoter_names = Column(Text)  # comma-separated
    requested_limit_cr = Column(Float, nullable=False)
    
    # Loan details
    loan_type = Column(String)  # Working Capital / Term Loan / CC/OD / BG/LC
    loan_tenure_months = Column(Integer)
    interest_type = Column(String)  # Fixed / Floating
    collateral_offered = Column(Text)
    purpose_of_loan = Column(Text)
    existing_banking = Column(Text)
    
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    
    # Financial data
    gstr_1_sales_cr = Column(Float)
    gstr_3b_sales_cr = Column(Float)
    gstr_2a_purchases_cr = Column(Float)
    bank_statement_inflows_cr = Column(Float)
    total_debt_cr = Column(Float)
    net_operating_income_cr = Column(Float)
    
    # Ratios
    dscr = Column(Float)
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    
    # Flags
    circular_trading_risk = Column(String)
    red_flag_triggered = Column(Boolean, default=False)
    gst_vs_bank_variance_percent = Column(Float)
    
    # Final results
    final_credit_score = Column(Integer)
    decision = Column(String)
    recommended_limit_cr = Column(Float)
    
    # CAM
    cam_document_url = Column(String)
    executive_summary = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("UploadedDocument", back_populates="application")
