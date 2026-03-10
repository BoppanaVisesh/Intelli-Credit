"""
End-to-End Pipeline Test — Runs all 8 steps for 3 test companies.

Company 1: Apex Manufacturing Pvt Ltd    → Healthy → expect APPROVE
Company 2: GreenField Logistics Ltd      → GST fraud → expect REJECT
Company 3: Orion Retail Pvt Ltd          → Circular trading → expect REJECT

Usage:
    python run_e2e_test.py

Requires: backend server running on http://localhost:8000
"""
import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

# Test companies
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


def header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def step(num, text):
    print(f"\n  Step {num}: {text}")
    print(f"  {'-'*50}")


def check_server():
    """Check if backend server is running."""
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def run_pipeline(company: dict, index: int):
    """Run full 8-step pipeline for one company."""
    header(f"Company {index+1}: {company['name']} [{company['label']}]")
    print(f"  Expected decision: {company['expected_decision']}")
    
    results = {}
    
    # ── Step 1: Create Application ──
    step(1, "Create Application")
    r = requests.post(f"{API}/applications", json={
        "company_name": company["name"],
        "mca_cin": company["cin"],
        "sector": company["sector"],
        "requested_limit_cr": company["loan_cr"],
    })
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        return None
    
    app_data = r.json()
    app_id = app_data.get("application_id") or app_data.get("id")
    print(f"    ✓ Application created: {app_id}")
    results["application_id"] = app_id
    
    # ── Step 2: Upload Documents ──
    step(2, "Upload Documents")
    data_dir = company["data_dir"]
    
    files_to_upload = [
        ("files", ("annual_report.json", open(f"{data_dir}/annual_report.json", "rb"), "application/json")),
        ("files", ("bank_statement.xlsx", open(f"{data_dir}/bank_statement.xlsx", "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ("files", ("gst_returns.xlsx", open(f"{data_dir}/gst_returns.xlsx", "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ]
    
    r = requests.post(
        f"{API}/ingestion/upload-documents",
        data={"application_id": app_id},
        files=files_to_upload,
    )
    
    # Close file handles
    for _, (_, fh, _) in files_to_upload:
        fh.close()
    
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        return None
    
    upload_data = r.json()
    print(f"    ✓ Uploaded {upload_data['total_files']} files")
    for f in upload_data["uploaded_files"]:
        print(f"      - {f['filename']} → {f['document_type']} (conf: {f['classification_confidence']:.0%})")
    
    # ── Step 3: Parse Documents ──
    step(3, "Parse Documents")
    r = requests.post(f"{API}/ingestion/parse-documents/{app_id}")
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        return None
    
    parse_data = r.json()
    print(f"    ✓ Parsed {parse_data['parsed_count']} documents")
    for doc in parse_data.get("results", []):
        status = doc["parse_status"]
        icon = "✓" if status == "COMPLETED" else "✗"
        print(f"      {icon} {doc['filename']} → {status}")
        if status == "COMPLETED" and doc.get("parsed_data"):
            pd_data = doc["parsed_data"]
            if doc["document_type"] == "BANK_STATEMENT":
                print(f"        Inflows: ₹{pd_data.get('total_inflows_cr', 0):.2f} Cr, Outflows: ₹{pd_data.get('total_outflows_cr', 0):.2f} Cr")
            elif doc["document_type"] == "GST_RETURN":
                print(f"        GSTR-1 Sales: ₹{pd_data.get('gstr_1_sales_cr', 0):.2f} Cr")
            elif doc["document_type"] == "ANNUAL_REPORT":
                print(f"        Revenue: ₹{pd_data.get('revenue_cr', 0):.2f} Cr, Auditor: {pd_data.get('auditor_opinion', 'N/A')}")
    
    # ── Step 4: Run Research ──
    step(4, "Run External Research (Tavily API)")
    r = requests.post(f"{API}/research/trigger-research", json={
        "application_id": app_id,
        "company_name": company["name"],
        "sector": company["sector"],
    })
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        # Research can fail if no Tavily key — continue anyway
        print(f"    ⚠ Continuing without research data...")
    else:
        research_data = r.json()
        print(f"    ✓ Research complete: {research_data.get('completed_tasks', 0)}/{research_data.get('completed_tasks', 0) + research_data.get('failed_tasks', 0)} engines, overall_risk={research_data.get('overall_risk', '?')}")
        for finding in research_data.get("results", []):
            print(f"      - [{finding.get('type', '?')}] risk={finding.get('risk', '?')}, status={finding.get('status', '?')}")
    
    # ── Step 5: Add Due Diligence Notes ──
    step(5, "Add Due Diligence Notes")
    r = requests.post(f"{API}/due-diligence/add-notes", json={
        "application_id": app_id,
        "insight_type": "site_visit",
        "credit_officer_notes": company["dd_notes"],
    })
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        print(f"    ⚠ Continuing without DD notes...")
    else:
        dd_data = r.json()
        print(f"    ✓ Notes analyzed")
        if "analysis" in dd_data:
            analysis = dd_data["analysis"]
            print(f"      Severity: {analysis.get('severity', 'N/A')}")
            print(f"      Score adjustment: {analysis.get('score_adjustment', 0)}")
            print(f"      Risk category: {analysis.get('risk_category', 'N/A')}")
    
    # ── Step 6: Run Fraud Detection ──
    step(6, "Run Fraud Detection")
    r = requests.post(f"{API}/fraud/run-verification/{app_id}")
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        return None
    
    fraud_data = r.json()
    results["fraud"] = fraud_data
    print(f"    ✓ Fraud analysis complete")
    print(f"      Combined score: {fraud_data['combined_fraud_score']}/100")
    print(f"      Risk level: {fraud_data['overall_risk_level']}")
    print(f"      Red flags: {fraud_data['total_flags']}")
    if fraud_data.get("all_flags"):
        for flag in fraud_data["all_flags"][:5]:
            print(f"        🚩 {flag}")
    
    cv = fraud_data.get("cross_verification", {})
    ct = fraud_data.get("circular_trading", {})
    ml = fraud_data.get("ml_prediction", {})
    print(f"      Cross-verification score: {cv.get('rule_score', 0)}")
    print(f"      Circular trading score: {ct.get('combined_score', 0)}")
    print(f"      ML prediction: {ml.get('prediction', 'N/A')} (prob: {ml.get('fraud_probability', 0):.2%})")
    
    # Graph analysis details
    ga = ct.get("graph_analysis", {})
    if ga.get("entities", 0) > 0:
        print(f"      Graph: {ga['entities']} entities, {ga['edges']} edges, {ga.get('cycle_count', 0)} cycles, score={ga.get('graph_risk_score', 0)}")
        if ga.get("cycles_detected"):
            for c in ga["cycles_detected"][:3]:
                print(f"        🔄 Cycle: {' → '.join(c)} → {c[0]}")
        ca = ga.get("concentration_analysis", {})
        if ca.get("reciprocal_counterparties"):
            print(f"        ⚠️ Reciprocal counterparties: {', '.join(ca['reciprocal_counterparties'])}")
    
    # ── Step 7: Run Credit Scoring ──
    step(7, "Run Credit Scoring (Five Cs)")
    r = requests.post(f"{API}/scoring/calculate-score", params={"application_id": app_id})
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        return None
    
    score_data = r.json()
    results["scoring"] = score_data
    print(f"    ✓ Scoring complete")
    print(f"      Final Credit Score: {score_data.get('final_credit_score', 'N/A')}/100")
    print(f"      Decision: {score_data.get('decision', 'N/A')}")
    print(f"      Risk Grade: {score_data.get('risk_grade', 'N/A')}")
    
    # Sub-scores
    sub = score_data.get("sub_scores", {})
    if sub:
        print(f"      Sub-scores:")
        for factor, data in sub.items():
            if isinstance(data, dict):
                print(f"        {factor}: {data.get('score', 'N/A')}/100 (weight: {data.get('weight', 'N/A')})")
    
    loan = score_data.get("loan_recommendation", {})
    rate = score_data.get("interest_rate", {})
    print(f"      Recommended Loan: ₹{loan.get('recommended_limit_cr', 0):.2f} Cr")
    print(f"      Interest Rate: {rate.get('final_interest_rate', 'N/A')}% ({rate.get('rate_category', 'N/A')})")
    
    reasons = score_data.get("decision_reasons", [])
    if reasons:
        print(f"      Key Reasons:")
        for reason in reasons[:5]:
            icon = "+" if reason.get("impact") == "POSITIVE" else "-"
            print(f"        [{icon}] {reason.get('text', '')}")
    
    # ── Step 8: Generate CAM ──
    step(8, "Generate CAM Document")
    r = requests.post(f"{API}/cam/generate", json={"application_id": app_id})
    if r.status_code != 200:
        print(f"    FAILED: {r.status_code} — {r.text[:200]}")
        print(f"    ⚠ CAM generation failed, but scoring was successful")
    else:
        cam_data = r.json()
        print(f"    ✓ CAM generated")
        if cam_data.get("download_url"):
            print(f"      Download: {BASE_URL}{cam_data['download_url']}")
        if cam_data.get("sections"):
            print(f"      Sections: {len(cam_data['sections'])}")
    
    # ── Summary ──
    actual_decision = score_data.get("decision", "UNKNOWN")
    expected = company["expected_decision"]
    match = "✓ PASS" if expected in actual_decision else "✗ MISMATCH"
    
    print(f"\n  {'─'*50}")
    print(f"  RESULT: {actual_decision} (expected: {expected}) — {match}")
    print(f"  Score: {score_data.get('final_credit_score', '?')}/100")
    print(f"  {'─'*50}")
    
    results["decision"] = actual_decision
    results["expected"] = expected
    results["score"] = score_data.get("final_credit_score")
    results["match"] = expected in actual_decision
    
    return results


def main():
    print("\n" + "█" * 70)
    print("  INTELLI-CREDIT — Full E2E Pipeline Test")
    print("  Testing 3 companies × 8 pipeline steps")
    print("█" * 70)
    
    # Check server
    if not check_server():
        print("\n  ✗ Backend server not running at http://localhost:8000")
        print("  Start it with: cd backend && python main.py")
        sys.exit(1)
    print("\n  ✓ Backend server is running")
    
    all_results = []
    
    for i, company in enumerate(COMPANIES):
        result = run_pipeline(company, i)
        all_results.append(result)
        
        if i < len(COMPANIES) - 1:
            time.sleep(1)  # Brief pause between companies
    
    # ── Final Summary ──
    header("FINAL SUMMARY")
    
    passed = 0
    total = len(COMPANIES)
    
    for i, (company, result) in enumerate(zip(COMPANIES, all_results)):
        if result is None:
            status = "✗ PIPELINE FAILED"
        elif result.get("match"):
            status = f"✓ PASS — Score: {result['score']}/100 → {result['decision']}"
            passed += 1
        else:
            status = f"✗ MISMATCH — Score: {result['score']}/100 → {result['decision']} (expected {result['expected']})"
        
        print(f"  Company {i+1}: {company['name']}")
        print(f"    [{company['label']}] {status}")
        print()
    
    print(f"  Results: {passed}/{total} passed")
    print(f"{'='*70}\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
