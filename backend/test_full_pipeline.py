"""
Full Pipeline E2E Test
Tests: Create App → Ingestion (structured) → External Intelligence → Primary Insights (LLM) → Pipeline Status
"""
import requests
import json
import os
import time

BASE = "http://localhost:8000/api/v1"
TEST_DATA = os.path.join(os.path.dirname(__file__), "test_data")

def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check(label, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {label}" + (f" — {detail}" if detail else ""))
    return condition

# ──────────────────────────────────────────────────
# STEP 1: Create Application
# ──────────────────────────────────────────────────
separator("STEP 1: Create Application")

app_data = {
    "company_name": "SpiceJet Limited",
    "mca_cin": "L51909DL1984PLC018603",
    "sector": "Aviation",
    "requested_limit_cr": 500,
}
r = requests.post(f"{BASE}/applications/", json=app_data)
assert r.status_code == 200, f"Create app failed: {r.status_code} {r.text}"
app = r.json()
APP_ID = app["application_id"]
print(f"  Created: {APP_ID}")
check("Application created", APP_ID.startswith("APP-"))
check("Status", app["status"] == "created", app["status"])

# ──────────────────────────────────────────────────
# STEP 2: Upload Documents (Structured: Bank + GST)
# ──────────────────────────────────────────────────
separator("STEP 2: Upload Structured Documents")

bank_file = os.path.join(TEST_DATA, "Bank_Statement_TechCorp_Industries_Ltd_good.xlsx")
gst_file = os.path.join(TEST_DATA, "GST_Returns_TechCorp_Industries_Ltd_good.xlsx")

assert os.path.exists(bank_file), f"Bank test file not found: {bank_file}"
assert os.path.exists(gst_file), f"GST test file not found: {gst_file}"

files = [
    ("files", ("bank_statement_spicejet.xlsx", open(bank_file, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ("files", ("gst_returns_spicejet.xlsx", open(gst_file, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
]
data = {"application_id": APP_ID}

r = requests.post(f"{BASE}/ingestion/upload-documents", files=files, data=data)
assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
upload_result = r.json()

check("Files uploaded", upload_result["total_files"] == 2, f"{upload_result['total_files']} files")

for uf in upload_result["uploaded_files"]:
    doc_type = uf["document_type"]
    confidence = uf["classification_confidence"]
    check(f"Classified: {uf['filename']}", doc_type in ["BANK_STATEMENT", "GST_RETURN"], f"{doc_type} ({confidence:.0%})")

# ──────────────────────────────────────────────────
# STEP 3: Parse Documents
# ──────────────────────────────────────────────────
separator("STEP 3: Parse Documents")

r = requests.post(f"{BASE}/ingestion/parse-documents/{APP_ID}")
assert r.status_code == 200, f"Parse failed: {r.status_code} {r.text}"
parse_result = r.json()

check("Documents parsed", parse_result["parsed_count"] > 0, f"{parse_result['parsed_count']} parsed")

for pr in parse_result["results"]:
    status = pr["parse_status"]
    parsed_data = pr.get("parsed_data", {})
    has_data = bool(parsed_data) and parsed_data != {}
    check(f"Parsed: {pr['filename']} ({pr['document_type']})", status == "COMPLETED" and has_data, status)
    
    # Show key parsed metrics
    if pr["document_type"] == "BANK_STATEMENT" and has_data:
        summary = parsed_data.get("summary", {})
        print(f"     📊 Bank: {summary.get('total_transactions', '?')} txns, "
              f"avg_balance=₹{summary.get('average_balance', 0):,.0f}")
    elif pr["document_type"] == "GST_RETURN" and has_data:
        summary = parsed_data.get("summary", {})
        print(f"     📊 GST: {summary.get('total_entries', '?')} entries, "
              f"total_revenue=₹{summary.get('total_taxable_value', 0):,.0f}")

# ──────────────────────────────────────────────────
# STEP 4: Get Ingestion Summary
# ──────────────────────────────────────────────────
separator("STEP 4: Ingestion Summary")

r = requests.get(f"{BASE}/ingestion/documents/{APP_ID}")
assert r.status_code == 200, f"Get docs failed: {r.status_code} {r.text}"
docs = r.json()

check("Documents in DB", len(docs["documents"]) == 2, f"{len(docs['documents'])} docs")
for d in docs["documents"]:
    check(f"  {d['filename']}", d["parse_status"] == "COMPLETED", d["document_type"])

# ──────────────────────────────────────────────────
# STEP 5: External Intelligence (5 engines)
# ──────────────────────────────────────────────────
separator("STEP 5: External Intelligence (Research)")

research_data = {
    "application_id": APP_ID,
    "company_name": "SpiceJet Limited",
    "sector": "Aviation",
    "promoter_names": ["Ajay Singh"],
    "cin": "L51909DL1984PLC018603"
}

r = requests.post(f"{BASE}/research/trigger-research", json=research_data, timeout=120)
assert r.status_code == 200, f"Research failed: {r.status_code} {r.text}"
research = r.json()

passed = research.get("completed_tasks", 0)
failed = research.get("failed_tasks", 0)
overall_risk = research.get("overall_risk", "?")
results_list = research.get("results", [])

check("Research completed", passed >= 4, f"{passed}/5 engines passed")
check("Overall risk level", overall_risk in ["HIGH", "MEDIUM", "LOW"], overall_risk)

for result in results_list:
    rtype = result.get("research_type", "unknown")
    risk = result.get("risk_level", "?")
    check(f"  {rtype}", True, f"risk={risk}")

# ──────────────────────────────────────────────────
# STEP 6: Primary Insights (LLM Analysis)
# ──────────────────────────────────────────────────
separator("STEP 6: Primary Insights — Site Visit")

site_visit_notes = """
Site visit conducted at SpiceJet's corporate office in Gurgaon on March 5, 2026.

Observations:
1. Office infrastructure appears well-maintained, ~200 employees visible in operations center
2. Fleet maintenance records reviewed - 50+ aircraft, average age 7.2 years (acceptable)
3. CFO Mr. Kiran Kumar presented Q3 financials showing 12% revenue growth YoY
4. However, noticed unusual pattern: 3 large vendor payments (₹15Cr each) to newly incorporated entities
5. Cash reserves appear stressed - current ratio close to 1.0
6. Airport slot utilization is 78% - room for improvement
7. Employee morale seemed low, 2 key pilots mentioned late salary payments in Dec 2025
"""

r = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": APP_ID,
    "insight_type": "site_visit",
    "credit_officer_notes": site_visit_notes
}, timeout=60)
assert r.status_code == 200, f"Site visit failed: {r.status_code} {r.text}"
sv = r.json()

ai = sv.get("ai_analysis", {})
is_real_analysis = ai.get("confidence", 0) > 0.5
check("AI analyzed site visit", is_real_analysis, 
      f"confidence={ai.get('confidence')}, provider={'LLM' if is_real_analysis else 'FALLBACK'}")
check("Risk category", ai.get("risk_category") in ["Operational", "Governance", "Financial", "Management", "Compliance", "Infrastructure", "Market"], 
      ai.get("risk_category"))
check("Severity", ai.get("severity") in ["HIGH", "MEDIUM", "LOW"], ai.get("severity"))
check("Score adjustment", isinstance(ai.get("score_adjustment"), (int, float)), f"{ai.get('score_adjustment')} pts")
check("Risk flags found", len(ai.get("risk_flags", [])) > 0, str(ai.get("risk_flags", [])))
check("Entities extracted", len(ai.get("entities", [])) > 0, str(ai.get("entities", [])))
print(f"     📝 Summary: {ai.get('summary', 'N/A')[:120]}...")

# ──────────────────────────────────────────────────
# STEP 7: Primary Insights — Management Interview
# ──────────────────────────────────────────────────
separator("STEP 7: Primary Insights — Management Interview")

time.sleep(10)  # Longer delay to avoid Gemini rate-limiting between LLM calls

interview_notes = """
Management interview with SpiceJet CEO Ajay Singh, conducted March 6, 2026.

Key points from the discussion:
1. CEO confident about FY27 guidance: targeting 15% revenue growth, breakeven EBITDA
2. Plans to induct 10 new Boeing 737 MAX aircraft by Q2 FY27 via lease financing
3. Recent settlement with Kalanithi Maran (₹600Cr) resolved via equity issuance
4. GoFirst's shutdown created route opportunities - SpiceJet added 14 new routes
5. DGCA had issued a show-cause notice for safety lapses - CEO claims resolved
6. Fuel hedging strategy: 40% hedged at $75/barrel for next 6 months
7. Acknowledged delayed salary payments to staff - promises resolution by April 2026
8. NCLT case with Credit Suisse pending, liability ~₹200Cr
9. Expressed interest in launching cargo division to diversify revenue
10. Board composition: only 2 independent directors out of 7 - governance concern
"""

r = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": APP_ID,
    "insight_type": "management_interview",
    "credit_officer_notes": interview_notes
}, timeout=60)
assert r.status_code == 200, f"Interview failed: {r.status_code} {r.text}"
mi = r.json()

ai2 = mi.get("ai_analysis", {})
is_real = ai2.get("confidence", 0) > 0.5
check("AI analyzed interview", is_real, f"confidence={ai2.get('confidence')}")
check("Risk category", bool(ai2.get("risk_category")), ai2.get("risk_category"))
check("Severity", ai2.get("severity") in ["HIGH", "MEDIUM", "LOW"], ai2.get("severity"))
check("Score adjustment", isinstance(ai2.get("score_adjustment"), (int, float)), f"{ai2.get('score_adjustment')} pts")
check("Risk flags found", len(ai2.get("risk_flags", [])) > 0, str(ai2.get("risk_flags", [])))
print(f"     📝 Summary: {ai2.get('summary', 'N/A')[:120]}...")

# ──────────────────────────────────────────────────
# STEP 8: Get All Insights (Aggregation)
# ──────────────────────────────────────────────────
separator("STEP 8: Insights Aggregation")

r = requests.get(f"{BASE}/due-diligence/{APP_ID}/notes")
assert r.status_code == 200, f"Get notes failed: {r.status_code} {r.text}"
all_notes = r.json()

check("Total insights", all_notes["total_insights"] == 2, f"{all_notes['total_insights']}")
check("Total score adjustment", isinstance(all_notes["total_score_adjustment"], (int, float)), 
      f"{all_notes['total_score_adjustment']} pts")
check("Severity breakdown", sum(all_notes["severity_breakdown"].values()) == 2, 
      str(all_notes["severity_breakdown"]))
check("All risk flags aggregated", len(all_notes["all_risk_flags"]) > 0, 
      f"{len(all_notes['all_risk_flags'])} unique flags")

print(f"\n  📊 Risk Flags: {all_notes['all_risk_flags'][:5]}")
print(f"  📊 Severity: {all_notes['severity_breakdown']}")
print(f"  📊 Total Adjustment: {all_notes['total_score_adjustment']} pts")

# ──────────────────────────────────────────────────
# STEP 9: Pipeline Status Check
# ──────────────────────────────────────────────────
separator("STEP 9: Pipeline Status")

r = requests.get(f"{BASE}/applications/{APP_ID}/summary")
assert r.status_code == 200, f"Summary failed: {r.status_code} {r.text}"
summary = r.json()

pipeline = summary.get("pipeline", {})
steps = {k: v.get("status") for k, v in pipeline.items()}
check("Ingestion: completed", steps.get("ingestion") == "completed")
check("Research: completed", steps.get("research") == "completed")
check("Due Diligence: completed", steps.get("due_diligence") == "completed")
check("Scoring: pending", steps.get("scoring") in ["not_started", "pending"])
check("CAM: pending", steps.get("cam") in ["not_started", "pending"])

# ──────────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────────
separator("FINAL RESULTS")

print(f"""
  Application: {APP_ID}
  Company: SpiceJet Limited
  
  📁 Ingestion:    {parse_result['parsed_count']} docs parsed (bank + GST)
  🔍 Research:     {passed}/5 engines passed — Overall: {overall_risk}
  🧠 Insights:     {all_notes['total_insights']} analyzed — Adjustment: {all_notes['total_score_adjustment']} pts
  
  LLM Analysis:    {'✅ REAL (Gemini/OpenAI)' if is_real_analysis else '⚠️ FALLBACK defaults'}
  Confidence:      {ai.get('confidence', 0)} / {ai2.get('confidence', 0)}
  
  Pipeline Steps: {json.dumps(steps, indent=2)}
""")

print("🏁 FULL PIPELINE TEST COMPLETE!")
