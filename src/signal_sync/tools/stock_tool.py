# src/signal_sync/tools/stock_tool.py
"""
Stock Data Tool for fetching historical stock data using yfinance.
This tool is used by the Scam Detection Agent to analyze trading patterns.
"""

import os
import json
import statistics
from datetime import datetime, timedelta
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Setup cache directory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CACHE_DIR = os.path.join(ROOT, "src", "signal_sync", "tools", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class StockDataToolInput(BaseModel):
    """Input schema for StockDataTool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'RELIANCE.NS')")
    period: str = Field(
        default="30d",
        description="Time period to fetch data for. Options: '7d', '15d', '30d', '60d', '90d', '1y'"
    )
    interval: str = Field(
        default="1d",
        description="Data interval. Options: '1d' (daily), '1h' (hourly), '5m' (5 minutes)"
    )


class StockDataTool(BaseTool):
    """
    Tool for fetching historical stock data from Yahoo Finance.
    Returns analysis-ready data including price and volume information.
    """
    name: str = "stock_data_fetcher"
    description: str = (
        "Fetches historical stock data (price, volume, etc.) for a given ticker symbol. "
        "Use this tool to analyze trading patterns, detect volume spikes, and identify "
        "potential market manipulation signals. The data is cached locally for efficiency."
    )
    args_schema: Type[BaseModel] = StockDataToolInput

    def _run(self, ticker: str, period: str = "30d", interval: str = "1d") -> str:
        """
        Fetch stock data and return analysis summary along with cache file path.
        """
        try:
            import yfinance as yf
            import pandas as pd
        except ImportError:
            return json.dumps({
                "error": "yfinance or pandas not installed. Please install with: pip install yfinance pandas",
                "success": False
            })

        ticker = ticker.upper().strip()
        
        try:
            # Fetch data from yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval, actions=False)
            
            if df.empty:
                return json.dumps({
                    "error": f"No data found for ticker '{ticker}'. Please verify the ticker symbol.",
                    "success": False
                })
            
            # Convert DataFrame to records
            df_reset = df.reset_index()
            # Handle datetime serialization
            if 'Date' in df_reset.columns:
                df_reset['Date'] = df_reset['Date'].astype(str)
            elif 'Datetime' in df_reset.columns:
                df_reset['Datetime'] = df_reset['Datetime'].astype(str)
            
            records = df_reset.to_dict(orient="records")
            
            # Calculate analysis metrics
            analysis = self._analyze_data(df)
            
            # Prepare output data
            data = {
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "data_points": len(records),
                "date_range": {
                    "from": str(df.index.min()),
                    "to": str(df.index.max())
                },
                "analysis": analysis,
                "data": records
            }
            
            # Save to cache
            timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            fname = f"{ticker}_yfinance_{period}_{interval}_{timestamp}.json"
            cache_path = os.path.join(CACHE_DIR, fname)
            
            with open(cache_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
            
            # Return summary for the agent
            result = {
                "success": True,
                "ticker": ticker,
                "cache_file": cache_path,
                "date_range": data["date_range"],
                "data_points": data["data_points"],
                "analysis_summary": analysis,
                "message": f"Successfully fetched {len(records)} data points for {ticker}. Data cached at: {cache_path}"
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to fetch data for {ticker}: {str(e)}",
                "success": False
            })

    def _analyze_data(self, df) -> Dict[str, Any]:
        """
        Perform basic analysis on the stock data to detect anomalies.
        """
        analysis = {
            "price_metrics": {},
            "volume_metrics": {},
            "anomalies": [],
            "risk_indicators": []
        }
        
        try:
            # Price analysis
            if 'Close' in df.columns:
                closes = df['Close'].dropna().tolist()
                if closes:
                    analysis["price_metrics"] = {
                        "current_price": round(closes[-1], 2),
                        "period_high": round(max(closes), 2),
                        "period_low": round(min(closes), 2),
                        "price_change_percent": round(((closes[-1] - closes[0]) / closes[0]) * 100, 2) if closes[0] != 0 else 0,
                        "volatility": round(statistics.stdev(closes), 2) if len(closes) > 1 else 0
                    }
                    
                    # Check for unusual price movements
                    if len(closes) > 1:
                        daily_changes = [(closes[i] - closes[i-1]) / closes[i-1] * 100 
                                        for i in range(1, len(closes)) if closes[i-1] != 0]
                        if daily_changes:
                            max_daily_change = max(abs(c) for c in daily_changes)
                            if max_daily_change > 10:
                                analysis["anomalies"].append(f"Large daily price movement detected: {max_daily_change:.1f}%")
                                analysis["risk_indicators"].append("HIGH_VOLATILITY")
            
            # Volume analysis
            if 'Volume' in df.columns:
                volumes = df['Volume'].dropna().tolist()
                volumes = [v for v in volumes if isinstance(v, (int, float)) and v > 0]
                
                if volumes:
                    median_vol = statistics.median(volumes)
                    avg_vol = statistics.mean(volumes)
                    max_vol = max(volumes)
                    
                    analysis["volume_metrics"] = {
                        "average_volume": int(avg_vol),
                        "median_volume": int(median_vol),
                        "max_volume": int(max_vol),
                        "volume_spike_ratio": round(max_vol / median_vol, 2) if median_vol > 0 else 0
                    }
                    
                    # Check for volume spikes (potential manipulation indicator)
                    if median_vol > 0:
                        spike_ratio = max_vol / median_vol
                        if spike_ratio > 3:
                            analysis["anomalies"].append(f"Significant volume spike detected: {spike_ratio:.1f}x median volume")
                            analysis["risk_indicators"].append("VOLUME_SPIKE")
                        if spike_ratio > 5:
                            analysis["risk_indicators"].append("POTENTIAL_MANIPULATION")
            
            # Gap analysis (unusual overnight price changes)
            if 'Open' in df.columns and 'Close' in df.columns:
                opens = df['Open'].tolist()
                closes = df['Close'].tolist()
                
                for i in range(1, len(opens)):
                    if closes[i-1] != 0:
                        gap_percent = abs((opens[i] - closes[i-1]) / closes[i-1]) * 100
                        if gap_percent > 5:
                            analysis["anomalies"].append(f"Price gap detected: {gap_percent:.1f}% gap on day {i}")
                            if "PRICE_GAP" not in analysis["risk_indicators"]:
                                analysis["risk_indicators"].append("PRICE_GAP")
                                
        except Exception as e:
            analysis["analysis_error"] = str(e)
        
        return analysis


# Utility function for direct usage (outside of CrewAI)
def fetch_stock_data(ticker: str, period: str = "30d", interval: str = "1d") -> Dict[str, Any]:
    """
    Utility function to fetch stock data directly.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period ('7d', '15d', '30d', '60d', '90d', '1y')
        interval: Data interval ('1d', '1h', '5m')
    
    Returns:
        Dictionary containing fetched data and analysis
    """
    tool = StockDataTool()
    result = tool._run(ticker=ticker, period=period, interval=interval)
    return json.loads(result)


# CLI test
if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = sys.argv[2] if len(sys.argv) > 2 else "15d"
    
    print(f"Fetching data for {ticker}...")
    result = fetch_stock_data(ticker, period=period)
    print(json.dumps(result, indent=2))
