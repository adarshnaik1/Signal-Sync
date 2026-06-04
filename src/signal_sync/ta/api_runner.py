from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

from crewai import Process

from api.jobs_store import update_job
from api.ta_analysis_steps import TA_STEP_DEFINITIONS, build_step_progress
from signal_sync.ta.crew import TAAnalysisCrew
from signal_sync.ta.explanation_generator import generate_explanations

DETERMINISTIC_RESULT_KEYS = (
    "bundle_file",
    "daily_rows",
    "weekly_rows",
    "actions_count",
    "validation",
    "trend",
    "momentum",
    "volatility",
    "volume",
    "candlestick_patterns",
    "chart_patterns",
    "chart_path",
    "chart_url",
    "rows_rendered",
    "source_key",
    "visual_review",
    "support_zones",
    "resistance_zones",
    "evidence_by_layer",
    "swing_highs",
    "swing_lows",
    "volume_zones",
    "dynamic_support",
    "dynamic_resistance",
)


def _task_label(task: Any, index: int) -> str:
    return getattr(task, "name", None) or f"Step {index + 1}"


def _parse_output(payload: Any) -> dict:
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "json_dict") and payload.json_dict:
        return payload.json_dict
    if hasattr(payload, "raw"):
        raw = payload.raw
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            # strip fenced code blocks like ```json\n{...}\n``` if present
            s = raw.strip()
            if s.startswith("```"):
                end = s.rfind("```")
                if end > 0:
                    inner = s[3:end]
                    # drop leading language token if present (e.g., json)
                    if "\n" in inner:
                        first, rest = inner.split("\n", 1)
                        if first.strip().isalpha() or first.strip().lower().startswith("json"):
                            inner = rest
                    s = inner.strip()
            try:
                return json.loads(s)
            except Exception:
                return {"raw": raw}
    if isinstance(payload, str):
        s = payload.strip()
        if s.startswith("```"):
            end = s.rfind("```")
            if end > 0:
                inner = s[3:end]
                if "\n" in inner:
                    first, rest = inner.split("\n", 1)
                    if first.strip().isalpha() or first.strip().lower().startswith("json"):
                        inner = rest
                s = inner.strip()
        try:
            return json.loads(s)
        except Exception:
            return {"raw": payload}
    return {"raw": str(payload)}


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == "N/A" or value == "Rendering failed; chart not available."


def _normalize_visual_review(value: Any, chart_path: str | None = None) -> dict:
    if isinstance(value, dict):
        normalized = dict(value)
    elif isinstance(value, str) and value.strip():
        lowered = value.strip().lower()
        status = "unavailable" if "fail" in lowered or "unable" in lowered or "not found" in lowered else "reported"
        normalized = {
            "success": status == "reported",
            "visual_summary": value.strip(),
            "confidence": 0.0,
            "advisory_only": True,
            "image_analysis_status": status,
        }
    else:
        normalized = {
            "success": False,
            "visual_summary": "Vision review was not returned by the pattern detection step.",
            "confidence": 0.0,
            "advisory_only": True,
            "image_analysis_status": "missing",
        }

    if chart_path and _is_missing(normalized.get("chart_path")):
        normalized["chart_path"] = chart_path
    normalized.setdefault("advisory_only", True)
    normalized.setdefault("confidence", 0.0)
    normalized.setdefault("image_analysis_status", "reported")
    return normalized


def _merge_deterministic_outputs(result_payload: dict, task_outputs: List[Any]) -> dict:
    merged: Dict[str, Any] = {}
    task_results: Dict[str, Any] = {}

    for index, output in enumerate(task_outputs):
        parsed = _parse_output(output)
        task_key = TA_STEP_DEFINITIONS[index]["key"] if index < len(TA_STEP_DEFINITIONS) else f"step_{index + 1}"
        task_results[task_key] = parsed
        if not isinstance(parsed, dict):
            continue
        if "raw" in parsed and len(parsed) == 1:
            continue

        for key in DETERMINISTIC_RESULT_KEYS:
            value = parsed.get(key)
            if not _is_missing(value):
                merged[key] = value

    final_payload = {**merged, **result_payload}
    for key, value in merged.items():
        if _is_missing(final_payload.get(key)):
            final_payload[key] = value

    chart_path = final_payload.get("chart_path") if isinstance(final_payload.get("chart_path"), str) else None
    final_payload["visual_review"] = _normalize_visual_review(final_payload.get("visual_review"), chart_path=chart_path)
    final_payload.setdefault("_task_results", task_results)
    return final_payload


def _attach_artifact_urls(result_payload: dict, artifacts_dir: str, job_id: str) -> List[str]:
    def _collect_paths(obj: Any, parent: Any = None) -> List[Tuple[Any, str, str]]:
        found: List[Tuple[Any, str, str]] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and k.lower().endswith("path") and os.path.exists(v):
                    found.append((obj, k, v))
                else:
                    found.extend(_collect_paths(v, obj))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(_collect_paths(item, parent))
        return found

    copied_urls: List[str] = []
    seen_paths = set()
    for parent, key, path_val in _collect_paths(result_payload):
        try:
            normalized_path = os.path.abspath(path_val)
            if normalized_path in seen_paths:
                continue
            seen_paths.add(normalized_path)
            dest_name = os.path.basename(path_val)
            dest_path = os.path.join(artifacts_dir, dest_name)
            shutil.copy2(path_val, dest_path)
            url = f"/api/ta/artifacts/{job_id}/{dest_name}"
            parent_key_url = key.replace("path", "url")
            parent[parent_key_url] = url
            copied_urls.append(url)
        except Exception:
            continue

    if copied_urls:
        result_payload.setdefault("_artifact_urls", copied_urls)
        if isinstance(result_payload.get("visual_review"), dict) and result_payload.get("chart_url"):
            result_payload["visual_review"].setdefault("chart_url", result_payload["chart_url"])

    return copied_urls


def run_ta_job(job_id: str, company_name: str, ticker: str, sector: str, horizon: str = "medium-term"):
    """
    Run the TA crew and update job progress after each deterministic stage.
    """
    try:
        output_dir = os.path.join(os.path.dirname(__file__), "output_data")
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_ticker = (ticker or "company").replace("/", "_")
        output_path = os.path.join(output_dir, f"{safe_ticker}_ta_{ts}.json")

        # prepare logs and artifacts directories
        base_dir = os.path.dirname(__file__)
        artifacts_root = os.path.abspath(os.path.join(base_dir, "artifacts"))
        os.makedirs(artifacts_root, exist_ok=True)
        artifacts_dir = os.path.join(artifacts_root, job_id)
        os.makedirs(artifacts_dir, exist_ok=True)

        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, f"ta_{job_id}.log")

        ta = TAAnalysisCrew(ticker=ticker, horizon=horizon)
        crew = ta.crew()

        inputs = {
            "company_name": company_name,
            "ticker": ticker,
            "sector": sector,
            "horizon": horizon,
            "output_path": output_path,
        }

        crew._inputs = inputs
        crew._interpolate_inputs(inputs)
        crew._set_tasks_callbacks()

        for agent in crew.agents:
            agent.create_agent_executor()

        if crew.process == Process.hierarchical:
            crew._create_manager_agent()

        update_job(
            job_id,
            status="running",
            progress=0,
            output_path=output_path,
            current_step="Initializing",
            current_agent=None,
            step_message="Starting TA analysis",
            completed_steps=[],
            remaining_steps=TA_STEP_DEFINITIONS,
        )

        task_outputs: List[Any] = []

        # capture stdout/stderr to per-job log while still writing to the terminal
        class _Tee:
            def __init__(self, *streams):
                self.streams = streams

            def write(self, data: str) -> int:
                for s in self.streams:
                    try:
                        s.write(data)
                    except Exception:
                        pass
                return len(data)

            def flush(self):
                for s in self.streams:
                    try:
                        s.flush()
                    except Exception:
                        pass

        with open(log_path, "w", encoding="utf-8") as logf, contextlib.redirect_stdout(_Tee(sys.stdout, logf)), contextlib.redirect_stderr(_Tee(sys.stderr, logf)):
            for index, task in enumerate(crew.tasks):
                agent_to_use = crew._get_agent_to_use(task)
                if agent_to_use is None:
                    raise ValueError(f"No agent available for task: {task.description}")

                step_definition = TA_STEP_DEFINITIONS[index] if index < len(TA_STEP_DEFINITIONS) else {
                    "key": f"step_{index + 1}",
                    "label": _task_label(task, index),
                    "agent": getattr(agent_to_use, "role", "Unknown Agent"),
                }

                progress_state = build_step_progress(TA_STEP_DEFINITIONS, index)
                update_job(
                    job_id,
                    status="running",
                    output_path=output_path,
                    step_message=f"Running {step_definition['label']}",
                    **progress_state,
                )

                tools_for_task = task.tools or agent_to_use.tools or []
                tools_for_task = crew._prepare_tools(agent_to_use, task, tools_for_task)

                crew._log_task_start(task, agent_to_use.role)
                context = crew._get_context(task, task_outputs)
                task_output = task.execute_sync(
                    agent=agent_to_use,
                    context=context,
                    tools=tools_for_task,
                )
                task_outputs.append(task_output)
                crew._process_task_result(task, task_output)
                crew._store_execution_log(task, task_output, index, False)

                completed_state = build_step_progress(TA_STEP_DEFINITIONS, index + 1)
                update_job(
                    job_id,
                    status="running",
                    output_path=output_path,
                    step_message=f"Completed {step_definition['label']}",
                    **completed_state,
                )

        crew_output = crew._create_crew_output(task_outputs)
        result_payload = _parse_output(crew_output)
        result_payload = _merge_deterministic_outputs(result_payload, task_outputs)

        copied_urls = _attach_artifact_urls(result_payload, artifacts_dir, job_id)

        # produce deterministic explanations and takeaways
        try:
            gen = generate_explanations(result_payload)
            result_payload.update(gen)
        except Exception:
            # non-fatal: continue without explanations
            pass

        # write final structured result
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2, default=str)

        # update job with final state and metadata (log path, artifacts)
        update_job(
            job_id,
            status="done",
            progress=100,
            output_path=output_path,
            result_json=result_payload,
            current_step="Complete",
            current_agent=None,
            step_message="TA analysis complete",
            completed_steps=TA_STEP_DEFINITIONS,
            remaining_steps=[],
            metadata={"log_path": log_path, "artifacts": copied_urls},
        )
    except Exception as exc:
        # ensure failed status is persisted
        update_job(job_id, status="failed", progress=100, error=str(exc), step_message="TA analysis failed")
