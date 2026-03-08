"""
ITR (Income Tax Return) Parser
Extracts structured data from ITR PDFs using Gemini Vision API
"""

import os
import json
from typing import Dict, Any
import google.generativeai as genai
from pdf2image import convert_from_path


class ITRParser:
    """Parse ITR documents using Gemini Vision"""
    
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse ITR PDF and extract structured data
        
        Returns:
            - pan: PAN number
            - assessment_year: e.g., "2023-24"
            - gross_total_income: Total income
            - total_tax_paid: Tax paid
            - refund_due: Refund amount if any
            - income_sources: List of income sources
        """
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not configured")
            return self._get_empty_structure()
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, first_page=1, last_page=3)
            
            # Prepare images for Gemini
            gemini_images = [img for img in images]
            
            # Prompt for structured extraction
            prompt = """Analyze this Income Tax Return (ITR) document and extract:
            
            Return ONLY valid JSON:
            {
                "pan": "PAN number",
                "assessment_year": "e.g. 2023-24",
                "gross_total_income": <amount in rupees>,
                "total_deductions": <amount in rupees>,
                "taxable_income": <amount in rupees>,
                "total_tax_paid": <amount in rupees>,
                "refund_due": <refund amount or 0>,
                "income_sources": [
                    {"type": "Salary/Business/Capital Gains", "amount": <amount>}
                ],
                "tds_deducted": <TDS amount>
            }
            
            Extract numbers WITHOUT commas or currency symbols. If field not found, use 0 or "N/A"."""
            
            # Call Gemini Vision
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt] + gemini_images)
            
            # Parse response
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response_text)
            
            print(f"✅ Parsed ITR: PAN={data.get('pan')}, Assessment Year={data.get('assessment_year')}")
            return data
            
        except Exception as e:
            print(f"❌ ITR parsing failed: {str(e)}")
            return self._get_empty_structure()
    
    def _get_empty_structure(self) -> Dict[str, Any]:
        """Return empty structure when parsing fails"""
        return {
            "pan": "N/A",
            "assessment_year": "N/A",
            "gross_total_income": 0.0,
            "total_deductions": 0.0,
            "taxable_income": 0.0,
            "total_tax_paid": 0.0,
            "refund_due": 0.0,
            "income_sources": [],
            "tds_deducted": 0.0,
            "note": "ITR parsing requires GEMINI_API_KEY"
        }
