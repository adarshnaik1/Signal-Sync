#!/usr/bin/env python
# src/news_sentiment/main.py
"""
News Sentiment Analysis Pipeline for Indian Stock Market.
Orchestrates RSS fetching, extraction, event detection, FinBERT sentiment,
fake news validation, and JSON output.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR, MAX_ARTICLES_TO_PROCESS
from collectors.rss_fetcher import RSSFetcher
from collectors.article_extractor import ArticleExtractor
from utils.text_cleaner import TextCleaner
from analyzers.event_detector import EventDetector
from analyzers.finbert_analyzer import FinBERTAnalyzer
from validators.fake_news_filter import FakeNewsFilter


def _generate_summary(
    company: str,
    overall_sentiment: str,
    events: List[str],
    articles: List[Dict],
    confidence_label: str,
) -> str:
    """Generate a readable summary using templates (no LLM)."""
    source_names = sorted({a.get("source", "") for a in articles if a.get("source")})
    source_text = ", ".join(source_names) if source_names else "trusted financial news sources"

    event_text = ""
    if events and events != ["General News"]:
        event_list = ", ".join(events[:3])
        event_text = f" Key events detected include {event_list}."

    sentiment_reasons = []
    for article in articles[:5]:
        if article.get("sentiment") == overall_sentiment:
            event = article.get("event_type", "")
            if event and event != "General News":
                sentiment_reasons.append(event.lower())

    reason_text = ""
    if sentiment_reasons:
        unique_reasons = list(dict.fromkeys(sentiment_reasons))[:2]
        reason_text = f" driven by {', '.join(unique_reasons)}"

    confidence_map = {
        "HIGH_CONFIDENCE": "high confidence",
        "MEDIUM_CONFIDENCE": "moderate confidence",
        "LOW_CONFIDENCE": "limited confidence",
    }
    conf_text = confidence_map.get(confidence_label, "moderate confidence")

    article_count = len(articles)
    return (
        f"{company} received {overall_sentiment.lower()} sentiment{reason_text} "
        f"based on analysis of {article_count} article(s) from {source_text}.{event_text} "
        f"News verification status: {conf_text} across trusted financial outlets."
    )


def _compute_overall_sentiment(articles: List[Dict]) -> tuple:
    """Compute overall sentiment label and average score from articles."""
    if not articles:
        return "Neutral", 0.5

    scores = {"Positive": 0, "Negative": 0, "Neutral": 0}
    total_score = 0.0

    for article in articles:
        sentiment = article.get("sentiment", "Neutral")
        scores[sentiment] = scores.get(sentiment, 0) + 1
        total_score += article.get("sentiment_score", 0.5)

    dominant = max(scores, key=scores.get)
    avg_score = round(total_score / len(articles), 4)
    return dominant, avg_score


def run_news_sentiment_analysis(
    company: str,
    max_articles: int = MAX_ARTICLES_TO_PROCESS,
    save_output: bool = True,
    output_dir: Optional[Path] = None,
) -> Dict:
    """
    Run the complete news sentiment analysis pipeline.

    Pipeline:
    1. Fetch RSS feeds
    2. Filter company-related articles
    3. Extract full article content
    4. Clean text
    5. Detect events
    6. Run FinBERT sentiment
    7. Validate confidence (fake news filter)
    8. Generate summary
    9. Save JSON
    10. Return result
    """
    output_dir = output_dir or OUTPUT_DIR
    company_display = company.strip().title()

    print("\n" + "=" * 60)
    print(f"News Sentiment Analysis for: {company_display}")
    print("=" * 60)

    # Phase 1: Fetch RSS feeds
    print("\nPHASE 1: Fetching RSS Feeds")
    print("-" * 40)
    fetcher = RSSFetcher()
    all_articles = fetcher.fetch_all()
    print(f"   [OK] Fetched {len(all_articles)} articles from trusted sources")

    # Phase 2: Filter by company
    print("\nPHASE 2: Filtering Company-Related Articles")
    print("-" * 40)
    company_articles = fetcher.filter_by_company(all_articles, company)
    company_articles = company_articles[:max_articles]
    print(f"   [OK] Found {len(company_articles)} articles related to {company_display}")

    if not company_articles:
        result = {
            "company": company_display,
            "overall_sentiment": "Neutral",
            "confidence": "LOW_CONFIDENCE",
            "events_detected": [],
            "summary": f"No recent news found for {company_display} from trusted financial sources.",
            "articles": [],
            "error": "No articles found",
        }
        if save_output:
            _save_result(result, company, output_dir)
        return result

    # Phase 3: Extract full article content
    print("\nPHASE 3: Extracting Full Article Content")
    print("-" * 40)
    extractor = ArticleExtractor()
    extracted = extractor.extract_batch(company_articles)
    print(f"   [OK] Extracted full text from {len(extracted)} articles")

    if not extracted:
        result = {
            "company": company_display,
            "overall_sentiment": "Neutral",
            "confidence": "LOW_CONFIDENCE",
            "events_detected": [],
            "summary": f"Articles found but full text extraction failed for {company_display}.",
            "articles": [],
            "error": "Extraction failed",
        }
        if save_output:
            _save_result(result, company, output_dir)
        return result

    # Phase 4: Clean text
    print("\nPHASE 4: Cleaning Text")
    print("-" * 40)
    cleaner = TextCleaner()
    for article in extracted:
        article["cleaned_text"] = cleaner.truncate(cleaner.clean(article["full_text"]))
    print(f"   [OK] Cleaned {len(extracted)} articles")

    # Phase 5: Detect events
    print("\nPHASE 5: Detecting Financial Events")
    print("-" * 40)
    event_detector = EventDetector()
    all_events = []
    for article in extracted:
        event_result = event_detector.detect(
            article["cleaned_text"],
            source=article.get("source", ""),
        )
        article["event_type"] = event_result["event_type"]
        article["event_impact"] = event_result["impact"]
        article["event_confidence"] = event_result["confidence"]
        all_events.append(event_result["event_type"])
    unique_events = sorted(set(e for e in all_events if e != "General News"))
    print(f"   [OK] Events detected: {unique_events or ['General News']}")

    # Phase 6: FinBERT sentiment analysis
    print("\nPHASE 6: Running FinBERT Sentiment Analysis")
    print("-" * 40)
    finbert = FinBERTAnalyzer()
    for article in extracted:
        sentiment_result = finbert.analyze(article["cleaned_text"])
        article["sentiment"] = sentiment_result["sentiment"]
        article["sentiment_score"] = sentiment_result["score"]
    print(f"   [OK] Analyzed sentiment for {len(extracted)} articles")

    # Phase 7: Fake news validation
    print("\nPHASE 7: Validating News Confidence")
    print("-" * 40)
    fake_filter = FakeNewsFilter()
    extracted = fake_filter.filter_untrusted(extracted)
    validated = fake_filter.validate_batch(extracted)
    overall_confidence = fake_filter.compute_overall_confidence(validated)
    print(f"   [OK] Overall confidence: {overall_confidence}")

    # Phase 8: Generate summary
    print("\nPHASE 8: Generating Summary")
    print("-" * 40)
    overall_sentiment, avg_score = _compute_overall_sentiment(validated)
    summary = _generate_summary(
        company_display, overall_sentiment, unique_events, validated, overall_confidence
    )
    print(f"   [OK] {summary[:80]}...")

    # Build output structure
    output_articles = [
        {
            "source": a.get("source", ""),
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "published_date": a.get("published_date", ""),
            "event_type": a.get("event_type", "General News"),
            "sentiment": a.get("sentiment", "Neutral"),
            "sentiment_score": a.get("sentiment_score", 0.5),
            "confidence": a.get("confidence", 50),
        }
        for a in validated
    ]

    result = {
        "company": company_display,
        "overall_sentiment": overall_sentiment,
        "average_sentiment_score": avg_score,
        "confidence": overall_confidence,
        "events_detected": unique_events or ["General News"],
        "summary": summary,
        "articles": output_articles,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # Phase 9: Save JSON
    if save_output:
        print("\nPHASE 9: Saving Results")
        print("-" * 40)
        output_path = _save_result(result, company, output_dir)
        result["output_path"] = output_path
        print(f"   [OK] Results saved to: {output_path}")

    print("\n" + "=" * 60)
    print("News Sentiment Analysis Complete!")
    print("=" * 60 + "\n")

    return result


def _save_result(result: Dict, company: str, output_dir: Path) -> str:
    """Save analysis result to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_name = company.replace(" ", "_").replace("/", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_news_sentiment_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return str(filepath)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="News Sentiment Analysis for Indian Stock Market",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Infosys"
  python main.py "TCS" --limit 15
  python main.py "Reliance" --no-save
        """,
    )

    parser.add_argument("company", type=str, help="Company name or ticker to analyze")
    parser.add_argument(
        "--limit", "-l", type=int, default=MAX_ARTICLES_TO_PROCESS,
        help=f"Maximum articles to process (default: {MAX_ARTICLES_TO_PROCESS})",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Custom output directory",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't save results to file",
    )

    args = parser.parse_args()

    result = run_news_sentiment_analysis(
        company=args.company,
        max_articles=args.limit,
        save_output=not args.no_save,
        output_dir=Path(args.output) if args.output else None,
    )

    return result


if __name__ == "__main__":
    main()
