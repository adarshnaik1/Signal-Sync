"""
Sentiment classification using Marketaux entity sentiment scores.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import extract_entity_sentiment, safe_round

POSITIVE_THRESHOLD = 0.1
NEGATIVE_THRESHOLD = -0.1


class SentimentProcessor:
    """
    Maps Marketaux sentiment_score to Positive / Neutral / Negative labels.
    Does not train custom ML models.
    """

    def __init__(
        self,
        positive_threshold: float = POSITIVE_THRESHOLD,
        negative_threshold: float = NEGATIVE_THRESHOLD,
    ):
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold

    def classify_score(self, score: Optional[float]) -> str:
        """
        Classify a numeric sentiment score.

        Args:
            score: Sentiment score from -1 to +1.

        Returns:
            Sentiment label string.
        """
        if score is None:
            return "Neutral"

        if score > self.positive_threshold:
            return "Positive"
        if score < self.negative_threshold:
            return "Negative"
        return "Neutral"

    def process_article(self, article: Dict, symbol: str) -> Dict:
        """
        Enrich article with sentiment_score and sentiment label.

        Args:
            article: Article dictionary from API.
            symbol: Target stock symbol.

        Returns:
            Article with sentiment fields.
        """
        enriched = article.copy()
        score = extract_entity_sentiment(article, symbol)
        enriched["sentiment_score"] = safe_round(score)
        enriched["sentiment"] = self.classify_score(score)
        return enriched

    def process_articles(self, articles: List[Dict], symbol: str) -> List[Dict]:
        """Process sentiment for all articles."""
        return [self.process_article(a, symbol) for a in articles]
