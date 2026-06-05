# Integrate Fundamental Analysis Pipeline with Frontend

Integrate the existing `agentic_pipeline` (fundamental analysis) into the Signal Sync frontend, following the same start/status/result pattern used by BGV and TA.

## Proposed Changes

The fundamental analysis pipeline has 6 sequential stages: **Data Acquisition → Business Analysis → Financial Analysis → Risk Analysis → Valuation → Investment Verdict**. Unlike BGV/TA which use CrewAI's internal task execution loop, the fundamental pipeline calls each agent's `run_*` method directly (each agent internally calls `llm.call()` instead of relying on crew task orchestration). The API runner will therefore call the pipeline's steps sequentially, updating job progress after each.

---

### Backend: API Layer

#### [NEW] [fa_analysis_steps.py](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/src/api/fa_analysis_steps.py)
- Define `FA_STEP_DEFINITIONS` (6 steps matching the pipeline stages):
  1. `data_acquisition_task` → "Data Acquisition" → "Data Acquisition Specialist"
  2. `business_analysis_task` → "Business Analysis" → "Business Analysis Specialist"  
  3. `financial_analysis_task` → "Financial Analysis" → "Financial Analysis Specialist"
  4. `risk_analysis_task` → "Risk Analysis" → "Risk Analysis Specialist"
  5. `valuation_task` → "Valuation" → "Valuation Specialist"
  6. `verdict_task` → "Investment Verdict" → "Investment Verdict Specialist"
- Reuse the same `build_step_progress()` function pattern from `analysis_steps.py`

#### [NEW] [fa_api_runner.py](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/src/agentic_pipeline/fa_api_runner.py)
- `run_fa_job(job_id, company_name, ticker, sector, exchange)` function
- Unlike TA/BGV which use CrewAI's internal `crew.tasks` loop, this runner will call each agent's `run_*` method sequentially:
  1. `DataAcquisitionCrew().run(ticker, exchange)` → unified_schema
  2. `BusinessAnalysisCrew().run_business_analysis(unified_schema)` → business_analysis
  3. `FinancialAnalysisCrew().run_financial_analysis(unified_schema)` → financial_analysis
  4. `RiskAnalysisCrew().run_risk_analysis(unified_schema)` → risk_analysis
  5. `ValuationCrew().run_valuation(unified_schema)` → valuation_analysis
  6. `VerdictCrew().run_verdict(business, financial, risk, valuation)` → verdict
- After each step: call `update_job()` with progress from `build_step_progress()`
- On completion: combine all results into a single dict, write to JSON file, and also store in `result_json`
- On failure: set `status="failed"` with error message
- Optionally run `ExplanationGenerator.generate()` to add executive summary

#### [MODIFY] [bgv_api.py](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/src/api/bgv_api.py)
- Add FA endpoints to the same FastAPI app (same pattern as TA endpoints already present):
  - `POST /api/fa/start` — accepts `company_name`, `ticker`, `sector`, `exchange` (defaults to "NSE")
  - `GET /api/fa/status/{job_id}` — returns job record
  - `GET /api/fa/result/{job_id}` — returns final JSON result
- Import `run_fa_job` from the new runner
- Create job with `prefix="fa"`

---

### Frontend: Components

#### [NEW] [faConfig.js](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/components/fa/faConfig.js)
- Export `FA_ANALYSIS_STEPS` array (matching `FA_STEP_DEFINITIONS` from backend)

#### [NEW] [FAAnalysisClient.jsx](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/components/fa/FAAnalysisClient.jsx)
- Wrapper component using `AnalysisRunView` with:
  - `statusPath="/api/fa/status"`
  - `resultPath="/api/fa/result"`
  - `title="Fundamental Analysis"`
  - `renderResult` → `<FAReportView />`

#### [NEW] [FAReportView.jsx](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/components/fa/FAReportView.jsx)
- Rich, structured report renderer for the fundamental analysis output. Sections:
  1. **Investment Verdict Hero** — dark gradient banner with verdict (BUY/HOLD/SELL), score, confidence, holding period
  2. **Company Identification** — symbol, name, exchange
  3. **Business Analysis** — business model, revenue drivers, competitive advantages, growth opportunities, industry outlook
  4. **Financial Analysis** — revenue growth, profitability, debt health, cash flow, operational efficiency cards with status indicators
  5. **Risk Analysis** — overall risk level, individual risk categories, warning signals
  6. **Valuation Analysis** — valuation status, PE analysis, growth vs valuation, intrinsic value outlook
  7. **Explanation** — executive summary, key strengths, key risks, what to monitor (if explanation generator ran)

---

### Frontend: Routes

#### [NEW] [page.jsx](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/src/app/fa/[jobId]/page.jsx)
- Next.js dynamic route page, same pattern as `ta/[jobId]/page.jsx`
- Renders `<FAAnalysisClient jobId={jobId} />`

#### [NEW] [loading.jsx](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/src/app/fa/[jobId]/loading.jsx)
- Loading spinner component, same pattern as TA

---

### Frontend: Stock Details CTA

#### [MODIFY] [StockDetails.jsx](file:///c:/Users/ADARSH%20NAIK/Desktop/signal_sync/frontend/ui/components/StockDetails.jsx)
- Add a third "Run Fundamental Analysis" button next to BGV and TA buttons
- Uses the existing `startAnalysis()` helper with:
  - `apiBase: BGV_API_BASE` (same server)
  - `routePrefix: "fa"`
  - `formFields: { company_name, ticker, sector, exchange: "NSE" }`
- Button styled with an emerald/green color scheme to differentiate from BGV (amber) and TA (dark)

---

## Verification Plan

### Manual Verification
- Start the FastAPI server (`uvicorn api.bgv_api:app`)
- Open the frontend, search for a stock, navigate to its details page
- Verify the "Run Fundamental Analysis" button appears
- Click the button, confirm navigation to `/fa/{job_id}`
- Verify live progress tracking shows all 6 steps completing
- Verify the final report renders with all sections populated
