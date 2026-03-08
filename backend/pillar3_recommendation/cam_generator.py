"""
CAM Generator - Generate Credit Appraisal Memo document
"""
from typing import Dict, Any
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import os


class CAMGenerator:
    """
    Generate Credit Appraisal Memo (CAM) document in Word/PDF format
    """
    
    def __init__(self, output_dir: str = './downloads/cam_reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_cam(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate CAM document
        Returns: file path
        """
        
        doc = Document()
        
        # Title
        title = doc.add_heading('CREDIT APPRAISAL MEMORANDUM', 0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Company Details Section
        self._add_company_section(doc, analysis_data)
        
        # Executive Summary
        self._add_executive_summary(doc, analysis_data)
        
        # Financial Analysis
        self._add_financial_analysis(doc, analysis_data)
        
        # Business & Industry Analysis
        self._add_business_analysis(doc, analysis_data)
        
        # Risk Assessment
        self._add_risk_assessment(doc, analysis_data)
        
        # Management & Promoter Assessment
        self._add_management_assessment(doc, analysis_data)
        
        # Credit Decision & Recommendation
        self._add_recommendation(doc, analysis_data)
        
        # Save document
        filename = f"{analysis_data['application_id']}.docx"
        filepath = os.path.join(self.output_dir, filename)
        doc.save(filepath)
        
        return filepath
    
    def _add_company_section(self, doc: Document, data: Dict):
        """Add company details section"""
        doc.add_heading('1. Company Details', 1)
        
        company = data['company_details']
        
        details = [
            ('Company Name', company['company_name']),
            ('CIN', company['mca_cin']),
            ('Sector', company['sector']),
            ('Requested Limit', f"₹{company['requested_limit_cr']} Crores"),
            ('Application ID', data['application_id']),
            ('Date', datetime.now().strftime('%d %B %Y'))
        ]
        
        for label, value in details:
            p = doc.add_paragraph()
            p.add_run(f"{label}: ").bold = True
            p.add_run(value)
    
    def _add_executive_summary(self, doc: Document, data: Dict):
        """Add executive summary"""
        doc.add_heading('2. Executive Summary', 1)
        
        doc.add_paragraph(data['cam_generation']['executive_summary'])
        
        # Decision box
        decision_para = doc.add_paragraph()
        decision_para.add_run('DECISION: ').bold = True
        decision_run = decision_para.add_run(data['risk_scoring_engine']['decision'])
        decision_run.bold = True
        
        if data['risk_scoring_engine']['decision'] == 'REJECT':
            decision_run.font.color.rgb = RGBColor(255, 0, 0)
        elif data['risk_scoring_engine']['decision'] == 'APPROVE':
            decision_run.font.color.rgb = RGBColor(0, 128, 0)
        
        # Key metrics
        doc.add_paragraph(
            f"Credit Score: {data['risk_scoring_engine']['final_credit_score']}/100"
        )
        doc.add_paragraph(
            f"Recommended Limit: ₹{data['risk_scoring_engine']['recommended_limit_cr']} Crores"
        )
    
    def _add_financial_analysis(self, doc: Document, data: Dict):
        """Add financial analysis section"""
        doc.add_heading('3. Financial Analysis', 1)
        
        fin = data['financial_analysis']
        
        doc.add_heading('3.1 Key Financial Ratios', 2)
        ratios = [
            ('DSCR', fin['calculated_ratios']['dscr']),
            ('Current Ratio', fin['calculated_ratios']['current_ratio']),
            ('Debt-to-Equity', fin['calculated_ratios']['debt_to_equity'])
        ]
        
        for label, value in ratios:
            doc.add_paragraph(f"{label}: {value}", style='List Bullet')
        
        doc.add_heading('3.2 Revenue Analysis', 2)
        doc.add_paragraph(
            f"GSTR-1 Sales: ₹{fin['raw_data_extracted']['gstr_1_sales_cr']} Cr"
        )
        doc.add_paragraph(
            f"Bank Inflows: ₹{fin['raw_data_extracted']['bank_statement_inflows_cr']} Cr"
        )
        doc.add_paragraph(
            f"Variance: {fin['reconciliation_flags']['gst_vs_bank_variance_percent']}%"
        )
    
    def _add_business_analysis(self, doc: Document, data: Dict):
        """Add business analysis"""
        doc.add_heading('4. Business & Industry Analysis', 1)
        
        doc.add_paragraph(data['ai_research_agent']['sector_headwinds'])
    
    def _add_risk_assessment(self, doc: Document, data: Dict):
        """Add risk assessment"""
        doc.add_heading('5. Risk Assessment', 1)
        
        doc.add_heading('5.1 Litigation Risk', 2)
        for lit in data['ai_research_agent']['litigation_and_nclt']:
            doc.add_paragraph(f"• {lit['summary']}", style='List Bullet')
        
        doc.add_heading('5.2 Circular Trading Analysis', 2)
        doc.add_paragraph(
            f"Risk Level: {data['financial_analysis']['reconciliation_flags']['circular_trading_risk']}"
        )
    
    def _add_management_assessment(self, doc: Document, data: Dict):
        """Add management assessment"""
        doc.add_heading('6. Management & Promoter Assessment', 1)
        
        for promoter in data['ai_research_agent']['promoter_checks']:
            doc.add_paragraph(f"{promoter['name']}: {promoter['finding']}")
    
    def _add_recommendation(self, doc: Document, data: Dict):
        """Add final recommendation"""
        doc.add_heading('7. Credit Committee Recommendation', 1)
        
        risk_engine = data['risk_scoring_engine']
        
        doc.add_paragraph(f"Based on comprehensive analysis, the credit score is {risk_engine['final_credit_score']}/100.")
        
        doc.add_paragraph()
        rec_para = doc.add_paragraph()
        rec_para.add_run('Recommendation: ').bold = True
        rec_para.add_run(
            f"{risk_engine['decision']} - ₹{risk_engine['recommended_limit_cr']} Crores"
        )
        
        # Add SHAP explanations
        doc.add_heading('7.1 Key Decision Factors', 2)
        for shap in risk_engine['shap_explanations']:
            impact_text = f"{'+' if shap['impact_value'] > 0 else ''}{shap['impact_value']}"
            doc.add_paragraph(
                f"{shap['feature']}: {impact_text} points",
                style='List Bullet'
            )
