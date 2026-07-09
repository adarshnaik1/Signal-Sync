from __future__ import annotations

from typing import Any, Dict, List


TA_STEP_DEFINITIONS: List[Dict[str, str]] = [
    {
        "key": "market_data_task",
        "label": "Market Data",
        "agent": "Market Data Validation Specialist",
    },
    {
        "key": "indicator_task",
        "label": "Indicators",
        "agent": "Technical Indicator Computation Specialist",
    },
    {
        "key": "pattern_detection_task",
        "label": "Pattern Detection",
        "agent": "Deterministic Pattern Detection Specialist",
    },
    {
        "key": "support_resistance_task",
        "label": "Support / Resistance",
        "agent": "Support and Resistance Structure Specialist",
    },
    {
        "key": "strategy_signal_task",
        "label": "Strategy Signal",
        "agent": "Technical Thesis and Signal Reasoning Specialist",
    },
    {
        "key": "explanation_task",
        "label": "Explanation",
        "agent": "Technical Analysis Explainer",
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