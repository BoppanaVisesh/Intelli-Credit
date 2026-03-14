"""
Five Cs Credit Scoring Engine — Deterministic, Explainable, Bank-Grade

Weights (per specification):
  Character  → 20%  (management integrity, litigation, reputation)
  Capacity   → 30%  (cash flow, profitability, DSCR)
  Capital    → 20%  (equity, net worth, D/E ratio)
  Collateral → 20%  (assets pledged, LTV)
  Conditions → 10%  (sector risk, industry trends, regulatory)

Decision thresholds:
  Score ≥ 80  → APPROVE
  Score 60-79 → CONDITIONAL_APPROVE
  Score < 60  → REJECT
"""
from typing import Dict, Any, List, Tuple


class CreditScorerFixed:

    WEIGHTS = {
        "character":  0.20,
        "capacity":   0.30,
        "capital":    0.20,
        "collateral": 0.20,
        "conditions": 0.10,
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def calculate_credit_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        financials      = data.get("financials", {})
        research        = data.get("research", {})
        due_diligence   = data.get("due_diligence", {})
        sector_info     = data.get("sector", {})
        collateral_info = data.get("collateral", {})

        char_score,  char_reasons  = self._score_character(research, financials)
        cap_score,   cap_reasons   = self._score_capacity(financials)
        capit_score, capit_reasons = self._score_capital(financials)
        coll_score,  coll_reasons  = self._score_collateral(financials, collateral_info)
        cond_score,  cond_reasons  = self._score_conditions(sector_info, research, financials)

        raw_score = (
            char_score  * self.WEIGHTS["character"]  +
            cap_score   * self.WEIGHTS["capacity"]   +
            capit_score * self.WEIGHTS["capital"]     +
            coll_score  * self.WEIGHTS["collateral"]  +
            cond_score  * self.WEIGHTS["conditions"]
        )

        dd_adj, dd_reasons = self._apply_due_diligence(due_diligence)
        final_score = max(0, min(100, int(round(raw_score + dd_adj))))

        decision, approval_pct = self._decide(final_score)
        risk_grade = self._risk_grade(final_score)

        requested = data.get("requested_limit_cr", 10.0)
        recommended = round(requested * approval_pct / 100, 2)

        return {
            "model_version": "five-cs-v3.0",
            "final_credit_score": final_score,
            "max_score": 100,
            "decision": decision,
            "risk_grade": risk_grade,
            "requested_limit_cr": requested,
            "recommended_limit_cr": recommended,
            "approval_percentage": approval_pct,
            "sub_scores": {
                "character":  {"score": int(char_score),  "weight": self.WEIGHTS["character"]},
                "capacity":   {"score": int(cap_score),   "weight": self.WEIGHTS["capacity"]},
                "capital":    {"score": int(capit_score),  "weight": self.WEIGHTS["capital"]},
                "collateral": {"score": int(coll_score),   "weight": self.WEIGHTS["collateral"]},
                "conditions": {"score": int(cond_score),   "weight": self.WEIGHTS["conditions"]},
            },
            "explanations": {
                "character":  " | ".join(char_reasons),
                "capacity":   " | ".join(cap_reasons),
                "capital":    " | ".join(capit_reasons),
                "collateral": " | ".join(coll_reasons),
                "conditions": " | ".join(cond_reasons),
                "due_diligence": " | ".join(dd_reasons) if dd_reasons else "No adjustments",
            },
            "key_factors": self._key_factors(
                char_score, cap_score, capit_score, coll_score, cond_score, dd_adj
            ),
        }

    # ------------------------------------------------------------------
    # 1. CHARACTER (20%)
    # ------------------------------------------------------------------
    def _score_character(self, research: Dict, fin: Dict) -> Tuple[float, List[str]]:
        score = 70
        reasons: List[str] = []

        lit = research.get("litigation_count", 0)
        if lit > 3:
            score -= 30
            reasons.append(f"❌ {lit} litigation cases — severe legal exposure")
        elif lit > 0:
            score -= lit * 5
            reasons.append(f"⚠️ {lit} litigation case(s) found")
        else:
            score += 20
            reasons.append("✅ No litigation — clean legal record")

        sentiment = research.get("promoter_sentiment", "Neutral")
        if sentiment in ("Positive", "POSITIVE"):
            score += 10
            reasons.append("✅ Positive management reputation")
        elif sentiment in ("Negative", "NEGATIVE"):
            score -= 25
            reasons.append("❌ Adverse promoter/management news detected")

        circ = research.get("circular_trading_risk_score", 0)
        if circ > 70:
            score -= 30
            reasons.append(f"❌ HIGH circular trading risk ({circ}/100)")
        elif circ > 40:
            score -= 15
            reasons.append(f"⚠️ Moderate circular trading indicators ({circ}/100)")
        else:
            score += 5
            reasons.append("✅ Clean transaction patterns")

        promoter_holding = fin.get("promoter_holding_pct", 0)
        pledged = fin.get("pledged_holding_pct", 0)
        if promoter_holding:
            if promoter_holding >= 50:
                score += 8
                reasons.append(f"✅ Strong promoter skin in the game ({promoter_holding:.1f}%)")
            elif promoter_holding >= 30:
                score += 3
                reasons.append(f"⚠️ Moderate promoter holding ({promoter_holding:.1f}%)")
            else:
                score -= 10
                reasons.append(f"❌ Low promoter holding ({promoter_holding:.1f}%)")

        if pledged > 50:
            score -= 20
            reasons.append(f"❌ Promoter pledge very high ({pledged:.1f}%)")
        elif pledged > 10:
            score -= 10
            reasons.append(f"⚠️ Promoter shares pledged ({pledged:.1f}%)")
        elif promoter_holding and pledged == 0:
            score += 3
            reasons.append("✅ No promoter pledge disclosed")

        return max(0, min(100, score)), reasons

    # ------------------------------------------------------------------
    # 2. CAPACITY (30%)
    # ------------------------------------------------------------------
    def _score_capacity(self, fin: Dict) -> Tuple[float, List[str]]:
        score = 50
        reasons: List[str] = []

        dscr = fin.get("dscr", 1.0)
        if dscr >= 2.0:
            score += 40
            reasons.append(f"✅ Excellent DSCR {dscr:.2f} — strong repayment capacity")
        elif dscr >= 1.5:
            score += 30
            reasons.append(f"✅ Good DSCR {dscr:.2f}")
        elif dscr >= 1.25:
            score += 15
            reasons.append(f"⚠️ Acceptable DSCR {dscr:.2f}")
        elif dscr >= 1.0:
            score -= 5
            reasons.append(f"⚠️ Low DSCR {dscr:.2f}")
        else:
            score -= 25
            reasons.append(f"❌ DSCR {dscr:.2f} < 1.0 — insufficient to service debt")

        cr = fin.get("current_ratio", 1.0)
        if cr >= 2.0:
            score += 10
            reasons.append(f"✅ Strong liquidity CR {cr:.2f}")
        elif cr >= 1.5:
            score += 5
        elif cr < 1.0:
            score -= 15
            reasons.append(f"❌ Liquidity risk CR {cr:.2f}")

        var = fin.get("gst_vs_bank_variance", 0.0)
        if var > 15:
            score -= 20
            reasons.append(f"❌ High GST-Bank mismatch {var:.1f}%")
        elif var > 10:
            score -= 10
            reasons.append(f"⚠️ Moderate GST-Bank variance {var:.1f}%")
        elif var <= 5:
            score += 5
            reasons.append(f"✅ GST-Bank aligned ({var:.1f}%)")

        return max(0, min(100, score)), reasons

    # ------------------------------------------------------------------
    # 3. CAPITAL (20%)
    # ------------------------------------------------------------------
    def _score_capital(self, fin: Dict) -> Tuple[float, List[str]]:
        score = 60
        reasons: List[str] = []

        de = fin.get("debt_to_equity", 1.0)
        if de <= 1.0:
            score += 35
            reasons.append(f"✅ Excellent D/E {de:.2f}")
        elif de <= 2.0:
            score += 20
            reasons.append(f"✅ Good leverage D/E {de:.2f}")
        elif de <= 3.0:
            reasons.append(f"⚠️ Moderate leverage D/E {de:.2f}")
        elif de <= 5.0:
            score -= 20
            reasons.append(f"❌ High leverage D/E {de:.2f}")
        else:
            score -= 40
            reasons.append(f"❌ Excessive leverage D/E {de:.2f}")

        nw = fin.get("net_worth_cr", 0)
        if nw and nw > 50:
            score += 5
            reasons.append(f"✅ Strong net worth ₹{nw:.1f} Cr")

        return max(0, min(100, score)), reasons

    # ------------------------------------------------------------------
    # 4. COLLATERAL (20%)
    # ------------------------------------------------------------------
    def _score_collateral(self, fin: Dict, collateral: Dict) -> Tuple[float, List[str]]:
        score = 50
        reasons: List[str] = []

        property_val = collateral.get("property_value_cr", 0) or fin.get("fixed_assets_cr", 0)
        inventory    = collateral.get("inventory_cr", 0) or fin.get("inventory_cr", 0)
        machinery    = collateral.get("machinery_cr", 0) or fin.get("plant_machinery_cr", 0)
        total = property_val + inventory + machinery

        if total > 0:
            loan = fin.get("requested_limit_cr", 10.0)
            ltv = loan / total if total else 999
            if ltv <= 0.5:
                score += 40
                reasons.append(f"✅ LTV {ltv:.0%} — excellent collateral (₹{total:.1f} Cr)")
            elif ltv <= 0.7:
                score += 25
                reasons.append(f"✅ LTV {ltv:.0%} — adequate collateral")
            elif ltv <= 1.0:
                score += 10
                reasons.append(f"⚠️ LTV {ltv:.0%} — marginal collateral")
            else:
                score -= 10
                reasons.append(f"❌ LTV {ltv:.0%} — under-collateralized")
        else:
            fa = fin.get("total_assets_cr", 0)
            if fa and fa > 0:
                score += 10
                reasons.append(f"Total assets ₹{fa:.1f} Cr (detailed collateral data unavailable)")
            else:
                reasons.append("Collateral data not available — assessed on financials only")

        return max(0, min(100, score)), reasons

    # ------------------------------------------------------------------
    # 5. CONDITIONS (10%)
    # ------------------------------------------------------------------
    def _score_conditions(self, sector: Dict, research: Dict, fin: Dict) -> Tuple[float, List[str]]:
        score = 70
        reasons: List[str] = []

        risk = sector.get("sector_risk_score", 30)
        if risk < 20:
            score += 25
            reasons.append("✅ Stable sector, low macro risk")
        elif risk < 40:
            score += 10
            reasons.append("✅ Moderate sector risk")
        elif risk < 60:
            score -= 5
            reasons.append(f"⚠️ Elevated sector risk ({risk}/100)")
        else:
            score -= 20
            reasons.append(f"❌ High sector risk ({risk}/100)")

        sent = research.get("sector_sentiment", "Neutral")
        if sent in ("Negative", "NEGATIVE"):
            score -= 10
            reasons.append("⚠️ Adverse sector news")
        elif sent in ("Positive", "POSITIVE"):
            score += 5
            reasons.append("✅ Positive sector outlook")

        top10_borrowings_pct = fin.get("top10_borrowings_pct", 0)
        if top10_borrowings_pct >= 70:
            score -= 15
            reasons.append(f"❌ Funding concentrated in top borrowings ({top10_borrowings_pct:.1f}%)")
        elif top10_borrowings_pct >= 50:
            score -= 8
            reasons.append(f"⚠️ Borrowing concentration elevated ({top10_borrowings_pct:.1f}%)")

        short_term_liabilities_pct = fin.get("short_term_liabilities_pct_total_liabilities", 0)
        if short_term_liabilities_pct >= 50:
            score -= 15
            reasons.append(f"❌ Short-term liabilities are high ({short_term_liabilities_pct:.1f}% of liabilities)")
        elif short_term_liabilities_pct >= 35:
            score -= 8
            reasons.append(f"⚠️ Short-term liabilities need monitoring ({short_term_liabilities_pct:.1f}%)")

        significant_counterparty_pct = fin.get("significant_counterparty_liabilities_pct", 0)
        if significant_counterparty_pct >= 25:
            score -= 6
            reasons.append(f"⚠️ Significant counterparty concentration ({significant_counterparty_pct:.1f}% of liabilities)")

        return max(0, min(100, score)), reasons

    # ------------------------------------------------------------------
    # Due-diligence overlay
    # ------------------------------------------------------------------
    def _apply_due_diligence(self, dd: Dict) -> Tuple[float, List[str]]:
        adj = 0
        reasons: List[str] = []
        sev = dd.get("severity", "None")
        notes = dd.get("notes", "")

        mapping = {
            "Critical": -20, "CRITICAL": -20,
            "High": -10, "HIGH": -10,
            "Medium": -5, "Moderate": -5, "MEDIUM": -5,
            "Positive": 5, "POSITIVE": 5,
        }
        adj = mapping.get(sev, 0)
        if adj < 0:
            reasons.append(f"{'❌' if adj <= -10 else '⚠️'} {sev} finding: {notes[:120]}")
        elif adj > 0:
            reasons.append("✅ Positive field observations")

        return adj, reasons

    # ------------------------------------------------------------------
    # Decision helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _decide(score: int) -> Tuple[str, int]:
        if score >= 80:
            return ("APPROVE", 100)
        if score >= 60:
            return ("CONDITIONAL_APPROVE", 75 if score >= 70 else 50)
        return ("REJECT", 0)

    @staticmethod
    def _risk_grade(score: int) -> str:
        if score >= 85: return "AAA"
        if score >= 75: return "AA"
        if score >= 65: return "A"
        if score >= 55: return "BBB"
        if score >= 45: return "BB"
        return "B"

    @staticmethod
    def _key_factors(char, cap, capit, coll, cond, dd_adj) -> List[str]:
        items = [
            ("Character & Legal Record", char * 0.20),
            ("Repayment Capacity (DSCR, Cash Flow)", cap * 0.30),
            ("Capital Structure (D/E, Net Worth)", capit * 0.20),
            ("Collateral Coverage (LTV)", coll * 0.20),
            ("Sector & Macro Conditions", cond * 0.10),
        ]
        if dd_adj:
            items.append(("Due Diligence Findings", abs(dd_adj)))
        items.sort(key=lambda x: abs(x[1]), reverse=True)
        return [i[0] for i in items[:3]]
