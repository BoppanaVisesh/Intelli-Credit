"""
Seed Pipeline Runner — Processes demo applications through the full pipeline.
Runs as a background thread after server startup so demo apps show real results.
"""
import requests
import time
import threading
import os
from pathlib import Path

from core.database import SessionLocal
from models.application import Application, ApplicationStatus

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

# Map demo IDs to test data directories and context
DEMO_PIPELINES = [
    {
        "app_id": "DEMO-APEX-001",
        "data_dir": os.path.join(os.path.dirname(__file__), "test_data", "company1_apex_manufacturing"),
        "company_name": "Apex Manufacturing Pvt Ltd",
        "sector": "Manufacturing",
        "cin": "U28110MH2015PTC265432",
        "promoters": "Rajesh Mehta, Sunita Mehta",
        "dd_notes": "Factory operating at 78% capacity. Well-maintained machinery. Strong management team with 15+ years experience. Clean premises, good inventory management.",
    },
    {
        "app_id": "DEMO-GREENFIELD-002",
        "data_dir": os.path.join(os.path.dirname(__file__), "test_data", "company2_greenfield_logistics"),
        "company_name": "GreenField Logistics Ltd",
        "sector": "Logistics",
        "cin": "U60100DL2018PLC328745",
        "promoters": "Vikram Singh Chauhan",
        "dd_notes": "Fleet appears much smaller than reported. Only 12 trucks observed vs 50 claimed. Warehouse partially empty. Promoter evasive about revenue sources. Multiple shell companies linked.",
    },
    {
        "app_id": "DEMO-ORION-003",
        "data_dir": os.path.join(os.path.dirname(__file__), "test_data", "company3_orion_retail"),
        "company_name": "Orion Retail Pvt Ltd",
        "sector": "Retail",
        "cin": "U52100KA2019PTC354321",
        "promoters": "Anand Rao, Priya Rao",
        "dd_notes": "Retail stores appear under-stocked. Most transactions seem to be inter-company. Customer footfall very low for claimed revenue. Related party transactions dominate the books.",
    },
    {
        "app_id": "DEMO-KINARA-004",
        "pdf_path": os.path.join(os.path.dirname(__file__), "downloads", "kinara_capital", "fy24-annual-report-kinara-capital.pdf"),
        "pdf_filename": "fy24-annual-report-kinara-capital.pdf",
        "document_type": "ANNUAL_REPORT",
        "company_name": "Kinara Capital Private Limited",
        "sector": "NBFC",
        "cin": "U65923KA1996PTC020518",
        "promoters": "Hardika Shah, Kalpana Sankar",
        "dd_notes": "Annual report indicates strong growth and improving profitability. Monitor debt mix and contingent liabilities as portfolio scales.",
    },
    {
        "app_id": "DEMO-TATA-005",
        "pdf_path": os.path.join(os.path.dirname(__file__), "downloads", "tata_capital", "tata-capital-limited.pdf"),
        "pdf_filename": "tata-capital-limited.pdf",
        "document_type": "ANNUAL_REPORT",
        "company_name": "Tata Capital Limited",
        "sector": "NBFC",
        "cin": "U65990MH1991PLC060670",
        "promoters": "Tata Sons Private Limited",
        "dd_notes": "Large diversified lender with strong operating scale; underwriting should monitor leverage and asset quality through cycle.",
    },
    {
        "app_id": "DEMO-MONEYBOXX-006",
        "seed_files": [
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "annual_report_primary_001_1756892129.pdf"),
                "filename": "annual_report_primary_001_1756892129.pdf",
                "document_type": "ANNUAL_REPORT",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_002_1770898482.pdf"),
                "filename": "balance_sheet_financial_results_002_1770898482.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_003_1761828852.pdf"),
                "filename": "balance_sheet_financial_results_003_1761828852.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_004_1753539558.pdf"),
                "filename": "balance_sheet_financial_results_004_1753539558.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_005_1748436574.pdf"),
                "filename": "balance_sheet_financial_results_005_1748436574.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_006_1739353411.pdf"),
                "filename": "balance_sheet_financial_results_006_1739353411.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "balance_sheet_financial_results_007_1739352866.pdf"),
                "filename": "balance_sheet_financial_results_007_1739352866.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "alm_liquidity_disclosure_008_1762339316.pdf"),
                "filename": "alm_liquidity_disclosure_008_1762339316.pdf",
                "document_type": "ALM",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "alm_liquidity_disclosure_009_1754051517.pdf"),
                "filename": "alm_liquidity_disclosure_009_1754051517.pdf",
                "document_type": "ALM",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "moneyboxx", "shareholding_pattern_010_1769083116.pdf"),
                "filename": "shareholding_pattern_010_1769083116.pdf",
                "document_type": "SHAREHOLDING_PATTERN",
            },
        ],
        "company_name": "Moneyboxx Finance Limited",
        "sector": "NBFC",
        "cin": "L65999DL1994PLC061485",
        "promoters": "Dilip Singh, Deepak Aggarwal",
        "dd_notes": "Well-diversified MSME lender with multiple public disclosures; underwriting should monitor leverage, collections efficiency, and liquidity buffers.",
    },
    {
        "app_id": "DEMO-VIVRITI-007",
        "seed_files": [
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "vivriti", "01_Annual Report FY 2024-25.pdf"),
                "filename": "01_Annual Report FY 2024-25.pdf",
                "document_type": "ANNUAL_REPORT",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "vivriti", "02_VCL Standalone Financial Statements - FY 24-25.pdf"),
                "filename": "02_VCL Standalone Financial Statements - FY 24-25.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "vivriti", "03_VCL Consolidated Financial Statements - FY 24-25.pdf"),
                "filename": "03_VCL Consolidated Financial Statements - FY 24-25.pdf",
                "document_type": "BALANCE_SHEET",
            },
            {
                "path": os.path.join(os.path.dirname(__file__), "downloads", "vivriti", "04_Annual Return FY 24-25.pdf"),
                "filename": "04_Annual Return FY 24-25.pdf",
                "document_type": "ANNUAL_REPORT",
            },
        ],
        "company_name": "Vivriti Capital Limited",
        "sector": "NBFC",
        "cin": "U67190TN2007PLC065149",
        "promoters": "Gaurav Kumar, R Sridhar",
        "dd_notes": "Credit profile should consider liability franchise, asset quality, and risk management in structured credit operations.",
    },
]


def _wait_for_server(timeout=30):
    """Block until the server responds."""
    for _ in range(timeout):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def _already_processed(app_id):
    """Check if the demo app already has pipeline results."""
    try:
        r = requests.get(f"{API}/applications/{app_id}/summary", timeout=5)
        if r.status_code == 200:
            pipeline = r.json().get("pipeline", {})
            # If scoring and CAM are done, skip
            return (pipeline.get("scoring", {}).get("status") == "completed" and
                    pipeline.get("cam", {}).get("status") == "completed")
    except Exception:
        pass
    return False


def _process_demo_app(cfg):
    """Run the full pipeline on one demo application."""
    app_id = cfg["app_id"]
    label = cfg["company_name"]

    # 1. Upload documents (only if app has no documents yet)
    existing_docs_count = 0
    r_docs = requests.get(f"{API}/ingestion/documents/{app_id}")
    if r_docs.status_code == 200:
        existing_docs_count = r_docs.json().get("total_documents", 0)

    if existing_docs_count > 0:
        r = None
    else:
        files_to_upload = []
        file_handles = []

        if "data_dir" in cfg:
            data_dir = cfg["data_dir"]
            for fname, ctype in [
                ("annual_report.json", "application/json"),
                ("bank_statement.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("gst_returns.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("itr_returns.json", "application/json"),
                ("balance_sheet.json", "application/json"),
            ]:
                fpath = os.path.join(data_dir, fname)
                if os.path.exists(fpath):
                    fh = open(fpath, "rb")
                    file_handles.append(fh)
                    files_to_upload.append(("files", (fname, fh, ctype)))
            upload_data = {"application_id": app_id}
        elif "seed_files" in cfg:
            for seed_file in cfg["seed_files"]:
                seed_path = Path(seed_file["path"])
                if not seed_path.exists():
                    print(f"      ✗ Missing seed PDF for {label}: {seed_path}")
                    return False
                fh = open(seed_path, "rb")
                file_handles.append(fh)
                files_to_upload.append((fh, seed_file))

            for fh, seed_file in files_to_upload:
                r = requests.post(
                    f"{API}/ingestion/upload-documents",
                    data={
                        "application_id": app_id,
                        "document_type": seed_file["document_type"],
                    },
                    files=[("files", (seed_file.get("filename", Path(seed_file["path"]).name), fh, "application/pdf"))],
                )
                if r.status_code != 200:
                    print(f"      ✗ Upload failed for {label}: {r.status_code}")
                    for open_fh in file_handles:
                        open_fh.close()
                    return False
            for fh in file_handles:
                fh.close()
            r = None
        else:
            pdf_path = Path(cfg["pdf_path"])
            if not pdf_path.exists():
                print(f"      ✗ Missing seed PDF for {label}: {pdf_path}")
                return False
            fh = open(pdf_path, "rb")
            file_handles.append(fh)
            files_to_upload.append(("files", (cfg.get("pdf_filename", pdf_path.name), fh, "application/pdf")))
            upload_data = {
                "application_id": app_id,
                "document_type": cfg.get("document_type", "ANNUAL_REPORT"),
            }

        if files_to_upload:
            r = requests.post(f"{API}/ingestion/upload-documents", data=upload_data, files=files_to_upload)
            for fh in file_handles:
                fh.close()

            if r.status_code != 200:
                print(f"      ✗ Upload failed for {label}: {r.status_code}")
                return False

    # 2. Parse documents
    r = requests.post(f"{API}/ingestion/parse-documents/{app_id}")
    if r.status_code != 200:
        print(f"      ✗ Parse failed for {label}: {r.status_code}")
        return False

    # 3. Extraction — extract each document with defaults
    r = requests.get(f"{API}/extraction/documents/{app_id}")
    if r.status_code == 200:
        for doc in r.json().get("documents", []):
            fid = doc["file_id"]
            requests.put(f"{API}/extraction/documents/{fid}/review", json={"action": "approve"})
            requests.post(f"{API}/extraction/extract/{fid}", json={})

    # 4. Fraud detection
    r = requests.post(f"{API}/fraud/run-verification/{app_id}")
    if r.status_code != 200:
        print(f"      ⚠ Fraud detection failed for {label} — continuing")

    # 5. External research
    r = requests.post(f"{API}/research/trigger-research", json={
        "application_id": app_id,
        "company_name": cfg["company_name"],
        "sector": cfg["sector"],
    })
    if r.status_code != 200:
        print(f"      ⚠ Research failed for {label} — continuing")

    # 6. Due diligence notes
    r = requests.post(f"{API}/due-diligence/add-notes", json={
        "application_id": app_id,
        "insight_type": "site_visit",
        "credit_officer_notes": cfg["dd_notes"],
    })
    if r.status_code != 200:
        print(f"      ⚠ DD notes failed for {label} — continuing")

    # 7. Credit scoring
    r = requests.post(f"{API}/scoring/calculate-score", params={"application_id": app_id})
    if r.status_code != 200:
        print(f"      ✗ Scoring failed for {label}: {r.status_code}")
        return False
    score_data = r.json()

    # 8. Pre-cognitive analysis
    r = requests.post(f"{API}/analysis/run/{app_id}", json={"use_llm": True}, timeout=120)
    if r.status_code != 200:
        print(f"      ⚠ Analysis failed for {label} — continuing")

    # 9. CAM generation
    r = requests.post(f"{API}/cam/generate", json={"application_id": app_id})
    if r.status_code != 200:
        print(f"      ⚠ CAM generation failed for {label} — continuing")

    # 10. Mark application as COMPLETED
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == app_id).first()
        if app:
            app.status = ApplicationStatus.COMPLETED
            db.commit()
    finally:
        db.close()

    decision = score_data.get("decision", "?")
    score = score_data.get("final_credit_score", "?")
    print(f"      ✓ {label}: Score {score}/100 → {decision}")
    return True


def run_seed_pipeline():
    """Background worker: wait for server, then process all demo apps."""
    print("\n   🔄 Seed pipeline: waiting for server...")
    if not _wait_for_server():
        print("   ✗ Seed pipeline: server not reachable — skipping")
        return

    processed = 0
    skipped = 0
    for cfg in DEMO_PIPELINES:
        if _already_processed(cfg["app_id"]):
            skipped += 1
            continue
        try:
            if _process_demo_app(cfg):
                processed += 1
        except Exception as e:
            print(f"      ✗ Pipeline error for {cfg['company_name']}: {e}")

    if skipped == len(DEMO_PIPELINES):
        print("   ✅ Seed pipeline: all demo apps already processed — skipped")
    elif processed > 0:
        print(f"   ✅ Seed pipeline: processed {processed} demo application(s)")


def start_seed_pipeline_thread():
    """Launch the seed pipeline in a daemon thread (non-blocking)."""
    t = threading.Thread(target=run_seed_pipeline, daemon=True, name="seed-pipeline")
    t.start()
    return t
