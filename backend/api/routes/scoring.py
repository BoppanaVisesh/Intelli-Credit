"""
Scoring API — Full credit assessment pipeline:
  1. Normalize parsed documents
  2. Cross-verification for fraud score
  3. Five Cs credit scoring (Character 20%, Capacity 30%, Capital 20%, Collateral 20%, Conditions 10%)
  4. Loan limit recommendation (revenue × 0.25, cashflow × 4, collateral × 0.7 → min)
  5. Interest rate (≥80→10%, 70-79→11.5%, 60-69→13%, <60→Reject)
  6. Explainable decision reasons
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import traceback

from core.database import get_db
from models.application import Application, ApplicationStatus
from models.uploaded_document import UploadedDocument
from models.research_result import ResearchResult
from models.due_diligence_note import DueDiligenceNote
from pillar1_ingestor.data_normalizer import DataNormalizer
from pillar1_ingestor.cross_verification_engine import CrossVerificationEngine
from pillar3_recommendation.credit_scorer_fixed import CreditScorerFixed
from pillar3_recommendation.loan_limit_engine import LoanLimitEngine
from pillar3_recommendation.risk_premium_calculator import RiskPremiumCalculator
from pillar3_recommendation.explainability import Explainability
from services.financial_snapshot import build_financials

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
async def calculate_score(application_id: str, db: Session = Depends(get_db)):
    """Full credit assessment: 5-Cs + loan limit + interest rate + reasons."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    try:
        # ── 1. Normalize parsed documents ─────────────────────────
        documents = db.query(UploadedDocument).filter(
            UploadedDocument.application_id == application_id,
            UploadedDocument.parse_status == "COMPLETED",
        ).all()

        normalizer = DataNormalizer()
        doc_records = [{"document_type": d.document_type, "parsed_data": d.parsed_data} for d in documents]
        normalized = normalizer.normalize(doc_records)

        if not documents:
            print(f"   ⚠ WARNING: No parsed documents found for {application_id} — scoring will use defaults")

        gst = normalized.get("gst", {})
        bank = normalized.get("bank", {})
        shareholding = normalized.get("shareholding", {})
        liquidity = normalized.get("liquidity", {})

        # ── 2. Cross-verification ─────────────────────────────────
        cv_engine = CrossVerificationEngine()
        cv_result = cv_engine.run_verification(normalized)
        fraud_score = cv_result.get("fraud_risk_score", 0)

        gst_sales     = gst.get("sales_cr", 0) or 0
        bank_inflows  = bank.get("total_inflows_cr", 0) or 0
        bank_outflows = bank.get("total_outflows_cr", 0) or 0
        gst_variance  = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0

        financials = build_financials(application, normalized)

        # ── 3. Research findings ──────────────────────────────────
        research_rows = db.query(ResearchResult).filter(
            ResearchResult.application_id == application_id
        ).all()

        litigation_count = 0
        promoter_sentiment = "Neutral"
        sector_sentiment = "Neutral"
        overall_research_risk = 0
        litigation_cases = []
        for r in research_rows:
            if r.research_type in ("litigation", "ecourt"):
                lit_data = _safe_json(r.findings_json)
                litigation_count += lit_data.get("total_cases", 0) or (1 if r.risk_level == "HIGH" else 0)
                if r.findings_summary:
                    litigation_cases.append({"summary": r.findings_summary})
            if r.research_type == "promoter" and r.sentiment:
                promoter_sentiment = r.sentiment.capitalize()
            if r.research_type == "sector" and r.sentiment:
                sector_sentiment = r.sentiment.capitalize()
            overall_research_risk += r.severity_penalty or 0

        research_data = {
            "litigation_count": litigation_count,
            "litigation_severity": "High" if overall_research_risk > 20 else "Low",
            "promoter_sentiment": promoter_sentiment,
            "circular_trading_risk_score": fraud_score,
            "sector_sentiment": sector_sentiment,
            "litigation_cases": litigation_cases,
        }

        sector_data = {"sector_risk_score": min(100, max(0, overall_research_risk))}

        # ── 4. Due diligence notes ────────────────────────────────
        dd_rows = db.query(DueDiligenceNote).filter(
            DueDiligenceNote.application_id == application_id
        ).all()

        dd_data = {}
        if dd_rows:
            worst = max(dd_rows, key=lambda d: abs(d.score_adjustment or 0))
            dd_data = {
                "notes": worst.ai_summary or worst.credit_officer_notes or "",
                "severity": worst.severity or "None",
            }

        requested_limit = application.requested_limit_cr or 10.0

        # ── 5. Five Cs credit scoring ─────────────────────────────
        scorer = CreditScorerFixed()
        scoring_result = scorer.calculate_credit_score({
            "financials": financials,
            "research": research_data,
            "due_diligence": dd_data,
            "sector": sector_data,
            "collateral": {},
            "requested_limit_cr": requested_limit,
        })

        credit_score = scoring_result["final_credit_score"]
        decision = scoring_result["decision"]

        # ── 6. Loan limit recommendation ──────────────────────────
        loan_engine = LoanLimitEngine()
        loan_result = loan_engine.calculate_loan_limit(financials, credit_score, requested_limit)

        # ── 7. Interest rate ──────────────────────────────────────
        rate_calc = RiskPremiumCalculator()
        rate_result = rate_calc.calculate(
            credit_score=credit_score,
            dscr=financials["dscr"],
            sector_risk_score=sector_data["sector_risk_score"],
            litigation_count=litigation_count,
        )

        # ── 8. Explainable reasons ────────────────────────────────
        explainer = Explainability()
        reasons = explainer.generate_reasons({
            "financials": financials,
            "research": research_data,
            "scoring": scoring_result,
        })
        narrative = explainer.generate_narrative(decision, reasons, credit_score)

        # ── Persist ───────────────────────────────────────────────
        application.final_credit_score = credit_score
        application.decision = decision
        application.recommended_limit_cr = loan_result["recommended_limit_cr"]
        application.status = ApplicationStatus.COMPLETED
        db.commit()

        return {
            "application_id": application_id,
            "company_name": application.company_name,
            "status": "scoring_complete",
            **scoring_result,
            "loan_recommendation": loan_result,
            "interest_rate": rate_result,
            "decision_reasons": reasons,
            "narrative": narrative,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@router.get("/{application_id}/explainability")
async def get_explainability(application_id: str, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    return {
        "application_id": application_id,
        "final_credit_score": application.final_credit_score,
        "decision": application.decision,
        "hint": "Run POST /calculate-score first for full explanations",
    }
