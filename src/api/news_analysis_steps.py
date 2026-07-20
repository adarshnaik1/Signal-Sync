from __future__ import annotations

from typing import Any, Dict, List


NEWS_STEP_DEFINITIONS: List[Dict[str, str]] = [
    {
        "key": "news_sentiment_analysis_task",
        "label": "News Sentiment Analysis",
        "agent": "News Sentiment Analyzer",
    }
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
