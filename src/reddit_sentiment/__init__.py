# src/reddit_sentiment/__init__.py
"""
Reddit Sentiment Analyzer
A system for extracting and analyzing sentiment from Reddit discussions about companies.
"""

from .main import run_sentiment_analysis
from .services import (
    RedditScraper,
    fetch_reddit_posts,
    TextProcessor,
    preprocess_text,
    preprocess_posts,
    SentimentAnalyzer,
    analyze_sentiment,
    save_sentiment_results
)
from .config import (
    REDDIT_CONFIG,
    DEFAULT_SUBREDDITS,
    SEARCH_CONFIG,
    SENTIMENT_THRESHOLDS,
    OUTPUT_DIR
)

__version__ = "1.0.0"

__all__ = [
    # Main function
    "run_sentiment_analysis",
    
    # Services
    "RedditScraper",
    "fetch_reddit_posts",
    "TextProcessor",
    "preprocess_text",
    "preprocess_posts",
    "SentimentAnalyzer",
    "analyze_sentiment",
    "save_sentiment_results",
    
    # Config
    "REDDIT_CONFIG",
    "DEFAULT_SUBREDDITS",
    "SEARCH_CONFIG",
    "SENTIMENT_THRESHOLDS",
    "OUTPUT_DIR"
]
