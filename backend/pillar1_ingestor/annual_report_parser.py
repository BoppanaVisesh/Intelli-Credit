"""
Annual Report Parser - Extract key information from annual reports using Gemini Vision LLM
"""
from typing import Dict, Any, Optional, List
import os
import json
from pathlib import Path
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image


class AnnualReportParser:
    """
    Parse annual reports using Gemini Vision LLM
    Extract: Auditor, Debt, Litigations, Management Commentary, etc.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def parse_annual_report(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main parsing function using Gemini Vision LLM
        1. Convert PDF pages to images
        2. Send to Gemini Vision with structured prompt
        3. Parse JSON response
        """
        
        if not os.path.exists(pdf_path):
            print(f"ERROR: PDF file not found: {pdf_path}")
            return self._get_default_data()
        
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set, returning default data")
            return self._get_default_data()
        
        try:
            # Step 1: Convert PDF to images (only first 15 pages for efficiency)
            print(f"Converting PDF to images: {pdf_path}")
            image_paths = self.pdf_to_images(pdf_path, max_pages=15)
            
            if not image_paths:
                print("ERROR: No images extracted from PDF")
                return self._get_default_data()
            
            # Step 2: Call Vision LLM
            print(f"Analyzing {len(image_paths)} pages with Gemini Vision...")
            extracted_data = self._call_vision_llm(image_paths)
            
            # Step 3: Cleanup temp images
            self._cleanup_temp_images(image_paths)
            
            return extracted_data
            
        except Exception as e:
            print(f"ERROR parsing annual report: {e}")
            return self._get_default_data()
    
    def pdf_to_images(self, pdf_path: str, max_pages: int = 15) -> List[str]:
        """
        Convert PDF pages to images
        Only convert first max_pages to save time and cost
        """
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
            image_paths = []
            
            for i, img in enumerate(images):
                temp_path = f"temp_page_{i}.png"
                img.save(temp_path, "PNG")
                image_paths.append(temp_path)
            
            print(f"   ✓ Converted {len(image_paths)} pages to images")
            return image_paths
            
        except Exception as e:
            print(f"ERROR converting PDF to images: {e}")
            print("   Hint: Install Poppler - https://github.com/oschwartz10612/poppler-windows/releases/")
            return []
    
    def _call_vision_llm(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Call Gemini Vision API to extract structured data
        """
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = """
Analyze this annual report and extract information in JSON format.

REQUIRED JSON FORMAT (respond with ONLY JSON, no markdown):
{
    "company_name": "Extract company name from cover page",
    "financial_year": "FY 2023-24",
    "auditor_name": "Name of auditing firm",
    "auditor_opinion": "Unqualified/Qualified/Adverse/Disclaimer",
    "total_debt_cr": 0.0,
    "total_equity_cr": 0.0,
    "revenue_cr": 0.0,
    "net_profit_cr": 0.0,
    "pending_litigations": [
        {"description": "Brief description", "amount_cr": 0.0, "status": "Pending/Resolved"}
    ],
    "contingent_liabilities_cr": 0.0,
    "related_party_transactions_cr": 0.0,
    "management_commentary": "Key points from MD&A",
    "key_risks": ["Risk 1", "Risk 2"],
    "expansion_plans": "Future plans mentioned"
}

EXTRACTION RULES:
- All amounts in CRORES (divide lakhs by 100)
- Look for: Balance Sheet, P&L, Notes to Accounts, Auditor Report
- Pending litigations: Check "Contingent Liabilities" note
- Key risks: Extract from "Risk Management" or "Forward Looking Statements"
- Return ONLY valid JSON, no explanations
"""
            
            # Load images
            images = [Image.open(path) for path in image_paths]
            
            # Generate content
            response = model.generate_content([prompt] + images)
            
            # Parse JSON from response
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
            print("   ✓ Successfully extracted data from annual report")
            return data
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON from Gemini response: {e}")
            print(f"Raw response: {text[:500]}")
            return self._get_default_data()
            
        except Exception as e:
            print(f"ERROR calling Gemini Vision API: {e}")
            return self._get_default_data()
    
    def _cleanup_temp_images(self, image_paths: List[str]):
        """Remove temporary image files"""
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Warning: Could not delete temp file {path}: {e}")
    
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
