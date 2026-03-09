"""
End-to-end test for the Fraud Detection / Cross-Verification Layer.

Tests:
 1. DataNormalizer — normalizes parsed docs
 2. CrossVerificationEngine — runs 14 rules
 3. CircularTradingDetector — ratio + graph analysis
 4. ML FraudModel — predict_fraud + extract_features
 5. Fraud API endpoint — POST /api/v1/fraud/run-verification/{id}
 6. Scoring API endpoint — POST /api/v1/scoring/calculate-score
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

API = "http://localhost:8000/api/v1"
APP_ID = None  # Will be discovered or created

# ── Helpers ──────────────────────────────────────────────────────────

def ok(msg):
    print(f"  PASS  {msg}")

def fail(msg):
    print(f"  FAIL  {msg}")
    raise AssertionError(msg)

passed = 0
failed = 0

def check(cond, msg):
    global passed, failed
    if cond:
        ok(msg)
        passed += 1
    else:
        fail(msg)
        failed += 1


# ── Unit Tests ───────────────────────────────────────────────────────

print("\n=== 1. DataNormalizer Unit Test ===")
from pillar1_ingestor.data_normalizer import DataNormalizer

normalizer = DataNormalizer()

# Test with realistic parsed data (mimicking what parsers store in DB)
sample_docs = [
    {
        "document_type": "BANK_STATEMENT",
        "parsed_data": json.dumps({
            "total_inflows_cr": 45.2,
            "total_outflows_cr": 38.7,
            "avg_monthly_balance_cr": 3.5,
            "bounced_checks": 2,
            "overdraft_instances": 1,
            "monthly_inflows": [3.5, 4.1, 3.8, 4.2, 3.6, 3.9, 4.0, 3.7, 3.8, 3.5, 3.6, 3.5],
        }),
    },
    {
        "document_type": "GST_RETURN",
        "parsed_data": json.dumps({
            "gstr_1_sales_cr": 48.5,
            "gstr_3b_sales_cr": 47.8,
            "gstr_2a_purchases_cr": 28.2,
            "net_tax_liability_cr": 3.65,
        }),
    },
    {
        "document_type": "ANNUAL_REPORT",
        "parsed_data": json.dumps({
            "company_name": "TestCorp Ltd",
            "revenue_cr": 50.0,
            "net_profit_cr": 4.2,
            "total_debt_cr": 12.0,
            "total_equity_cr": 18.0,
            "auditor_opinion": "unqualified",
            "pending_litigations": 1,
        }),
    },
]

normalized = normalizer.normalize(sample_docs)
check("gst" in normalized and "bank" in normalized and "annual_report" in normalized, "Normalizer produces all sections")
check(normalized["gst"]["sales_cr"] == 48.5, f"GST sales normalized: {normalized['gst'].get('sales_cr')}")
check(normalized["bank"]["total_inflows_cr"] == 45.2, f"Bank inflows normalized: {normalized['bank'].get('total_inflows_cr')}")
check(normalized["annual_report"]["revenue_cr"] == 50.0, f"AR revenue normalized")
check(len(normalized["sources_available"]) == 3, f"All 3 sources detected: {normalized['sources_available']}")


print("\n=== 2. CrossVerificationEngine Unit Test ===")
from pillar1_ingestor.cross_verification_engine import CrossVerificationEngine

cv = CrossVerificationEngine()
cv_result = cv.run_verification(normalized)

check("fraud_risk_score" in cv_result, f"CV returns fraud_risk_score: {cv_result.get('fraud_risk_score')}")
check("risk_level" in cv_result, f"CV risk level: {cv_result.get('risk_level')}")
check("anomalies" in cv_result, f"CV anomalies count: {len(cv_result.get('anomalies', []))}")
check(cv_result["fraud_risk_score"] >= 0, "Fraud score is non-negative")
check(cv_result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL"), f"Valid risk level")

# With this data, GST (48.5) vs Bank (45.2) ~7% variance — may or may not trigger
# But GST (48.5) vs AR (50) — ~3% variance — should be fine
print(f"  INFO  Fraud score={cv_result['fraud_risk_score']}, Level={cv_result['risk_level']}, Anomalies={len(cv_result.get('anomalies', []))}")


print("\n=== 3. CircularTradingDetector Unit Test ===")
from pillar1_ingestor.circular_trading_detector import CircularTradingDetector

ct = CircularTradingDetector()

# Test ratio-based detection
ratio_result = ct.detect_circular_trading(
    gst_sales=48.5, bank_inflows=45.2,
    gst_purchases=28.2, bank_outflows=38.7
)
check("circular_trading_risk" in ratio_result, f"Ratio risk: {ratio_result['circular_trading_risk']}")
check("risk_score" in ratio_result, f"Ratio score: {ratio_result['risk_score']}")

# Test graph-based detection with circular transactions
transactions = [
    {"from_entity": "CompanyA", "to_entity": "CompanyB", "amount": 10.0},
    {"from_entity": "CompanyB", "to_entity": "CompanyC", "amount": 9.5},
    {"from_entity": "CompanyC", "to_entity": "CompanyA", "amount": 9.0},  # circular!
    {"from_entity": "CompanyA", "to_entity": "CompanyD", "amount": 5.0},
]
graph_result = ct.detect_transaction_cycles(transactions)
check(graph_result["cycle_count"] >= 1, f"Graph detected {graph_result['cycle_count']} cycle(s)")
check(graph_result["entities"] == 4, f"Graph has {graph_result['entities']} entities")
check(len(graph_result["flags"]) > 0, f"Graph raised {len(graph_result['flags'])} flag(s)")

# Test full_analysis
full = ct.full_analysis(
    gst_sales=48.5, bank_inflows=45.2,
    gst_purchases=28.2, bank_outflows=38.7,
    transactions=transactions
)
check("combined_risk_score" in full, f"Full analysis score: {full['combined_risk_score']}")
check("combined_risk_level" in full, f"Full analysis level: {full['combined_risk_level']}")


print("\n=== 4. ML Fraud Model Unit Test ===")
from ml.fraud_model import predict_fraud, extract_features, load_model

features = extract_features(normalized)
check(len(features) == 10, f"Extracted {len(features)} features")
check("gst_bank_ratio" in features, f"gst_bank_ratio={features.get('gst_bank_ratio', 'MISSING'):.4f}")
check("purchase_sales_ratio" in features, f"purchase_sales_ratio={features.get('purchase_sales_ratio', 'MISSING'):.4f}")

ml_result = predict_fraud(normalized)
check("fraud_probability" in ml_result, f"Fraud prob: {ml_result['fraud_probability']}")
check("prediction" in ml_result, f"Prediction: {ml_result['prediction']}")
check("ml_risk_level" in ml_result, f"ML risk: {ml_result['ml_risk_level']}")
check(ml_result["prediction"] in ("LEGITIMATE", "FRAUDULENT"), "Valid prediction")
check(0 <= ml_result["fraud_probability"] <= 1, "Probability in [0,1]")
check(len(ml_result.get("top_features", [])) > 0, f"Top features: {len(ml_result.get('top_features', []))}")


# ── API Integration Tests ────────────────────────────────────────────

print("\n=== 5. Fraud Detection API Test ===")

# Find an application with parsed documents
try:
    resp = requests.get(f"{API}/applications/")
    apps = resp.json().get("applications", [])
    if apps:
        APP_ID = apps[0]["application_id"]
        print(f"  INFO  Using application: {APP_ID}")
except Exception as e:
    print(f"  SKIP  Could not connect to API: {e}")
    APP_ID = None

if APP_ID:
    try:
        resp = requests.post(f"{API}/fraud/run-verification/{APP_ID}", timeout=30)
        check(resp.status_code == 200, f"Fraud API returns 200 (got {resp.status_code})")
        data = resp.json()
        check("combined_fraud_score" in data, f"Combined score: {data.get('combined_fraud_score')}")
        check("overall_risk_level" in data, f"Overall risk: {data.get('overall_risk_level')}")
        check("cross_verification" in data, "Has cross_verification section")
        check("circular_trading" in data, "Has circular_trading section")
        check("ml_prediction" in data, "Has ml_prediction section")
        check("weight_breakdown" in data, "Has weight_breakdown section")
        check(data.get("status") == "verification_complete", "Status is verification_complete")
        check(data.get("total_flags", 0) >= 0, f"Total flags: {data.get('total_flags')}")
    except requests.exceptions.ConnectionError:
        print("  SKIP  Backend not running — skipping API tests")
    except Exception as e:
        fail(f"Fraud API error: {e}")


print("\n=== 6. Scoring API Test ===")

if APP_ID:
    try:
        resp = requests.post(f"{API}/scoring/calculate-score?application_id={APP_ID}", timeout=30)
        check(resp.status_code == 200, f"Scoring API returns 200 (got {resp.status_code})")
        data = resp.json()
        check("final_credit_score" in data, f"Credit score: {data.get('final_credit_score')}")
        check("decision" in data, f"Decision: {data.get('decision')}")
        check("sub_scores" in data, "Has sub_scores")
        check("explanations" in data, "Has explanations")
        check("risk_grade" in data, f"Risk grade: {data.get('risk_grade')}")
        check(data["decision"] in ("APPROVE", "CONDITIONAL_APPROVE", "REJECT"), "Valid decision")
        check(0 <= data["final_credit_score"] <= 100, "Score in [0,100]")
    except requests.exceptions.ConnectionError:
        print("  SKIP  Backend not running — skipping API tests")
    except Exception as e:
        fail(f"Scoring API error: {e}")
else:
    print("  SKIP  No application found — skipping API tests")


# ── Summary ──────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Total: {passed + failed} | PASSED: {passed} | FAILED: {failed}")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"SOME TESTS FAILED ({failed})")
print(f"{'='*50}\n")

sys.exit(0 if failed == 0 else 1)
