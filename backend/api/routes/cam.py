from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db
from models.application import Application
from pillar3_recommendation.cam_generator import CAMGenerator
import os
import json

router = APIRouter()
cam_generator = CAMGenerator()


@router.post("/generate")
async def generate_cam(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate Credit Appraisal Memo document.
    """
    
    # Get application from database
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if analysis is complete
    if not application.analysis_result:
        raise HTTPException(
            status_code=400,
            detail="Credit analysis not completed. Run analysis first."
        )
    
    try:
        # Parse analysis result
        analysis_data = json.loads(application.analysis_result)
        
        # Generate CAM document
        filepath = cam_generator.generate_cam(analysis_data)
        
        # Convert to PDF if needed (using python-docx2pdf or similar)
        # For now, keeping as DOCX
        
        return {
            "application_id": application_id,
            "status": "cam_generated",
            "document_url": f"/api/v1/cam/{application_id}/download",
            "executive_summary": analysis_data['cam_generation']['executive_summary'],
            "file_path": filepath
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CAM: {str(e)}"
        )


@router.get("/{application_id}/download")
async def download_cam(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Download generated CAM document"""
    
    # Check if CAM exists
    filename = f"{application_id}.docx"
    filepath = os.path.join('./downloads/cam_reports', filename)
    
    if not os.path.exists(filepath):
        # Try to generate it first
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application or not application.analysis_result:
            raise HTTPException(
                status_code=404,
                detail="CAM document not found. Generate it first."
            )
        
        # Generate CAM
        try:
            analysis_data = json.loads(application.analysis_result)
            filepath = cam_generator.generate_cam(analysis_data)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate CAM: {str(e)}"
            )
    
    # Return file
    return FileResponse(
        path=filepath,
        filename=f"CAM_{application_id}.docx",
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@router.get("/{application_id}/preview")
async def preview_cam(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get CAM preview data"""
    return {
        "application_id": application_id,
        "sections": {
            "executive_summary": "",
            "company_overview": "",
            "financial_analysis": "",
            "risk_assessment": "",
            "recommendation": ""
        }
    }
