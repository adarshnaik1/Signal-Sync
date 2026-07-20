## Background Verification (BGV) Agentic Flow Documentation

The Background Verification (BGV) module within Signal Sync is designed to perform a comprehensive due diligence process on companies. It leverages a multi-agent system built on CrewAI to research various aspects of a company, identify potential risks, and compile a final assessment. This documentation details its architecture, agents, tools, data flow, and output storage.

### 1. Introduction and Objective

The primary objective of the BGV module is to automate and streamline the process of company background verification for retail investment advisors. This includes assessing:
*   Company overview and profile.
*   Management team background and potential red flags.
*   Financial irregularities.
*   Market manipulation or scam signals.

The system aims to provide a structured and evidence-based report that contributes to informed investment decisions by highlighting potential risks and trustworthiness indicators.

### 2. Crew Architecture and Execution Flow

The BGV module employs a sequential CrewAI architecture, where a series of specialized agents collaborate to conduct the verification. The `BGVCrew` (defined in `src/signal_sync/crew.py`) orchestrates this flow.

**The sequential flow is as follows:**

1.  **Company Overview Agent**
2.  **Management Research Agent**
3.  **Financial Irregularities Agent**
4.  **Scam Detection Agent**
5.  **BGV Report Compiler Agent**

Each agent's role and goal are implicitly defined within the `src/signal_sync/crew.py` file, drawing configurations from `self.agents_config` and `self.tasks_config`. These configurations are loaded from YAML files (e.g., `config/agents.yaml`, `config/tasks.yaml`) but in this specific implementation, they are directly referenced via attribute access (`self.agents_config['agent_name']`). The `BGVCrew` also handles pre-processing of an optional annual report PDF to provide context to the agents.

#### 2.1. Agent Definitions and Roles (`src/signal_sync/crew.py` implicitly configures agents)

| Agent Name                               | Role                                                  | Goal                                                                                                      | LLM Usage (Inferred)                                                                                                |
| :--------------------------------------- | :---------------------------------------------------- | :-------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| `company_overview_agent`                 | Corporate Intelligence Analyst                        | Generates a comprehensive company overview.                                                               | Used to synthesize information from web searches and PDF documents to create a company profile.                     |
| `management_research_agent`              | Executive Background Verification Specialist          | Researches the backgrounds of key management personnel.                                                   | Used to search for public records, news, and reports about management, identifying any red flags or controversies. |
| `financial_irregularities_agent`         | Forensic Financial Analyst                            | Detects potential financial irregularities.                                                               | Analyzes extracted financial data and external reports to identify anomalies or suspicious financial activities.  |
| `scam_detection_agent`                   | Market Manipulation Detection Specialist              | Identifies signals related to market manipulation or fraudulent activities.                               | Interprets stock trading patterns and other market data for signs of manipulation.                                  |
| `bgv_report_compiler`                    | BGV Report Compiler                                   | Compiles the findings from all previous agents into a structured, final BGV report.                       | Synthesizes the outputs from all prior agents, calculates scores, and generates a final verdict.                    |

#### 2.2. Task Definitions and Dependencies (`src/api/analysis_steps.py` and `src/signal_sync/crew.py`)

The BGV tasks are defined in `src/api/analysis_steps.py` as `BGV_STEP_DEFINITIONS`. These steps are then used by `src/signal_sync/crew.py` to create the actual CrewAI `Task` objects.

| Task Name                         | Label                      | Agent                                     | Dependencies (Context)                                                                        | Expected Output (Pydantic Schema)            |
| :-------------------------------- | :------------------------- | :---------------------------------------- | :-------------------------------------------------------------------------------------------- | :------------------------------------------- |
| `company_overview_task`           | Company Overview           | Corporate Intelligence Analyst            | None                                                                                          | `CompanyOverviewOutput`                      |
| `management_research_task`        | Management Research        | Executive Background Verification Specialist | None                                                                                          | `ManagementResearchOutput`                   |
| `financial_irregularities_task`   | Financial Irregularities   | Forensic Financial Analyst                | None                                                                                          | `FinancialIrregularitiesOutput`              |
| `scam_detection_task`             | Scam Detection             | Market Manipulation Detection Specialist  | None                                                                                          | `ScamDetectionOutput`                        |
| `compile_bgv_report_task`         | Final Report               | BGV Report Compiler                       | `company_overview_task`, `management_research_task`, `financial_irregularities_task`, `scam_detection_task` | `BGVOutput` (The final comprehensive report) |

### 3. Tools and APIs Accessed

The agents in the BGV flow utilize a set of specialized tools and APIs to gather and process information.

*   **`SerperDevTool()`**: (CrewAI Tool) This tool is used by multiple agents, notably `company_overview_agent` and `management_research_agent`, for general web searching. It provides access to search engine results, enabling agents to find publicly available information about companies and individuals. (Implicitly imported from `crewai_tools`, configured via environment variables for API keys).

*   **`StockDataTool()` (`src/signal_sync/tools/stock_tool.py`)**:
    *   **Description:** Fetches historical stock data (price, volume) from Yahoo Finance. It also performs basic analysis to detect anomalies like large price movements, volume spikes, and significant price gaps, which can be indicators of market manipulation.
    *   **Used by:** `scam_detection_agent`.
    *   **Input:** `ticker`, `period`, `interval`.
    *   **Output:** JSON summary including price/volume metrics, detected anomalies, risk indicators, and a path to a cached JSON file containing the raw data.
    *   **Caching:** Data is cached locally in `src/signal_sync/tools/cache/` to avoid redundant API calls.

*   **PDF Extraction Tools (`src/signal_sync/tools/pdf_extraction_tool.py`)**: These tools are dynamically added to agents if an `annual_report_path` is provided during the `BGVCrew` initialization.
    *   `PDFTextExtractTool()`: Extracts raw text content from PDF documents, optionally from specific page ranges.
    *   `PDFTableExtractTool()`: Extracts tabular data from PDF documents, with an option to filter for financial tables. Tables are formatted into a readable text format.
    *   `PDFFullAnalysisTool()`: Performs a comprehensive analysis, extracting both text and tables, and provides a structured summary suitable for initial document overview.
    *   `CustomPDFSearchTool()` (aliased from `PDFSearchTool`): Searches for specific terms or phrases within a PDF and returns relevant contextual excerpts.
    *   **Used by:**
        *   `company_overview_agent`: Uses `PDFTextExtractTool` and `PDFFullAnalysisTool` to understand the company from its official reports.
        *   `management_research_agent`: Uses `CustomPDFSearchTool` to search for management-related information within the annual report.
        *   `financial_irregularities_agent`: Uses `PDFTableExtractTool` and `PDFFullAnalysisTool` to analyze financial tables and detect irregularities.
    *   **Internal dependencies:** These tools rely on `signal_sync.helpers.text_extractor` and `signal_sync.helpers.table_extractor` for the core extraction logic.

*   **`BGVCrew`'s Internal PDF Pre-extraction:**
    *   Upon initialization with an `annual_report_path`, the `BGVCrew` itself calls `_extract_pdf_context()` to pre-process the PDF. This involves:
        *   Extracting text sections (`extract_text_sections_impl`).
        *   Extracting all tables (`extract_tables_impl`).
        *   Extracting financial tables specifically (`extract_financial_tables`).
    *   This pre-extracted context is then summarized (`_build_pdf_context_summary()`) and provided to the agents as part of their initial `inputs`. This is a crucial step to reduce the cognitive load on agents and ensure relevant PDF data is available.

### 4. How Results Are Generated and Stored

#### 4.1. Execution Flow

1.  **Initiation:** The BGV process can be initiated either via the CLI (`src/signal_sync/main.py`) or via the FastAPI endpoint (`POST /api/bgv/start` in `src/api/bgv_api.py`).
2.  **Job Creation:** When initiated via the API, a new job record is created using `api.jobs_store.create_job`, assigning a unique `job_id`.
3.  **Background Task:** The core BGV logic is run in a background task (e.g., using `FastAPI.BackgroundTasks` for the API, or directly for CLI). `run_bgv_job` (`src/signal_sync/api_runner.py`) is responsible for this.
4.  **Crew Initialization:** Inside `run_bgv_job`, an instance of `BGVCrew` (`src/signal_sync/crew.py`) is created with the provided company details and `annual_report_path`.
5.  **PDF Context Pre-extraction:** If an annual report is provided, the `BGVCrew` extracts key information from it upfront and stores it in `self.pdf_context`.
6.  **Sequential Task Execution:** The `BGVCrew` then executes its predefined tasks sequentially.
    *   Each task is handled by a specific agent.
    *   Agents use their assigned tools (SerperDevTool, StockDataTool, PDF extraction tools) to gather information.
    *   The output of each task is passed as context to subsequent tasks, building up the overall analysis.
7.  **Progress Tracking:** As each task completes, `src/signal_sync/api_runner.py` updates the job status in `api.jobs_store` using `update_job`. This includes `progress` percentage, `current_step`, `current_agent`, `step_message`, and lists of `completed_steps` and `remaining_steps` (defined in `src/api/analysis_steps.py`).

#### 4.2. Output Generation (`src/signal_sync/crew.py`)

*   **Final Task:** The `compile_bgv_report_task` is the last task, executed by the `bgv_report_compiler` agent. Its primary role is to synthesize all the findings from the preceding agents.
*   **Structured Output:** The output of this final task is expected to conform to the `BGVOutput` Pydantic schema (defined in `signal_sync.schemas.bgv_schemas`).
*   **Post-processing (`_save_structured_output`):** After the crew `kickoff` completes, the `_save_structured_output` method in `BGVCrew` attempts to:
    1.  Extract the JSON output from the raw CrewAI result, handling cases where it might be wrapped in markdown code blocks (`_extract_json_from_text`).
    2.  Validate the extracted output against the `BGVOutput` Pydantic schema.
    3.  If validation fails or is partial, it merges the data with a default structure (`_merge_with_defaults`) and attempts to recalculate `scores` and `final_verdict` based on available findings (`_calculate_scores`, `_generate_verdict`). This ensures a consistent output structure even with imperfect LLM responses.

#### 4.3. Data Storage

*   **Temporary Uploads:** If an `annual_report` PDF is uploaded via the API, it's saved temporarily in an `uploads` directory (e.g., `src/api/uploads/`).
*   **Job Records:** The metadata and status of each BGV job (including `job_id`, `status`, `progress`, `output_path`, `metadata`) are stored in `jobs.json` by `api.jobs_store.py`.
*   **Final BGV Report:** The complete, structured BGV analysis (conforming to `BGVOutput` schema) is saved as a JSON file (e.g., `company_ticker_bgv_timestamp.json`) in the `src/signal_sync/output_data/` directory. The path to this file is stored in the job record.

#### 4.4. Output Structure (`signal_sync.schemas.bgv_schemas` - Inferred, but based on `streamlit_app/app.py` and `crew.py` usage)

The `BGVOutput` schema is crucial. Based on usage in `streamlit_app/app.py` and logic in `crew.py`, it contains:

*   **`meta`**: Metadata about the analysis (e.g., `generated_at`, `pipeline_version`, `sources`).
*   **`company`**: Detailed company profile (name, ticker, sector, headquarters, founded year, employees, summary).
*   **`scores`**: Numerical risk scores for different aspects:
    *   `trustworthiness_score`
    *   `financial_integrity_score`
    *   `management_risk_score`
    *   `market_manipulation_risk_score`
*   **`findings`**: Categorized findings from each agent:
    *   `overview_findings`
    *   `management_findings`
    *   `financial_irregularities`
    *   `scam_signals`
*   **`evidence`**: Supporting evidence, including `people_profiles` with `red_flags`.
*   **`final_verdict`**: A concise textual verdict (e.g., "LOW RISK", "CRITICAL RISK") generated based on the scores and findings.
*   **`raw_analysis`**: (Optional) The raw output from the crew, truncated if very large, as a fallback.

### 5. LLM Usage

The LLMs are integral to the agent's ability to interpret information, make decisions, and synthesize complex findings.
*   **Information Synthesis:** Agents use LLMs to process raw data from tools (search results, extracted PDF text/tables, stock analysis summaries) and synthesize it into coherent findings for their specific task.
*   **Reasoning:** LLMs enable agents to reason about potential risks, evaluate evidence, and identify patterns that contribute to their assigned goals (e.g., `management_research_agent` identifying red flags).
*   **Report Generation:** The `bgv_report_compiler` agent's LLM is responsible for structuring the final report, generating the `final_verdict`, and summarizing findings based on the numerical scores and textual evidence.

The actual LLM model used is configurable through CrewAI's environment variables or project settings (e.g., `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, or settings for other providers like OpenRouter). The design emphasizes using LLMs for high-level reasoning and synthesis, while delegating deterministic data processing to specialized tools.

### 6. Integration with Streamlit Frontend

The BGV backend is designed to integrate seamlessly with the Streamlit frontend (`streamlit_app/app.py`):
*   **Job Initiation:** The Streamlit app sends a `POST` request to `/api/bgv/start` with company details and an optional PDF upload.
*   **Progress Display:** The frontend continuously polls `/api/bgv/status/{job_id}` to update the user on the job's progress, current step, and messages.
*   **Result Visualization:** Once the job is `done`, the frontend fetches the final report from `/api/bgv/result/{job_id}` and renders it using custom components to display scorecards, detailed findings, company profiles, and the final verdict in a visually appealing manner.

This detailed documentation provides a comprehensive understanding of the BGV agentic flow, its internal mechanisms, and its role within the Signal Sync project.