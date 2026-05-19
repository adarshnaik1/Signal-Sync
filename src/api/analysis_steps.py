from __future__ import annotations

from typing import Any, Dict, List


BGV_STEP_DEFINITIONS: List[Dict[str, str]] = [
    {
        "key": "company_overview_task",
        "label": "Company Overview",
        "agent": "Corporate Intelligence Analyst",
    },
    {
        "key": "management_research_task",
        "label": "Management Research",
        "agent": "Executive Background Verification Specialist",
    },
    {
        "key": "financial_irregularities_task",
        "label": "Financial Irregularities",
        "agent": "Forensic Financial Analyst",
    },
    {
        "key": "scam_detection_task",
        "label": "Scam Detection",
        "agent": "Market Manipulation Detection Specialist",
    },
    {
        "key": "compile_bgv_report_task",
        "label": "Final Report",
        "agent": "BGV Report Compiler",
    },
]


def build_step_progress(step_definitions: List[Dict[str, str]], completed_count: int) -> Dict[str, Any]:
    total = len(step_definitions)
    completed = step_definitions[:completed_count]
    remaining = step_definitions[completed_count:]
    current = remaining[0] if remaining else None
    progress = 0 if total == 0 else int(round((completed_count / total) * 100))
    return {
        "progress": progress,
        "current_step": current["label"] if current else None,
        "current_agent": current["agent"] if current else None,
        "completed_steps": completed,
        "remaining_steps": remaining,
    }
