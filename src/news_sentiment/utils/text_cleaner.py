# src/news_sentiment/utils/text_cleaner.py
"""
Text cleaning utilities for extracted article content.
Preserves financial terms while removing noise.
"""

import re
from html import unescape


class TextCleaner:
    """Clean article text while preserving financial terminology."""

    URL_PATTERN = re.compile(
        r"https?://\S+|www\.\S+",
        re.IGNORECASE,
    )
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s.,;:!?%$₹\-'\"()/&@#]")
    WHITESPACE_PATTERN = re.compile(r"\s+")

    def clean(self, text: str) -> str:
        """Clean text: remove URLs, HTML, extra whitespace; keep finance terms."""
        if not text:
            return ""

        cleaned = unescape(text)
        cleaned = self.HTML_TAG_PATTERN.sub(" ", cleaned)
        cleaned = self.URL_PATTERN.sub(" ", cleaned)
        cleaned = self.SPECIAL_CHARS_PATTERN.sub(" ", cleaned)
        cleaned = self.WHITESPACE_PATTERN.sub(" ", cleaned)
        return cleaned.strip()

    def truncate(self, text: str, max_length: int = 1500) -> str:
        """Truncate text to max length for lightweight processing."""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(" ", 1)[0]


def clean_text(text: str, max_length: int = 1500) -> str:
    """Convenience function: clean and truncate text."""
    cleaner = TextCleaner()
    return cleaner.truncate(cleaner.clean(text), max_length)
