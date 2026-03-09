from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import traceback

from core.database import get_db
from models.application import Application
from models.uploaded_document import UploadedDocument
from models.research_result import ResearchResult
from models.due_diligence_note import DueDiligenceNote
from pillar1_ingestor.data_normalizer import DataNormalizer
from pillar1_ingestor.cross_verification_engine import CrossVerificationEngine
from pillar3_recommendation.credit_scorer_fixed import CreditScorerFixed

router = APIRouter()


def _safe_json(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


@router.post("/calculate-score")
async def calculate_score(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Calculate credit score using the 5-Cs rule-based engine.
    Pulls real data from parsed documents, research results, due diligence.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    try:
        # ---- Gather financial data from parsed documents ----
        documents = db.query(UploadedDocument).filter(
            UploadedDocument.application_id == application_id,
            UploadedDocument.parse_status == "COMPLETED"
        ).all()

        normalizer = DataNormalizer()
        doc_records = [{"document_type": d.document_type, "parsed_data": d.parsed_data} for d in documents]
        normalized = normalizer.normalize(doc_records)

        gst = normalized.get("gst", {})
        bank = normalized.get("bank", {})
        annual = normalized.get("annual_report", {})

        # Cross-verification for GST-Bank variance
        cv_engine = CrossVerificationEngine()
        cv_result = cv_engine.run_verification(normalized)
        fraud_score = cv_result.get("fraud_risk_score", 0)

        # Build financials dict for scorer
        gst_sales = gst.get("sales_cr", 0) or 0
        bank_inflows = bank.get("total_inflows_cr", 0) or 0
        gst_variance = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0

        ar_debt = annual.get("total_debt_cr", 0) or 0
        ar_equity = annual.get("total_equity_cr", 0) or 0
        debt_to_equity = ar_debt / ar_equity if ar_equity > 0 else 1.0

        financials = {
            "dscr": application.dscr or 1.0,
            "current_ratio": application.current_ratio or 1.0,
            "gst_vs_bank_variance": round(gst_variance, 2),
            "debt_to_equity": round(debt_to_equity, 2),
        }

        # ---- Gather research findings ----
        research_rows = db.query(ResearchResult).filter(
            ResearchResult.application_id == application_id
        ).all()

        litigation_count = 0
        promoter_sentiment = "Neutral"
        sector_sentiment = "Neutral"
        overall_research_risk = 0
        for r in research_rows:
            if r.research_type in ("litigation", "ecourt"):
                lit_data = _safe_json(r.findings_json)
                litigation_count += lit_data.get("total_cases", 0) or (1 if r.risk_level == "HIGH" else 0)
            if r.research_type == "promoter":
                if r.sentiment:
                    promoter_sentiment = r.sentiment.capitalize()
            if r.research_type == "sector":
                if r.sentiment:
                    sector_sentiment = r.sentiment.capitalize()
            overall_research_risk += r.severity_penalty or 0

        research_data = {
            "litigation_count": litigation_count,
            "litigation_severity": "High" if overall_research_risk > 20 else "Low",
            "promoter_sentiment": promoter_sentiment,
            "circular_trading_risk_score": fraud_score,
            "sector_sentiment": sector_sentiment,
        }

        sector_data = {
            "sector_risk_score": min(100, max(0, overall_research_risk)),
        }

        # ---- Gather due diligence notes ----
        dd_notes_rows = db.query(DueDiligenceNote).filter(
            DueDiligenceNote.application_id == application_id
        ).all()

        dd_data = {}
        if dd_notes_rows:
            worst = max(dd_notes_rows, key=lambda d: abs(d.score_adjustment or 0))
            dd_data = {
                "notes": worst.ai_summary or worst.credit_officer_notes or "",
                "severity": worst.severity or "None",
            }

        # ---- Calculate score ----
        scorer = CreditScorerFixed()
        result = scorer.calculate_credit_score({
            "financials": financials,
            "research": research_data,
            "due_diligence": dd_data,
            "sector": sector_data,
            "requested_limit_cr": application.requested_limit_cr or 10.0,
        })

        # Update application with results
        application.final_credit_score = result["final_credit_score"]
        application.decision = result["decision"]
        application.recommended_limit_cr = result.get("recommended_limit_cr", 0)
        db.commit()

        return {
            "application_id": application_id,
            "company_name": application.company_name,
            "status": "scoring_complete",
            **result,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@router.get("/{application_id}/explainability")
async def get_explainability(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get explainability details for a scoring decision — re-runs scorer to get explanations."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    return {
        "application_id": application_id,
        "final_credit_score": application.final_credit_score,
        "decision": application.decision,
        "hint": "Run POST /calculate-score first for full explanations",
    }
