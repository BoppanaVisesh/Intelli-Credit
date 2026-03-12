"""
Secondary Research Engine — Programmatic 360° alternate-data aggregation.

Scrapes and synthesizes:
  1. News & Media Sentiment  (Tavily)
  2. Legal / Litigation       (Tavily)
  3. Market Sentiment         (Tavily)
  4. Macro / Sector Trends    (internal + Tavily)
  5. Regulatory & Compliance  (Tavily)
  6. Promoter / Management    (Tavily)

Returns a unified SecondaryResearchBundle dict ready for triangulation.
"""
from typing import Dict, Any, List, Optional
import os
import requests
from datetime import datetime


class SecondaryResearchEngine:
    """Aggregate alternate data from multiple web sources into one bundle."""

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.tavily_url = "https://api.tavily.com/search"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_full_research(
        self,
        company_name: str,
        sector: str,
        cin: str = "",
        promoter_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run all 6 research modules and return a unified bundle."""
        bundle: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "company": company_name,
            "sector": sector,
        }

        bundle["news"] = self._research_news(company_name)
        bundle["legal"] = self._research_legal(company_name, cin)
        bundle["market_sentiment"] = self._research_market_sentiment(company_name, sector)
        bundle["macro_trends"] = self._research_macro(sector)
        bundle["regulatory"] = self._research_regulatory(company_name, sector)
        bundle["management"] = self._research_management(company_name, promoter_names or [])

        # Aggregate risk
        bundle["overall_signals"] = self._aggregate_signals(bundle)
        return bundle

    # ------------------------------------------------------------------
    # 1. News & Media
    # ------------------------------------------------------------------
    def _research_news(self, company: str) -> Dict[str, Any]:
        articles = self._tavily_search(
            f"{company} latest news business updates India",
            domains=["economictimes.indiatimes.com", "livemint.com",
                     "moneycontrol.com", "business-standard.com", "reuters.com"],
            max_results=8,
        )
        pos, neg, neu = 0, 0, 0
        risk_alerts: List[str] = []
        for a in articles:
            s = self._sentiment(a.get("content", ""))
            a["sentiment"] = s
            if s == "POSITIVE":
                pos += 1
            elif s == "NEGATIVE":
                neg += 1
                # check for risk keywords
                txt = (a.get("title", "") + " " + a.get("content", "")).lower()
                for kw, msg in _NEWS_RISKS.items():
                    if kw in txt and msg not in risk_alerts:
                        risk_alerts.append(msg)
            else:
                neu += 1

        overall = "POSITIVE" if pos > neg else ("NEGATIVE" if neg > pos else "NEUTRAL")
        return {
            "articles": articles,
            "positive": pos, "negative": neg, "neutral": neu,
            "overall_sentiment": overall,
            "risk_alerts": risk_alerts,
        }

    # ------------------------------------------------------------------
    # 2. Legal / Litigation
    # ------------------------------------------------------------------
    def _research_legal(self, company: str, cin: str) -> Dict[str, Any]:
        litigation = self._tavily_search(
            f"{company} litigation lawsuit court case legal",
            depth="advanced", max_results=5,
        )
        nclt = self._tavily_search(
            f"{company} NCLT insolvency IBC proceedings",
            max_results=3,
        )
        cases = [a for a in litigation
                 if any(kw in (a.get("content", "")).lower()
                        for kw in ("lawsuit", "court", "legal", "case", "litigation", "suit"))]
        nclt_hits = [a for a in nclt if "nclt" in (a.get("content", "")).lower()
                     or "insolvency" in (a.get("content", "")).lower()]
        risk = "HIGH" if len(cases) >= 5 else ("MEDIUM" if len(cases) >= 2 else "LOW")
        return {
            "cases": cases,
            "nclt_cases": nclt_hits,
            "case_count": len(cases),
            "nclt_count": len(nclt_hits),
            "risk_level": risk,
            "penalty": -10 * len(cases),
        }

    # ------------------------------------------------------------------
    # 3. Market Sentiment
    # ------------------------------------------------------------------
    def _research_market_sentiment(self, company: str, sector: str) -> Dict[str, Any]:
        results = self._tavily_search(
            f"{company} {sector} stock market sentiment investor outlook India",
            max_results=5,
        )
        sentiments = [self._sentiment(a.get("content", "")) for a in results]
        pos = sentiments.count("POSITIVE")
        neg = sentiments.count("NEGATIVE")
        overall = "POSITIVE" if pos > neg else ("NEGATIVE" if neg > pos else "NEUTRAL")
        return {
            "articles": results,
            "overall_sentiment": overall,
            "positive": pos, "negative": neg,
        }

    # ------------------------------------------------------------------
    # 4. Macro / Sector Trends
    # ------------------------------------------------------------------
    def _research_macro(self, sector: str) -> Dict[str, Any]:
        results = self._tavily_search(
            f"{sector} industry India macro trends outlook GDP policy 2024 2025",
            max_results=5,
        )
        themes: List[str] = []
        for a in results:
            txt = (a.get("title", "") + " " + a.get("content", "")).lower()
            for theme, keywords in _MACRO_THEMES.items():
                if any(k in txt for k in keywords) and theme not in themes:
                    themes.append(theme)
        sentiments = [self._sentiment(a.get("content", "")) for a in results]
        pos = sentiments.count("POSITIVE")
        neg = sentiments.count("NEGATIVE")
        overall = "POSITIVE" if pos > neg else ("NEGATIVE" if neg > pos else "NEUTRAL")
        return {
            "articles": results,
            "themes": themes,
            "overall_sentiment": overall,
        }

    # ------------------------------------------------------------------
    # 5. Regulatory
    # ------------------------------------------------------------------
    def _research_regulatory(self, company: str, sector: str) -> Dict[str, Any]:
        results = self._tavily_search(
            f"{company} {sector} RBI SEBI regulation compliance penalty India",
            max_results=4,
        )
        flags: List[str] = []
        for a in results:
            txt = (a.get("content", "")).lower()
            if any(kw in txt for kw in ("penalty", "fine", "violation", "non-compliance")):
                flags.append(a.get("title", "Regulatory concern"))
        return {
            "articles": results,
            "flags": flags,
            "has_issues": len(flags) > 0,
        }

    # ------------------------------------------------------------------
    # 6. Management / Promoter
    # ------------------------------------------------------------------
    def _research_management(self, company: str, promoters: List[str]) -> Dict[str, Any]:
        queries = [f"{p} promoter director {company} reputation" for p in promoters] if promoters else [
            f"{company} promoter director management reputation India"
        ]
        all_articles: List[Dict] = []
        for q in queries[:3]:
            all_articles.extend(self._tavily_search(q, max_results=3))
        sentiments = [self._sentiment(a.get("content", "")) for a in all_articles]
        pos = sentiments.count("POSITIVE")
        neg = sentiments.count("NEGATIVE")
        overall = "POSITIVE" if pos > neg else ("NEGATIVE" if neg > pos else "NEUTRAL")
        return {
            "articles": all_articles,
            "overall_sentiment": overall,
            "positive": pos, "negative": neg,
        }

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    def _aggregate_signals(self, bundle: Dict) -> Dict[str, Any]:
        signals: List[Dict] = []

        # News
        news = bundle.get("news", {})
        if news.get("overall_sentiment") == "NEGATIVE":
            signals.append({"source": "News", "signal": "NEGATIVE", "detail": f"{news.get('negative', 0)} negative articles"})
        elif news.get("overall_sentiment") == "POSITIVE":
            signals.append({"source": "News", "signal": "POSITIVE", "detail": f"{news.get('positive', 0)} positive articles"})
        for ra in news.get("risk_alerts", []):
            signals.append({"source": "News", "signal": "RISK_ALERT", "detail": ra})

        # Legal
        legal = bundle.get("legal", {})
        if legal.get("case_count", 0) > 0:
            signals.append({"source": "Legal", "signal": legal["risk_level"], "detail": f"{legal['case_count']} cases found"})
        if legal.get("nclt_count", 0) > 0:
            signals.append({"source": "Legal", "signal": "HIGH", "detail": f"{legal['nclt_count']} NCLT/insolvency cases"})

        # Market Sentiment
        mkt = bundle.get("market_sentiment", {})
        if mkt.get("overall_sentiment") == "NEGATIVE":
            signals.append({"source": "Market", "signal": "NEGATIVE", "detail": "Negative investor sentiment"})
        elif mkt.get("overall_sentiment") == "POSITIVE":
            signals.append({"source": "Market", "signal": "POSITIVE", "detail": "Positive investor sentiment"})

        # Macro
        macro = bundle.get("macro_trends", {})
        if macro.get("overall_sentiment") == "NEGATIVE":
            signals.append({"source": "Macro", "signal": "NEGATIVE", "detail": "Challenging macro environment"})
        elif macro.get("overall_sentiment") == "POSITIVE":
            signals.append({"source": "Macro", "signal": "POSITIVE", "detail": "Favorable macro conditions"})

        # Regulatory
        reg = bundle.get("regulatory", {})
        if reg.get("has_issues"):
            signals.append({"source": "Regulatory", "signal": "NEGATIVE", "detail": f"{len(reg['flags'])} regulatory flag(s)"})

        # Management
        mgmt = bundle.get("management", {})
        if mgmt.get("overall_sentiment") == "NEGATIVE":
            signals.append({"source": "Management", "signal": "NEGATIVE", "detail": "Adverse promoter reputation"})
        elif mgmt.get("overall_sentiment") == "POSITIVE":
            signals.append({"source": "Management", "signal": "POSITIVE", "detail": "Strong management reputation"})

        risk_count = sum(1 for s in signals if s["signal"] in ("NEGATIVE", "HIGH", "RISK_ALERT"))
        pos_count = sum(1 for s in signals if s["signal"] == "POSITIVE")

        return {
            "signals": signals,
            "risk_signal_count": risk_count,
            "positive_signal_count": pos_count,
            "overall_risk": "HIGH" if risk_count >= 4 else ("MEDIUM" if risk_count >= 2 else "LOW"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _tavily_search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        depth: str = "basic",
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            payload: Dict[str, Any] = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": depth,
                "max_results": max_results,
            }
            if domains:
                payload["include_domains"] = domains
            resp = requests.post(self.tavily_url, json=payload, timeout=12)
            if resp.status_code != 200:
                return []
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                    "source": (r.get("url", "").split("/")[2] if r.get("url") else "Unknown"),
                }
                for r in resp.json().get("results", [])
            ]
        except Exception:
            return []

    @staticmethod
    def _sentiment(text: str) -> str:
        t = text.lower()
        pos_kw = ["growth", "profit", "expansion", "success", "record", "strong",
                   "positive", "gained", "increase", "upgrade", "outperform"]
        neg_kw = ["loss", "decline", "bankruptcy", "fraud", "lawsuit", "investigation",
                   "closure", "layoffs", "default", "crisis", "downgrade", "debt"]
        p = sum(1 for k in pos_kw if k in t)
        n = sum(1 for k in neg_kw if k in t)
        return "POSITIVE" if p > n else ("NEGATIVE" if n > p else "NEUTRAL")


# ── Constants ──
_NEWS_RISKS: Dict[str, str] = {
    "default": "Payment default mentioned",
    "bankruptcy": "Bankruptcy/insolvency mentioned",
    "fraud": "Fraud allegations",
    "investigation": "Under investigation",
    "lawsuit": "Legal proceedings",
    "closure": "Business closure risk",
    "layoffs": "Workforce reduction",
    "downgrade": "Credit/rating downgrade",
}

_MACRO_THEMES: Dict[str, List[str]] = {
    "Interest Rate Risk": ["interest rate", "rbi", "repo rate", "monetary policy"],
    "Inflation": ["inflation", "cpi", "wpi", "price rise"],
    "GDP Growth": ["gdp", "economic growth", "growth rate"],
    "Policy / Regulation": ["policy", "regulation", "reform", "budget"],
    "Trade / Exports": ["export", "import", "trade", "tariff"],
    "FDI / Investment": ["fdi", "investment", "capital inflow"],
    "Currency": ["rupee", "exchange rate", "forex"],
}
