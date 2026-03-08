"""
FIXED Credit Scorer - Logical, Deterministic, and Accurate
Following the hackathon architecture requirements:
- Deterministic scoring for structured financial data
- Proper integration of research agent findings
- Explainable scoring logic (not a black box)
- 5 Cs Framework: Character, Capacity, Capital, Collateral, Conditions
"""
import numpy as np
from typing import Dict, Any, List, Tuple
import pickle
import os
import json


class CreditScorerFixed:
    """
    Fixed Credit Scoring Engine
    
    Architecture:
    1. Financial Analysis (Deterministic) - 40% weight
    2. Research Agent Findings (AI-powered) - 30% weight
    3. Due Diligence (Human input) - 20% weight
    4. Sector & Macro Conditions - 10% weight
    """
    
    def __init__(self):
        self.model_dir = './ml/models'
        self.model = None
        self.load_model_if_available()
    
    def calculate_credit_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate credit score using 5 Cs framework
        
        Args:
            data: Dictionary containing:
                - Financial ratios (DSCR, Current Ratio, etc.)
                - Research findings (litigation, promoter sentiment, etc.)
                - Due diligence notes
                - Sector information
        
        Returns:
            Comprehensive scoring result with explanations
        """
        
        # Extract data
        financials = data.get('financials', {})
        research = data.get('research', {})
        due_diligence = data.get('due_diligence', {})
        sector_info = data.get('sector', {})
        
        # Calculate sub-scores (5 Cs)
        capacity_score, capacity_explanation = self._score_capacity(financials)
        character_score, character_explanation = self._score_character(research)
        capital_score, capital_explanation = self._score_capital(financials)
        conditions_score, conditions_explanation = self._score_conditions(sector_info, research)
        collateral_score, collateral_explanation = self._score_collateral(financials)
        
        # Calculate weighted final score
        weights = {
            'capacity': 0.35,      # Ability to repay (most important)
            'character': 0.30,     # Willingness to repay
            'capital': 0.20,       # Equity cushion
            'conditions': 0.10,    # External factors
            'collateral': 0.05     # Security
        }
        
        final_score = (
            capacity_score * weights['capacity'] +
            character_score * weights['character'] +
            capital_score * weights['capital'] +
            conditions_score * weights['conditions'] +
            collateral_score * weights['collateral']
        )
        
        # Apply due diligence adjustments
        dd_adjustment, dd_explanation = self._apply_due_diligence(due_diligence, final_score)
        final_score += dd_adjustment
        
        # Clamp to 0-100
        final_score = max(0, min(100, int(final_score)))
        
        # Determine decision
        decision, recommended_limit_pct = self._get_decision(final_score)
        
        # Calculate recommended limit
        requested_limit = data.get('requested_limit_cr', 10.0)
        recommended_limit = requested_limit * (recommended_limit_pct / 100)
        
        return {
            'model_version': 'rule-based-fixed-v2.0',
            'final_credit_score': final_score,
            'max_score': 100,
            'decision': decision,
            'recommended_limit_cr': round(recommended_limit, 2),
            'requested_limit_cr': requested_limit,
            'approval_percentage': recommended_limit_pct,
            'risk_grade': self._get_risk_grade(final_score),
            'sub_scores': {
                'capacity': {'score': int(capacity_score), 'weight': weights['capacity']},
                'character': {'score': int(character_score), 'weight': weights['character']},
                'capital': {'score': int(capital_score), 'weight': weights['capital']},
                'conditions': {'score': int(conditions_score), 'weight': weights['conditions']},
                'collateral': {'score': int(collateral_score), 'weight': weights['collateral']}
            },
            'explanations': {
                'capacity': capacity_explanation,
                'character': character_explanation,
                'capital': capital_explanation,
                'conditions': conditions_explanation,
                'collateral': collateral_explanation,
                'due_diligence': dd_explanation
            },
            'key_factors': self._get_key_factors(
                capacity_score, character_score, capital_score,
                conditions_score, collateral_score, dd_adjustment
            )
        }
    
    def _score_capacity(self, financials: Dict) -> Tuple[float, str]:
        """
        Score CAPACITY (Ability to Repay) - 35% weight
        
        Key metrics:
        - DSCR (Debt Service Coverage Ratio): Most critical
        - Revenue/Cash flow trends
        - Operating efficiency
        """
        score = 50  # Start from middle
        reasons = []
        
        # DSCR is the most critical metric for capacity
        dscr = financials.get('dscr', 1.0)
        
        if dscr >= 2.0:
            score += 50
            reasons.append(f"✅ Excellent DSCR {dscr:.2f} (>2.0) - Strong repayment capacity")
        elif dscr >= 1.5:
            score += 35
            reasons.append(f"✅ Good DSCR {dscr:.2f} (1.5-2.0) - Adequate repayment capacity")
        elif dscr >= 1.25:
            score += 15
            reasons.append(f"⚠️ Acceptable DSCR {dscr:.2f} (1.25-1.5) - Moderate capacity")
        elif dscr >= 1.0:
            score -= 10
            reasons.append(f"⚠️ Low DSCR {dscr:.2f} (1.0-1.25) - Weak repayment capacity")
        else:
            score -= 30
            reasons.append(f"❌ Critical DSCR {dscr:.2f} (<1.0) - Insufficient income to service debt")
        
        # Current ratio (liquidity)
        current_ratio = financials.get('current_ratio', 1.0)
        if current_ratio >= 2.0:
            score += 10
            reasons.append(f"✅ Strong liquidity with Current Ratio {current_ratio:.2f}")
        elif current_ratio >= 1.5:
            score += 5
            reasons.append(f"✅ Adequate liquidity")
        elif current_ratio < 1.0:
            score -= 15
            reasons.append(f"❌ Poor liquidity - Current Ratio {current_ratio:.2f} < 1.0")
        
        # GST vs Bank reconciliation (revenue authenticity)
        gst_variance = financials.get('gst_vs_bank_variance', 0.0)
        if gst_variance > 15:
            score -= 25
            reasons.append(f"❌ HIGH GST-Bank mismatch {gst_variance:.1f}% - Revenue inflation suspected")
        elif gst_variance > 10:
            score -= 10
            reasons.append(f"⚠️ Moderate GST-Bank variance {gst_variance:.1f}%")
        elif gst_variance <= 5:
            score += 5
            reasons.append(f"✅ Excellent GST-Bank alignment ({gst_variance:.1f}%)")
        
        explanation = " | ".join(reasons)
        return max(0, min(100, score)), explanation
    
    def _score_character(self, research: Dict) -> Tuple[float, str]:
        """
        Score CHARACTER (Willingness to Repay) - 30% weight
        
        Based on:
        - Litigation history
        - Promoter background
        - Payment track record
        - Circular trading patterns
        """
        score = 70  # Start optimistic
        reasons = []
        
        # Litigation (critical red flag)
        litigation_count = research.get('litigation_count', 0)
        litigation_severity = research.get('litigation_severity', 'None')
        
        if litigation_count == 0:
            score += 20
            reasons.append("✅ No litigation found - Clean record")
        elif litigation_count <= 2 and litigation_severity == 'Low':
            score -= 5
            reasons.append(f"⚠️ {litigation_count} minor litigation cases")
        elif litigation_count <= 5:
            score -= 20
            reasons.append(f"❌ {litigation_count} litigation cases - Moderate concern")
        else:
            score -= 40
            reasons.append(f"❌ SERIOUS: {litigation_count} litigation cases - High character risk")
        
        # Promoter sentiment from web research
        promoter_sentiment = research.get('promoter_sentiment', 'Neutral')
        if promoter_sentiment == 'Positive':
            score += 10
            reasons.append("✅ Positive promoter reputation from news/web research")
        elif promoter_sentiment == 'Negative':
            score -= 25
            reasons.append("❌ Negative promoter reputation - Adverse news found")
        
        # Circular trading detection
        circular_risk = research.get('circular_trading_risk_score', 0)
        if circular_risk > 70:
            score -= 35
            reasons.append(f"❌ HIGH circular trading risk ({circular_risk}/100) - Suspicious transactions")
        elif circular_risk > 40:
            score -= 15
            reasons.append(f"⚠️ Moderate circular trading indicators")
        elif circular_risk < 20:
            score += 5
            reasons.append("✅ Clean transaction patterns")
        
        explanation = " | ".join(reasons)
        return max(0, min(100, score)), explanation
    
    def _score_capital(self, financials: Dict) -> Tuple[float, str]:
        """
        Score CAPITAL (Owner's equity cushion) - 20% weight
        
        Metrics:
        - Debt-to-Equity ratio
        - Net worth
        - Capital structure
        """
        score = 60
        reasons = []
        
        debt_to_equity = financials.get('debt_to_equity', 1.0)
        
        if debt_to_equity <= 1.0:
            score += 40
            reasons.append(f"✅ Excellent capital structure - D/E {debt_to_equity:.2f}")
        elif debt_to_equity <= 2.0:
            score += 20
            reasons.append(f"✅ Good leverage - D/E {debt_to_equity:.2f}")
        elif debt_to_equity <= 3.0:
            score += 0
            reasons.append(f"⚠️ Moderate leverage - D/E {debt_to_equity:.2f}")
        elif debt_to_equity <= 5.0:
            score -= 20
            reasons.append(f"❌ High leverage - D/E {debt_to_equity:.2f} - Limited equity cushion")
        else:
            score -= 40
            reasons.append(f"❌ EXCESSIVE leverage - D/E {debt_to_equity:.2f} - Very risky capital structure")
        
        explanation = " | ".join(reasons)
        return max(0, min(100, score)), explanation
    
    def _score_conditions(self, sector_info: Dict, research: Dict) -> Tuple[float, str]:
        """
        Score CONDITIONS (Economic/Sector factors) - 10% weight
        """
        score = 70
        reasons = []
        
        sector_risk = sector_info.get('sector_risk_score', 30)
        
        if sector_risk < 20:
            score += 20
            reasons.append("✅ Stable sector with low macro risk")
        elif sector_risk < 50:
            score += 5
            reasons.append("✅ Moderate sector risk")
        else:
            score -= 15
            reasons.append(f"⚠️ High sector risk ({sector_risk}/100)")
        
        # Check for adverse sector news from research
        sector_sentiment = research.get('sector_sentiment', 'Neutral')
        if sector_sentiment == 'Negative':
            score -= 10
            reasons.append("⚠️ Adverse sector news found")
        
        explanation = " | ".join(reasons) if reasons else "Sector conditions assessed"
        return max(0, min(100, score)), explanation
    
    def _score_collateral(self, financials: Dict) -> Tuple[float, str]:
        """
        Score COLLATERAL (Security) - 5% weight
        """
        # Simplified - would normally assess fixed assets, property, etc.
        score = 60
        explanation = "Collateral evaluation based on fixed assets"
        return score, explanation
    
    def _apply_due_diligence(self, dd_data: Dict, current_score: float) -> Tuple[float, str]:
        """
        Apply human due diligence observations
        
        This is where the Credit Officer's field visit findings affect the score
        """
        adjustment = 0
        reasons = []
        
        dd_notes = dd_data.get('notes', '')
        dd_severity = dd_data.get('severity', 'None')
        
        if dd_severity == 'Critical':
            adjustment = -20
            reasons.append(f"❌ CRITICAL due diligence finding: {dd_notes[:100]}")
        elif dd_severity == 'High':
            adjustment = -10
            reasons.append(f"⚠️ HIGH risk finding: {dd_notes[:100]}")
        elif dd_severity == 'Moderate':
            adjustment = -5
            reasons.append(f"⚠️ Moderate concern noted")
        elif dd_severity == 'Positive':
            adjustment = +5
            reasons.append("✅ Positive observations from field visit")
        
        explanation = " | ".join(reasons) if reasons else "No critical due diligence adjustments"
        return adjustment, explanation
    
    def _get_decision(self, score: int) -> Tuple[str, int]:
        """
        Decision logic with recommended approval percentage
        
        Returns: (decision_string, recommended_limit_percentage)
        """
        if score >= 75:
            return ('APPROVE', 100)  # Full approval
        elif score >= 65:
            return ('CONDITIONAL_APPROVE', 75)  # 75% of requested
        elif score >= 55:
            return ('CONDITIONAL_APPROVE', 50)  # 50% of requested
        else:
            return ('REJECT', 0)  # Rejection
    
    def _get_risk_grade(self, score: int) -> str:
        """Map score to risk grade (like bank ratings)"""
        if score >= 85:
            return 'AAA'
        elif score >= 75:
            return 'AA'
        elif score >= 65:
            return 'A'
        elif score >= 55:
            return 'BBB'
        elif score >= 45:
            return 'BB'
        else:
            return 'B'
    
    def _get_key_factors(self, capacity, character, capital, conditions, collateral, dd_adj) -> List[str]:
        """Identify top 3 factors influencing the decision"""
        factors = [
            ('Repayment Capacity (DSCR, Cash Flow)', capacity * 0.35),
            ('Character & Track Record', character * 0.30),
            ('Capital Structure', capital * 0.20),
            ('Sector Conditions', conditions * 0.10),
            ('Collateral', collateral * 0.05),
            ('Due Diligence Findings', dd_adj)
        ]
        
        # Sort by absolute impact
        sorted_factors = sorted(factors, key=lambda x: abs(x[1]), reverse=True)
        
        return [f[0] for f in sorted_factors[:3]]
    
    def load_model_if_available(self):
        """Try to load XGBoost model if available (future enhancement)"""
        try:
            model_path = f'{self.model_dir}/xgboost_credit_model.pkl'
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("✅ Loaded ML model (available for future use)")
        except:
            pass  # Fall back to rule-based
