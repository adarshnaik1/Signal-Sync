# 📈 Indian Market News Sentiment Analysis

Welcome to the **News Sentiment Analysis** module! This feature allows users to query Indian stock tickers or company names (e.g., _TCS, INFY, RELIANCE, HDFCBANK_), fetches real-time news headlines, and utilizes machine learning (**FinBERT**) to evaluate the market sentiment.

## 🚀 Features

- **Indian Market Optimized**: Hardcoded geolocation filtering to fetch news strictly relevant to the Indian Stock Market.
- **FinBERT ML Pipeline**: Uses `ProsusAI/finbert`, a state-of-the-art transformer model trained on financial contexts.
- **Second-Level Deep Evaluation**: If a headline is evaluated as "Neutral", the system dynamically falls back to an intelligent web scraper (BeautifulSoup4) to read the full article context and re-classifies the sentiment accurately.
- **Interactive UI**: Built with Streamlit, rendering live Plotly pie charts and dynamic confidence tables.

---

## 🛠️ Installation & Setup

### 1. Prerequisites

Make sure you are in your project root (`Signal-Sync`). Create and activate your virtual environment, then install the required dependencies:

```bash
pip install transformers torch plotly requests dateparser python-dotenv beautifulsoup4 streamlit pandas
```

### 2. Environment Variables

You need a SerperDev API key to fetch live Google News results.

1. Get a free API key at [Serper.dev](https://serper.dev/).
2. Create or edit the `.env` file at the root of `Signal-Sync` and add your key:

```env
SERPER_API_KEY=your_serper_api_key_here
```

### 3. Running the Application

From the `Signal-Sync` root directory, launch the Streamlit frontend:

```bash
streamlit run streamlit_app/news_app.py
```

_Note: The first time you run this, it will download the FinBERT model weights from HuggingFace (~400MB)._

---

## 🏛️ Implementation Architecture

This module follows a clean, decoupled architecture:

- **`config.py`**: Manages environment variables and global configurations (like the ML model name).
- **`collector.py` (`NewsCollector`)**:
  - Interfaces with the SerperDev API (up to 100 queries).
  - Uses `dateparser` to interpret arbitrary timestamps (e.g., "10 hours ago") and retain only the last 45 days.
  - Contains a BeautifulSoup4 `fetch_article_text` scraper that strips HTML, scripts, and navigation bars to securely read actual article bodies up to ~2500 characters.
- **`analyzer.py` (`SentimentAnalyzer`)**: Loads the HuggingFace `pipeline`. Batch inference is utilized to run arrays of strings efficiently. Explicit padding and truncation limit inputs to 512 tokens so the model operates cleanly without failure.
- **`service.py` (`NewsSentimentService`)**: The conductor. It intercepts the HTTP collector and the NLP analyzer. It holds the **Second-Level Evaluation workflow**: it reads headline scores first; if neutral, it triggers the scraper and re-runs the FinBERT pipeline on the full text.
- **`news_app.py`**: The Streamlit user interface caching the ML model (to prevent memory reloads) and translating aggregate scores (Bullish/Neutral/Bearish) into rich metrics and Plotly charts.

## 📝 Future Improvements Roadmap

1. Time-Decay Weighting for giving recent news mathematically higher relevance than older news.
2. Aspect-Based Sentiment Analysis (ABSA) for entity-specific evaluations.
3. Fine-tuning models directly onto Indian financial publications.
