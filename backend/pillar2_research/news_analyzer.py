"""
News Analyzer - Analyze news articles for sentiment and risks using REAL Tavily API
"""
from typing import Dict, List, Any, Optional
import os
import requests


class NewsAnalyzer:
    """
    Analyze news articles related to:
    - Company
    - Promoters
    - Sector
    Uses REAL Tavily Search API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        self.tavily_url = "https://api.tavily.com/search"
    
    def analyze_company_news(self, company_name: str) -> Dict[str, Any]:
        """
        Fetch and analyze recent news about the company using REAL Tavily API
        """
        
        articles = self._fetch_news(company_name)
        sentiment_analysis = self._analyze_bulk_sentiment(articles)
        
        return {
            'article_count': len(articles),
            'overall_sentiment': sentiment_analysis['overall'],
            'positive_count': sentiment_analysis['positive'],
            'negative_count': sentiment_analysis['negative'],
            'neutral_count': sentiment_analysis['neutral'],
            'key_topics': self._extract_topics(articles),
            'risk_alerts': self._identify_risks(articles),
            'articles': articles[:5]  # Return top 5
        }
    
    def _fetch_news(self, query: str, days: int = 90) -> List[Dict[str, Any]]:
        """
        Fetch REAL news articles using Tavily Search API
        """
        
        if not self.api_key:
            print("    ⚠️  No Tavily API key - cannot fetch news")
            return []
        
        try:
            # REAL Tavily API call
            search_query = f"{query} news recent updates"
            print(f"    🔍 Fetching news: {search_query[:50]}...")
            
            response = requests.post(
                self.tavily_url,
                json={
                    "api_key": self.api_key,
                    "query": search_query,
                    "search_depth": "basic",
                    "max_results": 10,
                    "include_domains": ["economictimes.indiatimes.com", "business-standard.com", 
                                       "livemint.com", "moneycontrol.com", "reuters.com", "bloomberg.com"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                articles = []
                for r in results:
                    # Determine sentiment from content
                    content = (r.get('title', '') + ' ' + r.get('content', '')).lower()
                    sentiment = self._detect_sentiment(content)
                    
                    articles.append({
                        'title': r.get('title', 'No title'),
                        'source': r.get('url', '').split('/')[2] if r.get('url') else 'Unknown',
                        'url': r.get('url', ''),
                        'snippet': r.get('content', '')[:200],
                        'sentiment': sentiment
                    })
                
                print(f"    ✓ Found {len(articles)} news articles")
                return articles
            else:
                print(f"    ⚠️  Tavily API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"    ❌ News fetch failed: {str(e)}")
            return []
    
    def _detect_sentiment(self, text: str) -> str:
        """
        Detect sentiment from text using keyword matching
        """
        positive_keywords = ['growth', 'profit', 'expansion', 'success', 'achievement', 
                            'record', 'strong', 'positive', 'gained', 'increase']
        negative_keywords = ['loss', 'decline', 'bankruptcy', 'fraud', 'lawsuit', 
                            'investigation', 'closure', 'layoffs', 'default', 'crisis']
        
        pos_count = sum(1 for keyword in positive_keywords if keyword in text)
        neg_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if pos_count > neg_count:
            return 'POSITIVE'
        elif neg_count > pos_count:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def _analyze_bulk_sentiment(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sentiment of multiple articles
        """
        
        if not articles:
            return {
                'overall': 'NEUTRAL',
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
        
        sentiment_counts = {
            'POSITIVE': 0,
            'NEGATIVE': 0,
            'NEUTRAL': 0
        }
        
        for article in articles:
            sentiment = article.get('sentiment', 'NEUTRAL')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Determine overall sentiment
        if sentiment_counts['POSITIVE'] > sentiment_counts['NEGATIVE']:
            overall = 'POSITIVE'
        elif sentiment_counts['NEGATIVE'] > sentiment_counts['POSITIVE']:
            overall = 'NEGATIVE'
        else:
            overall = 'NEUTRAL'
        
        return {
            'overall': overall,
            'positive': sentiment_counts['POSITIVE'],
            'negative': sentiment_counts['NEGATIVE'],
            'neutral': sentiment_counts['NEUTRAL']
        }
    
    def _extract_topics(self, articles: List[Dict]) -> List[str]:
        """
        Extract key topics from articles using simple keyword extraction
        """
        
        if not articles:
            return []
        
        # Common business topics
        topics = set()
        topic_keywords = {
            'expansion': ['expansion', 'growth', 'new facility', 'capacity'],
            'financial': ['revenue', 'profit', 'loss', 'earnings'],
            'litigation': ['lawsuit', 'court', 'legal', 'case'],
            'investment': ['funding', 'investment', 'capital', 'raise'],
            'management': ['ceo', 'director', 'appointment', 'resignation'],
            'regulation': ['regulatory', 'compliance', 'penalty', 'fine']
        }
        
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('snippet', '')).lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    topics.add(topic)
        
        return list(topics)
    
    def _identify_risks(self, articles: List[Dict]) -> List[str]:
        """
        Identify risk signals from news
        """
        
        risk_keywords = {
            'default': 'Payment default mentioned',
            'bankruptcy': 'Bankruptcy/insolvency mentioned',
            'fraud': 'Fraud allegations found',
            'investigation': 'Under investigation',
            'lawsuit': 'Legal proceedings ongoing',
            'closure': 'Business closure risk',
            'layoffs': 'Workforce reduction',
            'losses': 'Financial losses reported'
        }
        
        risks = []
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('snippet', '')).lower()
            for keyword, risk_msg in risk_keywords.items():
                if keyword in text:
                    risks.append(risk_msg)
        
        return list(set(risks))  # Remove duplicates
