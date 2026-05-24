import json
import os
from typing import List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SRInput(BaseModel):
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


class FindSwingsTool(BaseTool):
    name: str = "find_swings_tool"
    description: str = "Detect swing highs/lows using scipy find_peaks with prominence and distance."
    args_schema: Type[BaseModel] = SRInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            from scipy.signal import find_peaks

            df = _load_df(ohlcv_json).dropna(subset=["High", "Low", "Close"])
            close = df["Close"].to_numpy()
            if close.size < 30:
                return json.dumps({"success": False, "error": "Need at least 30 rows for swing detection."})

            prominence = max(close.mean() * 0.01, 0.5)
            peaks, _ = find_peaks(close, distance=5, prominence=prominence)
            troughs, _ = find_peaks(-close, distance=5, prominence=prominence)

            return json.dumps(
                {
                    "success": True,
                    "swing_highs": [round(float(close[i]), 4) for i in peaks[-10:]],
                    "swing_lows": [round(float(close[i]), 4) for i in troughs[-10:]],
                }
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Swing detection failed: {exc}"})


class ClusterLevelsInput(BaseModel):
    levels_json: str = Field(..., description="JSON list of numeric levels or object containing levels list.")
    threshold_pct: float = Field(default=0.005, description="Cluster threshold as % of level, default 0.5%.")


class ClusterLevelsTool(BaseTool):
    name: str = "cluster_levels_tool"
    description: str = "Merge nearby levels into support/resistance zones using threshold clustering."
    args_schema: Type[BaseModel] = ClusterLevelsInput

    def _run(self, levels_json: str, threshold_pct: float = 0.005) -> str:
        try:
            raw = json.loads(levels_json)
            if isinstance(raw, dict):
                levels = raw.get("levels") or raw.get("swing_highs") or raw.get("swing_lows") or []
            else:
                levels = raw

            levels = sorted([float(x) for x in levels])
            if not levels:
                return json.dumps({"success": True, "clusters": []})

            clusters: List[List[float]] = [[levels[0]]]
            for level in levels[1:]:
                anchor = sum(clusters[-1]) / len(clusters[-1])
                if abs(level - anchor) / max(anchor, 1e-9) <= threshold_pct:
                    clusters[-1].append(level)
                else:
                    clusters.append([level])

            merged = [round(sum(c) / len(c), 4) for c in clusters]
            return json.dumps({"success": True, "clusters": merged})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Level clustering failed: {exc}"})


class VolumeZoneTool(BaseTool):
    name: str = "volume_zone_tool"
    description: str = "Identify high-participation price zones using volume concentration bins."
    args_schema: Type[BaseModel] = SRInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            import numpy as np

            df = _load_df(ohlcv_json).dropna(subset=["Close", "Volume"])
            if df.empty:
                return json.dumps({"success": False, "error": "No valid Close/Volume data."})

            prices = df["Close"].to_numpy()
            volumes = df["Volume"].to_numpy()

            bins = min(20, max(8, len(prices) // 10))
            hist, edges = np.histogram(prices, bins=bins, weights=volumes)
            top_idx = hist.argsort()[-3:][::-1]

            zones = []
            for i in top_idx:
                low = float(edges[i])
                high = float(edges[i + 1])
                zones.append({"zone_low": round(low, 4), "zone_high": round(high, 4), "volume_weight": float(hist[i])})

            return json.dumps({"success": True, "volume_zones": zones})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Volume zone detection failed: {exc}"})


class DynamicSRTool(BaseTool):
    name: str = "dynamic_sr_tool"
    description: str = "Use EMA50/100/200 as dynamic support/resistance context."
    args_schema: Type[BaseModel] = SRInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json).dropna(subset=["Close"])
            close = float(df["Close"].iloc[-1])
            out = {}
            for span in [50, 100, 200]:
                ema = float(df["Close"].ewm(span=span, adjust=False).mean().iloc[-1])
                out[f"ema{span}"] = round(ema, 4)

            dynamic_support = [v for v in out.values() if v <= close]
            dynamic_resistance = [v for v in out.values() if v > close]

            return json.dumps(
                {
                    "success": True,
                    "close": round(close, 4),
                    "ema_levels": out,
                    "dynamic_support": sorted(dynamic_support),
                    "dynamic_resistance": sorted(dynamic_resistance),
                }
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Dynamic SR failed: {exc}"})
