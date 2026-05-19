"""
Plotly chart builders for news sentiment dashboard.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


SENTIMENT_COLORS = {
    "Positive": "#22c55e",
    "Neutral": "#94a3b8",
    "Negative": "#ef4444",
}


def create_sentiment_pie_chart(distribution: Dict) -> go.Figure:
    """
    Pie chart for positive / neutral / negative distribution.

    Args:
        distribution: Dict with positive, negative, neutral counts.

    Returns:
        Plotly Figure.
    """
    labels = ["Positive", "Neutral", "Negative"]
    values = [
        distribution.get("positive", 0),
        distribution.get("neutral", 0),
        distribution.get("negative", 0),
    ]
    colors = [SENTIMENT_COLORS[l] for l in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=colors),
                textinfo="label+percent",
            )
        ]
    )
    fig.update_layout(
        title="Sentiment Distribution",
        template="plotly_dark",
        height=400,
        showlegend=True,
    )
    return fig


def create_sentiment_timeline(timeline: List[Dict]) -> go.Figure:
    """
    Line chart of average daily sentiment over time.

    Args:
        timeline: List of {date, sentiment_score} records.

    Returns:
        Plotly Figure.
    """
    if not timeline:
        fig = go.Figure()
        fig.update_layout(
            title="Sentiment Timeline (no dated articles)",
            template="plotly_dark",
            height=400,
        )
        return fig

    df = pd.DataFrame(timeline)
    fig = px.line(
        df,
        x="date",
        y="sentiment_score",
        markers=True,
        title="Sentiment Timeline (Daily Average)",
        labels={"date": "Date", "sentiment_score": "Avg Sentiment Score"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#64748b", opacity=0.6)
    fig.add_hline(y=0.1, line_dash="dot", line_color="#22c55e", opacity=0.4)
    fig.add_hline(y=-0.1, line_dash="dot", line_color="#ef4444", opacity=0.4)
    fig.update_layout(template="plotly_dark", height=400)
    return fig


def create_keyword_bar_chart(keyword_scores: Dict[str, float], top_n: int = 12) -> go.Figure:
    """
    Horizontal bar chart of top TF-IDF keywords.

    Args:
        keyword_scores: Mapping of keyword to TF-IDF score.
        top_n: Maximum keywords to display.

    Returns:
        Plotly Figure.
    """
    if not keyword_scores:
        fig = go.Figure()
        fig.update_layout(
            title="Trending Keywords (no data)",
            template="plotly_dark",
            height=400,
        )
        return fig

    items = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    terms = [k for k, _ in reversed(items)]
    scores = [v for _, v in reversed(items)]

    fig = go.Figure(
        data=[
            go.Bar(
                x=scores,
                y=terms,
                orientation="h",
                marker_color="#6366f1",
            )
        ]
    )
    fig.update_layout(
        title="Trending Keywords (TF-IDF)",
        template="plotly_dark",
        height=max(350, 28 * len(terms)),
        xaxis_title="TF-IDF Score",
        yaxis_title="Keyword",
    )
    return fig


def create_sentiment_gauge(score: float, title: str = "Overall Sentiment Score") -> go.Figure:
    """Gauge chart for overall sentiment score (-1 to +1)."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": title},
            gauge={
                "axis": {"range": [-1, 1]},
                "bar": {"color": "#6366f1"},
                "steps": [
                    {"range": [-1, -0.1], "color": "#7f1d1d"},
                    {"range": [-0.1, 0.1], "color": "#334155"},
                    {"range": [0.1, 1], "color": "#14532d"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(template="plotly_dark", height=320)
    return fig
