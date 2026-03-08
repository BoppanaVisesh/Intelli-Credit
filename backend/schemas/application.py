from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Decision(str, Enum):
    APPROVE = "APPROVE"
    CONDITIONAL_APPROVE = "CONDITIONAL_APPROVE"
    REJECT = "REJECT"


class Sentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class ImpactType(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


# Request Schemas
class ApplicationCreateRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    mca_cin: str = Field(..., description="MCA CIN number")
    sector: str = Field(..., description="Business sector")
    requested_limit_cr: float = Field(..., description="Requested loan limit in Crores")


class DueDiligenceNoteRequest(BaseModel):
    application_id: str
    credit_officer_notes: str


# Response Sub-Schemas
class CompanyDetails(BaseModel):
    company_name: str
    mca_cin: str
    sector: str
    requested_limit_cr: float


class RawDataExtracted(BaseModel):
    gstr_1_sales_cr: float
    gstr_3b_sales_cr: float
    gstr_2a_purchases_cr: float
    bank_statement_inflows_cr: float
    total_debt_cr: float
    net_operating_income_cr: float


class ReconciliationFlags(BaseModel):
    gst_vs_bank_variance_percent: float
    circular_trading_risk: RiskLevel
    red_flag_triggered: bool


class CalculatedRatios(BaseModel):
    dscr: float
    current_ratio: float
    debt_to_equity: float


class FinancialAnalysis(BaseModel):
    raw_data_extracted: RawDataExtracted
    reconciliation_flags: ReconciliationFlags
    calculated_ratios: CalculatedRatios


class PromoterCheck(BaseModel):
    name: str
    finding: str
    sentiment: Sentiment


class LitigationRecord(BaseModel):
    source: str
    summary: str
    severity_penalty: int


class AIResearchAgent(BaseModel):
    promoter_checks: List[PromoterCheck]
    litigation_and_nclt: List[LitigationRecord]
    sector_headwinds: str


class AITranslatedImpact(BaseModel):
    risk_category: str
    severity: RiskLevel
    score_adjustment: int


class PrimaryDueDiligence(BaseModel):
    credit_officer_notes: str
    ai_translated_impact: AITranslatedImpact


class ShapExplanation(BaseModel):
    feature: str
    impact_value: float
    type: ImpactType


class RiskScoringEngine(BaseModel):
    model_version: str
    final_credit_score: int
    max_score: int
    decision: Decision
    recommended_limit_cr: float
    shap_explanations: List[ShapExplanation]


class CAMGeneration(BaseModel):
    executive_summary: str
    document_url: str


# Main Response Schema
class CreditAnalysisResponse(BaseModel):
    application_id: str
    timestamp: datetime
    company_details: CompanyDetails
    financial_analysis: FinancialAnalysis
    ai_research_agent: AIResearchAgent
    primary_due_diligence: Optional[PrimaryDueDiligence] = None
    risk_scoring_engine: RiskScoringEngine
    cam_generation: CAMGeneration


# List Response
class ApplicationListItem(BaseModel):
    application_id: str
    company_name: str
    sector: str
    requested_limit_cr: float
    status: str
    created_at: datetime
    final_score: Optional[int] = None
    decision: Optional[Decision] = None


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationListItem]
    total: int
