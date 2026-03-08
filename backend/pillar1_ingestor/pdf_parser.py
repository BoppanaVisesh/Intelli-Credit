"""
PDF Parser - Extract text and tables from PDF documents
"""
import PyPDF2
import pdfplumber
from typing import Dict, List, Any


class PDFParser:
    """Generic PDF parser with text and table extraction"""
    
    def __init__(self):
        pass
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        return text
    
    def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """Extract tables from PDF using pdfplumber"""
        all_tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
        except Exception as e:
            print(f"Error extracting tables from PDF: {e}")
        return all_tables
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Parse PDF and return both text and tables"""
        return {
            'text': self.extract_text(pdf_path),
            'tables': self.extract_tables(pdf_path),
            'metadata': self._extract_metadata(pdf_path)
        }
    
    def _extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = {}
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    'pages': len(pdf_reader.pages),
                    'info': pdf_reader.metadata if pdf_reader.metadata else {}
                }
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        return metadata
