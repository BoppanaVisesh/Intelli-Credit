"""
Explainable Decision Engine — Human-readable reasons for every credit decision.

Produces a structured list of reasons & a narrative summary suitable for
inclusion in the CAM document.
"""
from typing import Dict, List, Any


class Explainability:

    def generate_reasons(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Walk through all available signals and emit human-readable reasons.
        Each reason: { text, impact: POSITIVE|NEGATIVE|NEUTRAL, weight }
        """
        reasons: List[Dict[str, Any]] = []
        fin = data.get("financials", {})
        research = data.get("research", {})
        scoring = data.get("scoring", {})

        # Litigation
        lit = research.get("litigation_count", 0)
        if lit > 2:
            reasons.append({"text": f"High litigation exposure detected ({lit} cases)", "impact": "NEGATIVE", "weight": 3})
        elif lit > 0:
            reasons.append({"text": f"{lit} litigation case(s) on record", "impact": "NEGATIVE", "weight": 1})
        else:
            reasons.append({"text": "No litigation — clean legal record", "impact": "POSITIVE", "weight": 2})

        # GST variance
        gst_var = fin.get("gst_vs_bank_variance", 0)
        if gst_var > 5:
            reasons.append({"text": f"Mismatch between GSTR-1 and bank inflows ({gst_var:.1f}%)", "impact": "NEGATIVE", "weight": 2})
        else:
            reasons.append({"text": "GST and bank records well-aligned", "impact": "POSITIVE", "weight": 1})

        # Overdraft
        od = fin.get("overdraft_instances", 0)
        if od and od > 0:
            reasons.append({"text": f"Irregular bank balance patterns ({od} overdraft instances)", "impact": "NEGATIVE", "weight": 2})

        # Bounced cheques
        bounced = fin.get("bounced_cheques", 0)
        if bounced and bounced > 0:
            reasons.append({"text": f"{bounced} bounced cheque(s) detected", "impact": "NEGATIVE", "weight": 2})

        # D/E ratio
        de = fin.get("debt_to_equity", 1.0)
        if de > 3.0:
            reasons.append({"text": f"Debt-to-equity ratio ({de:.2f}) exceeds acceptable threshold", "impact": "NEGATIVE", "weight": 3})
        elif de <= 1.0:
            reasons.append({"text": f"Conservative leverage (D/E {de:.2f})", "impact": "POSITIVE", "weight": 2})

        # DSCR
        dscr = fin.get("dscr", 1.0)
        if dscr >= 1.5:
            reasons.append({"text": f"Strong debt service coverage (DSCR {dscr:.2f})", "impact": "POSITIVE", "weight": 3})
        elif dscr < 1.0:
            reasons.append({"text": f"Cash flows insufficient for debt service (DSCR {dscr:.2f})", "impact": "NEGATIVE", "weight": 3})

        # Circular trading
        circ = research.get("circular_trading_risk_score", 0)
        if circ > 50:
            reasons.append({"text": "Circular trading patterns detected in transaction data", "impact": "NEGATIVE", "weight": 3})

        # Promoter sentiment
        sent = research.get("promoter_sentiment", "Neutral")
        if sent in ("Negative", "NEGATIVE"):
            reasons.append({"text": "Adverse news about promoter/management found in web research", "impact": "NEGATIVE", "weight": 2})
        elif sent in ("Positive", "POSITIVE"):
            reasons.append({"text": "Positive promoter reputation in market", "impact": "POSITIVE", "weight": 1})

        promoter_holding = fin.get("promoter_holding_pct", 0)
        if promoter_holding:
            if promoter_holding >= 50:
                reasons.append({"text": f"Strong promoter ownership ({promoter_holding:.1f}%) supports alignment", "impact": "POSITIVE", "weight": 2})
            elif promoter_holding < 20:
                reasons.append({"text": f"Low promoter ownership ({promoter_holding:.1f}%) weakens sponsor alignment", "impact": "NEGATIVE", "weight": 2})

        pledged = fin.get("pledged_holding_pct", 0)
        if pledged > 10:
            reasons.append({"text": f"Promoter shares pledged ({pledged:.1f}%)", "impact": "NEGATIVE", "weight": 3})

        top10_borrowings_pct = fin.get("top10_borrowings_pct", 0)
        if top10_borrowings_pct >= 50:
            reasons.append({"text": f"Borrowing book concentrated in top facilities ({top10_borrowings_pct:.1f}%)", "impact": "NEGATIVE", "weight": 2})

        short_term_liabilities_pct = fin.get("short_term_liabilities_pct_total_liabilities", 0)
        if short_term_liabilities_pct >= 35:
            reasons.append({"text": f"Elevated short-term liabilities ({short_term_liabilities_pct:.1f}% of total liabilities)", "impact": "NEGATIVE", "weight": 2})

        # Sort by weight descending
        reasons.sort(key=lambda r: r["weight"], reverse=True)
        return reasons

    def generate_narrative(self, decision: str, reasons: List[Dict], score: int) -> str:
        """Build a prose paragraph for the CAM executive summary."""
        neg = [r["text"] for r in reasons if r["impact"] == "NEGATIVE"]
        pos = [r["text"] for r in reasons if r["impact"] == "POSITIVE"]

        if decision == "APPROVE":
            opening = f"With a credit score of {score}/100 the application is APPROVED. "
        elif decision == "CONDITIONAL_APPROVE":
            opening = f"With a credit score of {score}/100 the application is conditionally approved with a reduced limit. "
        else:
            opening = f"With a credit score of {score}/100 the application is REJECTED due to significant risk factors. "

        parts = [opening]
        if pos:
            parts.append("Positive factors: " + "; ".join(pos[:3]) + ". ")
        if neg:
            parts.append("Risk factors: " + "; ".join(neg[:3]) + ".")

        return "".join(parts)
