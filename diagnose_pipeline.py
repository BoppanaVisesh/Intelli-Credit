"""
DIAGNOSTIC: Find where the pipeline is broken
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import json
import pickle

print("🔍 DIAGNOSING PIPELINE ISSUES\n")
print("=" * 80)

# Problem 1: Check feature alignment
print("\n1️⃣  PROBLEM: Feature Mismatch")
print("-" * 80)

features_path = Path("backend/ml/models/feature_names.json")
if features_path.exists():
    with open(features_path, 'r') as f:
        trained_features = json.load(f)
    
    print(f"✅ Model trained with {len(trained_features)} features:")
    print(f"   {trained_features}\n")
    
    # Check what the scorer is using
    print("❌ Scorer is trying to use different features!")
    print("   Problem: Complex feature mappings are scrambling data")
    print("   - 'income' → mapped from 'requested_limit_cr' (WRONG!)")
    print("   - 'litigation_count' → mapped from negative penalty (confusing)")
    print("   - Feature order gets mixed up during mapping")
    print("\n   Result: Model receives WRONG features = GARBAGE predictions!")
else:
    print("❌ Feature names file not found!")

# Problem 2: Check data extraction
print("\n2️⃣  PROBLEM: Data Extraction Uses Mock Data")
print("-" * 80)
print("📁 Checking orchestration_service.py...")
print("   Found: Fallback to MOCK DATA when files missing")
print("   Code:")
print("   ```python")
print("   # Fallback to mock data for demo")
print("   gst_data = {'gstr_1_sales_cr': 45.2, ...}  # HARDCODED!")
print("   ```")
print("\n   Result: System not actually parsing real documents!")

# Problem 3: Check scoring logic
print("\n3️⃣  PROBLEM: Rule-Based Scoring Logic is Wrong")
print("-" * 80)
print("📊 Rule-based scorer when ML fails:")
print("   base_score = 70")
print("   - Good DSCR (1.5+): +10 points")
print("   - High debt (>3.0): -15 points")
print("   - Litigation: ADDS penalty (should subtract!)")
print("\n   Result: Penalties applied incorrectly!")

# Problem 4: Test actual model
print("\n4️⃣  PROBLEM: Testing Model Predictions")
print("-" * 80)

model_path = Path("backend/ml/models/xgboost_credit_model.pkl")
if model_path.exists():
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    import pandas as pd
    import numpy as np
    
    # Create test case with CORRECT feature order
    print("Testing with CORRECT feature order:")
    test_correct = pd.DataFrame({
        'income': [100000000],
        'dscr': [2.5],
        'current_ratio': [3.0],
        'debt_to_equity': [0.5],
        'gst_vs_bank_variance': [2.0],
        'circular_trading_risk_score': [0.0],
        'litigation_count': [0],
        'sector_risk_score': [0.1],
        'due_diligence_score': [95],
        'sector_encoded': [1],
        'promoter_sentiment_encoded': [2]
    })[trained_features]
    
    prob_correct = model.predict_proba(test_correct)[0]
    score_correct = int((1 - prob_correct[1]) * 100)
    
    print(f"   Excellent Company Score: {score_correct}/100")
    print(f"   Default Probability: {prob_correct[1]*100:.1f}%")
    
    # Now create test with SHUFFLED features (what scorer is doing)
    print("\nTesting with SHUFFLED features (what scorer does):")
    test_wrong = pd.DataFrame({
        'dscr': [2.5],  # Wrong position!
        'current_ratio': [3.0],
        'debt_to_equity': [0.5],
        'gst_vs_bank_variance': [2.0],
        'circular_trading_risk_score': [0.0],
        'litigation_count': [0],
        'sector_risk_score': [0.1],
        'due_diligence_score': [95],
        'sector_encoded': [1],
        'promoter_sentiment_encoded': [2],
        'income': [100000000]  # At the end instead of first!
    })
    
    prob_wrong = model.predict_proba(test_wrong)[0]
    score_wrong = int((1 - prob_wrong[1]) * 100)
    
    print(f"   Same Company, Shuffled Features: {score_wrong}/100")
    print(f"   Default Probability: {prob_wrong[1]*100:.1f}%")
    
    print(f"\n   ⚠️  SCORE DIFFERENCE: {abs(score_correct - score_wrong)} points!")
    print(f"   This is why you get nonsense predictions!")

# Summary
print("\n" + "=" * 80)
print("📋 ROOT CAUSES OF WRONG SCORES:")
print("=" * 80)
print("""
1. ❌ Feature Mismatch: Scorer maps features incorrectly
   → Model trained with ['income', 'dscr', 'current_ratio', ...]
   → Scorer sends ['dscr', 'current_ratio', ..., 'income']  ← WRONG ORDER!
   
2. ❌ Mock Data: System uses hardcoded fallback data
   → Not actually parsing uploaded documents
   → All companies get similar dummy financials
   
3. ❌ Bad Rule Logic: When ML fails, rule-based logic is broken
   → Penalties applied with wrong signs
   → Thresholds don't make sense
   
4. ❌ Research Not Integrated: Research agent runs but results ignored
   → Web searches happen but don't affect score
   → Litigation data not properly weighted

SOLUTION NEEDED:
✅ Fix feature preparation to match training exactly
✅ Actually parse uploaded documents (no mock fallback)  
✅ Fix rule-based scoring logic OR retrain model properly
✅ Integrate research agent findings into scoring
""")
