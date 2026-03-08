"""
Credit Scorer - ML-based credit scoring with XGBoost
"""
import numpy as np
from typing import Dict, Any, List, Optional
import pickle
import os
import json


class CreditScorer:
    """
    Credit scoring engine using XGBoost
    Features: Financial ratios, research penalties, sector risk, etc.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.shap_explainer = None
        self.label_encoders = None
        self.feature_names = None
        
        self.model_dir = model_path or './ml/models'
        self.model_path = f'{self.model_dir}/xgboost_credit_model.pkl'
        
        # Feature definitions (MUST match training exactly)
        # Will be loaded from feature_names.json
        self.features = None
        
        # Auto-load model if available
        self.load_model()
    
    def calculate_credit_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate credit score
        """
        
        # Prepare feature vector
        feature_vector = self._prepare_features(features)
        
        # For demo, use rule-based scoring
        # In production, load and use trained XGBoost model
        if self.model is None:
            score = self._rule_based_scoring(feature_vector, features)
        else:
            score = self._ml_based_scoring(feature_vector)
        
        # Determine decision
        decision = self._get_decision(score)
        recommended_limit = self._calculate_recommended_limit(
            score, 
            features.get('requested_limit_cr', 10.0)
        )
        
        return {
            'model_version': 'xgboost-v1.4',
            'final_credit_score': score,
            'max_score': 100,
            'decision': decision,
            'recommended_limit_cr': recommended_limit,
            'risk_grade': self._get_risk_grade(score)
        }
    
    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare feature vector for model"""
        
        if self.features is None:
            raise ValueError("Features not loaded! Model initialization failed.")
        
        # Feature mappings for compatibility
        feature_mappings = {
            'litigation_count': 'litigation_penalty',  # penalty is negative count
            'due_diligence_score': 'due_diligence_penalty',
            'income': 'requested_limit_cr',  # Use loan amount as proxy for income
            'promoter_sentiment_encoded': 'promoter_risk_score',  # 0=positive, 1=neutral, 2=negative
            'sector_encoded': 'sector_risk_score'  # Use risk score as proxy
        }
        
        feature_values = []
        for feature_name in self.features:
            # Try to get value directly
            if feature_name in features:
                value = features.get(feature_name, 0.0)
            # Try mapped name
            elif feature_name in feature_mappings:
                mapped_name = feature_mappings[feature_name]
                value = features.get(mapped_name, 0.0)
                
                # Special handling for mapped features
                if feature_name == 'litigation_count':
                    # Penalty is negative, convert to count
                    value = abs(value) if value < 0 else value
                elif feature_name == 'income':
                    # Loan amount as proxy for income (assume DSCR for scaling)
                    dscr = features.get('dscr', 1.0)
                    value = value * dscr * 10  # Scale up
                elif feature_name == 'promoter_sentiment_encoded':
                    # Map risk score to sentiment: 0-20=positive(0), 20-50=neutral(1), >50=negative(2)
                    if value < 20:
                        value = 0
                    elif value < 50:
                        value = 1
                    else:
                        value = 2
                elif feature_name == 'sector_encoded':
                    # Normalize sector risk to 0-9 range
                    value = int(value / 10) % 10
            else:
                # Default value
                value = 0.0
            
            feature_values.append(float(value))
        
        return np.array(feature_values).reshape(1, -1)
    
    def _rule_based_scoring(self, feature_vector: np.ndarray, features: Dict) -> int:
        """
        Rule-based scoring logic (used when ML model not available)
        """
        
        base_score = 70  # Start with neutral score
        
        # DSCR impact (very important)
        dscr = features.get('dscr', 1.0)
        if dscr < 1.0:
            base_score -= 20
        elif dscr < 1.25:
            base_score -= 10
        elif dscr >= 1.5:
            base_score += 10
        
        # Current Ratio impact
        current_ratio = features.get('current_ratio', 1.0)
        if current_ratio < 1.0:
            base_score -= 10
        elif current_ratio >= 1.5:
            base_score += 5
        
        # Debt to Equity impact
        debt_to_equity = features.get('debt_to_equity', 1.0)
        if debt_to_equity > 3.0:
            base_score -= 15
        elif debt_to_equity > 2.0:
            base_score -= 5
        elif debt_to_equity < 1.0:
            base_score += 5
        
        # GST vs Bank variance
        variance = features.get('gst_vs_bank_variance', 0.0)
        if variance > 10:
            base_score -= 15
        elif variance > 5:
            base_score -= 5
        
        # Circular trading risk
        ct_risk = features.get('circular_trading_risk_score', 0)
        base_score -= ct_risk
        
        # Litigation penalty
        litigation_penalty = features.get('litigation_penalty', 0)
        base_score += litigation_penalty  # Already negative
        
        # Promoter risk
        promoter_risk = features.get('promoter_risk_score', 0)
        base_score += promoter_risk
        
        # Sector risk
        sector_risk = features.get('sector_risk_score', 0)
        base_score -= sector_risk
        
        # Due diligence penalty
        dd_penalty = features.get('due_diligence_penalty', 0)
        base_score += dd_penalty  # Already negative
        
        # Clamp to 0-100
        return max(0, min(100, base_score))
    
    def _ml_based_scoring(self, feature_vector: np.ndarray) -> int:
        """ML-based scoring using trained XGBoost model"""
        
        try:
            # Get probability of default
            prediction_proba = self.model.predict_proba(feature_vector)[0]
            prob_no_default = prediction_proba[0]
            
            # Convert to credit score (higher prob of no-default = higher score)
            score = int(prob_no_default * 100)
            
            return max(0, min(100, score))
        
        except Exception as e:
            print(f"ML prediction error: {e}. Falling back to rule-based.")
            return None
    
    def _get_decision(self, score: int) -> str:
        """Determine decision based on score"""
        
        if score >= 75:
            return 'APPROVE'
        elif score >= 60:
            return 'CONDITIONAL_APPROVE'
        else:
            return 'REJECT'
    
    def _calculate_recommended_limit(self, score: int, requested_limit: float) -> float:
        """Calculate recommended loan limit based on score"""
        
        if score >= 75:
            return requested_limit  # Full approval
        elif score >= 60:
            return requested_limit * 0.6  # 60% of requested
        else:
            return 0.0  # Reject
    
    def _get_risk_grade(self, score: int) -> str:
        """Map score to risk grade"""
        
        if score >= 80:
            return 'AAA'
        elif score >= 70:
            return 'AA'
        elif score >= 60:
            return 'A'
        elif score >= 50:
            return 'BBB'
        elif score >= 40:
            return 'BB'
        else:
            return 'B'
    
    def load_model(self):
        """Load trained XGBoost model and SHAP explainer"""
        
        try:
            # Load feature names FIRST (critical for correct predictions)
            features_path = f'{self.model_dir}/feature_names.json'
            if os.path.exists(features_path):
                with open(features_path, 'r') as f:
                    self.feature_names = json.load(f)
                    self.features = self.feature_names  # Use training features
                print(f"✅ Loaded {len(self.feature_names)} feature names")
            else:
                # Fallback to rule-based features
                self.features = [
                    'dscr', 'current_ratio', 'debt_to_equity',
                    'gst_vs_bank_variance', 'circular_trading_risk_score',
                    'sector_risk_score'
                ]
                print(f"⚠️ Feature names not found, using fallback")
            
            # Load XGBoost model
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"✅ Loaded XGBoost model from {self.model_path}")
            
            # Load SHAP explainer
            explainer_path = f'{self.model_dir}/shap_explainer.pkl'
            if os.path.exists(explainer_path):
                with open(explainer_path, 'rb') as f:
                    self.shap_explainer = pickle.load(f)
                print(f"✅ Loaded SHAP explainer")
            
            # Load label encoders
            encoders_path = f'{self.model_dir}/label_encoders.pkl'
            if os.path.exists(encoders_path):
                with open(encoders_path, 'rb') as f:
                    self.label_encoders = pickle.load(f)
            
        except Exception as e:
            print(f"⚠️ Could not load ML model: {e}. Using rule-based scoring.")
            self.model = None
    
    def get_shap_explanation(self, feature_vector: np.ndarray, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate SHAP-based feature explanations"""
        
        if self.shap_explainer is None or self.model is None:
            # Fallback to rule-based explanations
            return self._rule_based_explanations(features)
        
        try:
            # Compute SHAP values
            shap_values = self.shap_explainer.shap_values(feature_vector)[0]
            
            # Map to feature names with interpretable labels
            feature_map = {
                'dscr': 'Debt Service Coverage (DSCR)',
                'current_ratio': 'Current Ratio',
                'debt_to_equity': 'Debt-to-Equity',
                'gst_vs_bank_variance': 'GST vs Bank Variance',
                'circular_trading_risk_score': 'Circular Trading Risk',
                'litigation_penalty': 'Litigation Impact',
                'promoter_risk_score': 'Promoter Sentiment',
                'sector_risk_score': 'Sector Risk',
                'due_diligence_penalty': 'Due Diligence Notes'
            }
            
            explanations = []
            for i, feature_name in enumerate(self.features):
                shap_value = float(shap_values[i])
                
                explanations.append({
                    'feature': feature_map.get(feature_name, feature_name),
                    'impact_value': round(shap_value, 2),
                    'type': 'POSITIVE' if shap_value > 0 else 'NEGATIVE',
                    'actual_value': features.get(feature_name, 0)
                })
            
            # Sort by absolute impact
            explanations.sort(key=lambda x: abs(x['impact_value']), reverse=True)
            
            return explanations
        
        except Exception as e:
            print(f"SHAP computation error: {e}")
            return self._rule_based_explanations(features)
    
    def _rule_based_explanations(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback rule-based explanations when SHAP unavailable"""
        
        explanations = []
        
        # DSCR impact
        dscr = features.get('dscr', 1.0)
        if dscr < 1.0:
            impact = -20
        elif dscr < 1.25:
            impact = -10
        elif dscr >= 1.5:
            impact = 10
        else:
            impact = 0
        
        explanations.append({
            'feature': 'Debt Service Coverage (DSCR)',
            'impact_value': impact,
            'type': 'POSITIVE' if impact > 0 else 'NEGATIVE',
            'actual_value': dscr
        })
        
        # Add other features similarly...
        variance = features.get('gst_vs_bank_variance', 0)
        if variance > 10:
            explanations.append({
                'feature': 'GST vs Bank Variance',
                'impact_value': -15,
                'type': 'NEGATIVE',
                'actual_value': variance
            })
        
        return explanations
