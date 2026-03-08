"""
Test CAM Dynamic Generation
============================

Verify that CAM executive summary and sector headwinds are DIFFERENT
for different companies.
"""

import sys
sys.path.insert(0, '.')

from services.orchestration_service import CreditAnalysisOrchestrator

# Test data - Excellent company
excellent_company = {
    'company_name': 'TechCorp Industries Ltd',
    'sector': 'Technology',
    'requested_limit_cr': 15.0
}

excellent_financial = {
    'raw_data_extracted': {
        'gstr_1_sales_cr': 65.5,
        'bank_statement_inflows_cr': 64.2
    },
    'calculated_ratios': {
        'dscr': 1.85,
        'current_ratio': 2.0,
        'debt_to_equity': 0.70
    },
    'reconciliation_flags': {
        'gst_vs_bank_variance_percent': 2.0,
        'circular_trading_risk': 0
    }
}

excellent_research = {
    'litigation_and_nclt': [],
    'sector_risk_score': 20,
    'promoter_checks': [{'sentiment': 'POSITIVE'}]
}

excellent_scoring = {
    'final_credit_score': 88,
    'decision': 'APPROVE',
    'recommended_limit_cr': 12.5,
    'risk_grade': 'A'
}

# Test data - Risky company
risky_company = {
    'company_name': 'Struggling Steel Traders Ltd',
    'sector': 'Steel Trading',
    'requested_limit_cr': 20.0
}

risky_financial = {
    'raw_data_extracted': {
        'gstr_1_sales_cr': 27.3,
        'bank_statement_inflows_cr': 18.1
    },
    'calculated_ratios': {
        'dscr': 0.65,
        'current_ratio': 0.85,
        'debt_to_equity': 14.0
    },
    'reconciliation_flags': {
        'gst_vs_bank_variance_percent': 33.7,
        'circular_trading_risk': 55
    }
}

risky_research = {
    'litigation_and_nclt': [
        {'summary': 'Supplier default case pending'},
        {'summary': 'Tax evasion investigation'}
    ],
    'sector_risk_score': 65,
    'promoter_checks': [{'sentiment': 'NEGATIVE'}]
}

risky_scoring = {
    'final_credit_score': 22,
    'decision': 'REJECT',
    'recommended_limit_cr': 0.0,
    'risk_grade': 'D'
}

# Initialize orchestrator
orchestrator = CreditAnalysisOrchestrator()

print("\n" + "="*80)
print("🧪 TESTING CAM DYNAMIC GENERATION")
print("="*80)

# Test 1: Excellent company
print("\n1️⃣  EXCELLENT COMPANY - Executive Summary")
print("-" * 80)
summary1 = orchestrator._generate_executive_summary(
    excellent_company, excellent_financial, excellent_research, excellent_scoring
)
print(summary1)

# Test 2: Risky company
print("\n\n2️⃣  RISKY COMPANY - Executive Summary")
print("-" * 80)
summary2 = orchestrator._generate_executive_summary(
    risky_company, risky_financial, risky_research, risky_scoring
)
print(summary2)

# Test 3: Sector headwinds - Tech
print("\n\n3️⃣  TECHNOLOGY SECTOR - Sector Headwinds")
print("-" * 80)
tech_sector_data = {
    'outlook': 'Positive',
    'growth_rate': 12.8,
    'risk_score': 20,
    'headwinds': ['US recession fears', 'Client budget cuts'],
    'tailwinds': ['Digital transformation demand', 'Cloud migration', 'AI/ML adoption'],
    'regulatory_changes': 'No major regulatory changes'
}
headwinds1 = orchestrator._build_sector_headwinds_text(
    'TechCorp Industries Ltd', 'Technology', tech_sector_data
)
print(headwinds1)

# Test 4: Sector headwinds - Steel
print("\n\n4️⃣  STEEL TRADING SECTOR - Sector Headwinds")
print("-" * 80)
steel_sector_data = {
    'outlook': 'Challenging',
    'growth_rate': 2.0,
    'risk_score': 65,
    'headwinds': ['Raw material price volatility', 'Import dumping', 'Overcapacity'],
    'tailwinds': ['Infrastructure demand'],
    'regulatory_changes': 'New anti-dumping duties imposed on Chinese steel imports'
}
headwinds2 = orchestrator._build_sector_headwinds_text(
    'Struggling Steel Traders Ltd', 'Steel Trading', steel_sector_data
)
print(headwinds2)

# Verification
print("\n\n" + "="*80)
print("📊 VERIFICATION RESULTS")
print("="*80)

# Check if summaries are different
if summary1 != summary2:
    print("✅ PASS: Executive summaries are DIFFERENT")
    print(f"   Length: Excellent={len(summary1)} chars, Risky={len(summary2)} chars")
else:
    print("❌ FAIL: Executive summaries are IDENTICAL (hardcoded)")

# Check if sector headwinds are different
if headwinds1 != headwinds2:
    print("✅ PASS: Sector headwinds are DIFFERENT")
    print(f"   Length: Tech={len(headwinds1)} chars, Steel={len(headwinds2)} chars")
else:
    print("❌ FAIL: Sector headwinds are IDENTICAL (hardcoded)")

# Check for company names in summaries
if 'TechCorp Industries' in summary1:
    print("✅ PASS: Company name appears in executive summary")
else:
    print("❌ FAIL: Company name missing from executive summary")

# Check for specific numbers
if '88/100' in summary1 and '22/100' in summary2:
    print("✅ PASS: Different credit scores appear in summaries")
else:
    print("❌ FAIL: Credit scores not showing correctly")

if 'APPROVE' in summary1 and 'REJECT' in summary2:
    print("✅ PASS: Different decisions appear in summaries")
else:
    print("❌ FAIL: Decisions not showing correctly")

# Check for specific issues mentioned
if 'litigation' in summary2.lower() or '2 litigation' in summary2:
    print("✅ PASS: Specific litigation count mentioned in risky company")
else:
    print("⚠️  WARNING: Litigation details may not be specific enough")

if '33.7%' in summary2 or 'SIGNIFICANT' in summary2:
    print("✅ PASS: High GST-Bank variance mentioned in risky company")
else:
    print("❌ FAIL: GST-Bank variance not calculated correctly")

print("\n" + "="*80)
print("🎯 CAM DYNAMIC GENERATION TEST COMPLETE")
print("="*80 + "\n")
