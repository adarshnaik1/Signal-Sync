import requests
import json
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta
import dateparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsCollector:
    """Fetches and deduplicates news headlines from SerperDev API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://google.serper.dev/news"

    def fetch_news(self, query: str, days: int = 45) -> List[Dict[str, Any]]:
        """Fetch news for a given query over the last N days."""
        if not self.api_key:
            logger.error("Serper API key is missing.")
            raise ValueError("Serper API key is missing. Please set SERPER_API_KEY environment variable.")

        payload = json.dumps({
            "q": f"{query} India stock",
            "gl": "in", # Set geolocation to India
            "num": 100  # Max limit per request is 100 for SerperDev
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            logger.info(f"Fetching news from Serper API for query: '{query}'")
            response = requests.post(self.url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            
            news_items = data.get("news", [])
            logger.info(f"Retrieved {len(news_items)} raw news items from Serper API.")
            
            filtered_news = self._filter_and_deduplicate(news_items, days)
            logger.info(f"Retained {len(filtered_news)} items after filtering and deduplication.")
            return filtered_news
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news for {query}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def _filter_and_deduplicate(self, news_items: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
        """Removes duplicates and filters out news older than the specified days."""
        seen_titles = set()
        filtered = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for item in news_items:
            title = item.get("title", "")
            date_str = item.get("date", "")
            
            if not title or title in seen_titles:
                continue

            try:
                # dateparser handles strings like "10 hours ago", "Oct 12, 2023", etc.
                parsed_date = dateparser.parse(date_str)
                if not parsed_date:
                    parsed_date = datetime.now()
            except Exception:
                parsed_date = datetime.now()

            # Ensure timezone-naive datetime for comparison
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)

            if parsed_date >= cutoff_date:
                item['parsed_date'] = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                seen_titles.add(title)
                filtered.append(item)

        return filtered

    def fetch_article_text(self, url: str) -> str:
        """Attempt to extract the main text content from a news article URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # Timeout is important so we don't hang the stream
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return ""
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.extract()
                
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Limit text to ~2500 characters to process only the core article context efficiently
            return text[:2500]
        except Exception as e:
            logger.warning(f"Failed to fetch article text from {url}: {e}")
            return ""
