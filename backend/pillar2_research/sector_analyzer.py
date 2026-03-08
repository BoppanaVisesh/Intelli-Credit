"""
Sector Analyzer - Analyze industry-specific trends and risks
"""
from typing import Dict, Any, List


class SectorAnalyzer:
    """
    Analyze sector-specific factors:
    - Industry trends
    - Regulatory changes
    - Market conditions
    - Competitive landscape
    """
    
    def __init__(self):
        self.sector_data = self._load_sector_data()
    
    def analyze_sector(self, sector: str) -> Dict[str, Any]:
        """
        Analyze sector conditions and risks
        """
        
        sector_info = self.sector_data.get(sector, self._get_default_sector_info(sector))
        
        return {
            'sector': sector,
            'outlook': sector_info['outlook'],
            'growth_rate': sector_info['growth_rate'],
            'headwinds': sector_info['headwinds'],
            'tailwinds': sector_info['tailwinds'],
            'regulatory_changes': sector_info['regulatory_changes'],
            'risk_score': sector_info['risk_score'],
            'recommendation': self._get_sector_recommendation(sector_info['risk_score'])
        }
    
    def _load_sector_data(self) -> Dict[str, Dict]:
        """
        Load sector-specific data
        In production: fetch from database or external API
        """
        
        return {
            'Industrial Manufacturing': {
                'outlook': 'Stable',
                'growth_rate': 6.5,
                'headwinds': [
                    'Raw material price volatility',
                    'Increased import tariffs',
                    'Global supply chain disruptions'
                ],
                'tailwinds': [
                    'Government PLI schemes',
                    'Domestic demand recovery',
                    'Infrastructure spending'
                ],
                'regulatory_changes': 'Recent RBI tightening on unsecured lending does not directly impact this manufacturing unit, but raw material import tariffs have increased.',
                'risk_score': 25
            },
            'Textiles': {
                'outlook': 'Challenging',
                'growth_rate': 3.2,
                'headwinds': [
                    'Cotton price fluctuations',
                    'Export market slowdown',
                    'Competition from Bangladesh'
                ],
                'tailwinds': [
                    'Government export incentives',
                    'Shift to domestic brands'
                ],
                'regulatory_changes': 'New sustainability norms being implemented',
                'risk_score': 45
            },
            'IT Services': {
                'outlook': 'Positive',
                'growth_rate': 12.8,
                'headwinds': [
                    'US recession fears',
                    'Client budget cuts'
                ],
                'tailwinds': [
                    'Digital transformation demand',
                    'Cloud migration projects',
                    'AI/ML adoption'
                ],
                'regulatory_changes': 'No major regulatory changes',
                'risk_score': 15
            }
        }
    
    def _get_default_sector_info(self, sector: str = "") -> Dict[str, Any]:
        """
        Default sector info for unknown sectors
        Uses keyword matching to assign approximate risk scores
        """
        
        # Dynamic risk scoring based on sector keywords
        sector_lower = sector.lower()
        
        # Low risk sectors (15-25)
        if any(keyword in sector_lower for keyword in ['technology', 'it', 'software', 'pharma', 'healthcare']):
            risk_score = 20
            outlook = 'Positive'
            growth_rate = 10.0
        # Medium risk sectors (30-45)
        elif any(keyword in sector_lower for keyword in ['manufacturing', 'construction', 'real estate', 'retail']):
            risk_score = 35
            outlook = 'Stable'
            growth_rate = 5.0
        # High risk sectors (50-70)
        elif any(keyword in sector_lower for keyword in ['steel', 'mining', 'aviation', 'hospitality', 'tourism']):
            risk_score = 55
            outlook = 'Challenging'
            growth_rate = 2.0
        else:
            # Unknown sector
            risk_score = 30
            outlook = 'Unknown'
            growth_rate = 0.0
        
        return {
            'outlook': outlook,
            'growth_rate': growth_rate,
            'headwinds': [f'{sector} sector dynamics under monitoring'],
            'tailwinds': ['Sector-specific opportunities'],
            'regulatory_changes': 'No major regulatory changes identified',
            'risk_score': risk_score
        }
    
    def _get_sector_recommendation(self, risk_score: int) -> str:
        """Get recommendation based on sector risk score"""
        if risk_score >= 50:
            return 'HIGH RISK: Sector facing significant challenges. Extra caution advised.'
        elif risk_score >= 30:
            return 'MODERATE RISK: Monitor sector conditions closely.'
        else:
            return 'LOW RISK: Favorable sector conditions.'
    
    def compare_with_peers(self, company_metrics: Dict, sector: str) -> Dict[str, Any]:
        """
        Compare company metrics with sector benchmarks
        Uses industry-standard thresholds for comparison
        """
        
        # Industry-standard benchmarks
        benchmarks = {
            'dscr': {'excellent': 2.0, 'good': 1.5, 'average': 1.25, 'poor': 1.0},
            'debt_equity': {'excellent': 0.5, 'good': 1.0, 'average': 2.0, 'poor': 3.0},
            'current_ratio': {'excellent': 2.0, 'good': 1.5, 'average': 1.2, 'poor': 1.0}
        }
        
        # Calculate percentiles based on benchmarks
        dscr = company_metrics.get('dscr', 1.0)
        debt_equity = company_metrics.get('debt_to_equity', 2.0)
        current_ratio = company_metrics.get('current_ratio', 1.2)
        
        # Simple percentile calculation (higher DSCR and current_ratio = better, lower D/E = better)
        dscr_percentile = min(100, int((dscr / benchmarks['dscr']['good']) * 60))
        de_percentile = min(100, int((benchmarks['debt_equity']['good'] / max(debt_equity, 0.1)) * 60))
        cr_percentile = min(100, int((current_ratio / benchmarks['current_ratio']['good']) * 60))
        
        avg_percentile = (dscr_percentile + de_percentile + cr_percentile) / 3
        
        if avg_percentile >= 70:
            standing = 'Above Average'
        elif avg_percentile >= 40:
            standing = 'Average'
        else:
            standing = 'Below Average'
        
        return {
            'dscr_percentile': dscr_percentile,
            'debt_equity_percentile': de_percentile,
            'current_ratio_percentile': cr_percentile,
            'overall_standing': standing,
            'note': 'Compared against industry-standard benchmarks'
        }
