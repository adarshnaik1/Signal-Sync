"""
Fundamental Analysis API runner.

Executes the SignalSyncPipeline stages one-by-one, updating
the shared job store after each step so the frontend can poll
progress — exactly like BGV and TA runners.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Ensure the src directory is on the path so sibling packages resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure the agentic_pipeline package root is also importable
PIPELINE_ROOT = os.path.dirname(__file__)
if PIPELINE_ROOT not in sys.path:
    sys.path.insert(0, PIPELINE_ROOT)

from dotenv import load_dotenv

# Load the pipeline-local .env so OPENAI_API_KEY is available
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

from api.jobs_store import update_job
from api.fa_analysis_steps import FA_STEP_DEFINITIONS, build_step_progress

from agentic_pipeline.agents.data_acquisition_agent import DataAcquisitionCrew
from agentic_pipeline.agents.business_analysis_agent import BusinessAnalysisCrew
from agentic_pipeline.agents.financial_analysis_agent import FinancialAnalysisCrew
from agentic_pipeline.agents.risk_analysis_agent import RiskAnalysisCrew
from agentic_pipeline.agents.valuation_agent import ValuationCrew
from agentic_pipeline.agents.verdict_agent import VerdictCrew


def _try_explanation(business, financial, risk, valuation, verdict) -> Dict[str, Any]:
    """Optionally run the explanation generator; non-fatal on failure."""
    try:
        from agentic_pipeline.explainers.explanation_generator import ExplanationGenerator
        gen = ExplanationGenerator()
        return gen.generate(business, financial, risk, valuation, verdict)
    except Exception:
        return {}


def run_fa_job(
    job_id: str,
    company_name: str,
    ticker: str,
    sector: str,
    exchange: str = "NSE",
):
    """
    Run the full fundamental analysis pipeline for a job.

    Each of the 6 stages updates the job store so the frontend
    can track live progress via polling.
    """
    try:
        # ── output file ──────────────────────────────────────
        output_dir = os.path.join(os.path.dirname(__file__), "output_data")
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_ticker = (ticker or "company").replace("/", "_")
        output_path = os.path.join(output_dir, f"{safe_ticker}_fa_{ts}.json")

        # ── initial status ────────────────────────────────────
        update_job(
            job_id,
            status="running",
            progress=0,
            output_path=output_path,
            current_step="Initializing",
            current_agent=None,
            step_message="Starting fundamental analysis",
            completed_steps=[],
            remaining_steps=FA_STEP_DEFINITIONS,
        )

        # Helper to update progress before/after a step
        def _pre_step(index: int):
            step = FA_STEP_DEFINITIONS[index]
            state = build_step_progress(FA_STEP_DEFINITIONS, index)
            update_job(
                job_id,
                status="running",
                output_path=output_path,
                step_message=f"Running {step['label']}",
                **state,
            )

        def _post_step(index: int):
            step = FA_STEP_DEFINITIONS[index]
            state = build_step_progress(FA_STEP_DEFINITIONS, index + 1)
            update_job(
                job_id,
                status="running",
                output_path=output_path,
                step_message=f"Completed {step['label']}",
                **state,
            )

        # ── Step 1: Data Acquisition ─────────────────────────
        _pre_step(0)
        unified_schema = DataAcquisitionCrew().run(ticker, exchange)
        if isinstance(unified_schema, dict) and unified_schema.get("error"):
            raise RuntimeError(f"Data acquisition failed: {unified_schema['error']}")
        _post_step(0)

        # ── Step 2: Business Analysis ────────────────────────
        _pre_step(1)
        business_analysis = BusinessAnalysisCrew().run_business_analysis(unified_schema)
        _post_step(1)

        # ── Step 3: Financial Analysis ───────────────────────
        _pre_step(2)
        financial_analysis = FinancialAnalysisCrew().run_financial_analysis(unified_schema)
        _post_step(2)

        # ── Step 4: Risk Analysis ────────────────────────────
        _pre_step(3)
        risk_analysis = RiskAnalysisCrew().run_risk_analysis(unified_schema)
        _post_step(3)

        # ── Step 5: Valuation ────────────────────────────────
        _pre_step(4)
        valuation_analysis = ValuationCrew().run_valuation(unified_schema)
        _post_step(4)

        # ── Step 6: Investment Verdict ───────────────────────
        _pre_step(5)
        verdict = VerdictCrew().run_verdict(
            business_analysis,
            financial_analysis,
            risk_analysis,
            valuation_analysis,
        )
        _post_step(5)

        # ── Assemble final payload ───────────────────────────
        result_payload: Dict[str, Any] = {
            "company_identification": unified_schema.get("company_identification", {}),
            "company_metadata": unified_schema.get("company_metadata", {}),
            "market_data": unified_schema.get("market_data", {}),
            "financial_ratios": unified_schema.get("financial_ratios", {}),
            "business_analysis": business_analysis.get("business_analysis", {}),
            "financial_analysis": financial_analysis.get("financial_analysis", {}),
            "risk_analysis": risk_analysis.get("risk_analysis", {}),
            "valuation_analysis": valuation_analysis.get("valuation_analysis", {}),
            "investment_verdict": verdict,
        }

        # ── Optional explanation layer ───────────────────────
        explanation = _try_explanation(
            business_analysis,
            financial_analysis,
            risk_analysis,
            valuation_analysis,
            verdict,
        )
        if explanation:
            result_payload["explanation"] = explanation

        # ── Persist result ───────────────────────────────────
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2, default=str)

        update_job(
            job_id,
            status="done",
            progress=100,
            output_path=output_path,
            result_json=result_payload,
            current_step="Complete",
            current_agent=None,
            step_message="Fundamental analysis complete",
            completed_steps=FA_STEP_DEFINITIONS,
            remaining_steps=[],
        )
    except Exception as exc:
        update_job(
            job_id,
            status="failed",
            progress=100,
            error=str(exc),
            step_message="Fundamental analysis failed",
        )
