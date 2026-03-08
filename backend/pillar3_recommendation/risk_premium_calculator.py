"""
Risk Premium Calculator - Calculate appropriate interest rate/risk premium
"""
from typing import Dict, Any


class RiskPremiumCalculator:
    """
    Calculate risk premium and interest rate based on:
    - Credit score
    - Sector risk
    - Financial strength
    """
    
    def __init__(self):
        self.base_rate = 9.5  # Base lending rate in %
    
    def calculate_risk_premium(
        self,
        credit_score: int,
        sector_risk_score: int,
        dscr: float,
        litigation_risk: bool
    ) -> Dict[str, Any]:
        """
        Calculate risk premium and final interest rate
        """
        
        premium = 0.0
        
        # Credit score based premium
        if credit_score >= 80:
            premium += 0.0  # No premium for excellent credit
        elif credit_score >= 70:
            premium += 0.5
        elif credit_score >= 60:
            premium += 1.5
        elif credit_score >= 50:
            premium += 2.5
        else:
            premium += 4.0
        
        # Sector risk premium
        if sector_risk_score >= 40:
            premium += 1.0
        elif sector_risk_score >= 25:
            premium += 0.5
        
        # DSCR-based adjustment
        if dscr < 1.0:
            premium += 1.5
        elif dscr < 1.25:
            premium += 0.75
        elif dscr >= 2.0:
            premium -= 0.25  # Reward for strong DSCR
        
        # Litigation premium
        if litigation_risk:
            premium += 0.5
        
        final_rate = self.base_rate + premium
        
        return {
            'base_rate': self.base_rate,
            'risk_premium': round(premium, 2),
            'final_interest_rate': round(final_rate, 2),
            'rate_category': self._get_rate_category(premium)
        }
    
    def _get_rate_category(self, premium: float) -> str:
        """Map premium to rate category"""
        
        if premium <= 1.0:
            return 'Prime'
        elif premium <= 2.5:
            return 'Standard'
        elif premium <= 4.0:
            return 'Sub-Prime'
        else:
            return 'High Risk'
