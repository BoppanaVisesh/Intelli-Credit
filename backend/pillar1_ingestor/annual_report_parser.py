"""
Annual Report Parser - Extract key information from annual reports using TEXT extraction + Gemini LLM
Uses PyMuPDF text extraction (free, local) instead of Vision API (expensive image tokens)
"""
from typing import Dict, Any, Optional, List, Tuple
import os
import json
import re
from pathlib import Path
import google.generativeai as genai
import fitz  # PyMuPDF


class AnnualReportParser:
    """
    Parse annual reports using TEXT extraction + Gemini LLM.
    Extracts text locally from PDF (free), finds key financial sections,
    then sends only relevant text to Gemini for structured JSON extraction.
    This uses ~5-10K tokens instead of millions (from images).
    """
    
    # Section keywords for categorizing extracted text
    SECTION_KEYWORDS = {
        'balance_sheet': [
            'balance sheet', 'statement of financial position',
            'total equity', 'shareholders funds', "shareholders' funds",
            'net worth', 'total borrowings', 'non-current liabilities',
            'current liabilities', 'total assets', 'non-current assets',
        ],
        'profit_loss': [
            'statement of profit', 'profit and loss', 'income statement',
            'revenue from operations', 'other income', 'total expenses',
            'profit before tax', 'profit after tax', 'earnings per share',
            'ebitda', 'operating profit',
        ],
        'auditor': [
            'independent auditor', 'audit report', 'auditors report',
            "auditor's report", 'qualified opinion', 'unqualified',
            'basis for opinion', 'key audit matters',
        ],
        'litigations': [
            'contingent liabilities', 'pending litigations', 'legal proceedings',
            'claims against', 'disputed', 'arbitration',
        ],
        'management': [
            'management discussion', 'md&a', "director's report",
            'directors report', 'business overview', 'outlook',
            'expansion', 'future plans', 'risk management',
            'key risks', 'forward-looking',
        ],
        'related_party': [
            'related party', 'transactions with related',
        ],
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def parse_annual_report(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main parsing function.
        - JSON files: load directly as pre-parsed structured data
        - PDF files: TEXT extraction + Gemini LLM
        """
        
        if not os.path.exists(pdf_path):
            print(f"ERROR: File not found: {pdf_path}")
            return self._get_default_data()
        
        # Handle JSON files (pre-parsed structured data)
        if pdf_path.lower().endswith('.json'):
            return self._parse_json_report(pdf_path)
        
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set, returning default data")
            try:
                doc = fitz.open(pdf_path)
                all_pages_text = self._extract_all_text(doc)
                doc.close()
                condensed_text = self._build_condensed_text(all_pages_text)
                return self._local_text_fallback(condensed_text, pdf_path)
            except Exception:
                return self._get_default_data()
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            print(f"   PDF has {total_pages} pages")
            
            # Step 1: Extract text from all pages (free, local)
            all_pages_text = self._extract_all_text(doc)
            doc.close()
            
            # Step 2: Find key sections and build condensed text
            condensed_text = self._build_condensed_text(all_pages_text)
            text_len = len(condensed_text)
            print(f"   Condensed text: {text_len} chars (~{text_len // 4} tokens)")
            
            if text_len < 100:
                print("ERROR: Very little text extracted from PDF (scanned/image PDF?)")
                return self._local_text_fallback(condensed_text, pdf_path)
            
            # Step 3: Call Gemini with text prompt (NOT images)
            print(f"   Sending text to Gemini for structured extraction...")
            extracted_data = self._call_text_llm(condensed_text)
            if extracted_data.get("company_name") == "Unknown Company":
                fallback_data = self._local_text_fallback(condensed_text, pdf_path)
                # Keep LLM output as primary, but fill obvious unknowns from local fallback.
                for k, v in fallback_data.items():
                    if k not in extracted_data:
                        extracted_data[k] = v
                    elif extracted_data[k] in (None, "", 0, 0.0, "Unknown Company", "Unknown Auditor", "Not Available"):
                        extracted_data[k] = v

            if (
                extracted_data.get("key_risks") == ["Document parsing failed"]
                and (
                    extracted_data.get("company_name") not in (None, "", "Unknown Company")
                    or float(extracted_data.get("revenue_cr") or 0.0) > 0
                    or float(extracted_data.get("net_profit_cr") or 0.0) != 0
                    or float(extracted_data.get("total_debt_cr") or 0.0) > 0
                    or float(extracted_data.get("total_equity_cr") or 0.0) > 0
                )
            ):
                extracted_data["key_risks"] = ["LLM parsing unavailable; populated via local text fallback"]
            return extracted_data
            
        except Exception as e:
            print(f"ERROR parsing annual report: {e}")
            try:
                return self._local_text_fallback(condensed_text if 'condensed_text' in locals() else "", pdf_path)
            except Exception:
                return self._get_default_data()

    def _local_text_fallback(self, condensed_text: str, pdf_path: str) -> Dict[str, Any]:
        """Deterministic fallback when LLM is unavailable (quota/key/runtime)."""
        data = self._get_default_data()
        text = condensed_text or ""
        text_lower = text.lower()

        # Company name: robust matching for uppercase and title-case report styles.
        company_match = re.search(
            r"\b([A-Za-z][A-Za-z&.,'\- ]{3,90}(?:LIMITED|LTD|LLP|PRIVATE LIMITED))\b",
            text,
            re.IGNORECASE,
        )
        if not company_match:
            company_match = re.search(
                r"(?:for\s+the\s+year\s+ended[\s\S]{0,80})\b([A-Za-z][A-Za-z&.,'\- ]{3,90}(?:Limited|Ltd|LLP|Private Limited))\b",
                text,
                re.IGNORECASE,
            )
        if company_match:
            data["company_name"] = re.sub(r"\s+", " ", company_match.group(1)).strip().title()
        else:
            stem = Path(pdf_path).stem.replace("_", " ").strip()
            if stem and not re.fullmatch(r"[0-9a-fA-F\-]{20,}", stem):
                data["company_name"] = stem[:80]

        # Financial year extraction.
        fy_match = re.search(r"FY\s*([0-9]{2,4})\s*[-/]\s*([0-9]{2,4})", text, re.IGNORECASE)
        if fy_match:
            y1, y2 = fy_match.group(1), fy_match.group(2)
            if len(y1) == 2:
                y1 = "20" + y1
            if len(y2) == 2:
                y2 = "20" + y2
            data["financial_year"] = f"{y1}-{y2[-2:]}"
        else:
            year_match = re.search(r"(20[0-9]{2})", text)
            if year_match:
                y = int(year_match.group(1))
                data["financial_year"] = f"{y}-{str(y + 1)[-2:]}"

        # Auditor name and opinion.
        auditor_match = re.search(r"(?:M/s\.?\s*)?([A-Z][A-Za-z&.,'\- ]{2,70}(?:LLP|&\s*Co\.?|Associates|Chartered Accountants))", text)
        if auditor_match:
            data["auditor_name"] = auditor_match.group(1).strip()

        if "qualified opinion" in text_lower:
            data["auditor_opinion"] = "Qualified"
        elif "adverse opinion" in text_lower:
            data["auditor_opinion"] = "Adverse"
        elif "disclaimer of opinion" in text_lower:
            data["auditor_opinion"] = "Disclaimer"
        elif "unmodified opinion" in text_lower or "true and fair" in text_lower:
            data["auditor_opinion"] = "Unqualified"

        # Basic numeric extraction (expects values already reported in crores in many summaries).
        def capture_amount(patterns):
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if not m:
                    continue
                raw = m.group(1).replace(",", "")
                try:
                    v = float(raw)
                    return v
                except Exception:
                    continue
            return 0.0

        data["revenue_cr"] = capture_amount([
            r"revenue(?:\s+from\s+operations)?[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
            r"total\s+income[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
        ])
        data["net_profit_cr"] = capture_amount([
            r"profit\s+after\s+tax[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
            r"net\s+profit[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
        ])
        data["total_equity_cr"] = capture_amount([
            r"total\s+equity[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
            r"shareholders'?\s+funds[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
            r"net\s+worth[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
        ])
        data["total_debt_cr"] = capture_amount([
            r"total\s+borrowings[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
            r"borrowings[^0-9\-]{0,30}([0-9]+(?:\.[0-9]+)?)",
        ])

        # Quick risk hints.
        risks = []
        if "contingent liabilities" in text_lower:
            risks.append("Contingent liabilities disclosed")
        if "litigation" in text_lower or "legal proceedings" in text_lower:
            risks.append("Legal/litigation references found")
        if risks:
            data["key_risks"] = risks[:3]

        meaningful = any([
            data.get("company_name") not in ("", "Unknown Company"),
            data.get("auditor_name") not in ("", "Unknown Auditor"),
            data.get("revenue_cr", 0.0) > 0,
            data.get("net_profit_cr", 0.0) != 0,
            data.get("total_debt_cr", 0.0) > 0,
            data.get("total_equity_cr", 0.0) > 0,
        ])
        if meaningful and data.get("key_risks") == ["Document parsing failed"]:
            data["key_risks"] = ["LLM parsing unavailable; populated via local text fallback"]

        return data
    
    def _extract_all_text(self, doc) -> List[Tuple[int, str]]:
        """Extract text from every page. Returns list of (page_num, text)."""
        pages = []
        for page_num in range(len(doc)):
            try:
                text = doc[page_num].get_text()
                if text.strip():
                    pages.append((page_num, text))
            except Exception:
                continue
        print(f"   Extracted text from {len(pages)}/{len(doc)} pages")
        return pages
    
    def _build_condensed_text(self, all_pages: List[Tuple[int, str]]) -> str:
        """
        Build a condensed text from key financial sections.
        Categorizes pages by section type and selects the most relevant ones.
        Target: ~15K chars (~4K tokens) to stay well within limits.
        """
        # Categorize pages by section
        section_pages: Dict[str, List[Tuple[int, str]]] = {k: [] for k in self.SECTION_KEYWORDS}
        cover_pages: List[Tuple[int, str]] = []
        
        for page_num, text in all_pages:
            text_lower = text.lower()
            
            # First 3 pages are cover/highlights
            if page_num < 3:
                cover_pages.append((page_num, text))
                continue
            
            # Categorize by keywords
            for section, keywords in self.SECTION_KEYWORDS.items():
                if any(kw in text_lower for kw in keywords):
                    section_pages[section].append((page_num, text))
        
        # Build condensed text with section headers
        parts = []
        
        # Cover pages (first 2 only, truncated)
        if cover_pages:
            parts.append("=== COVER / HIGHLIGHTS ===")
            for pn, txt in cover_pages[:2]:
                parts.append(f"[Page {pn+1}]\n{txt[:2000]}")
        
        # Balance Sheet (most important - take best 3 pages)
        if section_pages['balance_sheet']:
            parts.append("\n=== BALANCE SHEET / FINANCIAL POSITION ===")
            for pn, txt in section_pages['balance_sheet'][:3]:
                parts.append(f"[Page {pn+1}]\n{txt[:3000]}")
        
        # Profit & Loss (take best 3 pages)
        if section_pages['profit_loss']:
            parts.append("\n=== STATEMENT OF PROFIT AND LOSS ===")
            for pn, txt in section_pages['profit_loss'][:3]:
                parts.append(f"[Page {pn+1}]\n{txt[:3000]}")
        
        # Auditor Report (take best 2 pages)
        if section_pages['auditor']:
            parts.append("\n=== AUDITOR'S REPORT ===")
            for pn, txt in section_pages['auditor'][:2]:
                parts.append(f"[Page {pn+1}]\n{txt[:2000]}")
        
        # Litigations / Contingent Liabilities (take best 2 pages)
        if section_pages['litigations']:
            parts.append("\n=== CONTINGENT LIABILITIES / LITIGATIONS ===")
            for pn, txt in section_pages['litigations'][:2]:
                parts.append(f"[Page {pn+1}]\n{txt[:2000]}")
        
        # Management Discussion (take best 2 pages)
        if section_pages['management']:
            parts.append("\n=== MANAGEMENT DISCUSSION & ANALYSIS ===")
            for pn, txt in section_pages['management'][:2]:
                parts.append(f"[Page {pn+1}]\n{txt[:2000]}")
        
        # Related Party (take 1 page)
        if section_pages['related_party']:
            parts.append("\n=== RELATED PARTY TRANSACTIONS ===")
            for pn, txt in section_pages['related_party'][:1]:
                parts.append(f"[Page {pn+1}]\n{txt[:1500]}")
        
        condensed = "\n".join(parts)
        
        # Hard cap at 50K chars (~12.5K tokens) to capture more financial sections
        if len(condensed) > 50000:
            print(f"   ⚠ Condensed text truncated from {len(condensed)} to 50000 chars — late sections may be missed")
            condensed = condensed[:50000] + "\n\n[TEXT TRUNCATED - key sections included above]"
        
        return condensed
    
    def _call_text_llm(self, condensed_text: str) -> Dict[str, Any]:
        """
        Call Gemini with extracted TEXT (not images) for structured data extraction.
        Uses ~5-10K tokens instead of millions from images.
        """
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""You are a financial analyst. Extract structured data from this annual report text.

The text below contains key sections (Balance Sheet, P&L, Auditor Report, etc.) extracted from a PDF annual report.

ANNUAL REPORT TEXT:
{condensed_text}

Extract the following data and return ONLY valid JSON:
{{
    "company_name": "Company name from the report",
    "financial_year": "FY 2023-24",
    "auditor_name": "Name of the auditing firm",
    "auditor_opinion": "Unqualified/Qualified/Adverse/Disclaimer",
    "total_debt_cr": 0.0,
    "total_equity_cr": 0.0,
    "revenue_cr": 0.0,
    "net_profit_cr": 0.0,
    "ebitda_cr": 0.0,
    "total_assets_cr": 0.0,
    "current_assets_cr": 0.0,
    "current_liabilities_cr": 0.0,
    "pending_litigations": [
        {{"description": "Brief description", "amount_cr": 0.0, "status": "Pending/Resolved"}}
    ],
    "contingent_liabilities_cr": 0.0,
    "related_party_transactions_cr": 0.0,
    "management_commentary": "Key points from MD&A section",
    "key_risks": ["Risk 1", "Risk 2", "Risk 3"],
    "expansion_plans": "Future plans mentioned"
}}

RULES:
- All monetary amounts MUST be in Indian CRORES (Rs. Crore). Convert lakhs to crores (divide by 100). Convert millions to crores appropriately.
- total_debt_cr = Total Borrowings (long-term + short-term) from Balance Sheet
- total_equity_cr = Total Equity / Shareholders' Funds from Balance Sheet
- revenue_cr = Revenue from Operations
- net_profit_cr = Profit/(Loss) for the period (can be negative)
- ebitda_cr = Operating profit before interest, tax, depreciation
- If a value is not found, use 0.0 but try hard to find it
- Return ONLY valid JSON, no markdown, no explanation"""

            config = genai.GenerationConfig(
                max_output_tokens=8000,
                temperature=0.1,
                response_mime_type="application/json"
            )
            
            response = model.generate_content(
                prompt,
                generation_config=config
            )
            
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            print("   Successfully extracted data from annual report")
            return data
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON from Gemini response: {e}")
            try:
                print(f"Raw response: {text[:500]}")
            except Exception:
                pass
            return self._get_default_data()
            
        except Exception as e:
            print(f"ERROR calling Gemini API: {e}")
            return self._get_default_data()
    
    def _parse_json_report(self, json_path: str) -> Dict[str, Any]:
        """Load pre-parsed annual report data from a JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   ✓ Loaded annual report JSON: {json_path}")
            # Merge with defaults so all expected keys exist
            defaults = self._get_default_data()
            defaults.update(data)
            return defaults
        except Exception as e:
            print(f"ERROR loading JSON annual report: {e}")
            return self._get_default_data()

    def _get_default_data(self) -> Dict[str, Any]:
        """Return default structure when parsing fails"""
        return {
            'company_name': 'Unknown Company',
            'financial_year': '2025-26',
            'auditor_name': 'Unknown Auditor',
            'auditor_opinion': 'Not Available',
            'total_debt_cr': 0.0,
            'total_equity_cr': 0.0,
            'revenue_cr': 0.0,
            'net_profit_cr': 0.0,
            'pending_litigations': [],
            'contingent_liabilities_cr': 0.0,
            'related_party_transactions_cr': 0.0,
            'management_commentary': 'Not available',
            'key_risks': ['Document parsing failed'],
            'expansion_plans': 'Not available'
        }
