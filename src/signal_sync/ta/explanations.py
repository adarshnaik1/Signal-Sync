"""Plain-language explanations for TA indicators and patterns.

This module provides short, investor-friendly mappings that translate
technical jargon into simple, actionable bullet points.
"""
from typing import Any, Dict, Optional

MAPPINGS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "indicators": {
        "ema": {
            "meaning": "Exponential Moving Average gives recent prices more weight, showing short-to-midterm trend.",
            "implication": [
                "Price above EMA: short-term bullish bias.",
                "Price below EMA: short-term bearish bias.",
                "Crosses of faster EMA above slower EMA signal strengthening momentum."
            ],
            "takeaway": "If price stays above key EMAs (e.g., 50/200), consider the trend supportive; if below, be cautious."
        },
        "sma": {
            "meaning": "Simple Moving Average smooths price over a window to reveal trend direction.",
            "implication": [
                "Rising SMA: trend is up over that window.",
                "Falling SMA: trend is down.",
                "Price crossing the SMA indicates potential change in trend."
            ],
            "takeaway": "Look for price consistently above longer SMAs for confirmation of an uptrend; otherwise preserve capital."
        },
        "rsi": {
            "meaning": "Relative Strength Index measures recent gains vs losses to gauge momentum (0-100).",
            "implication": [
                "RSI > 70 often means overbought (short-term pullback possible).",
                "RSI < 30 often means oversold (possible bounce).",
                "Divergences vs price can signal weakening trend."
            ],
            "takeaway": "Use RSI as a momentum check: avoid buying into high RSI spikes without confirmation; consider watchlist for low RSI recovery."
        },
        "macd": {
            "meaning": "MACD shows momentum by comparing two EMAs and their difference (histogram).",
            "implication": [
                "MACD line crossing above signal line suggests bullish momentum gaining.",
                "MACD below zero implies longer-term downward bias.",
            ],
            "takeaway": "Watch MACD crossovers as supporting evidence for entries or exits, not as sole signals."
        },
        "atr": {
            "meaning": "Average True Range measures recent price volatility (higher = more movement).",
            "implication": [
                "Higher ATR means larger expected moves; position sizing should account for this.",
                "Lower ATR means quieter market; breakouts may be more meaningful."
            ],
            "takeaway": "Use ATR to size stops and position sizes — increase stop distance when ATR is high."
        },
        "obv": {
            "meaning": "On-Balance Volume accumulates volume on up vs down days to show participation direction.",
            "implication": [
                "Rising OBV with rising price confirms healthy buying interest.",
                "Falling OBV while price rises suggests weak participation and risk of reversal."
            ],
            "takeaway": "Prefer trades where volume/OBV confirm price moves; be cautious when price diverges from OBV."
        },
        "bollinger_bands": {
            "meaning": "Bands around a moving average that expand/contract with volatility.",
            "implication": [
                "Price touching upper band may be stretched; lower band touch may be oversold.",
                "Squeezes (narrow bands) often precede bigger breakouts."
            ],
            "takeaway": "Use bands to sense volatility regimes and to avoid chasing extreme moves."
        }
    },
    "patterns": {
        "double_bottom": {
            "meaning": "Two lows at similar price suggesting buyers defended support; potential reversal signal.",
            "implication": [
                "If price breaks the interim peak between lows with volume, trend may reverse up.",
                "Failure to break up keeps structure doubtful."
            ],
            "takeaway": "Consider confirmation (break of neckline with volume) before assuming a durable reversal."
        },
        "double_top": {
            "meaning": "Two highs at similar price suggesting sellers defended resistance; potential top formation.",
            "implication": [
                "Break of the valley between peaks signals increased chance of declines.",
            ],
            "takeaway": "Use conservative stops and wait for confirmation before shorting; prioritize risk management."
        },
        "channel": {
            "meaning": "Price oscillating between parallel support and resistance lines.",
            "implication": [
                "Buy near lower boundary with tight stops; sell or trim near upper boundary.",
                "Breakout from the channel can lead to a stronger directional move."
            ],
            "takeaway": "Trade the range with clear stop-loss; on breakout, look for confirmation before scaling exposure."
        },
        "head_and_shoulders": {
            "meaning": "A peak (left shoulder), higher peak (head), then lower peak (right shoulder) — classic reversal pattern.",
            "implication": [
                "Neckline break increases likelihood of a sustained decline.",
            ],
            "takeaway": "Treat as a strong reversal sign only after neckline break and consider reducing exposure."
        },
        "doji": {
            "meaning": "Candlestick with little to no body; shows indecision between buyers and sellers.",
            "implication": [
                "Alone it means indecision; context (trend, volume) determines significance."
            ],
            "takeaway": "Look for confirmation candles before acting on a doji."
        },
        "hammer": {
            "meaning": "A candlestick with a small body and long lower wick, often at bottoms indicating rejection of lower prices.",
            "implication": [
                "Can signal a short-term bullish reversal if followed by confirming strength."
            ],
            "takeaway": "Use confirmation (next candle close higher) before treating as a buy signal."
        },
        "engulfing": {
            "meaning": "A candle that fully engulfs the prior candle's body, indicating a strong shift in control.",
            "implication": [
                "Bullish engulfing after a downmove can signal buyers stepping in; bearish engulfing the opposite."
            ],
            "takeaway": "Prefer signals confirmed by volume and follow-up price action."
        }
    }
}


def explain_indicator(name: str, value: Optional[Any] = None) -> Dict[str, Any]:
    key = name.lower()
    entry = MAPPINGS.get("indicators", {}).get(key)
    if not entry:
        return {"meaning": f"No plain-language mapping for '{name}'.", "takeaway": "Refer to technical output."}
    out = dict(entry)
    if value is not None:
        out["observed_value"] = value
    return out


def explain_pattern(name: str) -> Dict[str, Any]:
    key = name.lower()
    entry = MAPPINGS.get("patterns", {}).get(key)
    if not entry:
        return {"meaning": f"No plain-language mapping for '{name}'.", "takeaway": "Refer to technical output."}
    return dict(entry)


__all__ = ["MAPPINGS", "explain_indicator", "explain_pattern"]
