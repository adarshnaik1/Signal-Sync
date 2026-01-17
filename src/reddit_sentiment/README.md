# Reddit Sentiment Analyzer

A Python-based system for extracting public discussions about companies from Reddit and performing sentiment analysis using VADER.

## 🎯 Features

- **Reddit Data Extraction**: Fetches posts from multiple subreddits using PRAW
- **Text Preprocessing**: Cleans Reddit-specific formatting, URLs, and noise
- **VADER Sentiment Analysis**: Classifies posts as Positive, Negative, or Neutral
- **Summary Statistics**: Generates sentiment distribution and insights
- **Dummy Data Mode**: Test without API credentials

## 📁 Project Structure

```
reddit_sentiment/
├── config/
│   ├── __init__.py
│   └── config.py           # Configuration settings
├── services/
│   ├── __init__.py
│   ├── reddit_scraper.py   # Reddit data extraction
│   ├── text_processor.py   # Text preprocessing
│   └── sentiment_analyzer.py # VADER sentiment analysis
├── output/                  # Generated JSON results
├── main.py                  # Main entry point
├── requirements.txt         # Dependencies
├── .env.example            # Template for credentials
└── README.md
```

## 🚀 Installation

1. **Install dependencies:**

   ```bash
   cd src/reddit_sentiment
   pip install -r requirements.txt
   ```

2. **Configure Reddit API credentials:**

   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env with your credentials
   # Get credentials from: https://www.reddit.com/prefs/apps
   ```

## 🖥️ Usage

### Command Line

```bash
# Basic usage (uses dummy data if no credentials)
python main.py "Tesla"

# With specific subreddits
python main.py "Apple" --subreddits stocks investing technology

# Limit posts per subreddit
python main.py "Microsoft" --limit 100

# Use dummy data for testing
python main.py "Amazon" --dummy

# Specify custom output directory
python main.py "Google" --output ./my_results
```

### Programmatic Usage

```python
from reddit_sentiment import run_sentiment_analysis

# Run analysis
result = run_sentiment_analysis(
    company_name="Tesla",
    subreddits=["stocks", "investing", "wallstreetbets"],
    posts_limit=50,
    use_dummy_data=False  # Set True for testing
)

# Access results
print(f"Overall Sentiment: {result['summary']['overall_sentiment']}")
print(f"Positive: {result['summary']['sentiment_distribution']['positive_percentage']}%")

# Get analyzed posts
for post in result['posts'][:5]:
    print(f"{post['sentiment_label']}: {post['title'][:50]}...")
```

### Direct Service Usage

```python
from reddit_sentiment.services import (
    RedditScraper,
    TextProcessor,
    SentimentAnalyzer
)

# Extract posts
scraper = RedditScraper(use_dummy_data=True)
posts = scraper.search_company("Tesla")

# Preprocess
processor = TextProcessor()
processed = processor.process_posts(posts)

# Analyze sentiment
analyzer = SentimentAnalyzer()
analyzed = analyzer.analyze_posts(processed)
summary = analyzer.generate_summary(analyzed)
```

## 📊 Output Format

Results are saved as JSON with the following structure:

```json
{
  "company": "Tesla",
  "generated_at": "2026-01-17T12:00:00Z",
  "summary": {
    "total_posts_analyzed": 50,
    "sentiment_distribution": {
      "positive": 25,
      "negative": 15,
      "neutral": 10,
      "positive_percentage": 50.0,
      "negative_percentage": 30.0,
      "neutral_percentage": 20.0
    },
    "average_sentiment_score": 0.1234,
    "overall_sentiment": "Positive",
    "subreddit_breakdown": {...}
  },
  "extreme_posts": {
    "most_positive": [...],
    "most_negative": [...]
  },
  "posts": [
    {
      "post_id": "abc123",
      "title": "...",
      "post_text": "...",
      "sentiment_label": "Positive",
      "sentiment_score": 0.8542,
      ...
    }
  ]
}
```

## 🔧 Configuration

Edit `config/config.py` to customize:

- **DEFAULT_SUBREDDITS**: List of subreddits to search
- **SEARCH_CONFIG**: Posts per subreddit, sort order, time filter
- **SENTIMENT_THRESHOLDS**: Thresholds for positive/negative classification
- **PREPROCESSING_CONFIG**: Text cleaning options

## ⚠️ Notes

- Reddit API has rate limits; the scraper includes delays
- Dummy data mode is available for testing without credentials
- VADER works best with English text and social media content

## 📚 VADER Sentiment Scores

- **Compound Score**: Overall sentiment (-1 to +1)
  - > = 0.05: Positive
  - <= -0.05: Negative
  - Between: Neutral
- **pos/neg/neu**: Proportion of each sentiment type (0 to 1)
