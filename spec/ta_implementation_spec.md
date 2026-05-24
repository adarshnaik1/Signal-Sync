# TA Technical Analysis System Specification

Status: Active and consolidated

This document is the merged source of truth for TA architecture, implementation mapping, current runtime behavior, and pending validation work. It supersedes separate planning content.

## 1. Objective

Build a modular TA pipeline for medium-term and long-term equity analysis where deterministic quantitative tools are the primary source of truth and LLM output is synthesis-only.

Primary targets:
- Indian equities first
- Deterministic indicators/patterns/levels first
- Advisory vision layer only
- Explainable JSON outputs
- Low operational cost with swappable model providers

## 2. Design Principles

- Deterministic quantitative tools are source-of-truth.
- LLM reasoning is synthesis-only and must not perform numeric calculations.
- Vision review is advisory-only and must not override deterministic signals.
- Sequential execution is preferred for MVP reliability.
- Tools must return structured JSON with success boolean and typed sections.

## 3. Current Crew Architecture (Implemented)

Current flow is sequential with specialist agents and no manager stage:

1. Market Data Agent
2. Indicator Agent
3. Pattern Detection Agent
4. Support/Resistance Agent
5. Strategy/Signal Agent
6. Explanation Agent

Rationale:
- Manager stage was removed to reduce orchestration stalls and delegation overhead.

## 4. Implemented Repository Modules

- Crew orchestration:
  - src/signal_sync/ta/crew.py
  - src/signal_sync/ta/main.py
- Agent/task config:
  - src/signal_sync/ta/config/agents.yaml
  - src/signal_sync/ta/config/tasks.yaml
- Deterministic tools:
  - src/signal_sync/ta/tools/market_data_tools.py
  - src/signal_sync/ta/tools/indicator_tools.py
  - src/signal_sync/ta/tools/pattern_tools.py
  - src/signal_sync/ta/tools/support_resistance_tools.py
  - src/signal_sync/ta/tools/chart_tools.py

## 5. Deterministic Tool Contracts

All tools return JSON object payloads with:
- success: boolean
- structured output or error field

### 5.1 Market Data

- fetch_ohlcv_tool
- fetch_actions_tool
- validate_data_tool
- fetch_market_data_bundle_tool

Current bundle tool behavior:
- Fetches daily and weekly OHLCV
- Fetches actions
- Runs validation summary
- Writes bundle file to cache
- Returns compact handoff payload containing bundle_file path and summary stats

### 5.2 Indicators

Single-pass preferred tool:
- indicator_rule_engine_tool

Legacy/specialized tools retained:
- compute_sma_tool
- compute_ema_tool
- compute_rsi_tool
- compute_macd_tool
- compute_atr_tool
- compute_bollinger_tool
- compute_obv_tool

### 5.3 Patterns

- detect_candlestick_patterns_tool
- detect_chart_patterns_tool

### 5.4 Support/Resistance

- find_swings_tool
- cluster_levels_tool
- volume_zone_tool
- dynamic_sr_tool

### 5.5 Chart and Vision

- render_chart_tool
- vision_review_tool

Vision is advisory-only and must degrade gracefully when image/model access is unavailable.

## 6. Data Handoff and Payload Rules

Current handoff is file-path based to reduce context bloat.

Upstream output:
- fetch_market_data_bundle_tool returns bundle_file

Downstream input:
- tools accept ohlcv_json field as either:
  - JSON string payload, or
  - filesystem path to JSON payload

Accepted OHLCV container keys:
- ohlcv
- daily_ohlcv
- weekly_ohlcv

Critical loader rule:
- never construct DataFrame directly from bundle metadata dict
- always extract candle rows first, then build DataFrame

## 7. Indicator and Analytics Scope

Trend:
- SMA 20/50/100/200
- EMA 20/50/100/200

Momentum:
- RSI(14)
- MACD(12,26,9)

Volatility:
- ATR(14)
- Bollinger Bands(20, 2)

Volume:
- OBV

## 8. Pattern and Structure Scope

Candlestick patterns (deterministic):
- doji
- hammer
- shooting star
- bullish engulfing
- bearish engulfing

Chart structures (deterministic):
- double top
- double bottom
- channel proxy

Support/resistance confluence layers:
- swing highs/lows
- clustered levels
- volume concentration zones
- dynamic EMA levels

## 9. Runtime and Output Expectations

Expected end-to-end behavior:
- market data task returns bundle_file handoff
- indicator task consumes same handoff and computes full indicator block in one call
- pattern and support/resistance tasks consume same handoff
- strategy and explanation synthesize deterministic outputs
- final analysis is printed to stdout and returned by run

## 10. Engineering Constraints

- Determinism first
- Explainability first
- Low cost model usage
- Modular and swappable components
- Tool-level validation and defensive parsing
- Backward compatibility for JSON string based tool inputs

## 11. Testing Status and Remaining Validation

Current status:
- Core flow works with bundle_file handoff
- Indicator rule engine path-input failure has been fixed
- Pattern and support/resistance loaders now support bundle payload shapes

Deep testing still pending:
- unit tests for each deterministic tool
- edge-case payload tests for malformed/incomplete OHLCV
- regression tests for bundle and non-bundle inputs
- integration test snapshot for full crew outputs

## 12. Execution Checklist

Minimum acceptance checklist:
- all deterministic tools return success or explicit error JSON
- indicator rule engine computes all required sections in one call
- downstream tools accept both raw JSON and bundle file path
- no manager-stage dependency in sequential flow
- final output printed for CLI runs

## 13. Future Iterations

Planned post-MVP enhancements:
- typed schemas for all task outputs
- backtesting and signal quality evaluation
- optional sentiment/macro branches
- production API endpoint for TA crew execution
- expanded pattern library and confidence calibration