# src/news_sentiment/validators/fake_news_filter.py
"""
Fake news prevention via trusted-source validation and multi-source verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from difflib import SequenceMatcher

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TRUSTED_SOURCES, CONFIDENCE_LABELS


class FakeNewsFilter:
    """Validate news credibility using trusted sources and cross-verification."""

    RECENT_DAYS = 7

    def validate_article(
        self,
        article: Dict,
        multi_source_count: int = 1,
    ) -> Dict:
        """
        Score a single article's credibility.

        Returns confidence score (0-100) and label.
        """
        score = 0
        source = article.get("source", "")

        if source in TRUSTED_SOURCES:
            score += 50

        if multi_source_count >= 2:
            score += min(40, multi_source_count * 15)

        if self._is_recent(article.get("published_date", "")):
            score += 10

        event_confidence = article.get("event_confidence", 0)
        if event_confidence >= 70:
            score += 5

        score = min(score, 100)
        label = self._score_to_label(score)

        return {
            "confidence": score,
            "confidence_label": label,
        }

    def validate_batch(self, articles: List[Dict]) -> List[Dict]:
        """Validate all articles with multi-source cross-verification."""
        title_groups = self._group_similar_titles(articles)

        validated = []
        for article in articles:
            title = article.get("title", "")
            group_size = len(title_groups.get(title, [article]))
            result = self.validate_article(article, multi_source_count=group_size)
            article.update(result)
            validated.append(article)

        return validated

    def compute_overall_confidence(self, articles: List[Dict]) -> str:
        """Compute overall confidence label from validated articles."""
        if not articles:
            return "LOW_CONFIDENCE"

        avg_score = sum(a.get("confidence", 0) for a in articles) / len(articles)
        trusted_count = sum(1 for a in articles if a.get("source") in TRUSTED_SOURCES)
        multi_verified = self._count_multi_source_groups(articles)

        overall = avg_score
        if trusted_count == len(articles):
            overall += 5
        if multi_verified >= 2:
            overall += 10

        return self._score_to_label(min(overall, 100))

    def _group_similar_titles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Group articles with similar titles for multi-source verification."""
        groups: Dict[str, List[Dict]] = {}

        for article in articles:
            title = article.get("title", "")
            matched_key = None

            for key in groups:
                if self._title_similarity(title, key) >= 0.6:
                    matched_key = key
                    break

            if matched_key:
                groups[matched_key].append(article)
            else:
                groups[title] = [article]

        return groups

    def _count_multi_source_groups(self, articles: List[Dict]) -> int:
        groups = self._group_similar_titles(articles)
        return sum(
            1 for group in groups.values()
            if len({a.get("source") for a in group}) >= 2
        )

    def _title_similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _is_recent(self, date_str: str) -> bool:
        if not date_str:
            return False
        try:
            from email.utils import parsedate_to_datetime
            pub_date = parsedate_to_datetime(date_str)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.RECENT_DAYS)
            return pub_date >= cutoff
        except Exception:
            return True

    def _score_to_label(self, score: float) -> str:
        if score >= CONFIDENCE_LABELS["HIGH_CONFIDENCE"]:
            return "HIGH_CONFIDENCE"
        if score >= CONFIDENCE_LABELS["MEDIUM_CONFIDENCE"]:
            return "MEDIUM_CONFIDENCE"
        return "LOW_CONFIDENCE"

    def is_trusted_source(self, source: str) -> bool:
        return source in TRUSTED_SOURCES

    def filter_untrusted(self, articles: List[Dict]) -> List[Dict]:
        """Reject articles from non-trusted sources."""
        return [a for a in articles if self.is_trusted_source(a.get("source", ""))]
