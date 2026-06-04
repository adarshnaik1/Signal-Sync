from typing import Any, Dict, List

from .explanations import explain_indicator, explain_pattern


COMMON_INDICATOR_KEYS = ["ema", "sma", "rsi", "macd", "atr", "obv", "bollinger_bands"]


def _get_path(node: Any, path: List[str]):
    current = node
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _first_numeric_value(node: Any):
    if isinstance(node, (int, float, str)):
        return node
    if isinstance(node, dict):
        for key in ["value", "observed_value", "macd_value", "atr14", "obv", "bb_basis20", "bb_upper20", "bb_lower20"]:
            candidate = node.get(key)
            if isinstance(candidate, (int, float, str)):
                return candidate
        for candidate in node.values():
            found = _first_numeric_value(candidate)
            if found is not None:
                return found
    if isinstance(node, list):
        for candidate in node:
            found = _first_numeric_value(candidate)
            if found is not None:
                return found
    return None


def _find_indicator_value(result: Dict[str, Any], key: str):
    indicator_paths = {
        "sma": [
            ["trend", "sma", "sma20"],
            ["trend", "sma20"],
            ["indicator_explanation", "moving_averages", "sma", "sma20"],
            ["indicator_explanation", "moving_averages", "sma"],
            ["indicator_explanation", "sma"],
        ],
        "ema": [
            ["trend", "ema", "ema50"],
            ["trend", "ema50"],
            ["indicator_explanation", "moving_averages", "ema", "ema50"],
            ["indicator_explanation", "moving_averages", "ema"],
            ["indicator_explanation", "ema"],
        ],
        "rsi": [
            ["momentum", "rsi14"],
            ["indicator_explanation", "momentum_indicators", "rsi", "value"],
            ["indicator_explanation", "rsi", "value"],
        ],
        "macd": [
            ["momentum", "macd"],
            ["indicator_explanation", "momentum_indicators", "macd", "macd_value"],
            ["indicator_explanation", "momentum_indicators", "macd", "value"],
            ["indicator_explanation", "macd", "value"],
        ],
        "atr": [
            ["volatility", "atr14"],
            ["indicator_explanation", "volatility", "atr14"],
            ["indicator_explanation", "atr", "value"],
        ],
        "obv": [
            ["volume", "obv"],
            ["indicator_explanation", "volume_analysis", "obv"],
            ["indicator_explanation", "obv", "value"],
        ],
        "bollinger_bands": [
            ["volatility", "bb_basis20"],
            ["volatility", "bb_upper20"],
            ["volatility", "bb_lower20"],
        ],
    }

    for path in indicator_paths.get(key, []):
        found = _first_numeric_value(_get_path(result, path))
        if found is not None:
            return found

    # Fall back to scanning common explanation sections for a matching scalar.
    sections = [
        _get_path(result, ["indicator_explanation"]),
        _get_path(result, ["indicator_explanation", "moving_averages"]),
        _get_path(result, ["indicator_explanation", "momentum_indicators"]),
        _get_path(result, ["indicator_explanation", "volatility"]),
        _get_path(result, ["indicator_explanation", "volume"]),
        _get_path(result, ["explanations", key]),
    ]
    for node in sections:
        if not isinstance(node, dict):
            continue
        for subkey, subvalue in node.items():
            if key in str(subkey).lower():
                found = _first_numeric_value(subvalue)
                if found is not None:
                    return found
    return None


def generate_explanations(result: Dict[str, Any]) -> Dict[str, Any]:
    explanations: Dict[str, Any] = {}
    takeaways: List[str] = []

    # Indicators
    for key in COMMON_INDICATOR_KEYS:
        val = _find_indicator_value(result, key)
        expl = explain_indicator(key, val)
        explanations[key] = expl
        # prefer concise takeaway
        if expl.get("takeaway"):
            takeaways.append(expl["takeaway"])

    # Patterns
    patterns = []
    if isinstance(result.get("pattern_explanation"), dict):
        # try chart_patterns
        cp = result["pattern_explanation"].get("patterns") or result["pattern_explanation"].get("chart_patterns")
        if cp:
            patterns = cp
    if not patterns and isinstance(result.get("chart_patterns"), list):
        patterns = result.get("chart_patterns", [])
    if not patterns and isinstance(result.get("pattern_explanation"), list):
        patterns = result.get("pattern_explanation")

    explanations["patterns"] = {}
    for pat in patterns:
        expl = explain_pattern(pat)
        explanations["patterns"][pat] = expl
        if expl.get("takeaway"):
            takeaways.append(expl["takeaway"])

    # Deduplicate takeaways preserving order
    seen = set()
    final_takeaways: List[str] = []
    for t in takeaways:
        if t not in seen:
            final_takeaways.append(t)
            seen.add(t)

    return {"explanations": explanations, "takeaways": final_takeaways}


__all__ = ["generate_explanations"]
