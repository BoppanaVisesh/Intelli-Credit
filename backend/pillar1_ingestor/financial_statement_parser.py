"""
Financial Statement Parser
Extracts structured financial metrics from quarterly / standalone financial-result PDFs.
"""

import json
import os
import re
from typing import Any, Dict

import google.generativeai as genai

from pillar1_ingestor.pdf_parser import PDFParser


class FinancialStatementParser:
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.pdf_parser = PDFParser()

    def parse(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return self._default_data(note="File not found")

        if file_path.lower().endswith(".json"):
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                default = self._default_data()
                default.update(data)
                return default
            except Exception as e:
                return self._default_data(note=f"JSON load failed: {e}")

        parsed = self.pdf_parser.parse_pdf(file_path)
        text = (parsed.get("text") or "").strip()
        tables = parsed.get("tables") or []
        if not text:
            return self._default_data(note="No extractable text found")

        table_blobs = []
        for table in tables[:5]:
            for row in table[:15]:
                cleaned = [str(cell).strip() for cell in row if cell]
                if cleaned:
                    table_blobs.append(" | ".join(cleaned))

        fallback_text = text
        if table_blobs:
            fallback_text += "\n\nTABLE EXTRACTS:\n" + "\n".join(table_blobs[:120])

        condensed = text[:14000]
        if len(text) > 24000:
            condensed += "\n\n" + text[-10000:]
        elif len(text) > 14000:
            condensed += "\n\n" + text[14000:22000]
        if table_blobs:
            condensed += "\n\nTABLE EXTRACTS:\n" + "\n".join(table_blobs[:60])

        if not self.api_key:
            return self._regex_fallback(fallback_text, note="Extracted using local text fallback (model unavailable)")

        try:
            prompt = f"""Extract structured financial metrics from this financial results / balance-sheet style PDF and return ONLY valid JSON.

DOCUMENT TEXT:
{condensed}

JSON schema:
{{
  "period": "e.g. Q2 FY2025-26 or Sep 2025",
  "revenue_cr": 0.0,
  "net_profit_cr": 0.0,
  "ebitda_cr": 0.0,
  "total_debt_cr": 0.0,
  "total_equity_cr": 0.0,
  "total_assets_cr": 0.0,
  "current_assets_cr": 0.0,
  "current_liabilities_cr": 0.0,
  "fixed_assets_cr": 0.0,
  "note": "short summary"
}}

Rules:
- Convert monetary values to Indian crores.
- If a value is not present, use 0.
- Return JSON only.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=3000,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text.strip())
            default = self._default_data()
            default.update(data)
            return default
        except Exception:
            return self._regex_fallback(
                fallback_text,
                note="Extracted using local text fallback (model response unavailable)",
            )

    def _regex_fallback(self, text: str, note: str = "") -> Dict[str, Any]:
        normalized = re.sub(r"\s+", " ", text)
        data = self._default_data(note=note)

        patterns = {
            "revenue_cr": [r"revenue from operations[^0-9-]{0,40}([0-9]+(?:\.[0-9]+)?)", r"total income[^0-9-]{0,40}([0-9]+(?:\.[0-9]+)?)"],
            "net_profit_cr": [r"profit(?:/|\s*)\(?loss\)?[^0-9-]{0,40}([0-9]+(?:\.[0-9]+)?)", r"profit after tax[^0-9-]{0,40}([0-9]+(?:\.[0-9]+)?)"],
            "ebitda_cr": [r"ebitda[^0-9-]{0,20}([0-9]+(?:\.[0-9]+)?)"],
            "total_assets_cr": [r"(?<!to\s)\btotal assets\b\s*([0-9]+(?:\.[0-9]+)?)"],
            "current_assets_cr": [r"current assets[^0-9-]{0,30}([0-9]+(?:\.[0-9]+)?)"],
            "current_liabilities_cr": [r"current liabilities[^0-9-]{0,30}([0-9]+(?:\.[0-9]+)?)"],
            "total_equity_cr": [r"\btotal equity\b\s*([0-9]+(?:\.[0-9]+)?)", r"shareholders'? funds\s*([0-9]+(?:\.[0-9]+)?)"],
            "total_debt_cr": [r"\btotal borrowings\b\s*([0-9]+(?:\.[0-9]+)?)"],
            "fixed_assets_cr": [r"fixed assets[^0-9-]{0,30}([0-9]+(?:\.[0-9]+)?)", r"property plant and equipment[^0-9-]{0,30}([0-9]+(?:\.[0-9]+)?)"],
        }

        for key, regexes in patterns.items():
            for regex in regexes:
                match = re.search(regex, normalized, re.IGNORECASE)
                if match:
                    data[key] = float(match.group(1))
                    break

        # Moneyboxx filings frequently contain statement blocks in lakhs with OCR-heavy punctuation.
        # Apply deterministic extraction and convert values to crores when available.
        self._enrich_with_statement_block(normalized, data)

        period_patterns = [
            r"as\s+at\s+([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})",
            r"quarter\s+and\s+half\s+year\s+ended\s+([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})",
            r"quarter\s+ended\s+([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})",
            r"financial\s+year\s+ended\s+([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})",
            r"(Q[1-4]\s*FY\s*[0-9-]+|[A-Za-z]+\s+[0-9]{4})",
        ]
        for period_regex in period_patterns:
            period_match = re.search(period_regex, normalized, re.IGNORECASE)
            if period_match:
                data["period"] = period_match.group(1)
                break

        sanitized = self._sanitize_ocr_spikes(data)
        if sanitized:
            data["note"] = (data.get("note") or "").strip()
            if data["note"]:
                data["note"] += " | "
            data["note"] += "Fallback numeric sanity applied"

        if any(data[k] for k in (
            "revenue_cr",
            "net_profit_cr",
            "total_assets_cr",
            "total_equity_cr",
        )):
            if not note:
                data["note"] = "Extracted using local text fallback"

        self._set_document_quality(data)

        return data

    def _enrich_with_statement_block(self, normalized_text: str, data: Dict[str, Any]) -> None:
        def first_amount(regexes, max_value=None):
            for regex in regexes:
                match = re.search(regex, normalized_text, re.IGNORECASE)
                if not match:
                    continue
                value = self._parse_numeric_token(match.group(1))
                if value is None:
                    continue
                if max_value is not None and value > max_value:
                    continue
                return value
            return None

        # Core statement values are usually printed in lakhs in Moneyboxx filings.
        total_assets_lakhs = first_amount(
            [
                r"(?<!to\s)\btotal assets\b\s*([0-9][0-9,\.]{2,20})",
                r"\btotal liabilities and equities\b\s*([0-9][0-9,\.]{2,20})",
            ]
        )
        if total_assets_lakhs:
            data["total_assets_cr"] = round(total_assets_lakhs / 100.0, 2)

        networth_lakhs = first_amount(
            [
                r"net\s*worth\s*\(in\s*lakhs\)[^0-9-]{0,20}([0-9][0-9,\.]{2,20})",
                r"net\s*worth[^0-9-]{0,80}rs\.?\s*in\s*lakhs[^0-9-]{0,10}([0-9][0-9,\.]{2,20})",
                r"networth[^0-9-]{0,60}([0-9][0-9,\.]{2,20})",
            ]
        )
        equity_share_lakhs = first_amount([r"equity share capital[^0-9-]{0,20}([0-9][0-9,\.]{2,20})"])
        other_equity_lakhs = first_amount([r"other\s+equity[^0-9-]{0,20}([0-9][0-9,\.]{2,20})"])
        component_equity_cr = None
        if equity_share_lakhs is not None and other_equity_lakhs is not None:
            component_equity_cr = round((equity_share_lakhs + other_equity_lakhs) / 100.0, 2)

        networth_cr = round(networth_lakhs / 100.0, 2) if networth_lakhs else None
        if networth_cr and networth_cr > 1000:
            networth_cr = None
        if networth_cr and component_equity_cr and networth_cr > (component_equity_cr * 3):
            networth_cr = None

        if networth_cr and (data["total_equity_cr"] == 0.0 or data["total_equity_cr"] > 10000.0):
            data["total_equity_cr"] = networth_cr
        elif component_equity_cr and data["total_equity_cr"] == 0.0:
            data["total_equity_cr"] = component_equity_cr

        debt_equity_ratio = first_amount([r"debt[-\s]*equity\s*ratio[^0-9-]{0,140}([0-9]+(?:\.[0-9]+)?)"], max_value=5)
        debt_assets_ratio = first_amount(
            [
                r"total debts to total assets[^\n]{0,140}?/\s*total\s*([0-9]+(?:\.[0-9]+)?)\s*assets",
                r"total debts to total assets[^0-9-]{0,140}([0-9]+\.[0-9]+)",
                r"total debts to total assets[^0-9-]{0,140}([0-9]+(?:\.[0-9]+)?)",
            ],
            max_value=200,
        )

        if debt_assets_ratio is not None and debt_assets_ratio > 10:
            debt_assets_ratio = debt_assets_ratio / 100.0

        if debt_equity_ratio is not None and data["total_equity_cr"] > 0:
            inferred_debt = round(debt_equity_ratio * data["total_equity_cr"], 2)
            if data["total_debt_cr"] == 0.0 or data["total_debt_cr"] < (0.25 * inferred_debt):
                data["total_debt_cr"] = inferred_debt
        elif debt_assets_ratio is not None and data["total_assets_cr"] > 0:
            inferred_debt = round(debt_assets_ratio * data["total_assets_cr"], 2)
            if data["total_debt_cr"] == 0.0:
                data["total_debt_cr"] = inferred_debt

        # Second pass: if statement total-assets line is not extractable, recover assets
        # from debt and debt-to-assets ratio only under conservative thresholds.
        if (
            data["total_assets_cr"] == 0.0
            and data["total_debt_cr"] >= 100.0
            and debt_assets_ratio is not None
            and 0.10 <= debt_assets_ratio <= 1.50
        ):
            data["total_assets_cr"] = round(data["total_debt_cr"] / debt_assets_ratio, 2)

    def _parse_numeric_token(self, raw_token: str):
        if not raw_token:
            return None

        matches = re.findall(r"[0-9][0-9,\.]{0,20}", raw_token)
        if not matches:
            return None

        token = matches[0]

        if token.count(".") > 1 and "," not in token:
            parts = token.split(".")
            if len(parts[-1]) <= 2:
                token = "".join(parts[:-1]) + "." + parts[-1]
            else:
                token = "".join(parts)

        if token.count(".") > 1:
            parts = token.split(".")
            token = "".join(parts[:-1]) + "." + parts[-1]

        token = token.replace(",", "")
        try:
            return float(token)
        except ValueError:
            return None

    def _set_document_quality(self, data: Dict[str, Any]) -> None:
        core_values = [
            data.get("total_assets_cr", 0.0),
            data.get("total_equity_cr", 0.0),
            data.get("total_debt_cr", 0.0),
            data.get("revenue_cr", 0.0),
            data.get("net_profit_cr", 0.0),
        ]

        if not any(core_values):
            data["document_quality"] = {
                "status": "non_statement",
                "summary": "No financial statement totals detected. This appears to be a disclosure or certificate, not a usable statement page.",
                "should_exclude_from_scoring": True,
            }
            return

        missing_core = sum(
            1
            for key in ("total_assets_cr", "total_equity_cr", "total_debt_cr")
            if not data.get(key)
        )
        if missing_core >= 1:
            data["document_quality"] = {
                "status": "partial",
                "summary": "Some financial anchors were recovered, but this extraction is incomplete and should be reviewed before relying on all fields.",
                "should_exclude_from_scoring": False,
            }
            return

        data["document_quality"] = {
            "status": "usable",
            "summary": "Core financial totals were extracted and can be used in downstream scoring.",
            "should_exclude_from_scoring": False,
        }

    def _sanitize_ocr_spikes(self, data: Dict[str, Any]) -> bool:
        changed = False

        def normalize_down(value: float, ceiling: float) -> float:
            v = float(value)
            while v > ceiling and v >= 1000:
                v = v / 10.0
            return round(v, 2)

        assets = float(data.get("total_assets_cr") or 0.0)
        revenue = float(data.get("revenue_cr") or 0.0)
        profit = float(data.get("net_profit_cr") or 0.0)

        if revenue > 0:
            ceiling = 10000.0
            if assets > 0:
                # For these filings, revenue should not be orders of magnitude above the balance sheet size.
                ceiling = max(ceiling, assets * 5.0)
            normalized_revenue = normalize_down(revenue, ceiling)
            if normalized_revenue != revenue:
                data["revenue_cr"] = normalized_revenue
                changed = True
                revenue = normalized_revenue

        if profit > 0 and revenue > 0:
            # Prevent OCR spikes where PAT is unrealistically larger than revenue.
            profit_ceiling = max(revenue * 1.2, 1000.0)
            normalized_profit = normalize_down(profit, profit_ceiling)
            if normalized_profit != profit:
                data["net_profit_cr"] = normalized_profit
                changed = True

        return changed

    def _default_data(self, note: str = "") -> Dict[str, Any]:
        return {
            "period": "Unknown",
            "revenue_cr": 0.0,
            "net_profit_cr": 0.0,
            "ebitda_cr": 0.0,
            "total_debt_cr": 0.0,
            "total_equity_cr": 0.0,
            "total_assets_cr": 0.0,
            "current_assets_cr": 0.0,
            "current_liabilities_cr": 0.0,
            "fixed_assets_cr": 0.0,
            "document_quality": {
                "status": "unknown",
                "summary": "Quality not assessed yet.",
                "should_exclude_from_scoring": False,
            },
            "note": note or "Not available",
        }