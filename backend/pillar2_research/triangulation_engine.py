"""
Triangulation Engine — Cross-references extracted document data with
secondary research signals to produce confidence-rated findings.

Creates a matrix: each financial metric is compared against research
signals to identify confirmations, contradictions, and gaps.
"""
from typing import Dict, Any, List, Optional
import json


class TriangulationEngine:
    """Cross-verify extracted financial data against alternate-data research."""

    def triangulate(
        self,
        financials: Dict[str, Any],
        research_bundle: Dict[str, Any],
        extracted_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Args:
            financials: Normalized financial metrics (from scoring / extraction)
            research_bundle: Output of SecondaryResearchEngine.run_full_research()
            extracted_fields: Raw extracted field values per doc type
        Returns:
            Triangulation matrix with confirmations, contradictions, gaps.
        """
        findings: List[Dict[str, Any]] = []

        # ── 1. Revenue consistency ────────────────────────────────
        gst_sales = financials.get("gst_sales_cr", 0) or 0
        bank_inflows = financials.get("bank_inflows_cr", 0) or 0
        ar_revenue = financials.get("revenue_cr", 0) or 0
        news_sentiment = research_bundle.get("news", {}).get("overall_sentiment", "NEUTRAL")

        if gst_sales > 0 and bank_inflows > 0:
            variance = abs(gst_sales - bank_inflows) / gst_sales * 100
            if variance <= 5:
                findings.append(_finding(
                    "Revenue Cross-Check", "CONFIRMED",
                    f"GST sales (₹{gst_sales:.1f}Cr) aligns with bank inflows (₹{bank_inflows:.1f}Cr) — variance {variance:.1f}%",
                    confidence=0.95, sources=["GST Return", "Bank Statement"],
                ))
            elif variance <= 15:
                findings.append(_finding(
                    "Revenue Cross-Check", "WARNING",
                    f"Moderate gap between GST (₹{gst_sales:.1f}Cr) and bank (₹{bank_inflows:.1f}Cr) — {variance:.1f}% variance",
                    confidence=0.75, sources=["GST Return", "Bank Statement"],
                ))
            else:
                findings.append(_finding(
                    "Revenue Cross-Check", "CONTRADICTION",
                    f"Significant mismatch: GST ₹{gst_sales:.1f}Cr vs Bank ₹{bank_inflows:.1f}Cr — {variance:.1f}% variance",
                    confidence=0.90, sources=["GST Return", "Bank Statement"],
                ))
        else:
            findings.append(_finding(
                "Revenue Cross-Check", "GAP",
                "Missing GST or bank data — cannot cross-verify revenue",
                confidence=0.0, sources=[],
            ))

        # ── 2. Profitability vs News ──────────────────────────────
        if ar_revenue > 0 and news_sentiment == "NEGATIVE":
            findings.append(_finding(
                "Profitability vs Media", "WARNING",
                f"Annual report shows ₹{ar_revenue:.1f}Cr revenue but media sentiment is NEGATIVE — investigate downside risks",
                confidence=0.70, sources=["Annual Report", "News"],
            ))
        elif ar_revenue > 0 and news_sentiment == "POSITIVE":
            findings.append(_finding(
                "Profitability vs Media", "CONFIRMED",
                f"Revenue of ₹{ar_revenue:.1f}Cr supported by positive media coverage",
                confidence=0.80, sources=["Annual Report", "News"],
            ))

        # ── 3. Debt vs Legal exposure ─────────────────────────────
        de = financials.get("debt_to_equity", 0)
        legal = research_bundle.get("legal", {})
        case_count = legal.get("case_count", 0)
        if de > 2.0 and case_count > 0:
            findings.append(_finding(
                "Leverage + Litigation", "CONTRADICTION",
                f"High leverage (D/E {de:.2f}) compounded by {case_count} legal case(s) — elevated default risk",
                confidence=0.85, sources=["Financial Statements", "Legal Database"],
            ))
        elif de > 2.0:
            findings.append(_finding(
                "Leverage Check", "WARNING",
                f"Debt-to-equity {de:.2f} is elevated — no litigation found to compound risk",
                confidence=0.75, sources=["Financial Statements"],
            ))
        elif case_count > 0:
            findings.append(_finding(
                "Litigation Exposure", "WARNING",
                f"{case_count} legal case(s) found — leverage is manageable (D/E {de:.2f})",
                confidence=0.75, sources=["Legal Database"],
            ))

        # ── 4. DSCR vs Cash Flow ──────────────────────────────────
        dscr = financials.get("dscr", 0)
        ocf = financials.get("operating_cash_flow_cr", 0)
        if dscr >= 1.5 and ocf > 0:
            findings.append(_finding(
                "Cash Flow Adequacy", "CONFIRMED",
                f"DSCR {dscr:.2f} supported by positive operating cash flow ₹{ocf:.1f}Cr",
                confidence=0.90, sources=["Bank Statement", "Financial Ratios"],
            ))
        elif dscr < 1.0:
            findings.append(_finding(
                "Cash Flow Adequacy", "CONTRADICTION",
                f"DSCR {dscr:.2f} below 1.0 — debt service capacity questionable",
                confidence=0.90, sources=["Financial Ratios"],
            ))

        # ── 5. Market sentiment vs Sector ─────────────────────────
        mkt = research_bundle.get("market_sentiment", {}).get("overall_sentiment", "NEUTRAL")
        macro = research_bundle.get("macro_trends", {}).get("overall_sentiment", "NEUTRAL")
        if mkt == "NEGATIVE" and macro == "NEGATIVE":
            findings.append(_finding(
                "Market & Macro Alignment", "CONTRADICTION",
                "Both market sentiment and macro trends are negative — systemic risk elevated",
                confidence=0.80, sources=["Market News", "Macro Data"],
            ))
        elif mkt == "POSITIVE" and macro == "POSITIVE":
            findings.append(_finding(
                "Market & Macro Alignment", "CONFIRMED",
                "Market sentiment and macro conditions are both favorable",
                confidence=0.80, sources=["Market News", "Macro Data"],
            ))
        elif mkt != macro and mkt != "NEUTRAL" and macro != "NEUTRAL":
            findings.append(_finding(
                "Market vs Macro Divergence", "WARNING",
                f"Market sentiment ({mkt}) diverges from macro outlook ({macro})",
                confidence=0.65, sources=["Market News", "Macro Data"],
            ))

        # ── 6. Management / Promoter ──────────────────────────────
        mgmt = research_bundle.get("management", {}).get("overall_sentiment", "NEUTRAL")
        if mgmt == "NEGATIVE":
            findings.append(_finding(
                "Management Reputation", "CONTRADICTION",
                "Adverse information about promoters/management detected in public sources",
                confidence=0.75, sources=["Promoter Research"],
            ))
        elif mgmt == "POSITIVE":
            findings.append(_finding(
                "Management Reputation", "CONFIRMED",
                "Positive promoter/management reputation in public sources",
                confidence=0.75, sources=["Promoter Research"],
            ))

        # ── 7. Regulatory ────────────────────────────────────────
        reg = research_bundle.get("regulatory", {})
        if reg.get("has_issues"):
            findings.append(_finding(
                "Regulatory Compliance", "CONTRADICTION",
                f"{len(reg.get('flags', []))} regulatory concern(s): {'; '.join(reg.get('flags', [])[:2])}",
                confidence=0.80, sources=["Regulatory Sources"],
            ))
        else:
            findings.append(_finding(
                "Regulatory Compliance", "CONFIRMED",
                "No regulatory penalties or compliance flags detected",
                confidence=0.70, sources=["Regulatory Sources"],
            ))

        # ── Summary ──────────────────────────────────────────────
        confirmed = sum(1 for f in findings if f["status"] == "CONFIRMED")
        contradictions = sum(1 for f in findings if f["status"] == "CONTRADICTION")
        warnings = sum(1 for f in findings if f["status"] == "WARNING")
        gaps = sum(1 for f in findings if f["status"] == "GAP")

        if contradictions >= 3:
            confidence_grade = "LOW"
        elif contradictions >= 1 or warnings >= 3:
            confidence_grade = "MODERATE"
        else:
            confidence_grade = "HIGH"

        return {
            "findings": findings,
            "summary": {
                "confirmed": confirmed,
                "contradictions": contradictions,
                "warnings": warnings,
                "gaps": gaps,
                "total": len(findings),
                "confidence_grade": confidence_grade,
            },
        }


def _finding(
    metric: str, status: str, detail: str,
    confidence: float, sources: List[str],
) -> Dict[str, Any]:
    return {
        "metric": metric,
        "status": status,       # CONFIRMED | WARNING | CONTRADICTION | GAP
        "detail": detail,
        "confidence": round(confidence, 2),
        "sources": sources,
    }
