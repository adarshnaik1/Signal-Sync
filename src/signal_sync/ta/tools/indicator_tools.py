import json
import math
import os
from typing import Dict, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class IndicatorInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string or file path containing OHLCV list/object. Supports keys: ohlcv, daily_ohlcv, weekly_ohlcv.")


def _safe_round(value, ndigits: int = 4):
    try:
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            return None
        return round(numeric, ndigits)
    except Exception:
        return None


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


class ComputeEMATool(BaseTool):
    name: str = "compute_ema_tool"
    description: str = "Compute EMA20/50/100/200 on Close price."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            out = {}
            for span in [20, 50, 100, 200]:
                col = f"ema{span}"
                df[col] = df["Close"].ewm(span=span, adjust=False).mean()
                out[col] = _safe_round(df[col].iloc[-1]) if not df[col].empty else None
            return json.dumps({"success": True, **out})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"EMA failed: {exc}"})


class ComputeRSITool(BaseTool):
    name: str = "compute_rsi_tool"
    description: str = "Compute RSI(14) from Close prices."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            delta = df["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            # If avg_loss is zero and gains exist, RSI should be 100 instead of NaN.
            rs = avg_gain / avg_loss.replace(0, 1e-12)
            rsi = 100 - (100 / (1 + rs))
            if avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] > 0:
                rsi_value = 100.0
            elif avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] == 0:
                rsi_value = 50.0
            else:
                rsi_value = rsi.iloc[-1]
            return json.dumps({"success": True, "rsi": _safe_round(rsi_value)})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"RSI failed: {exc}"})


class ComputeMACDTool(BaseTool):
    name: str = "compute_macd_tool"
    description: str = "Compute MACD(12,26,9) from Close prices."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            ema12 = df["Close"].ewm(span=12, adjust=False).mean()
            ema26 = df["Close"].ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            return json.dumps(
                {
                    "success": True,
                    "macd": _safe_round(macd.iloc[-1]),
                    "macd_signal": _safe_round(signal.iloc[-1]),
                    "macd_histogram": _safe_round(hist.iloc[-1]),
                }
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"MACD failed: {exc}"})


class ComputeATRTool(BaseTool):
    name: str = "compute_atr_tool"
    description: str = "Compute ATR(14) from OHLC prices."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            hl = df["High"] - df["Low"]
            hc = (df["High"] - df["Close"].shift()).abs()
            lc = (df["Low"] - df["Close"].shift()).abs()
            tr = hl.to_frame("hl")
            tr["hc"] = hc
            tr["lc"] = lc
            atr = tr.max(axis=1).rolling(14).mean()
            return json.dumps({"success": True, "atr": _safe_round(atr.iloc[-1])})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"ATR failed: {exc}"})


class ComputeBollingerTool(BaseTool):
    name: str = "compute_bollinger_tool"
    description: str = "Compute Bollinger Bands(20, 2)."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            basis = df["Close"].rolling(20).mean()
            std = df["Close"].rolling(20).std()
            upper = basis + 2 * std
            lower = basis - 2 * std
            return json.dumps(
                {
                    "success": True,
                    "bb_basis": _safe_round(basis.iloc[-1]),
                    "bb_upper": _safe_round(upper.iloc[-1]),
                    "bb_lower": _safe_round(lower.iloc[-1]),
                }
            )
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Bollinger failed: {exc}"})


class ComputeOBVTool(BaseTool):
    name: str = "compute_obv_tool"
    description: str = "Compute OBV from Close and Volume."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            direction = df["Close"].diff().fillna(0)
            sign = direction.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
            obv = (sign * df["Volume"].fillna(0)).cumsum()
            return json.dumps({"success": True, "obv": _safe_round(obv.iloc[-1])})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"OBV failed: {exc}"})


class ComputeSMATool(BaseTool):
    name: str = "compute_sma_tool"
    description: str = "Compute SMA20/50/100/200 on Close price."
    args_schema: Type[BaseModel] = IndicatorInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            out: Dict[str, object] = {}
            for period in [20, 50, 100, 200]:
                series = df["Close"].rolling(period).mean()
                out[f"sma{period}"] = _safe_round(series.iloc[-1])
            return json.dumps({"success": True, **out})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"SMA failed: {exc}"})


class IndicatorRuleEngineInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string or file path containing OHLCV list/object. Supports keys: ohlcv, daily_ohlcv, weekly_ohlcv.")


class IndicatorRuleEngineTool(BaseTool):
    name: str = "indicator_rule_engine_tool"
    description: str = "Compute all core technical indicators in one deterministic pass: SMA, EMA, RSI, MACD, ATR, Bollinger Bands, and OBV."
    args_schema: Type[BaseModel] = IndicatorRuleEngineInput

    def _run(self, ohlcv_json: str) -> str:
        try:
            df = _load_df(ohlcv_json)
            if df.empty or "Close" not in df.columns:
                return json.dumps({"success": False, "error": "No valid OHLCV data provided."})

            out: Dict[str, object] = {"success": True}

            close = df["Close"]
            high = df["High"] if "High" in df.columns else close
            low = df["Low"] if "Low" in df.columns else close
            volume = df["Volume"] if "Volume" in df.columns else None

            # Trend: SMA and EMA family
            sma_levels = {}
            ema_levels = {}
            for period in [20, 50, 100, 200]:
                sma_series = close.rolling(period).mean()
                ema_series = close.ewm(span=period, adjust=False).mean()
                sma_levels[f"sma{period}"] = _safe_round(sma_series.iloc[-1])
                ema_levels[f"ema{period}"] = _safe_round(ema_series.iloc[-1])

            # Momentum: RSI and MACD
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss.replace(0, 1e-12)
            rsi = 100 - (100 / (1 + rs))
            if len(avg_loss) and avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] > 0:
                rsi_value = 100.0
            elif len(avg_loss) and avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] == 0:
                rsi_value = 50.0
            else:
                rsi_value = rsi.iloc[-1]

            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal

            # Volatility: ATR and Bollinger Bands
            hl = high - low
            hc = (high - close.shift()).abs()
            lc = (low - close.shift()).abs()
            tr = hl.to_frame("hl")
            tr["hc"] = hc
            tr["lc"] = lc
            atr = tr.max(axis=1).rolling(14).mean()

            basis = close.rolling(20).mean()
            std = close.rolling(20).std()
            bb_upper = basis + 2 * std
            bb_lower = basis - 2 * std

            # Volume: OBV
            obv_value = None
            if volume is not None:
                direction = close.diff().fillna(0)
                sign = direction.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
                obv = (sign * volume.fillna(0)).cumsum()
                obv_value = _safe_round(obv.iloc[-1])

            out["trend"] = {
                "sma": sma_levels,
                "ema": ema_levels,
            }
            out["momentum"] = {
                "rsi14": _safe_round(rsi_value),
                "macd": _safe_round(macd.iloc[-1]),
                "macd_signal": _safe_round(macd_signal.iloc[-1]),
                "macd_histogram": _safe_round(macd_hist.iloc[-1]),
            }
            out["volatility"] = {
                "atr14": _safe_round(atr.iloc[-1]),
                "bb_basis20": _safe_round(basis.iloc[-1]),
                "bb_upper20": _safe_round(bb_upper.iloc[-1]),
                "bb_lower20": _safe_round(bb_lower.iloc[-1]),
            }
            out["volume"] = {
                "obv": obv_value,
            }

            return json.dumps(out)
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Indicator rule engine failed: {exc}"})
