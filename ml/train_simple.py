"""
Simple training script using existing synthetic data
Trains XGBoost with the exact features needed for credit scoring
"""
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb
import shap


def create_training_data(n_samples=5000):
    """Create synthetic but realistic credit data"""
    
    print(f"\nCreating {n_samples} training samples...")
    
    np.random.seed(42)
    
    # Financial metrics
    dscr = np.random.normal(1.5, 0.5, n_samples).clip(0.3, 4.0)
    current_ratio = np.random.normal(1.6, 0.4, n_samples).clip(0.5, 3.5)
    debt_to_equity = np.random.normal(1.2, 0.6, n_samples).clip(0.1, 4.0)
    
    # Income (for scaling)
    income = np.random.normal(50, 20, n_samples).clip(10, 200)
    
    # Risk factors
    gst_vs_bank_variance = np.abs(np.random.normal(3, 4, n_samples)).clip(0, 25)
    circular_trading_risk_score = np.random.exponential(15, n_samples).clip(0, 60)
    litigation_count = np.random.choice([0, 0, 0, 1, 2], size=n_samples)
    
    # Sector and promoter (categorical encoded)
    sector_encoded = np.random.randint(0, 8, n_samples)
    promoter_sentiment_encoded = np.random.choice([0, 1, 2], size=n_samples, p=[0.4, 0.4, 0.2])
    
    # Due diligence score (can be positive or negative)
    due_diligence_score = np.random.normal(0, 2, n_samples).clip(-8, 5)
    sector_risk_score = np.random.uniform(20, 60, n_samples)
    
    # Create target: Default probability based on features
    # Lower DSCR, lower current ratio, higher debt = higher default risk
    risk_score = (
        (2.0 - dscr) * 25 +  # Lower DSCR = higher risk
        (2.0 - current_ratio) * 15 +  # Lower current ratio = higher risk
        (debt_to_equity - 1.0) * 20 +  # Higher debt = higher risk
        gst_vs_bank_variance * 1.5 +  # Variance = risk
        circular_trading_risk_score * 0.8 +  # Circular trading = risk
        litigation_count * 15 +  # Litigation = risk
        promoter_sentiment_encoded * 10 +  # Negative sentiment = risk
        sector_risk_score * 0.3 +  # Sector risk
        (-due_diligence_score) * 3  # Negative DD score = risk
    )
    
    # Normalize and create binary target
    risk_score_normalized = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
    default = (risk_score_normalized > 0.55).astype(int)  # ~40-45% default rate
    
    # Create DataFrame with exact feature names
    df = pd.DataFrame({
        'income': income,
        'dscr': dscr,
        'current_ratio': current_ratio,
        'debt_to_equity': debt_to_equity,
        'gst_vs_bank_variance': gst_vs_bank_variance,
        'circular_trading_risk_score': circular_trading_risk_score,
        'litigation_count': litigation_count,
        'sector_risk_score': sector_risk_score,
        'due_diligence_score': due_diligence_score,
        'sector_encoded': sector_encoded,
        'promoter_sentiment_encoded': promoter_sentiment_encoded,
        'default': default
    })
    
    print(f"Default rate: {default.mean()*100:.1f}%")
    
    return df


def train_model():
    """Train XGBoost model"""
    
    print("="*70)
    print("TRAINING XGBOOST CREDIT MODEL")
    print("="*70)
    
    # Create training data
    df = create_training_data(n_samples=10000)
    
    # Features and target
    feature_cols = [
        'income', 'dscr', 'current_ratio', 'debt_to_equity',
        'gst_vs_bank_variance', 'circular_trading_risk_score',
        'litigation_count', 'sector_risk_score', 'due_diligence_score',
        'sector_encoded', 'promoter_sentiment_encoded'
    ]
    
    X = df[feature_cols]
    y = df['default']
    
    print(f"\nFeatures ({len(feature_cols)}): {feature_cols}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")
    
    # Train XGBoost
    print("\nTraining XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = (y_pred == y_test).mean()
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print("\n" + "="*70)
    print("MODEL PERFORMANCE")
    print("="*70)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC AUC: {roc_auc:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Default', 'Default']))
    
    # Test with example cases
    print("\n" + "="*70)
    print("VERIFICATION TEST")
    print("="*70)
    
    # Excellent company
    excellent = pd.DataFrame([{
        'income': 100, 'dscr': 3.0, 'current_ratio': 2.5, 'debt_to_equity': 0.3,
        'gst_vs_bank_variance': 2, 'circular_trading_risk_score': 5,
        'litigation_count': 0, 'sector_risk_score': 25, 'due_diligence_score': 2,
        'sector_encoded': 3, 'promoter_sentiment_encoded': 0
    }])
    
    # Poor company
    poor = pd.DataFrame([{
        'income': 20, 'dscr': 0.7, 'current_ratio': 0.8, 'debt_to_equity': 3.5,
        'gst_vs_bank_variance': 15, 'circular_trading_risk_score': 45,
        'litigation_count': 2, 'sector_risk_score': 55, 'due_diligence_score': -5,
        'sector_encoded': 7, 'promoter_sentiment_encoded': 2
    }])
    
    excellent_proba = model.predict_proba(excellent)[0][0]  # Prob of NO default
    poor_proba = model.predict_proba(poor)[0][0]
    
    print(f"\nExcellent Company:")
    print(f"  Prob No Default: {excellent_proba:.2f}")
    print(f"  Credit Score: {int(excellent_proba * 100)}/100")
    
    print(f"\nPoor Company:")
    print(f"  Prob No Default: {poor_proba:.2f}")
    print(f"  Credit Score: {int(poor_proba * 100)}/100")
    
    if excellent_proba > poor_proba:
        print("\n✓ VERIFICATION PASSED: Excellent scores higher than poor")
    else:
        print("\nX VERIFICATION FAILED: Scores are inverted!")
    
    # SHAP
    print("\nComputing SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    
    # Save everything
    print("\nSaving model...")
    model_dir = Path('backend/ml/models')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    with open(model_dir / 'xgboost_credit_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open(model_dir / 'shap_explainer.pkl', 'wb') as f:
        pickle.dump(explainer, f)
    
    with open(model_dir / 'feature_names.json', 'w') as f:
        json.dump(feature_cols, f, indent=2)
    
    with open(model_dir / 'label_encoders.pkl', 'wb') as f:
        pickle.dump({}, f)
    
    print(f"✓ Saved to {model_dir}")
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print(f"Accuracy: {accuracy:.4f} | ROC AUC: {roc_auc:.4f}")
    print("\nRestart backend to use the new model.")
    
    return model


if __name__ == "__main__":
    train_model()
