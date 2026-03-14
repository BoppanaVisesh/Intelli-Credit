"""
Run full post-ingestion pipeline for a specific application.

Covers:
- Extraction review + extraction run
- External research
- Due diligence
- Fraud detection
- Credit scoring
- Pre-cognitive analysis
- CAM generation

Usage:
    python run_moneyboxx_full_analysis.py APP-2026-FACA6
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
OUT_DIR = Path("downloads") / "moneyboxx"


def call(method: str, url: str, **kwargs):
    r = requests.request(method, url, timeout=300, **kwargs)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    return r.status_code, data


def run(app_id: str) -> Path:
    summary = {
        "application_id": app_id,
        "steps": {},
        "status": "started",
    }

    # Step A: Extraction documents + approve + extract
    status, docs_data = call("GET", f"{API}/extraction/documents/{app_id}")
    summary["steps"]["extraction_documents"] = {"status_code": status, "data": docs_data}

    doc_ids = []
    if status == 200:
        for d in docs_data.get("documents", []):
            fid = d.get("file_id")
            if not fid:
                continue
            doc_ids.append(fid)
            call("PUT", f"{API}/extraction/documents/{fid}/review", json={"action": "approve"})
            call("POST", f"{API}/extraction/extract/{fid}", json={})

    # Step B: External research
    status, app_data = call("GET", f"{API}/applications/{app_id}")
    company_name = app_data.get("company_name", "Moneyboxx Finance Limited") if status == 200 else "Moneyboxx Finance Limited"
    sector = app_data.get("sector", "NBFC") if status == 200 else "NBFC"
    status, research_data = call(
        "POST",
        f"{API}/research/trigger-research",
        json={"application_id": app_id, "company_name": company_name, "sector": sector},
    )
    summary["steps"]["external_research"] = {"status_code": status, "data": research_data}

    # Step C: Due diligence
    dd_payload = {
        "application_id": app_id,
        "insight_type": "site_visit",
        "credit_officer_notes": (
            "Visited core operations and reviewed controls."
            " Management bandwidth is strong, but liquidity discipline and borrowing concentration need monitoring."
            " Recommend tighter monthly covenant tracking and lender diversification."
        ),
    }
    status, dd_data = call("POST", f"{API}/due-diligence/add-notes", json=dd_payload)
    summary["steps"]["due_diligence"] = {"status_code": status, "data": dd_data}

    # Step D: Fraud detection
    status, fraud_data = call("POST", f"{API}/fraud/run-verification/{app_id}")
    summary["steps"]["fraud_detection"] = {"status_code": status, "data": fraud_data}

    # Step E: Credit scoring
    status, scoring_data = call("POST", f"{API}/scoring/calculate-score", params={"application_id": app_id})
    summary["steps"]["credit_scoring"] = {"status_code": status, "data": scoring_data}

    # Step F: Pre-cognitive analysis
    status, analysis_data = call("POST", f"{API}/analysis/run/{app_id}", json={"use_llm": True})
    summary["steps"]["pre_cognitive_analysis"] = {"status_code": status, "data": analysis_data}

    # Step G: CAM generation
    status, cam_data = call("POST", f"{API}/cam/generate", json={"application_id": app_id})
    summary["steps"]["cam_generation"] = {"status_code": status, "data": cam_data}

    # Final app summary for frontend pipeline badges
    status, app_summary = call("GET", f"{API}/applications/{app_id}/summary")
    summary["steps"]["application_summary"] = {"status_code": status, "data": app_summary}

    summary["status"] = "completed"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"full_pipeline_{app_id}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    app_id = sys.argv[1] if len(sys.argv) > 1 else "APP-2026-FACA6"
    output = run(app_id)
    print(f"Saved: {output}")
