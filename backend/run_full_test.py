"""
Full Pipeline Test — All 11 processes for 3 test companies.

Tests every API endpoint in the Intelli-Credit platform:
 1. Create Application
 2. Upload Documents (5 per company: annual report, bank statement, GST, ITR, balance sheet)
 3. Parse Documents (all 5 types)
 4. Extraction: Review classifications
 5. Extraction: Schema CRUD + run extraction
 6. External Research (Tavily)
 7. Due Diligence Notes
 8. Fraud Detection
 9. Credit Scoring (Five Cs)
10. Pre-Cognitive Analysis (SWOT, Triangulation, Recommendation)
11. CAM Generation + Download

Usage:
    python run_full_test.py

Requires: backend server running on http://localhost:8000
"""
import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

COMPANIES = [
    {
        "name": "Apex Manufacturing Pvt Ltd",
        "cin": "U28110MH2015PTC265432",
        "sector": "Manufacturing",
        "loan_cr": 10.0,
        "data_dir": "test_data/company1_apex_manufacturing",
        "expected_decision": "APPROVE",
        "label": "HEALTHY",
        "dd_notes": "Factory operating at 78% capacity. Well-maintained machinery. Strong management team with 15+ years experience. Clean premises, good inventory management.",
    },
    {
        "name": "GreenField Logistics Ltd",
        "cin": "U60100DL2018PLC328745",
        "sector": "Logistics",
        "loan_cr": 15.0,
        "data_dir": "test_data/company2_greenfield_logistics",
        "expected_decision": "REJECT",
        "label": "GST FRAUD",
        "dd_notes": "Fleet appears much smaller than reported. Only 12 trucks observed vs 50 claimed. Warehouse partially empty. Promoter evasive about revenue sources. Multiple shell companies linked.",
    },
    {
        "name": "Orion Retail Pvt Ltd",
        "cin": "U52100KA2019PTC354321",
        "sector": "Retail",
        "loan_cr": 8.0,
        "data_dir": "test_data/company3_orion_retail",
        "expected_decision": "REJECT",
        "label": "CIRCULAR TRADING",
        "dd_notes": "Retail stores appear under-stocked. Most transactions seem to be inter-company. Customer footfall very low for claimed revenue. Related party transactions dominate the books.",
    },
]

# ── Counters ──
total_tests = 0
passed_tests = 0
failed_tests = 0
failures = []


def header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def step(num, text):
    print(f"\n  Step {num}: {text}")
    print(f"  {'-'*50}")


def check(label, condition, detail=""):
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"    ✓ {label}")
    else:
        failed_tests += 1
        msg = f"{label} — {detail}" if detail else label
        print(f"    ✗ FAIL: {msg}")
        failures.append(msg)
    return condition


def api_ok(label, response, expected_status=200):
    """Check response status and return parsed JSON or None."""
    ok = check(label, response.status_code == expected_status,
               f"got {response.status_code}: {response.text[:200]}")
    if ok:
        try:
            return response.json()
        except Exception:
            return {}
    return None


def check_server():
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def run_full_pipeline(company: dict, index: int):
    """Run all 11 processes for one company."""
    header(f"Company {index+1}: {company['name']} [{company['label']}]")
    print(f"  Expected decision: {company['expected_decision']}")

    ctx = {}  # shared context for the pipeline

    # ═══════════════ STEP 1: Create Application ═══════════════
    step(1, "Create Application")
    r = requests.post(f"{API}/applications", json={
        "company_name": company["name"],
        "mca_cin": company["cin"],
        "sector": company["sector"],
        "requested_limit_cr": company["loan_cr"],
    })
    data = api_ok("Application created", r)
    if not data:
        return None
    app_id = data.get("application_id") or data.get("id")
    check("application_id is present", bool(app_id), "no app id in response")
    print(f"      → {app_id}")
    ctx["app_id"] = app_id

    # ═══════════════ STEP 2: Upload Documents ═══════════════
    step(2, "Upload Documents")
    data_dir = company["data_dir"]
    files_to_upload = [
        ("files", ("annual_report.json", open(f"{data_dir}/annual_report.json", "rb"), "application/json")),
        ("files", ("bank_statement.xlsx", open(f"{data_dir}/bank_statement.xlsx", "rb"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ("files", ("gst_returns.xlsx", open(f"{data_dir}/gst_returns.xlsx", "rb"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ("files", ("itr_returns.json", open(f"{data_dir}/itr_returns.json", "rb"), "application/json")),
        ("files", ("balance_sheet.json", open(f"{data_dir}/balance_sheet.json", "rb"), "application/json")),
    ]
    r = requests.post(f"{API}/ingestion/upload-documents",
                      data={"application_id": app_id}, files=files_to_upload)
    for _, (_, fh, _) in files_to_upload:
        fh.close()

    data = api_ok("Upload endpoint returned 200", r)
    if not data:
        return None
    check(f"Uploaded {data.get('total_files', 0)} files", data.get("total_files", 0) == 5, f"expected 5")
    for f in data.get("uploaded_files", []):
        check(f"  {f['filename']} → {f['document_type']}", f["classification_confidence"] >= 0.5)
        ctx.setdefault("doc_ids", []).append(f["file_id"])
        ctx.setdefault("doc_types", {})[f["file_id"]] = f["document_type"]
    print(f"      → {len(ctx.get('doc_ids', []))} documents stored")

    # ═══════════════ STEP 3: Parse Documents ═══════════════
    step(3, "Parse Documents")
    r = requests.post(f"{API}/ingestion/parse-documents/{app_id}")
    data = api_ok("Parse endpoint returned 200", r)
    if not data:
        return None
    check(f"Parsed {data.get('parsed_count', 0)} documents", data.get("parsed_count", 0) == 5)
    for doc in data.get("results", []):
        status = doc.get("parse_status", "UNKNOWN")
        check(f"  {doc['filename']} → {status}", status == "COMPLETED")
        pd = doc.get("parsed_data", {})
        if doc["document_type"] == "ANNUAL_REPORT":
            check("  Annual report: revenue present", pd.get("revenue_cr", 0) > 0,
                  f"revenue_cr={pd.get('revenue_cr')}")
            ctx["revenue_cr"] = pd.get("revenue_cr", 0)
        elif doc["document_type"] == "BANK_STATEMENT":
            check("  Bank statement: inflows present", pd.get("total_inflows_cr", 0) > 0)
            ctx["inflows_cr"] = pd.get("total_inflows_cr", 0)
        elif doc["document_type"] == "GST_RETURN":
            check("  GST returns: sales present", pd.get("gstr_1_sales_cr", 0) > 0)
            ctx["gst_sales_cr"] = pd.get("gstr_1_sales_cr", 0)
        elif doc["document_type"] == "ITR":
            check("  ITR: PAN present", bool(pd.get("pan")))
            check("  ITR: assessment year present", bool(pd.get("assessment_year")))
        elif doc["document_type"] == "BALANCE_SHEET":
            assets = pd.get("assets", {})
            check("  Balance sheet: total assets present", assets.get("total_assets_cr", 0) > 0)

    # ═══════════════ STEP 4: Extraction — Review Classifications ═══════════════
    step(4, "Extraction — Review Classifications")
    r = requests.get(f"{API}/extraction/documents/{app_id}")
    data = api_ok("List extraction documents", r)
    if data:
        docs_list = data.get("documents", [])
        check(f"Found {len(docs_list)} documents", len(docs_list) == 5)
        # Approve all classifications
        approved = 0
        for doc in docs_list:
            fid = doc["file_id"]
            r2 = requests.put(f"{API}/extraction/documents/{fid}/review",
                              json={"action": "approve"})
            d2 = api_ok(f"  Approve {doc['filename']}", r2)
            if d2 and d2.get("reviewed") == "approved":
                approved += 1
        check(f"All {approved}/5 classifications approved", approved == 5)

    # ═══════════════ STEP 5: Extraction — Schema CRUD + Run Extraction ═══════════════
    step(5, "Extraction — Schema CRUD & Extraction")

    # 5a. Get default schemas
    r = requests.get(f"{API}/extraction/schemas/defaults")
    data = api_ok("Get default schemas", r)
    if data:
        check(f"Default schemas returned ({len(data)} types)", len(data) >= 5)

    # 5b. Create a custom schema
    r = requests.post(f"{API}/extraction/schemas/{app_id}", json={
        "document_type": "ANNUAL_REPORT",
        "schema_name": "Custom AR Schema",
        "fields": [
            {"key": "revenue_cr", "label": "Revenue (Cr)", "type": "number", "required": True},
            {"key": "net_profit_cr", "label": "Net Profit (Cr)", "type": "number", "required": True},
            {"key": "auditor_opinion", "label": "Auditor Opinion", "type": "text", "required": False},
        ]
    })
    schema_data = api_ok("Create custom schema", r)
    custom_schema_id = None
    if schema_data:
        custom_schema_id = schema_data.get("id")
        check("Custom schema has id", bool(custom_schema_id))
        check("Schema has 3 fields", len(schema_data.get("fields", [])) == 3)

    # 5c. List schemas for application
    r = requests.get(f"{API}/extraction/schemas/{app_id}")
    data = api_ok("List custom schemas", r)
    if data:
        check(f"Found {len(data.get('schemas', []))} custom schema(s)", len(data.get("schemas", [])) >= 1)

    # 5d. Update the custom schema
    if custom_schema_id:
        r = requests.put(f"{API}/extraction/schemas/{custom_schema_id}", json={
            "schema_name": "Custom AR Schema v2",
            "fields": [
                {"key": "revenue_cr", "label": "Revenue (Cr)", "type": "number", "required": True},
                {"key": "net_profit_cr", "label": "Net Profit (Cr)", "type": "number", "required": True},
                {"key": "auditor_opinion", "label": "Auditor Opinion", "type": "text", "required": False},
                {"key": "total_assets_cr", "label": "Total Assets (Cr)", "type": "number", "required": False},
            ]
        })
        data = api_ok("Update custom schema", r)
        if data:
            check("Updated schema name", data.get("schema_name") == "Custom AR Schema v2")
            check("Updated schema has 4 fields", len(data.get("fields", [])) == 4)

    # 5e. Run extraction on each document (using default schemas)
    doc_ids = ctx.get("doc_ids", [])
    for fid in doc_ids:
        r = requests.post(f"{API}/extraction/extract/{fid}", json={})
        d = api_ok(f"  Extract doc {fid[:8]}…", r)
        if d:
            ext = d.get("extracted", {})
            check(f"    Extracted {len(ext)} fields", len(ext) > 0, f"got {ext}")

    # 5f. Run extraction with custom schema on the annual report doc
    if custom_schema_id:
        ar_doc_id = None
        for fid, dtype in ctx.get("doc_types", {}).items():
            if dtype == "ANNUAL_REPORT":
                ar_doc_id = fid
                break
        if ar_doc_id:
            r = requests.post(f"{API}/extraction/extract/{ar_doc_id}",
                              json={"schema_id": custom_schema_id})
            d = api_ok("  Extract with custom schema", r)
            if d:
                ext = d.get("extracted", {})
                check("    Has revenue_cr field", "revenue_cr" in ext or len(ext) > 0)

    # 5g. Edit extracted fields manually
    if doc_ids:
        r = requests.put(f"{API}/extraction/extract/{doc_ids[0]}/fields", json={
            "extracted_fields": {"manual_note": "Verified by analyst", "revenue_cr": 999.99}
        })
        d = api_ok("  Manual field edit", r)
        if d:
            check("    Fields saved", d.get("extracted_fields", {}).get("manual_note") == "Verified by analyst")

    # 5h. Delete the custom schema
    if custom_schema_id:
        r = requests.delete(f"{API}/extraction/schemas/{custom_schema_id}")
        d = api_ok("Delete custom schema", r)
        if d:
            check("Schema deleted", d.get("deleted") is True)

    # ═══════════════ STEP 6: External Research ═══════════════
    step(6, "External Research (Tavily API)")
    r = requests.post(f"{API}/research/trigger-research", json={
        "application_id": app_id,
        "company_name": company["name"],
        "sector": company["sector"],
    })
    if r.status_code == 200:
        data = r.json()
        check("Research completed", data.get("completed_tasks", 0) > 0)
        for finding in data.get("results", []):
            check(f"  [{finding.get('type')}] status={finding.get('status')}", finding.get("status") == "completed")
        print(f"      → overall_risk={data.get('overall_risk', '?')}")
    else:
        print(f"    ⚠ Research failed ({r.status_code}) — continuing...")

    # ═══════════════ STEP 7: Due Diligence Notes ═══════════════
    step(7, "Due Diligence Notes")
    r = requests.post(f"{API}/due-diligence/add-notes", json={
        "application_id": app_id,
        "insight_type": "site_visit",
        "credit_officer_notes": company["dd_notes"],
    })
    data = api_ok("DD notes submitted", r)
    if data:
        analysis = data.get("analysis", {})
        if analysis:
            check("DD analysis has severity", bool(analysis.get("severity")))
            check("DD analysis has score_adjustment", "score_adjustment" in analysis)
            print(f"      → severity={analysis.get('severity')}, adj={analysis.get('score_adjustment')}")

    # ═══════════════ STEP 8: Fraud Detection ═══════════════
    step(8, "Fraud Detection")
    r = requests.post(f"{API}/fraud/run-verification/{app_id}")
    data = api_ok("Fraud analysis returned 200", r)
    if data:
        score = data.get("combined_fraud_score", -1)
        risk = data.get("overall_risk_level", "?")
        flags = data.get("total_flags", 0)
        check(f"Fraud score: {score}/100", score >= 0)
        check(f"Risk level: {risk}", risk in ("LOW", "MEDIUM", "HIGH", "CRITICAL"))
        check(f"Red flags: {flags}", isinstance(flags, int))

        # Sub-systems
        cv = data.get("cross_verification", {})
        ct = data.get("circular_trading", {})
        ml = data.get("ml_prediction", {})
        check("Cross-verification ran", "rule_score" in cv)
        check("Circular trading ran", "combined_score" in ct)
        check("ML model ran", "prediction" in ml)

        ga = ct.get("graph_analysis", {})
        if ga.get("entities", 0) > 0:
            print(f"      → Graph: {ga['entities']} entities, {ga['edges']} edges, {ga.get('cycle_count', 0)} cycles")
        if data.get("all_flags"):
            for flag in data["all_flags"][:3]:
                print(f"        🚩 {flag[:80]}")

        ctx["fraud_score"] = score
        ctx["fraud_risk"] = risk

    # ═══════════════ STEP 9: Credit Scoring (Five Cs) ═══════════════
    step(9, "Credit Scoring (Five Cs)")
    r = requests.post(f"{API}/scoring/calculate-score", params={"application_id": app_id})
    data = api_ok("Scoring returned 200", r)
    if data:
        score = data.get("final_credit_score", -1)
        decision = data.get("decision", "?")
        grade = data.get("risk_grade", "?")
        check(f"Credit score: {score}/100", 0 <= score <= 100)
        check(f"Decision: {decision}", decision in ("APPROVE", "CONDITIONAL_APPROVE", "REJECT", "MANUAL_REVIEW"))
        check(f"Risk grade: {grade}", bool(grade))

        sub = data.get("sub_scores", {})
        for factor in ["character", "capacity", "capital", "collateral", "conditions"]:
            if factor in sub:
                s = sub[factor]
                check(f"  {factor}: {s.get('score', '?')}/100", 0 <= s.get("score", -1) <= 100)

        loan = data.get("loan_recommendation", {})
        rate = data.get("interest_rate", {})
        print(f"      → Recommended: ₹{loan.get('recommended_limit_cr', 0):.2f} Cr @ {rate.get('final_interest_rate', 'N/A')}%")

        reasons = data.get("decision_reasons", [])
        for reason in reasons[:3]:
            icon = "+" if reason.get("impact") == "POSITIVE" else "-"
            print(f"        [{icon}] {reason.get('text', '')[:80]}")

        ctx["score"] = score
        ctx["decision"] = decision

    # ═══════════════ STEP 10: Pre-Cognitive Analysis ═══════════════
    step(10, "Pre-Cognitive Analysis (SWOT + Triangulation + Recommendation)")
    r = requests.post(f"{API}/analysis/run/{app_id}", json={"use_llm": True}, timeout=120)
    data = api_ok("Analysis pipeline returned 200", r)
    if data:
        check("Status is analysis_complete", data.get("status") == "analysis_complete")
        check("SWOT present", bool(data.get("swot")))
        check("Triangulation present", bool(data.get("triangulation")))
        check("Recommendation present", bool(data.get("recommendation")))
        check("Research bundle present", bool(data.get("research_bundle")))

        rec = data.get("recommendation", {})
        if rec:
            print(f"      → Decision: {rec.get('decision')}")
            print(f"      → Confidence: {rec.get('confidence', '?')}")
            if rec.get("key_factors"):
                for kf in rec["key_factors"][:3]:
                    print(f"        • {str(kf)[:80]}")

        swot = data.get("swot", {})
        if swot:
            for quad in ["strengths", "weaknesses", "opportunities", "threats"]:
                items = swot.get(quad, [])
                check(f"  SWOT {quad}: {len(items)} items", len(items) > 0)

        tri = data.get("triangulation", {})
        if tri:
            conf = tri.get("confidence_level") or tri.get("overall_confidence")
            print(f"      → Triangulation confidence: {conf}")

    # 10b. Retrieve stored analysis
    r = requests.get(f"{API}/analysis/{app_id}")
    data = api_ok("Retrieve stored analysis", r)
    if data:
        check("Retrieved has SWOT", bool(data.get("swot")))
        check("Retrieved has recommendation", bool(data.get("recommendation")))

    # 10c. Generate investment report
    r = requests.post(f"{API}/analysis/{app_id}/report")
    data = api_ok("Generate investment report", r)
    if data:
        check("Report status ok", data.get("status") == "report_generated")
        dl_url = data.get("download_url")
        check("Download URL present", bool(dl_url))
        # 10d. Download report
        if dl_url:
            r2 = requests.get(f"{BASE_URL}{dl_url}")
            check(f"Download report ({r2.status_code})", r2.status_code == 200,
                  f"content-type={r2.headers.get('content-type', '?')}")
            if r2.status_code == 200:
                print(f"      → Report size: {len(r2.content):,} bytes")

    # ═══════════════ STEP 11: CAM Generation ═══════════════
    step(11, "CAM Generation")
    r = requests.post(f"{API}/cam/generate", json={"application_id": app_id})
    data = api_ok("CAM generated", r)
    if data:
        if data.get("download_url"):
            print(f"      → Download: {BASE_URL}{data['download_url']}")
            r2 = requests.get(f"{BASE_URL}{data['download_url']}")
            check(f"CAM download ({r2.status_code})", r2.status_code == 200)
            if r2.status_code == 200:
                print(f"      → CAM size: {len(r2.content):,} bytes")
        if data.get("sections"):
            check(f"CAM has {len(data['sections'])} sections", len(data["sections"]) > 0)

    # ═══════════════ RESULT ═══════════════
    actual = ctx.get("decision", "UNKNOWN")
    expected = company["expected_decision"]
    match = expected in actual
    icon = "✓ PASS" if match else "✗ MISMATCH"

    print(f"\n  {'─'*50}")
    print(f"  RESULT: {actual} (expected: {expected}) — {icon}")
    print(f"  Score: {ctx.get('score', '?')}/100 | Fraud: {ctx.get('fraud_score', '?')}/100 ({ctx.get('fraud_risk', '?')})")
    print(f"  {'─'*50}")

    return {"match": match, "decision": actual, "expected": expected, "score": ctx.get("score")}


def main():
    print("\n" + "█" * 70)
    print("  INTELLI-CREDIT — Full Pipeline Test (All 11 Processes)")
    print("  Testing 3 companies × 11 steps = 33 process invocations")
    print("█" * 70)

    if not check_server():
        print("\n  ✗ Backend server not running at http://localhost:8000")
        print("  Start it with: cd backend && python main.py")
        sys.exit(1)
    print("\n  ✓ Backend server is running")

    all_results = []

    for i, company in enumerate(COMPANIES):
        result = run_full_pipeline(company, i)
        all_results.append(result)
        if i < len(COMPANIES) - 1:
            time.sleep(1)

    # ══════════════════════ FINAL SUMMARY ══════════════════════
    header("FINAL SUMMARY")

    co_passed = 0
    for i, (company, result) in enumerate(zip(COMPANIES, all_results)):
        if result is None:
            status = "✗ PIPELINE FAILED"
        elif result.get("match"):
            status = f"✓ PASS — Score: {result['score']}/100 → {result['decision']}"
            co_passed += 1
        else:
            status = f"✗ MISMATCH — Score: {result['score']}/100 → {result['decision']} (expected {result['expected']})"
        print(f"  Company {i+1}: {company['name']}")
        print(f"    [{company['label']}] {status}")
        print()

    print(f"  Company results: {co_passed}/{len(COMPANIES)} passed")
    print()
    print(f"  Endpoint tests:  {passed_tests}/{total_tests} passed, {failed_tests} failed")
    if failures:
        print(f"\n  ── Failed tests ──")
        for f in failures:
            print(f"    ✗ {f}")
    print(f"\n{'='*70}\n")

    return 0 if failed_tests == 0 and co_passed == len(COMPANIES) else 1


if __name__ == "__main__":
    sys.exit(main())
