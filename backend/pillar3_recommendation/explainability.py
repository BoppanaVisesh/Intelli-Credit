"""
Explainability - SHAP-based feature importance and explainability
"""
from typing import Dict, List, Any
import numpy as np


class Explainability:
    """
    Generate SHAP values and explanations for credit decisions
    """
    
    def __init__(self):
        pass
    
    def generate_shap_explanation(
        self,
        features: Dict[str, Any],
        base_score: int,
        final_score: int
    ) -> List[Dict[str, Any]]:
        """
        Generate SHAP-like explanations
        In production: use actual SHAP library with trained model
        """
        
        explanations = []
        
        # DSCR impact
        dscr = features.get('dscr', 1.0)
        if dscr < 1.0:
            explanations.append({
                'feature': 'DSCR < 1.0',
                'impact_value': -18.5,
                'type': 'NEGATIVE'
            })
        elif dscr >= 1.5:
            explanations.append({
                'feature': 'Strong DSCR',
                'impact_value': 10.0,
                'type': 'POSITIVE'
            })
        
        # Litigation
        litigation_penalty = features.get('litigation_penalty', 0)
        if litigation_penalty < 0:
            explanations.append({
                'feature': 'Pending Litigation (eCourts)',
                'impact_value': float(litigation_penalty),
                'type': 'NEGATIVE'
            })
        
        # GST/Bank consistency
        variance = features.get('gst_vs_bank_variance', 0.0)
        if variance < 2.0:
            explanations.append({
                'feature': 'Consistent GST/Bank Inflows',
                'impact_value': 15.0,
                'type': 'POSITIVE'
            })
        elif variance > 10:
            explanations.append({
                'feature': 'High GST/Bank Variance',
                'impact_value': -15.0,
                'type': 'NEGATIVE'
            })
        
        # Due Diligence
        dd_penalty = features.get('due_diligence_penalty', 0)
        if dd_penalty < 0:
            explanations.append({
                'feature': 'Aging Machinery (Primary Insight)',
                'impact_value': float(dd_penalty),
                'type': 'NEGATIVE'
            })
        
        # Debt to Equity
        dte = features.get('debt_to_equity', 1.0)
        if dte > 2.5:
            explanations.append({
                'feature': 'High Leverage (D/E > 2.5)',
                'impact_value': -10.0,
                'type': 'NEGATIVE'
            })
        elif dte < 1.0:
            explanations.append({
                'feature': 'Low Leverage',
                'impact_value': 8.0,
                'type': 'POSITIVE'
            })
        
        # Sector risk
        sector_risk = features.get('sector_risk_score', 0)
        if sector_risk > 30:
            explanations.append({
                'feature': 'Challenging Sector Conditions',
                'impact_value': -8.0,
                'type': 'NEGATIVE'
            })
        
        # Sort by absolute impact
        explanations.sort(key=lambda x: abs(x['impact_value']), reverse=True)
        
        return explanations
    
    def generate_textual_explanation(
        self,
        decision: str,
        shap_explanations: List[Dict],
        features: Dict
    ) -> str:
        """
        Generate human-readable explanation
        """
        
        if decision == 'APPROVE':
            intro = "The application is approved based on strong financial metrics and favorable risk assessment."
        elif decision == 'CONDITIONAL_APPROVE':
            intro = "The application is conditionally approved with reduced limit due to mixed signals."
        else:
            intro = "The application is rejected due to significant risk factors."
        
        # Top positive factors
        positive = [exp for exp in shap_explanations if exp['type'] == 'POSITIVE']
        negative = [exp for exp in shap_explanations if exp['type'] == 'NEGATIVE']
        
        explanation_parts = [intro]
        
        if positive:
            explanation_parts.append(
                f"\n\nPositive factors: {', '.join([p['feature'] for p in positive[:3]])}"
            )
        
        if negative:
            explanation_parts.append(
                f"\n\nRisk factors: {', '.join([n['feature'] for n in negative[:3]])}"
            )
        
        return ' '.join(explanation_parts)
    
    def create_waterfall_data(self, shap_explanations: List[Dict], base_score: int) -> List[Dict]:
        """
        Create data for waterfall chart visualization
        """
        
        waterfall = [{'label': 'Base Score', 'value': base_score, 'cumulative': base_score}]
        
        cumulative = base_score
        for exp in shap_explanations:
            cumulative += exp['impact_value']
            waterfall.append({
                'label': exp['feature'],
                'value': exp['impact_value'],
                'cumulative': cumulative
            })
        
        return waterfall
