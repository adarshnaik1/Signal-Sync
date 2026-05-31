# src/news_sentiment/collectors/rss_fetcher.py
"""
RSS feed fetcher for trusted Indian financial news sources.
"""

import feedparser
from typing import List, Dict, Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RSS_FEEDS, MAX_ARTICLES_PER_FETCH, COMPANY_ALIASES


class RSSFetcher:
    """Fetch and parse articles from trusted RSS feeds."""

    def __init__(self, feeds: Optional[Dict[str, str]] = None):
        self.feeds = feeds or RSS_FEEDS

    def fetch_all(self, max_per_source: int = MAX_ARTICLES_PER_FETCH) -> List[Dict]:
        """Fetch articles from all configured RSS feeds."""
        all_articles = []
        for source, feed_url in self.feeds.items():
            articles = self._fetch_feed(source, feed_url, max_per_source)
            all_articles.extend(articles)
        return self._remove_duplicates(all_articles)

    def _fetch_feed(self, source: str, feed_url: str, max_articles: int) -> List[Dict]:
        """Parse a single RSS feed."""
        articles = []
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:max_articles]:
                articles.append({
                    "source": source,
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "published": entry.get("published", entry.get("updated", "")),
                    "summary": entry.get("summary", entry.get("description", "")).strip(),
                })
        except Exception as e:
            print(f"   [WARN] Failed to fetch {source}: {e}")
        return articles

    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles by URL."""
        seen_urls = set()
        unique = []
        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(article)
        return unique

    def filter_by_company(self, articles: List[Dict], company: str) -> List[Dict]:
        """Filter articles related to a company using alias matching."""
        aliases = self._get_company_aliases(company)
        if not aliases:
            return []

        filtered = []
        for article in articles:
            searchable = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            if any(alias in searchable for alias in aliases):
                filtered.append(article)
        return filtered[:MAX_ARTICLES_PER_FETCH]

    def _get_company_aliases(self, company: str) -> List[str]:
        """Resolve company name to search aliases."""
        company_lower = company.lower().strip()

        if company_lower in COMPANY_ALIASES:
            return COMPANY_ALIASES[company_lower]

        for key, aliases in COMPANY_ALIASES.items():
            if company_lower in key or key in company_lower:
                return aliases

        return [company_lower]


def fetch_rss_articles(company: str, max_per_source: int = MAX_ARTICLES_PER_FETCH) -> List[Dict]:
    """Convenience function: fetch all feeds and filter by company."""
    fetcher = RSSFetcher()
    all_articles = fetcher.fetch_all(max_per_source=max_per_source)
    return fetcher.filter_by_company(all_articles, company)
