"""Test just the 2 LLM calls with a gap"""
import requests, time, json

BASE = "http://localhost:8000/api/v1"

# Create app
r = requests.post(f"{BASE}/applications/", json={
    "company_name": "TestCorp", "requested_limit_cr": 50,
    "mca_cin": "U12345MH2020PTC000001", "sector": "Manufacturing"
})
app_id = r.json()["application_id"]
print(f"App: {app_id}")

# Call 1 - Site Visit
print("\n=== CALL 1: Site Visit ===")
r1 = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": app_id,
    "insight_type": "site_visit",
    "credit_officer_notes": "Visited factory in Gurgaon. Operations active. Fleet maintenance fair."
})
d1 = r1.json()
analysis1 = d1["ai_analysis"]
print(f"Confidence: {analysis1['confidence']}")
print(f"Risk: {analysis1['risk_category']}")
print(f"Score: {analysis1['score_adjustment']}")

print("\nWaiting 8 seconds...")
time.sleep(8)

# Call 2 - Interview
print("\n=== CALL 2: Interview ===")
r2 = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": app_id,
    "insight_type": "management_interview",
    "credit_officer_notes": "Interviewed CEO Ajay Singh. Confident about recovery. Revenue targets met."
})
d2 = r2.json()
analysis2 = d2["ai_analysis"]
print(f"Confidence: {analysis2['confidence']}")
print(f"Risk: {analysis2['risk_category']}")
print(f"Score: {analysis2['score_adjustment']}")

print("\nDONE!")
