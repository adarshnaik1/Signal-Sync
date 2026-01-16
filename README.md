# Signal Sync - BGV Verification System

Welcome to the Signal Sync project, an **Agentic AI Retail Investment Advisor** powered by [crewAI](https://crewai.com). This system provides comprehensive Background Verification (BGV) for companies to help retail investors make informed decisions.

## 🎯 Features

The BGV Verification Crew performs:

- **🏢 Company Overview Analysis** - Generates comprehensive company profiles including business description, products, subsidiaries, and market presence
- **👥 Management Research** - Verifies backgrounds of founders and executives, identifying red flags such as past fraud or controversies
- **📊 Financial Irregularities Detection** - Detects accounting anomalies, unusual revenue patterns, debt issues, and audit concerns
- **⚠️ Scam Detection** - Analyzes trading patterns using yfinance data to detect volume spikes and potential market manipulation

## 📁 Project Structure

```
signal_sync/
├── streamlit_app/
│   └── app.py                    # Streamlit frontend
├── src/signal_sync/
│   ├── config/
│   │   ├── agents.yaml           # Agent configurations
│   │   └── tasks.yaml            # Task configurations
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── bgv_schemas.py        # Pydantic models for structured outputs
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stock_tool.py         # Stock data fetcher using yfinance
│   │   └── cache/                # Cached stock data
│   ├── output_data/
│   │   └── bgv_output.json       # Final BGV report output
│   ├── crew.py                   # BGV Crew definition
│   └── main.py                   # Entry points
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## 🚀 Installation

### Prerequisites
- Python >=3.10 <3.14
- [UV](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd signal_sync
   ```

2. **Install dependencies:**
   ```bash
   # Using UV (recommended)
   pip install uv
   crewai install
   
   # Or using pip
   pip install -e .
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required API keys:
   - `OPENAI_API_KEY` - For LLM-based analysis
   - `SERPER_API_KEY` - For web search functionality

## 🖥️ Running the Application

### Option 1: Streamlit Web Interface (Recommended)

```bash
streamlit run streamlit_app/app.py
```

This launches a user-friendly web interface where you can:
- Enter company name and ticker
- Upload annual report PDF
- Trigger BGV verification
- View results with interactive visualizations

### Option 2: Command Line

```bash
# Using CrewAI CLI
crewai run

# Or directly with Python
python -m signal_sync.main

# With arguments
python -m signal_sync.main "Company Name" "TICKER" "Sector" "/path/to/annual_report.pdf"
```

### Option 3: Programmatic Usage

```python
from signal_sync.main import run_bgv

output_path = run_bgv(
    company_name="Infosys Limited",
    ticker="INFY.NS",
    sector="Technology",
    annual_report_path="/path/to/annual_report.pdf"  # Optional
)

print(f"BGV Report saved to: {output_path}")
```

## 📊 Output Format

The BGV verification produces a structured JSON output (`bgv_output.json`) with:

```json
{
  "meta": {
    "generated_at": "2026-01-16T12:00:00Z",
    "pipeline_version": "bgv_v1.0",
    "sources": [...]
  },
  "company": {
    "name": "Company Name",
    "ticker": "TICKER",
    "sector": "Technology",
    "profile_summary": "...",
    ...
  },
  "scores": {
    "trustworthiness_score": 78.5,
    "financial_integrity_score": 72.0,
    "management_risk_score": 45.0,
    "market_manipulation_risk_score": 20.0
  },
  "findings": {
    "overview_findings": [...],
    "management_findings": [...],
    "financial_irregularities": [...],
    "scam_signals": [...]
  },
  "evidence": {
    "documents": [...],
    "time_series": [...],
    "people_profiles": [...]
  },
  "final_verdict": "MODERATE RISK: Proceed with caution..."
}
```

## 🔧 Stock Data Tool

The project includes a custom stock data tool that fetches historical data from Yahoo Finance:

```python
from signal_sync.tools.stock_tool import fetch_stock_data

# Fetch 30 days of daily data
result = fetch_stock_data("AAPL", period="30d", interval="1d")
print(result)
```

The tool automatically:
- Fetches price and volume data
- Calculates key metrics (volatility, volume spikes, etc.)
- Detects anomalies
- Caches data locally for efficiency

## 🏗️ Customization

### Adding New Agents
Edit `src/signal_sync/config/agents.yaml` to define new agents

### Adding New Tasks
Edit `src/signal_sync/config/tasks.yaml` to define new tasks

### Modifying Output Schema
Edit `src/signal_sync/schemas/bgv_schemas.py` to modify the structured output format

## ⚠️ Disclaimer

This tool is for **informational purposes only**. Always conduct your own due diligence before making investment decisions. The BGV verification results should be used as one of many inputs in your investment research process.

## 📚 Support

- [CrewAI Documentation](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
