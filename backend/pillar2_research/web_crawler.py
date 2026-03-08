"""
Web Crawler
General-purpose web search and content extraction using Tavily API
"""

import os
from typing import List, Dict, Any
from tavily import TavilyClient


class WebCrawler:
    """
    Web crawler using Tavily Search API
    Provides general web search capabilities for research agent
    """
    
    def __init__(self, tavily_api_key: str = None):
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
        else:
            self.client = None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search
        
        Returns:
            List of results with title, url, content
        """
        
        if not self.client:
            print("⚠️ TAVILY_API_KEY not configured")
            return []
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0.0)
                })
            
            print(f"🔍 Found {len(results)} search results for: {query}")
            return results
            
        except Exception as e:
            print(f"❌ Web search failed: {str(e)}")
            return []
    
    def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        Search for general company information
        
        Returns:
            Aggregated company information
        """
        
        query = f"{company_name} company India business information"
        results = self.search(query, max_results=3)
        
        if not results:
            return {
                'company_name': company_name,
                'info_found': False,
                'sources': []
            }
        
        # Aggregate information
        return {
            'company_name': company_name,
            'info_found': True,
            'summary': results[0]['content'] if results else '',
            'sources': [
                {'title': r['title'], 'url': r['url']}
                for r in results
            ]
        }
    
    def search_sector_news(self, sector: str) -> List[Dict[str, Any]]:
        """
        Search for recent sector/industry news
        
        Returns:
            List of news articles
        """
        
        query = f"{sector} industry India news trends 2024"
        results = self.search(query, max_results=5)
        
        return results
