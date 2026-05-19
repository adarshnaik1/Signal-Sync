"""
Streamlit dashboard for financial news sentiment analysis.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from visualization.charts import (
    create_keyword_bar_chart,
    create_sentiment_gauge,
    create_sentiment_pie_chart,
    create_sentiment_timeline,
)


def _sentiment_badge_class(sentiment: str) -> str:
    mapping = {
        "Positive": "positive",
        "Negative": "negative",
        "Neutral": "neutral",
    }
    return mapping.get(sentiment, "neutral")


def render_dashboard(results: Dict[str, Any]) -> None:
    """
    Render the full news sentiment dashboard in Streamlit.

    Args:
        results: Pipeline output from run_news_sentiment_analysis.
    """
    if results.get("error"):
        st.error(results["error"])
        return

    company = results.get("company_name", "Company")
    symbol = results.get("symbol", "")
    summary = results.get("summary", {})
    articles = results.get("articles", [])
    keywords_data = results.get("keywords", {})
    news_summary = results.get("news_summary", {})
    raw_response = results.get("raw_response")

    st.markdown(f"# 📰 News Sentiment Analysis")
    st.markdown(f"### {company} (`{symbol}`)")

    _inject_styles()

    # --- Overall sentiment ---
    st.markdown("## 🎯 Overall Sentiment")
    col1, col2, col3, col4 = st.columns(4)

    overall = summary.get("overall_sentiment", "Neutral")
    avg_score = summary.get("average_sentiment", 0)
    dist = summary.get("sentiment_distribution", {})

    with col1:
        st.metric("Overall Sentiment", overall)
    with col2:
        st.metric("Sentiment Score", f"{avg_score:.4f}")
    with col3:
        st.metric("Positive %", f"{dist.get('positive_percentage', 0)}%")
    with col4:
        st.metric("Negative %", f"{dist.get('negative_percentage', 0)}%")

    st.plotly_chart(create_sentiment_gauge(avg_score), use_container_width=True)

    # --- News statistics ---
    st.markdown("## 📊 News Statistics")
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.metric("Total Articles", summary.get("total_articles", 0))
    with s2:
        st.metric("Average Sentiment", f"{avg_score:.4f}")
    with s3:
        pos_src = summary.get("most_positive_source") or {}
        st.metric(
            "Most Positive Source",
            pos_src.get("name", "N/A"),
            delta=f"{pos_src.get('average_score', 0):.3f}" if pos_src else None,
        )
    with s4:
        neg_src = summary.get("most_negative_source") or {}
        st.metric(
            "Most Negative Source",
            neg_src.get("name", "N/A"),
            delta=f"{neg_src.get('average_score', 0):.3f}" if neg_src else None,
        )

    # --- Charts ---
    st.markdown("## 📈 Visual Analytics")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.plotly_chart(
            create_sentiment_pie_chart(dist),
            use_container_width=True,
        )
    with chart_col2:
        st.plotly_chart(
            create_keyword_bar_chart(keywords_data.get("keyword_scores", {})),
            use_container_width=True,
        )

    st.plotly_chart(
        create_sentiment_timeline(summary.get("timeline", [])),
        use_container_width=True,
    )

    # --- Top headlines table ---
    st.markdown("## 📋 Top Headlines")
    if articles:
        table_df = pd.DataFrame(
            [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", ""),
                    "sentiment": a.get("sentiment", "Neutral"),
                    "published_at": a.get("published_at", ""),
                    "sentiment_score": a.get("sentiment_score", 0),
                    "url": a.get("url", ""),
                }
                for a in articles
            ]
        )
        st.dataframe(
            table_df[["title", "source", "sentiment", "published_at"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No articles available for the selected filters.")

    # --- Trending keywords ---
    st.markdown("## 🏷️ Trending Keywords")
    keywords = keywords_data.get("keywords", [])
    if keywords:
        st.write(", ".join(f"`{kw}`" for kw in keywords))
    else:
        st.write("No keywords extracted.")

    # --- News summary ---
    st.markdown("## 📝 News Summary")
    st.write(news_summary.get("overview", ""))

    snippets = news_summary.get("snippets", [])
    if snippets:
        st.markdown("**Key snippets:**")
        for snippet in snippets:
            st.markdown(f"- {snippet}")

    # --- Raw JSON (optional) ---
    with st.expander("🔍 Raw News JSON Viewer (optional)"):
        if raw_response:
            st.json(raw_response)
        else:
            st.json(results)

    st.caption(
        f"Analysis generated at {summary.get('analysis_timestamp', 'N/A')} | "
        f"Data source: Marketaux API"
    )


def render_input_form() -> Optional[Dict[str, Any]]:
    """
    Render sidebar / main input form for user parameters.

    Returns:
        Dict of user inputs if submitted, else None.
    """
    st.sidebar.header("🔎 Analysis Parameters")

    company_name = st.sidebar.text_input(
        "Company Name",
        value="Reliance Industries",
        help="Display name for the company",
    )
    stock_symbol = st.sidebar.text_input(
        "Stock Symbol",
        value="RELIANCE.NS",
        help="Marketaux symbol, e.g. RELIANCE.NS, TCS.NS",
    )
    articles_limit = st.sidebar.slider(
        "Number of Articles",
        min_value=5,
        max_value=100,
        value=50,
        step=5,
    )
    days = st.sidebar.slider(
        "Number of Days",
        min_value=1,
        max_value=30,
        value=7,
    )

    submitted = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

    if submitted:
        if not company_name.strip() or not stock_symbol.strip():
            st.sidebar.error("Company name and stock symbol are required.")
            return None
        return {
            "company_name": company_name.strip(),
            "stock_symbol": stock_symbol.strip().upper(),
            "articles_limit": articles_limit,
            "days": days,
        }
    return None


def _inject_styles() -> None:
    """Inject minimal custom CSS for sentiment badges."""
    st.markdown(
        """
        <style>
        .stMetric label { font-size: 0.85rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run_streamlit_app(run_pipeline_fn) -> None:
    """
    Entry point for Streamlit app with input form and dashboard.

    Args:
        run_pipeline_fn: Callable that accepts user params and returns results.
    """
    st.set_page_config(
        page_title="News Sentiment Analysis",
        page_icon="📰",
        layout="wide",
    )

    params = render_input_form()

    if params is None:
        st.markdown(
            """
            ### Welcome to News Sentiment Analysis

            Enter a company name and NSE stock symbol in the sidebar, then click
            **Run Analysis** to fetch financial news from Marketaux and visualize sentiment.

            **Example**
            - Company: Reliance Industries
            - Symbol: RELIANCE.NS
            - Articles: 50
            - Days: 7
            """
        )
        return

    with st.spinner("Fetching and analyzing news articles..."):
        try:
            results = run_pipeline_fn(**params)
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            return

    render_dashboard(results)
