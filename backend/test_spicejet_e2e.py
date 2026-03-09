"""
Comprehensive SpiceJet E2E Pipeline Test
Tests ALL pillars: Ingestion (Bank+GST+Annual Report PDF), External Intelligence (5 engines), Primary Insights (LLM)
"""
import requests
import json
import os
import time
import sys

BASE = "http://localhost:8000/api/v1"
TEST_DATA = os.path.join(os.path.dirname(__file__), "test_data")
DOWNLOADS = os.path.join(os.path.dirname(__file__), "..", "downloads")

passed_count = 0
failed_count = 0


def separator(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(label, condition, detail=""):
    global passed_count, failed_count
    status = "PASS" if condition else "FAIL"
    icon = "+" if condition else "X"
    if condition:
        passed_count += 1
    else:
        failed_count += 1
    print(f"  [{icon}] {label}" + (f" -- {detail}" if detail else ""))
    return condition


# ============================================================
# STEP 1: Create Application
# ============================================================
separator("STEP 1: Create SpiceJet Application")

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
print(f"  Application ID: {APP_ID}")
check("Application created", APP_ID.startswith("APP-"))
check("Status is 'created'", app["status"] == "created", app["status"])

# ============================================================
# STEP 2: Upload ALL Documents (Bank + GST + Annual Report PDF)
# ============================================================
separator("STEP 2: Upload Documents (Bank + GST + Annual Report PDF)")

bank_file = os.path.join(TEST_DATA, "Bank_Statement_TechCorp_Industries_Ltd_good.xlsx")
gst_file = os.path.join(TEST_DATA, "GST_Returns_TechCorp_Industries_Ltd_good.xlsx")
annual_report_pdf = os.path.join(DOWNLOADS, "AnnualReport_SpiceJet_202324.pdf")

check("Bank statement file exists", os.path.exists(bank_file), bank_file)
check("GST returns file exists", os.path.exists(gst_file), gst_file)
check("Annual Report PDF exists", os.path.exists(annual_report_pdf), annual_report_pdf)

files = [
    ("files", ("bank_statement_spicejet.xlsx", open(bank_file, "rb"),
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ("files", ("gst_returns_spicejet.xlsx", open(gst_file, "rb"),
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ("files", ("AnnualReport_SpiceJet_202324.pdf", open(annual_report_pdf, "rb"),
               "application/pdf")),
]
data = {"application_id": APP_ID}

r = requests.post(f"{BASE}/ingestion/upload-documents", files=files, data=data)
assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
upload_result = r.json()

check("All 3 files uploaded", upload_result["total_files"] == 3, f"{upload_result['total_files']} files")

for uf in upload_result["uploaded_files"]:
    doc_type = uf["document_type"]
    confidence = uf["classification_confidence"]
    check(f"Classified: {uf['filename']}", 
          doc_type in ["BANK_STATEMENT", "GST_RETURN", "ANNUAL_REPORT"],
          f"{doc_type} ({confidence:.0%})")

# ============================================================
# STEP 3: Parse ALL Documents (including Annual Report via Gemini Vision)
# ============================================================
separator("STEP 3: Parse All Documents")

r = requests.post(f"{BASE}/ingestion/parse-documents/{APP_ID}", timeout=180)
assert r.status_code == 200, f"Parse failed: {r.status_code} {r.text}"
parse_result = r.json()

check("All documents parsed", parse_result["parsed_count"] == 3, 
      f"{parse_result['parsed_count']}/3 parsed")

for pr in parse_result["results"]:
    status = pr["parse_status"]
    parsed_data = pr.get("parsed_data", {})
    has_data = bool(parsed_data) and parsed_data != {}
    check(f"Parsed: {pr['filename']} ({pr['document_type']})", 
          status == "COMPLETED" and has_data, status)

    if pr["document_type"] == "BANK_STATEMENT" and has_data:
        summary = parsed_data.get("summary", {})
        print(f"       Bank: {summary.get('total_transactions', '?')} txns, "
              f"avg_balance=Rs.{summary.get('average_balance', 0):,.0f}")

    elif pr["document_type"] == "GST_RETURN" and has_data:
        summary = parsed_data.get("summary", {})
        print(f"       GST: {summary.get('total_entries', '?')} entries, "
              f"total_revenue=Rs.{summary.get('total_taxable_value', 0):,.0f}")

    elif pr["document_type"] == "ANNUAL_REPORT" and has_data:
        print(f"       Company: {parsed_data.get('company_name', '?')}")
        print(f"       Revenue: Rs.{parsed_data.get('revenue_cr', 0)} Cr")
        print(f"       Debt: Rs.{parsed_data.get('total_debt_cr', 0)} Cr")
        print(f"       Equity: Rs.{parsed_data.get('total_equity_cr', 0)} Cr")
        print(f"       Auditor: {parsed_data.get('auditor_name', '?')}")
        print(f"       Opinion: {parsed_data.get('auditor_opinion', '?')}")
        print(f"       Litigations: {len(parsed_data.get('pending_litigations', []))}")
        print(f"       Key Risks: {parsed_data.get('key_risks', [])[:3]}")

# ============================================================
# STEP 4: Verify Ingestion Summary
# ============================================================
separator("STEP 4: Ingestion Summary")

r = requests.get(f"{BASE}/ingestion/documents/{APP_ID}")
assert r.status_code == 200
docs = r.json()

check("All 3 documents in DB", len(docs["documents"]) == 3, f"{len(docs['documents'])} docs")

doc_types_found = set()
for d in docs["documents"]:
    doc_types_found.add(d["document_type"])
    check(f"  {d['filename']}", d["parse_status"] == "COMPLETED", 
          f"{d['document_type']} -- {d['parse_status']}")

check("Bank Statement present", "BANK_STATEMENT" in doc_types_found)
check("GST Return present", "GST_RETURN" in doc_types_found)
check("Annual Report present", "ANNUAL_REPORT" in doc_types_found)

# ============================================================
# STEP 5: External Intelligence (5 Research Engines)
# ============================================================
separator("STEP 5: External Intelligence (5 Engines)")

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

completed = research.get("completed_tasks", 0)
failed = research.get("failed_tasks", 0)
overall_risk = research.get("overall_risk", "?")
results_list = research.get("results", [])

check("Research completed", completed >= 4, f"{completed}/5 engines passed, {failed} failed")
check("Overall risk level", overall_risk in ["HIGH", "MEDIUM", "LOW"], overall_risk)

for result in results_list:
    rtype = result.get("type", "unknown")
    risk = result.get("risk", "?")
    status = result.get("status", "unknown")
    check(f"  Engine: {rtype}", status == "completed", f"risk={risk}, status={status}")

# Verify detailed results via GET endpoint
print("\n  --- Detailed Research Results ---")
r = requests.get(f"{BASE}/research/{APP_ID}/results")
assert r.status_code == 200
research_detail = r.json()

check("Research detail available", research_detail.get("research_completed") == True)
check("Company name correct", research_detail.get("company_name") == "SpiceJet Limited")

results_by_type = research_detail.get("results_by_type", {})
for rtype, items in results_by_type.items():
    for item in items:
        risk = item.get("risk_level", "?")
        entity = item.get("entity_name", "?")
        sentiment = item.get("sentiment", "?")
        summary = item.get("findings_summary", "")[:100]
        check(f"    {rtype}: {entity}", True, f"risk={risk}, sentiment={sentiment}")
        print(f"       Summary: {summary}...")

# ============================================================
# STEP 6: Primary Insights - Site Visit (LLM)
# ============================================================
separator("STEP 6: Primary Insights -- Site Visit")

site_visit_notes = """
Site visit conducted at SpiceJet's corporate office in Gurgaon on March 5, 2026.

Observations:
1. Office infrastructure appears well-maintained, ~200 employees visible in operations center
2. Fleet maintenance records reviewed - 50+ aircraft, average age 7.2 years (acceptable)
3. CFO Mr. Kiran Kumar presented Q3 financials showing 12% revenue growth YoY
4. However, noticed unusual pattern: 3 large vendor payments (Rs.15Cr each) to newly incorporated entities
5. Cash reserves appear stressed - current ratio close to 1.0
6. Airport slot utilization is 78% - room for improvement
7. Employee morale seemed low, 2 key pilots mentioned late salary payments in Dec 2025
"""

r = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": APP_ID,
    "insight_type": "site_visit",
    "credit_officer_notes": site_visit_notes
}, timeout=180)
assert r.status_code == 200, f"Site visit failed: {r.status_code} {r.text}"
sv = r.json()

ai = sv.get("ai_analysis", {})
is_real_analysis = ai.get("confidence", 0) > 0.5
check("AI analyzed site visit", is_real_analysis,
      f"confidence={ai.get('confidence')}, {'LLM' if is_real_analysis else 'FALLBACK'}")
check("Risk category valid", 
      ai.get("risk_category") in ["Operational", "Governance", "Financial", "Management", "Compliance", "Infrastructure", "Market"],
      ai.get("risk_category"))
check("Severity valid", ai.get("severity") in ["HIGH", "MEDIUM", "LOW"], ai.get("severity"))
check("Score adjustment", isinstance(ai.get("score_adjustment"), (int, float)), 
      f"{ai.get('score_adjustment')} pts")
check("Risk flags found", len(ai.get("risk_flags", [])) > 0, 
      f"{len(ai.get('risk_flags', []))} flags")
check("Entities extracted", len(ai.get("entities", [])) > 0, 
      str(ai.get("entities", [])))
print(f"       Summary: {ai.get('summary', 'N/A')[:150]}...")

# ============================================================
# STEP 7: Primary Insights - Management Interview (LLM)
# ============================================================
separator("STEP 7: Primary Insights -- Management Interview")

print("  Waiting 10s for Gemini rate limit...")
time.sleep(10)

interview_notes = """
Management interview with SpiceJet CEO Ajay Singh, conducted March 6, 2026.

Key points:
1. CEO confident about FY27 guidance: targeting 15% revenue growth, breakeven EBITDA
2. Plans to induct 10 new Boeing 737 MAX aircraft by Q2 FY27 via lease financing
3. Recent settlement with Kalanithi Maran (Rs.600Cr) resolved via equity issuance
4. GoFirst's shutdown created route opportunities - SpiceJet added 14 new routes
5. DGCA had issued a show-cause notice for safety lapses - CEO claims resolved
6. Fuel hedging strategy: 40% hedged at $75/barrel for next 6 months
7. Acknowledged delayed salary payments to staff - promises resolution by April 2026
8. NCLT case with Credit Suisse pending, liability ~Rs.200Cr
9. Expressed interest in launching cargo division to diversify revenue
10. Board composition: only 2 independent directors out of 7 - governance concern
"""

r = requests.post(f"{BASE}/due-diligence/add-notes", json={
    "application_id": APP_ID,
    "insight_type": "management_interview",
    "credit_officer_notes": interview_notes
}, timeout=180)
assert r.status_code == 200, f"Interview failed: {r.status_code} {r.text}"
mi = r.json()

ai2 = mi.get("ai_analysis", {})
is_real2 = ai2.get("confidence", 0) > 0.5
check("AI analyzed interview", is_real2,
      f"confidence={ai2.get('confidence')}, {'LLM' if is_real2 else 'FALLBACK'}")
check("Risk category valid", bool(ai2.get("risk_category")), ai2.get("risk_category"))
check("Severity valid", ai2.get("severity") in ["HIGH", "MEDIUM", "LOW"], ai2.get("severity"))
check("Score adjustment", isinstance(ai2.get("score_adjustment"), (int, float)),
      f"{ai2.get('score_adjustment')} pts")
check("Risk flags found", len(ai2.get("risk_flags", [])) > 0,
      f"{len(ai2.get('risk_flags', []))} flags")
print(f"       Summary: {ai2.get('summary', 'N/A')[:150]}...")

# ============================================================
# STEP 8: Insights Aggregation
# ============================================================
separator("STEP 8: Insights Aggregation")

r = requests.get(f"{BASE}/due-diligence/{APP_ID}/notes")
assert r.status_code == 200
all_notes = r.json()

check("Total insights", all_notes["total_insights"] == 2, f"{all_notes['total_insights']}")
check("Total score adjustment", 
      isinstance(all_notes["total_score_adjustment"], (int, float)),
      f"{all_notes['total_score_adjustment']} pts")
check("Severity breakdown", 
      sum(all_notes["severity_breakdown"].values()) == 2,
      str(all_notes["severity_breakdown"]))
check("Risk flags aggregated", 
      len(all_notes["all_risk_flags"]) > 0,
      f"{len(all_notes['all_risk_flags'])} unique flags")

# ============================================================
# STEP 9: Pipeline Status
# ============================================================
separator("STEP 9: Pipeline Status")

r = requests.get(f"{BASE}/applications/{APP_ID}/summary")
assert r.status_code == 200
summary = r.json()

pipeline = summary.get("pipeline", {})
steps = {k: v.get("status") for k, v in pipeline.items()}
check("Ingestion: completed", steps.get("ingestion") == "completed")
check("Research: completed", steps.get("research") == "completed")
check("Due Diligence: completed", steps.get("due_diligence") == "completed")
check("Scoring: pending", steps.get("scoring") in ["not_started", "pending"])
check("CAM: pending", steps.get("cam") in ["not_started", "pending"])

# ============================================================
# FINAL SUMMARY
# ============================================================
separator("FINAL RESULTS")

print(f"""
  Application: {APP_ID}
  Company: SpiceJet Limited

  --- Ingestion (Pillar 1) ---
  Documents parsed: {parse_result['parsed_count']}/3 (Bank + GST + Annual Report PDF)

  --- External Intelligence (Pillar 2) ---
  Research engines: {completed}/5 passed
  Overall Risk: {overall_risk}

  --- Primary Insights (Pillar 3) ---
  Insights analyzed: {all_notes['total_insights']}
  Total score adjustment: {all_notes['total_score_adjustment']} pts
  Severity: {all_notes['severity_breakdown']}

  --- LLM Analysis ---
  Site Visit: confidence={ai.get('confidence', 0)}, severity={ai.get('severity')}
  Interview:  confidence={ai2.get('confidence', 0)}, severity={ai2.get('severity')}

  --- Pipeline ---
  {json.dumps(steps, indent=4)}
""")

print(f"  TOTAL: {passed_count} passed, {failed_count} failed")
print(f"  {'ALL TESTS PASSED!' if failed_count == 0 else 'SOME TESTS FAILED!'}")
print()
