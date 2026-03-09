"""
Cross-Verification Engine - Compares financial data from multiple independent sources
and flags mismatches, anomalies, and potential fraud signals.

Pipeline:
    Normalized Data → Rule Checks → Anomaly Scoring → Fraud Signals → Fraud Risk Score
"""
from typing import Dict, Any, List, Tuple
import math


class CrossVerificationEngine:
    """
    Consistency engine that compares numbers from different sources and flags mismatches.
    Uses real parsed data from Bank Statements, GST Returns, ITR, and Annual Reports.
    """

    def __init__(self):
        self.rules = [
            self._check_gst_vs_bank,
            self._check_gst_1_vs_3b,
            self._check_itr_vs_annual_report,
            self._check_gst_vs_annual_report,
            self._check_bank_vs_annual_report,
            self._check_cashflow_stability,
            self._check_bounced_cheques,
            self._check_overdraft_pattern,
            self._check_debt_equity_sanity,
            self._check_related_party_exposure,
            self._check_contingent_liabilities,
            self._check_auditor_opinion,
            self._check_purchase_to_sales_ratio,
            self._check_net_cash_retention,
        ]

    def run_verification(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all cross-verification rules on the unified dataset.
        
        Returns:
            {
                "anomalies": [...],         # list of flagged issues
                "fraud_risk_score": int,    # 0-100
                "risk_level": str,          # LOW / MEDIUM / HIGH / CRITICAL
                "source_count": int,        # how many independent sources available
                "checks_run": int,
                "checks_flagged": int,
                "category_scores": {...},   # per-category breakdown
                "summary": str,
            }
        """
        sources = unified_data.get("sources_available", [])
        anomalies: List[Dict[str, Any]] = []

        for rule_fn in self.rules:
            try:
                result = rule_fn(unified_data)
                if result and result.get("flag"):
                    anomalies.append(result)
            except Exception:
                continue  # silently skip rules that can't run

        # Compute fraud risk score
        raw_score = sum(a.get("score_impact", 0) for a in anomalies)
        # Scale: more sources disagreeing = higher confidence in the score
        source_multiplier = min(len(sources) / 2.0, 1.5)  # max 1.5x
        fraud_score = min(100, int(raw_score * source_multiplier))

        # Category breakdown
        categories: Dict[str, int] = {}
        for a in anomalies:
            cat = a.get("category", "other")
            categories[cat] = categories.get(cat, 0) + a.get("score_impact", 0)

        risk_level = self._risk_level(fraud_score)

        return {
            "anomalies": anomalies,
            "fraud_risk_score": fraud_score,
            "risk_level": risk_level,
            "source_count": len(sources),
            "sources_available": sources,
            "checks_run": len(self.rules),
            "checks_flagged": len(anomalies),
            "category_scores": categories,
            "summary": self._build_summary(anomalies, fraud_score, risk_level, sources),
        }

    # ── Individual Rule Implementations ──────────────────────────────────

    def _check_gst_vs_bank(self, data: Dict) -> Dict[str, Any]:
        """Rule 1: GST sales vs Bank inflows — revenue inflation check."""
        gst = data["gst"]["sales_cr"]
        bank = data["bank"]["total_inflows_cr"]
        if gst <= 0 or bank <= 0:
            return {}
        ratio = bank / gst
        if ratio < 0.5:
            return {
                "flag": True,
                "rule": "GST vs Bank Inflows",
                "category": "revenue_inflation",
                "severity": "HIGH",
                "score_impact": 25,
                "detail": f"Bank inflows (Rs.{bank:.1f} Cr) are only {ratio:.0%} of GST sales (Rs.{gst:.1f} Cr). Suspected revenue inflation.",
                "values": {"gst_sales_cr": gst, "bank_inflows_cr": bank, "ratio": round(ratio, 2)},
            }
        if ratio < 0.75:
            return {
                "flag": True,
                "rule": "GST vs Bank Inflows",
                "category": "revenue_inflation",
                "severity": "MEDIUM",
                "score_impact": 12,
                "detail": f"Bank inflows (Rs.{bank:.1f} Cr) are {ratio:.0%} of GST sales (Rs.{gst:.1f} Cr). Moderate revenue gap.",
                "values": {"gst_sales_cr": gst, "bank_inflows_cr": bank, "ratio": round(ratio, 2)},
            }
        return {}

    def _check_gst_1_vs_3b(self, data: Dict) -> Dict[str, Any]:
        """Rule 2: GSTR-1 vs GSTR-3B — internal GST mismatch."""
        g1 = data["gst"]["sales_cr"]
        g3b = data["gst"]["sales_3b_cr"]
        if g1 <= 0 or g3b <= 0:
            return {}
        variance = abs(g1 - g3b) / max(g1, g3b)
        if variance > 0.10:
            return {
                "flag": True,
                "rule": "GSTR-1 vs GSTR-3B Mismatch",
                "category": "gst_discrepancy",
                "severity": "HIGH" if variance > 0.25 else "MEDIUM",
                "score_impact": 20 if variance > 0.25 else 10,
                "detail": f"GSTR-1 sales (Rs.{g1:.1f} Cr) differ from GSTR-3B (Rs.{g3b:.1f} Cr) by {variance:.0%}.",
                "values": {"gstr1_cr": g1, "gstr3b_cr": g3b, "variance_pct": round(variance * 100, 1)},
            }
        return {}

    def _check_itr_vs_annual_report(self, data: Dict) -> Dict[str, Any]:
        """Rule 3: ITR revenue vs Annual Report revenue."""
        itr_rev = data["itr"]["revenue_cr"]
        ar_rev = data["annual_report"]["revenue_cr"]
        if itr_rev <= 0 or ar_rev <= 0:
            return {}
        variance = abs(itr_rev - ar_rev) / max(itr_rev, ar_rev)
        if variance > 0.15:
            return {
                "flag": True,
                "rule": "ITR vs Annual Report Revenue",
                "category": "revenue_mismatch",
                "severity": "HIGH" if variance > 0.30 else "MEDIUM",
                "score_impact": 20 if variance > 0.30 else 10,
                "detail": f"ITR revenue (Rs.{itr_rev:.1f} Cr) differs from Annual Report (Rs.{ar_rev:.1f} Cr) by {variance:.0%}.",
                "values": {"itr_revenue_cr": itr_rev, "ar_revenue_cr": ar_rev, "variance_pct": round(variance * 100, 1)},
            }
        return {}

    def _check_gst_vs_annual_report(self, data: Dict) -> Dict[str, Any]:
        """Rule 4: GST sales vs Annual Report revenue."""
        gst = data["gst"]["sales_cr"]
        ar = data["annual_report"]["revenue_cr"]
        if gst <= 0 or ar <= 0:
            return {}
        variance = abs(gst - ar) / max(gst, ar)
        if variance > 0.15:
            return {
                "flag": True,
                "rule": "GST vs Annual Report Revenue",
                "category": "revenue_mismatch",
                "severity": "HIGH" if variance > 0.30 else "MEDIUM",
                "score_impact": 18 if variance > 0.30 else 8,
                "detail": f"GST sales (Rs.{gst:.1f} Cr) differ from Annual Report revenue (Rs.{ar:.1f} Cr) by {variance:.0%}.",
                "values": {"gst_sales_cr": gst, "ar_revenue_cr": ar, "variance_pct": round(variance * 100, 1)},
            }
        return {}

    def _check_bank_vs_annual_report(self, data: Dict) -> Dict[str, Any]:
        """Rule 5: Bank inflows vs Annual Report revenue."""
        bank = data["bank"]["total_inflows_cr"]
        ar = data["annual_report"]["revenue_cr"]
        if bank <= 0 or ar <= 0:
            return {}
        ratio = bank / ar
        if ratio < 0.5:
            return {
                "flag": True,
                "rule": "Bank Inflows vs Annual Report Revenue",
                "category": "revenue_inflation",
                "severity": "HIGH",
                "score_impact": 20,
                "detail": f"Bank inflows (Rs.{bank:.1f} Cr) are only {ratio:.0%} of Annual Report revenue (Rs.{ar:.1f} Cr).",
                "values": {"bank_inflows_cr": bank, "ar_revenue_cr": ar, "ratio": round(ratio, 2)},
            }
        return {}

    def _check_cashflow_stability(self, data: Dict) -> Dict[str, Any]:
        """Rule 6: Monthly cash-flow variance."""
        var = data["bank"]["monthly_variability"]
        if var <= 0:
            return {}
        if var > 0.6:
            return {
                "flag": True,
                "rule": "Cash Flow Stability",
                "category": "cashflow_irregularity",
                "severity": "HIGH" if var > 0.8 else "MEDIUM",
                "score_impact": 15 if var > 0.8 else 8,
                "detail": f"Monthly cash flow variability is {var:.2f} — highly irregular.",
                "values": {"monthly_variability": round(var, 2)},
            }
        return {}

    def _check_bounced_cheques(self, data: Dict) -> Dict[str, Any]:
        """Rule 7: Bounced cheques — payment discipline signal."""
        bounced = data["bank"]["bounced_checks"]
        if bounced >= 5:
            return {
                "flag": True,
                "rule": "Bounced Cheques",
                "category": "payment_discipline",
                "severity": "HIGH" if bounced >= 10 else "MEDIUM",
                "score_impact": 15 if bounced >= 10 else 8,
                "detail": f"{bounced} bounced cheques detected — poor payment discipline.",
                "values": {"bounced_checks": bounced},
            }
        return {}

    def _check_overdraft_pattern(self, data: Dict) -> Dict[str, Any]:
        """Rule 8: Frequent overdrafts."""
        od = data["bank"]["overdraft_instances"]
        if od >= 3:
            return {
                "flag": True,
                "rule": "Frequent Overdrafts",
                "category": "liquidity_stress",
                "severity": "MEDIUM",
                "score_impact": 10,
                "detail": f"{od} overdraft instances — indicates cash-flow stress.",
                "values": {"overdraft_instances": od},
            }
        return {}

    def _check_debt_equity_sanity(self, data: Dict) -> Dict[str, Any]:
        """Rule 9: Debt-to-equity ratio from Annual Report."""
        debt = data["annual_report"]["total_debt_cr"]
        equity = data["annual_report"]["total_equity_cr"]
        if debt <= 0 or equity <= 0:
            return {}
        de_ratio = debt / equity
        if de_ratio > 5.0:
            return {
                "flag": True,
                "rule": "Debt-to-Equity Ratio",
                "category": "over_leverage",
                "severity": "HIGH",
                "score_impact": 18,
                "detail": f"Debt-to-Equity ratio is {de_ratio:.1f}x — excessive leverage.",
                "values": {"debt_cr": debt, "equity_cr": equity, "de_ratio": round(de_ratio, 2)},
            }
        if de_ratio > 3.0:
            return {
                "flag": True,
                "rule": "Debt-to-Equity Ratio",
                "category": "over_leverage",
                "severity": "MEDIUM",
                "score_impact": 8,
                "detail": f"Debt-to-Equity ratio is {de_ratio:.1f}x — high leverage.",
                "values": {"debt_cr": debt, "equity_cr": equity, "de_ratio": round(de_ratio, 2)},
            }
        return {}

    def _check_related_party_exposure(self, data: Dict) -> Dict[str, Any]:
        """Rule 10: Related party transactions vs revenue."""
        rpt = data["annual_report"]["related_party_transactions_cr"]
        rev = data["annual_report"]["revenue_cr"]
        if rpt <= 0 or rev <= 0:
            return {}
        ratio = rpt / rev
        if ratio > 0.25:
            return {
                "flag": True,
                "rule": "Related Party Exposure",
                "category": "related_party_risk",
                "severity": "HIGH" if ratio > 0.5 else "MEDIUM",
                "score_impact": 15 if ratio > 0.5 else 8,
                "detail": f"Related party transactions (Rs.{rpt:.1f} Cr) are {ratio:.0%} of revenue — elevated risk.",
                "values": {"rpt_cr": rpt, "revenue_cr": rev, "ratio": round(ratio, 2)},
            }
        return {}

    def _check_contingent_liabilities(self, data: Dict) -> Dict[str, Any]:
        """Rule 11: Contingent liabilities vs equity."""
        cl = data["annual_report"]["contingent_liabilities_cr"]
        equity = data["annual_report"]["total_equity_cr"]
        if cl <= 0:
            return {}
        if equity > 0 and cl / equity > 0.5:
            return {
                "flag": True,
                "rule": "Contingent Liabilities",
                "category": "hidden_liabilities",
                "severity": "HIGH",
                "score_impact": 15,
                "detail": f"Contingent liabilities (Rs.{cl:.1f} Cr) exceed 50% of equity (Rs.{equity:.1f} Cr).",
                "values": {"contingent_cr": cl, "equity_cr": equity},
            }
        return {}

    def _check_auditor_opinion(self, data: Dict) -> Dict[str, Any]:
        """Rule 12: Non-clean audit opinion."""
        opinion = data["annual_report"]["auditor_opinion"].lower()
        if opinion in ("qualified", "adverse", "disclaimer"):
            severity = "HIGH" if opinion in ("adverse", "disclaimer") else "MEDIUM"
            return {
                "flag": True,
                "rule": "Auditor Opinion",
                "category": "audit_risk",
                "severity": severity,
                "score_impact": 20 if severity == "HIGH" else 10,
                "detail": f"Audit opinion is '{opinion.title()}' — indicates financial reporting concerns.",
                "values": {"auditor_opinion": opinion.title()},
            }
        return {}

    def _check_purchase_to_sales_ratio(self, data: Dict) -> Dict[str, Any]:
        """Rule 13: Purchases ≈ Sales — possible round-tripping."""
        sales = data["gst"]["sales_cr"]
        purchases = data["gst"]["purchases_cr"]
        if sales <= 0 or purchases <= 0:
            return {}
        ratio = purchases / sales
        if 0.85 < ratio < 1.15:
            return {
                "flag": True,
                "rule": "Purchase-to-Sales Parity",
                "category": "circular_trading",
                "severity": "MEDIUM",
                "score_impact": 12,
                "detail": f"GST purchases (Rs.{purchases:.1f} Cr) suspiciously close to sales (Rs.{sales:.1f} Cr) — ratio {ratio:.2f}. Possible round-tripping.",
                "values": {"purchases_cr": purchases, "sales_cr": sales, "ratio": round(ratio, 2)},
            }
        return {}

    def _check_net_cash_retention(self, data: Dict) -> Dict[str, Any]:
        """Rule 14: Bank outflows ≈ inflows — minimal cash retention."""
        inflows = data["bank"]["total_inflows_cr"]
        outflows = data["bank"]["total_outflows_cr"]
        if inflows <= 0 or outflows <= 0:
            return {}
        ratio = outflows / inflows
        if 0.90 < ratio < 1.10:
            return {
                "flag": True,
                "rule": "Minimal Net Cash Retention",
                "category": "circular_trading",
                "severity": "MEDIUM",
                "score_impact": 10,
                "detail": f"Bank outflows (Rs.{outflows:.1f} Cr) nearly equal inflows (Rs.{inflows:.1f} Cr) — ratio {ratio:.2f}. Minimal cash retained.",
                "values": {"outflows_cr": outflows, "inflows_cr": inflows, "ratio": round(ratio, 2)},
            }
        return {}

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 70:
            return "CRITICAL"
        if score >= 45:
            return "HIGH"
        if score >= 25:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _build_summary(anomalies: List, score: int, level: str, sources: List) -> str:
        n = len(anomalies)
        if n == 0:
            return f"No anomalies detected across {len(sources)} data sources. Financial data appears consistent."
        categories = set(a.get("category", "") for a in anomalies)
        high_count = sum(1 for a in anomalies if a.get("severity") == "HIGH")
        return (
            f"Cross-verification flagged {n} anomalies (Fraud Risk Score: {score}/100, Level: {level}). "
            f"{high_count} HIGH severity issues found across categories: {', '.join(categories)}. "
            f"Based on {len(sources)} independent data sources: {', '.join(sources)}."
        )
