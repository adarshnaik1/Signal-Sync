# streamlit_app/app.py
"""
BGV Verification Streamlit Frontend
Provides a user interface for triggering the BGV verification pipeline.
"""

import streamlit as st
import json
import os
import sys
import glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add the src directory to the path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

# Load environment variables from .env file
load_dotenv(ROOT_DIR / ".env")

# Import PDF extraction helpers directly (avoiding signal_sync package init which loads crewai)
PDF_EXTRACTION_AVAILABLE = False
extract_text_sections_impl = None
get_full_text = None
extract_tables_impl = None
extract_financial_tables = None

try:
    # Add helpers directory directly to path to avoid triggering crewai imports
    helpers_dir = ROOT_DIR / "src" / "signal_sync" / "helpers"
    if str(helpers_dir) not in sys.path:
        sys.path.insert(0, str(helpers_dir))
    from text_extractor import extract_text_sections_impl, get_full_text
    from table_extractor import extract_tables_impl, extract_financial_tables
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    pass  # Will use fallback or show message in UI

# Page configuration
st.set_page_config(
    page_title="Signal Sync - BGV & News Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #60a5fa;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white !important;
        text-align: center;
        margin: 10px;
    }
    .score-card h1, .score-card h3, .score-card p {
        color: white !important;
    }
    .risk-high { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .risk-moderate { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .risk-low { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .finding-item {
        background-color: #1e293b;
        border-left: 4px solid #667eea;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 5px 5px 0;
        color: #e2e8f0 !important;
    }
    .red-flag {
        border-left-color: #f5576c;
        background-color: #2d1f2f;
    }
    .sentiment-positive {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    .sentiment-negative {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
    }
    .sentiment-neutral {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .metric-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #334155;
    }
    .post-card {
        background: #1e293b;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    .post-card-positive {
        border-left-color: #43e97b;
    }
    .post-card-negative {
        border-left-color: #f5576c;
    }
    .subreddit-tag {
        background: #334155;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/search--v1.png", width=80)
    st.title("Signal Sync")
    st.markdown("### Analysis Dashboard")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigate to:",
        ["🔍 BGV Verification", "📊 Reddit News Analysis"],
        index=0
    )
    
    st.markdown("---")
    if page == "🔍 BGV Verification":
        st.markdown("""
        **Background Verification Checks:**
        - 🏢 Company Overview
        - 👥 Management Research
        - 📊 Financial Irregularities
        - ⚠️ Scam Detection
        """)
    else:
        st.markdown("""
        **News Analysis Features:**
        - 📈 Overall Sentiment Score
        - 📊 Sentiment Distribution
        - 🏷️ Subreddit Breakdown
        - 🔥 Trending Posts
        - 📝 Detailed Post Analysis
        """)
    st.markdown("---")
    st.info("Ensure you have set your API keys in the environment variables.")


# ============================================================================
# HELPER FUNCTIONS FOR REDDIT NEWS ANALYSIS
# ============================================================================

def get_sentiment_color(sentiment: str) -> str:
    """Return color based on sentiment label."""
    colors = {
        "Positive": "#43e97b",
        "Negative": "#f5576c",
        "Neutral": "#667eea"
    }
    return colors.get(sentiment, "#667eea")


def get_sentiment_emoji(sentiment: str) -> str:
    """Return emoji based on sentiment label."""
    emojis = {
        "Positive": "😊",
        "Negative": "😟",
        "Neutral": "😐"
    }
    return emojis.get(sentiment, "📊")


def load_sentiment_files():
    """Load all available sentiment analysis files."""
    output_dir = ROOT_DIR / "src" / "reddit_sentiment" / "output"
    if not output_dir.exists():
        # Fallback: try to find output relative to the current file
        output_dir = Path(__file__).resolve().parent.parent / "src" / "reddit_sentiment" / "output"
    if not output_dir.exists():
        return []
    files = list(output_dir.glob("*_sentiment_results_*.json"))
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)


def extract_company_name(filename: str) -> str:
    """Extract company name from filename."""
    # Format: company_sentiment_results_YYYYMMDD_HHMMSS.json
    parts = filename.replace("_sentiment_results_", "|").split("|")
    if parts:
        return parts[0].replace("_", " ").title()
    return "Unknown"


def create_sentiment_gauge(score: float, title: str) -> go.Figure:
    """Create a gauge chart for sentiment score."""
    # Normalize score from [-1, 1] to [0, 100]
    normalized = (score + 1) * 50
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=normalized,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': 'white'}},
        number={'suffix': '%', 'font': {'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'white'},
            'bar': {'color': '#667eea'},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 2,
            'bordercolor': '#334155',
            'steps': [
                {'range': [0, 33], 'color': '#f5576c'},
                {'range': [33, 66], 'color': '#fee140'},
                {'range': [66, 100], 'color': '#43e97b'}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 4},
                'thickness': 0.75,
                'value': normalized
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


# ============================================================================
# PAGE: REDDIT NEWS ANALYSIS
# ============================================================================

def render_reddit_sentiment_page():
    """Render the Reddit News Analysis page."""
    st.markdown('<h1 class="main-header">📊 Reddit News Analysis</h1>', unsafe_allow_html=True)
    
    # Load available sentiment files
    sentiment_files = load_sentiment_files()
    
    if not sentiment_files:
        st.warning("⚠️ No news analysis results found. Run the Reddit news analyzer first.")
        st.info("To analyze a company, run: `python -m src.reddit_sentiment.main --company 'Company Name'`")
        return
    
    # Create selection options
    file_options = {}
    for f in sentiment_files:
        company = extract_company_name(f.stem)
        timestamp = f.stem.split("_")[-2] + "_" + f.stem.split("_")[-1]
        try:
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            display_name = f"{company} - {dt.strftime('%b %d, %Y %H:%M')}"
        except:
            display_name = f"{company} - {timestamp}"
        file_options[display_name] = f
    
    # Company selection
    st.markdown("### 🏢 Select Company Analysis")
    selected_display = st.selectbox(
        "Choose a news analysis report:",
        options=list(file_options.keys()),
        help="Select from previously analyzed companies"
    )
    
    if selected_display:
        selected_file = file_options[selected_display]
        
        # Load the data
        with open(selected_file, encoding="utf-8") as f:
            data = json.load(f)
        
        company_name = data.get("company", "Unknown")
        summary = data.get("summary", {})
        extreme_posts = data.get("extreme_posts", {})
        posts = data.get("posts", [])
        
        # ================================================================
        # SECTION 1: OVERALL SENTIMENT OVERVIEW
        # ================================================================
        st.markdown("---")
        st.markdown(f"## 🎯 Sentiment Overview for **{company_name}**")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        overall_sentiment = summary.get("overall_sentiment", "Unknown")
        sentiment_color = get_sentiment_color(overall_sentiment)
        sentiment_emoji = get_sentiment_emoji(overall_sentiment)
        
        with col1:
            st.markdown(f"""
            <div class="score-card sentiment-{overall_sentiment.lower()}">
                <h3>Overall Sentiment</h3>
                <h1>{sentiment_emoji} {overall_sentiment}</h1>
                <p>Based on {summary.get('total_posts_analyzed', 0)} posts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_score = summary.get("average_sentiment_score", 0)
            score_class = "sentiment-positive" if avg_score > 0.1 else ("sentiment-negative" if avg_score < -0.1 else "sentiment-neutral")
            st.markdown(f"""
            <div class="score-card {score_class}">
                <h3>Avg. Sentiment Score</h3>
                <h1>{avg_score:.3f}</h1>
                <p>Range: -1.0 to +1.0</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            dist = summary.get("sentiment_distribution", {})
            positive_pct = dist.get("positive_percentage", 0)
            st.markdown(f"""
            <div class="score-card sentiment-positive">
                <h3>Positive Posts</h3>
                <h1>{positive_pct:.1f}%</h1>
                <p>{dist.get('positive', 0)} posts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            negative_pct = dist.get("negative_percentage", 0)
            st.markdown(f"""
            <div class="score-card sentiment-negative">
                <h3>Negative Posts</h3>
                <h1>{negative_pct:.1f}%</h1>
                <p>{dist.get('negative', 0)} posts</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ================================================================
        # SECTION 2: SENTIMENT DISTRIBUTION CHARTS
        # ================================================================
        st.markdown("---")
        st.markdown("## 📈 Sentiment Distribution Analysis")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Pie chart for sentiment distribution
            dist = summary.get("sentiment_distribution", {})
            fig_pie = px.pie(
                names=["Positive", "Negative", "Neutral"],
                values=[dist.get("positive", 0), dist.get("negative", 0), dist.get("neutral", 0)],
                color_discrete_sequence=["#43e97b", "#f5576c", "#667eea"],
                title="Sentiment Distribution"
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': 'white'},
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with chart_col2:
            # Gauge chart for sentiment score
            fig_gauge = create_sentiment_gauge(
                summary.get("average_sentiment_score", 0),
                "Sentiment Score Index"
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # ================================================================
        # SECTION 3: SUBREDDIT BREAKDOWN
        # ================================================================
        st.markdown("---")
        st.markdown("## 🏷️ Subreddit Analysis")
        
        subreddit_breakdown = summary.get("subreddit_breakdown", {})
        subreddit_sentiments = summary.get("subreddit_sentiments", {})
        
        if subreddit_breakdown:
            sub_col1, sub_col2 = st.columns(2)
            
            with sub_col1:
                # Bar chart for post distribution by subreddit
                fig_bar = px.bar(
                    x=list(subreddit_breakdown.keys()),
                    y=list(subreddit_breakdown.values()),
                    title="Posts per Subreddit",
                    labels={'x': 'Subreddit', 'y': 'Number of Posts'},
                    color_discrete_sequence=['#667eea']
                )
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': 'white'},
                    xaxis={'tickangle': 45}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with sub_col2:
                # Stacked bar for sentiment by subreddit
                subreddit_data = []
                for sub, sentiments in subreddit_sentiments.items():
                    subreddit_data.append({
                        'Subreddit': sub,
                        'Positive': sentiments.get('positive', 0),
                        'Negative': sentiments.get('negative', 0),
                        'Neutral': sentiments.get('neutral', 0)
                    })
                
                if subreddit_data:
                    df_sub = pd.DataFrame(subreddit_data)
                    fig_stacked = px.bar(
                        df_sub,
                        x='Subreddit',
                        y=['Positive', 'Negative', 'Neutral'],
                        title="Sentiment by Subreddit",
                        color_discrete_sequence=['#43e97b', '#f5576c', '#667eea'],
                        barmode='stack'
                    )
                    fig_stacked.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font={'color': 'white'},
                        xaxis={'tickangle': 45},
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                    )
                    st.plotly_chart(fig_stacked, use_container_width=True)
        
        # ================================================================
        # SECTION 4: EXTREME POSTS (MOST POSITIVE & NEGATIVE)
        # ================================================================
        st.markdown("---")
        st.markdown("## 🔥 Notable Posts")
        
        extreme_tabs = st.tabs(["🟢 Most Positive", "🔴 Most Negative"])
        
        with extreme_tabs[0]:
            most_positive = extreme_posts.get("most_positive", [])
            if most_positive:
                for i, post in enumerate(most_positive, 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="post-card post-card-positive">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span class="subreddit-tag">r/{post.get('subreddit', 'unknown')}</span>
                                <span style="color: #43e97b; font-weight: bold;">Score: {post.get('sentiment_score', 0):.4f}</span>
                            </div>
                            <h4 style="margin: 10px 0; color: #e2e8f0;">{post.get('title', 'No title')[:100]}...</h4>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                <span style="color: #94a3b8;">⬆️ {post.get('score', 0)} upvotes</span>
                                <a href="{post.get('url', '#')}" target="_blank" style="color: #60a5fa;">View on Reddit →</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No positive posts found.")
        
        with extreme_tabs[1]:
            most_negative = extreme_posts.get("most_negative", [])
            if most_negative:
                for i, post in enumerate(most_negative, 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="post-card post-card-negative">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span class="subreddit-tag">r/{post.get('subreddit', 'unknown')}</span>
                                <span style="color: #f5576c; font-weight: bold;">Score: {post.get('sentiment_score', 0):.4f}</span>
                            </div>
                            <h4 style="margin: 10px 0; color: #e2e8f0;">{post.get('title', 'No title')[:100]}...</h4>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                <span style="color: #94a3b8;">⬆️ {post.get('score', 0)} upvotes</span>
                                <a href="{post.get('url', '#')}" target="_blank" style="color: #60a5fa;">View on Reddit →</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No negative posts found.")
        
        # ================================================================
        # SECTION 5: DETAILED POST ANALYSIS TABLE
        # ================================================================
        st.markdown("---")
        st.markdown("## 📝 Detailed Post Analysis")
        
        if posts:
            # Create dataframe for posts
            df_posts = pd.DataFrame([{
                'Title': p.get('title', '')[:60] + '...' if len(p.get('title', '')) > 60 else p.get('title', ''),
                'Subreddit': p.get('subreddit', ''),
                'Sentiment': p.get('sentiment_label', ''),
                'Score': round(p.get('sentiment_score', 0), 4),
                'Upvotes': p.get('score', 0),
                'Comments': p.get('num_comments', 0),
                'URL': p.get('url', '')
            } for p in posts])
            
            # Filters
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                sentiment_filter = st.multiselect(
                    "Filter by Sentiment:",
                    options=["Positive", "Negative", "Neutral"],
                    default=["Positive", "Negative", "Neutral"]
                )
            
            with filter_col2:
                subreddit_filter = st.multiselect(
                    "Filter by Subreddit:",
                    options=list(df_posts['Subreddit'].unique()),
                    default=list(df_posts['Subreddit'].unique())
                )
            
            # Apply filters
            filtered_df = df_posts[
                (df_posts['Sentiment'].isin(sentiment_filter)) &
                (df_posts['Subreddit'].isin(subreddit_filter))
            ]
            
            # Display metrics for filtered data
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Posts Shown", len(filtered_df))
            with metric_col2:
                st.metric("Avg. Sentiment Score", f"{filtered_df['Score'].mean():.3f}" if len(filtered_df) > 0 else "N/A")
            with metric_col3:
                st.metric("Total Engagement", f"{filtered_df['Upvotes'].sum() + filtered_df['Comments'].sum():,}")
            
            # Display table
            st.dataframe(
                filtered_df,
                column_config={
                    "URL": st.column_config.LinkColumn("Link", display_text="View"),
                    "Score": st.column_config.NumberColumn("Sentiment", format="%.4f"),
                    "Upvotes": st.column_config.NumberColumn("⬆️ Upvotes"),
                    "Comments": st.column_config.NumberColumn("💬 Comments"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Download option
            st.download_button(
                label="📥 Download Full Analysis (JSON)",
                data=json.dumps(data, indent=2),
                file_name=f"sentiment_analysis_{company_name.lower().replace(' ', '_')}.json",
                mime="application/json"
            )
        
        # ================================================================
        # SECTION 6: KEY INSIGHTS SUMMARY
        # ================================================================
        st.markdown("---")
        st.markdown("## 💡 Key Insights")
        
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.markdown("### 📊 Statistical Summary")
            
            # Calculate additional stats
            if posts:
                sentiment_scores = [p.get('sentiment_score', 0) for p in posts]
                upvotes = [p.get('score', 0) for p in posts]
                
                st.markdown(f"""
                - **Total Posts Analyzed:** {len(posts)}
                - **Date Range:** {data.get('generated_at', 'Unknown')[:10]}
                - **Highest Sentiment Score:** {max(sentiment_scores):.4f}
                - **Lowest Sentiment Score:** {min(sentiment_scores):.4f}
                - **Most Upvoted Post:** {max(upvotes):,} upvotes
                - **Total Community Engagement:** {sum(upvotes):,} upvotes
                """)
        
        with insights_col2:
            st.markdown("### 🎯 Sentiment Verdict")
            
            avg_score = summary.get("average_sentiment_score", 0)
            positive_pct = summary.get("sentiment_distribution", {}).get("positive_percentage", 0)
            
            if avg_score > 0.3 and positive_pct > 60:
                st.success(f"""
                **Strong Positive Sentiment** 🚀
                
                The Reddit community shows overwhelmingly positive sentiment toward {company_name}. 
                With {positive_pct:.1f}% positive posts and an average score of {avg_score:.3f}, 
                the public perception appears favorable.
                """)
            elif avg_score > 0 and positive_pct > 40:
                st.info(f"""
                **Moderately Positive Sentiment** 📈
                
                {company_name} receives generally positive feedback on Reddit.
                The community sentiment is cautiously optimistic with {positive_pct:.1f}% positive posts.
                """)
            elif avg_score < -0.2:
                st.error(f"""
                **Negative Sentiment Alert** ⚠️
                
                The Reddit community shows concerning negative sentiment toward {company_name}.
                With an average score of {avg_score:.3f}, there may be underlying issues worth investigating.
                """)
            else:
                st.warning(f"""
                **Mixed/Neutral Sentiment** 😐
                
                Sentiment toward {company_name} is mixed or neutral.
                Consider analyzing individual posts for more context.
                       """)


# ============================================================================
# PDF EXTRACTION PREVIEW FUNCTIONS
# ============================================================================

def render_pdf_extraction_preview(pdf_path: str, pdf_name: str):
    """Render a preview of extracted PDF content with tables and text."""
    st.markdown("### 📄 PDF Extraction Preview")
    
    with st.expander("🔍 View Extracted Content", expanded=False):
        try:
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Financial Tables", "📝 Text Content", "📈 Document Stats"])
            
            with tab1:
                render_extracted_tables(pdf_path, pdf_name)
            
            with tab2:
                render_extracted_text(pdf_path, pdf_name)
            
            with tab3:
                render_document_stats(pdf_path, pdf_name)
                
        except Exception as e:
            st.error(f"Error extracting PDF content: {str(e)}")


def render_extracted_tables(pdf_path: str, pdf_name: str):
    """Render extracted tables from the PDF."""
    st.markdown("#### Extracted Tables")
    
    try:
        # Extract all tables
        all_tables = extract_tables_impl(pdf_path, pdf_name)
        
        if not all_tables:
            st.info("No tables found in the document.")
            return
        
        st.success(f"Found **{len(all_tables)}** tables in the document")
        
        # Filter for financial tables
        financial_tables = extract_financial_tables(pdf_path)
        
        if financial_tables:
            st.markdown("##### 💰 Financial Tables")
            st.caption(f"Found {len(financial_tables)} tables with financial data")
            
            for i, table in enumerate(financial_tables[:5]):  # Limit to first 5
                with st.expander(f"📊 {table.get('table_id', f'Table {i+1}')} (Page {table.get('page_no', '?')})", expanded=(i == 0)):
                    headers = table.get('headers', [])
                    rows = table.get('rows', [])
                    
                    if headers and rows:
                        # Clean headers - replace None with empty string
                        clean_headers = [str(h) if h else f"Column {j+1}" for j, h in enumerate(headers)]
                        
                        # Clean rows
                        clean_rows = []
                        for row in rows:
                            clean_row = [str(cell) if cell else "" for cell in row]
                            # Pad row if needed
                            while len(clean_row) < len(clean_headers):
                                clean_row.append("")
                            clean_rows.append(clean_row[:len(clean_headers)])
                        
                        # Create DataFrame and display
                        df = pd.DataFrame(clean_rows, columns=clean_headers)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("Table has incomplete data")
        
        # Show other tables
        st.markdown("##### 📋 All Tables")
        table_select = st.selectbox(
            "Select a table to view:",
            options=range(len(all_tables)),
            format_func=lambda x: f"{all_tables[x].get('table_id', f'Table {x+1}')} (Page {all_tables[x].get('page_no', '?')})"
        )
        
        if table_select is not None:
            selected_table = all_tables[table_select]
            headers = selected_table.get('headers', [])
            rows = selected_table.get('rows', [])
            
            if headers and rows:
                clean_headers = [str(h) if h else f"Column {j+1}" for j, h in enumerate(headers)]
                clean_rows = []
                for row in rows:
                    clean_row = [str(cell) if cell else "" for cell in row]
                    while len(clean_row) < len(clean_headers):
                        clean_row.append("")
                    clean_rows.append(clean_row[:len(clean_headers)])
                
                df = pd.DataFrame(clean_rows, columns=clean_headers)
                st.dataframe(df, use_container_width=True)
                
                # Download button for the table
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{selected_table.get('table_id', 'table')}.csv",
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"Error extracting tables: {str(e)}")


def render_extracted_text(pdf_path: str, pdf_name: str):
    """Render extracted text from the PDF."""
    st.markdown("#### Extracted Text")
    
    try:
        text_sections = extract_text_sections_impl(pdf_path, pdf_name)
        
        if not text_sections:
            st.info("No text content found.")
            return
        
        total_pages = len(text_sections)
        st.success(f"Extracted text from **{total_pages}** pages")
        
        # Page selector
        col1, col2 = st.columns([1, 3])
        with col1:
            page_num = st.number_input(
                "Select Page:",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )
        
        with col2:
            # Show page text
            page_data = text_sections[page_num - 1]
            char_count = page_data.get('char_count', 0)
            st.caption(f"Page {page_num} • {char_count:,} characters")
        
        # Display page text in a scrollable container
        page_text = page_data.get('text', 'No text found on this page.')
        st.text_area(
            "Page Content:",
            value=page_text,
            height=400,
            disabled=True
        )
        
        # Full text search
        st.markdown("##### 🔍 Search in Document")
        search_term = st.text_input("Enter search term:", placeholder="e.g., revenue, profit, risk")
        
        if search_term:
            search_results = []
            for section in text_sections:
                text = section.get('text', '')
                if search_term.lower() in text.lower():
                    page_no = section.get('page_no', 0)
                    # Find position and extract context
                    pos = text.lower().find(search_term.lower())
                    start = max(0, pos - 100)
                    end = min(len(text), pos + len(search_term) + 100)
                    context = text[start:end]
                    search_results.append({
                        'page': page_no,
                        'context': f"...{context}..."
                    })
            
            if search_results:
                st.success(f"Found **{len(search_results)}** matches")
                for result in search_results[:10]:  # Limit display
                    st.markdown(f"""
                    <div class="finding-item">
                        <strong>Page {result['page']}:</strong> {result['context'].replace(search_term, f'<mark>{search_term}</mark>')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(f"No matches found for '{search_term}'")
        
        # Download full text
        full_text = get_full_text(pdf_path)
        st.download_button(
            label="📥 Download Full Text",
            data=full_text,
            file_name=f"{pdf_name.replace('.pdf', '')}_text.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")


def render_document_stats(pdf_path: str, pdf_name: str):
    """Render document statistics."""
    st.markdown("#### Document Statistics")
    
    try:
        text_sections = extract_text_sections_impl(pdf_path, pdf_name)
        all_tables = extract_tables_impl(pdf_path, pdf_name)
        financial_tables = extract_financial_tables(pdf_path)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Pages", len(text_sections))
        
        with col2:
            total_chars = sum(s.get('char_count', 0) for s in text_sections)
            st.metric("Total Characters", f"{total_chars:,}")
        
        with col3:
            st.metric("Tables Found", len(all_tables))
        
        with col4:
            st.metric("Financial Tables", len(financial_tables))
        
        st.markdown("---")
        
        # Character distribution per page
        st.markdown("##### 📊 Content Distribution by Page")
        
        page_data = [
            {"Page": s.get('page_no', i+1), "Characters": s.get('char_count', 0)}
            for i, s in enumerate(text_sections)
        ]
        df = pd.DataFrame(page_data)
        
        fig = px.bar(
            df,
            x='Page',
            y='Characters',
            title='Characters per Page',
            color='Characters',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Table distribution
        if all_tables:
            st.markdown("##### 📋 Table Distribution by Page")
            table_pages = {}
            for t in all_tables:
                page = t.get('page_no', 0)
                table_pages[page] = table_pages.get(page, 0) + 1
            
            table_df = pd.DataFrame([
                {"Page": k, "Tables": v} for k, v in sorted(table_pages.items())
            ])
            
            fig2 = px.bar(
                table_df,
                x='Page',
                y='Tables',
                title='Tables per Page',
                color='Tables',
                color_continuous_scale='Greens'
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error calculating statistics: {str(e)}")


# ============================================================================
# PAGE: BGV VERIFICATION (Original functionality)
# ============================================================================

def render_bgv_page():
    """Render the BGV Verification page."""
    st.markdown('<h1 class="main-header">🔍 BGV Verification Portal</h1>', unsafe_allow_html=True)

    # Input form
    st.markdown("### Enter Company Details")

    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input(
            "Company Name *",
            placeholder="e.g., Infosys Limited",
            help="Enter the full legal name of the company"
        )
        
        sector = st.selectbox(
            "Sector *",
            options=[
                "Technology",
                "Finance & Banking",
                "Healthcare",
                "Consumer Goods",
                "Energy",
                "Manufacturing",
                "Real Estate",
                "Telecommunications",
                "Retail",
                "Other"
            ],
            help="Select the primary business sector"
        )

    with col2:
        ticker = st.text_input(
            "Stock Ticker *",
            placeholder="e.g., INFY.NS, AAPL, RELIANCE.NS",
            help="Enter the stock ticker symbol (include exchange suffix if applicable)"
        )
        
        # Custom sector input if "Other" is selected
        if sector == "Other":
            sector = st.text_input(
                "Specify Sector",
                placeholder="Enter the sector"
            )

    # File uploader for annual report
    st.markdown("### Upload Annual Report")
    annual_pdf = st.file_uploader(
        "Annual Report PDF (Optional but recommended)",
        type=["pdf"],
        help="Upload the company's annual report for financial analysis"
    )

    # Display uploaded file info and extraction preview
    if annual_pdf:
        st.success(f"✅ Uploaded: {annual_pdf.name} ({annual_pdf.size / 1024:.1f} KB)")
        
        # Save temporarily for extraction preview
        temp_uploads_dir = ROOT_DIR / "uploads"
        temp_uploads_dir.mkdir(parents=True, exist_ok=True)
        temp_pdf_path = str(temp_uploads_dir / f"temp_{annual_pdf.name}")
        
        with open(temp_pdf_path, "wb") as f:
            f.write(annual_pdf.getbuffer())
        
        # Show PDF extraction preview
        if PDF_EXTRACTION_AVAILABLE:
            render_pdf_extraction_preview(temp_pdf_path, annual_pdf.name)
        else:
            st.info("📄 PDF preview will be available after running BGV verification.")

    st.markdown("---")

    # Run BGV button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button(
            "🚀 Run BGV Verification",
            type="primary",
            use_container_width=True
        )

    # Handle form submission
    if run_button:
        # Validation
        if not company_name:
            st.error("⚠️ Please enter the company name.")
        elif not ticker:
            st.error("⚠️ Please enter the stock ticker.")
        elif not sector:
            st.error("⚠️ Please select or enter the sector.")
        else:
            # Create uploads directory
            uploads_dir = ROOT_DIR / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded PDF if provided
            pdf_path = ""
            if annual_pdf:
                pdf_path = str(uploads_dir / f"{ticker.replace('.', '_')}_annual_report.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(annual_pdf.read())
                st.info(f"📄 Annual report saved to: {pdf_path}")
            
            # Progress indicator
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Initializing BGV verification pipeline...")
                progress_bar.progress(10)
                
                # Import and run the BGV pipeline
                from signal_sync.main import run_bgv
                
                status_text.text("🔍 Running company overview analysis...")
                progress_bar.progress(30)
                
                status_text.text("👥 Researching management team...")
                progress_bar.progress(50)
                
                status_text.text("📊 Analyzing financial data...")
                progress_bar.progress(70)
                
                status_text.text("⚠️ Running scam detection...")
                progress_bar.progress(85)
                
                # Run the actual pipeline
                output_path = run_bgv(
                    company_name=company_name.strip(),
                    ticker=ticker.strip().upper(),
                    sector=sector.strip(),
                    annual_report_path=pdf_path
                )
                
                progress_bar.progress(100)
                status_text.text("✅ BGV verification completed!")
                
                # Display results
                st.markdown("---")
                st.markdown("## 📋 BGV Verification Results")
                
                # Load and display results
                if os.path.exists(output_path):
                    with open(output_path) as f:
                        result = json.load(f)
                    
                    # Display scores
                    st.markdown("### Risk Scores")
                    score_cols = st.columns(4)
                    
                    scores = result.get('scores', {})
                    
                    with score_cols[0]:
                        trust_score = scores.get('trustworthiness_score', 0)
                        score_class = 'risk-low' if trust_score >= 70 else ('risk-moderate' if trust_score >= 40 else 'risk-high')
                        st.markdown(f"""
                        <div class="score-card {score_class}">
                            <h3>Trustworthiness</h3>
                            <h1>{trust_score:.1f}</h1>
                            <p>/100</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with score_cols[1]:
                        fin_score = scores.get('financial_integrity_score', 0)
                        score_class = 'risk-low' if fin_score >= 70 else ('risk-moderate' if fin_score >= 40 else 'risk-high')
                        st.markdown(f"""
                        <div class="score-card {score_class}">
                            <h3>Financial Integrity</h3>
                            <h1>{fin_score:.1f}</h1>
                            <p>/100</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with score_cols[2]:
                        mgmt_risk = scores.get('management_risk_score', 0)
                        score_class = 'risk-low' if mgmt_risk <= 30 else ('risk-moderate' if mgmt_risk <= 60 else 'risk-high')
                        st.markdown(f"""
                        <div class="score-card {score_class}">
                            <h3>Management Risk</h3>
                            <h1>{mgmt_risk:.1f}</h1>
                            <p>/100</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with score_cols[3]:
                        market_risk = scores.get('market_manipulation_risk_score', 0)
                        score_class = 'risk-low' if market_risk <= 30 else ('risk-moderate' if market_risk <= 60 else 'risk-high')
                        st.markdown(f"""
                        <div class="score-card {score_class}">
                            <h3>Market Manipulation</h3>
                            <h1>{market_risk:.1f}</h1>
                            <p>/100</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Final Verdict
                    st.markdown("### Final Verdict")
                    verdict = result.get('final_verdict', 'No verdict available')
                    if 'CRITICAL' in verdict.upper() or 'HIGH' in verdict.upper():
                        st.error(f"🚨 {verdict}")
                    elif 'MODERATE' in verdict.upper():
                        st.warning(f"⚠️ {verdict}")
                    else:
                        st.success(f"✅ {verdict}")
                    
                    # Findings tabs
                    st.markdown("### Detailed Findings")
                    findings_tabs = st.tabs([
                        "🏢 Company Overview",
                        "👥 Management",
                        "📊 Financial",
                        "⚠️ Scam Signals"
                    ])
                    
                    findings = result.get('findings', {})
                    
                    with findings_tabs[0]:
                        overview_findings = findings.get('overview_findings', [])
                        if overview_findings:
                            for finding in overview_findings:
                                st.markdown(f'<div class="finding-item">{finding}</div>', unsafe_allow_html=True)
                        else:
                            st.info("No specific findings to report.")
                    
                    with findings_tabs[1]:
                        mgmt_findings = findings.get('management_findings', [])
                        if mgmt_findings:
                            for finding in mgmt_findings:
                                css_class = "finding-item red-flag" if any(kw in finding.lower() for kw in ['fraud', 'scandal', 'fine', 'violation']) else "finding-item"
                                st.markdown(f'<div class="{css_class}">{finding}</div>', unsafe_allow_html=True)
                        else:
                            st.info("No specific findings to report.")
                        
                        # People profiles
                        people = result.get('evidence', {}).get('people_profiles', [])
                        if people:
                            st.markdown("#### Executive Profiles")
                            for person in people:
                                with st.expander(f"👤 {person.get('name', 'Unknown')} - {person.get('role', 'Unknown')}"):
                                    red_flags = person.get('red_flags', [])
                                    if red_flags:
                                        st.markdown("**Red Flags:**")
                                        for flag in red_flags:
                                            st.markdown(f"- 🚩 {flag}")
                                    else:
                                        st.success("No red flags identified.")
                    
                    with findings_tabs[2]:
                        fin_findings = findings.get('financial_irregularities', [])
                        if fin_findings:
                            for finding in fin_findings:
                                css_class = "finding-item red-flag" if any(kw in finding.lower() for kw in ['spike', 'anomaly', 'irregularity', 'concern']) else "finding-item"
                                st.markdown(f'<div class="{css_class}">{finding}</div>', unsafe_allow_html=True)
                        else:
                            st.success("No financial irregularities detected.")
                    
                    with findings_tabs[3]:
                        scam_findings = findings.get('scam_signals', [])
                        if scam_findings:
                            for finding in scam_findings:
                                st.markdown(f'<div class="finding-item red-flag">{finding}</div>', unsafe_allow_html=True)
                        else:
                            st.success("No scam signals detected.")
                    
                    # Company Profile
                    st.markdown("### Company Profile")
                    company = result.get('company', {})
                    profile_cols = st.columns(2)
                    
                    with profile_cols[0]:
                        st.markdown(f"**Name:** {company.get('name', 'N/A')}")
                        st.markdown(f"**Ticker:** {company.get('ticker', 'N/A')}")
                        st.markdown(f"**Sector:** {company.get('sector', 'N/A')}")
                        st.markdown(f"**Headquarters:** {company.get('headquarters', 'N/A')}")
                    
                    with profile_cols[1]:
                        st.markdown(f"**Founded:** {company.get('founded_year', 'N/A')}")
                        st.markdown(f"**Employees:** {company.get('employees', 'N/A')}")
                        if company.get('profile_summary'):
                            st.markdown(f"**Summary:** {company.get('profile_summary')}")
                    
                    # Download button
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="📥 Download Full BGV Report (JSON)",
                            data=json.dumps(result, indent=2),
                            file_name=f"bgv_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                else:
                    st.error("❌ Output file not found. Please check the logs.")
                    
            except ImportError as e:
                st.error(f"❌ Import error: {e}")
                st.info("Make sure all dependencies are installed. Run: `pip install -e .` in the project root.")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                st.exception(e)


# ============================================================================
# MAIN ROUTING
# ============================================================================

# Route to the appropriate page based on sidebar selection
if page == "🔍 BGV Verification":
    render_bgv_page()
else:
    render_reddit_sentiment_page()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Signal Sync - BGV & News Analysis | Built with CrewAI & Streamlit</p>
        <p>⚠️ This tool is for informational purposes only. Always conduct your own due diligence.</p>
    </div>
    """,
    unsafe_allow_html=True
)