import json
import os
from typing import List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PatternInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string or file path containing OHLCV list/object. Supports keys: ohlcv, daily_ohlcv, weekly_ohlcv.")


def _extract_ohlcv_rows(raw):
    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        for key in ["ohlcv", "daily_ohlcv", "weekly_ohlcv"]:
            value = raw.get(key)
            if isinstance(value, list):
                return value

        if all(k in raw for k in ["Open", "High", "Low", "Close"]):
            return [raw]

        if all(k in raw for k in ["open", "high", "low", "close"]):
            return [raw]

    raise ValueError("No OHLCV rows found. Expected list or dict with keys: ohlcv/daily_ohlcv/weekly_ohlcv.")


def _load_df(ohlcv_json: str):
    import pandas as pd

    if os.path.exists(ohlcv_json):
        with open(ohlcv_json, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = json.loads(ohlcv_json)
    rows = _extract_ohlcv_rows(raw)
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
    if dt_col:
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
        df = df.sort_values(dt_col)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _last_row(df):
    return df.iloc[-1], df.iloc[-2] if len(df) > 1 else (None, None)


class DetectCandlestickPatternsTool(BaseTool):
    name: str = "detect_candlestick_patterns_tool"
    description: str = "Detect deterministic candlestick patterns: doji, hammer, engulfing, shooting star."
    args_schema: Type[BaseModel] = PatternInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json).dropna(subset=["Open", "High", "Low", "Close"])
            if len(df) < 2:
                return json.dumps({"success": False, "error": "Need at least 2 candles."})

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            body = abs(latest["Close"] - latest["Open"])
            candle_range = max(latest["High"] - latest["Low"], 1e-9)
            upper_wick = latest["High"] - max(latest["Open"], latest["Close"])
            lower_wick = min(latest["Open"], latest["Close"]) - latest["Low"]

            patterns: List[str] = []

            if body / candle_range < 0.1:
                patterns.append("doji")

            if lower_wick > body * 2 and upper_wick < body:
                patterns.append("hammer")

            if upper_wick > body * 2 and lower_wick < body:
                patterns.append("shooting_star")

            prev_body_low = min(prev["Open"], prev["Close"])
            prev_body_high = max(prev["Open"], prev["Close"])
            cur_body_low = min(latest["Open"], latest["Close"])
            cur_body_high = max(latest["Open"], latest["Close"])

            if latest["Close"] > latest["Open"] and prev["Close"] < prev["Open"] and cur_body_low <= prev_body_low and cur_body_high >= prev_body_high:
                patterns.append("bullish_engulfing")

            if latest["Close"] < latest["Open"] and prev["Close"] > prev["Open"] and cur_body_low <= prev_body_low and cur_body_high >= prev_body_high:
                patterns.append("bearish_engulfing")

            return json.dumps({"success": True, "candlestick_patterns": patterns})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Candlestick detection failed: {exc}"})


class DetectChartPatternsTool(BaseTool):
    name: str = "detect_chart_patterns_tool"
    description: str = "Detect deterministic chart structures using local extrema: double top, double bottom, channel proxy."
    args_schema: Type[BaseModel] = PatternInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            import numpy as np
            from scipy.signal import find_peaks

            df = _load_df(ohlcv_json).dropna(subset=["Close"])
            close = df["Close"].to_numpy()
            if close.size < 40:
                return json.dumps({"success": False, "error": "Need at least 40 data points."})

            peaks, _ = find_peaks(close, distance=5)
            troughs, _ = find_peaks(-close, distance=5)

            patterns = []

            if len(peaks) >= 2:
                p1, p2 = peaks[-2], peaks[-1]
                top1, top2 = close[p1], close[p2]
                if abs(top1 - top2) / max(top1, 1e-9) < 0.03:
                    valley = close[min(p1, p2): max(p1, p2) + 1].min()
                    if (min(top1, top2) - valley) / max(min(top1, top2), 1e-9) > 0.04:
                        patterns.append("double_top")

            if len(troughs) >= 2:
                t1, t2 = troughs[-2], troughs[-1]
                bot1, bot2 = close[t1], close[t2]
                if abs(bot1 - bot2) / max(bot1, 1e-9) < 0.03:
                    ridge = close[min(t1, t2): max(t1, t2) + 1].max()
                    if (ridge - max(bot1, bot2)) / max(ridge, 1e-9) > 0.04:
                        patterns.append("double_bottom")

            x = np.arange(len(close))
            slope, _ = np.polyfit(x[-30:], close[-30:], 1)
            rel_std = float(np.std(close[-30:]) / max(np.mean(close[-30:]), 1e-9))
            if abs(slope) < np.mean(close[-30:]) * 0.001 and rel_std < 0.04:
                patterns.append("channel")

            return json.dumps({"success": True, "chart_patterns": patterns})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Chart pattern detection failed: {exc}"})
