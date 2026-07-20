from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Ensure src is on the path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.jobs_store import update_job
from api.news_analysis_steps import NEWS_STEP_DEFINITIONS, build_step_progress

from news_sentiment.config import Config
from news_sentiment.collector import NewsCollector
from news_sentiment.analyzer import SentimentAnalyzer
from news_sentiment.service import NewsSentimentService


def run_news_job(
    job_id: str,
    ticker: str,
    company_name: str,
):
    """
    Run the news sentiment analysis pipeline for a job.
    Updates the job store so the frontend can track progress.
    """
    try:
        # Output file setup
        output_dir = os.path.join(os.path.dirname(__file__), "output_data")
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_ticker = (ticker or "company").replace("/", "_")
        output_path = os.path.join(output_dir, f"{safe_ticker}_news_{ts}.json")

        # Initial status updates
        update_job(
            job_id,
            status="running",
            progress=0,
            output_path=output_path,
            current_step="Initializing",
            current_agent=None,
            step_message="Starting news sentiment analysis",
            completed_steps=[],
            remaining_steps=NEWS_STEP_DEFINITIONS,
        )

        # Helper to update progress before the step starts
        step = NEWS_STEP_DEFINITIONS[0]
        state = build_step_progress(NEWS_STEP_DEFINITIONS, 0)
        update_job(
            job_id,
            status="running",
            output_path=output_path,
            step_message=f"Running {step['label']}",
            **state,
        )

        # The query should be company name if present, otherwise ticker
        query = company_name if company_name else ticker
        
        # Initialize analyzer, collector, and service
        # Note: analyzer loads the model weights on the first run
        analyzer = SentimentAnalyzer(model_name=Config.FINBERT_MODEL)
        collector = NewsCollector(api_key=Config.SERPER_API_KEY)
        service = NewsSentimentService(collector=collector, analyzer=analyzer)

        # Execute analysis
        result = service.get_sentiment_analysis(query, days=45)

        if result.get("status") == "error":
            raise RuntimeError(result.get("message", "Unknown error in sentiment service."))

        # Update progress after the step completes
        completed_state = build_step_progress(NEWS_STEP_DEFINITIONS, 1)
        update_job(
            job_id,
            status="running",
            output_path=output_path,
            step_message=f"Completed {step['label']}",
            **completed_state,
        )

        # Persist result to output file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

        # Final done status update
        update_job(
            job_id,
            status="done",
            progress=100,
            output_path=output_path,
            result_json=result,
            current_step="Complete",
            current_agent=None,
            step_message="News sentiment analysis complete",
            completed_steps=NEWS_STEP_DEFINITIONS,
            remaining_steps=[],
        )

    except Exception as exc:
        update_job(
            job_id,
            status="failed",
            progress=100,
            error=str(exc),
            step_message="News sentiment analysis failed",
        )
