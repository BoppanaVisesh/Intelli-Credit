"""
Fraud Detection API Routes
Runs the full cross-verification + ML + circular trading pipeline.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import traceback

from api.dependencies import get_db
from models.application import Application
from models.uploaded_document import UploadedDocument
from pillar1_ingestor.data_normalizer import DataNormalizer
from pillar1_ingestor.cross_verification_engine import CrossVerificationEngine
from pillar1_ingestor.circular_trading_detector import CircularTradingDetector
from ml.fraud_model import predict_fraud, extract_features

router = APIRouter()


@router.post("/run-verification/{application_id}")
async def run_fraud_verification(application_id: str, db: Session = Depends(get_db)):
    """
    Run the full fraud verification pipeline for an application:
    1. Normalize parsed document data
    2. Run 14 cross-verification rules
    3. Run circular trading detection (ratio + graph)
    4. Run ML fraud prediction
    5. Compute combined fraud risk score
    """
    # Verify application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    # Fetch all parsed documents for this application
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.application_id == application_id,
        UploadedDocument.parse_status == "COMPLETED"
    ).all()

    if not documents:
        raise HTTPException(status_code=400, detail="No parsed documents found. Run document ingestion first.")

    doc_records = []
    for doc in documents:
        doc_records.append({
            "document_type": doc.document_type,
            "parsed_data": doc.parsed_data,
        })

    try:
        # Step 1: Normalize data
        normalizer = DataNormalizer()
        normalized = normalizer.normalize(doc_records)

        # Step 2: Cross-verification rules (14 rules)
        cv_engine = CrossVerificationEngine()
        cv_result = cv_engine.run_verification(normalized)

        # Step 3: Circular trading detection
        gst = normalized.get("gst", {})
        bank = normalized.get("bank", {})
        ct_detector = CircularTradingDetector()
        ct_result = ct_detector.full_analysis(
            gst_sales=gst.get("sales_cr", 0) or 0,
            bank_inflows=bank.get("total_inflows_cr", 0) or 0,
            gst_purchases=gst.get("purchases_cr", 0) or 0,
            bank_outflows=bank.get("total_outflows_cr", 0) or 0,
            transactions=[],  # No individual transaction data yet
        )

        # Step 4: ML prediction
        ml_result = predict_fraud(normalized)

        # Step 5: Combined fraud risk score
        rule_score = cv_result.get("fraud_risk_score", 0)
        ct_score = ct_result.get("combined_risk_score", 0)
        ml_score = ml_result.get("ml_score", 0)

        # Weighted combination: Rules 40%, ML 35%, Circular Trading 25%
        combined_score = round(rule_score * 0.40 + ml_score * 0.35 + ct_score * 0.25, 1)
        combined_score = min(100, max(0, combined_score))

        if combined_score >= 60:
            overall_risk = "CRITICAL"
        elif combined_score >= 40:
            overall_risk = "HIGH"
        elif combined_score >= 20:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        # All flags combined
        all_flags = (
            [a.get("detail", a.get("rule", "Unknown anomaly")) for a in cv_result.get("anomalies", [])]
            + ct_result.get("all_flags", [])
        )

        # Update application with fraud results
        application.circular_trading_risk = ct_result.get("combined_risk_level", "LOW")
        application.red_flag_triggered = combined_score >= 50
        application.gst_vs_bank_variance_percent = ct_result.get("ratio_analysis", {}).get("gst_vs_bank_variance_percent", 0)
        db.commit()

        result = {
            "application_id": application_id,
            "company_name": application.company_name,
            "status": "verification_complete",
            "combined_fraud_score": combined_score,
            "overall_risk_level": overall_risk,
            "red_flag_triggered": combined_score >= 50,
            "total_flags": len(all_flags),
            "all_flags": all_flags,
            "normalized_data_summary": {
                "sources_available": normalized.get("sources_available", []),
                "gst_sales_cr": gst.get("sales_cr", 0),
                "bank_inflows_cr": bank.get("total_inflows_cr", 0),
                "annual_revenue_cr": normalized.get("annual_report", {}).get("revenue_cr", 0),
            },
            "cross_verification": {
                "rule_score": cv_result.get("fraud_risk_score", 0),
                "risk_level": cv_result.get("risk_level", "LOW"),
                "anomalies_count": len(cv_result.get("anomalies", [])),
                "anomalies": cv_result.get("anomalies", []),
                "category_scores": cv_result.get("category_scores", {}),
                "summary": cv_result.get("summary", ""),
            },
            "circular_trading": {
                "combined_score": ct_result.get("combined_risk_score", 0),
                "risk_level": ct_result.get("combined_risk_level", "LOW"),
                "flags": ct_result.get("all_flags", []),
                "ratio_analysis": ct_result.get("ratio_analysis", {}),
                "graph_analysis": ct_result.get("graph_analysis", {}),
            },
            "ml_prediction": {
                "fraud_probability": ml_result.get("fraud_probability", 0),
                "prediction": ml_result.get("prediction", "LEGITIMATE"),
                "ml_risk_level": ml_result.get("ml_risk_level", "LOW"),
                "ml_score": ml_result.get("ml_score", 0),
                "top_features": ml_result.get("top_features", []),
            },
            "weight_breakdown": {
                "rules_weight": "40%",
                "ml_weight": "35%",
                "circular_trading_weight": "25%",
                "rules_contribution": round(rule_score * 0.40, 1),
                "ml_contribution": round(ml_score * 0.35, 1),
                "ct_contribution": round(ct_score * 0.25, 1),
            },
        }
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fraud verification failed: {str(e)}")


@router.get("/{application_id}/results")
async def get_fraud_results(application_id: str, db: Session = Depends(get_db)):
    """
    Get cached fraud analysis results for an application.
    If no previous results, runs the verification on-the-fly.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    # Return what we have from the application record
    return {
        "application_id": application_id,
        "company_name": application.company_name,
        "circular_trading_risk": application.circular_trading_risk or "NOT_RUN",
        "red_flag_triggered": application.red_flag_triggered or False,
        "gst_vs_bank_variance_percent": application.gst_vs_bank_variance_percent or 0,
        "hint": "Run POST /run-verification/{application_id} for full analysis"
    }
