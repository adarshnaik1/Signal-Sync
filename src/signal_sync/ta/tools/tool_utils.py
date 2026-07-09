import functools
import json
import os
from typing import Any, Callable, Dict, Tuple


def make_response(success: bool, **kwargs) -> Dict[str, Any]:
    resp = {"success": bool(success)}
    resp.update(kwargs)
    return resp


def ensure_abs_path(path: str) -> str:
    if not path:
        return path
    try:
        return os.path.abspath(path)
    except Exception:
        return path


def load_json_or_path(value: str) -> Any:
    if os.path.exists(value):
        with open(value, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(value)


def extract_ohlcv_rows(raw: Any, min_rows: int = 1) -> Tuple[list, str]:
    """Select the most useful OHLCV row set from a raw payload.

    Market bundles can contain a short current-day dataset plus longer weekly
    history. Prefer daily rows when they are usable, otherwise fall back to the
    largest usable OHLCV list so charts and indicators are not based on one bar.
    """
    if isinstance(raw, list):
        return raw, "list"

    if isinstance(raw, dict):
        for key in ("ohlcv", "daily_ohlcv", "data", "rows", "weekly_ohlcv"):
            value = raw.get(key)
            if isinstance(value, list) and len(value) >= min_rows:
                return value, key

        candidates = []
        for key in ("ohlcv", "daily_ohlcv", "data", "rows", "weekly_ohlcv"):
            value = raw.get(key)
            if isinstance(value, list):
                candidates.append((len(value), key, value))
        if candidates:
            _, key, value = max(candidates, key=lambda item: item[0])
            return value, key

        if all(k in raw for k in ("Open", "High", "Low", "Close")):
            return [raw], "object"

        if all(k in raw for k in ("open", "high", "low", "close")):
            return [raw], "object"

    raise ValueError("No OHLCV rows found. Expected list or dict with keys: ohlcv/daily_ohlcv/weekly_ohlcv.")


def catch_and_normalize(fn: Callable) -> Callable:
    """Decorator to catch exceptions and ensure tool returns a JSON-like dict.

    Any exception is caught and converted to {'success': False, 'error': str(exc)}.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # convert unexpected exceptions to normalized dict
            return make_response(False, error=str(exc))

        # If the tool returned a raw string, wrap as error text
        if isinstance(result, str):
            # try to parse JSON string
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and "success" in parsed:
                    return parsed
                return make_response(False, error=parsed)
            except Exception:
                return make_response(False, error=result)

        # If already a dict-like, ensure it has 'success'
        if isinstance(result, dict):
            if "success" not in result:
                result = {"success": True, **result}
            return result

        # For any other return types, wrap as success and attach value
        return make_response(True, result=result)

    return wrapper
