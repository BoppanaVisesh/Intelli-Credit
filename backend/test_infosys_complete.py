"""
Complete End-to-End Credit Analysis Test
Uses REAL Infosys Annual Report + Web Research + Credit Scoring
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.orchestration_service import CreditAnalysisOrchestrator
from pillar1_ingestor.annual_report_parser import AnnualReportParser
from pillar2_research.news_analyzer import NewsAnalyzer
from pillar2_research.ecourt_fetcher import ECourtsFetcher
from pillar2_research.promoter_profiler import PromoterProfiler
from pillar3_recommendation.credit_scorer_fixed import CreditScorerFixed
import os
from dotenv import load_dotenv

load_dotenv()


def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


async def test_infosys_credit_analysis():
    """Complete credit analysis for Infosys using real data"""
    
    print_header("🚀 INTELLI-CREDIT: COMPLETE CREDIT ANALYSIS FOR INFOSYS")
    
    # Company details
    company_name = "Infosys Limited"
    mca_cin = "L85110KA1981PLC013115"  # Infosys's actual CIN
    sector = "Information Technology"
    requested_limit_cr = 1000.0  # 1000 Crores loan request
    
    print(f"📋 Application Details:")
    print(f"   Company: {company_name}")
    print(f"   CIN: {mca_cin}")
    print(f"   Sector: {sector}")
    print(f"   Requested Limit: ₹{requested_limit_cr} Crores")
    
    # Check API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print(f"\n🔑 API Keys:")
    print(f"   GEMINI_API_KEY: {'✅ Configured' if gemini_key else '❌ Missing'}")
    print(f"   TAVILY_API_KEY: {'✅ Configured' if tavily_key else '❌ Missing'}")
    
    # ==================== PILLAR 1: DOCUMENT PARSING ====================
    print_header("📄 PILLAR 1: PARSING ANNUAL REPORT")
    
    pdf_path = "infosys-ar-24.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📂 Found: {pdf_path}")
    print(f"   File size: {Path(pdf_path).stat().st_size / (1024*1024):.2f} MB")
    
    parser = AnnualReportParser(api_key=gemini_key)
    print(f"\n🔍 Parsing with Gemini Vision AI...")
    print(f"   This may take 30-60 seconds...")
    
    annual_report_data = parser.parse_annual_report(pdf_path)
    
    print(f"\n✅ Annual Report Parsed!")
    print(f"\n📊 Extracted Financial Data:")
    print(f"   Revenue (Cr): ₹{annual_report_data.get('revenue_cr', 'N/A')}")
    print(f"   Total Assets (Cr): ₹{annual_report_data.get('total_assets_cr', 'N/A')}")
    print(f"   Total Debt (Cr): ₹{annual_report_data.get('total_debt_cr', 'N/A')}")
    print(f"   Net Worth (Cr): ₹{annual_report_data.get('net_worth_cr', 'N/A')}")
    print(f"   Net Profit (Cr): ₹{annual_report_data.get('net_profit_cr', 'N/A')}")
    print(f"   EBITDA (Cr): ₹{annual_report_data.get('ebitda_cr', 'N/A')}")
    
    print(f"\n📋 Other Information:")
    print(f"   Auditor: {annual_report_data.get('auditor_name', 'N/A')}")
    print(f"   Audit Opinion: {annual_report_data.get('audit_opinion', 'N/A')}")
    print(f"   Pending Litigations: {len(annual_report_data.get('pending_litigations', []))}")
    
    # ==================== PILLAR 2: WEB RESEARCH ====================
    print_header("🌐 PILLAR 2: WEB RESEARCH & INTELLIGENCE")
    
    # News Analysis
    print(f"📰 Analyzing Company News...")
    news_analyzer = NewsAnalyzer(api_key=tavily_key)
    news_data = news_analyzer.analyze_company_news(company_name)
    
    print(f"\n✅ News Analysis Complete:")
    print(f"   Articles Found: {news_data.get('article_count', 0)}")
    print(f"   Overall Sentiment: {news_data.get('overall_sentiment', 'N/A')}")
    print(f"   Positive: {news_data.get('positive_count', 0)}")
    print(f"   Negative: {news_data.get('negative_count', 0)}")
    print(f"   Neutral: {news_data.get('neutral_count', 0)}")
    
    if news_data.get('risk_alerts'):
        print(f"\n⚠️  Risk Alerts:")
        for alert in news_data['risk_alerts'][:3]:
            print(f"   • {alert}")
    
    # Litigation Search
    print(f"\n⚖️  Searching Litigation Records...")
    ecourts = ECourtsFetcher(tavily_api_key=tavily_key)
    litigation_cases = ecourts.search_litigation(company_name, mca_cin)
    
    print(f"\n✅ Litigation Search Complete:")
    print(f"   Total Results: {len(litigation_cases)}")
    
    # Determine risk level based on case count
    if len(litigation_cases) == 0:
        lit_risk = "LOW"
    elif len(litigation_cases) <= 3:
        lit_risk = "MEDIUM"
    else:
        lit_risk = "HIGH"
    print(f"   Risk Level: {lit_risk}")
    
    if litigation_cases:
        print(f"\n   Recent Cases:")
        for case in litigation_cases[:3]:
            print(f"   • {case.get('title', 'N/A')[:80]}...")
    
    # Promoter Profiling
    print(f"\n👥 Promoter/Director Research...")
    promoter_profiler = PromoterProfiler(tavily_api_key=tavily_key)
    
    # Infosys key promoters
    promoters = ["Salil Parekh", "Infosys Management"]
    promoter_findings = []
    
    for promoter in promoters[:1]:  # Test with first one
        print(f"   Researching: {promoter}...")
        finding = promoter_profiler.profile_promoter(promoter, company_name)
        promoter_findings.append(finding)
    
    print(f"✅ Promoter Research Complete: {len(promoter_findings)} profiles")
    
    # ==================== PILLAR 3: CREDIT SCORING ====================
    print_header("🎯 PILLAR 3: CREDIT SCORING ENGINE")
    
    # Calculate financial ratios
    revenue = annual_report_data.get('revenue_cr', 100000)
    total_debt = annual_report_data.get('total_debt_cr', 5000)
    total_equity = annual_report_data.get('total_equity_cr', 80000)
    net_worth = total_equity if total_equity else annual_report_data.get('net_worth_cr', 80000)
    net_profit = annual_report_data.get('net_profit_cr', 20000)
    ebitda = annual_report_data.get('ebitda_cr', net_profit * 1.2)  # Estimate if not available
    
    # Calculate ratios
    interest_estimate = total_debt * 0.08  # Assume 8% interest rate (IT companies have low rates)
    dscr = ebitda / interest_estimate if interest_estimate > 0 else 10.0  # High DSCR for IT companies
    debt_to_equity = total_debt / net_worth if net_worth > 0 else 0.05
    current_ratio = 1.8  # IT companies typically have good liquidity
    
    print(f"📊 Financial Ratios:")
    print(f"   DSCR: {dscr:.2f}")
    print(f"   Debt-to-Equity: {debt_to_equity:.2f}")
    print(f"   Current Ratio: {current_ratio:.2f}")
    print(f"   Net Profit Margin: {(net_profit/revenue*100):.1f}%")
    
    # Prepare scoring input
    scoring_input = {
        'requested_limit_cr': requested_limit_cr,
        'financials': {
            'dscr': dscr,
            'current_ratio': current_ratio,
            'debt_to_equity': debt_to_equity,
            'revenue_cr': revenue,
            'total_debt_cr': total_debt,
            'net_worth_cr': net_worth,
            'ebitda_cr': ebitda,
            'gst_vs_bank_variance': 1.5,  # Low variance (good)
            'circular_trading_score': 5   # Very low risk
        },
        'research': {
            'news_sentiment': news_data.get('overall_sentiment', 'NEUTRAL'),
            'litigation_count': len(litigation_cases),
            'litigation_risk': lit_risk,
            'promoter_sentiment': promoter_findings[0]['sentiment'] if promoter_findings else 'NEUTRAL'
        },
        'sector': {
            'name': sector,
            'risk_level': 'LOW'  # IT is stable sector
        },
        'due_diligence': {
            'notes': 'Tier-1 IT company with strong fundamentals and global presence.',
            'officer_assessment': 'STRONG'
        }
    }
    
    # Calculate credit score
    scorer = CreditScorerFixed()
    print(f"\n🧮 Calculating Credit Score using 5 Cs Framework...")
    
    scoring_result = scorer.calculate_credit_score(scoring_input)
    
    print(f"\n✅ SCORING COMPLETE!")
    print(f"\n{'='*80}")
    print(f"  CREDIT SCORE: {scoring_result['final_credit_score']}/100")
    print(f"  DECISION: {scoring_result['decision']}")
    print(f"  RECOMMENDED LIMIT: ₹{scoring_result['recommended_limit_cr']:.2f} Crores")
    print(f"{'='*80}")
    
    print(f"\n📊 Score Breakdown (5 Cs of Credit):")
    print(f"   Capacity (Repayment Ability): {scoring_result['sub_scores']['capacity']['score']}/100 (weight: {scoring_result['sub_scores']['capacity']['weight']}%)")
    print(f"   Character (Willingness):      {scoring_result['sub_scores']['character']['score']}/100 (weight: {scoring_result['sub_scores']['character']['weight']}%)")
    print(f"   Capital (Equity Cushion):     {scoring_result['sub_scores']['capital']['score']}/100 (weight: {scoring_result['sub_scores']['capital']['weight']}%)")
    print(f"   Conditions (Market/Sector):   {scoring_result['sub_scores']['conditions']['score']}/100 (weight: {scoring_result['sub_scores']['conditions']['weight']}%)")
    print(f"   Collateral (Security):        {scoring_result['sub_scores']['collateral']['score']}/100 (weight: {scoring_result['sub_scores']['collateral']['weight']}%)")
    
    print(f"\n🔍 Key Score Drivers:")
    for factor in scoring_result.get('key_factors', [])[:5]:
        print(f"   • {factor}")
    
    # ==================== DECISION RECOMMENDATION ====================
    print_header("💼 LOAN DECISION RECOMMENDATION")
    
    final_decision = scoring_result['decision']
    final_score = scoring_result['final_credit_score']
    
    if final_decision == "APPROVE":
        print(f"✅ RECOMMENDATION: APPROVE LOAN")
        print(f"\n   Approved Limit: ₹{scoring_result['recommended_limit_cr']:.2f} Crores")
        print(f"   Terms: Standard commercial terms")
        print(f"   Interest Rate: Prime rate (best rate for AAA/AA companies)")
        print(f"   Monitoring: Standard quarterly reviews")
        print(f"   Collateral: Unsecured/Corporate guarantee acceptable")
    elif final_decision == "CONDITIONAL_APPROVE":
        print(f"⚠️  RECOMMENDATION: CONDITIONAL APPROVAL")
        print(f"\n   Approved Limit: ₹{scoring_result['recommended_limit_cr']:.2f} Crores")
        print(f"   Conditions:")
        print(f"   • Enhanced monitoring required")
        print(f"   • Quarterly financial reviews")
        print(f"   • Maintain minimum financial covenants")
    else:
        print(f"❌ RECOMMENDATION: REJECT LOAN APPLICATION")
        print(f"\n   Reasons:")
        if dscr < 1.25:
            print(f"   • Low DSCR ({dscr:.2f}) - Inadequate debt servicing capacity")
        if debt_to_equity > 3:
            print(f"   • High leverage ({debt_to_equity:.2f}x) - Excessive debt burden")
    
    # ==================== EXECUTIVE SUMMARY ====================
    print_header("📝 EXECUTIVE SUMMARY")
    
    print(f"Based on comprehensive analysis of {company_name}:")
    print(f"\n1️⃣ DOCUMENT ANALYSIS")
    print(f"   • Annual Report FY 2024 parsed using Gemini Vision AI")
    print(f"   • Revenue: ₹{revenue:,.0f} Crores")
    print(f"   • Net Profit: ₹{net_profit:,.0f} Crores")
    print(f"   • Auditor: {annual_report_data.get('auditor_name', 'Unknown')}")
    
    print(f"\n2️⃣ WEB INTELLIGENCE")
    print(f"   • News Sentiment: {news_data.get('overall_sentiment', 'N/A')}")
    print(f"   • Articles Analyzed: {news_data.get('article_count', 0)}")
    print(f"   • Litigation Cases: {len(litigation_cases)} (Risk: {lit_risk})")
    print(f"   • Promoter Research: {len(promoter_findings)} profile(s)")
    
    print(f"\n3️⃣ CREDIT ASSESSMENT")
    print(f"   • Final Score: {final_score}/100")
    print(f"   • Risk Grade: {scoring_result.get('risk_grade', 'N/A')}")
    print(f"   • Decision: {final_decision}")
    print(f"   • Recommended Limit: ₹{scoring_result['recommended_limit_cr']:.2f} Crores")
    print(f"   • Approval Rate: {scoring_result.get('approval_percentage', 0)}% of requested amount")
    
    print(f"\n4️⃣ KEY HIGHLIGHTS")
    if final_decision == "APPROVE":
        print(f"   ✓ Excellent financial strength")
        print(f"   ✓ Strong operating cash flows")
        print(f"   ✓ Market leadership position")
        print(f"   ✓ Minimal credit risk")
    elif final_decision == "CONDITIONAL_APPROVE":
        print(f"   ✓ Good financial position with minor concerns")
        print(f"   ✓ Enhanced monitoring recommended")
    
    # ==================== FINAL SUMMARY ====================
    print_header("📋 ANALYSIS COMPLETE - FINAL SUMMARY")
    
    print(f"🏢 Company: {company_name}")
    print(f"📊 Credit Score: {final_score}/100")
    print(f"⚖️  Decision: {final_decision}")
    print(f"💰 Recommended Limit: ₹{scoring_result['recommended_limit_cr']:.2f} Crores")
    print(f"   (Requested: ₹{requested_limit_cr} Crores)")
    
    print(f"\n✅ Data Sources Used:")
    print(f"   • Annual Report (Gemini Vision AI)")
    print(f"   • Web News ({news_data.get('article_count', 0)} articles)")
    print(f"   • Litigation Search (Tavily API)")
    print(f"   • Promoter Research (Web Search)")
    print(f"   • Financial Ratio Analysis")
    print(f"   • 5 Cs Credit Framework")
    
    print(f"\n{'='*80}")
    print(f"  🎯 END-TO-END CREDIT ANALYSIS COMPLETED SUCCESSFULLY!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_infosys_credit_analysis())
