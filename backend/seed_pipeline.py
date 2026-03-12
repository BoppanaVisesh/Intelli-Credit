"""
Seed Pipeline Runner — Processes the 3 demo applications through the full pipeline.
Runs as a background thread after server startup so demo apps show real results.
"""
import requests
import time
import threading
import os

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
    data_dir = cfg["data_dir"]
    label = cfg["company_name"]

    # 1. Upload 5 documents
    files_to_upload = []
    file_handles = []
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

    r = requests.post(f"{API}/ingestion/upload-documents",
                      data={"application_id": app_id}, files=files_to_upload)
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
