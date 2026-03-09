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
        Main parsing function using TEXT extraction + Gemini LLM.
        1. Extract text from ALL pages locally (free via PyMuPDF)
        2. Find and group key financial sections
        3. Send condensed text to Gemini for structured JSON extraction
        """
        
        if not os.path.exists(pdf_path):
            print(f"ERROR: PDF file not found: {pdf_path}")
            return self._get_default_data()
        
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set, returning default data")
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
                return self._get_default_data()
            
            # Step 3: Call Gemini with text prompt (NOT images)
            print(f"   Sending text to Gemini for structured extraction...")
            extracted_data = self._call_text_llm(condensed_text)
            
            return extracted_data
            
        except Exception as e:
            print(f"ERROR parsing annual report: {e}")
            return self._get_default_data()
    
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
        
        # Hard cap at 30K chars (~7.5K tokens) to be safe
        if len(condensed) > 30000:
            condensed = condensed[:30000] + "\n\n[TEXT TRUNCATED - key sections included above]"
        
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
