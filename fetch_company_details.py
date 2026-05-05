"""Fetch company details from Yahoo Finance.

Usage:
    python fetch_company_details.py AAPL
    python fetch_company_details.py RELIANCE.NS --json
    python fetch_company_details.py MSFT --output msft_details.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def coerce_number(value: Any) -> Optional[float]:
    """Convert Yahoo Finance values to floats when possible."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip()
        if not text or text.lower() in {"none", "nan", "null"}:
            return None
        return float(text.replace(",", ""))
    except (TypeError, ValueError):
        return None


def format_money(value: Any) -> str:
    number = coerce_number(value)
    if number is None:
        return "N/A"
    abs_value = abs(number)
    if abs_value >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"{number:,.2f}"
    return f"{number:.2f}"


def format_percent(value: Any) -> str:
    number = coerce_number(value)
    if number is None:
        return "N/A"
    if abs(number) <= 1:
        number *= 100
    return f"{number:.2f}%"


def get_first(mapping: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, "", "N/A"):
            return mapping[key]
    return None


def extract_company_details(ticker_symbol: str) -> Dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - import failure is runtime specific
        raise SystemExit(
            "yfinance is not installed. Install it with: pip install yfinance"
        ) from exc

    ticker = yf.Ticker(ticker_symbol)

    info: Dict[str, Any] = {}
    try:
        info = ticker.get_info()
    except Exception:
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

    fast_info: Dict[str, Any] = {}
    try:
        fast_info = dict(ticker.fast_info)
    except Exception:
        fast_info = {}

    quote = {
        "symbol": ticker_symbol.upper(),
        "shortName": get_first(info, "shortName", "longName"),
        "longName": info.get("longName"),
        "industry": info.get("industry"),
        "sector": info.get("sector"),
        "country": info.get("country"),
        "website": info.get("website"),
        "currency": get_first(info, "currency", "financialCurrency"),
        "exchange": info.get("exchange"),
        "marketState": info.get("marketState"),
        "currentPrice": get_first(fast_info, "lastPrice", "last_price", "regularMarketPrice")
        or info.get("currentPrice")
        or info.get("regularMarketPrice"),
        "previousClose": get_first(fast_info, "previousClose") or info.get("previousClose"),
        "open": get_first(fast_info, "open") or info.get("open"),
        "dayHigh": get_first(fast_info, "dayHigh") or info.get("dayHigh"),
        "dayLow": get_first(fast_info, "dayLow") or info.get("dayLow"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh") or fast_info.get("yearHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow") or fast_info.get("yearLow"),
        "marketCap": info.get("marketCap") or fast_info.get("marketCap"),
        "sharesOutstanding": info.get("sharesOutstanding"),
        "beta": info.get("beta"),
        "employees": info.get("fullTimeEmployees"),
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }

    ratios = {
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
        "priceToBook": info.get("priceToBook"),
        "priceToSales": info.get("priceToSalesTrailing12Months"),
        "pegRatio": info.get("pegRatio"),
        "profitMargin": info.get("profitMargins"),
        "operatingMargin": info.get("operatingMargins"),
        "grossMargin": info.get("grossMargins"),
        "returnOnAssets": info.get("returnOnAssets"),
        "returnOnEquity": info.get("returnOnEquity"),
        "debtToEquity": info.get("debtToEquity"),
        "currentRatio": info.get("currentRatio"),
        "quickRatio": info.get("quickRatio"),
        "dividendYield": info.get("dividendYield"),
        "payoutRatio": info.get("payoutRatio"),
    }

    summary = {
        "quote": quote,
        "ratios": ratios,
        "highlights": {
            "targetMeanPrice": info.get("targetMeanPrice"),
            "recommendationKey": info.get("recommendationKey"),
            "recommendationMean": info.get("recommendationMean"),
            "targetHighPrice": info.get("targetHighPrice"),
            "targetLowPrice": info.get("targetLowPrice"),
        },
        "financials": {
            "revenue": info.get("totalRevenue"),
            "grossProfits": info.get("grossProfits"),
            "ebitda": info.get("ebitda"),
            "freeCashflow": info.get("freeCashflow"),
            "operatingCashflow": info.get("operatingCashflow"),
            "totalCash": info.get("totalCash"),
            "totalDebt": info.get("totalDebt"),
        },
    }

    return summary


def print_human_readable(data: Dict[str, Any]) -> None:
    quote = data["quote"]
    ratios = data["ratios"]
    highlights = data["highlights"]
    financials = data["financials"]

    print(f"Company: {quote.get('shortName') or quote['symbol']}")
    print(f"Symbol: {quote['symbol']}")
    if quote.get("sector") or quote.get("industry"):
        print(f"Sector / Industry: {quote.get('sector') or 'N/A'} / {quote.get('industry') or 'N/A'}")
    print(f"Exchange: {quote.get('exchange') or 'N/A'}")
    print(f"Country: {quote.get('country') or 'N/A'}")
    print(f"Website: {quote.get('website') or 'N/A'}")
    print()
    print("Price")
    print(f"  Current: {format_money(quote.get('currentPrice'))}")
    print(f"  Previous Close: {format_money(quote.get('previousClose'))}")
    print(f"  Open: {format_money(quote.get('open'))}")
    print(f"  Day Range: {format_money(quote.get('dayLow'))} - {format_money(quote.get('dayHigh'))}")
    print(f"  52W Range: {format_money(quote.get('fiftyTwoWeekLow'))} - {format_money(quote.get('fiftyTwoWeekHigh'))}")
    print(f"  Market Cap: {format_money(quote.get('marketCap'))}")
    print()
    print("Ratios")
    print(f"  Trailing P/E: {ratios.get('trailingPE') or 'N/A'}")
    print(f"  Forward P/E: {ratios.get('forwardPE') or 'N/A'}")
    print(f"  Price to Book: {ratios.get('priceToBook') or 'N/A'}")
    print(f"  Price to Sales: {ratios.get('priceToSales') or 'N/A'}")
    print(f"  PEG Ratio: {ratios.get('pegRatio') or 'N/A'}")
    print(f"  Profit Margin: {format_percent(ratios.get('profitMargin'))}")
    print(f"  Operating Margin: {format_percent(ratios.get('operatingMargin'))}")
    print(f"  Gross Margin: {format_percent(ratios.get('grossMargin'))}")
    print(f"  ROA: {format_percent(ratios.get('returnOnAssets'))}")
    print(f"  ROE: {format_percent(ratios.get('returnOnEquity'))}")
    print(f"  Debt / Equity: {ratios.get('debtToEquity') or 'N/A'}")
    print(f"  Current Ratio: {ratios.get('currentRatio') or 'N/A'}")
    print(f"  Quick Ratio: {ratios.get('quickRatio') or 'N/A'}")
    print(f"  Dividend Yield: {format_percent(ratios.get('dividendYield'))}")
    print(f"  Payout Ratio: {format_percent(ratios.get('payoutRatio'))}")
    print()
    print("Valuation / Analyst Snapshot")
    print(f"  Recommendation: {highlights.get('recommendationKey') or 'N/A'}")
    print(f"  Mean Target Price: {format_money(highlights.get('targetMeanPrice'))}")
    print(f"  High Target Price: {format_money(highlights.get('targetHighPrice'))}")
    print(f"  Low Target Price: {format_money(highlights.get('targetLowPrice'))}")
    print(f"  Recommendation Mean: {highlights.get('recommendationMean') or 'N/A'}")
    print()
    print("Financial Snapshot")
    print(f"  Revenue: {format_money(financials.get('revenue'))}")
    print(f"  Gross Profit: {format_money(financials.get('grossProfits'))}")
    print(f"  EBITDA: {format_money(financials.get('ebitda'))}")
    print(f"  Free Cash Flow: {format_money(financials.get('freeCashflow'))}")
    print(f"  Operating Cash Flow: {format_money(financials.get('operatingCashflow'))}")
    print(f"  Total Cash: {format_money(financials.get('totalCash'))}")
    print(f"  Total Debt: {format_money(financials.get('totalDebt'))}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch company details, price data, and financial ratios from Yahoo Finance."
    )
    parser.add_argument("ticker", help="Ticker symbol, for example AAPL or RELIANCE.NS")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a human-readable summary")
    parser.add_argument("--output", type=Path, help="Write the result to a JSON file")

    args = parser.parse_args()

    data = extract_company_details(args.ticker.strip())

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, ensure_ascii=False, default=str)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print_human_readable(data)


if __name__ == "__main__":
    main()