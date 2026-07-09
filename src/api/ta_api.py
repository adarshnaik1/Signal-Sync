import os
import sys
import json
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure src is on path so we can import project modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.jobs_store import create_job, get_job, update_job
from signal_sync.ta.api_runner import run_ta_job

app = FastAPI(title="TA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_result_payload(data):
    """Return structured TA JSON even if the saved payload is wrapped as {raw: '```json...```'}."""
    if not isinstance(data, dict):
        return data

    raw = data.get("raw")
    if not isinstance(raw, str):
        return data

    text = raw.strip()
    if text.startswith("```"):
        end = text.rfind("```")
        if end > 0:
            inner = text[3:end].strip()
            if "\n" in inner:
                first, rest = inner.split("\n", 1)
                first = first.strip().lower()
                if first.startswith("json") or first.isalpha():
                    inner = rest.strip()
            text = inner

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return data


@app.post("/api/ta/start")
async def start_ta(
    background: BackgroundTasks,
    company_name: str = Form(...),
    ticker: str = Form(...),
    sector: str = Form(""),
    horizon: str = Form("medium-term"),
    annual_report: Optional[UploadFile] = File(None),
):
    metadata = {"company_name": company_name, "ticker": ticker, "sector": sector, "horizon": horizon}
    job = create_job(metadata, prefix="ta")
    job_id = job["job_id"]

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

    background.add_task(run_ta_job, job_id, company_name, ticker, sector, horizon)

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/ta/status/{job_id}")
def ta_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/ta/result/{job_id}")
def ta_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job not completed")

    stored_result = job.get("result_json")
    if isinstance(stored_result, dict) and stored_result:
        return _normalize_result_payload(stored_result)

    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Result file not found")

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _normalize_result_payload(data)


@app.get("/api/ta/artifacts/{job_id}/{filename}")
def ta_artifact(job_id: str, filename: str):
    # Serve artifact files created by TA runs; restrict to artifacts directory
    artifacts_root = os.path.abspath(os.path.join(ROOT, "signal_sync", "ta", "artifacts"))
    safe_dir = os.path.abspath(os.path.join(artifacts_root, job_id))
    if not safe_dir.startswith(artifacts_root):
        raise HTTPException(status_code=400, detail="Invalid job id")
    file_path = os.path.join(safe_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Artifact not found: looked at {file_path}")
    return FileResponse(file_path)