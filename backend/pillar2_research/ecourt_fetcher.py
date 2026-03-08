"""
eCourts Fetcher - Search legal databases for litigation history using REAL web search
"""
from typing import Dict, List, Any, Optional
import requests
import os


class ECourtsFetcher:
    """
    Fetch litigation data using REAL web search (Tavily API)
    """
    
    def __init__(self, tavily_api_key: Optional[str] = None, llm=None):
        self.api_key = tavily_api_key or os.getenv('TAVILY_API_KEY')
        self.llm = llm
        self.tavily_url = "https://api.tavily.com/search"
    
    def search_litigation(self, company_name: str, cin: str) -> List[Dict[str, Any]]:
        """
        Search for litigation involving the company using REAL web search
        Uses Tavily to find news and public records about litigation
        """
        
        if not self.api_key:
            print("    ⚠️  No Tavily API key - cannot search litigation")
            return []
        
        try:
            # REAL Tavily API call for litigation search
            query = f"{company_name} litigation lawsuit court case legal proceedings"
            print(f"    🔍 Searching litigation: {company_name}...")
            
            response = requests.post(
                self.tavily_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                litigation_records = []
                for r in results:
                    title = r.get('title', '')
                    content = r.get('content', '')
                    
                    # Check if it's actually about litigation
                    litigation_keywords = ['lawsuit', 'court', 'legal', 'case', 'litigation', 'suit', 'petition']
                    if any(kw in (title + content).lower() for kw in litigation_keywords):
                        litigation_records.append({
                            'source': 'Web Search (Tavily)',
                            'case_number': 'N/A',
                            'summary': content[:200],
                            'case_type': 'Unknown',
                            'court': 'Unknown',
                            'filing_date': 'Unknown',
                            'status': 'Unknown',
                            'amount_involved_cr': 0.0,
                            'severity_penalty': -10,
                            'url': r.get('url', '')
                        })
                
                print(f"    ✓ Found {len(litigation_records)} litigation records")
                return litigation_records
            else:
                print(f"    ⚠️  Tavily API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"    ❌ Litigation search failed: {str(e)}")
            return []
    
    def search_nclt_cases(self, company_name: str, cin: str) -> List[Dict[str, Any]]:
        """
        Search NCLT (National Company Law Tribunal) cases using web search
        """
        
        if not self.api_key:
            return []
        
        try:
            query = f"{company_name} NCLT insolvency bankruptcy IBC proceedings"
            
            response = requests.post(
                self.tavily_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                nclt_cases = []
                for r in results:
                    content = r.get('content', '')
                    if 'nclt' in content.lower() or 'insolvency' in content.lower():
                        nclt_cases.append({
                            'source': 'NCLT Web Search',
                            'summary': content[:200],
                            'url': r.get('url', '')
                        })
                
                return nclt_cases
            else:
                return []
                
        except Exception as e:
            print(f"    Warning: NCLT search failed: {str(e)}")
            return []
    
    def calculate_litigation_risk(self, litigation_records: List[Dict]) -> Dict[str, Any]:
        """
        Calculate overall litigation risk score
        """
        
        if not litigation_records:
            return {
                'risk_level': 'LOW',
                'total_penalty': 0,
                'case_count': 0
            }
        
        total_penalty = sum(record.get('severity_penalty', 0) for record in litigation_records)
        case_count = len(litigation_records)
        
        # Determine risk level
        if case_count >= 5 or total_penalty <= -30:
            risk_level = 'HIGH'
        elif case_count >= 2 or total_penalty <= -15:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_level': risk_level,
            'total_penalty': total_penalty,
            'case_count': case_count,
            'recommendation': self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on litigation risk"""
        recommendations = {
            'HIGH': 'Significant litigation risk. Detailed legal review required before approval.',
            'MEDIUM': 'Moderate litigation exposure. Monitor closely and consider legal opinion.',
            'LOW': 'Minimal litigation risk. Standard legal review sufficient.'
        }
        return recommendations.get(risk_level, '')
