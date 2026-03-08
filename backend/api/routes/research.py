from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()


@router.post("/trigger-research")
async def trigger_research(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger AI research agent for an application.
    This will be connected to Pillar 2 processors.
    """
    return {
        "application_id": application_id,
        "status": "research_initiated",
        "tasks": ["promoter_check", "litigation_search", "sector_analysis"]
    }


@router.get("/{application_id}/results")
async def get_research_results(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get research results for an application"""
    from models.application import Application
    from models.research_result import ResearchResult
    
    # Get application
    app = db.query(Application).filter(Application.id == application_id).first()
    
    if not app:
        return {
            "application_id": application_id,
            "error": "Application not found",
            "research_completed": False
        }
    
    # Get research results from database
    research_results = db.query(ResearchResult).filter(
        ResearchResult.application_id == application_id
    ).all()
    
    if not research_results:
        return {
            "application_id": application_id,
            "research_completed": False,
            "findings": {
                "promoter_checks": [],
                "litigation": [],
                "sector_analysis": "No research completed yet"
            },
            "note": "Run /applications/{application_id}/analyze to generate research"
        }
    
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
                "severity": result.risk_level
            })
        elif result.research_type == "sector":
            sector_info = result.findings_json.get("analysis", "")
    
    return {
        "application_id": application_id,
        "research_completed": True,
        "findings": {
            "promoter_checks": promoter_checks,
            "litigation": litigation,
            "sector_analysis": sector_info
        }
    }
