import json
import os
import threading
from datetime import datetime
import uuid

JOBS_FILE = os.path.join(os.path.dirname(__file__), "jobs.json")
_lock = threading.Lock()


def _load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_jobs(jobs):
    with _lock:
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, default=str)


def create_job(metadata: dict, prefix: str = "bgv") -> dict:
    jobs = _load_jobs()
    safe_prefix = (prefix or "job").strip().lower()
    job_id = f"{safe_prefix}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    job = {
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata,
        "progress": 0,
        "current_step": None,
        "current_agent": None,
        "step_message": "Queued",
        "completed_steps": [],
        "remaining_steps": [],
        "output_path": None,
        "error": None,
    }
    jobs[job_id] = job
    _save_jobs(jobs)
    return job


def update_job(job_id: str, **fields) -> dict:
    jobs = _load_jobs()
    job = jobs.get(job_id)
    if not job:
        raise KeyError(f"Job not found: {job_id}")
    job.update(fields)
    job["updated_at"] = datetime.utcnow().isoformat() + "Z"
    jobs[job_id] = job
    _save_jobs(jobs)
    return job


def update_job_progress(job_id: str, **fields) -> dict:
    return update_job(job_id, **fields)


def get_job(job_id: str) -> dict:
    jobs = _load_jobs()
    return jobs.get(job_id)


def list_jobs() -> dict:
    return _load_jobs()
