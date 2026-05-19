import os
from datetime import datetime
from signal_sync.crew import BGVCrew
from api.jobs_store import update_job


def run_bgv_job(job_id: str, company_name: str, ticker: str, sector: str, annual_report_path: str | None = None):
    """
    Run the BGVCrew for a specific job and update job store as it progresses.
    This is intended to be run in a background thread/task.
    """
    try:
        # create job-specific output filename
        output_dir = os.path.join(os.path.dirname(__file__), "output_data")
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        safe_ticker = (ticker or "company").replace('/', '_')
        output_path = os.path.join(output_dir, f"{safe_ticker}_bgv_{ts}.json")

        update_job(job_id, status="running", progress=10, output_path=output_path)

        bgv = BGVCrew(
            company_name=company_name,
            ticker=ticker,
            sector=sector,
            annual_report_path=annual_report_path or ""
        )

        # override output_path on the crew instance
        bgv.output_path = output_path

        # run the crew (this may be long-running)
        result_path = bgv.run()

        update_job(job_id, status="done", progress=100, output_path=result_path)
    except Exception as e:
        update_job(job_id, status="failed", progress=100, error=str(e))
