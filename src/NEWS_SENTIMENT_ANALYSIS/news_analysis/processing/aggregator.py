"""
Aggregate sentiment statistics and news analytics.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import parse_published_at, safe_round


class SentimentAggregator:
    """Computes overall sentiment, distribution, and source-level statistics."""

    def aggregate(self, articles: List[Dict], company_name: str, symbol: str) -> Dict[str, Any]:
        """
        Build full analytics summary from processed articles.

        Args:
            articles: Articles with sentiment fields.
            company_name: Display name for the company.
            symbol: Stock symbol analyzed.

        Returns:
            Summary dictionary for dashboard and export.
        """
        if not articles:
            return {
                "company_name": company_name,
                "symbol": symbol,
                "total_articles": 0,
                "error": "No articles to aggregate",
            }

        labels = [a.get("sentiment", "Neutral") for a in articles]
        scores = [a.get("sentiment_score", 0.0) for a in articles]
        total = len(articles)

        positive = labels.count("Positive")
        negative = labels.count("Negative")
        neutral = labels.count("Neutral")

        avg_score = sum(scores) / total if total else 0.0
        overall = self._overall_sentiment(positive, negative, neutral, avg_score)

        source_stats = self._source_statistics(articles)
        timeline = self._build_timeline(articles)

        return {
            "company_name": company_name,
            "symbol": symbol,
            "total_articles": total,
            "average_sentiment": safe_round(avg_score),
            "overall_sentiment": overall,
            "overall_sentiment_score": safe_round(avg_score),
            "sentiment_distribution": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_percentage": round(positive / total * 100, 1),
                "negative_percentage": round(negative / total * 100, 1),
                "neutral_percentage": round(neutral / total * 100, 1),
            },
            "most_positive_source": source_stats.get("most_positive_source"),
            "most_negative_source": source_stats.get("most_negative_source"),
            "source_breakdown": source_stats.get("source_breakdown", {}),
            "timeline": timeline,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _overall_sentiment(
        self, positive: int, negative: int, neutral: int, avg_score: float
    ) -> str:
        """Determine headline overall sentiment label."""
        if avg_score > 0.1:
            return "Positive"
        if avg_score < -0.1:
            return "Negative"
        if positive > negative and positive >= neutral:
            return "Positive"
        if negative > positive and negative >= neutral:
            return "Negative"
        return "Neutral"

    def _source_statistics(self, articles: List[Dict]) -> Dict[str, Any]:
        """Compute per-source average sentiment and extremes."""
        by_source: Dict[str, List[float]] = defaultdict(list)

        for article in articles:
            source = article.get("source") or "unknown"
            by_source[source].append(article.get("sentiment_score", 0.0))

        if not by_source:
            return {}

        averages = {
            source: sum(vals) / len(vals) for source, vals in by_source.items()
        }

        most_positive = max(averages, key=averages.get)
        most_negative = min(averages, key=averages.get)

        return {
            "most_positive_source": {
                "name": most_positive,
                "average_score": safe_round(averages[most_positive]),
            },
            "most_negative_source": {
                "name": most_negative,
                "average_score": safe_round(averages[most_negative]),
            },
            "source_breakdown": {
                src: {"count": len(by_source[src]), "avg_score": safe_round(avg)}
                for src, avg in averages.items()
            },
        }

    def _build_timeline(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Build daily average sentiment for timeline chart."""
        rows = []
        for article in articles:
            ts = parse_published_at(article.get("published_at"))
            if ts is None:
                continue
            rows.append(
                {
                    "date": ts.date().isoformat(),
                    "sentiment_score": article.get("sentiment_score", 0.0),
                    "sentiment": article.get("sentiment", "Neutral"),
                }
            )

        if not rows:
            return []

        df = pd.DataFrame(rows)
        daily = (
            df.groupby("date", as_index=False)["sentiment_score"]
            .mean()
            .sort_values("date")
        )
        daily["sentiment_score"] = daily["sentiment_score"].round(4)
        return daily.to_dict(orient="records")
