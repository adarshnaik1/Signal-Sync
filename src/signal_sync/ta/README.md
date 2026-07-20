# TA Module — Signal-Sync

This folder contains the Technical Analysis (TA) module used by Signal-Sync to produce deterministic technical-analysis outputs, charts, and plain-language explanations for a given ticker.

Purpose
- Provide deterministic, auditable TA outputs (indicators, patterns, support/resistance, volume zones).
- Render charts and produce machine- and human-readable JSON results suitable for downstream reporting and archives.
- Produce concise, plain-language explanations and takeaways to support report writing.

Quick overview of important files
- `main.py`: simple CLI entrypoint to run a TA crew for a ticker (example: `python -m signal_sync.ta.main TCS.NS medium-term`).
- `api_runner.py`: orchestrates running TA for a job, persisting results and artifacts to `output_data` and `artifacts/` and updating a jobs store (used by the API/service layer).
- `crew.py`: defines `TAAnalysisCrew` (agents, tasks, tools wiring) — this is the core orchestration for the TA pipeline.
- `explanation_generator.py`: produces deterministic plain-language explanations and takeaways from TA outputs.
- `explanations.py`: small mapping of technical concepts (EMA, RSI, patterns) to investor-friendly language — used by the generator.
- `schemas.py`: `pydantic` models that define the shape of task outputs and final result JSON.
- `tools/`: deterministic tools (fetching data, computing indicators, pattern detection, chart rendering, vision review, support/resistance analysis).

Prerequisites
- Python 3.10+ (project uses modern typing and pydantic).
- Install repository dependencies from the root:

```bash
pip install -r requirements.txt
```

Note: The repository's top-level `requirements.txt` contains packages required across the project. If your environment splits dependencies, ensure the TA tools (pandas/numpy/matplotlib, crewai, pydantic, dotenv, any vision dependencies) are present.

Running locally (CLI)
- Run a quick analysis from the repo root:

```bash
python -m signal_sync.ta.main TCS.NS medium-term
```

- The CLI returns JSON printed to stdout and (when invoked via the API runner) writes structured JSON into `src/signal_sync/ta/output_data/` and copies any rendered images into `src/signal_sync/ta/artifacts/<job_id>/`.

Running via API/service (recommended for production)
- Use `api_runner.run_ta_job(job_id, company_name, ticker, sector, horizon)` to run a TA job inside the server context. This function:
  - Updates job progress via `api.jobs_store.update_job`.
  - Writes logs to `src/signal_sync/ta/logs/`.
  - Writes final JSON to `src/signal_sync/ta/output_data/` and copies artifacts to `src/signal_sync/ta/artifacts/<job_id>/`.

Core concepts & outputs
- Deterministic outputs (primary): indicator values, detected patterns, support/resistance levels, volume analysis, swings, chart paths. These are defined in `schemas.py` and gathered at the end of the crew run.
- Advisory outputs (secondary): LLM-derived explanations and vision review results — helpful for human reports but treated as advisory in the pipeline.

Where to look for results
- JSON results: `src/signal_sync/ta/output_data/<TICKER>_ta_<TIMESTAMP>.json`
- Artifacts (charts, images): `src/signal_sync/ta/artifacts/<job_id>/` (copied by `api_runner.py`).
- Logs: `src/signal_sync/ta/logs/ta_<job_id>.log`

How to interpret the main fields (high level)
- `trend` / `indicator` sections: moving averages (SMA/EMA) — compare price vs EMA20/EMA50/EMA200 to determine short/medium/long-term bias.
- `momentum`: `rsi14`, `macd` — use RSI to spot overbought/oversold and MACD for momentum confirmation.
- `volatility`: `atr14`, Bollinger band basis/upper/lower — volatility context for stop sizing.
- `candlestick_patterns` / `chart_patterns`: string-list of detected patterns (e.g., `doji`, `hammer`, `double_bottom`), used by the explanation generator to form takeaways.
- `support_zones` / `resistance_zones`: numeric lists of key levels (use these to cite expected reaction zones in a report).
- `visual_review`: camera/vision summary for the rendered chart (advisory; may include `confidence`).

Example: minimal report template (use the JSON output to fill sections)
- Title: Technical Analysis — <TICKER> — <DATE>
- Executive stance: `result['strategy']['stance']` with `confidence`.
- Key supporting evidence: list top N items from `result['strategy']['key_supporting_evidence']`.
- Indicator summary: summarize `result['indicator_explanation']` or `result['trend']` / `result['momentum']` values.
- Patterns & structure: report `chart_patterns` and `candlestick_patterns`, and describe support/resistance zones from `support_zones`/`resistance_zones`.
- Chart: embed the image from `visual_review.chart_url` or the chart file copied into artifacts.

Where the plain-language explanations come from
- `explanation_generator.generate_explanations(result)` will:
  - Extract indicator values using `explanations` mapping and produce short `explanations` and `takeaways`.
  - Explain detected chart/patterns using the `explanations` mapping.
- Use the returned `takeaways` and `explanations` sections directly in reports for a consistent tone.

Configuration & tuning
- Agent and task behavior is driven by `config/agents.yaml` and `config/tasks.yaml` in this folder. To change how tasks run (tool chains, verbosity, role of LLM agents), edit those files and test runs in a controlled environment.

Testing & validation
- Unit tests for the TA tooling are in `src/signal_sync/ta/tests/`.
- Run tests using your preferred test runner (e.g., `pytest src/signal_sync/ta/tests`).

Troubleshooting
- Missing charts or images: inspect `logs/` for rendering/vision errors. The runner will fall back to advisory-only explanations if rendering fails.
- Data missing/validation failures: check `validation` section in the Market Data output. The pipeline logs validation issues and row counts.

Extending for reports
- You can write a thin wrapper that:
  1. Calls `api_runner.run_ta_job` or `TAAnalysisCrew.run()` for a list of tickers.
  2. Loads the resulting JSON from `output_data`.
  3. Renders a templated PDF/HTML report by filling the sections listed in "Example: minimal report template" above.

Contact / Next steps
- If you want, I can:
  - Provide a ready-to-use report Jinja template that converts the JSON into PDF/HTML.
  - Add a `report_example.py` that loads a result JSON and produces a one-page summary.

---
Generated by developer documentation assistant. For deeper file-level docs, run `python -m signal_sync.ta.main` and share output to include concrete examples.
