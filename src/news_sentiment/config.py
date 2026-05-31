# src/news_sentiment/config.py
"""
Configuration for News Sentiment Analysis module.
Trusted Indian financial news sources only.
"""

from pathlib import Path

MODULE_DIR = Path(__file__).parent
OUTPUT_DIR = MODULE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Trusted RSS feeds (free, verified financial sources)
RSS_FEEDS = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
}

# Additional sources (optional, for fake-news filter whitelist)
TRUSTED_SOURCES = {
    "Moneycontrol",
    "Economic Times",
    "Business Standard",
    "LiveMint",
}

MAX_ARTICLES_PER_FETCH = 20
MAX_ARTICLES_TO_PROCESS = 20
MAX_TEXT_LENGTH = 1500

# FinBERT model (free, CPU-friendly)
FINBERT_MODEL = "ProsusAI/finbert"

# Company alias mapping for filtering
COMPANY_ALIASES = {
    "infosys": ["infosys", "infy", "infosys ltd", "infosys limited"],
    "tcs": ["tcs", "tata consultancy services", "tata consultancy"],
    "reliance": ["reliance", "ril", "reliance industries", "reliance industries ltd"],
    "hdfc bank": ["hdfc bank", "hdfc", "hdfc bank ltd"],
    "icici bank": ["icici bank", "icici", "icici bank ltd"],
    "wipro": ["wipro", "wipro ltd", "wipro limited"],
    "tata motors": ["tata motors", "tatamotors", "tata motors ltd"],
    "bharti airtel": ["bharti airtel", "airtel", "bharti"],
    "itc": ["itc", "itc ltd", "itc limited"],
    "hcl tech": ["hcl tech", "hcl technologies", "hcl"],
    "maruti": ["maruti", "maruti suzuki", "msil"],
    "sbi": ["sbi", "state bank of india"],
    "axis bank": ["axis bank", "axis"],
    "bajaj finance": ["bajaj finance", "bajaj fin"],
    "lt": ["l&t", "larsen", "larsen and toubro", "larsen & toubro"],
}

# Confidence thresholds
CONFIDENCE_LABELS = {
    "HIGH_CONFIDENCE": 80,
    "MEDIUM_CONFIDENCE": 50,
    "LOW_CONFIDENCE": 0,
}
