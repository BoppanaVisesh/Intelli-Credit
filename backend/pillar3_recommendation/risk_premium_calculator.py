"""
Interest Rate / Risk Premium Calculator

Logic (per specification):
  Score ≥ 80  → 10.0%
  Score 70-79 → 11.5%
  Score 60-69 → 13.0%
  Score < 60  → REJECT (no rate offered)

Additional micro-adjustments for DSCR, sector risk, litigation.
"""
from typing import Dict, Any, Optional


class RiskPremiumCalculator:

    BASE_RATE = 9.5  # percent

    def calculate(
        self,
        credit_score: int,
        dscr: float = 1.0,
        sector_risk_score: int = 30,
        litigation_count: int = 0,
    ) -> Dict[str, Any]:
        # Primary rate from score bands
        primary_rate = self._band_rate(credit_score)
        if primary_rate is None:
            return {
                "base_rate": self.BASE_RATE,
                "risk_premium": None,
                "final_interest_rate": None,
                "rate_category": "Rejected",
                "offered": False,
            }

        # Micro-adjustments
        premium = primary_rate - self.BASE_RATE

        # DSCR bonus/penalty
        if dscr >= 2.0:
            premium -= 0.25
        elif dscr < 1.0:
            premium += 1.5
        elif dscr < 1.25:
            premium += 0.75

        # Sector risk
        if sector_risk_score >= 50:
            premium += 1.0
        elif sector_risk_score >= 30:
            premium += 0.5

        # Litigation
        if litigation_count > 3:
            premium += 1.0
        elif litigation_count > 0:
            premium += 0.5

        final = round(self.BASE_RATE + premium, 2)

        return {
            "base_rate": self.BASE_RATE,
            "risk_premium": round(premium, 2),
            "final_interest_rate": final,
            "rate_category": self._category(premium),
            "offered": True,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _band_rate(score: int) -> Optional[float]:
        if score >= 80:
            return 10.0
        if score >= 70:
            return 11.5
        if score >= 60:
            return 13.0
        return None  # Reject

    @staticmethod
    def _category(premium: float) -> str:
        if premium <= 1.0:
            return "Prime"
        if premium <= 2.5:
            return "Standard"
        if premium <= 4.0:
            return "Sub-Prime"
        return "High Risk"
