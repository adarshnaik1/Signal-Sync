"""
Lightweight news summary without LLM or transformer models.
"""

from __future__ import annotations

from typing import Dict, List


class NewsSummarizer:
    """
    Builds a simple summary from top headlines, snippets, and keywords.
    """

    def __init__(self, max_headlines: int = 5):
        self.max_headlines = max_headlines

    def generate_summary(
        self,
        articles: List[Dict],
        keywords: List[str],
        company_name: str,
    ) -> Dict:
        """
        Generate a lightweight textual summary.

        Args:
            articles: Processed articles with sentiment.
            keywords: Extracted top keywords.
            company_name: Company display name.

        Returns:
            Summary dict with bullets and headline list.
        """
        if not articles:
            return {
                "overview": f"No recent news articles found for {company_name}.",
                "top_headlines": [],
                "keyword_topics": [],
                "snippets": [],
            }

        sorted_articles = sorted(
            articles,
            key=lambda a: abs(a.get("sentiment_score", 0)),
            reverse=True,
        )

        top_by_sentiment = sorted(
            articles,
            key=lambda a: a.get("sentiment_score", 0),
            reverse=True,
        )[: self.max_headlines]

        positive_count = sum(1 for a in articles if a.get("sentiment") == "Positive")
        negative_count = sum(1 for a in articles if a.get("sentiment") == "Negative")
        neutral_count = len(articles) - positive_count - negative_count

        keyword_str = ", ".join(keywords[:8]) if keywords else "N/A"

        overview = (
            f"Analyzed {len(articles)} articles about {company_name}. "
            f"Sentiment mix: {positive_count} positive, {neutral_count} neutral, "
            f"{negative_count} negative. "
            f"Key topics: {keyword_str}."
        )

        headlines = [
            {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "sentiment": a.get("sentiment", "Neutral"),
                "published_at": a.get("published_at", ""),
            }
            for a in top_by_sentiment
        ]

        snippets = []
        for article in sorted_articles[:3]:
            snippet = article.get("snippet") or article.get("description") or ""
            if snippet:
                snippets.append(snippet[:280].strip())

        return {
            "overview": overview,
            "top_headlines": headlines,
            "keyword_topics": keywords[:10],
            "snippets": snippets,
        }
