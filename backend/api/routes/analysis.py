"""
Pre-Cognitive Secondary Analysis & Reporting API

POST /run/{application_id}               → Full analysis pipeline
GET  /{application_id}                    → Retrieve stored analysis results
POST /{application_id}/report             → Generate investment report (.docx)
GET  /{application_id}/report/download    → Download the .docx
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import json
import traceback

from core.database import get_db
from core.config import get_settings
from models.application import Application
from models.uploaded_document import UploadedDocument
from models.research_result import ResearchResult
from models.due_diligence_note import DueDiligenceNote
from pillar1_ingestor.data_normalizer import DataNormalizer
from pillar1_ingestor.cross_verification_engine import CrossVerificationEngine
from pillar3_recommendation.credit_scorer_fixed import CreditScorerFixed
from pillar3_recommendation.loan_limit_engine import LoanLimitEngine
from pillar3_recommendation.risk_premium_calculator import RiskPremiumCalculator
from pillar3_recommendation.explainability import Explainability
from pillar2_research.secondary_research_engine import SecondaryResearchEngine
from pillar2_research.triangulation_engine import TriangulationEngine
from pillar3_recommendation.recommendation_engine import RecommendationEngine
from pillar3_recommendation.swot_report_generator import SWOTGenerator, InvestmentReportGenerator
from services.llm_service import get_llm_service
from services.financial_snapshot import build_financials

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────

def _safe_json(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def _build_financials(app: Application, normalized: dict) -> dict:
    """Derive the standard financials dict from normalised documents."""
    return build_financials(app, normalized)


def _build_research_data(research_rows, fraud_score: float) -> tuple:
    """Summarise research rows into research_data dict + sector_data dict."""
    litigation_count = 0
    promoter_sentiment = "Neutral"
    sector_sentiment = "Neutral"
    overall_risk = 0
    litigation_cases = []
    for r in research_rows:
        if r.research_type in ("litigation", "ecourt"):
            lit = _safe_json(r.findings_json)
            litigation_count += lit.get("total_cases", 0) or (1 if r.risk_level == "HIGH" else 0)
            if r.findings_summary:
                litigation_cases.append({"summary": r.findings_summary})
        if r.research_type == "promoter" and r.sentiment:
            promoter_sentiment = r.sentiment.capitalize()
        if r.research_type == "sector" and r.sentiment:
            sector_sentiment = r.sentiment.capitalize()
        overall_risk += r.severity_penalty or 0

    research_data = {
        "litigation_count": litigation_count,
        "litigation_severity": "High" if overall_risk > 20 else "Low",
        "promoter_sentiment": promoter_sentiment,
        "circular_trading_risk_score": fraud_score,
        "sector_sentiment": sector_sentiment,
        "litigation_cases": litigation_cases,
    }
    sector_data = {"sector_risk_score": min(100, max(0, overall_risk))}
    return research_data, sector_data, litigation_count


def _gather_all(application_id: str, db: Session) -> dict:
    """Gather financial, research, scoring, and loan data for analysis."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Normalise documents
    docs = db.query(UploadedDocument).filter(
        UploadedDocument.application_id == application_id,
        UploadedDocument.parse_status == "COMPLETED",
    ).all()
    normalizer = DataNormalizer()
    doc_records = [{"document_type": d.document_type, "parsed_data": d.parsed_data} for d in docs]
    normalized = normalizer.normalize(doc_records)

    # Cross-verification
    cv_engine = CrossVerificationEngine()
    cv_result = cv_engine.run_verification(normalized)
    fraud_score = cv_result.get("fraud_risk_score", 0)

    financials = _build_financials(app, normalized)

    # Research
    research_rows = db.query(ResearchResult).filter(
        ResearchResult.application_id == application_id,
    ).all()
    research_data, sector_data, litigation_count = _build_research_data(research_rows, fraud_score)

    # Due diligence
    dd_rows = db.query(DueDiligenceNote).filter(
        DueDiligenceNote.application_id == application_id,
    ).all()
    dd_data = {}
    if dd_rows:
        worst = max(dd_rows, key=lambda d: abs(d.score_adjustment or 0))
        dd_data = {"notes": worst.ai_summary or worst.credit_officer_notes or "", "severity": worst.severity or "None"}

    requested_limit = app.requested_limit_cr or 10.0

    # Five Cs scoring
    scorer = CreditScorerFixed()
    scoring = scorer.calculate_credit_score({
        "financials": financials, "research": research_data,
        "due_diligence": dd_data, "sector": sector_data,
        "collateral": {}, "requested_limit_cr": requested_limit,
    })

    # Loan limit
    loan = LoanLimitEngine().calculate_loan_limit(financials, scoring["final_credit_score"], requested_limit)

    # Interest rate
    rate = RiskPremiumCalculator().calculate(
        credit_score=scoring["final_credit_score"],
        dscr=financials["dscr"],
        sector_risk_score=sector_data["sector_risk_score"],
        litigation_count=litigation_count,
    )

    return {
        "app": app,
        "financials": financials,
        "research_data": research_data,
        "sector_data": sector_data,
        "scoring": scoring,
        "loan": loan,
        "rate": rate,
        "normalized": normalized,
    }


# ── Endpoints ────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    use_llm: bool = True


@router.post("/run/{application_id}")
async def run_analysis(application_id: str, req: AnalysisRequest = AnalysisRequest(), db: Session = Depends(get_db)):
    """Run the full pre-cognitive analysis pipeline."""
    try:
        bundle = _gather_all(application_id, db)
        app = bundle["app"]
        financials = bundle["financials"]
        scoring = bundle["scoring"]
        loan = bundle["loan"]
        rate = bundle["rate"]
        settings = get_settings()

        # 1. Secondary research
        sec_engine = SecondaryResearchEngine(tavily_api_key=settings.TAVILY_API_KEY)
        research_bundle = sec_engine.run_full_research(
            company_name=app.company_name,
            sector=app.sector or "General",
            cin=app.mca_cin or "",
            promoter_names=(app.promoter_names or "").split(",") if app.promoter_names else [],
        )

        # 2. Triangulation
        tri_engine = TriangulationEngine()
        triangulation = tri_engine.triangulate(
            financials=financials,
            research_bundle=research_bundle,
        )

        # 3. Recommendation
        rec_engine = RecommendationEngine()
        recommendation = rec_engine.generate_recommendation(
            scoring=scoring,
            research_signals=research_bundle.get("overall_signals", {}),
            triangulation=triangulation,
            financials=financials,
            loan_recommendation=loan,
            interest_rate=rate,
        )

        # 4. SWOT
        swot_gen = SWOTGenerator()
        llm = None
        if req.use_llm:
            try:
                llm = get_llm_service("gemini")
            except Exception:
                pass
        swot = swot_gen.generate_swot(
            company_name=app.company_name,
            sector=app.sector or "General",
            scoring=scoring,
            financials=financials,
            research_bundle=research_bundle,
            triangulation=triangulation,
            llm=llm,
        )

        # Persist summary on application
        app.decision = recommendation["decision"]
        app.final_credit_score = recommendation["credit_score"]
        db.commit()

        result = {
            "application_id": application_id,
            "company_name": app.company_name,
            "sector": app.sector,
            "status": "analysis_complete",
            "research_bundle": research_bundle,
            "triangulation": triangulation,
            "recommendation": recommendation,
            "swot": swot,
            "scoring": scoring,
            "financials": financials,
            "loan_recommendation": loan,
            "interest_rate": rate,
        }

        # Store full analysis as JSON on application executive_summary
        app.executive_summary = json.dumps({
            "research_bundle": research_bundle,
            "triangulation": triangulation,
            "recommendation": recommendation,
            "swot": swot,
        }, default=str)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{application_id}")
async def get_analysis(application_id: str, db: Session = Depends(get_db)):
    """Retrieve previously-run analysis results."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if not app.executive_summary:
        raise HTTPException(status_code=404, detail="Analysis not yet run for this application")

    stored = _safe_json(app.executive_summary)
    if not stored:
        raise HTTPException(status_code=404, detail="No analysis data found")

    return {
        "application_id": application_id,
        "company_name": app.company_name,
        "sector": app.sector,
        "status": "analysis_retrieved",
        **stored,
    }


class ReportRequest(BaseModel):
    pass


@router.post("/{application_id}/report")
async def generate_report(application_id: str, db: Session = Depends(get_db)):
    """Generate the downloadable investment report (.docx)."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    stored = _safe_json(app.executive_summary)
    if not stored:
        raise HTTPException(status_code=400, detail="Run analysis first before generating report")

    try:
        # Re-gather financials + scoring for report
        bundle = _gather_all(application_id, db)

        report_gen = InvestmentReportGenerator()
        filepath = report_gen.generate_report(
            application_id=application_id,
            company_name=app.company_name,
            sector=app.sector or "General",
            swot=stored.get("swot", {}),
            recommendation=stored.get("recommendation", {}),
            triangulation=stored.get("triangulation", {}),
            scoring=bundle["scoring"],
            financials=bundle["financials"],
            research_bundle=stored.get("research_bundle", {}),
        )

        return {
            "application_id": application_id,
            "status": "report_generated",
            "download_url": f"/api/v1/analysis/{application_id}/report/download",
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/{application_id}/report/download")
async def download_report(application_id: str):
    """Download the investment report .docx."""
    filepath = os.path.join("downloads", "investment_reports", f"{application_id}_investment_report.docx")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found — generate it first")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{application_id}_investment_report.docx",
    )
