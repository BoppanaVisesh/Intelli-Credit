"""
Document Classifier
Automatically classifies uploaded documents by type using filename patterns and content analysis
"""

import os
import io
from typing import Tuple
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF


class DocumentClassifier:
    """
    Classifies documents into:
    - BANK_STATEMENT
    - GST_RETURN
    - ANNUAL_REPORT
    - ITR
    - BALANCE_SHEET
    - OTHER
    """
    
    # Filename pattern keywords
    PATTERNS = {
        'BANK_STATEMENT': ['bank', 'statement', 'account', 'transaction'],
        'GST_RETURN': ['gst', 'gstr', 'goods and services tax'],
        'ANNUAL_REPORT': ['annual', 'report', 'financial statement', 'audit', '-ar-', '_ar_', 'ar-20', 'ar_20'],
        'ITR': ['itr', 'income tax', 'tax return'],
        'BALANCE_SHEET': ['balance sheet', 'balance_sheet', 'b/s', 'financial position'],
        'ALM': ['alm', 'asset liability', 'maturity', 'gap analysis'],
        'SHAREHOLDING_PATTERN': ['shareholding', 'shareholder', 'promoter holding'],
        'BORROWING_PROFILE': ['borrowing', 'debt profile', 'loan schedule', 'consortium'],
        'PORTFOLIO_DATA': ['portfolio', 'npa', 'provision coverage', 'segment'],
    }
    
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            print(f"📄 DocumentClassifier initialized with Gemini API key")
    
    def classify(self, file_path: str, original_filename: str = None) -> Tuple[str, float]:
        """
        Classify document type
        
        Args:
            file_path: Path to the actual file (for content analysis)
            original_filename: Original filename (for pattern matching)
        
        Returns:
            (document_type, confidence)
        """
        
        # First, try filename-based classification
        # Use original filename if provided, otherwise use file_path
        filename = (original_filename or os.path.basename(file_path)).lower()
        
        for doc_type, keywords in self.PATTERNS.items():
            for keyword in keywords:
                if keyword in filename:
                    print(f"📄 Classified by filename: {doc_type} (confidence: 0.80)")
                    return doc_type, 0.80
        
        # If filename doesn't match, try content-based classification for PDFs
        is_pdf = file_path.lower().endswith('.pdf') or filename.lower().endswith('.pdf')
        if is_pdf and self.api_key:
            return self._classify_by_content(file_path)
        
        # Default to OTHER
        print(f"📄 Could not classify: {filename} -> OTHER")
        return "OTHER", 0.30
    
    def _classify_by_content(self, pdf_path: str) -> Tuple[str, float]:
        """Use Gemini Vision to classify by content"""
        
        try:
            # Convert first page to image using PyMuPDF
            doc = fitz.open(pdf_path)
            page = doc[0]  # First page only
            pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))  # 150 DPI
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            doc.close()
            
            prompt = """Look at this document and classify it into ONE category:
            
            - BANK_STATEMENT
            - GST_RETURN
            - ANNUAL_REPORT
            - ITR (Income Tax Return)
            - BALANCE_SHEET
            - OTHER
            
            Return ONLY the category name in uppercase."""
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt, img])
            
            doc_type = response.text.strip().upper()
            
            # Validate response
            valid_types = ['BANK_STATEMENT', 'GST_RETURN', 'ANNUAL_REPORT', 'ITR', 'BALANCE_SHEET', 'OTHER']
            
            if doc_type in valid_types:
                print(f"📄 Classified by content: {doc_type} (confidence: 0.90)")
                return doc_type, 0.90
            else:
                print(f"📄 Invalid classification result: {doc_type} -> OTHER")
                return "OTHER", 0.40
                
        except Exception as e:
            print(f"⚠️ Content classification failed: {str(e)}")
            return "OTHER", 0.30
