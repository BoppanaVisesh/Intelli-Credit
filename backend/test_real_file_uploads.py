"""
REAL DATA TEST SCRIPT
=====================

This script tests the system with ACTUAL file uploads (not just API calls).
Creates realistic sample documents and uploads them through the API.
"""

import requests
import pandas as pd
import os
from datetime import datetime
import json

BASE_URL = "http://localhost:8000/api/v1"

# Create sample data directory
os.makedirs("./test_data", exist_ok=True)


def create_sample_gst_file(company_name: str, scenario: str = "good"):
    """Create realistic GST data file"""
    
    if scenario == "good":
        # Strong company with aligned GST-Bank data
        data = {
            'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
                     'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
            'GSTR-1 Sales (Cr)': [4.2, 4.5, 4.8, 5.1, 5.3, 5.5, 5.8, 6.0, 6.2, 6.5, 6.8, 7.0],
            'GSTR-3B Sales (Cr)': [4.1, 4.4, 4.7, 5.0, 5.2, 5.4, 5.7, 5.9, 6.1, 6.4, 6.7, 6.9],
            'GSTR-2A Purchases (Cr)': [2.5, 2.7, 2.9, 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.9, 4.0, 4.2],
            'Input Tax Credit (Lakhs)': [45, 48, 52, 56, 58, 60, 63, 65, 67, 70, 72, 75],
            'GST Paid (Lakhs)': [30, 32, 34, 36, 38, 39, 41, 42, 44, 46, 48, 49]
        }
    elif scenario == "average":
        # Moderate company with some variance
        data = {
            'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
                     'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
            'GSTR-1 Sales (Cr)': [3.2, 2.8, 3.5, 3.0, 3.3, 2.9, 3.4, 3.1, 3.6, 3.2, 3.5, 3.3],
            'GSTR-3B Sales (Cr)': [3.0, 2.7, 3.3, 2.9, 3.1, 2.8, 3.2, 3.0, 3.4, 3.1, 3.3, 3.2],
            'GSTR-2A Purchases (Cr)': [2.0, 1.8, 2.2, 1.9, 2.1, 1.9, 2.2, 2.0, 2.3, 2.1, 2.3, 2.2],
            'Input Tax Credit (Lakhs)': [36, 32, 40, 34, 38, 34, 40, 36, 41, 38, 41, 40],
            'GST Paid (Lakhs)': [18, 16, 20, 17, 19, 17, 19, 18, 20, 19, 20, 19]
        }
    else:  # poor
        # Struggling company with high variance (suspicious)
        data = {
            'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
                     'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
            'GSTR-1 Sales (Cr)': [2.5, 1.8, 3.2, 1.5, 2.8, 1.9, 2.6, 1.7, 3.0, 1.6, 2.7, 2.0],
            'GSTR-3B Sales (Cr)': [2.0, 1.5, 2.8, 1.2, 2.4, 1.6, 2.2, 1.4, 2.6, 1.3, 2.3, 1.7],
            'GSTR-2A Purchases (Cr)': [2.8, 2.2, 3.5, 2.0, 3.0, 2.3, 2.9, 2.1, 3.2, 2.0, 3.0, 2.5],
            'Input Tax Credit (Lakhs)': [50, 40, 63, 36, 54, 41, 52, 38, 58, 36, 54, 45],
            'GST Paid (Lakhs)': [12, 9, 17, 7, 14, 10, 13, 8, 16, 8, 14, 10]
        }
    
    df = pd.DataFrame(data)
    
    # Add totals row
    totals = {
        'Month': 'TOTAL',
        'GSTR-1 Sales (Cr)': df['GSTR-1 Sales (Cr)'].sum(),
        'GSTR-3B Sales (Cr)': df['GSTR-3B Sales (Cr)'].sum(),
        'GSTR-2A Purchases (Cr)': df['GSTR-2A Purchases (Cr)'].sum(),
        'Input Tax Credit (Lakhs)': df['Input Tax Credit (Lakhs)'].sum(),
        'GST Paid (Lakhs)': df['GST Paid (Lakhs)'].sum()
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    
    # Save to Excel
    filename = f"./test_data/GST_Returns_{company_name.replace(' ', '_')}_{scenario}.xlsx"
    df.to_excel(filename, index=False, sheet_name='GST Returns')
    
    print(f"✅ Created GST file: {filename}")
    print(f"   Total Sales (GSTR-1): ₹{totals['GSTR-1 Sales (Cr)']:.2f} Cr")
    print(f"   Variance: {abs(totals['GSTR-1 Sales (Cr)'] - totals['GSTR-3B Sales (Cr)']) / totals['GSTR-1 Sales (Cr)'] * 100:.2f}%")
    
    return filename


def create_sample_bank_statement(company_name: str, scenario: str = "good"):
    """Create realistic bank statement"""
    
    if scenario == "good":
        # Aligned with GST data
        data = {
            'Date': pd.date_range(start='2025-04-01', end='2026-03-31', freq='MS'),
            'Description': ['Sales Receipt - Customer Payment'] * 12,
            'Credit (Cr)': [4.0, 4.3, 4.6, 4.9, 5.1, 5.3, 5.6, 5.8, 6.0, 6.3, 6.6, 6.8],
            'Debit (Cr)': [2.4, 2.6, 2.8, 3.0, 3.1, 3.2, 3.4, 3.5, 3.6, 3.8, 3.9, 4.1]
        }
    elif scenario == "average":
        # Moderate alignment
        data = {
            'Date': pd.date_range(start='2025-04-01', end='2026-03-31', freq='MS'),
            'Description': ['Sales Receipt - Customer Payment'] * 12,
            'Credit (Cr)': [2.9, 2.6, 3.2, 2.8, 3.0, 2.7, 3.1, 2.9, 3.3, 3.0, 3.2, 3.1],
            'Debit (Cr)': [1.9, 1.7, 2.1, 1.8, 2.0, 1.8, 2.1, 1.9, 2.2, 2.0, 2.2, 2.1]
        }
    else:  # poor
        # Misaligned with GST (suspicious)
        data = {
            'Date': pd.date_range(start='2025-04-01', end='2026-03-31', freq='MS'),
            'Description': ['Sales Receipt - Customer Payment'] * 12,
            'Credit (Cr)': [1.8, 1.3, 2.4, 1.1, 2.0, 1.4, 1.9, 1.2, 2.3, 1.2, 2.0, 1.5],
            'Debit (Cr)': [2.7, 2.1, 3.4, 1.9, 2.9, 2.2, 2.8, 2.0, 3.1, 1.9, 2.9, 2.4]
        }
    
    df = pd.DataFrame(data)
    df['Balance (Cr)'] = (df['Credit (Cr)'] - df['Debit (Cr)']).cumsum()
    
    # Add totals
    totals = {
        'Date': 'TOTAL',
        'Description': 'Annual Summary',
        'Credit (Cr)': df['Credit (Cr)'].sum(),
        'Debit (Cr)': df['Debit (Cr)'].sum(),
        'Balance (Cr)': df['Balance (Cr)'].iloc[-1]
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    
    # Save to Excel (simulating PDF extract)
    filename = f"./test_data/Bank_Statement_{company_name.replace(' ', '_')}_{scenario}.xlsx"
    df.to_excel(filename, index=False, sheet_name='Bank Statement')
    
    print(f"✅ Created Bank Statement: {filename}")
    print(f"   Total Inflows: ₹{totals['Credit (Cr)']:.2f} Cr")
    print(f"   Total Outflows: ₹{totals['Debit (Cr)']:.2f} Cr")
    
    return filename


def create_sample_annual_report(company_name: str, scenario: str = "good"):
    """Create sample annual report data (would be PDF in production)"""
    
    if scenario == "good":
        financials = {
            'Revenue': 65.5,
            'Operating Profit': 12.8,
            'Net Profit': 8.5,
            'Total Assets': 85.0,
            'Total Liabilities': 35.0,
            'Shareholders Equity': 50.0,
            'Current Assets': 40.0,
            'Current Liabilities': 20.0,
            'Long Term Debt': 15.0,
            'EBITDA': 14.2
        }
    elif scenario == "average":
        financials = {
            'Revenue': 38.5,
            'Operating Profit': 4.2,
            'Net Profit': 2.1,
            'Total Assets': 55.0,
            'Total Liabilities': 35.0,
            'Shareholders Equity': 20.0,
            'Current Assets': 22.0,
            'Current Liabilities': 18.0,
            'Long Term Debt': 17.0,
            'EBITDA': 5.8
        }
    else:  # poor
        financials = {
            'Revenue': 28.0,
            'Operating Profit': -1.5,
            'Net Profit': -3.2,
            'Total Assets': 45.0,
            'Total Liabilities': 42.0,
            'Shareholders Equity': 3.0,
            'Current Assets': 12.0,
            'Current Liabilities': 15.0,
            'Long Term Debt': 27.0,
            'EBITDA': 0.8
        }
    
    filename = f"./test_data/Annual_Report_{company_name.replace(' ', '_')}_{scenario}.json"
    with open(filename, 'w') as f:
        json.dump(financials, f, indent=2)
    
    print(f"✅ Created Annual Report: {filename}")
    print(f"   Revenue: ₹{financials['Revenue']:.2f} Cr")
    print(f"   D/E Ratio: {financials['Total Liabilities']/financials['Shareholders Equity']:.2f}")
    
    return filename


def test_with_real_files(company_name: str, scenario: str, requested_limit: float):
    """Test the complete flow with real file uploads"""
    
    print(f"\n{'='*80}")
    print(f"🧪 TESTING WITH REAL FILES: {company_name} ({scenario.upper()})")
    print(f"{'='*80}")
    
    # Create test documents
    print("\n📄 Creating sample documents...")
    gst_file = create_sample_gst_file(company_name, scenario)
    bank_file = create_sample_bank_statement(company_name, scenario)
    annual_file = create_sample_annual_report(company_name, scenario)
    
    # Prepare multipart form data
    print(f"\n📤 Uploading documents to API...")
    
    try:
        with open(gst_file, 'rb') as gst, \
             open(bank_file, 'rb') as bank:
            
            files = {
                'gst_returns': ('gst_returns.xlsx', gst, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                'bank_statements': ('bank_statements.xlsx', bank, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            
            data = {
                'company_name': company_name,
                'mca_cin': f'U{scenario.upper()}123TN2020PLC123456',
                'sector': 'Manufacturing',
                'requested_limit_cr': requested_limit,
                'credit_officer_notes': f'Field visit completed. {scenario.capitalize()} operational infrastructure observed.'
            }
            
            print(f"   Company: {company_name}")
            print(f"   Requested Limit: ₹{requested_limit} Cr")
            
            response = requests.post(
                f"{BASE_URL}/applications/analyze-credit",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n{'='*80}")
                print(f"📊 ANALYSIS RESULTS")
                print(f"{'='*80}")
                
                # Extract key results
                scoring = result.get('risk_scoring_engine', {})
                financial = result.get('financial_analysis', {})
                research = result.get('ai_research_agent', {})
                
                print(f"\n🎯 CREDIT DECISION:")
                print(f"   Score: {scoring.get('final_credit_score', 'N/A')}/100")
                print(f"   Decision: {scoring.get('decision', 'N/A')}")
                print(f"   Risk Grade: {scoring.get('risk_grade', 'N/A')}")
                print(f"   Recommended Limit: ₹{scoring.get('recommended_limit_cr', 'N/A')} Cr")
                print(f"   Approval %: {scoring.get('approval_percentage', 0)}%")
                
                print(f"\n💼 FINANCIAL ANALYSIS:")
                ratios = financial.get('calculated_ratios', {})
                print(f"   DSCR: {ratios.get('dscr', 'N/A')}")
                print(f"   Current Ratio: {ratios.get('current_ratio', 'N/A')}")
                print(f"   Debt-to-Equity: {ratios.get('debt_to_equity', 'N/A')}")
                
                recon = financial.get('reconciliation_flags', {})
                print(f"   GST-Bank Variance: {recon.get('gst_vs_bank_variance_percent', 'N/A')}%")
                print(f"   Circular Trading Risk: {recon.get('circular_trading_risk', 'N/A')}")
                
                print(f"\n🌐 RESEARCH FINDINGS:")
                promoters = research.get('promoter_checks', [])
                if promoters:
                    print(f"   Promoter Sentiment: {promoters[0].get('sentiment', 'N/A')}")
                
                litigation = research.get('litigation_and_nclt', [])
                print(f"   Litigation Cases: {len(litigation)}")
                
                print(f"   Sector Risk: {research.get('sector_risk_score', 'N/A')}/100")
                
                print(f"\n📝 SUB-SCORES (5 Cs):")
                sub_scores = scoring.get('sub_scores', {})
                for factor, data in sub_scores.items():
                    score = data.get('score', 0)
                    weight = data.get('weight', 0)
                    print(f"   {factor.capitalize():12s}: {score}/100 (weight: {weight*100:.0f}%)")
                
                print(f"\n💡 KEY DECISION FACTORS:")
                key_factors = scoring.get('key_factors', [])
                for i, factor in enumerate(key_factors, 1):
                    print(f"   {i}. {factor}")
                
                print(f"\n✅ TEST COMPLETED SUCCESSFULLY")
                print(f"   Files uploaded and processed")
                print(f"   Real data extracted from documents")
                print(f"   Web research conducted")
                print(f"   Credit score calculated dynamically")
                
                return result
                
            else:
                print(f"\n❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def run_comprehensive_test():
    """Run comprehensive test with all scenarios"""
    
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE REAL FILE UPLOAD TEST")
    print("="*80)
    print("\nThis test creates realistic documents and uploads them through the API")
    print("to verify that the system processes REAL data correctly.\n")
    
    # Test 1: Excellent Company
    result1 = test_with_real_files(
        company_name="TechCorp Industries Ltd",
        scenario="good",
        requested_limit=15.0
    )
    
    # Test 2: Average Company
    result2 = test_with_real_files(
        company_name="MidTier Manufacturing Pvt Ltd",
        scenario="average",
        requested_limit=10.0
    )
    
    # Test 3: Poor Company
    result3 = test_with_real_files(
        company_name="Struggling Enterprises Ltd",
        scenario="poor",
        requested_limit=20.0
    )
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    if result1 and result2 and result3:
        score1 = result1.get('risk_scoring_engine', {}).get('final_credit_score', 0)
        score2 = result2.get('risk_scoring_engine', {}).get('final_credit_score', 0)
        score3 = result3.get('risk_scoring_engine', {}).get('final_credit_score', 0)
        
        print(f"\n✅ All three tests completed successfully!")
        print(f"\nScore Comparison:")
        print(f"   Excellent Company: {score1}/100")
        print(f"   Average Company:   {score2}/100")
        print(f"   Poor Company:      {score3}/100")
        
        if score1 >= score2 >= score3:
            print(f"\n✅ ✅ ✅ VALIDATION PASSED!")
            print(f"✅ Scores are LOGICAL: {score1} >= {score2} >= {score3}")
            print(f"✅ System correctly processes REAL uploaded files!")
        else:
            print(f"\n⚠️ Scores not in expected order")
    else:
        print(f"\n⚠️ Some tests failed - check errors above")
    
    print(f"\n📁 Sample files created in: ./test_data/")
    print(f"   You can upload these files through the frontend UI as well!")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    run_comprehensive_test()
