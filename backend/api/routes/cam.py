"""
CAM API — Generate & Download Credit Appraisal Memo

POST /generate       → build full CAM .docx (with optional LLM narrative)
GET  /{id}/download  → download the .docx
GET  /{id}/preview   → JSON preview of CAM sections
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
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
from pillar3_recommendation.loan_limit_engine import LoanLimitEngine
from pillar3_recommendation.risk_premium_calculator import RiskPremiumCalculator
from pillar3_recommendation.explainability import Explainability
from pillar3_recommendation.cam_generator import CAMGenerator
from services.llm_service import get_llm_service

router = APIRouter()
cam_gen = CAMGenerator()


def _safe_json(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def _gather_cam_data(application_id: str, db: Session) -> dict:
    """Gather all data needed for CAM from DB, run scoring if needed."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Parsed documents
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.application_id == application_id,
        UploadedDocument.parse_status == "COMPLETED",
    ).all()

    normalizer = DataNormalizer()
    doc_records = [{"document_type": d.document_type, "parsed_data": d.parsed_data} for d in documents]
    normalized = normalizer.normalize(doc_records)

    gst    = normalized.get("gst", {})
    bank   = normalized.get("bank", {})
    annual = normalized.get("annual_report", {})

    cv_engine = CrossVerificationEngine()
    cv_result = cv_engine.run_verification(normalized)
    fraud_score = cv_result.get("fraud_risk_score", 0)

    gst_sales     = gst.get("sales_cr", 0) or 0
    bank_inflows  = bank.get("total_inflows_cr", 0) or 0
    bank_outflows = bank.get("total_outflows_cr", 0) or 0
    gst_variance  = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0
    ar_debt    = annual.get("total_debt_cr", 0) or 0
    ar_equity  = annual.get("total_equity_cr", 0) or 0
    ar_revenue = annual.get("revenue_cr", 0) or 0
    debt_to_equity = ar_debt / ar_equity if ar_equity > 0 else 1.0

    financials = {
        "dscr": app.dscr or 1.0,
        "current_ratio": app.current_ratio or 1.0,
        "gst_vs_bank_variance": round(gst_variance, 2),
        "debt_to_equity": round(debt_to_equity, 2),
        "revenue_cr": ar_revenue or gst_sales,
        "gst_sales_cr": gst_sales,
        "gst_3b_sales_cr": gst.get("gst_3b_sales_cr", gst_sales),
        "bank_inflows_cr": bank_inflows,
        "bank_outflows_cr": bank_outflows,
        "operating_cash_flow_cr": max(bank_inflows - bank_outflows, 0),
        "bounced_cheques": bank.get("bounced_cheques", 0),
        "overdraft_instances": bank.get("overdraft_instances", 0),
        "fixed_assets_cr": annual.get("fixed_assets_cr", 0),
        "total_assets_cr": annual.get("total_assets_cr", 0),
        "net_worth_cr": ar_equity,
    }

    # Research
    research_rows = db.query(ResearchResult).filter(
        ResearchResult.application_id == application_id
    ).all()

    litigation_count = 0
    promoter_sentiment = "Neutral"
    sector_sentiment = "Neutral"
    overall_risk = 0
    litigation_cases = []
    sector_narrative = ""
    for r in research_rows:
        if r.research_type in ("litigation", "ecourt"):
            lit_data = _safe_json(r.findings_json)
            litigation_count += lit_data.get("total_cases", 0) or (1 if r.risk_level == "HIGH" else 0)
            if r.findings_summary:
                litigation_cases.append({"summary": r.findings_summary})
        if r.research_type == "promoter" and r.sentiment:
            promoter_sentiment = r.sentiment.capitalize()
        if r.research_type == "sector":
            if r.sentiment:
                sector_sentiment = r.sentiment.capitalize()
            if r.findings_summary:
                sector_narrative = r.findings_summary
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

    # Due diligence
    dd_rows = db.query(DueDiligenceNote).filter(
        DueDiligenceNote.application_id == application_id
    ).all()
    dd_data = {}
    if dd_rows:
        worst = max(dd_rows, key=lambda d: abs(d.score_adjustment or 0))
        dd_data = {"notes": worst.ai_summary or worst.credit_officer_notes or "", "severity": worst.severity or "None"}

    requested_limit = app.requested_limit_cr or 10.0

    # Five Cs
    scorer = CreditScorerFixed()
    scoring = scorer.calculate_credit_score({
        "financials": financials, "research": research_data,
        "due_diligence": dd_data, "sector": sector_data,
        "collateral": {}, "requested_limit_cr": requested_limit,
    })

    # Loan limit
    loan = LoanLimitEngine().calculate_loan_limit(financials, scoring["final_credit_score"], requested_limit)

    # Interest
    rate = RiskPremiumCalculator().calculate(
        credit_score=scoring["final_credit_score"],
        dscr=financials["dscr"],
        sector_risk_score=sector_data["sector_risk_score"],
        litigation_count=litigation_count,
    )

    # Reasons
    explainer = Explainability()
    reasons = explainer.generate_reasons({"financials": financials, "research": research_data, "scoring": scoring})

    # Persist
    app.final_credit_score = scoring["final_credit_score"]
    app.decision = scoring["decision"]
    app.recommended_limit_cr = loan["recommended_limit_cr"]
    db.commit()

    return {
        "application_id": application_id,
        "company": {
            "company_name": app.company_name,
            "mca_cin": app.mca_cin,
            "sector": app.sector,
            "requested_limit_cr": requested_limit,
        },
        "financials": financials,
        "research": research_data,
        "conditions": {"sector_risk_score": sector_data["sector_risk_score"], "sector_narrative": sector_narrative},
        "scoring": scoring,
        "loan_recommendation": loan,
        "interest_rate": rate,
        "decision_reasons": reasons,
        "fraud": {"combined_score": fraud_score, "overall_risk": cv_result.get("risk_level", "UNKNOWN")},
    }


def _llm_narrative(cam_data: dict) -> str:
    """Call Gemini to write an executive-summary paragraph for the CAM."""
    try:
        llm = get_llm_service("gemini")
        company = cam_data["company"]["company_name"]
        sector = cam_data["company"]["sector"]
        score = cam_data["scoring"]["final_credit_score"]
        decision = cam_data["scoring"]["decision"]
        limit = cam_data["loan_recommendation"]["recommended_limit_cr"]
        rate_info = cam_data["interest_rate"]
        subs = cam_data["scoring"]["sub_scores"]
        reasons = cam_data["decision_reasons"]

        neg_reasons = [r["text"] for r in reasons if r["impact"] == "NEGATIVE"][:3]
        pos_reasons = [r["text"] for r in reasons if r["impact"] == "POSITIVE"][:3]

        prompt = f"""Generate a professional Credit Appraisal Memo executive summary (150-200 words) for:

Company: {company}
Sector: {sector}
Credit Score: {score}/100
Decision: {decision}
Recommended Loan: ₹{limit} Cr
Interest Rate: {rate_info.get('final_interest_rate', 'N/A')}%

Five Cs Assessment:
- Character: {subs.get('character', {}).get('score', '-')}/100
- Capacity: {subs.get('capacity', {}).get('score', '-')}/100
- Capital: {subs.get('capital', {}).get('score', '-')}/100
- Collateral: {subs.get('collateral', {}).get('score', '-')}/100
- Conditions: {subs.get('conditions', {}).get('score', '-')}/100

Positive: {'; '.join(pos_reasons) if pos_reasons else 'None'}
Risks: {'; '.join(neg_reasons) if neg_reasons else 'None'}

Write in formal banking language. Include financial analysis, risk commentary, and final recommendation. Do NOT use markdown."""

        narrative = llm.generate_text(prompt, max_tokens=2000, temperature=0.4)
        return narrative.strip()
    except Exception as e:
        print(f"[CAM] LLM narrative failed: {e}")
        return ""


class _CAMRequest(BaseModel):
    application_id: str

@router.post("/generate")
async def generate_cam(req: _CAMRequest, db: Session = Depends(get_db)):
    application_id = req.application_id
    """Generate CAM document (.docx) with all 10 sections + LLM narrative."""
    try:
        cam_data = _gather_cam_data(application_id, db)

        # LLM narrative (best-effort)
        llm_text = _llm_narrative(cam_data)
        if llm_text:
            cam_data["executive_summary"] = llm_text

        filepath = cam_gen.generate_cam(cam_data, llm_narrative=llm_text or None)

        # Persist CAM URL
        app = db.query(Application).filter(Application.id == application_id).first()
        if app:
            app.cam_document_url = f"/api/v1/cam/{application_id}/download"
            db.commit()

        return {
            "application_id": application_id,
            "status": "cam_generated",
            "document_url": f"/api/v1/cam/{application_id}/download",
            "scoring": cam_data["scoring"],
            "loan_recommendation": cam_data["loan_recommendation"],
            "interest_rate": cam_data["interest_rate"],
            "decision_reasons": cam_data["decision_reasons"],
            "executive_summary": llm_text or "See document for details.",
            "file_path": filepath,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"CAM generation failed: {str(e)}")


@router.get("/{application_id}/download")
async def download_cam(application_id: str, db: Session = Depends(get_db)):
    """Download generated CAM .docx."""
    filepath = os.path.join("./downloads/cam_reports", f"{application_id}.docx")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CAM not generated yet. Call POST /generate first.")
    return FileResponse(
        path=filepath,
        filename=f"CAM_{application_id}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{application_id}/preview")
async def preview_cam(application_id: str, db: Session = Depends(get_db)):
    """JSON preview of CAM data (without generating the .docx)."""
    try:
        cam_data = _gather_cam_data(application_id, db)
        explainer = Explainability()
        narrative = explainer.generate_narrative(
            cam_data["scoring"]["decision"],
            cam_data["decision_reasons"],
            cam_data["scoring"]["final_credit_score"],
        )
        return {
            "application_id": application_id,
            "company": cam_data["company"],
            "scoring": cam_data["scoring"],
            "loan_recommendation": cam_data["loan_recommendation"],
            "interest_rate": cam_data["interest_rate"],
            "decision_reasons": cam_data["decision_reasons"],
            "narrative": narrative,
            "sections": [
                "Executive Summary", "Company Profile", "Industry Analysis",
                "Financial Analysis", "Bank Statement Analysis", "GST Compliance",
                "Litigation Check", "Five Cs Evaluation", "Risk Assessment",
                "Loan Recommendation",
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
