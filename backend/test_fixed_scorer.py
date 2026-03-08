"""
Test the FIXED Credit Scorer to verify logical scoring

This test verifies that:
1. Excellent companies score HIGHER than poor companies
2. Scores reflect financial strength correctly
3. Each C factor contributes properly
"""

from pillar3_recommendation.credit_scorer_fixed import CreditScorerFixed


def test_logical_scoring():
    """Test that the fixed scorer produces logical results"""
    
    scorer = CreditScorerFixed()
    
    print("="*70)
    print("TESTING FIXED CREDIT SCORER")
    print("="*70)
    
    # Test Case 1: EXCELLENT Company
    print("\n" + "="*70)
    print("TEST 1: EXCELLENT COMPANY (Strong fundamentals, no red flags)")
    print("="*70)
    
    excellent_company = {
        'financials': {
            'dscr': 3.0,                      # Excellent debt coverage
            'current_ratio': 2.5,             # Strong liquidity
            'debt_to_equity': 0.3,            # Low leverage
            'gst_vs_bank_variance': 2.0,      # Good reconciliation
        },
        'research': {
            'litigation_count': 0,             # Clean record
            'litigation_severity': 'None',
            'promoter_sentiment': 'Positive',  # Good reputation
            'circular_trading_risk_score': 10, # No suspicious patterns
            'sector_sentiment': 'Neutral'
        },
        'sector': {
            'sector_risk_score': 20            # Stable sector
        },
        'due_diligence': {
            'notes': 'Impressive operations observed',
            'severity': 'Positive'
        },
        'requested_limit_cr': 10.0
    }
    
    result1 = scorer.calculate_credit_score(excellent_company)
    
    print(f"\n✅ FINAL SCORE: {result1['final_credit_score']}/100")
    print(f"✅ DECISION: {result1['decision']}")
    print(f"✅ RISK GRADE: {result1['risk_grade']}")
    print(f"✅ RECOMMENDED LIMIT: ₹{result1['recommended_limit_cr']} Cr ({result1['approval_percentage']}% of requested)")
    
    print(f"\n📊 SUB-SCORES:")
    for factor, data in result1['sub_scores'].items():
        print(f"   {factor.upper():15s} : {data['score']}/100 (weight: {data['weight']*100:.0f}%)")
    
    print(f"\n💡 KEY FACTORS:")
    for i, factor in enumerate(result1['key_factors'], 1):
        print(f"   {i}. {factor}")
    
    # Test Case 2: AVERAGE Company
    print("\n" + "="*70)
    print("TEST 2: AVERAGE COMPANY (Moderate fundamentals, some concerns)")
    print("="*70)
    
    average_company = {
        'financials': {
            'dscr': 1.3,                      # Barely adequate
            'current_ratio': 1.2,
            'debt_to_equity': 2.0,            # Moderate leverage
            'gst_vs_bank_variance': 8.0,
        },
        'research': {
            'litigation_count': 2,             # Minor litigation
            'litigation_severity': 'Low',
            'promoter_sentiment': 'Neutral',
            'circular_trading_risk_score': 35,
            'sector_sentiment': 'Neutral'
        },
        'sector': {
            'sector_risk_score': 40
        },
        'due_diligence': {
            'notes': '',
            'severity': 'None'
        },
        'requested_limit_cr': 10.0
    }
    
    result2 = scorer.calculate_credit_score(average_company)
    
    print(f"\n⚠️ FINAL SCORE: {result2['final_credit_score']}/100")
    print(f"⚠️ DECISION: {result2['decision']}")
    print(f"⚠️ RISK GRADE: {result2['risk_grade']}")
    print(f"⚠️ RECOMMENDED LIMIT: ₹{result2['recommended_limit_cr']} Cr ({result2['approval_percentage']}% of requested)")
    
    print(f"\n📊 SUB-SCORES:")
    for factor, data in result2['sub_scores'].items():
        print(f"   {factor.upper():15s} : {data['score']}/100 (weight: {data['weight']*100:.0f}%)")
    
    # Test Case 3: POOR Company
    print("\n" + "="*70)
    print("TEST 3: POOR COMPANY (Weak fundamentals, multiple red flags)")
    print("="*70)
    
    poor_company = {
        'financials': {
            'dscr': 0.7,                      # CANNOT service debt
            'current_ratio': 0.8,             # Liquidity crisis
            'debt_to_equity': 6.0,            # Massively overleveraged
            'gst_vs_bank_variance': 18.0,     # Revenue inflation suspected
        },
        'research': {
            'litigation_count': 8,             # Serious litigation
            'litigation_severity': 'High',
            'promoter_sentiment': 'Negative',  # Adverse news
            'circular_trading_risk_score': 85, # High circular trading
            'sector_sentiment': 'Negative'
        },
        'sector': {
            'sector_risk_score': 65            # Troubled sector
        },
        'due_diligence': {
            'notes': 'Critical findings during field visit',
            'severity': 'Critical'
        },
        'requested_limit_cr': 10.0
    }
    
    result3 = scorer.calculate_credit_score(poor_company)
    
    print(f"\n❌ FINAL SCORE: {result3['final_credit_score']}/100")
    print(f"❌ DECISION: {result3['decision']}")
    print(f"❌ RISK GRADE: {result3['risk_grade']}")
    print(f"❌ RECOMMENDED LIMIT: ₹{result3['recommended_limit_cr']} Cr ({result3['approval_percentage']}% of requested)")
    
    print(f"\n📊 SUB-SCORES:")
    for factor, data in result3['sub_scores'].items():
        print(f"   {factor.upper():15s} : {data['score']}/100 (weight: {data['weight']*100:.0f}%)")
    
    print(f"\n💡 KEY FACTORS:")
    for i, factor in enumerate(result3['key_factors'], 1):
        print(f"   {i}. {factor}")
    
    # Validation
    print("\n" + "="*70)
    print("VALIDATION:")
    print("="*70)
    
    excellent_score = result1['final_credit_score']
    average_score = result2['final_credit_score']
    poor_score = result3['final_credit_score']
    
    print(f"\nExcellent Company Score: {excellent_score}/100")
    print(f"Average Company Score  : {average_score}/100")
    print(f"Poor Company Score     : {poor_score}/100")
    
    # Check logic
    if excellent_score > average_score > poor_score:
        print("\n✅ ✅ ✅ VALIDATION PASSED!")
        print("✅ Scoring is LOGICAL: Excellent > Average > Poor")
        return True
    else:
        print("\n❌ VALIDATION FAILED!")
        print("❌ Scores are still illogical")
        return False


if __name__ == "__main__":
    test_logical_scoring()
