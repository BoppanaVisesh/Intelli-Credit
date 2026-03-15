"""
Liquidity Disclosure / ALM Parser
Extracts funding concentration and short-term liability signals from RBI liquidity disclosures.
"""

import json
import os
import re
from typing import Any, Dict

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from pillar1_ingestor.pdf_parser import PDFParser


class LiquidityDisclosureParser:
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key and genai is not None:
            genai.configure(api_key=self.api_key)
        self.pdf_parser = PDFParser()

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        if not os.path.exists(pdf_path):
            return self._default_data(note="File not found")

        parsed = self.pdf_parser.parse_pdf(pdf_path)
        text = (parsed.get("text") or "").strip()
        tables = parsed.get("tables") or []
        if not text:
            return self._default_data(note="No extractable text found")

        table_blobs = []
        for table in tables[:5]:
            for row in table[:12]:
                cleaned = [str(cell).strip() for cell in row if cell]
                if cleaned:
                    table_blobs.append(" | ".join(cleaned))

        if not self.api_key or genai is None:
            return self._regex_fallback(text, table_blobs, note="GEMINI_API_KEY not configured")

        condensed = text[:20000]
        if table_blobs:
            condensed += "\n\nTABLE EXTRACTS:\n" + "\n".join(table_blobs[:50])

        try:
            prompt = f"""Extract liquidity-risk metrics from this RBI/NBFC liquidity disclosure and return ONLY valid JSON.

DISCLOSURE TEXT:
{condensed}

JSON schema:
{{
  "disclosure_period": "e.g. Sep 2025",
  "top10_borrowings_cr": 0.0,
  "top10_borrowings_pct": 0.0,
  "significant_counterparty_amount_cr": 0.0,
  "significant_counterparty_liabilities_pct": 0.0,
  "short_term_liabilities_pct_public_funds": 0.0,
  "short_term_liabilities_pct_total_liabilities": 0.0,
  "short_term_liabilities_pct_total_assets": 0.0,
  "liquidity_management_note": "short summary"
}}

Rules:
- Use percentages without % signs.
- Use crore values as numbers only.
- If a field is unavailable, use 0 or empty string.
- Return JSON only.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text.strip())
            default = self._default_data()
            default.update(data)
            return default
        except Exception as e:
            return self._regex_fallback(text, table_blobs, note=f"Liquidity parsing fallback used: {e}")

    def _regex_fallback(self, text: str, table_blobs: list[str], note: str = "") -> Dict[str, Any]:
        corpus = " ".join([text] + table_blobs)
        normalized = re.sub(r"\s+", " ", corpus)

        top10_match = re.search(
            r"Top\s*10\s*borrowings.*?Amount\s*in\s*Rs\.?\s*Crore\*?\s*([0-9]+(?:\.[0-9]+)?)\s*%\s*of\s*total\s*borrowings\s*([0-9]+(?:\.[0-9]+)?)%",
            normalized,
            re.IGNORECASE,
        )
        sig_match = re.search(
            r"significant\s*counterpar.*?([0-9]+(?:\.[0-9]+)?)\s*(?:Not Applicable|[0-9]+(?:\.[0-9]+)?%)\s*([0-9]+(?:\.[0-9]+)?)%",
            normalized,
            re.IGNORECASE,
        )
        stl_match = re.search(
            r"Other\s*short\s*-?term\s*liabilit(?:y|ies)\s*as\s*a\s*%\s*of\s*([0-9]+(?:\.[0-9]+)?)%\s*([0-9]+(?:\.[0-9]+)?)%\s*([0-9]+(?:\.[0-9]+)?)%",
            normalized,
            re.IGNORECASE,
        )
        period_match = re.search(r"as on\s+([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})", normalized, re.IGNORECASE)

        data = self._default_data(note=note)
        if period_match:
            data["disclosure_period"] = period_match.group(1)
        if top10_match:
            data["top10_borrowings_cr"] = float(top10_match.group(1))
            data["top10_borrowings_pct"] = float(top10_match.group(2))
        if sig_match:
            data["significant_counterparty_amount_cr"] = float(sig_match.group(1))
            data["significant_counterparty_liabilities_pct"] = float(sig_match.group(2))
        if stl_match:
            data["short_term_liabilities_pct_public_funds"] = float(stl_match.group(1))
            data["short_term_liabilities_pct_total_liabilities"] = float(stl_match.group(2))
            data["short_term_liabilities_pct_total_assets"] = float(stl_match.group(3))

        if any(data[k] for k in (
            "top10_borrowings_pct",
            "significant_counterparty_liabilities_pct",
            "short_term_liabilities_pct_total_liabilities",
        )):
            data["liquidity_management_note"] = "Extracted using local text fallback"

        return data

    def _default_data(self, note: str = "") -> Dict[str, Any]:
        return {
            "disclosure_period": "Unknown",
            "top10_borrowings_cr": 0.0,
            "top10_borrowings_pct": 0.0,
            "significant_counterparty_amount_cr": 0.0,
            "significant_counterparty_liabilities_pct": 0.0,
            "short_term_liabilities_pct_public_funds": 0.0,
            "short_term_liabilities_pct_total_liabilities": 0.0,
            "short_term_liabilities_pct_total_assets": 0.0,
            "liquidity_management_note": note or "Not available",
        }