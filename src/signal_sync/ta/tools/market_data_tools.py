import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CACHE_DIR = os.path.join(ROOT, "src", "signal_sync", "ta", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

VALID_YF_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
PERIOD_ALIASES = {
    "1w": "1y",
    "1wk": "1y",
    "1week": "1y",
    "weekly": "1y",
}


def _normalize_period(period: str, default: str = "1y") -> str:
    value = str(period).strip().lower()
    if value in PERIOD_ALIASES:
        return PERIOD_ALIASES[value]
    if value in VALID_YF_PERIODS:
        return value
    return default


class FetchOHLCVInput(BaseModel):
    ticker: str = Field(..., description="Ticker symbol like 'TCS.NS' or 'INFY.NS'.")
    period: str = Field(default="1y", description="yfinance period like '6mo', '1y', '2y'.")
    interval: str = Field(default="1d", description="Use '1d' or '1wk' for MVP.")
    auto_adjust: bool = Field(default=True, description="Use adjusted prices for deterministic TA.")


class FetchOHLCVTool(BaseTool):
    name: str = "fetch_ohlcv_tool"
    description: str = "Fetch OHLCV data from Yahoo Finance using adjusted prices when requested."
    args_schema: Type[BaseModel] = FetchOHLCVInput

    @staticmethod
    def _normalize_ohlcv_columns(df):
        import pandas as pd

        normalized = []
        for col in df.columns:
            if isinstance(col, tuple):
                parts = [str(part).strip() for part in col if part not in (None, "")]
                col_name = parts[0] if parts else ""
            else:
                col_name = str(col).strip()
            normalized.append(col_name)
        df.columns = normalized

        rename_map = {}
        for col in df.columns:
            lower = col.lower()
            if lower in ("date", "timestamp") or lower.startswith("date"):
                rename_map[col] = "Date"
            elif lower.startswith("datetime"):
                rename_map[col] = "Datetime"
            elif lower.startswith("open"):
                rename_map[col] = "Open"
            elif lower.startswith("high"):
                rename_map[col] = "High"
            elif lower.startswith("low"):
                rename_map[col] = "Low"
            elif lower.startswith("close"):
                rename_map[col] = "Close"
            elif lower.startswith("adj close") and "Close" not in df.columns:
                rename_map[col] = "Close"
            elif lower.startswith("volume"):
                rename_map[col] = "Volume"

        if rename_map:
            df = df.rename(columns=rename_map)

        if isinstance(df.columns, pd.Index):
            deduped_cols = []
            seen = {}
            for col in df.columns:
                count = seen.get(col, 0)
                deduped_cols.append(col if count == 0 else f"{col}_{count}")
                seen[col] = count + 1
            df.columns = deduped_cols

        return df

    def _run(self, ticker: str, period: str = "1y", interval: str = "1d", auto_adjust: bool = True) -> str:
        try:
            import pandas as pd
            import yfinance as yf
        except ImportError:
            return json.dumps({"success": False, "error": "Missing dependencies. Install pandas and yfinance."})

        symbol = ticker.strip().upper()
        normalized_period = _normalize_period(period)
        try:
            df = yf.download(
                tickers=symbol,
                period=normalized_period,
                interval=interval,
                auto_adjust=auto_adjust,
                progress=False,
                threads=False,
            )
            if df is None or df.empty:
                return json.dumps({"success": False, "error": f"No data found for {symbol}."})
            

            df = df.reset_index()
            df = self._normalize_ohlcv_columns(df)
            datetime_col = "Date" if "Date" in df.columns else "Datetime"
            df[datetime_col] = df[datetime_col].astype(str)
            records = df.to_dict(orient="records")

            payload = {
                "ticker": symbol,
                "period": period,
                "interval": interval,
                "auto_adjust": auto_adjust,
                "rows": len(records),
                "ohlcv": records,
            }

            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            cache_file = os.path.join(CACHE_DIR, f"{symbol}_{period}_{interval}_{ts}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)

            return json.dumps(
                {
                    "success": True,
                    "ticker": symbol,
                    "cache_file": cache_file,
                    "rows": len(records),
                    "interval": interval,
                    "period": normalized_period,
                    "auto_adjust": auto_adjust,
                    "ohlcv": records,
                },
                default=str,
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Failed to fetch OHLCV: {exc}"})


class FetchActionsInput(BaseModel):
    ticker: str = Field(..., description="Ticker symbol like 'TCS.NS'.")


class FetchActionsTool(BaseTool):
    name: str = "fetch_actions_tool"
    description: str = "Fetch corporate actions (dividends/splits) from Yahoo Finance."
    args_schema: Type[BaseModel] = FetchActionsInput

    def _run(self, ticker: str) -> str:
        try:
            import yfinance as yf
        except ImportError:
            return json.dumps({"success": False, "error": "Missing dependency: yfinance."})

        symbol = ticker.strip().upper()
        try:
            tk = yf.Ticker(symbol)
            actions = tk.actions
            if actions is None or actions.empty:
                return json.dumps({"success": True, "ticker": symbol, "actions": []})

            actions = actions.reset_index()
            dt_col = "Date" if "Date" in actions.columns else actions.columns[0]
            actions[dt_col] = actions[dt_col].astype(str)
            return json.dumps({"success": True, "ticker": symbol, "actions": actions.to_dict(orient="records")}, default=str)
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Failed to fetch actions: {exc}"})


class ValidateDataInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string with list of OHLCV rows or object containing 'ohlcv'.")


class ValidateDataTool(BaseTool):
    name: str = "validate_data_tool"
    description: str = "Clean and validate OHLCV data: remove duplicates, sort chronologically, and drop invalid rows."
    args_schema: Type[BaseModel] = ValidateDataInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            import pandas as pd
        except ImportError:
            return json.dumps({"success": False, "error": "Missing dependency: pandas."})

        try:
            raw = json.loads(ohlcv_json)
            rows = raw.get("ohlcv", raw) if isinstance(raw, dict) else raw
            if not isinstance(rows, list) or not rows:
                return json.dumps({"success": False, "error": "No OHLCV rows provided."})

            df = pd.DataFrame(rows)
            rename_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "date": "Date",
                "datetime": "Datetime",
                "timestamp": "Date",
            }
            for src, dst in rename_map.items():
                if src in df.columns and dst not in df.columns:
                    df = df.rename(columns={src: dst})

            dt_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else None)
            if dt_col is None:
                return json.dumps({"success": False, "error": "Expected Date/Datetime column."})

            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            before = len(df)
            df = df.dropna(subset=[c for c in ["Open", "High", "Low", "Close"] if c in df.columns])
            df = df.drop_duplicates(subset=[dt_col])
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
            df = df.dropna(subset=[dt_col]).sort_values(dt_col)
            df[dt_col] = df[dt_col].astype(str)
            after = len(df)

            return json.dumps(
                {
                    "success": True,
                    "dropped_rows": before - after,
                    "rows": after,
                    "ohlcv": df.to_dict(orient="records"),
                },
                default=str,
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Validation failed: {exc}"})


class FetchMarketDataBundleInput(BaseModel):
    ticker: str = Field(..., description="Ticker symbol like 'TCS.NS' or 'INFY.NS'.")
    daily_period: str = Field(default="3mo", description="Daily OHLCV period for the primary dataset.")
    weekly_period: str = Field(default="1y", description="Weekly OHLCV period for the secondary dataset.")
    auto_adjust: bool = Field(default=True, description="Use adjusted prices for deterministic TA.")


class FetchMarketDataBundleTool(BaseTool):
    name: str = "fetch_market_data_bundle_tool"
    description: str = "Fetch daily and weekly OHLCV, corporate actions, and validated OHLCV in one deterministic pass."
    args_schema: Type[BaseModel] = FetchMarketDataBundleInput

    def _run(self, ticker: str, daily_period: str = "3mo", weekly_period: str = "1y", auto_adjust: bool = True) -> str:
        try:
            daily_raw = FetchOHLCVTool()._run(ticker=ticker, period=_normalize_period(daily_period, "3mo"), interval="1d", auto_adjust=auto_adjust)
            daily_data = json.loads(daily_raw)
            if not daily_data.get("success"):
                return json.dumps({"success": False, "error": daily_data.get("error", "Daily OHLCV fetch failed.")})

            weekly_raw = FetchOHLCVTool()._run(ticker=ticker, period=_normalize_period(weekly_period, "1y"), interval="1wk", auto_adjust=auto_adjust)
            weekly_data = json.loads(weekly_raw)

            actions_raw = FetchActionsTool()._run(ticker=ticker)
            actions_data = json.loads(actions_raw)

            validated_raw = ValidateDataTool()._run(json.dumps({"ohlcv": daily_data.get("ohlcv", [])}))
            validated_data = json.loads(validated_raw)

            bundle = {
                "success": True,
                "ticker": daily_data.get("ticker", ticker.strip().upper()),
                "daily_ohlcv": daily_data.get("ohlcv", []),
                "weekly_ohlcv": weekly_data.get("ohlcv", []) if weekly_data.get("success") else [],
                "actions": actions_data.get("actions", []) if actions_data.get("success") else [],
                "validation": {
                    "success": validated_data.get("success", False),
                    "rows": validated_data.get("rows", 0),
                    "dropped_rows": validated_data.get("dropped_rows", 0),
                },
            }

            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            bundle_file = os.path.join(CACHE_DIR, f"{ticker.strip().upper()}_bundle_{ts}.json")
            with open(bundle_file, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2, default=str)

            return json.dumps(
                {
                    "success": True,
                    "ticker": daily_data.get("ticker", ticker.strip().upper()),
                    "bundle_file": bundle_file,
                    "daily_rows": len(bundle["daily_ohlcv"]),
                    "weekly_rows": len(bundle["weekly_ohlcv"]),
                    "actions_count": len(bundle["actions"]),
                    "validation": bundle["validation"],
                },
                default=str,
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Market data bundle failed: {exc}"})
