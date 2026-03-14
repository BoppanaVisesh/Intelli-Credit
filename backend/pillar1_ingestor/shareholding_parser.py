"""
Shareholding Pattern Parser
Extracts promoter holding / pledged shares from shareholding PDFs using Gemini Vision.
"""

import io
import json
import os
from typing import Any, Dict

import fitz
import google.generativeai as genai
from PIL import Image


class ShareholdingPatternParser:
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        if not os.path.exists(pdf_path):
            return self._default_data(note="File not found")
        if not self.api_key:
            return self._default_data(note="GEMINI_API_KEY not configured")

        try:
            doc = fitz.open(pdf_path)
            images = []
            for page_num in range(min(len(doc), 3)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))
                images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
            doc.close()

            prompt = """Analyze this shareholding pattern / shareholder disclosure and return ONLY valid JSON.

{
  "filing_period": "e.g. Sep 2025 or FY 2025",
  "promoter_holding_pct": 0.0,
  "public_holding_pct": 0.0,
  "pledged_holding_pct": 0.0,
  "non_promoter_non_public_pct": 0.0,
  "governance_flags": ["flag 1", "flag 2"],
  "remarks": "short summary"
}

Rules:
- Extract percentages only, without percent symbol.
- pledged_holding_pct means promoter shares pledged / encumbered if disclosed, else 0.
- If a field is not visible, use 0 or empty string.
- Return JSON only.
"""

            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt] + images)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())

            default = self._default_data()
            default.update(data)
            return default
        except Exception as e:
            return self._default_data(note=f"Shareholding parsing failed: {e}")

    def _default_data(self, note: str = "") -> Dict[str, Any]:
        return {
            "filing_period": "Unknown",
            "promoter_holding_pct": 0.0,
            "public_holding_pct": 0.0,
            "pledged_holding_pct": 0.0,
            "non_promoter_non_public_pct": 0.0,
            "governance_flags": [],
            "remarks": note or "Not available",
        }