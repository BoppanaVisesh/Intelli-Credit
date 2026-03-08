from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.due_diligence_note import DueDiligenceNote
from schemas.application import DueDiligenceNoteRequest

router = APIRouter()


@router.post("/add-notes")
async def add_due_diligence_notes(
    request: DueDiligenceNoteRequest,
    db: Session = Depends(get_db)
):
    """
    Add due diligence notes from credit officer.
    AI will translate these into risk adjustments.
    """
    note = DueDiligenceNote(
        application_id=request.application_id,
        credit_officer_notes=request.credit_officer_notes,
        risk_category="Operational",  # AI will determine this
        severity="MEDIUM",
        score_adjustment=-5
    )
    db.add(note)
    db.commit()
    
    return {
        "application_id": request.application_id,
        "status": "notes_added",
        "ai_analysis": {
            "risk_category": "Operational",
            "severity": "MEDIUM",
            "score_adjustment": -5
        }
    }


@router.get("/{application_id}/notes")
async def get_due_diligence_notes(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get all due diligence notes for an application"""
    notes = db.query(DueDiligenceNote).filter(
        DueDiligenceNote.application_id == application_id
    ).all()
    
    return {
        "application_id": application_id,
        "notes": [
            {
                "id": note.id,
                "notes": note.credit_officer_notes,
                "risk_category": note.risk_category,
                "severity": note.severity,
                "score_adjustment": note.score_adjustment,
                "created_at": note.created_at
            }
            for note in notes
        ]
    }
