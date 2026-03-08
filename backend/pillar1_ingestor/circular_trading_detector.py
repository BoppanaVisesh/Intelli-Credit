"""
Circular Trading Detector - Identify suspicious transaction patterns
"""
from typing import Dict, List, Any


class CircularTradingDetector:
    """
    Detect circular trading patterns by cross-checking:
    - GST sales vs Bank inflows
    - Unusual vendor/customer patterns
    - Round-tripping indicators
    """
    
    def detect_circular_trading(
        self,
        gst_sales: float,
        bank_inflows: float,
        gst_purchases: float,
        bank_outflows: float
    ) -> Dict[str, Any]:
        """
        Main detection logic
        """
        
        # Calculate variance
        revenue_variance_percent = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0
        
        # Simple heuristics for circular trading risk
        risk_score = 0
        flags = []
        
        # Check 1: High variance between GST and Bank (>10% is suspicious)
        if revenue_variance_percent > 10:
            risk_score += 30
            flags.append("High variance between GST sales and bank inflows")
        
        # Check 2: Sales and purchases are too similar (possible round-tripping)
        if gst_sales > 0 and gst_purchases > 0:
            purchase_to_sales_ratio = gst_purchases / gst_sales
            if 0.85 < purchase_to_sales_ratio < 1.15:
                risk_score += 20
                flags.append("Suspiciously similar sales and purchase amounts")
        
        # Check 3: Bank inflows and outflows are too similar
        if bank_inflows > 0 and bank_outflows > 0:
            flow_ratio = bank_outflows / bank_inflows
            if 0.90 < flow_ratio < 1.10:
                risk_score += 15
                flags.append("Minimal net cash retention")
        
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
            'gst_vs_bank_variance_percent': revenue_variance_percent,
            'red_flag_triggered': risk_score >= 50,
            'flags': flags,
            'recommendation': self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            'HIGH': 'Conduct detailed investigation. Request vendor/customer confirmations.',
            'MEDIUM': 'Review transaction patterns closely. May require additional verification.',
            'LOW': 'Transaction patterns appear normal. Standard monitoring recommended.'
        }
        return recommendations.get(risk_level, '')
    
    def analyze_vendor_concentration(self, vendor_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze vendor concentration (placeholder for future enhancement)
        """
        return {
            'top_vendor_concentration': 0.0,
            'unusual_patterns': []
        }
