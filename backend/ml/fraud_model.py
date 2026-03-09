"""
ML Fraud Detection Model - Train and save a RandomForest fraud classifier.

Features derived from financial data cross-verification:
  1. gst_bank_ratio        – GST Sales / Bank Inflows
  2. purchase_sales_ratio   – GST Purchases / GST Sales
  3. outflow_inflow_ratio   – Bank Outflows / Bank Inflows
  4. debt_equity_ratio      – Total Debt / Total Equity
  5. revenue_variance       – |GST Sales - AR Revenue| / AR Revenue
  6. bounced_check_rate     – Bounced Cheques / 12 (monthly)
  7. overdraft_rate         – Overdraft Instances / 12
  8. monthly_variability    – Std/Mean of monthly bank inflows
  9. cash_retention_pct     – (Inflows - Outflows) / Inflows
  10. gst_mismatch_ratio    – |GSTR1 - GSTR3B| / GSTR1

Target: 0 = Legitimate, 1 = Fraudulent
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "fraud_model.pkl"
FEATURE_NAMES = [
    "gst_bank_ratio",
    "purchase_sales_ratio",
    "outflow_inflow_ratio",
    "debt_equity_ratio",
    "revenue_variance",
    "bounced_check_rate",
    "overdraft_rate",
    "monthly_variability",
    "cash_retention_pct",
    "gst_mismatch_ratio",
]


def _generate_synthetic_dataset(n_samples: int = 2000, fraud_rate: float = 0.25, seed: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic financial data for training."""
    rng = np.random.default_rng(seed)

    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    def _legit_rows(n):
        return pd.DataFrame({
            "gst_bank_ratio": rng.normal(1.0, 0.05, n).clip(0.8, 1.2),
            "purchase_sales_ratio": rng.normal(0.55, 0.12, n).clip(0.2, 0.85),
            "outflow_inflow_ratio": rng.normal(0.75, 0.08, n).clip(0.5, 0.92),
            "debt_equity_ratio": rng.exponential(0.8, n).clip(0, 4),
            "revenue_variance": rng.exponential(0.03, n).clip(0, 0.15),
            "bounced_check_rate": rng.poisson(0.3, n).clip(0, 3) / 12,
            "overdraft_rate": rng.poisson(0.2, n).clip(0, 2) / 12,
            "monthly_variability": rng.normal(0.2, 0.08, n).clip(0.05, 0.5),
            "cash_retention_pct": rng.normal(0.25, 0.08, n).clip(0.08, 0.5),
            "gst_mismatch_ratio": rng.exponential(0.02, n).clip(0, 0.1),
            "is_fraud": 0,
        })

    def _fraud_rows(n):
        return pd.DataFrame({
            # Fraudulent companies show GST ≠ bank
            "gst_bank_ratio": rng.choice(
                [rng.normal(0.6, 0.1, n), rng.normal(1.5, 0.15, n)],
            ).clip(0.3, 2.5),
            # Round-tripping: purchases ≈ sales
            "purchase_sales_ratio": rng.normal(0.95, 0.08, n).clip(0.8, 1.15),
            # Minimal retention
            "outflow_inflow_ratio": rng.normal(0.96, 0.03, n).clip(0.88, 1.05),
            "debt_equity_ratio": rng.exponential(2.5, n).clip(0.5, 15),
            "revenue_variance": rng.exponential(0.15, n).clip(0.05, 0.8),
            "bounced_check_rate": rng.poisson(2, n).clip(0, 10) / 12,
            "overdraft_rate": rng.poisson(1.5, n).clip(0, 8) / 12,
            "monthly_variability": rng.normal(0.55, 0.15, n).clip(0.3, 1.0),
            "cash_retention_pct": rng.normal(0.04, 0.03, n).clip(-0.1, 0.12),
            "gst_mismatch_ratio": rng.exponential(0.12, n).clip(0.03, 0.6),
            "is_fraud": 1,
        })

    df = pd.concat([_legit_rows(n_legit), _fraud_rows(n_fraud)], ignore_index=True)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def train_and_save(n_samples: int = 2000):
    """Train RandomForest on synthetic data and save as .pkl."""
    print("[ML] Generating synthetic dataset...")
    df = _generate_synthetic_dataset(n_samples)

    X = df[FEATURE_NAMES].values
    y = df["is_fraud"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    print("[ML] --- Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraudulent"]))
    print(f"[ML] ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    # Feature importance
    importances = dict(zip(FEATURE_NAMES, clf.feature_importances_.tolist()))
    print("[ML] Feature importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.4f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "features": FEATURE_NAMES, "importances": importances}, MODEL_PATH)
    print(f"[ML] Model saved to {MODEL_PATH}")
    return clf


def load_model():
    """Load the trained model from disk."""
    if not MODEL_PATH.exists():
        print("[ML] No model found — training now...")
        train_and_save()
    return joblib.load(MODEL_PATH)


def extract_features(normalized_data: dict) -> dict:
    """
    Extract ML features from the normalized financial data produced by DataNormalizer.
    Returns a dict of feature_name -> float value.
    """
    gst = normalized_data.get("gst", {})
    bank = normalized_data.get("bank", {})
    annual = normalized_data.get("annual_report", {})

    gst_sales = gst.get("sales_cr", 0) or 0
    gst_3b = gst.get("sales_3b_cr", 0) or 0
    gst_purchases = gst.get("purchases_cr", 0) or 0
    bank_in = bank.get("total_inflows_cr", 0) or 0
    bank_out = bank.get("total_outflows_cr", 0) or 0
    ar_revenue = annual.get("revenue_cr", 0) or 0
    ar_debt = annual.get("total_debt_cr", 0) or 0
    ar_equity = annual.get("total_equity_cr", 0) or 0

    def safe_div(a, b, default=0.0):
        return a / b if b > 0 else default

    features = {
        "gst_bank_ratio": safe_div(gst_sales, bank_in, 1.0),
        "purchase_sales_ratio": safe_div(gst_purchases, gst_sales, 0.5),
        "outflow_inflow_ratio": safe_div(bank_out, bank_in, 0.75),
        "debt_equity_ratio": safe_div(ar_debt, ar_equity, 1.0),
        "revenue_variance": safe_div(abs(gst_sales - ar_revenue), ar_revenue, 0.0) if ar_revenue > 0 else 0.0,
        "bounced_check_rate": safe_div(bank.get("bounced_checks", 0) or 0, 12),
        "overdraft_rate": safe_div(bank.get("overdraft_instances", 0) or 0, 12),
        "monthly_variability": bank.get("monthly_variability", 0.2) or 0.2,
        "cash_retention_pct": safe_div(bank_in - bank_out, bank_in, 0.25) if bank_in > 0 else 0.25,
        "gst_mismatch_ratio": safe_div(abs(gst_sales - gst_3b), gst_sales, 0.0) if gst_sales > 0 else 0.0,
    }
    return features


def predict_fraud(normalized_data: dict) -> dict:
    """
    Run the ML model on normalized financial data.
    Returns fraud probability, prediction, and feature contributions.
    """
    bundle = load_model()
    model = bundle["model"]
    feature_names = bundle["features"]
    importances = bundle.get("importances", {})

    features = extract_features(normalized_data)
    X = np.array([[features[f] for f in feature_names]])

    proba = model.predict_proba(X)[0]
    fraud_prob = float(proba[1])
    prediction = int(model.predict(X)[0])

    # ML risk level
    if fraud_prob >= 0.7:
        ml_risk = "HIGH"
    elif fraud_prob >= 0.4:
        ml_risk = "MEDIUM"
    else:
        ml_risk = "LOW"

    # Top contributing features
    feature_contributions = []
    for fname in feature_names:
        val = features[fname]
        imp = importances.get(fname, 0)
        feature_contributions.append({
            "feature": fname,
            "value": round(val, 4),
            "importance": round(imp, 4),
        })
    feature_contributions.sort(key=lambda x: -x["importance"])

    return {
        "fraud_probability": round(fraud_prob, 4),
        "prediction": "FRAUDULENT" if prediction == 1 else "LEGITIMATE",
        "ml_risk_level": ml_risk,
        "ml_score": round(fraud_prob * 100, 1),
        "feature_values": features,
        "top_features": feature_contributions[:5],
    }


if __name__ == "__main__":
    train_and_save()
