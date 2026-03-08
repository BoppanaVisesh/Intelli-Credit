"""
Promoter Profiler - Research company promoters using REAL web sources
"""
from typing import Dict, List, Any, Optional
import os
import requests


class PromoterProfiler:
    """
    Research promoters using:
    - Web search (Tavily API) - REAL
    - Sentiment analysis (Gemini LLM) - REAL
    - Past company affiliations
    - Regulatory filings
    """
    
    def __init__(self, tavily_api_key: Optional[str] = None, llm=None):
        self.api_key = tavily_api_key or os.getenv('TAVILY_API_KEY')
        self.llm = llm
        self.tavily_url = "https://api.tavily.com/search"
    
    def profile_promoter(self, promoter_name: str, company_name: str) -> Dict[str, Any]:
        """
        Main promoter profiling function - uses REAL Tavily API and sentiment analysis
        """
        
        # Search web using Tavily API
        search_results = self._search_web(promoter_name, company_name)
        sentiment = self._analyze_sentiment(search_results)
        
        return {
            'name': promoter_name,
            'finding': self._summarize_findings(search_results),
            'sentiment': sentiment,
            'sources': search_results.get('sources', []),
            'risk_score': self._calculate_risk_score(sentiment, search_results)
        }
    
    def _search_web(self, promoter_name: str, company_name: str) -> Dict[str, Any]:
        """
        Search web for promoter information using REAL Tavily API
        """
        
        if not self.api_key:
            print("    ⚠️  No Tavily API key - using fallback")
            return {
                'findings': 'No API key provided for web search',
                'sources': [],
                'summary': 'Limited information available'
            }
        
        try:
            # REAL Tavily API call
            query = f"{promoter_name} {company_name} director litigation fraud criminal"
            print(f"    🔍 Searching web: {query[:50]}...")
            
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
                
                findings_text = "\n".join([
                    f"{r.get('title', '')}: {r.get('content', '')}" 
                    for r in results[:3]
                ])
                
                sources = [r.get('url', '') for r in results if r.get('url')]
                
                print(f"    ✓ Found {len(results)} web results")
                
                return {
                    'findings': findings_text or 'No significant findings',
                    'sources': sources,
                    'summary': data.get('content', 'Web search completed')
                }
            else:
                print(f"    ⚠️  Tavily API error: {response.status_code}")
                return {
                    'findings': 'API error',
                    'sources': [],
                    'summary': 'Search temporarily unavailable'
                }
                
        except Exception as e:
            print(f"    ❌ Web search failed: {str(e)}")
            return {
                'findings': 'Search failed',
                'sources': [],
                'summary': str(e)
            }
    
    def _analyze_sentiment(self, search_results: Dict) -> str:
        """
        Analyze sentiment from search results using REAL Gemini LLM
        """
        
        findings = search_results.get('findings', '')
        
        if not findings or not self.llm:
            # Fallback to keyword matching
            negative_keywords = ['fraud', 'scam', 'default', 'bankruptcy', 'lawsuit', 'criminal', 'arrest']
            positive_keywords = ['award', 'recognition', 'successful', 'innovative', 'leader', 'growth']
            
            findings_lower = findings.lower()
            
            has_negative = any(word in findings_lower for word in negative_keywords)
            has_positive = any(word in findings_lower for word in positive_keywords)
            
            if has_negative:
                return 'NEGATIVE'
            elif has_positive:
                return 'POSITIVE'
            else:
                return 'NEUTRAL'
        
        try:
            # REAL Gemini API sentiment analysis
            prompt = f"""Analyze the sentiment of this promoter research findings.
            Classify as: POSITIVE, NEGATIVE, or NEUTRAL
            
            Findings: {findings[:500]}
            
            Return only one word: POSITIVE, NEGATIVE, or NEUTRAL
            """
            
            result = self.llm.generate_text(prompt, max_tokens=50, temperature=0.1)
            sentiment = result.strip().upper()
            
            if sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
                print(f"    🤖 LLM Sentiment: {sentiment}")
                return sentiment
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            print(f"    ⚠️  LLM sentiment analysis failed: {str(e)}")
            return 'NEUTRAL'
    
    def _summarize_findings(self, search_results: Dict) -> str:
        """Summarize web search findings"""
        return search_results.get('findings', 'No significant findings')
    
    def _calculate_risk_score(self, sentiment: str, search_results: Dict) -> int:
        """Calculate risk score based on findings"""
        score_map = {
            'POSITIVE': 10,
            'NEUTRAL': 0,
            'NEGATIVE': -20
        }
        return score_map.get(sentiment, 0)
