"""End-to-end test for full pipeline: Application → Research → Primary Insights."""
import requests
import json

BASE = "http://localhost:8000/api/v1"

# ── Step 1: Create Application ──
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
app_id = app_data.get("application_id")
print(f"Application ID: {app_id}")

# ── Step 2: Get Application Summary (pipeline status) ──
print()
print("=" * 60)
print("Step 2: Application Summary (Pipeline Status)")
print("=" * 60)
summary_resp = requests.get(f"{BASE}/applications/{app_id}/summary")
print(f"Status: {summary_resp.status_code}")
summary = summary_resp.json()
print(f"Company: {summary['company_name']}")
print(f"Pipeline steps:")
for k, v in summary["pipeline"].items():
    print(f"  {k}: {v['status']}")

# ── Step 3: Trigger External Intelligence ──
print()
print("=" * 60)
print("Step 3: Running External Intelligence (Tavily API)")
print("(Expect 15-30 seconds)")
print("=" * 60)
research_resp = requests.post(f"{BASE}/research/trigger-research", json={
    "application_id": app_id,
    "company_name": "SpiceJet Limited",
    "sector": "Aviation",
    "promoter_names": ["Ajay Singh"],
})
print(f"Status: {research_resp.status_code}")
result = research_resp.json()
print(f"Overall Risk: {result['overall_risk']}")
print(f"Completed: {result['completed_tasks']}, Failed: {result['failed_tasks']}")
for r in result["results"]:
    print(f"  {r['type']}: {r['status']} - risk={r.get('risk', 'N/A')}")

# ── Step 4: Add Primary Insight (Site Visit) ──
print()
print("=" * 60)
print("Step 4: Adding Primary Insight - Site Visit Report")
print("=" * 60)
insight1_resp = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": app_id,
    "insight_type": "site_visit",
    "credit_officer_notes": (
        "Visited SpiceJet operational office at Gurgaon on March 5, 2026. "
        "Fleet of 50 aircraft, but only 32 are operational. 18 grounded due to Pratt & Whitney engine issues. "
        "Maintenance hangar at IGI airport was overcrowded. Staff morale appears low. "
        "Several senior pilots have resigned in last quarter. "
        "Office infrastructure is adequate but aging. "
        "Observed significant vendor payment delays - cleaning and catering contracts unpaid for 3 months."
    ),
})
print(f"Status: {insight1_resp.status_code}")
insight1 = insight1_resp.json()
print(f"AI Analysis: {json.dumps(insight1.get('ai_analysis', {}), indent=2)}")

# ── Step 5: Add Primary Insight (Management Interview) ──
print()
print("=" * 60)
print("Step 5: Adding Primary Insight - Management Interview")
print("=" * 60)
insight2_resp = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": app_id,
    "insight_type": "management_interview",
    "credit_officer_notes": (
        "Met with CFO Mr. Kiran Kumar on March 6, 2026. "
        "Management projects 15% revenue growth in FY27 citing summer travel season recovery. "
        "However, debt restructuring talks are ongoing with consortium of 5 banks. "
        "DGCA has issued show-cause notice for maintenance lapses. "
        "Company is exploring sale-and-leaseback for 8 aircraft to generate liquidity. "
        "Promoter Ajay Singh committed to infusing Rs 200 Cr personal equity. "
        "Management seems competent but stretched thin. Their cash runway is only 3-4 months without new funding."
    ),
})
print(f"Status: {insight2_resp.status_code}")
insight2 = insight2_resp.json()
print(f"AI Analysis: {json.dumps(insight2.get('ai_analysis', {}), indent=2)}")

# ── Step 6: Get All Insights ──
print()
print("=" * 60)
print("Step 6: All Due Diligence Insights Summary")
print("=" * 60)
notes_resp = requests.get(f"{BASE}/due-diligence/{app_id}/notes")
print(f"Status: {notes_resp.status_code}")
notes_data = notes_resp.json()
print(f"Total Insights: {notes_data['total_insights']}")
print(f"Total Score Adjustment: {notes_data['total_score_adjustment']} pts")
print(f"Severity Breakdown: {notes_data['severity_breakdown']}")
print(f"Risk Flags: {notes_data['all_risk_flags']}")

# ── Step 7: Final Pipeline Status ──
print()
print("=" * 60)
print("Step 7: Final Pipeline Status")
print("=" * 60)
final_resp = requests.get(f"{BASE}/applications/{app_id}/summary")
final = final_resp.json()
for k, v in final["pipeline"].items():
    status_icon = "✅" if v["status"] == "completed" else "⏳" if v["status"] == "in_progress" else "⭕"
    detail = ""
    if k == "research":
        detail = f" ({v['count']} checks, risk={v.get('overall_risk', 'N/A')})"
    elif k == "due_diligence":
        detail = f" ({v['count']} insights, adj={v['total_adjustment']} pts)"
    print(f"  {status_icon} {k}: {v['status']}{detail}")

print()
print("=" * 60)
print("E2E TEST COMPLETE")
print(f"App ID for frontend: {app_id}")
print("=" * 60)
