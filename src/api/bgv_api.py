import os
import sys
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure src is on path so we can import project modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.jobs_store import create_job, get_job, update_job
from signal_sync.api_runner import run_bgv_job

app = FastAPI(title="BGV API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    company_name: str
    ticker: str
    sector: Optional[str] = ""


@app.post("/api/bgv/start")
async def start_bgv(
    background: BackgroundTasks,
    company_name: str = Form(...),
    ticker: str = Form(...),
    sector: str = Form(""),
    annual_report: Optional[UploadFile] = File(None),
):
    """
    Start a BGV job. Accepts form-data with optional PDF upload.
    Returns job_id to poll for status.
    """
    metadata = {"company_name": company_name, "ticker": ticker, "sector": sector}
    job = create_job(metadata)
    job_id = job["job_id"]

    # Handle file upload if present
    annual_path = None
    if annual_report:
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        filename = f"{job_id}_" + os.path.basename(annual_report.filename)
        dest = os.path.join(uploads_dir, filename)
        with open(dest, "wb") as f:
            f.write(await annual_report.read())
        annual_path = dest
        update_job(job_id, metadata={**metadata, "annual_report": dest})

    # Queue background task
    background.add_task(run_bgv_job, job_id, company_name, ticker, sector, annual_path)

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/bgv/status/{job_id}")
def bgv_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/bgv/result/{job_id}")
def bgv_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job not completed")
    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    import json
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
