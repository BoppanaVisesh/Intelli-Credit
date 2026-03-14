"""
Moneyboxx Investor PDF ingestion runner.

What this does:
1) Fetches PDF links from Moneyboxx investor pages
2) Selects ONLY core files needed for Intelli-Credit CAM pipeline
3) Downloads selected PDFs into backend/downloads/moneyboxx/
4) Creates a new application in Intelli-Credit
5) Uploads selected PDFs for ingestion
6) Triggers parse, scoring, and CAM generation
7) Saves a run summary JSON

Usage:
    python run_moneyboxx_ingest.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import requests

from core.config import get_settings
from core.database import SessionLocal
from models.uploaded_document import UploadedDocument
from pillar1_ingestor.annual_report_parser import AnnualReportParser
from pillar1_ingestor.shareholding_parser import ShareholdingPatternParser

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

SOURCE_PAGES: Dict[str, str] = {
    "annual": "https://moneyboxxfinance.com/annual-reports",
    "financial": "https://moneyboxxfinance.com/financial-results",
    "shareholding": "https://moneyboxxfinance.com/shareholding-pattern",
    "liquidity": "https://moneyboxxfinance.com/liquidity-disclosures",
    "investor": "https://moneyboxxfinance.com/investor-relations",
}

OUT_DIR = Path("downloads") / "moneyboxx"
PDF_RX = re.compile(r'href\s*=\s*["\']([^"\']+?\.pdf(?:\?[^"\']*)?)["\']', re.IGNORECASE)

# Keep ingestion lean. These are enough for CAM synthesis in this project.
MAX_DOCS_BY_CATEGORY: Dict[str, int] = {
    "annual": 1,
    "financial": 6,
    "liquidity": 2,
    "shareholding": 1,
    "investor": 0,
}


@dataclass
class PdfItem:
    category: str
    source_page: str
    url: str


def fetch_pdf_links(page_url: str) -> List[str]:
    html = requests.get(page_url, timeout=30).text
    links = [m.group(1) for m in PDF_RX.finditer(html)]
    resolved: List[str] = []
    for link in links:
        if link.startswith("http://") or link.startswith("https://"):
            resolved.append(link)
        elif link.startswith("/"):
            resolved.append(f"https://moneyboxxfinance.com{link}")
        elif link.startswith("./"):
            resolved.append(f"https://moneyboxxfinance.com/{link[2:]}")
        else:
            resolved.append(f"https://moneyboxxfinance.com/{link}")
    # Keep order, remove duplicates.
    seen = set()
    unique = []
    for u in resolved:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def collect_links() -> List[PdfItem]:
    all_items: List[PdfItem] = []
    for cat, page in SOURCE_PAGES.items():
        links = fetch_pdf_links(page)
        for link in links:
            if "moneyboxxfinance.com" not in link:
                continue
            all_items.append(PdfItem(category=cat, source_page=page, url=link))

    # De-duplicate across pages while preserving first-seen category.
    final_items: List[PdfItem] = []
    seen = set()
    for item in all_items:
        if item.url in seen:
            continue
        seen.add(item.url)
        final_items.append(item)
    return final_items


def _category_rank(item: PdfItem) -> tuple:
    """Sort newer-looking files first within a category."""
    path = item.url.lower()
    # Prefer explicit annual report names where available.
    annual_hint = 1 if "annual-report" in path else 0
    # Extract largest numeric token as recency hint (many files use unix-like ids).
    nums = re.findall(r"\d+", path)
    num_hint = int(max(nums, key=len)) if nums else 0
    return (annual_hint, num_hint)


def select_required_items(items: List[PdfItem]) -> List[PdfItem]:
    """
    Pick only core docs needed for this project pipeline:
    - Annual report (latest)
    - Financial results (recent set)
    - Liquidity disclosures (recent set)
    """
    selected: List[PdfItem] = []
    by_category: Dict[str, List[PdfItem]] = {}

    for item in items:
        by_category.setdefault(item.category, []).append(item)

    for category, cap in MAX_DOCS_BY_CATEGORY.items():
        if cap <= 0:
            continue
        candidates = by_category.get(category, [])
        candidates = sorted(candidates, key=_category_rank, reverse=True)
        selected.extend(candidates[:cap])

    # Final de-duplication safety.
    deduped: List[PdfItem] = []
    seen = set()
    for item in selected:
        if item.url in seen:
            continue
        seen.add(item.url)
        deduped.append(item)
    return deduped


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return cleaned.strip("_") or "file.pdf"


def local_name(item: PdfItem, index: int, annual_primary_done: bool) -> Tuple[str, bool]:
    raw_last = item.url.split("/")[-1].split("?")[0]
    raw_last = sanitize_name(raw_last)

    if item.category == "annual":
        # Parse only one latest annual report through annual parser.
        if not annual_primary_done:
            return f"annual_report_primary_{index:03d}_{raw_last}", True
        return f"portfolio_data_annual_archive_{index:03d}_{raw_last}", annual_primary_done

    if item.category == "financial":
        return f"balance_sheet_financial_results_{index:03d}_{raw_last}", annual_primary_done

    if item.category == "shareholding":
        return f"shareholding_pattern_{index:03d}_{raw_last}", annual_primary_done

    if item.category == "liquidity":
        return f"alm_liquidity_disclosure_{index:03d}_{raw_last}", annual_primary_done

    return f"borrowing_profile_investor_{index:03d}_{raw_last}", annual_primary_done


def download_pdfs(items: List[PdfItem]) -> List[Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    annual_primary_done = False
    files: List[Path] = []

    for i, item in enumerate(items, start=1):
        fname, annual_primary_done = local_name(item, i, annual_primary_done)
        out_path = OUT_DIR / fname
        if out_path.exists() and out_path.stat().st_size > 0:
            files.append(out_path)
            continue

        r = requests.get(item.url, timeout=60)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        files.append(out_path)

    return files


def create_application() -> str:
    payload = {
        "company_name": "Moneyboxx Finance Limited",
        "mca_cin": "L65999DL1994PLC061485",
        "sector": "NBFC",
        "requested_limit_cr": 25.0,
    }
    r = requests.post(f"{API}/applications", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    app_id = data.get("application_id") or data.get("id")
    if not app_id:
        raise RuntimeError(f"No application id in response: {data}")
    return app_id


def upload_documents(app_id: str, files: List[Path]) -> dict:
    multipart = []
    handles = []
    try:
        for p in files:
            fh = open(p, "rb")
            handles.append(fh)
            multipart.append(("files", (p.name, fh, "application/pdf")))

        r = requests.post(
            f"{API}/ingestion/upload-documents",
            data={"application_id": app_id},
            files=multipart,
            timeout=300,
        )
        r.raise_for_status()
        return r.json()
    finally:
        for fh in handles:
            fh.close()


def call_post(url: str, json_body: dict | None = None, timeout: int = 300) -> dict:
    r = requests.post(url, json=json_body, timeout=timeout)
    r.raise_for_status()
    return r.json()


def call_get(url: str, timeout: int = 60) -> dict:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def repair_critical_parses(app_id: str) -> None:
    """
    Re-parse the annual report and shareholding PDF in-process.

    This bypasses stale server-side parser state and ensures the final scoring/CAM
    uses the strongest available extracted signals.
    """
    settings = get_settings()
    annual_parser = AnnualReportParser(settings.GEMINI_API_KEY)
    shareholding_parser = ShareholdingPatternParser(settings.GEMINI_API_KEY)

    db = SessionLocal()
    try:
        docs = db.query(UploadedDocument).filter(UploadedDocument.application_id == app_id).all()
        for doc in docs:
            rel_path = Path("uploads") / doc.file_path
            if not rel_path.exists():
                continue

            if str(doc.document_type) == "DocumentType.ANNUAL_REPORT" or str(doc.document_type) == "ANNUAL_REPORT":
                data = annual_parser.parse_annual_report(str(rel_path))
                doc.parsed_data = json.dumps(data)
            elif str(doc.document_type) == "DocumentType.SHAREHOLDING_PATTERN" or str(doc.document_type) == "SHAREHOLDING_PATTERN":
                data = shareholding_parser.parse(str(rel_path))
                doc.parsed_data = json.dumps(data)

        db.commit()
    finally:
        db.close()


def wait_for_backend(max_attempts: int = 8) -> None:
    """Wait until backend is reachable on /health or /docs."""
    last_err = None
    for attempt in range(1, max_attempts + 1):
        for path in ("/health", "/docs"):
            try:
                r = requests.get(f"{BASE_URL}{path}", timeout=25)
                if r.status_code == 200:
                    return
            except Exception as e:
                last_err = e
        print(f"   Backend not ready (attempt {attempt}/{max_attempts})...")
    raise RuntimeError(f"Backend is not reachable: {last_err}")


def run() -> None:
    print("\n=== Moneyboxx Ingestion Run ===")
    print(f"Backend: {BASE_URL}")

    # API availability check with retry/fallback.
    wait_for_backend()

    print("1) Collecting PDF links...")
    items = collect_links()
    print(f"   Found {len(items)} unique PDFs")

    print("1b) Selecting required PDFs only...")
    selected_items = select_required_items(items)
    print(f"   Selected {len(selected_items)} PDFs for ingestion")

    print("2) Downloading PDFs...")
    local_files = download_pdfs(selected_items)
    print(f"   Downloaded/ready: {len(local_files)} files in {OUT_DIR}")

    print("3) Creating application...")
    app_id = create_application()
    print(f"   Application: {app_id}")

    print("4) Uploading documents...")
    uploaded = upload_documents(app_id, local_files)
    print(f"   Uploaded: {uploaded.get('total_files', 0)}")

    print("5) Parsing documents...")
    parsed = call_post(f"{API}/ingestion/parse-documents/{app_id}", timeout=3600)
    print(f"   Parsed: {parsed.get('parsed_count', 0)} / {parsed.get('total_documents', 0)}")

    print("5b) Repairing annual/shareholding parses locally...")
    repair_critical_parses(app_id)
    parsed_docs = call_get(f"{API}/ingestion/documents/{app_id}", timeout=120)

    print("6) Running scoring...")
    scoring = call_post(f"{API}/scoring/calculate-score?application_id={app_id}", timeout=300)
    decision = scoring.get("decision")
    final_score = scoring.get("final_credit_score")
    print(f"   Score: {final_score} | Decision: {decision}")

    print("7) Generating CAM...")
    cam = call_post(f"{API}/cam/generate", json_body={"application_id": app_id}, timeout=600)
    print(f"   CAM URL: {cam.get('document_url')}")

    summary = {
        "application_id": app_id,
        "pdf_count": len(local_files),
        "upload": uploaded,
        "parse": {
            "parsed_count": parsed.get("parsed_count"),
            "total_documents": parsed.get("total_documents"),
            "results": parsed_docs.get("documents", []),
        },
        "scoring": {
            "final_credit_score": final_score,
            "decision": decision,
            "loan_recommendation": scoring.get("loan_recommendation"),
            "interest_rate": scoring.get("interest_rate"),
            "decision_reasons": scoring.get("decision_reasons"),
        },
        "cam": cam,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / f"run_summary_{app_id}.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== Completed ===")
    print(f"Summary JSON: {out_json}")
    print(f"CAM download endpoint: {BASE_URL}/api/v1/cam/{app_id}/download")


if __name__ == "__main__":
    run()
