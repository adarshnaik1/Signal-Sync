## Technical Analysis (TA) Module Documentation

The Technical Analysis (TA) module within Signal Sync is designed to provide automated, data-driven insights into stock market trends and signals. It leverages a CrewAI-based multi-agent system to perform comprehensive technical analysis, producing structured outputs and human-readable explanations. This documentation details its architecture, internal workings, data flow, and integration points.

### 1. Introduction and Objective

The primary objective of the TA module is to generate objective technical analysis for equities, focusing on medium-term and long-term horizons. A foundational design principle is that **deterministic quantitative tools are the primary source of truth**, with Large Language Model (LLM) output strictly limited to synthesis, reasoning, and explanation, never performing direct numerical calculations. This ensures reproducibility and explainability of the analysis.

Key targets for the TA module include:
*   Analysis of Indian equities.
*   Reliable detection of deterministic indicators, patterns, and support/resistance levels.
*   Advisory-only role for visual analysis.
*   Generation of explainable JSON outputs at each stage.
*   Low operational cost and flexible LLM provider integration.

### 2. Crew Architecture and Execution Flow

The TA module employs a sequential CrewAI architecture, where a series of specialized agents collaborate to complete the analysis. This design avoids a manager agent to reduce orchestration overhead and improve reliability.

**The sequential flow is as follows:**

1.  **Market Data Agent**
2.  **Indicator Agent**
3.  **Pattern Detection Agent**
4.  **Support/Resistance Agent**
5.  **Strategy/Signal Agent**
6.  **Explanation Agent**

Each agent is defined in `src/signal_sync/ta/config/agents.yaml`, and their respective tasks and interdependencies are specified in `src/signal_sync/ta/config/tasks.yaml`.

#### 2.1. Agent Definitions (`src/signal_sync/ta/config/agents.yaml`)

| Agent Name                       | Role                                                | Goal                                                                                                                                                                             | Backstory                                                                                                                                                                                                                             | LLM Usage (Inferred)                                                                        |
| :------------------------------- | :-------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------ |
| `manager_agent` (Removed)        | -                                                   | -                                                                                                                                                                                | -                                                                                                                                                                                                                                     | -                                                                                           |
| `market_data_agent`              | Market Data Validation Specialist for `{ticker}`    | Fetch adjusted OHLCV and corporate actions, then validate and clean the dataset.                                                                                                 | Strict about data integrity and reproducibility. Always cleans missing, duplicate, and unsorted records before downstream analysis.                                                                                                        | Used to orchestrate tool calls for data fetching and validation.                            |
| `indicator_agent`                | Technical Indicator Computation Specialist          | Compute trend, momentum, volatility, and volume indicators using deterministic tools only.                                                                                       | A quant engineer specialized in indicator libraries and reproducible metrics. Never invents values.                                                                                                                                     | Used to invoke `IndicatorRuleEngineTool` and format its output.                             |
| `pattern_detection_agent`        | Deterministic Pattern Detection Specialist          | Detect candlestick and chart patterns using rule-based tool outputs, then attach advisory vision review.                                                                         | Enforces geometry-based pattern logic and treats vision output as advisory only.                                                                                                                                                      | Interprets tool outputs for patterns and potentially formulates an advisory visual review. |
| `support_resistance_agent`       | Support and Resistance Structure Specialist         | Build support and resistance zones from swings, clustering, volume concentration, and dynamic EMA levels.                                                                        | Uses weighted confluence and avoids single-point level bias.                                                                                                                                                                          | Synthesizes results from support/resistance tools.                                          |
| `strategy_signal_agent`          | Technical Thesis and Signal Reasoning Specialist    | Synthesize deterministic outputs into bullish, bearish, or neutral stance with confidence.                                                                                       | Reasons solely from evidence. Does not perform numerical calculations manually.                                                                                                                                                       | Core LLM reasoning for synthesizing technical signals into a coherent thesis and stance.    |
| `explanation_agent`              | Technical Analysis Explainer                      | Convert quantitative and reasoning outputs into a clear, professional, educational narrative that stays specific to the current ticker and the supplied evidence.            | Known for accurate, plain-language investment education and uncertainty communication. Avoids boilerplate phrasing and anchors uncertainty to concrete values, levels, or patterns.                                                     | Responsible for generating human-readable explanations based on all prior agent outputs.    |

#### 2.2. Task Definitions and Data Handoff (`src/signal_sync/ta/config/tasks.yaml`)

Each task corresponds to a step in the sequential pipeline. Data is primarily handed off between tasks using a **file-path based approach** (`bundle_file`) to minimize context bloat and ensure consistency.

| Task Name                   | Description                                                                                                                                                                                                                                                                                                                               | Agent                     | Expected Output (Pydantic Schema)                                                                           |
| :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------ | :---------------------------------------------------------------------------------------------------------- |
| `market_data_task`          | Uses `fetch_market_data_bundle_tool` to return a compact `bundle_file` (containing daily/weekly OHLCV, actions, and validation metadata). The `bundle_file` path is passed to downstream tasks.                                                                                                                                                | `market_data_agent`       | `MarketDataTaskOutput`                                                                                      |
| `indicator_task`            | Uses `indicator_rule_engine_tool` to compute SMA, EMA, RSI, MACD, ATR, Bollinger Bands, and OBV in one pass. It consumes the `bundle_file` from `market_data_task`.                                                                                                                                                                            | `indicator_agent`         | `IndicatorTaskOutput` (JSON with trend, momentum, volatility, volume sections)                              |
| `pattern_detection_task`    | Detects candlestick and chart patterns from cleaned OHLCV data and renders a chart. Performs an advisory visual review. Consumes the `bundle_file`.                                                                                                                                                                                              | `pattern_detection_agent` | `PatternDetectionTaskOutput` (JSON with candlestick/chart patterns, `chart_path`, and `visual_review`)    |
| `support_resistance_task`   | Builds support and resistance zones from swings, clustered levels, volume zones, and dynamic EMA levels. Consumes the `bundle_file`.                                                                                                                                                                                                    | `support_resistance_agent`| `SupportResistanceTaskOutput` (JSON with support/resistance zones, evidence, and confidence scores)         |
| `strategy_signal_task`      | Synthesizes outputs from the `indicator_task`, `pattern_detection_task`, and `support_resistance_task` into a technical stance, confidence level, and a concise thesis.                                                                                                                                                                         | `strategy_signal_agent`   | `StrategySignalTaskOutput` (JSON with stance, confidence, thesis, key supporting evidence)                  |
| `explanation_task`          | Explains the entire analysis in human-readable terms, avoiding jargon and anchoring uncertainty to concrete values from the analysis. Consumes the `strategy_signal_task` output.                                                                                                                                                                   | `explanation_agent`       | `ExplanationTaskOutput` (JSON with summary, indicator/pattern/SR explanations, uncertainty notes, checklist) |

**Data Handoff:**
Tools that require OHLCV data accept the `ohlcv_json` field, which can be either a JSON string payload or a filesystem path to a JSON file (e.g., the `bundle_file`). This flexible input mechanism helps in efficient data passing without re-embedding large datasets into LLM context.

### 3. Tools and Functionalities (`src/signal_sync/ta/tools/`)

The `tools/` directory contains Python modules that implement the deterministic quantitative analysis. These tools are wrapped as `crewai.tools.BaseTool` objects, allowing agents to interact with them programmatically. All tools return structured JSON with a `success` boolean and relevant data or error messages.

#### 3.1. Market Data Tools (`market_data_tools.py`)

*   `FetchOHLCVTool`: Fetches historical Open, High, Low, Close, Volume (OHLCV) data for a given stock ticker, period (e.g., `1y`, `6mo`), and interval (e.g., `1d`, `1wk`) from Yahoo Finance. It supports auto-adjustment for deterministic technical analysis and caches results.
*   `FetchActionsTool`: Retrieves corporate actions (dividends, splits) for a specified ticker from Yahoo Finance.
*   `ValidateDataTool`: Cleans and validates OHLCV data. This involves removing duplicates, coercing data types, sorting chronologically, and dropping invalid rows to ensure data integrity.
*   `FetchMarketDataBundleTool`: A composite tool that orchestrates the fetching of daily OHLCV, weekly OHLCV, and corporate actions. It performs initial validation and saves all this data into a `bundle_file` in the `src/signal_sync/ta/cache/` directory. It then returns a compact JSON payload with the `bundle_file` path and summary statistics for efficient handoff.

#### 3.2. Indicator Tools (`indicator_tools.py`)

This module implements various technical indicators. Each individual indicator tool takes an `ohlcv_json` (JSON string or file path) as input.

*   `ComputeEMATool`: Calculates Exponential Moving Averages (EMA) for periods 20, 50, 100, and 200 on the Close price.
*   `ComputeRSITool`: Computes the Relative Strength Index (RSI) with a period of 14.
*   `ComputeMACDTool`: Calculates the Moving Average Convergence Divergence (MACD) with default periods (12, 26, 9 for signal line).
*   `ComputeATRTool`: Determines the Average True Range (ATR) over 14 periods.
*   `ComputeBollingerTool`: Computes Bollinger Bands (20-period simple moving average for basis, 2 standard deviations for upper and lower bands).
*   `ComputeOBVTool`: Calculates On-Balance Volume (OBV).
*   `ComputeSMATool`: Computes Simple Moving Averages (SMA) for periods 20, 50, 100, and 200 on the Close price.
*   `IndicatorRuleEngineTool`: A comprehensive tool designed to compute *all* core technical indicators (SMA, EMA, RSI, MACD, ATR, Bollinger Bands, OBV) in a single deterministic pass. This is the preferred tool for the `indicator_agent`.

#### 3.3. Pattern and Support/Resistance Tools (Inferred: `pattern_tools.py`, `support_resistance_tools.py`)

While the full content of these files was not provided, their functionality is clearly defined in `ta_implementation_spec.md`:

*   **Pattern Tools:**
    *   `DetectCandlestickPatternsTool`: Identifies deterministic candlestick patterns (e.g., doji, hammer, shooting star, bullish/bearish engulfing).
    *   `DetectChartPatternsTool`: Recognizes broader chart patterns (e.g., double top, double bottom, channel proxy).
*   **Support/Resistance Tools:**
    *   `FindSwingsTool`: Identifies significant swing highs and lows.
    *   `ClusterLevelsTool`: Clusters price levels to identify common support/resistance zones.
    *   `VolumeZoneTool`: Determines support/resistance based on volume concentration at certain price levels.
    *   `DynamicSRTool`: Integrates dynamic levels, such as those derived from moving averages, into support/resistance analysis.

#### 3.4. Chart and Vision Tools (Inferred: `chart_tools.py`)

*   `RenderChartTool`: Responsible for generating visual charts (e.g., candlestick charts with overlays of indicators, patterns, and support/resistance lines) and saving them to `src/signal_sync/ta/artifacts/` or `charts/` as PNG files.
*   `VisionReviewTool`: An advisory tool that can perform an image analysis of the rendered chart. Its output is advisory and must degrade gracefully if the vision model or image access is unavailable.

#### 3.5. Utility Tools (`tool_utils.py`)

This module provides common helper functions for the other tools, such as `extract_ohlcv_rows` (to parse OHLCV data from various JSON structures) and `load_json_or_path` (to handle both JSON string and file path inputs).

### 4. LLM Usage and Models

The LLMs are primarily employed by the `strategy_signal_agent` and `explanation_agent` for *synthesis, reasoning, and narrative generation*. They are explicitly forbidden from performing numerical calculations or overriding deterministic tool outputs.

The specific LLM provider can be configured. While the specification mentions a deferred switch from OpenAI to OpenRouter, the CrewAI framework typically allows configuration of `ollama_llm`, `openai_llm`, etc., through environment variables or CrewAI's project configuration. The `agents.yaml` and `tasks.yaml` define the *behavior* and *goals* for the agents but do not hardcode the LLM provider, making it flexible.

### 5. Data Structures (Schemas - `src/signal_sync/ta/schemas.py`)

Pydantic models are used to define the structured JSON output for each task, ensuring consistency and type safety.

*   `ValidationResult`: Details of data validation (success, rows, dropped rows).
*   `MarketDataTaskOutput`: Output for market data fetching, including `bundle_file` path.
*   `TrendIndicators`, `MomentumIndicators`, `VolatilityIndicators`, `VolumeIndicators`: Sub-schemas defining the various computed indicator values.
*   `IndicatorTaskOutput`: Aggregates all indicator results.
*   `VisualReview`: Details of the chart's visual analysis (summary, confidence, status).
*   `PatternDetectionTaskOutput`: Lists detected candlestick and chart patterns, `chart_path`, and `visual_review`.
*   `SupportResistanceTaskOutput`: Provides identified support/resistance zones, evidence, and confidence scores.
*   `StrategySignalTaskOutput`: Captures the overall stance (`bullish`, `bearish`, `neutral`), confidence, thesis, and supporting evidence.
*   `ExplanationSummary`: A summary of the stance, confidence, and thesis for the final explanation.
*   `ExplanationTaskOutput`: The final structured output, including `summary`, detailed explanations for indicators, patterns, and S/R, along with `uncertainty_notes` and a `monitoring_checklist`.

### 6. Explanation Generation (`explanation_generator.py`, `explanations.py`)

*   `explanations.py`: This module contains static, plain-language mappings for various technical indicators and patterns. It translates technical jargon into simple meanings, implications, and actionable takeaways for investors. This ensures consistent and objective explanations.
    *   Functions: `explain_indicator(name: str, value: Optional[Any])` and `explain_pattern(name: str)`.
*   `explanation_generator.py`: This module acts as an orchestrator for creating a comprehensive explanation from the various outputs of the TA pipeline. It finds relevant indicator values and patterns from the results and uses the `explanations.py` mappings to generate a structured output of explanations and concise takeaways.

### 7. API Integration (`src/api/`)

The TA module exposes its functionality via a FastAPI endpoint for asynchronous job execution and status tracking, following a common pattern established for BGV analysis.

*   `src/api/ta_api.py`: Defines the FastAPI endpoints for interacting with the TA analysis.
    *   `POST /api/ta/start`: Initiates a TA job. Takes `company_name`, `ticker`, `sector`, `horizon`, and an optional `annual_report` (uploaded file) as input. It creates a job record, saves the annual report if provided, and schedules `run_ta_job` as a background task.
    *   `GET /api/ta/status/{job_id}`: Allows polling for the status of a TA job. Returns the full job record.
    *   `GET /api/ta/result/{job_id}`: Fetches the final structured JSON result of a completed TA job. Includes logic to normalize the result payload if it's wrapped in markdown.
    *   `GET /api/ta/artifacts/{job_id}/{filename}`: Serves artifact files (e.g., generated charts) associated with a specific TA job.
*   `src/api/jobs_store.py`: Manages the persistence of job records (e.g., status, progress, metadata) using a file-based JSON store (`jobs.json`) for prototyping.
*   `src/api/ta_analysis_steps.py`: Defines `TA_STEP_DEFINITIONS`, which is a list of dictionaries outlining each step of the TA analysis, including its `key`, `label`, and the `agent` responsible. It also provides `build_step_progress` function to calculate job progress dynamically.
*   `src/signal_sync/ta/api_runner.py`: (Inferred, as specified in `crew_integration_spec.md`) This module contains the `run_ta_job` function, which is executed as a background task. It orchestrates the sequential execution of the `TAAnalysisCrew`, updating the job status in `jobs_store.py` after each step.

### 8. Frontend Integration

The Streamlit application (`streamlit_app/app.py`) integrates with the TA API to provide a user-friendly interface:
*   A button on the stock details page likely triggers the `POST /api/ta/start` endpoint.
*   A dedicated TA progress UI (`frontend/ui/components/ta/TAAnalysisClient.jsx` - external to this project) polls the `GET /api/ta/status/{job_id}` endpoint to show real-time progress.
*   Once completed, a TA report renderer (`frontend/ui/components/ta/TAReportView.jsx` - external to this project) fetches the results from `GET /api/ta/result/{job_id}` and maps the structured JSON output to visual cards, sections, and charts (for indicators, patterns, support/resistance, thesis, uncertainty, and monitoring checklists).

### 9. Key Design Principles and Constraints

*   **Determinism First:** All quantitative analysis is performed by deterministic Python tools.
*   **Explainability:** Outputs are structured and accompanied by plain-language explanations.
*   **Low Cost Model Usage:** The system is designed to be flexible with LLM providers to manage costs.
*   **Modularity:** Components (agents, tools) are modular and swappable.
*   **Tool-level Validation:** Tools perform defensive parsing and validation of their inputs and outputs.
*   **Backward Compatibility:** Tools support both raw JSON string and file-path inputs for OHLCV data.

### 10. Testing and Validation

*   **Unit Tests:** Individual deterministic tools are expected to have unit tests (e.g., `src/signal_sync/ta/tests/test_tools.py`).
*   **Edge-case Testing:** Specific focus on malformed/incomplete OHLCV payloads.
*   **Regression Tests:** For both `bundle_file` and non-bundle inputs.
*   **Integration Tests:** Snapshot tests for full crew outputs are planned to ensure end-to-end correctness.

### 11. Future Enhancements

*   Implementation of typed schemas for all task outputs within CrewAI.
*   Integration of backtesting and signal quality evaluation.
*   Optional branches for sentiment and macroeconomic analysis.
*   Development of a production-ready API endpoint for TA crew execution.
*   Expansion of the pattern library and calibration of confidence scores.

This documentation serves as a comprehensive guide to the Technical Analysis module, its components, flow, and underlying principles, providing all necessary context for further development, analysis, and visualization.