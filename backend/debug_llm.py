"""Debug Gemini response"""
from services.llm_service import get_llm_service
import json

llm = get_llm_service("gemini")
print(f"Model: {llm.model}")

prompt = """You are a credit analyst. Analyze this observation:
Site visit found stressed cash reserves and low employee morale at the company office.

Respond ONLY with valid JSON (no markdown, no code blocks):
{"summary": "2-3 sentence summary", "risk_category": "one of: Operational, Governance, Financial", "severity": "HIGH or MEDIUM or LOW", "sentiment": "POSITIVE or NEGATIVE or NEUTRAL", "score_adjustment": -5, "confidence": 0.8, "risk_flags": ["list of flags"], "entities": ["list of entities"]}"""

raw = llm.generate_text(prompt=prompt, temperature=0.2, max_tokens=2000)
print(f"RAW LENGTH: {len(raw)}")
print(f"RAW RESPONSE:\n---\n{raw}\n---")

# Try to parse
try:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            p = part.strip()
            if p.startswith("{"):
                cleaned = p
                break
    
    cleaned = cleaned.strip()
    if not cleaned.startswith("{"):
        idx = cleaned.find("{")
        if idx != -1:
            cleaned = cleaned[idx:]
    
    result = json.loads(cleaned)
    print(f"\nPARSED OK: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"\nPARSE ERROR: {e}")
    print(f"CLEANED: {repr(cleaned[:300])}")
