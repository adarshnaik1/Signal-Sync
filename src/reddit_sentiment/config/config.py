# src/reddit_sentiment/config/config.py
"""
Configuration settings for Reddit Sentiment Analyzer.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
MODULE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MODULE_DIR.parent.parent  # Signal-Sync root

# Try loading from project root first, then fall back to module directory
if (PROJECT_ROOT / ".env").exists():
    load_dotenv(PROJECT_ROOT / ".env")
else:
    load_dotenv(MODULE_DIR / ".env")

# Reddit API Credentials
REDDIT_CONFIG = {
    "client_id": os.getenv("REDDIT_CLIENT_ID", ""),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
    "username": os.getenv("REDDIT_USERNAME", ""),
    "password": os.getenv("REDDIT_PASSWORD", ""),
    "user_agent": os.getenv("REDDIT_USER_AGENT", "SentimentAnalyzer/1.0")
}

# Default subreddits to search for company discussions (India-focused)
DEFAULT_SUBREDDITS = [
    "IndianStockMarket",      # Primary Indian stock market discussions
    "IndiaInvestments",       # Indian investment community
    "indiabusiness",          # Indian business news
    "india",                  # General India subreddit
    "bangalore",              # Tech hub - Bangalore discussions
    "mumbai",                 # Financial capital discussions
    "IndianStreetBets",       # Indian version of WSB
    "dalalstreetbets",        # Dalal Street (BSE/NSE) discussions
    "financialIndependenceIndia",  # FIRE movement India
    "CarsIndia",              # For auto companies like Tata Motors, Maruti
]

# Search settings
SEARCH_CONFIG = {
    "posts_per_subreddit": 50,  # Number of posts to fetch per subreddit
    "sort_by": "relevance",      # Options: relevance, hot, top, new
    "time_filter": "month",      # Options: all, year, month, week, day, hour
}

# Sentiment thresholds (VADER compound score)
SENTIMENT_THRESHOLDS = {
    "positive": 0.05,   # >= 0.05 is positive
    "negative": -0.05,  # <= -0.05 is negative
    # Between -0.05 and 0.05 is neutral
}

# Output directory
OUTPUT_DIR = MODULE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Text preprocessing settings
PREPROCESSING_CONFIG = {
    "remove_urls": True,
    "remove_reddit_formatting": True,
    "remove_special_chars": True,
    "lowercase": True,
    "min_text_length": 10,  # Minimum characters for valid text
}
