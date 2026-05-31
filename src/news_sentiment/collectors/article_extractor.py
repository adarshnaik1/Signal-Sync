# src/news_sentiment/collectors/article_extractor.py
"""
Full article text extraction using newspaper3k.
"""

from typing import Dict, Optional
from newspaper import Article


class ArticleExtractor:
    """Extract full article content from trusted news URLs."""

    def extract(self, article_meta: Dict) -> Optional[Dict]:
        """
        Download and parse full article text from URL.

        Returns None if extraction fails (paywall, network error, etc.).
        """
        url = article_meta.get("url", "")
        if not url:
            return None

        try:
            article = Article(url)
            article.download()
            article.parse()

            full_text = article.text.strip()
            if not full_text or len(full_text) < 50:
                return None

            return {
                "title": article_meta.get("title") or article.title or "",
                "source": article_meta.get("source", ""),
                "url": url,
                "published_date": article_meta.get("published", ""),
                "full_text": full_text,
            }
        except Exception:
            return None

    def extract_batch(self, articles: list) -> list:
        """Extract full text for a batch of article metadata dicts."""
        extracted = []
        for meta in articles:
            result = self.extract(meta)
            if result:
                extracted.append(result)
        return extracted


def extract_article(article_meta: Dict) -> Optional[Dict]:
    """Convenience function for single article extraction."""
    return ArticleExtractor().extract(article_meta)
