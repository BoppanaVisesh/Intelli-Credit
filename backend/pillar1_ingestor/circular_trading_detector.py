"""
Circular Trading Detector - Identify suspicious transaction patterns
Uses NetworkX for graph-based cycle detection and heuristic rules.
"""
from typing import Dict, List, Any

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class CircularTradingDetector:
    """
    Detect circular trading patterns by:
    1. Cross-checking GST sales vs Bank inflows
    2. Purchase-to-sales ratio analysis
    3. Cash retention analysis
    4. Graph-based cycle detection on transaction data (NetworkX)
    """

    def detect_circular_trading(
        self,
        gst_sales: float,
        bank_inflows: float,
        gst_purchases: float,
        bank_outflows: float
    ) -> Dict[str, Any]:
        """Main detection logic using financial ratios."""

        revenue_variance_percent = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0

        risk_score = 0
        flags = []

        # Check 1: High variance between GST and Bank (>10% suspicious)
        if revenue_variance_percent > 10:
            risk_score += 30
            flags.append("High variance between GST sales and bank inflows")

        # Check 2: Sales ≈ purchases (round-tripping signal)
        if gst_sales > 0 and gst_purchases > 0:
            purchase_to_sales_ratio = gst_purchases / gst_sales
            if 0.85 < purchase_to_sales_ratio < 1.15:
                risk_score += 20
                flags.append("Suspiciously similar sales and purchase amounts (possible round-tripping)")

        # Check 3: Outflows ≈ inflows (minimal retention)
        if bank_inflows > 0 and bank_outflows > 0:
            flow_ratio = bank_outflows / bank_inflows
            if 0.90 < flow_ratio < 1.10:
                risk_score += 15
                flags.append("Minimal net cash retention — outflows nearly match inflows")

        # Determine risk level
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            'circular_trading_risk': risk_level,
            'risk_score': risk_score,
            'gst_vs_bank_variance_percent': round(revenue_variance_percent, 2),
            'red_flag_triggered': risk_score >= 50,
            'flags': flags,
            'recommendation': self._get_recommendation(risk_level)
        }

    def detect_transaction_cycles(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Graph-based circular trading detection using NetworkX.
        
        Args:
            transactions: List of dicts with keys:
                - from_entity: str (company/party name)
                - to_entity: str
                - amount: float (optional)
                - description: str (optional)
        
        Returns:
            Dict with cycles detected, risk score, and graph stats.
        """
        if not HAS_NETWORKX or not transactions:
            return {
                "cycles_detected": [],
                "cycle_count": 0,
                "graph_risk_score": 0,
                "risk_level": "LOW",
                "entities": 0,
                "edges": 0,
                "flags": [],
            }

        G = nx.DiGraph()

        for txn in transactions:
            src = txn.get("from_entity", "").strip()
            dst = txn.get("to_entity", "").strip()
            amt = float(txn.get("amount", 0))
            if src and dst and src != dst:
                if G.has_edge(src, dst):
                    G[src][dst]["weight"] += amt
                    G[src][dst]["count"] += 1
                else:
                    G.add_edge(src, dst, weight=amt, count=1)

        # Detect simple cycles
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception:
            cycles = []

        flags = []
        graph_score = 0

        if cycles:
            graph_score += min(len(cycles) * 15, 60)
            for cycle in cycles[:5]:  # top 5 cycles
                flags.append(f"Circular trading loop: {' -> '.join(cycle)} -> {cycle[0]}")

        # Check for strongly connected components (tight trading clusters)
        sccs = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
        if sccs:
            graph_score += min(len(sccs) * 10, 30)
            for scc in sccs[:3]:
                flags.append(f"Tight trading cluster: {', '.join(sorted(scc))}")

        # Reciprocal edges (A→B and B→A)
        reciprocal = [(u, v) for u, v in G.edges() if G.has_edge(v, u)]
        if reciprocal:
            graph_score += min(len(reciprocal) * 5, 20)
            for u, v in reciprocal[:3]:
                flags.append(f"Reciprocal transactions: {u} <-> {v}")

        graph_score = min(graph_score, 100)

        if graph_score >= 50:
            risk = "HIGH"
        elif graph_score >= 25:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "cycles_detected": [list(c) for c in cycles[:10]],
            "cycle_count": len(cycles),
            "graph_risk_score": graph_score,
            "risk_level": risk,
            "entities": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "flags": flags,
            "strongly_connected_components": [sorted(list(c)) for c in sccs[:5]],
        }

    def full_analysis(
        self,
        gst_sales: float,
        bank_inflows: float,
        gst_purchases: float,
        bank_outflows: float,
        transactions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Combined circular trading analysis: ratio checks + graph analysis.
        """
        ratio_result = self.detect_circular_trading(gst_sales, bank_inflows, gst_purchases, bank_outflows)

        graph_result = self.detect_transaction_cycles(transactions or [])

        # Combined score
        combined_score = min(100, ratio_result["risk_score"] + graph_result["graph_risk_score"])
        all_flags = ratio_result["flags"] + graph_result["flags"]

        if combined_score >= 60:
            overall_risk = "HIGH"
        elif combined_score >= 30:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        return {
            "combined_risk_score": combined_score,
            "combined_risk_level": overall_risk,
            "red_flag_triggered": combined_score >= 50,
            "all_flags": all_flags,
            "ratio_analysis": ratio_result,
            "graph_analysis": graph_result,
            "recommendation": self._get_recommendation(overall_risk),
        }

    def _get_recommendation(self, risk_level: str) -> str:
        recommendations = {
            'HIGH': 'Conduct detailed investigation. Request vendor/customer confirmations. Review related-party transaction records.',
            'MEDIUM': 'Review transaction patterns closely. May require additional verification of top vendors/customers.',
            'LOW': 'Transaction patterns appear normal. Standard monitoring recommended.'
        }
        return recommendations.get(risk_level, '')
