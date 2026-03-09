"""
Loan Limit Engine — Three-method recommendation per specification

Methods:
  1. Revenue Multiple:   loan_limit = revenue × 0.25
  2. Cash Flow Based:    loan_limit = operating_cash_flow × 4
  3. Collateral Based:   loan_limit = collateral_value × 0.7

Final recommendation = min(revenue_limit, cashflow_limit, collateral_limit)
Then apply risk-score adjustment.
"""
from typing import Dict, Any


class LoanLimitEngine:

    def calculate_loan_limit(
        self,
        financials: Dict[str, Any],
        risk_score: int,
        requested_limit_cr: float = 10.0,
    ) -> Dict[str, Any]:
        revenue   = financials.get("revenue_cr", 0) or financials.get("gst_sales_cr", 0) or 0
        op_cf     = financials.get("operating_cash_flow_cr", 0)
        if not op_cf:
            # Estimate: inflows - outflows
            inflows  = financials.get("bank_inflows_cr", 0) or 0
            outflows = financials.get("bank_outflows_cr", 0) or 0
            op_cf = max(inflows - outflows, 0)

        collateral = (
            financials.get("collateral_value_cr", 0)
            or (
                (financials.get("fixed_assets_cr", 0) or 0) +
                (financials.get("inventory_cr", 0) or 0) +
                (financials.get("plant_machinery_cr", 0) or 0)
            )
        )

        # Three methods
        revenue_limit    = revenue * 0.25
        cashflow_limit   = op_cf * 4
        collateral_limit = collateral * 0.7

        candidates = []
        if revenue_limit > 0:
            candidates.append(revenue_limit)
        if cashflow_limit > 0:
            candidates.append(cashflow_limit)
        if collateral_limit > 0:
            candidates.append(collateral_limit)

        if candidates:
            base_limit = min(candidates)
        else:
            base_limit = requested_limit_cr * 0.5  # fallback

        # Risk adjustment
        risk_adj = self._risk_multiplier(risk_score)
        recommended = round(base_limit * risk_adj, 2)

        # Never exceed requested amount
        recommended = min(recommended, requested_limit_cr)

        return {
            "revenue_limit_cr": round(revenue_limit, 2),
            "cashflow_limit_cr": round(cashflow_limit, 2),
            "collateral_limit_cr": round(collateral_limit, 2),
            "base_limit_cr": round(base_limit, 2),
            "risk_adjustment_factor": risk_adj,
            "recommended_limit_cr": recommended,
            "requested_limit_cr": requested_limit_cr,
            "methodology": "min(Revenue×0.25, CashFlow×4, Collateral×0.7) × risk_adj",
        }

    @staticmethod
    def _risk_multiplier(score: int) -> float:
        if score >= 80:
            return 1.0
        if score >= 70:
            return 0.85
        if score >= 60:
            return 0.65
        if score >= 50:
            return 0.40
        return 0.0
