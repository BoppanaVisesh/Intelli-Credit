"""Debug: test back-to-back Gemini calls with json_mode"""
import os, time, json
import google.generativeai as genai

# Read key from .env
with open('.env') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY='):
            key = line.strip().split('=',1)[1]
            genai.configure(api_key=key)

model = genai.GenerativeModel('gemini-2.5-flash')

prompt1 = """You are a senior credit risk analyst. Analyze this:
**Insight Type:** Site Visit
**Officer's Notes:** Visited SpiceJet HQ in Gurgaon. Operations active. Fleet maintenance fair.

Respond ONLY with valid JSON:
{"summary": "brief", "risk_category": "Financial", "severity": "MEDIUM", "sentiment": "NEUTRAL", "score_adjustment": -5, "confidence": 0.8, "risk_flags": [], "entities": []}"""

prompt2 = """You are a senior credit risk analyst. Analyze this:
**Insight Type:** Management Interview
**Officer's Notes:** Interviewed CEO Ajay Singh. Confident about recovery plan. Revenue targets achieved. Plans to add 10 aircraft next year.

Respond ONLY with valid JSON:
{"summary": "brief", "risk_category": "Management", "severity": "LOW", "sentiment": "POSITIVE", "score_adjustment": 3, "confidence": 0.9, "risk_flags": [], "entities": []}"""

config = genai.GenerationConfig(
    max_output_tokens=2000,
    temperature=0.2,
    response_mime_type="application/json"
)

print("=== CALL 1 ===")
r1 = model.generate_content(prompt1, generation_config=config)
print(f"Finish reason: {r1.candidates[0].finish_reason}")
print(f"Length: {len(r1.text)} chars")
print(f"Text: {r1.text[:500]}")
try:
    parsed1 = json.loads(r1.text)
    print(f"Parsed OK: {list(parsed1.keys())}")
except json.JSONDecodeError as e:
    print(f"JSON PARSE FAILED: {e}")

print()
print("Waiting 5 seconds...")
time.sleep(5)

print()
print("=== CALL 2 ===")
try:
    r2 = model.generate_content(prompt2, generation_config=config)
    print(f"Finish reason: {r2.candidates[0].finish_reason}")
    print(f"Length: {len(r2.text)} chars")
    print(f"Text: {r2.text[:500]}")
    try:
        parsed2 = json.loads(r2.text)
        print(f"Parsed OK: {list(parsed2.keys())}")
    except json.JSONDecodeError as e:
        print(f"JSON PARSE FAILED: {e}")
except Exception as e:
    print(f"CALL 2 ERROR: {type(e).__name__}: {e}")

print()
print("DONE!")
