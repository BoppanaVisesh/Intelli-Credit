from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()


@router.post("/calculate-score")
async def calculate_score(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Calculate credit score using ML model.
    This will be connected to Pillar 3 scoring engine.
    """
    return {
        "application_id": application_id,
        "status": "scoring_complete",
        "score": 58,
        "decision": "REJECT"
    }


@router.get("/{application_id}/explainability")
async def get_explainability(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get SHAP explainability for a scoring decision"""
    return {
        "application_id": application_id,
        "shap_values": [],
        "feature_importance": []
    }
