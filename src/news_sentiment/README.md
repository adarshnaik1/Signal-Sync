# News Sentiment Analysis (Indian Stock Market)

A standalone Python module that analyzes **financial news** for Indian companies using **trusted RSS sources only**. It fetches news, extracts full article text, detects financial events, runs **FinBERT** sentiment analysis, validates credibility, and saves structured JSON results. It integrates with the Signal Sync **Streamlit** dashboard.

This module is **separate** from `reddit_sentiment/` (social media) and is designed for academic / final-year project use: lightweight, CPU-only, free tools only—no paid APIs or OpenAI.

---

## What Was Implemented

| Component | Purpose |
|-----------|---------|
| **RSS fetching** | Pull recent articles from Moneycontrol and Economic Times |
| **Company filtering** | Match articles to a company via alias mapping (e.g. INFY → Infosys) |
| **Article extraction** | Download full article body with `newspaper3k` (RSS summaries are not enough) |
| **Text cleaning** | Remove URLs/HTML/noise; keep financial terms intact |
| **Event detection** | Hybrid pipeline: keywords + context + rules (NLTK; optional spaCy) |
| **FinBERT sentiment** | `ProsusAI/finbert` via Hugging Face `transformers` |
| **Fake news filter** | Trusted sources only + multi-source verification + confidence labels |
| **Summary generation** | Template-based readable summary (no LLM APIs) |
| **JSON storage** | Results under `output/` with timestamped filenames |
| **Streamlit page** | Run analysis and view charts from the dashboard |

---

## How a Teammate Should Read This Codebase

### High-level flow

```
User enters company name
        │
        ▼
┌───────────────────┐
│  main.py          │  Orchestrates all phases in order
└─────────┬─────────┘
          │
    ┌─────┴─────┬─────────────┬──────────────┬─────────────┐
    ▼           ▼             ▼              ▼             ▼
 collectors  utils/        analyzers/    validators/    config.py
 (RSS +      text_cleaner  finbert +     fake_news      settings,
  extract)                 event_det.    filter         aliases, feeds
          │
          ▼
    output/*.json  ──►  Streamlit "News Sentiment Analysis" page
```

### Where to start reading

1. **`config.py`** — RSS URLs, company aliases, limits (`MAX_ARTICLES`, `MAX_TEXT_LENGTH`), trusted source names.
2. **`main.py`** — Full pipeline; best single file to understand end-to-end behavior.
3. **`collectors/rss_fetcher.py`** — How feeds are parsed and deduplicated.
4. **`collectors/article_extractor.py`** — Full text download; returns `None` on paywall/errors.
5. **`analyzers/event_detector.py`** — Financial event types and confidence scoring.
6. **`analyzers/finbert_analyzer.py`** — Lazy-loaded FinBERT; truncates text to 1500 chars.
7. **`validators/fake_news_filter.py`** — `HIGH_CONFIDENCE` / `MEDIUM_CONFIDENCE` / `LOW_CONFIDENCE`.
8. **`streamlit_app/app.py`** — Search for `render_news_sentiment_page()` for UI integration.

### Pipeline phases (in `main.py`)

| Phase | Module | What happens |
|-------|--------|----------------|
| 1 | `rss_fetcher` | Fetch all trusted feeds, dedupe by URL |
| 2 | `rss_fetcher` | Filter articles whose title/summary match company aliases |
| 3 | `article_extractor` | Download and parse full article text |
| 4 | `text_cleaner` | Clean and truncate text for analysis |
| 5 | `event_detector` | Detect event type (e.g. Dividend, Acquisition) + impact |
| 6 | `finbert_analyzer` | Positive / Negative / Neutral + score |
| 7 | `fake_news_filter` | Per-article and overall confidence |
| 8 | `main.py` | Template-based summary string |
| 9 | `main.py` | Save JSON to `output/` |

### Design choices (for reviewers / teammates)

- **Trusted sources only** — Articles not from the whitelist in `config.TRUSTED_SOURCES` are dropped after extraction.
- **Lightweight** — Max ~20 articles, 1500 characters per article for FinBERT; model loads once (singleton) and uses CPU.
- **No database** — JSON files only; easy to inspect and demo.
- **Separate from Reddit** — `reddit_sentiment` uses VADER + PRAW; this module uses RSS + FinBERT + financial event rules.

---

## Project Structure

```
news_sentiment/
├── collectors/
│   ├── rss_fetcher.py        # feedparser: Moneycontrol + Economic Times
│   └── article_extractor.py  # newspaper3k: full article text
├── analyzers/
│   ├── finbert_analyzer.py   # ProsusAI/finbert sentiment
│   └── event_detector.py     # Hybrid financial event detection
├── validators/
│   └── fake_news_filter.py   # Source trust + multi-source scoring
├── utils/
│   └── text_cleaner.py       # Clean text, preserve finance terms
├── output/                   # Generated JSON (gitkeep only in repo)
├── config.py                 # Feeds, aliases, limits, trusted sources
├── main.py                   # CLI + run_news_sentiment_analysis()
├── requirements.txt          # Module-specific dependencies
├── __init__.py
└── README.md
```

---

## Trusted News Sources

| Source | RSS feed (active in `config.py`) |
|--------|----------------------------------|
| Moneycontrol | `https://www.moneycontrol.com/rss/business.xml` |
| Economic Times (Markets) | `https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms` |

**Optional later:** Business Standard, LiveMint (names are already in `TRUSTED_SOURCES` for the filter).

---

## Installation

From the **Signal-Sync** project root:

```bash
cd Signal-Sync
pip install -r requirements.txt
```

Or install only this module’s dependencies:

```bash
cd src/news_sentiment
pip install -r requirements.txt
```

**Optional** (better event detection with named entities):

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

**First run note:** FinBERT (`ProsusAI/finbert`) is downloaded from Hugging Face on first use (~400MB). Use a stable internet connection; subsequent runs reuse the cached model.

---

## How to Run

### 1. Command line (recommended for testing)

```bash
cd src/news_sentiment
```

**Basic analysis:**

```bash
python main.py "Infosys"
```

**Other examples:**

```bash
python main.py "TCS"
python main.py "Reliance"
python main.py "ICICI" --limit 10
python main.py "HDFC Bank" --limit 15
```

**Custom output folder / skip saving:**

```bash
python main.py "Wipro" --output ./my_results
python main.py "Infosys" --no-save
```

**Help:**

```bash
python main.py --help
```

Output files are written to:

```text
src/news_sentiment/output/{company}_news_sentiment_YYYYMMDD_HHMMSS.json
```

Example: `icici_news_sentiment_20260531_101941.json`

---

### 2. From project root (with `src` on path)

```bash
cd Signal-Sync
set PYTHONPATH=src
python -c "from news_sentiment.main import run_news_sentiment_analysis; run_news_sentiment_analysis('Infosys')"
```

On PowerShell:

```powershell
cd Signal-Sync
$env:PYTHONPATH = "src"
python -c "from news_sentiment.main import run_news_sentiment_analysis; run_news_sentiment_analysis('Infosys')"
```

---

### 3. Streamlit dashboard

From **Signal-Sync** root:

```bash
streamlit run streamlit_app/app.py
```

In the sidebar, choose **News Sentiment Analysis**:

- **Run Analysis** — Enter company name (e.g. `Infosys`, `TCS`, `Reliance`) and click run.
- **View Results** — Pick a saved JSON report; see sentiment, confidence meter, event timeline, article cards, and Plotly charts.

---

## Programmatic Usage

```python
from pathlib import Path
import sys

sys.path.insert(0, "src")  # or run from src/news_sentiment

from news_sentiment.main import run_news_sentiment_analysis

result = run_news_sentiment_analysis(
    company="Infosys",
    max_articles=15,
    save_output=True,
)

print(result["overall_sentiment"])
print(result["confidence"])
print(result["summary"])
print(result.get("output_path"))
```

---

## Output JSON Format

```json
{
  "company": "Icici",
  "overall_sentiment": "Negative",
  "average_sentiment_score": 0.9667,
  "confidence": "MEDIUM_CONFIDENCE",
  "events_detected": ["Dividend"],
  "summary": "Icici received negative sentiment ...",
  "articles": [
    {
      "source": "Moneycontrol",
      "title": "...",
      "url": "https://...",
      "published_date": "...",
      "event_type": "Dividend",
      "sentiment": "Negative",
      "sentiment_score": 0.9617,
      "confidence": 55
    }
  ],
  "generated_at": "2026-05-31T04:49:41.312188Z"
}
```

**Confidence labels:** `HIGH_CONFIDENCE`, `MEDIUM_CONFIDENCE`, `LOW_CONFIDENCE` (see `validators/fake_news_filter.py`).

---

## Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ARTICLES_PER_FETCH` | 20 | Max items per RSS source per run |
| `MAX_ARTICLES_TO_PROCESS` | 20 | Cap after company filter |
| `MAX_TEXT_LENGTH` | 1500 | Characters sent to FinBERT |
| `COMPANY_ALIASES` | dict | Map company keys to search strings |
| `FINBERT_MODEL` | `ProsusAI/finbert` | Hugging Face model id |

To add a company, extend `COMPANY_ALIASES` in `config.py`:

```python
"your company": ["alias1", "alias2", "ticker"],
```

---

## Supported Companies (aliases in config)

Examples already configured: Infosys, TCS, Reliance, HDFC Bank, ICICI Bank, Wipro, Tata Motors, Bharti Airtel, ITC, HCL Tech, Maruti, SBI, Axis Bank, Bajaj Finance, L&T.

If no articles are found, the company string may not match current RSS headlines—try the full name or a common alias from `config.py`.

---

## Dependencies (free only)

| Library | Role |
|---------|------|
| feedparser | RSS parsing |
| newspaper3k | Full article download |
| transformers + torch | FinBERT (CPU) |
| nltk | Sentence tokenization for events |
| beautifulsoup4 / lxml_html_clean | HTML handling |
| pandas, plotly | Streamlit charts |

See `requirements.txt` for pinned minimum versions.

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `No articles found` | Company not in recent headlines; check aliases in `config.py` or try `ICICI`, `Reliance`, etc. |
| Extraction returns 0 articles | Paywall or site blocking; pipeline still completes with an error message in JSON |
| Slow first run | FinBERT model download; wait or pre-download with Hugging Face CLI |
| `UnicodeEncodeError` on Windows console | Pipeline uses ASCII log prefixes; use Streamlit or redirect output if needed |
| Import errors in Streamlit | Run from `Signal-Sync` root; ensure `src` is on path (see `streamlit_app/app.py`) |

---

## Relation to Other Signal Sync Features

| Module | Data source | Sentiment model | Dashboard page |
|--------|-------------|-----------------|----------------|
| `news_sentiment/` | Moneycontrol, ET RSS | FinBERT | News Sentiment Analysis |
| `reddit_sentiment/` | Reddit (PRAW) | VADER | Reddit News Analysis |
| `signal_sync/` | BGV / CrewAI | N/A | BGV Verification |

---

## Academic / Project Notes

- Intended for **8GB RAM, CPU-only** laptops.
- Prioritizes **explainability** (rules + FinBERT labels) over black-box LLMs.
- **Not financial advice** — for educational and demonstration purposes only.

---

## Quick Command Cheat Sheet

```bash
# Install
cd Signal-Sync/src/news_sentiment && pip install -r requirements.txt

# Run CLI
python main.py "Infosys"
python main.py "TCS" --limit 15

# Streamlit
cd Signal-Sync && streamlit run streamlit_app/app.py
```
