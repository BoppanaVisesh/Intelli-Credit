"""
Document Classifier
Automatically classifies uploaded documents by type using filename patterns and content analysis
"""

import os
from typing import Tuple
import google.generativeai as genai
from pdf2image import convert_from_path


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
        'ANNUAL_REPORT': ['annual', 'report', 'financial statement', 'audit'],
        'ITR': ['itr', 'income tax', 'tax return'],
        'BALANCE_SHEET': ['balance sheet', 'b/s', 'financial position']
    }
    
    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def classify(self, file_path: str) -> Tuple[str, float]:
        """
        Classify document type
        
        Returns:
            (document_type, confidence)
        """
        
        # First, try filename-based classification
        filename = os.path.basename(file_path).lower()
        
        for doc_type, keywords in self.PATTERNS.items():
            for keyword in keywords:
                if keyword in filename:
                    print(f"📄 Classified by filename: {doc_type} (confidence: 0.80)")
                    return doc_type, 0.80
        
        # If filename doesn't match, try content-based classification
        if file_path.endswith('.pdf') and self.api_key:
            return self._classify_by_content(file_path)
        
        # Default to OTHER
        print(f"📄 Could not classify: {filename} -> OTHER")
        return "OTHER", 0.30
    
    def _classify_by_content(self, pdf_path: str) -> Tuple[str, float]:
        """Use Gemini Vision to classify by content"""
        
        try:
            # Convert first page to image
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            
            prompt = """Look at this document and classify it into ONE category:
            
            - BANK_STATEMENT
            - GST_RETURN
            - ANNUAL_REPORT
            - ITR (Income Tax Return)
            - BALANCE_SHEET
            - OTHER
            
            Return ONLY the category name in uppercase."""
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, images[0]])
            
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
