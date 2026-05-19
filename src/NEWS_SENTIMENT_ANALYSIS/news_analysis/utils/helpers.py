"""
Shared utility functions for the news sentiment analysis pipeline.
"""

from __future__ import annotations

import os
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv


MODULE_DIR = Path(__file__).resolve().parent.parent
FEATURE_ROOT = MODULE_DIR.parent
PROJECT_ROOT = FEATURE_ROOT.parent.parent


def load_environment() -> None:
    """Load environment variables from feature or project .env files."""
    for env_path in (FEATURE_ROOT / ".env", PROJECT_ROOT / ".env"):
        if env_path.exists():
            load_dotenv(env_path)
            return
    load_dotenv()


def get_api_key() -> str:
    """Return Marketaux API key from environment."""
    load_environment()
    key = os.getenv("MARKETAUX_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "MARKETAUX_API_KEY is not set. Add it to .env in the NEWS SENTIMENT ANALYSIS folder."
        )
    return key


def published_after_date(days: int) -> str:
    """
    Compute ISO published_after parameter for Marketaux.

    Args:
        days: Number of days to look back from today (UTC).

    Returns:
        Date string YYYY-MM-DD.
    """
    if days < 1:
        days = 1
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%d")


def validate_api_response(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate Marketaux API JSON and extract article list.

    Args:
        response_json: Parsed API response.

    Returns:
        List of article dictionaries.

    Raises:
        ValueError: If response structure is invalid or indicates an error.
    """
    if not isinstance(response_json, dict):
        raise ValueError("Invalid API response: expected JSON object.")

    if "error" in response_json:
        message = response_json.get("error", {}).get("message", "Unknown API error")
        raise ValueError(f"Marketaux API error: {message}")

    data = response_json.get("data")
    if data is None:
        raise ValueError("Invalid API response: missing 'data' field.")

    if not isinstance(data, list):
        raise ValueError("Invalid API response: 'data' must be a list.")

    return data


def remove_duplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles by uuid, then url, then normalized title.

    Args:
        articles: Raw article list from API.

    Returns:
        Deduplicated articles preserving first occurrence order.
    """
    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []

    for article in articles:
        key = _article_dedup_key(article)
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)

    return unique


def _article_dedup_key(article: Dict[str, Any]) -> str:
    """Build a stable deduplication key for an article."""
    uuid_val = article.get("uuid")
    if uuid_val:
        return f"uuid:{uuid_val}"

    url = article.get("url", "")
    if url:
        return f"url:{url.strip().lower()}"

    title = (article.get("title") or "").strip().lower()
    return f"title:{hashlib.md5(title.encode('utf-8')).hexdigest()}"


def extract_entity_sentiment(article: Dict[str, Any], symbol: str) -> Optional[float]:
    """
    Extract sentiment_score for the requested symbol from article entities.

    Args:
        article: Single article dict.
        symbol: Stock symbol (e.g. RELIANCE.NS).

    Returns:
        Sentiment score or None if not found.
    """
    entities = article.get("entities") or []
    symbol_upper = symbol.upper()

    for entity in entities:
        if (entity.get("symbol") or "").upper() == symbol_upper:
            score = entity.get("sentiment_score")
            if score is not None:
                return float(score)

    if entities:
        score = entities[0].get("sentiment_score")
        if score is not None:
            return float(score)

    return None


def combine_article_text(article: Dict[str, Any]) -> str:
    """Combine title, description, snippet, and keywords for NLP processing."""
    parts = [
        article.get("title", ""),
        article.get("description", ""),
        article.get("snippet", ""),
        article.get("keywords", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def parse_published_at(value: Any) -> Optional[pd.Timestamp]:
    """Parse published_at into pandas Timestamp."""
    if not value:
        return None
    try:
        return pd.to_datetime(value, utc=True)
    except (ValueError, TypeError):
        return None


def safe_round(value: Optional[float], digits: int = 4) -> float:
    """Round float safely, defaulting to 0.0."""
    if value is None:
        return 0.0
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0
