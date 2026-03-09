"""End-to-end test for External Intelligence Research pipeline."""
import requests
import json

BASE = "http://localhost:8000/api/v1"

# Step 1: Create application
print("=" * 60)
print("Step 1: Creating SpiceJet Application")
print("=" * 60)
app_resp = requests.post(f"{BASE}/applications", json={
    "company_name": "SpiceJet Limited",
    "mca_cin": "L51909DL1984PLC018603",
    "sector": "Aviation",
    "requested_limit_cr": 500.0,
})
print(f"Status: {app_resp.status_code}")
app_data = app_resp.json()
print(f"Response: {json.dumps(app_data, indent=2, default=str)[:500]}")
app_id = app_data.get("id") or app_data.get("application_id") or app_data.get("application", {}).get("id")
print(f"Application ID: {app_id}")

# Step 2: Trigger research
print()
print("=" * 60)
print("Step 2: Triggering External Intelligence Research")
print("(Calling Tavily API for real web searches - expect 15-30s)")
print("=" * 60)
research_resp = requests.post(f"{BASE}/research/trigger-research", json={
    "application_id": app_id,
    "company_name": "SpiceJet Limited",
    "sector": "Aviation",
    "promoter_names": ["Ajay Singh"],
})
print(f"Status: {research_resp.status_code}")
result = research_resp.json()
print(json.dumps(result, indent=2))

# Step 3: Fetch results
print()
print("=" * 60)
print("Step 3: Fetching Research Results (GET)")
print("=" * 60)
results_resp = requests.get(f"{BASE}/research/{app_id}/results")
print(f"Status: {results_resp.status_code}")
results_data = results_resp.json()

print(f"\nResearch Completed: {results_data['research_completed']}")
print(f"Overall Risk: {results_data['overall_risk']}")
print(f"Total Penalty: {results_data['total_penalty']}")
print(f"Result Count: {results_data['result_count']}")

for rtype, items in results_data["results_by_type"].items():
    print(f"\n--- {rtype.upper()} ---")
    for item in items:
        print(f"  Entity: {item['entity_name']}")
        print(f"  Risk: {item['risk_level']} | Sentiment: {item['sentiment']}")
        print(f"  Summary: {item['findings_summary'][:120]}...")
        print(f"  Penalty: {item['severity_penalty']}")
        print()

print("\n" + "=" * 60)
print("E2E TEST COMPLETE")
print(f"App ID for frontend testing: {app_id}")
print("=" * 60)
