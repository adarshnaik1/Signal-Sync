#!/usr/bin/env python
"""
News Sentiment Analysis Pipeline
Main entry point — mirrors Reddit sentiment workflow for financial news (Marketaux).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure package root is on path
PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE_ROOT))

from api.marketaux_client import MarketauxAPIError, MarketauxClient
from processing.aggregator import SentimentAggregator
from processing.cleaner import TextCleaner
from processing.keyword_extractor import KeywordExtractor
from processing.sentiment_processor import SentimentProcessor
from processing.summarizer import NewsSummarizer
from utils.helpers import load_environment, remove_duplicate_articles, validate_api_response

OUTPUT_DIR = PACKAGE_ROOT.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_news_sentiment_analysis(
    company_name: str,
    stock_symbol: str,
    articles_limit: int = 50,
    days: int = 7,
    save_output: bool = False,
) -> Dict[str, Any]:
    """
    Run the complete news sentiment analysis pipeline.

    USER INPUT → FETCH → VALIDATE → EXTRACT → DEDUPE → CLEAN →
    KEYWORDS → SENTIMENT → AGGREGATE → SUMMARIZE → RESULTS

    Args:
        company_name: Company display name.
        stock_symbol: Marketaux symbol (e.g. RELIANCE.NS).
        articles_limit: Max articles to fetch.
        days: Lookback window in days.
        save_output: Whether to save JSON results to output/.

    Returns:
        Full results dictionary for dashboard or export.
    """
    load_environment()
    symbol = stock_symbol.strip().upper()

    print("\n" + "=" * 60)
    print(f"News Sentiment Analysis: {company_name} ({symbol})")
    print("=" * 60)

    # --- FETCH NEWS ---
    print("\n[1/6] Fetching news from Marketaux API...")
    client = MarketauxClient()
    try:
        raw_response = client.fetch_news(
            symbol=symbol,
            limit=articles_limit,
            days=days,
        )
    except (MarketauxAPIError, ValueError) as exc:
        return {
            "error": str(exc),
            "company_name": company_name,
            "symbol": symbol,
        }

    # --- VALIDATE & EXTRACT ---
    print("[2/6] Validating API response...")
    try:
        articles = validate_api_response(raw_response)
    except ValueError as exc:
        return {"error": str(exc), "company_name": company_name, "symbol": symbol}

    if not articles:
        return {
            "error": "No articles returned for this symbol and date range.",
            "company_name": company_name,
            "symbol": symbol,
            "raw_response": raw_response,
        }

    print(f"   Found {len(articles)} articles (meta: {raw_response.get('meta', {})})")

    # --- REMOVE DUPLICATES ---
    articles = remove_duplicate_articles(articles)
    print(f"   After deduplication: {len(articles)} articles")

    # --- CLEAN TEXT ---
    print("\n[3/6] Cleaning article text...")
    cleaner = TextCleaner()
    cleaned_articles = cleaner.process_articles(articles)

    # --- KEYWORDS (TF-IDF) ---
    print("\n[4/6] Extracting keywords (TF-IDF)...")
    keyword_extractor = KeywordExtractor()
    keywords_data = keyword_extractor.extract_from_articles(cleaned_articles)

    # --- SENTIMENT (Marketaux scores) ---
    print("\n[5/6] Classifying sentiment from Marketaux scores...")
    sentiment_processor = SentimentProcessor()
    analyzed_articles = sentiment_processor.process_articles(cleaned_articles, symbol)

    # --- AGGREGATE ---
    print("\n[6/6] Aggregating sentiment statistics...")
    aggregator = SentimentAggregator()
    summary = aggregator.aggregate(analyzed_articles, company_name, symbol)

    # --- SUMMARY ---
    print("\nGenerating lightweight summary...")
    summarizer = NewsSummarizer()
    news_summary = summarizer.generate_summary(
        analyzed_articles,
        keywords_data.get("keywords", []),
        company_name,
    )

    results: Dict[str, Any] = {
        "company_name": company_name,
        "symbol": symbol,
        "articles": analyzed_articles,
        "summary": summary,
        "keywords": keywords_data,
        "news_summary": news_summary,
        "raw_response": raw_response,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if save_output:
        filepath = _save_results(results)
        results["output_path"] = str(filepath)
        print(f"\nResults saved to: {filepath}")

    print("\n" + "=" * 60)
    print("News Sentiment Analysis Complete!")
    print("=" * 60 + "\n")

    return results


def _save_results(results: Dict[str, Any]) -> Path:
    """Save pipeline results to JSON file."""
    company = results.get("company_name", "company")
    clean_name = company.replace(" ", "_").replace("/", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_news_sentiment_{timestamp}.json"
    filepath = OUTPUT_DIR / filename

    export = {
        "company_name": results.get("company_name"),
        "symbol": results.get("symbol"),
        "generated_at": results.get("generated_at"),
        "summary": results.get("summary"),
        "keywords": results.get("keywords"),
        "news_summary": results.get("news_summary"),
        "articles": [
            {
                "title": a.get("title"),
                "source": a.get("source"),
                "sentiment": a.get("sentiment"),
                "sentiment_score": a.get("sentiment_score"),
                "published_at": a.get("published_at"),
                "url": a.get("url"),
            }
            for a in results.get("articles", [])
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    return filepath


def main_cli() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Financial News Sentiment Analysis (Marketaux)",
    )
    parser.add_argument("--company", "-c", required=True, help="Company name")
    parser.add_argument("--symbol", "-s", required=True, help="Stock symbol e.g. RELIANCE.NS")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Article limit")
    parser.add_argument("--days", "-d", type=int, default=7, help="Lookback days")
    parser.add_argument("--save", action="store_true", help="Save JSON output")

    args = parser.parse_args()

    result = run_news_sentiment_analysis(
        company_name=args.company,
        stock_symbol=args.symbol,
        articles_limit=args.limit,
        days=args.days,
        save_output=args.save,
    )

    if result.get("error"):
        print(f"Error: {result['error']}")
        sys.exit(1)

    summary = result.get("summary", {})
    dist = summary.get("sentiment_distribution", {})
    print(f"Overall: {summary.get('overall_sentiment')} ({summary.get('average_sentiment')})")
    print(
        f"Distribution — +{dist.get('positive_percentage', 0)}% "
        f"/ ={dist.get('neutral_percentage', 0)}% "
        f"/ -{dist.get('negative_percentage', 0)}%"
    )


def main_streamlit() -> None:
    """Streamlit dashboard entry point."""
    from visualization.dashboard import run_streamlit_app

    run_streamlit_app(run_news_sentiment_analysis)


def _is_cli_invocation() -> bool:
    """Detect CLI usage vs Streamlit launch."""
    return "--company" in sys.argv or "-c" in sys.argv


if __name__ == "__main__":
    if _is_cli_invocation():
        main_cli()
    else:
        main_streamlit()
