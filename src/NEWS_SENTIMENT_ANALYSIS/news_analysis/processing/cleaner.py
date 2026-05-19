"""
Lightweight text cleaning for financial news articles.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import nltk
from nltk.corpus import stopwords

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import combine_article_text

_STOPWORDS: Optional[set] = None
_NLTK_READY = False


def _ensure_nltk_data() -> None:
    """Download NLTK stopwords once if missing."""
    global _NLTK_READY
    if _NLTK_READY:
        return
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    _NLTK_READY = True


def get_stopwords() -> set:
    """Return English stopwords set (cached)."""
    global _STOPWORDS
    _ensure_nltk_data()
    if _STOPWORDS is None:
        _STOPWORDS = set(stopwords.words("english"))
    return _STOPWORDS


class TextCleaner:
    """
    Cleans article text for keyword extraction and display.
    Applies lowercase, URL removal, punctuation removal, stopword removal.
    """

    def __init__(self, extra_stopwords: Optional[List[str]] = None):
        """
        Initialize cleaner.

        Args:
            extra_stopwords: Additional words to remove.
        """
        self.stopwords = get_stopwords()
        if extra_stopwords:
            self.stopwords = self.stopwords.union({w.lower() for w in extra_stopwords})

    def clean_text(self, text: str) -> str:
        """
        Clean a single text string.

        Args:
            text: Raw text.

        Returns:
            Cleaned lowercase text without stopwords.
        """
        if not text or not isinstance(text, str):
            return ""

        cleaned = text.lower()
        cleaned = self._remove_urls(cleaned)
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        tokens = [t for t in cleaned.split() if t and t not in self.stopwords and len(t) > 1]
        return " ".join(tokens)

    def _remove_urls(self, text: str) -> str:
        """Remove HTTP/HTTPS and www URLs."""
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        return text

    def process_article(self, article: Dict) -> Dict:
        """
        Add cleaned text fields to an article dict.

        Args:
            article: Article dictionary.

        Returns:
            Article with raw_text, cleaned_text fields.
        """
        processed = article.copy()
        raw = combine_article_text(article)
        processed["raw_text"] = raw
        processed["cleaned_text"] = self.clean_text(raw)
        return processed

    def process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Clean text for a list of articles."""
        return [self.process_article(a) for a in articles]
