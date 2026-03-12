"""
Recommendation Reasoning Engine — Explainable loan-approval pipeline.

Produces a fully auditable decision tree with:
  - Weighted reason chain (each factor, its source, its impact, its weight)
  - Stage-by-stage gate results (primary scoring → secondary validation → triangulation check)
  - Final recommendation with confidence % and human-readable narrative
  - Override / adjustment explanations

Designed to be serialisable as JSON for API + PDF rendering.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class RecommendationEngine:
    """
    Three-gate decision pipeline:
      Gate 1 — Primary Financial Score (Five Cs)
      Gate 2 — Secondary Research Validation
      Gate 3 — Triangulation Consistency Check
    """

    # Gate thresholds
    APPROVE_SCORE = 80
    CONDITIONAL_SCORE = 60

    def generate_recommendation(
        self,
        scoring: Dict[str, Any],
        research_signals: Dict[str, Any],
        triangulation: Dict[str, Any],
        financials: Dict[str, Any],
        loan_recommendation: Dict[str, Any],
        interest_rate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run the full reasoning pipeline and return explainable recommendation.
        """
        reason_chain: List[Dict[str, Any]] = []
        gates: List[Dict[str, Any]] = []

        credit_score = scoring.get("final_credit_score", 0)
        sub_scores = scoring.get("sub_scores", {})
        explanations = scoring.get("explanations", {})

        # ══════════════════════════════════════════════════════════
        # GATE 1 — Primary Financial Score
        # ══════════════════════════════════════════════════════════
        g1_pass = credit_score >= self.CONDITIONAL_SCORE
        g1_strong = credit_score >= self.APPROVE_SCORE

        for dim in ("character", "capacity", "capital", "collateral", "conditions"):
            info = sub_scores.get(dim, {})
            sc = info.get("score", 0)
            wt = info.get("weight", 0)
            explanation = explanations.get(dim, "")
            impact = "POSITIVE" if sc >= 70 else ("NEGATIVE" if sc < 50 else "NEUTRAL")
            reason_chain.append({
                "gate": 1,
                "factor": f"Five Cs — {dim.capitalize()}",
                "score": sc,
                "weight": wt,
                "impact": impact,
                "detail": explanation,
                "source": "Financial Analysis",
            })

        gates.append({
            "gate": 1,
            "name": "Primary Financial Score",
            "score": credit_score,
            "threshold": self.CONDITIONAL_SCORE,
            "passed": g1_pass,
            "verdict": "STRONG PASS" if g1_strong else ("PASS" if g1_pass else "FAIL"),
        })

        # ══════════════════════════════════════════════════════════
        # GATE 2 — Secondary Research Validation
        # ══════════════════════════════════════════════════════════
        signals = research_signals.get("signals", [])
        risk_count = research_signals.get("risk_signal_count", 0)
        pos_count = research_signals.get("positive_signal_count", 0)
        overall_risk = research_signals.get("overall_risk", "MEDIUM")

        for sig in signals:
            impact = "POSITIVE" if sig["signal"] == "POSITIVE" else (
                "NEGATIVE" if sig["signal"] in ("NEGATIVE", "HIGH", "RISK_ALERT") else "NEUTRAL")
            reason_chain.append({
                "gate": 2,
                "factor": f"Secondary — {sig['source']}",
                "score": None,
                "weight": 0.15 if impact == "NEGATIVE" else 0.10,
                "impact": impact,
                "detail": sig["detail"],
                "source": sig["source"],
            })

        g2_pass = overall_risk != "HIGH"
        g2_score = max(0, 100 - risk_count * 15 + pos_count * 5)
        gates.append({
            "gate": 2,
            "name": "Secondary Research Validation",
            "score": g2_score,
            "threshold": 40,
            "passed": g2_pass,
            "verdict": "PASS" if g2_pass else "FAIL",
        })

        # ══════════════════════════════════════════════════════════
        # GATE 3 — Triangulation Consistency
        # ══════════════════════════════════════════════════════════
        tri_summary = triangulation.get("summary", {})
        contradictions = tri_summary.get("contradictions", 0)
        confirmed = tri_summary.get("confirmed", 0)
        confidence_grade = tri_summary.get("confidence_grade", "MODERATE")

        for f in triangulation.get("findings", []):
            impact = {"CONFIRMED": "POSITIVE", "CONTRADICTION": "NEGATIVE",
                       "WARNING": "NEUTRAL", "GAP": "NEUTRAL"}.get(f["status"], "NEUTRAL")
            reason_chain.append({
                "gate": 3,
                "factor": f"Triangulation — {f['metric']}",
                "score": int(f["confidence"] * 100),
                "weight": 0.10,
                "impact": impact,
                "detail": f["detail"],
                "source": ", ".join(f["sources"]) if f["sources"] else "Cross-reference",
            })

        g3_pass = confidence_grade != "LOW"
        g3_score = max(0, confirmed * 15 - contradictions * 20 + 50)
        gates.append({
            "gate": 3,
            "name": "Triangulation Consistency",
            "score": min(100, g3_score),
            "threshold": 40,
            "passed": g3_pass,
            "verdict": "PASS" if g3_pass else "FAIL",
        })

        # ══════════════════════════════════════════════════════════
        # FINAL DECISION
        # ══════════════════════════════════════════════════════════
        gates_passed = sum(1 for g in gates if g["passed"])

        if g1_strong and gates_passed == 3:
            decision = "APPROVE"
            confidence_pct = min(95, 70 + pos_count * 3 + confirmed * 4)
        elif g1_pass and gates_passed >= 2:
            decision = "CONDITIONAL_APPROVE"
            confidence_pct = min(80, 50 + pos_count * 2 + confirmed * 3)
        else:
            decision = "REJECT"
            confidence_pct = min(90, 60 + risk_count * 5 + contradictions * 5)

        # Build narrative
        narrative = self._build_narrative(
            decision, credit_score, gates, reason_chain,
            loan_recommendation, interest_rate, confidence_pct,
        )

        # Sort reasons by impact (negatives first, then positives)
        impact_order = {"NEGATIVE": 0, "NEUTRAL": 1, "POSITIVE": 2}
        reason_chain.sort(key=lambda r: (impact_order.get(r["impact"], 1), -(r.get("weight") or 0)))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision,
            "credit_score": credit_score,
            "confidence_pct": confidence_pct,
            "gates": gates,
            "reason_chain": reason_chain,
            "narrative": narrative,
            "loan_recommendation": loan_recommendation,
            "interest_rate": interest_rate,
            "key_risks": [r for r in reason_chain if r["impact"] == "NEGATIVE"][:5],
            "key_strengths": [r for r in reason_chain if r["impact"] == "POSITIVE"][:5],
        }

    # ------------------------------------------------------------------
    def _build_narrative(
        self, decision, score, gates, reasons,
        loan, rate, confidence,
    ) -> str:
        parts = []

        # Opening
        if decision == "APPROVE":
            parts.append(
                f"Based on a comprehensive three-gate analysis, this application is **APPROVED** "
                f"with a credit score of {score}/100 and {confidence}% recommendation confidence."
            )
        elif decision == "CONDITIONAL_APPROVE":
            parts.append(
                f"This application receives a **CONDITIONAL APPROVAL** with a credit score of "
                f"{score}/100. Confidence in recommendation: {confidence}%."
            )
        else:
            parts.append(
                f"This application is **REJECTED** with a credit score of {score}/100. "
                f"Multiple gates have failed with {confidence}% confidence in this assessment."
            )

        # Gate summary
        for g in gates:
            parts.append(
                f"Gate {g['gate']} ({g['name']}): {g['verdict']} "
                f"(Score {g['score']}, threshold {g['threshold']})"
            )

        # Key factors
        negatives = [r for r in reasons if r["impact"] == "NEGATIVE"]
        positives = [r for r in reasons if r["impact"] == "POSITIVE"]
        if positives:
            parts.append("Strengths: " + "; ".join(r["detail"][:100] for r in positives[:3]))
        if negatives:
            parts.append("Risks: " + "; ".join(r["detail"][:100] for r in negatives[:3]))

        # Loan terms
        if decision != "REJECT" and loan:
            limit = loan.get("recommended_limit_cr", 0)
            ir = rate.get("final_interest_rate", "N/A")
            parts.append(f"Recommended limit: ₹{limit} Cr at {ir}% interest rate.")

        return "\n\n".join(parts)
