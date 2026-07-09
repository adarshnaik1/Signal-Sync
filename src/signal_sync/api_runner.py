import os
from datetime import datetime
from typing import Any, List

from crewai import Process

from api.analysis_steps import BGV_STEP_DEFINITIONS, build_step_progress
from api.jobs_store import update_job
from signal_sync.crew import BGVCrew


def _task_label(task: Any, index: int) -> str:
    return getattr(task, "name", None) or f"Step {index + 1}"


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

        bgv = BGVCrew(
            company_name=company_name,
            ticker=ticker,
            sector=sector,
            annual_report_path=annual_report_path or ""
        )
        bgv.output_path = output_path

        crew = bgv.crew()
        inputs = {
            "company_name": company_name,
            "ticker": ticker,
            "sector": sector,
            "annual_report_path": annual_report_path or "",
            "output_path": output_path,
            "pdf_context": bgv.pdf_context if hasattr(bgv, "pdf_context") and bgv.pdf_context else "No annual report provided",
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
            step_message="Starting BGV analysis",
            completed_steps=[],
            remaining_steps=BGV_STEP_DEFINITIONS,
        )

        task_outputs: List[Any] = []

        for index, task in enumerate(crew.tasks):
            agent_to_use = crew._get_agent_to_use(task)
            if agent_to_use is None:
                raise ValueError(f"No agent available for task: {task.description}")

            step_definition = BGV_STEP_DEFINITIONS[index] if index < len(BGV_STEP_DEFINITIONS) else {
                "key": f"step_{index + 1}",
                "label": _task_label(task, index),
                "agent": getattr(agent_to_use, "role", "Unknown Agent"),
            }

            progress_state = build_step_progress(BGV_STEP_DEFINITIONS, index)
            update_job(
                job_id,
                status="running",
                output_path=output_path,
                step_message=f"Running {step_definition['label']}",
                **progress_state,
            )

            tools_for_task = task.tools or agent_to_use.tools or []
            tools_for_task = crew._prepare_tools(
                agent_to_use,
                task,
                tools_for_task,
            )

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

            completed_state = build_step_progress(BGV_STEP_DEFINITIONS, index + 1)
            update_job(
                job_id,
                status="running",
                output_path=output_path,
                step_message=f"Completed {step_definition['label']}",
                **completed_state,
            )

        crew_output = crew._create_crew_output(task_outputs)
        bgv._save_structured_output(crew_output)

        update_job(
            job_id,
            status="done",
            progress=100,
            output_path=output_path,
            current_step="Complete",
            current_agent=None,
            step_message="BGV analysis complete",
            completed_steps=BGV_STEP_DEFINITIONS,
            remaining_steps=[],
        )
    except Exception as e:
        update_job(job_id, status="failed", progress=100, error=str(e), step_message="BGV analysis failed")
