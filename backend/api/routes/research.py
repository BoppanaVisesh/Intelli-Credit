from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json

from api.dependencies import get_db
from core.config import get_settings
from models.application import Application
from models.research_result import ResearchResult
from pillar2_research.news_analyzer import NewsAnalyzer
from pillar2_research.ecourt_fetcher import ECourtsFetcher
from pillar2_research.promoter_profiler import PromoterProfiler
from pillar2_research.sector_analyzer import SectorAnalyzer
from pillar2_research.mca_fetcher import MCAFetcher
from pillar2_research.web_crawler import WebCrawler

router = APIRouter()


class ResearchRequest(BaseModel):
    application_id: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    promoter_names: Optional[List[str]] = None
    cin: Optional[str] = None


@router.post("/trigger-research")
async def trigger_research(
    request: ResearchRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger full external intelligence research for an application.
    Runs: News Analysis, Litigation Search, Promoter Profiling, Sector Analysis, Regulatory Check
    """
    settings = get_settings()

    application = db.query(Application).filter(
        Application.id == request.application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail=f"Application {request.application_id} not found")

    company_name = request.company_name or application.company_name
    sector = request.sector or application.sector or "General"
    cin = request.cin or application.mca_cin or ""
    promoter_names = request.promoter_names or []

    # Clear old research results
    db.query(ResearchResult).filter(
        ResearchResult.application_id == request.application_id
    ).delete()
    db.commit()

    # Initialize engines
    news_analyzer = NewsAnalyzer(api_key=settings.TAVILY_API_KEY)
    ecourts = ECourtsFetcher(tavily_api_key=settings.TAVILY_API_KEY)
    promoter_profiler = PromoterProfiler(tavily_api_key=settings.TAVILY_API_KEY)
    sector_analyzer = SectorAnalyzer()
    web_crawler = WebCrawler(tavily_api_key=settings.TAVILY_API_KEY)

    all_results = []

    # ── 1. NEWS ANALYSIS ──
    print(f"\n📰 Running News Analysis for {company_name}...")
    try:
        news_data = news_analyzer.analyze_company_news(company_name)

        news_risk = "LOW"
        if news_data.get("negative_count", 0) >= 3:
            news_risk = "HIGH"
        elif news_data.get("negative_count", 0) >= 1:
            news_risk = "MEDIUM"

        db.add(ResearchResult(
            application_id=request.application_id,
            research_type="news",
            entity_name=company_name,
            risk_level=news_risk,
            findings_summary=(
                f"Found {news_data['article_count']} articles. "
                f"Sentiment: {news_data['overall_sentiment']}. "
                f"Risk alerts: {', '.join(news_data.get('risk_alerts', [])) or 'None'}"
            ),
            findings_json=json.dumps({
                "article_count": news_data["article_count"],
                "overall_sentiment": news_data["overall_sentiment"],
                "positive_count": news_data["positive_count"],
                "negative_count": news_data["negative_count"],
                "neutral_count": news_data["neutral_count"],
                "key_topics": news_data.get("key_topics", []),
                "risk_alerts": news_data.get("risk_alerts", []),
                "articles": news_data.get("articles", [])[:5],
            }),
            sentiment=news_data["overall_sentiment"],
            severity_penalty=-5 * news_data.get("negative_count", 0),
            confidence=0.85,
        ))
        all_results.append({"type": "news", "status": "completed", "risk": news_risk})
        print(f"   ✅ News: {news_data['article_count']} articles, sentiment={news_data['overall_sentiment']}")
    except Exception as e:
        print(f"   ❌ News analysis failed: {e}")
        all_results.append({"type": "news", "status": "failed", "error": str(e)})

    # ── 2. LITIGATION SEARCH ──
    print(f"\n⚖️  Running Litigation Search for {company_name}...")
    try:
        litigation_records = ecourts.search_litigation(company_name, cin)
        nclt_cases = ecourts.search_nclt_cases(company_name, cin)
        litigation_risk = ecourts.calculate_litigation_risk(litigation_records)

        db.add(ResearchResult(
            application_id=request.application_id,
            research_type="litigation",
            entity_name=company_name,
            risk_level=litigation_risk["risk_level"],
            findings_summary=(
                f"Found {litigation_risk['case_count']} litigation records. "
                f"Risk: {litigation_risk['risk_level']}. "
                f"NCLT cases: {len(nclt_cases)}. "
                f"{litigation_risk.get('recommendation', '')}"
            ),
            findings_json=json.dumps({
                "case_count": litigation_risk["case_count"],
                "risk_level": litigation_risk["risk_level"],
                "total_penalty": litigation_risk["total_penalty"],
                "recommendation": litigation_risk.get("recommendation", ""),
                "records": litigation_records[:10],
                "nclt_cases": nclt_cases[:5],
            }),
            sentiment="NEGATIVE" if litigation_risk["risk_level"] == "HIGH" else "NEUTRAL",
            severity_penalty=litigation_risk["total_penalty"],
            confidence=0.75,
        ))
        all_results.append({"type": "litigation", "status": "completed", "risk": litigation_risk["risk_level"]})
        print(f"   ✅ Litigation: {litigation_risk['case_count']} cases, risk={litigation_risk['risk_level']}")
    except Exception as e:
        print(f"   ❌ Litigation search failed: {e}")
        all_results.append({"type": "litigation", "status": "failed", "error": str(e)})

    # ── 3. PROMOTER PROFILING ──
    if not promoter_names:
        promoter_names = [f"Promoter of {company_name}"]

    print(f"\n👤 Running Promoter Profiling for {len(promoter_names)} promoter(s)...")
    for pname in promoter_names:
        try:
            profile = promoter_profiler.profile_promoter(pname, company_name)

            promo_risk = "LOW"
            if profile.get("risk_score", 0) <= -15:
                promo_risk = "HIGH"
            elif profile.get("risk_score", 0) < 0:
                promo_risk = "MEDIUM"

            db.add(ResearchResult(
                application_id=request.application_id,
                research_type="promoter",
                entity_name=pname,
                risk_level=promo_risk,
                findings_summary=profile.get("finding", "No significant findings")[:500],
                findings_json=json.dumps({
                    "name": pname,
                    "finding": profile.get("finding", "")[:1000],
                    "sentiment": profile.get("sentiment", "NEUTRAL"),
                    "risk_score": profile.get("risk_score", 0),
                    "sources": profile.get("sources", [])[:5],
                }),
                sentiment=profile.get("sentiment", "NEUTRAL"),
                severity_penalty=profile.get("risk_score", 0),
                confidence=0.70,
                source_url=(profile.get("sources") or [None])[0],
            ))
            all_results.append({"type": "promoter", "name": pname, "status": "completed", "risk": promo_risk})
            print(f"   ✅ Promoter '{pname}': sentiment={profile.get('sentiment')}, risk={promo_risk}")
        except Exception as e:
            print(f"   ❌ Promoter profiling failed for {pname}: {e}")
            all_results.append({"type": "promoter", "name": pname, "status": "failed", "error": str(e)})

    # ── 4. SECTOR ANALYSIS ──
    print(f"\n📊 Running Sector Analysis for '{sector}'...")
    try:
        sector_data = sector_analyzer.analyze_sector(sector)

        sec_risk = "LOW"
        if sector_data.get("risk_score", 0) >= 50:
            sec_risk = "HIGH"
        elif sector_data.get("risk_score", 0) >= 30:
            sec_risk = "MEDIUM"

        outlook = sector_data.get("outlook", "Unknown")
        db.add(ResearchResult(
            application_id=request.application_id,
            research_type="sector",
            entity_name=sector,
            risk_level=sec_risk,
            findings_summary=(
                f"Sector: {sector}. Outlook: {outlook}. "
                f"Growth: {sector_data['growth_rate']}%. "
                f"Headwinds: {', '.join(sector_data.get('headwinds', []))}"
            ),
            findings_json=json.dumps(sector_data),
            sentiment="POSITIVE" if outlook == "Positive" else
                     ("NEGATIVE" if outlook == "Challenging" else "NEUTRAL"),
            severity_penalty=-sector_data.get("risk_score", 0) // 5,
            confidence=0.90,
        ))
        all_results.append({"type": "sector", "status": "completed", "risk": sec_risk})
        print(f"   ✅ Sector: outlook={outlook}, risk_score={sector_data['risk_score']}")
    except Exception as e:
        print(f"   ❌ Sector analysis failed: {e}")
        all_results.append({"type": "sector", "status": "failed", "error": str(e)})

    # ── 5. REGULATORY / CREDIT RATING CHECK ──
    print(f"\n🏛️  Running Regulatory & Credit Rating Check for {company_name}...")
    try:
        reg_results = web_crawler.search(
            f"{company_name} credit rating downgrade regulatory action SEBI RBI penalty",
            max_results=5,
        )

        if web_crawler.last_error:
            raise RuntimeError(web_crawler.last_error)

        reg_findings = []
        reg_risk = "LOW"
        for r in reg_results:
            content_lower = (r.get("title", "") + " " + r.get("content", "")).lower()
            risk_kws = ["downgrade", "penalty", "fine", "ban", "suspension", "warning", "violation"]
            if any(kw in content_lower for kw in risk_kws):
                reg_findings.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:300],
                    "url": r.get("url", ""),
                })
                reg_risk = "HIGH" if len(reg_findings) >= 2 else "MEDIUM"

        db.add(ResearchResult(
            application_id=request.application_id,
            research_type="regulatory",
            entity_name=company_name,
            risk_level=reg_risk,
            findings_summary=(
                f"Found {len(reg_findings)} regulatory/rating concerns"
                if reg_findings else "No regulatory concerns found"
            ),
            findings_json=json.dumps({
                "findings": reg_findings,
                "total_results_checked": len(reg_results),
                "concerns_found": len(reg_findings),
            }),
            sentiment="NEGATIVE" if reg_findings else "NEUTRAL",
            severity_penalty=-10 * len(reg_findings),
            confidence=0.80,
        ))
        all_results.append({"type": "regulatory", "status": "completed", "risk": reg_risk})
        print(f"   ✅ Regulatory: {len(reg_findings)} concerns, risk={reg_risk}")
    except Exception as e:
        print(f"   ❌ Regulatory check failed: {e}")
        db.add(ResearchResult(
            application_id=request.application_id,
            research_type="regulatory",
            entity_name=company_name,
            risk_level="UNKNOWN",
            findings_summary="Regulatory search unavailable (Tavily quota/config issue)",
            findings_json=json.dumps({"error": str(e)}),
            sentiment="NEUTRAL",
            severity_penalty=0,
            confidence=0.0,
        ))
        all_results.append({"type": "regulatory", "status": "failed", "error": str(e)})

    db.commit()

    # Overall risk
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in all_results:
        if r.get("status") == "completed":
            risk_counts[r.get("risk", "LOW")] += 1

    if risk_counts["HIGH"] >= 2:
        overall_risk = "HIGH"
    elif risk_counts["HIGH"] >= 1 or risk_counts["MEDIUM"] >= 2:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    completed = sum(1 for r in all_results if r["status"] == "completed")
    failed = sum(1 for r in all_results if r["status"] == "failed")

    print(f"\n{'='*60}")
    print(f"🔍 Research Complete: {completed} passed, {failed} failed")
    print(f"   Overall Risk: {overall_risk}")
    print(f"{'='*60}")

    return {
        "application_id": request.application_id,
        "status": "research_completed",
        "company_name": company_name,
        "overall_risk": overall_risk,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "results": all_results,
        "risk_summary": risk_counts,
    }


@router.get("/{application_id}/results")
async def get_research_results(
    application_id: str,
    db: Session = Depends(get_db),
):
    """Get all research results for an application, grouped by type."""

    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    results = (
        db.query(ResearchResult)
        .filter(ResearchResult.application_id == application_id)
        .order_by(ResearchResult.created_at.desc())
        .all()
    )

    if not results:
        return {
            "application_id": application_id,
            "research_completed": False,
            "results_by_type": {},
            "note": "No research completed yet. Trigger research first.",
        }

    grouped = {}
    total_penalty = 0
    for r in results:
        rtype = r.research_type or "unknown"
        if rtype not in grouped:
            grouped[rtype] = []

        findings_data = {}
        if r.findings_json:
            try:
                findings_data = json.loads(r.findings_json)
            except json.JSONDecodeError:
                findings_data = {}

        grouped[rtype].append({
            "id": r.id,
            "entity_name": r.entity_name,
            "risk_level": r.risk_level,
            "sentiment": r.sentiment,
            "findings_summary": r.findings_summary,
            "findings_data": findings_data,
            "severity_penalty": r.severity_penalty,
            "confidence": r.confidence,
            "source_url": r.source_url,
            "created_at": str(r.created_at) if r.created_at else None,
        })
        total_penalty += r.severity_penalty or 0

    risk_levels = [r.risk_level for r in results if r.risk_level]
    high_count = risk_levels.count("HIGH")
    medium_count = risk_levels.count("MEDIUM")

    if high_count >= 2:
        overall_risk = "HIGH"
    elif high_count >= 1 or medium_count >= 2:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    return {
        "application_id": application_id,
        "company_name": application.company_name,
        "research_completed": True,
        "overall_risk": overall_risk,
        "total_penalty": total_penalty,
        "result_count": len(results),
        "results_by_type": grouped,
    }
