# News Sentiment Analysis

Financial news sentiment dashboard for the Indian stock market.

> **For teammates**: Full architecture, inputs, API details, and troubleshooting →  
> [`NEWS_SENTIMENT_ANALYSIS_DEEP_REVIEW.md`](../../NEWS_SENTIMENT_ANALYSIS_DEEP_REVIEW.md) (project root, next to the Reddit deep review). Fetches company-related articles from the **Marketaux API**, classifies sentiment using API-provided scores, extracts keywords with **TF-IDF**, and visualizes results in **Streamlit**.

Architecture mirrors the Reddit Sentiment Analysis pipeline in `src/reddit_sentiment/`.

## Project Structure

```
src/NEWS SENTIMENT ANALYSIS/
├── news_analysis/
│   ├── api/
│   │   └── marketaux_client.py
│   ├── processing/
│   │   ├── cleaner.py
│   │   ├── keyword_extractor.py
│   │   ├── sentiment_processor.py
│   │   ├── aggregator.py
│   │   └── summarizer.py
│   ├── visualization/
│   │   ├── charts.py
│   │   └── dashboard.py
│   ├── utils/
│   │   └── helpers.py
│   └── main.py
├── output/
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

```bash
cd "src/NEWS SENTIMENT ANALYSIS"
pip install -r requirements.txt
```

Copy environment file and set your API key:

```bash
copy .env.example .env
# Edit .env: MARKETAUX_API_KEY=your_key
```

## Configuration

| Variable | Description |
|----------|-------------|
| `MARKETAUX_API_KEY` | API token from [marketaux.com](https://www.marketaux.com/) |

## Usage

### Streamlit Dashboard (recommended)

```bash
cd "src/NEWS SENTIMENT ANALYSIS"
streamlit run news_analysis/main.py
```

**Sidebar inputs:**
- Company Name: `Reliance Industries`
- Stock Symbol: `RELIANCE.NS`
- Number of Articles: `50`
- Number of Days: `7`

Click **Run Analysis** to execute the full pipeline.

### Command Line

```bash
cd "src/NEWS SENTIMENT ANALYSIS"
python news_analysis/main.py --company "Reliance Industries" --symbol RELIANCE.NS --limit 50 --days 7 --save
```

## Pipeline Workflow

```
USER INPUT
    ↓
FETCH NEWS (Marketaux API)
    ↓
VALIDATE API RESPONSE
    ↓
EXTRACT ARTICLES
    ↓
REMOVE DUPLICATES
    ↓
CLEAN TEXT (NLTK stopwords)
    ↓
EXTRACT KEYWORDS (TF-IDF)
    ↓
SENTIMENT (Marketaux sentiment_score)
    ↓
CLASSIFY: Positive / Neutral / Negative
    ↓
AGGREGATE STATISTICS
    ↓
GENERATE SUMMARY
    ↓
STREAMLIT DASHBOARD
```

## Sentiment Rules

Uses Marketaux `sentiment_score` (no custom ML model):

| Condition | Label |
|-----------|--------|
| score > 0.1 | Positive |
| score < -0.1 | Negative |
| otherwise | Neutral |

## Dashboard Outputs

1. Company header and overall sentiment score  
2. Sentiment distribution (Positive / Neutral / Negative %)  
3. News statistics (total articles, average sentiment, source extremes)  
4. Plotly charts: pie, timeline, keyword bar  
5. Top headlines table (`title`, `source`, `sentiment`, `published_at`)  
6. Trending keywords  
7. Lightweight news summary  
8. Optional raw JSON viewer  

## Tech Stack

Python · Streamlit · requests · pandas · nltk · scikit-learn · TF-IDF · Plotly · python-dotenv

## Notes

- CPU-only, lightweight design for laptop demos  
- Rate-limit retries (HTTP 429) with exponential backoff  
- `.env` is gitignored — never commit API keys  
