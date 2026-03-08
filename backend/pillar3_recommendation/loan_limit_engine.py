"""
Loan Limit Engine - Calculate optimal loan limits
"""
from typing import Dict, Any


class LoanLimitEngine:
    """
    Calculate loan limits based on:
    - Debt servicing capacity
    - Collateral coverage
    - Risk-adjusted limits
    """
    
    def calculate_loan_limit(self, financial_data: Dict[str, Any], risk_score: int) -> Dict[str, Any]:
        """
        Calculate recommended loan limit
        """
        
        # Extract key metrics
        net_operating_income = financial_data.get('net_operating_income_cr', 0)
        existing_debt = financial_data.get('total_debt_cr', 0)
        dscr = financial_data.get('dscr', 1.0)
        
        # Method 1: DSCR-based limit
        dscr_based_limit = self._calculate_dscr_based_limit(
            net_operating_income, existing_debt
        )
        
        # Method 2: Collateral-based limit (assuming 1.5x coverage)
        # In production, get actual collateral value
        collateral_based_limit = dscr_based_limit * 0.75  # Placeholder
        
        # Method 3: Risk-adjusted limit
        risk_adjusted_limit = self._apply_risk_adjustment(
            min(dscr_based_limit, collateral_based_limit), risk_score
        )
        
        return {
            'dscr_based_limit_cr': round(dscr_based_limit, 2),
            'collateral_based_limit_cr': round(collateral_based_limit, 2),
            'risk_adjusted_limit_cr': round(risk_adjusted_limit, 2),
            'recommended_limit_cr': round(risk_adjusted_limit, 2),
            'methodology': 'DSCR + Risk Adjustment'
        }
    
    def _calculate_dscr_based_limit(self, net_operating_income: float, existing_debt: float) -> float:
        """
        Calculate limit based on desired DSCR of 1.5
        """
        
        target_dscr = 1.5
        annual_interest_rate = 0.12  # 12% assumption
        loan_tenure_years = 5
        
        # Maximum annual debt service = NOI / target DSCR
        max_annual_debt_service = net_operating_income / target_dscr
        
        # Calculate loan amount using EMI formula
        # For simplification, use approximate calculation
        max_loan = (max_annual_debt_service * loan_tenure_years) / 1.5
        
        # Subtract existing debt
        available_limit = max(0, max_loan - existing_debt)
        
        return available_limit
    
    def _apply_risk_adjustment(self, base_limit: float, risk_score: int) -> float:
        """
        Adjust limit based on risk score
        """
        
        if risk_score >= 75:
            multiplier = 1.0  # Full limit
        elif risk_score >= 60:
            multiplier = 0.6  # 60% of calculated limit
        elif risk_score >= 50:
            multiplier = 0.4  # 40% of calculated limit
        else:
            multiplier = 0.0  # Reject
        
        return base_limit * multiplier
