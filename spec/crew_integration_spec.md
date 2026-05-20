# Crew Integration Specification

Version: 1.0
Date: 2026-05-19
Author: GitHub Copilot (pair-programming assistant)

Purpose
-------
This document describes the integration contract and operational behavior for integrating a "crew" (BGV crew) into the Signal Sync system. It captures the backend API, job store schema, runner behavior, progress model, frontend contract, error handling, testing guidance, and rollout notes.

Scope
-----
- BGVCrew integration (agentic sequence of tasks) exposed via FastAPI endpoints.
- File-based job store used for prototype persistence (`src/api/jobs_store.py`).
- Frontend integration points in Next.js: `AnalysisRunView.jsx` and related BGV report components.

Architecture Overview
---------------------
- Client triggers a job via POST `/api/bgv/start` (or equivalent) which creates a job record and schedules `run_bgv_job(job_id, ...)` as a background task.
- `run_bgv_job` (runner) executes the crew sequentially, updating the job via `update_job()` after each step and at key transition points.
- Job state and final structured output are persisted on-disk; frontend polls `/api/bgv/status/{job_id}` for progress and `/api/bgv/result/{job_id}` for final output.

Key Files
---------
- Backend runner: `src/signal_sync/api_runner.py`
- Step definitions / progress helper: `src/api/analysis_steps.py`
- Job store: `src/api/jobs_store.py`
- API endpoints: `src/api/bgv_api.py`
- Crew implementation: `src/signal_sync/crew.py` (BGVCrew)
- Frontend progress UI: `frontend/ui/components/analysis/AnalysisRunView.jsx`
- Frontend report renderer: `frontend/ui/components/bgv/BGVReportView.jsx`

API Contract
------------
Start job (request):
- POST `/api/bgv/start`
- Body: { company_name, ticker, sector, optional: annual_report (file or path) }
- Response: { job_id }

Status poll (response):
- GET `/api/bgv/status/{job_id}`
- Response: full job record (JSON)
  - Required fields used by UI:
    - `job_id` (string)
    - `status` (queued|running|done|failed)
    - `progress` (0-100 integer)
    - `current_step` (string)
    - `current_agent` (string|null)
    - `step_message` (string|null)
    - `completed_steps` (array of step-def objects)
    - `remaining_steps` (array of step-def objects)
    - `created_at`, `updated_at` (ISO datetimes)
    - `output_path` (string)
    - `metadata` (object, e.g., company_name, ticker)

Result fetch (final output):
- GET `/api/bgv/result/{job_id}`
- Response: structured JSON produced by the crew (BGVOutput schema)

Job Store Schema (essential fields)
-----------------------------------
- job_id: string
- status: string
- progress: number
- current_step: string
- current_agent: string|null
- step_message: string|null
- completed_steps: array
- remaining_steps: array
- output_path: string
- metadata: object
- created_at / updated_at: ISO timestamp
- error: nullable string

Progress Model and Step Definitions
----------------------------------
- Progress is represented as an integer 0-100. The helper `build_step_progress(step_defs, completed_count)` should consistently compute:
  - `progress` (rounded integer)
  - `current_step` (label of current step or `Complete`)
  - `current_agent`
  - `completed_steps` (array slice of step definitions)
  - `remaining_steps` (array slice of step definitions)

- Step definition object shape (shared backend/frontend):
  - `key` (stable string id)
  - `label` (human readable label)
  - `agent` (agent role name)

Runner Behavior (implementation notes)
--------------------------------------
- On job start:
  - Create output path and instantiate the crew instance with inputs.
  - Persist initial `status=running`, `progress=0`, `current_step=Initializing` via `update_job()`.
- Per-step execution loop:
  - For each step index:
    - Call `build_step_progress()` to compute progress dict.
    - Call `update_job(job_id, status="running", output_path=..., step_message="Running <label>", **progress_state)`.
    - Execute the task synchronously (or await async executor) and capture its output.
    - After step completes, call `build_step_progress()` for `index+1` and update job with `step_message="Completed <label>"` and `**completed_state`.
- On success:
  - Persist structured output JSON via crew's saver.
  - Call `update_job(job_id, status="done", progress=100, current_step="Complete", step_message="BGV analysis complete", completed_steps=all_steps, remaining_steps=[])`.
- On failure:
  - Capture exception, set `status="failed"`, `error=str(e)`, `progress` set to current progress (or 100 if terminal), and `step_message` describing failure.

Frontend Contract (UI expectations)
----------------------------------
- The frontend polling UI (`AnalysisRunView.jsx`) expects the status payload to include the fields listed above.
- UI layout rules:
  - Row 1: two side-by-side cards — `Live Progress` (left) and `Run Summary` (right).
  - Row 2: full-width `Final Report` area rendered only when `status === 'done'` and result is available.
- The `renderResult(result, job)` callback should render the structured BGV output. The frontend should *not* display raw JSON; instead map fields to cards/sections (scores, company profile, findings, evidence groups).

Error Handling and Retries
-------------------------
- Runner should catch and log exceptions from each step and surface a concise message to `job.step_message` and `job.error`.
- For transient tool/HTTP errors, consider adding a limited retry loop (e.g., 3 attempts with exponential backoff) inside the task execution wrapper.
- The job store `update_job()` must be robust to partial updates; use atomic writes and file locks when persisting JSON.

Security and Resource Limits
----------------------------
- Validate input fields at `/api/bgv/start` to avoid injection or overly large payloads.
- For file uploads (PDFs), store temporarily in a controlled directory with size limits and scanning if required.
- Rate-limit job creation per-user/IP in production.

Testing & Validation
--------------------
- Unit tests for `build_step_progress()` that cover edge cases: zero steps, one step, all steps complete.
- Integration test: start a job, poll status until completion, assert final `status==='done'` and result schema matches expectations.
- UI test: mount `AnalysisRunView` with a mock poller to simulate transitions (queued→running→done) and assert layout behavior (two columns + full-width result).

Deployment & Rollout
--------------------
- This integration is prototype-friendly with file-based persistence. For production, swap `jobs_store` to a durable DB (Postgres/Redis) and keep same API contract.
- Monitor long-running job queues and provide operator tooling to cancel or restart jobs.

Open Items
----------
- Switch LLM provider from OpenAI to OpenRouter (deferred). Update agent initialization accordingly.
- Consider upgrading polling to SSE/WebSocket for better UX and reduced load.
- Add authentication/authorization around job creation and result access.

Appendix: Quick examples
-----------------------
Example: minimal status response

```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": 42,
  "current_step": "Company overview",
  "current_agent": "ResearchAgent",
  "step_message": "Running Company overview",
  "completed_steps": [{"key":"overview","label":"Company overview","agent":"ResearchAgent"}],
  "remaining_steps": [{"key":"finance","label":"Financial checks","agent":"FinanceAgent"}],
  "created_at": "2026-05-19T12:00:00Z",
  "updated_at": "2026-05-19T12:00:30Z",
  "output_path": "src/signal_sync/output_data/TSLA_bgv_20260519T120030Z.json",
  "metadata": {"company_name":"Tesla","ticker":"TSLA"}
}
```


---

If you want, I can:
- Commit this spec to Git and add a short PR message.
- Expand any section (e.g., retry policy, export formats, or migrate `jobs_store` to Postgres).
