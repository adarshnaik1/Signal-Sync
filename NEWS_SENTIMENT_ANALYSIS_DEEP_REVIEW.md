# News Sentiment Analysis — Technical Documentation

**Date**: May 19, 2026  
**Project**: Signal Sync — Final Year Project (Indian Stock Market)  
**Feature location**: `src/NEWS_SENTIMENT_ANALYSIS/`  
**Companion doc**: `REDDIT_SENTIMENT_ANALYSIS_DEEP_REVIEW.md` (similar architecture, different data source)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Was Implemented](#2-what-was-implemented)
3. [How It Works (End-to-End)](#3-how-it-works-end-to-end)
4. [Architecture](#4-architecture)
5. [User Inputs & Valid Values](#5-user-inputs--valid-values)
6. [External API (Marketaux)](#6-external-api-marketaux)
7. [Sentiment & Keyword Logic](#7-sentiment--keyword-logic)
8. [Data Structures](#8-data-structures)
9. [File-by-File Reference](#9-file-by-file-reference)
10. [Running the Feature](#10-running-the-feature)
11. [Dashboard Outputs](#11-dashboard-outputs)
12. [Error Handling & Troubleshooting](#12-error-handling--troubleshooting)
13. [Comparison with Reddit Sentiment](#13-comparison-with-reddit-sentiment)
14. [Security & Configuration](#14-security--configuration)
15. [Dependencies](#15-dependencies)
16. [Known Limitations & Future Improvements](#16-known-limitations--future-improvements)

---

## 1. Executive Summary

The **News Sentiment Analysis** feature is a **Python-based, modular data pipeline** that:

1. Fetches **company-related financial news** from the **Marketaux API**
2. Cleans article text and removes duplicates
3. Classifies sentiment using **Marketaux-provided `sentiment_score`** (no custom ML model)
4. Extracts **trending keywords** using **TF-IDF** (scikit-learn)
5. Aggregates statistics and builds a **lightweight text summary**
6. Displays everything in a **Streamlit dashboard** with **Plotly** charts

It is designed for **retail investors** evaluating **long-term** sentiment from **professional news sources**, complementing the Reddit feature (social / community sentiment).

**Design goals**: lightweight, CPU-only, fast on a laptop, easy to demo for a final-year project.

---

## 2. What Was Implemented

### Deliverables

| Item | Path / description |
|------|-------------------|
| API client | `news_analysis/api/marketaux_client.py` |
| Text cleaning | `news_analysis/processing/cleaner.py` |
| TF-IDF keywords | `news_analysis/processing/keyword_extractor.py` |
| Sentiment labels | `news_analysis/processing/sentiment_processor.py` |
| Statistics | `news_analysis/processing/aggregator.py` |
| Summary text | `news_analysis/processing/summarizer.py` |
| Plotly charts | `news_analysis/visualization/charts.py` |
| Streamlit UI | `news_analysis/visualization/dashboard.py` |
| Shared utils | `news_analysis/utils/helpers.py` |
| Pipeline orchestrator | `news_analysis/main.py` |
| Dependencies | `requirements.txt` |
| Env template | `.env.example` |
| Quick start | `README.md` |
| Saved runs | `output/*.json` |

### What was intentionally NOT implemented

- No transformer / LLM summarization
- No custom trained sentiment model (uses Marketaux scores)
- No database (JSON files in `output/` only when `--save` is used)
- No integration yet into the main `streamlit_app/app.py` (standalone app)

---

## 3. How It Works (End-to-End)

### Pipeline phases

```
USER INPUT (company, symbol, limit, days)
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 1 — FETCH (MarketauxClient)    │
│  GET /v1/news/all                     │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 2 — VALIDATE & EXTRACT         │
│  validate_api_response() → data[]     │
│  Empty data[] → error to UI           │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 3 — DEDUPLICATE                │
│  By uuid → url → title hash           │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 4 — CLEAN TEXT (TextCleaner)   │
│  lowercase, URLs, punctuation,        │
│  NLTK stopwords                       │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 5 — KEYWORDS (TF-IDF)          │
│  TfidfVectorizer on cleaned corpus    │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 6 — SENTIMENT                  │
│  entity.sentiment_score per symbol    │
│  → Positive / Neutral / Negative      │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  PHASE 7 — AGGREGATE + SUMMARIZE      │
│  distribution, timeline, sources      │
└───────────────────────────────────────┘
        │
        ▼
STREAMLIT DASHBOARD (or CLI JSON with --save)
```

### Entry points

| Mode | Command | Behavior |
|------|---------|----------|
| **Streamlit (default)** | `streamlit run news_analysis/main.py` | Sidebar form → live API call → dashboard |
| **CLI** | `python news_analysis/main.py -c "..." -s SYMBOL --limit N --days D --save` | Console logs + optional JSON in `output/` |
| **Programmatic** | `from main import run_news_sentiment_analysis` | Returns Python `dict` for other services |

The orchestrator function is:

```python
run_news_sentiment_analysis(
    company_name: str,
    stock_symbol: str,
    articles_limit: int = 50,
    days: int = 7,
    save_output: bool = False,
) -> dict
```

---

## 4. Architecture

### Layered design (mirrors Reddit sentiment)

```
┌─────────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                          │
│  visualization/dashboard.py  +  charts.py (Plotly)          │
│  Streamlit metrics, tables, expanders                       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                 ORCHESTRATION LAYER                           │
│  main.py — run_news_sentiment_analysis()                      │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────┐
│  API LAYER    │  │ PROCESSING      │  │ UTILS        │
│ marketaux_    │  │ cleaner         │  │ helpers      │
│ client.py     │  │ keyword_        │  │ (env, dedup, │
│               │  │ extractor       │  │  validate)   │
│               │  │ sentiment_      │  │              │
│               │  │ processor       │  │              │
│               │  │ aggregator      │  │              │
│               │  │ summarizer      │  │              │
└───────┬───────┘  └─────────────────┘  └──────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICE                            │
│  Marketaux API — https://api.marketaux.com/v1/news/all      │
└─────────────────────────────────────────────────────────────┘
```

### Component communication

```
main.py
  ├── MarketauxClient.fetch_news()
  ├── validate_api_response()          [utils/helpers.py]
  ├── remove_duplicate_articles()      [utils/helpers.py]
  ├── TextCleaner.process_articles()
  ├── KeywordExtractor.extract_from_articles()
  ├── SentimentProcessor.process_articles()
  ├── SentimentAggregator.aggregate()
  ├── NewsSummarizer.generate_summary()
  └── dashboard.render_dashboard()     [Streamlit only]
```

### Project folder structure

```
src/NEWS_SENTIMENT_ANALYSIS/
│
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
│
├── output/                    # JSON exports (--save)
├── requirements.txt
├── .env.example
├── .env                       # gitignored — API key
└── README.md
```

---

## 5. User Inputs & Valid Values

### Streamlit sidebar parameters

| Input | Type | Default | Range / notes |
|-------|------|---------|----------------|
| **Company Name** | string | `Reliance Industries` | Display label only; used in headers and summary text |
| **Stock Symbol** | string | `RELIANCE.NS` | **Must match Marketaux entity symbol** (see below) |
| **Number of Articles** | int (slider) | 50 | 5–100 (API request `limit`, capped at 100 in code) |
| **Number of Days** | int (slider) | 7 | 1–30 → sets `published_after` lookback |

### Stock symbol format (critical for teammates)

Marketaux uses **exchange-qualified tickers** for Indian stocks. The `symbols` query parameter must match how entities are tagged in articles.

| User input | Usually works? | Notes |
|------------|----------------|-------|
| `RELIANCE.NS` | Yes | NSE — recommended for Indian equities |
| `INFY.NS` | Yes | Infosys on NSE |
| `TCS.NS` | Yes | TCS on NSE |
| `INFY` | Often **no articles** | Missing `.NS` suffix; entity filter returns empty `data` |
| `INFY.BO` | Sometimes | BSE listing if covered by API |
| `AAPL` | Yes (US) | US symbols often work without suffix |
| `TSLA` | Yes (US) | US large caps |

**Rule of thumb for NSE stocks**: use `TICKER.NS` (e.g. `HDFCBANK.NS`, `WIPRO.NS`).

Company name does **not** affect the API query — only the symbol does. Use a clear company name for reports and UI only.

### CLI arguments

```bash
python news_analysis/main.py \
  --company "Infosys Limited" \
  --symbol INFY.NS \
  --limit 50 \
  --days 7 \
  --save
```

| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| `--company` | `-c` | Yes | Company display name |
| `--symbol` | `-s` | Yes | Marketaux symbol |
| `--limit` | `-l` | No (default 50) | Max articles |
| `--days` | `-d` | No (default 7) | Lookback days |
| `--save` | — | No | Write JSON to `output/` |

### Example input combinations (demo-ready)

| Company | Symbol | Articles | Days | Use case |
|---------|--------|----------|------|----------|
| Reliance Industries | `RELIANCE.NS` | 50 | 7 | Default demo (verified) |
| Infosys Limited | `INFY.NS` | 30 | 14 | IT sector |
| Tata Consultancy Services | `TCS.NS` | 40 | 7 | Large cap IT |
| HDFC Bank | `HDFCBANK.NS` | 25 | 7 | Banking |
| Apple Inc. | `AAPL` | 20 | 7 | US comparison |

---

## 6. External API (Marketaux)

### Endpoint

```
GET https://api.marketaux.com/v1/news/all
```

### Query parameters (built in `marketaux_client.py`)

| Parameter | Value | Purpose |
|-----------|--------|---------|
| `api_token` | From `MARKETAUX_API_KEY` in `.env` | Authentication |
| `symbols` | User symbol (uppercased) | Filter news by ticker |
| `language` | `en` | English articles |
| `filter_entities` | `true` | Only articles with matched entities |
| `limit` | 1–100 | Max articles returned |
| `published_after` | `YYYY-MM-DD` | UTC date = today − N days |

### Example request URL (structure only)

```
https://api.marketaux.com/v1/news/all
  ?symbols=RELIANCE.NS
  &language=en
  &filter_entities=true
  &limit=50
  &published_after=2026-05-12
  &api_token=YOUR_KEY
```

### Response shape (simplified)

```json
{
  "meta": {
    "found": 8,
    "returned": 3,
    "limit": 3,
    "page": 1
  },
  "data": [
    {
      "uuid": "...",
      "title": "...",
      "description": "...",
      "snippet": "...",
      "url": "...",
      "published_at": "2026-05-18T09:58:57.000000Z",
      "source": "thehindubusinessline.com",
      "entities": [
        {
          "symbol": "RELIANCE.NS",
          "name": "Reliance Industries Limited",
          "sentiment_score": 0.6077,
          "match_score": 20.41
        }
      ]
    }
  ]
}
```

### Client resilience

- **401**: Invalid API key → `MarketauxAPIError`
- **429**: Rate limit → retry up to 3 times with backoff (2s, 4s, …)
- **Network errors**: Retry then fail with clear message
- **Empty `data`**: Pipeline returns user-facing error (not a crash)

---

## 7. Sentiment & Keyword Logic

### Sentiment (no custom ML)

Scores come from `entities[].sentiment_score` for the **requested symbol** (see `extract_entity_sentiment` in `helpers.py`). If no exact match, the first entity’s score is used as fallback.

**Classification rules** (`sentiment_processor.py`):

| Condition | Label |
|-----------|--------|
| `score > 0.1` | **Positive** |
| `score < -0.1` | **Negative** |
| otherwise | **Neutral** |
| `score is None` | **Neutral** (score stored as `0.0`) |

**Overall sentiment** (`aggregator.py`): based on average score and majority label counts.

### Text cleaning (`cleaner.py`)

Applied to combined `title + description + snippet + keywords`:

1. Lowercase  
2. Remove URLs (`http://`, `www.`)  
3. Remove punctuation (keep word characters and spaces)  
4. Remove NLTK English stopwords  
5. Collapse extra whitespace  

Used primarily for **TF-IDF**, not for sentiment (sentiment uses API scores).

### Keyword extraction (`keyword_extractor.py`)

- **Library**: `sklearn.feature_extraction.text.TfidfVectorizer`
- **Settings**: `max_features=500`, `ngram_range=(1, 2)`, English stop words
- **Output**: Top 15 terms with TF-IDF weights
- **Single-article edge case**: Falls back to simple word frequency

### Summary (`summarizer.py`)

- One paragraph **overview** (counts + keyword list)
- Top headlines by sentiment magnitude
- Up to 3 **snippets** (truncated)
- **No** GPT / transformer models

---

## 8. Data Structures

### Pipeline return value (`run_news_sentiment_analysis`)

```python
{
    "company_name": str,
    "symbol": str,
    "articles": list[dict],      # Full enriched articles
    "summary": dict,             # Aggregated stats
    "keywords": dict,            # keywords, keyword_scores, trending_terms
    "news_summary": dict,        # overview, top_headlines, snippets
    "raw_response": dict,        # Full Marketaux JSON
    "generated_at": str,         # ISO UTC timestamp
    "output_path": str,          # Only if save_output=True
    "error": str,                # Only on failure
}
```

### Enriched article fields (after processing)

| Field | Source |
|-------|--------|
| `title`, `description`, `snippet`, `url`, `source`, `published_at` | API |
| `entities` | API |
| `raw_text`, `cleaned_text` | `TextCleaner` |
| `sentiment_score`, `sentiment` | `SentimentProcessor` |

### Summary object (key fields)

```python
{
    "total_articles": int,
    "average_sentiment": float,
    "overall_sentiment": "Positive" | "Negative" | "Neutral",
    "sentiment_distribution": {
        "positive", "negative", "neutral",
        "positive_percentage", "negative_percentage", "neutral_percentage"
    },
    "most_positive_source": {"name": str, "average_score": float},
    "most_negative_source": {"name": str, "average_score": float},
    "source_breakdown": {source: {"count", "avg_score"}},
    "timeline": [{"date": "YYYY-MM-DD", "sentiment_score": float}],
    "analysis_timestamp": str
}
```

### Saved JSON file (`output/{company}_news_sentiment_{timestamp}.json`)

Subset export: company, symbol, summary, keywords, news_summary, and a slim article list (title, source, sentiment, score, published_at, url).

---

## 9. File-by-File Reference

| File | Responsibility |
|------|----------------|
| `main.py` | Orchestrates all phases; CLI vs Streamlit routing |
| `api/marketaux_client.py` | HTTP client, params, retries, error mapping |
| `utils/helpers.py` | `.env` loading, API validation, dedup, entity sentiment, date helper |
| `processing/cleaner.py` | NLTK stopwords + regex cleaning |
| `processing/keyword_extractor.py` | TF-IDF top terms |
| `processing/sentiment_processor.py` | Score → label mapping |
| `processing/aggregator.py` | Stats, timeline, per-source averages |
| `processing/summarizer.py` | Rule-based summary text |
| `visualization/charts.py` | Pie, line, bar, gauge (Plotly) |
| `visualization/dashboard.py` | Streamlit layout, sidebar form, sections |

---

## 10. Running the Feature

### Prerequisites

```bash
cd src/NEWS_SENTIMENT_ANALYSIS
pip install -r requirements.txt
```

Copy `.env.example` → `.env` and set:

```
MARKETAUX_API_KEY=your_api_key_here
```

NLTK stopwords are downloaded automatically on first run.

### Streamlit dashboard (recommended for demos)

```bash
cd src/NEWS_SENTIMENT_ANALYSIS
streamlit run news_analysis/main.py
```

1. Fill sidebar inputs  
2. Click **Run Analysis**  
3. Wait for API + processing (typically 5–20 seconds)  
4. Review charts and tables  

### CLI (batch / testing)

```bash
python news_analysis/main.py \
  --company "Reliance Industries" \
  --symbol RELIANCE.NS \
  --limit 50 \
  --days 7 \
  --save
```

### Programmatic use (for integration)

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src/NEWS_SENTIMENT_ANALYSIS/news_analysis")))
from main import run_news_sentiment_analysis

result = run_news_sentiment_analysis(
    company_name="Infosys Limited",
    stock_symbol="INFY.NS",
    articles_limit=30,
    days=14,
    save_output=True,
)

if "error" in result:
    print(result["error"])
else:
    print(result["summary"]["overall_sentiment"])
```

---

## 11. Dashboard Outputs

After a successful run, the Streamlit UI shows:

| Section | Content |
|---------|---------|
| **Header** | Company name + symbol |
| **Overall Sentiment** | Label, score, positive/negative %, gauge chart |
| **News Statistics** | Total articles, avg sentiment, best/worst sources |
| **Visual Analytics** | Pie (distribution), bar (keywords), line (timeline) |
| **Top Headlines** | Table: title, source, sentiment, published_at |
| **Trending Keywords** | Comma-separated top TF-IDF terms |
| **News Summary** | Overview paragraph + key snippets |
| **Raw JSON** | Expandable full API + pipeline payload |

### Charts (`charts.py`)

| Chart | Type | Data source |
|-------|------|-------------|
| Sentiment distribution | Pie | `summary.sentiment_distribution` |
| Sentiment timeline | Line | `summary.timeline` (daily avg score) |
| Trending keywords | Horizontal bar | `keywords.keyword_scores` |
| Overall score | Gauge | `summary.average_sentiment` |

---

## 12. Error Handling & Troubleshooting

### Common errors

| Message | Likely cause | Fix |
|---------|--------------|-----|
| `No articles returned for this symbol and date range.` | Wrong symbol (e.g. `INFY` vs `INFY.NS`), short date range, or no tagged news | Use `*.NS` for NSE; increase days to 7–14; check raw JSON `meta.found` |
| `MARKETAUX_API_KEY is not set` | Missing `.env` | Copy `.env.example` → `.env` |
| `Unauthorized: invalid or missing API token` | Bad/expired key | Regenerate key on marketaux.com |
| `Rate limit exceeded` | Too many requests | Wait; client auto-retries 3 times |
| `Invalid API response` | Unexpected JSON | Check network; verify API status |

### Debugging tips

1. Expand **Raw News JSON Viewer** — inspect `meta.found` vs `meta.returned`  
2. Test symbol in browser/API client with same `published_after`  
3. Compare `filter_entities=true` vs `false` (would require code change; default is strict)  
4. Free API tiers may return fewer articles than requested `limit`  

### Windows console note

CLI progress logs avoid emoji characters to prevent `UnicodeEncodeError` on cp1252 terminals.

---

## 13. Comparison with Reddit Sentiment

| Aspect | Reddit Sentiment | News Sentiment |
|--------|------------------|----------------|
| **Data source** | Reddit API (PRAW) | Marketaux REST API |
| **Content** | Posts & comments | Financial news articles |
| **Sentiment engine** | VADER (local NLP) | Marketaux `sentiment_score` |
| **Thresholds** | ±0.05 compound | ±0.1 score |
| **Keywords** | Not implemented | TF-IDF |
| **Grouping** | By subreddit | By news source |
| **Config folder** | `config/config.py` | `.env` + `helpers.py` |
| **Main Streamlit app** | Tab in `streamlit_app/app.py` (loads saved JSON) | Standalone `news_analysis/main.py` (live fetch) |
| **Typical symbol** | Company name search | `TICKER.NS` |

Both share: phased pipeline, JSON export, Plotly + Streamlit, modular `services`/`processing`-style layout.

---

## 14. Security & Configuration

| Topic | Practice |
|-------|----------|
| API key | Store in `.env` only; never commit |
| `.gitignore` | Project root ignores `.env` |
| Key load order | `NEWS_SENTIMENT_ANALYSIS/.env` then `Signal-Sync/.env` |
| Read-only | Feature only **reads** news; no trading actions |

**Teammate onboarding**: each developer needs their own Marketaux API key in a local `.env` file.

---

## 15. Dependencies

From `requirements.txt`:

| Package | Role |
|---------|------|
| `requests` | HTTP calls to Marketaux |
| `pandas` | Timeline aggregation, tables |
| `nltk` | English stopwords |
| `scikit-learn` | TF-IDF vectorizer |
| `plotly` | Interactive charts |
| `streamlit` | Web UI |
| `python-dotenv` | Load `MARKETAUX_API_KEY` |

**Runtime**: Python 3.10+ recommended; tested on 3.13. CPU only.

---

## 16. Known Limitations & Future Improvements

### Current limitations

1. **Symbol sensitivity** — Users must know Marketaux ticker format (`.NS` for NSE).  
2. **No auto `.NS` suffix** — Plain `INFY` often returns zero articles.  
3. **Standalone UI** — Not yet a tab in main Signal Sync Streamlit app.  
4. **API plan caps** — Free tier may limit `limit` and historical depth.  
5. **`filter_entities=true`** — Misses articles that mention company name but lack entity tags.  
6. **English only** — `language=en` hardcoded.  
7. **No caching** — Every Run Analysis hits the API (cost + rate limits).  

### Suggested improvements (for future sprints)

- Auto-append `.NS` when symbol has no exchange suffix and country=India  
- Integrate into `streamlit_app/app.py` as third navigation tab  
- Cache API responses (file or Redis) with TTL  
- Load saved `output/*.json` without re-fetching (like Reddit tab)  
- Symbol search / autocomplete via Marketaux entities endpoint  
- Export PDF report for FYP documentation  

---

## Quick Reference Card (for teammates)

```
┌─────────────────────────────────────────────────────────────┐
│  NEWS SENTIMENT ANALYSIS — QUICK START                      │
├─────────────────────────────────────────────────────────────┤
│  cd src/NEWS_SENTIMENT_ANALYSIS                             │
│  pip install -r requirements.txt                            │
│  copy .env.example .env   → add MARKETAUX_API_KEY           │
│  streamlit run news_analysis/main.py                          │
├─────────────────────────────────────────────────────────────┤
│  Inputs:  Company Name | SYMBOL.NS | Articles | Days        │
│  Example: Infosys Limited | INFY.NS | 30 | 7                │
├─────────────────────────────────────────────────────────────┤
│  Code entry:  news_analysis/main.py                         │
│  Pipeline:    run_news_sentiment_analysis()                 │
│  Output JSON: output/*_news_sentiment_*.json (--save)       │
└─────────────────────────────────────────────────────────────┘
```

---

**Document maintained for**: Signal Sync development team · Final Year Project  
**For questions**: see `src/NEWS_SENTIMENT_ANALYSIS/README.md` or inspect `news_analysis/main.py` orchestration flow.
