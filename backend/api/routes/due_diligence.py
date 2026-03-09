from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import time

from core.database import get_db
from core.config import get_settings
from models.due_diligence_note import DueDiligenceNote
from models.application import Application
from services.llm_service import get_llm_service

router = APIRouter()


# Provider preference order: try Gemini first (free), fallback to OpenAI
LLM_PROVIDERS = ["gemini", "openai"]


class InsightRequest(BaseModel):
    application_id: str
    insight_type: str = "general"  # site_visit, management_interview, observation, general
    credit_officer_notes: str


class BulkInsightRequest(BaseModel):
    application_id: str
    insights: List[InsightRequest]


ANALYSIS_PROMPT = """You are a senior credit risk analyst. Analyze the following due diligence observation from a credit officer's field visit / management interview / site inspection.

**Insight Type:** {insight_type}
**Officer's Notes:**
{notes}

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "summary": "2-3 sentence executive summary of the observation",
  "risk_category": "one of: Operational, Governance, Financial, Management, Compliance, Infrastructure, Market",
  "severity": "one of: HIGH, MEDIUM, LOW",
  "sentiment": "one of: POSITIVE, NEGATIVE, NEUTRAL",
  "score_adjustment": <integer from -20 to +5>,
  "confidence": <float 0.0 to 1.0>,
  "risk_flags": ["list of specific risk flags identified"],
  "entities": ["list of key entities: people names, org names, locations mentioned"]
}}

Scoring guide:
- Positive observations (good capacity, strong governance): +1 to +5
- Neutral/minor observations: 0
- Moderate concerns (partial capacity issues, minor gaps): -3 to -8
- Serious concerns (fraud indicators, governance failures): -10 to -20"""


@router.post("/add-notes")
async def add_due_diligence_notes(
    request: InsightRequest,
    db: Session = Depends(get_db)
):
    """
    Add a primary insight from credit officer with AI-powered analysis.
    Processes: Notes → LLM summarization → Sentiment analysis → Risk flags → Score adjustment
    """
    # Validate application exists
    application = db.query(Application).filter(
        Application.id == request.application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {request.application_id} not found")

    # Run LLM analysis
    print(f"\n🔍 Analyzing primary insight for {request.application_id}...")
    print(f"   Type: {request.insight_type}")
    print(f"   Notes length: {len(request.credit_officer_notes)} chars")

    ai_analysis = None
    try:
        prompt = ANALYSIS_PROMPT.format(
            insight_type=request.insight_type.replace("_", " ").title(),
            notes=request.credit_officer_notes,
        )
        
        # Try each provider in order
        last_error = None
        for provider_name in LLM_PROVIDERS:
            try:
                llm = get_llm_service(provider_name)
                # Retry up to 3 times with increasing delay for rate-limits / truncation
                for attempt in range(3):
                    try:
                        raw_response = llm.generate_text(
                            prompt=prompt,
                            temperature=0.2,
                            max_tokens=8000,
                            json_mode=True,
                        )
                    except Exception as api_err:
                        err_str = str(api_err)
                        # Handle rate limiting with retry
                        if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                            if attempt < 2:
                                # Extract retry delay from error if available, otherwise use escalating delay
                                import re
                                delay_match = re.search(r'retry in (\d+(?:\.\d+)?)', err_str)
                                delay = float(delay_match.group(1)) + 2 if delay_match else 20 * (attempt + 1)
                                print(f"   -- {provider_name} rate limited, retrying in {delay:.0f}s (attempt {attempt+1}/3)...")
                                time.sleep(delay)
                                continue
                        raise  # Non-rate-limit error, propagate
                    
                    print(f"   Raw response ({provider_name}, attempt {attempt+1}): {len(raw_response)} chars")
                    # Robust JSON extraction
                    cleaned = raw_response.strip()
                    # Remove markdown code blocks
                    if "```json" in cleaned:
                        cleaned = cleaned.split("```json", 1)[1]
                        cleaned = cleaned.split("```", 1)[0]
                    elif "```" in cleaned:
                        parts = cleaned.split("```")
                        for part in parts:
                            part = part.strip()
                            if part.startswith("{"):
                                cleaned = part
                                break
                        else:
                            cleaned = parts[1] if len(parts) > 1 else cleaned
                    
                    cleaned = cleaned.strip()
                    if not cleaned.startswith("{"):
                        idx = cleaned.find("{")
                        if idx != -1:
                            cleaned = cleaned[idx:]
                    if cleaned.startswith("{"):
                        depth = 0
                        end_idx = 0
                        for i, ch in enumerate(cleaned):
                            if ch == "{":
                                depth += 1
                            elif ch == "}":
                                depth -= 1
                                if depth == 0:
                                    end_idx = i + 1
                                    break
                        if end_idx > 0:
                            cleaned = cleaned[:end_idx]
                    
                    try:
                        ai_analysis = json.loads(cleaned)
                        print(f"   AI Analysis ({provider_name}): {ai_analysis['risk_category']} / {ai_analysis['severity']} / {ai_analysis['score_adjustment']} pts")
                        break  # JSON parsed successfully
                    except json.JSONDecodeError as json_err:
                        if attempt < 2:
                            delay = 8 * (attempt + 1)
                            print(f"   -- {provider_name} attempt {attempt+1} JSON truncated, retrying after {delay}s...")
                            time.sleep(delay)
                            continue
                        else:
                            raise json_err
                
                if ai_analysis is not None:
                    break  # Success, stop trying providers
            except Exception as provider_err:
                last_error = provider_err
                print(f"   ⚠️  {provider_name} failed: {provider_err}")
                continue
        
        if ai_analysis is None:
            raise Exception(f"All LLM providers failed. Last error: {last_error}")
            
    except Exception as e:
        print(f"   ⚠️  LLM analysis failed: {e}")
        ai_analysis = {
            "summary": request.credit_officer_notes[:200],
            "risk_category": "Operational",
            "severity": "MEDIUM",
            "sentiment": "NEUTRAL",
            "score_adjustment": -3,
            "confidence": 0.3,
            "risk_flags": [],
            "entities": [],
        }

    # Store in DB
    note = DueDiligenceNote(
        application_id=request.application_id,
        insight_type=request.insight_type,
        credit_officer_notes=request.credit_officer_notes,
        ai_summary=ai_analysis.get("summary", ""),
        risk_category=ai_analysis.get("risk_category", "Operational"),
        severity=ai_analysis.get("severity", "MEDIUM"),
        score_adjustment=ai_analysis.get("score_adjustment", -3),
        sentiment=ai_analysis.get("sentiment", "NEUTRAL"),
        confidence=ai_analysis.get("confidence", 0.5),
        risk_flags_json=json.dumps(ai_analysis.get("risk_flags", [])),
        entities_json=json.dumps(ai_analysis.get("entities", [])),
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "id": note.id,
        "application_id": request.application_id,
        "status": "analyzed",
        "insight_type": request.insight_type,
        "ai_analysis": {
            "summary": ai_analysis.get("summary", ""),
            "risk_category": ai_analysis.get("risk_category"),
            "severity": ai_analysis.get("severity"),
            "sentiment": ai_analysis.get("sentiment"),
            "score_adjustment": ai_analysis.get("score_adjustment"),
            "confidence": ai_analysis.get("confidence"),
            "risk_flags": ai_analysis.get("risk_flags", []),
            "entities": ai_analysis.get("entities", []),
        },
    }


@router.get("/{application_id}/notes")
async def get_due_diligence_notes(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get all primary insights for an application with aggregated risk."""
    notes = (
        db.query(DueDiligenceNote)
        .filter(DueDiligenceNote.application_id == application_id)
        .order_by(DueDiligenceNote.created_at.desc())
        .all()
    )

    total_adjustment = sum(n.score_adjustment or 0 for n in notes)
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for n in notes:
        sev = n.severity or "LOW"
        if sev in severity_counts:
            severity_counts[sev] += 1

    all_flags = []
    for n in notes:
        if n.risk_flags_json:
            try:
                all_flags.extend(json.loads(n.risk_flags_json))
            except json.JSONDecodeError:
                pass

    return {
        "application_id": application_id,
        "total_insights": len(notes),
        "total_score_adjustment": total_adjustment,
        "severity_breakdown": severity_counts,
        "all_risk_flags": list(set(all_flags)),
        "notes": [
            {
                "id": note.id,
                "insight_type": note.insight_type,
                "notes": note.credit_officer_notes,
                "ai_summary": note.ai_summary,
                "risk_category": note.risk_category,
                "severity": note.severity,
                "sentiment": note.sentiment,
                "score_adjustment": note.score_adjustment,
                "confidence": note.confidence,
                "risk_flags": json.loads(note.risk_flags_json) if note.risk_flags_json else [],
                "entities": json.loads(note.entities_json) if note.entities_json else [],
                "created_at": str(note.created_at) if note.created_at else None,
            }
            for note in notes
        ],
    }


@router.delete("/{application_id}/notes/{note_id}")
async def delete_due_diligence_note(
    application_id: str,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific insight note."""
    note = db.query(DueDiligenceNote).filter(
        DueDiligenceNote.id == note_id,
        DueDiligenceNote.application_id == application_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"status": "deleted", "id": note_id}
