from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid
import os

from core.database import get_db
from core.config import get_settings
from models.application import Application, ApplicationStatus
from schemas.application import (
    ApplicationCreateRequest,
    CreditAnalysisResponse,
    ApplicationListResponse,
    ApplicationListItem,
    CompanyDetails,
    FinancialAnalysis,
    RawDataExtracted,
    ReconciliationFlags,
    CalculatedRatios,
    AIResearchAgent,
    PromoterCheck,
    LitigationRecord,
    PrimaryDueDiligence,
    AITranslatedImpact,
    RiskScoringEngine,
    ShapExplanation,
    CAMGeneration,
    RiskLevel,
    Sentiment,
    Decision,
    ImpactType
)

# Import REAL processing services
from services.orchestration_service import CreditAnalysisOrchestrator
from services.llm_service import get_llm_service

router = APIRouter()
settings = get_settings()

# Initialize orchestrator with REAL APIs
orchestrator = CreditAnalysisOrchestrator(
    llm_provider=settings.LLM_PROVIDER,  # Uses Gemini from .env
    gemini_api_key=settings.GEMINI_API_KEY,
    tavily_api_key=settings.TAVILY_API_KEY
)


# No mock functions - all processing is real


@router.post("/analyze-credit", response_model=CreditAnalysisResponse)
async def analyze_credit(
    company_name: str = Form(...),
    mca_cin: str = Form(...),
    sector: str = Form(...),
    requested_limit_cr: float = Form(...),
    credit_officer_notes: Optional[str] = Form(None),
    annual_report: Optional[UploadFile] = File(None),
    bank_statements: Optional[UploadFile] = File(None),
    gst_returns: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    REAL credit analysis endpoint - processes documents, searches web, scores with ML.
    Uses Gemini AI + Tavily Search + real parsers.
    """
    
    # Generate application ID
    application_id = f"APP-{datetime.utcnow().year}-{uuid.uuid4().hex[:5].upper()}"
    
    # Create application in database
    app = Application(
        id=application_id,
        company_name=company_name,
        mca_cin=mca_cin,
        sector=sector,
        requested_limit_cr=requested_limit_cr,
        status=ApplicationStatus.PROCESSING
    )
    db.add(app)
    db.commit()
    
    # Save uploaded files
    file_paths = {}
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    if annual_report:
        file_path = os.path.join(upload_dir, f"{application_id}_annual_report.pdf")
        with open(file_path, "wb") as f:
            f.write(await annual_report.read())
        file_paths['annual_report'] = file_path
    
    if bank_statements:
        file_path = os.path.join(upload_dir, f"{application_id}_bank.pdf")
        with open(file_path, "wb") as f:
            f.write(await bank_statements.read())
        file_paths['bank_statements'] = file_path
    
    if gst_returns:
        file_path = os.path.join(upload_dir, f"{application_id}_gst.xlsx")
        with open(file_path, "wb") as f:
            f.write(await gst_returns.read())
        file_paths['gst_returns'] = file_path
    
    try:
        # 🚀 REAL PROCESSING - Uses Gemini + Tavily + ML
        result = await orchestrator.analyze_application(
            application_id=application_id,
            company_name=company_name,
            mca_cin=mca_cin,
            sector=sector,
            requested_limit_cr=requested_limit_cr,
            credit_officer_notes=credit_officer_notes,
            file_paths=file_paths
        )
        
        # Update database with REAL results
        app.status = ApplicationStatus.COMPLETED
        app.final_credit_score = result["risk_scoring_engine"]["final_credit_score"]
        app.decision = result["risk_scoring_engine"]["decision"]
        app.recommended_limit_cr = result["risk_scoring_engine"]["recommended_limit_cr"]
        app.executive_summary = result["cam_generation"]["executive_summary"]
        app.cam_document_url = result["cam_generation"]["document_url"]
        
        # Save financial data
        app.gstr_1_sales_cr = result["financial_analysis"]["raw_data_extracted"]["gstr_1_sales_cr"]
        app.bank_statement_inflows_cr = result["financial_analysis"]["raw_data_extracted"]["bank_statement_inflows_cr"]
        app.dscr = result["financial_analysis"]["calculated_ratios"]["dscr"]
        app.current_ratio = result["financial_analysis"]["calculated_ratios"]["current_ratio"]
        app.debt_to_equity = result["financial_analysis"]["calculated_ratios"]["debt_to_equity"]
        
        db.commit()
        
        return CreditAnalysisResponse(**result)
        
    except Exception as e:
        app.status = ApplicationStatus.FAILED
        db.commit()
        
        # Return clear error message instead of mock data
        print(f"❌ Credit analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Credit analysis processing failed",
                "message": str(e),
                "application_id": application_id,
                "status": "FAILED",
                "note": "Check API keys (GEMINI_API_KEY, TAVILY_API_KEY) and uploaded documents"
            }
        )


@router.post("/", response_model=dict)
async def create_application(
    request: ApplicationCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new application without processing"""
    application_id = f"APP-{datetime.utcnow().year}-{uuid.uuid4().hex[:5].upper()}"
    
    app = Application(
        id=application_id,
        company_name=request.company_name,
        mca_cin=request.mca_cin,
        sector=request.sector,
        requested_limit_cr=request.requested_limit_cr,
        status=ApplicationStatus.PENDING
    )
    db.add(app)
    db.commit()
    
    return {
        "application_id": application_id,
        "status": "created",
        "message": "Application created successfully"
    }


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all applications"""
    applications = db.query(Application).offset(skip).limit(limit).all()
    total = db.query(Application).count()
    
    items = [
        ApplicationListItem(
            application_id=app.id,
            company_name=app.company_name,
            sector=app.sector,
            requested_limit_cr=app.requested_limit_cr,
            status=app.status.value,
            created_at=app.created_at,
            final_score=app.final_credit_score,
            decision=app.decision
        )
        for app in applications
    ]
    
    return ApplicationListResponse(applications=items, total=total)


@router.get("/{application_id}", response_model=CreditAnalysisResponse)
async def get_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific application's full analysis"""
    app = db.query(Application).filter(Application.id == application_id).first()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if analysis is completed
    if app.status != ApplicationStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not completed. Current status: {app.status}"
        )
    
    # Get research results if available
    from models.research_result import ResearchResult
    research_results = db.query(ResearchResult).filter(
        ResearchResult.application_id == application_id
    ).all()
    
    # Format research findings
    promoter_checks = []
    litigation = []
    sector_info = ""
    
    for result in research_results:
        if result.research_type == "promoter":
            promoter_checks.append({
                "name": result.entity_name,
                "finding": result.findings_json.get("summary", ""),
                "sentiment": result.sentiment
            })
        elif result.research_type == "litigation":
            litigation.append({
                "source": result.source_url or "eCourts Search",
                "summary": result.findings_json.get("summary", ""),
                "severity_penalty": -10 if result.risk_level == RiskLevel.HIGH else -5
            })
        elif result.research_type == "sector":
            sector_info = result.findings_json.get("analysis", "")
    
    # Build response from database fields
    return CreditAnalysisResponse(
        application_id=app.id,
        timestamp=app.created_at,
        company_details={
            "company_name": app.company_name,
            "mca_cin": app.mca_cin,
            "sector": app.sector,
            "requested_limit_cr": app.requested_limit_cr
        },
        financial_analysis={
            "raw_data_extracted": {
                "gstr_1_sales_cr": app.gstr_1_sales_cr or 0.0,
                "bank_statement_inflows_cr": app.bank_statement_inflows_cr or 0.0,
                "total_debt_cr": 0.0  # Extract from balance sheet if available
            },
            "calculated_ratios": {
                "dscr": app.dscr or 0.0,
                "current_ratio": app.current_ratio or 0.0,
                "debt_to_equity": app.debt_to_equity or 0.0
            }
        },
        ai_research_agent={
            "promoter_checks": promoter_checks,
            "litigation_and_nclt": litigation,
            "sector_headwinds": sector_info
        },
        risk_scoring_engine={
            "final_credit_score": app.final_credit_score or 0,
            "decision": app.decision or Decision.PENDING,
            "recommended_limit_cr": app.recommended_limit_cr or 0.0
        },
        cam_generation={
            "executive_summary": app.executive_summary or "Analysis pending",
            "document_url": app.cam_document_url or ""
        }
    )
