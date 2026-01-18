# src/reddit_sentiment/config/__init__.py
"""Configuration module for Reddit Sentiment Analyzer."""

from .config import (
    REDDIT_CONFIG,
    DEFAULT_SUBREDDITS,
    SEARCH_CONFIG,
    SENTIMENT_THRESHOLDS,
    OUTPUT_DIR,
    PREPROCESSING_CONFIG
)

__all__ = [
    "REDDIT_CONFIG",
    "DEFAULT_SUBREDDITS", 
    "SEARCH_CONFIG",
    "SENTIMENT_THRESHOLDS",
    "OUTPUT_DIR",
    "PREPROCESSING_CONFIG"
]
