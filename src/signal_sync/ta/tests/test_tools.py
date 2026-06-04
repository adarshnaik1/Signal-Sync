import json
import os
from datetime import datetime, timedelta

import pytest

from signal_sync.ta.api_runner import _merge_deterministic_outputs
from signal_sync.ta.tools.chart_tools import RenderChartTool, VisionReviewTool
from signal_sync.ta.tools.indicator_tools import IndicatorRuleEngineTool
from signal_sync.ta.tools.pattern_tools import DetectChartPatternsTool
from signal_sync.ta.tools.support_resistance_tools import FindSwingsTool, ClusterLevelsTool


def make_ohlcv_rows(n=40):
    base = datetime.utcnow()
    rows = []
    price = 100.0
    for i in range(n):
        dt = (base - timedelta(days=n - i)).isoformat()
        open_p = price + (i % 5 - 2) * 0.5
        close = open_p + (i % 3 - 1) * 0.3
        high = max(open_p, close) + 0.2
        low = min(open_p, close) - 0.2
        vol = 1000 + i * 10
        rows.append({"Date": dt, "Open": open_p, "High": high, "Low": low, "Close": close, "Volume": vol})
        price = close
    return rows


def test_render_chart_creates_file(tmp_path):
    rows = make_ohlcv_rows(50)
    payload = json.dumps({"ohlcv": rows})
    tool = RenderChartTool()
    out = tool._run(payload, ticker="TEST", include_rsi=True)
    assert isinstance(out, dict)
    assert out.get("success") is True
    path = out.get("chart_path")
    assert path and os.path.exists(path)
    # cleanup
    os.remove(path)


def test_render_chart_uses_weekly_history_when_daily_bundle_is_too_short(tmp_path):
    bundle = {
        "ticker": "TEST",
        "daily_ohlcv": make_ohlcv_rows(1),
        "weekly_ohlcv": make_ohlcv_rows(53),
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    tool = RenderChartTool()
    out = tool._run(str(bundle_path), ticker="TEST", include_rsi=True)

    assert out.get("success") is True
    assert out.get("source_key") == "weekly_ohlcv"
    assert out.get("rows_rendered") == 53
    path = out.get("chart_path")
    assert path and os.path.exists(path)
    os.remove(path)


def test_vision_review_returns_structured_skip_without_api_key(tmp_path, monkeypatch):
    rows = make_ohlcv_rows(50)
    chart = RenderChartTool()._run(json.dumps({"ohlcv": rows}), ticker="TEST", include_rsi=False)
    chart_path = chart.get("chart_path")
    assert chart_path and os.path.exists(chart_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    out = VisionReviewTool()._run(chart_path, model="standard")

    assert out.get("success") is True
    assert out.get("image_analysis_status") == "skipped_no_api_key"
    assert out.get("model") == "gpt-4.1-mini"
    assert out.get("chart_path") == chart_path
    assert out.get("visual_summary")
    os.remove(chart_path)


def test_final_payload_merge_preserves_chart_and_visual_review():
    final_payload = {"summary": {"stance": "neutral"}, "visual_review": None}
    task_outputs = [
        {"success": True, "bundle_file": "bundle.json", "daily_rows": 50},
        {"success": True, "trend": {"ema": {"ema20": 100.0}}},
        {
            "success": True,
            "candlestick_patterns": ["doji"],
            "chart_patterns": ["channel"],
            "chart_path": "C:\\charts\\TEST.png",
            "rows_rendered": 53,
            "source_key": "weekly_ohlcv",
            "visual_review": {
                "success": True,
                "visual_summary": "Range-bound chart with fading momentum.",
                "confidence": 0.6,
                "image_analysis_status": "completed",
            },
        },
    ]

    merged = _merge_deterministic_outputs(final_payload, task_outputs)

    assert merged["summary"]["stance"] == "neutral"
    assert merged["chart_path"] == "C:\\charts\\TEST.png"
    assert merged["rows_rendered"] == 53
    assert merged["visual_review"]["visual_summary"] == "Range-bound chart with fading momentum."
    assert merged["visual_review"]["chart_path"] == "C:\\charts\\TEST.png"
    assert merged["candlestick_patterns"] == ["doji"]


def test_indicator_engine_uses_weekly_history_when_daily_bundle_is_too_short(tmp_path):
    bundle = {
        "ticker": "TEST",
        "daily_ohlcv": make_ohlcv_rows(1),
        "weekly_ohlcv": make_ohlcv_rows(53),
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    out = json.loads(IndicatorRuleEngineTool()._run(str(bundle_path)))

    assert out.get("success") is True
    assert out["momentum"]["macd"] != 0
    assert out["volatility"]["atr14"] is not None


def test_chart_patterns_use_weekly_history_when_daily_bundle_is_too_short(tmp_path):
    bundle = {
        "ticker": "TEST",
        "daily_ohlcv": make_ohlcv_rows(1),
        "weekly_ohlcv": make_ohlcv_rows(53),
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    out = json.loads(DetectChartPatternsTool()._run(str(bundle_path)))

    assert out.get("success") is True
    assert isinstance(out.get("chart_patterns"), list)


def test_find_swings_fallback_insufficient_rows():
    rows = make_ohlcv_rows(10)
    payload = json.dumps({"ohlcv": rows})
    tool = FindSwingsTool()
    out = tool._run(payload)
    assert isinstance(out, dict)
    assert out.get("success") is False
    assert "required_rows" in out and out["required_rows"] >= 30


def test_cluster_levels_accepts_zone_dicts():
    zones = [{"zone_low": 99.5, "zone_high": 100.5}, {"zone_low": 100.4, "zone_high": 101.0}, {"zone_low": 110, "zone_high": 111}]
    payload = json.dumps(zones)
    tool = ClusterLevelsTool()
    out = tool._run(payload)
    assert isinstance(out, dict)
    assert out.get("success") is True
    clusters = out.get("clusters")
    assert isinstance(clusters, list) and len(clusters) >= 1
