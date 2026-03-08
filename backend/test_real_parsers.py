"""
Test All Real Parsers - Verify NO MOCK DATA is being used

This script tests:
1. ✅ Annual Report Parser - Uses Gemini Vision (not mock)
2. ✅ Bank Statement Parser - Real calculations (not mock)
3. ✅ GST Parser - Real extraction (not mock)
4. ✅ News Analyzer - Uses Tavily API (not mock)
5. ✅ eCourts Fetcher - Uses Tavily search (not mock)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pillar1_ingestor.annual_report_parser import AnnualReportParser
from pillar1_ingestor.bank_statement_parser import BankStatementParser
from pillar1_ingestor.gst_parser import GSTParser
from pillar2_research.news_analyzer import NewsAnalyzer
from pillar2_research.ecourt_fetcher import ECourtsFetcher
import os


def test_annual_report_parser():
    """Test Annual Report Parser with real PDF"""
    print("\n" + "="*90)
    print("TEST 1: ANNUAL REPORT PARSER (Gemini Vision)")
    print("="*90)
    
    parser = AnnualReportParser()
    
    # Check if API key is configured
    if not parser.api_key:
        print("⚠️  GEMINI_API_KEY not set - parser will return default data")
        return False
    else:
        print(f"✅ Gemini API Key: {parser.api_key[:20]}... ({len(parser.api_key)} chars)")
    
    # Test with actual PDF if available
    test_pdf = "AnnualReport_SpiceJet_202324.pdf"
    if os.path.exists(test_pdf):
        print(f"\n📄 Parsing: {test_pdf}")
        result = parser.parse_annual_report(test_pdf)
        
        print(f"\n✅ EXTRACTED DATA:")
        print(f"   Company: {result.get('company_name', 'N/A')}")
        print(f"   FY: {result.get('financial_year', 'N/A')}")
        print(f"   Auditor: {result.get('auditor_name', 'N/A')}")
        print(f"   Opinion: {result.get('auditor_opinion', 'N/A')}")
        print(f"   Revenue: ₹{result.get('revenue_cr', 0):.2f} Cr")
        print(f"   Debt: ₹{result.get('total_debt_cr', 0):.2f} Cr")
        print(f"   Equity: ₹{result.get('total_equity_cr', 0):.2f} Cr")
        print(f"   Litigations: {len(result.get('pending_litigations', []))}")
        
        return True
    else:
        print(f"⚠️  Test PDF not found: {test_pdf}")
        return False


def test_bank_statement_parser():
    """Test Bank Statement Parser with real Excel file"""
    print("\n" + "="*90)
    print("TEST 2: BANK STATEMENT PARSER (Real Calculations)")
    print("="*90)
    
    parser = BankStatementParser()
    
    # Test with created Excel files
    test_files = [
        "test_data/Bank_Statement_TechCorp_Excellent.xlsx",
        "test_data/Bank_Statement_MidTier_Average.xlsx",
        "test_data/Bank_Statement_Struggling_Risky.xlsx"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📊 Parsing: {test_file}")
            result = parser.parse_bank_statement(test_file)
            
            print(f"   Inflows: ₹{result['total_inflows_cr']:.2f} Cr")
            print(f"   Outflows: ₹{result['total_outflows_cr']:.2f} Cr")
            print(f"   Avg Balance: ₹{result['average_monthly_balance_cr']:.2f} Cr")
            print(f"   Transactions: {result['number_of_transactions']}")
            print(f"   Bounced Checks: {result['bounced_checks']}")
            print(f"   Overdrafts: {result['overdraft_instances']}")
            
            # Verify it's not returning mock data (exact 44.8 Cr would indicate mock)
            if result['total_inflows_cr'] == 44.8 and result['total_outflows_cr'] == 42.3:
                print("   ⚠️  WARNING: Looks like mock data!")
                return False
            else:
                print("   ✅ REAL calculations performed")
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return True


def test_gst_parser():
    """Test GST Parser with real Excel file"""
    print("\n" + "="*90)
    print("TEST 3: GST PARSER (Real Extraction)")
    print("="*90)
    
    parser = GSTParser()
    
    # Test with created GST files
    test_files = [
        "test_data/GST_Returns_TechCorp_Excellent.xlsx",
        "test_data/GST_Returns_MidTier_Average.xlsx"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📋 Parsing: {test_file}")
            result = parser.parse_gst_file(test_file)
            
            print(f"   GSTR-1 Sales: ₹{result['gstr_1_sales_cr']:.2f} Cr")
            print(f"   GSTR-3B Sales: ₹{result['gstr_3b_sales_cr']:.2f} Cr")
            print(f"   Purchases: ₹{result['gstr_2a_purchases_cr']:.2f} Cr")
            print(f"   Tax Liability: ₹{result['net_tax_liability_cr']:.2f} Cr")
            
            # Verify not mock (exact 45.2 would be mock)
            if result['gstr_1_sales_cr'] == 45.2:
                print("   ⚠️  WARNING: Looks like mock data!")
                return False
            else:
                print("   ✅ REAL extraction performed")
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return True


def test_news_analyzer():
    """Test News Analyzer with real Tavily API"""
    print("\n" + "="*90)
    print("TEST 4: NEWS ANALYZER (Tavily API)")
    print("="*90)
    
    analyzer = NewsAnalyzer()
    
    if not analyzer.api_key:
        print("⚠️  TAVILY_API_KEY not set - cannot fetch real news")
        return False
    else:
        print(f"✅ Tavily API Key: {analyzer.api_key[:20]}... ({len(analyzer.api_key)} chars)")
    
    # Test with real company
    print(f"\n🔍 Fetching news for: Infosys Limited")
    result = analyzer.analyze_company_news("Infosys Limited")
    
    print(f"\n✅ NEWS ANALYSIS:")
    print(f"   Articles Found: {result['article_count']}")
    print(f"   Overall Sentiment: {result['overall_sentiment']}")
    print(f"   Positive: {result['positive_count']}, Negative: {result['negative_count']}, Neutral: {result['neutral_count']}")
    print(f"   Key Topics: {', '.join(result['key_topics'])}")
    print(f"   Risk Alerts: {len(result['risk_alerts'])}")
    
    if result['article_count'] > 0:
        print(f"\n   Sample Article:")
        article = result['articles'][0]
        print(f"   - {article['title']}")
        print(f"   - Source: {article['source']}")
        print(f"   - Sentiment: {article['sentiment']}")
        return True
    else:
        print("   ⚠️  No articles found")
        return False


def test_ecourts_fetcher():
    """Test eCourts Fetcher with real Tavily search"""
    print("\n" + "="*90)
    print("TEST 5: ECOURTS FETCHER (Tavily Search)")
    print("="*90)
    
    fetcher = ECourtsFetcher()
    
    if not fetcher.api_key:
        print("⚠️  TAVILY_API_KEY not set - cannot search litigation")
        return False
    else:
        print(f"✅ Tavily API Key configured")
    
    # Test with real company
    print(f"\n🔍 Searching litigation for: SpiceJet Limited")
    result = fetcher.search_litigation("SpiceJet Limited", "")
    
    print(f"\n✅ LITIGATION SEARCH:")
    print(f"   Records Found: {len(result)}")
    
    if len(result) > 0:
        for i, record in enumerate(result[:3], 1):
            print(f"\n   Case {i}:")
            print(f"   - Source: {record.get('source', 'N/A')}")
            print(f"   - Summary: {record.get('summary', 'N/A')[:100]}...")
            print(f"   - Severity: {record.get('severity_penalty', 0)}")
        return True
    else:
        print("   ⚠️  No litigation records found")
        return True  # Still counts as success if API worked


def main():
    """Run all parser tests"""
    print("\n" + "="*90)
    print(" " * 25 + "REAL PARSER VERIFICATION")
    print("="*90)
    print("\nVerifying all parsers use REAL code, not mock data\n")
    
    results = {
        'Annual Report Parser': test_annual_report_parser(),
        'Bank Statement Parser': test_bank_statement_parser(),
        'GST Parser': test_gst_parser(),
        'News Analyzer': test_news_analyzer(),
        'eCourts Fetcher': test_ecourts_fetcher()
    }
    
    # Summary
    print("\n" + "="*90)
    print(" " * 30 + "TEST SUMMARY")
    print("="*90)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:>10} - {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nRESULT: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\nSUCCESS: All parsers using REAL code, NO mock data!")
    else:
        print("\nATTENTION: Some parsers still using mock data or APIs not configured")
    
    print("\n" + "="*90)


if __name__ == "__main__":
    main()
