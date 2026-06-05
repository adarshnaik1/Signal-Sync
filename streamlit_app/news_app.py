import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.news_sentiment.config import Config
from src.news_sentiment.collector import NewsCollector
from src.news_sentiment.analyzer import SentimentAnalyzer
from src.news_sentiment.service import NewsSentimentService

# Page configuration
st.set_page_config(page_title="News Sentiment Analysis", layout="wide", page_icon="📈")

@st.cache_resource
def get_analyzer():
    """Cache the FinBERT model to avoid reloading on every interaction."""
    return SentimentAnalyzer(model_name=Config.FINBERT_MODEL)

def main():
    st.title("📈 Indian Market News Sentiment Analysis")
    st.markdown("Analyze real-time news sentiment for any Indian stock ticker or company using **FinBERT** and **SerperDev API**.")

    # UI Inputs
    query = st.text_input("Enter Indian Stock Ticker or Company Name (e.g., TCS, INFY, RELIANCE, HDFCBANK):").strip()
    
    if st.button("Analyze Sentiment", type="primary"):
        if not query:
            st.warning("⚠️ Please enter a valid ticker or company name.")
            return
            
        with st.spinner(f"Fetching news and analyzing sentiment for '{query}'... This may take a moment."):
            # Initialize components
            try:
                analyzer = get_analyzer()
                collector = NewsCollector(api_key=Config.SERPER_API_KEY)
                service = NewsSentimentService(collector=collector, analyzer=analyzer)
                
                # Run pipeline
                result = service.get_sentiment_analysis(query, days=45)
                
                if result.get("status") == "error":
                    st.error(f"❌ {result.get('message')}")
                elif result.get("status") == "success":
                    st.success("✅ Analysis completed successfully!")
                    st.header(f"Results for `{query}`")
                    
                    # --- Key Metrics ---
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Color formatting for status
                    status_color = "green" if result["overall_status"] == "Bullish" else "red" if result["overall_status"] == "Bearish" else "gray"
                    
                    col1.metric("Overall Outlook", result["overall_status"])
                    col2.metric("Average Score", f"{result['average_score']:.2f}", 
                                delta="Positive" if result["average_score"] > 0 else "Negative" if result["average_score"] < 0 else "Neutral")
                    col3.metric("Articles Analyzed", result["total_articles"])
                    
                    dist = result["distribution"]
                    col4.metric("Bullish / Bearish %", f"{dist['positive_pct']:.1f}% / {dist['negative_pct']:.1f}%")

                    st.markdown("---")
                    
                    # --- Data Visualizations ---
                    col_chart, col_empty = st.columns([1, 1])
                    with col_chart:
                        st.subheader("Sentiment Distribution")
                        pie_data = pd.DataFrame({
                            "Sentiment": ["Positive", "Neutral", "Negative"],
                            "Count": [dist["positive"], dist["neutral"], dist["negative"]]
                        })
                        
                        fig = px.pie(pie_data, values="Count", names="Sentiment", 
                                    color="Sentiment",
                                    color_discrete_map={
                                        "Positive": "#2ca02c",  # Green
                                        "Neutral": "#7f7f7f",   # Gray
                                        "Negative": "#d62728"   # Red
                                    },
                                    hole=0.4) # Donut chart style
                        
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # --- Detailed Results Table ---
                    st.subheader("Analyzed Headlines (Last 45 Days)")
                    news_df = pd.DataFrame(result["news"])
                    
                    # Format DataFrame for UI
                    display_df = news_df[["parsed_date", "title", "source", "sentiment_label", "sentiment_confidence"]].copy()
                    display_df.columns = ["Date", "Headline", "Source", "Sentiment", "Confidence"]
                    
                    # Capitalize and format
                    display_df["Sentiment"] = display_df["Sentiment"].str.capitalize()
                    display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x:.2%}")
                    
                    # Sort by latest
                    display_df = display_df.sort_values(by="Date", ascending=False).reset_index(drop=True)
                    
                    # Display with conditional formatting mapping
                    def color_sentiment(val):
                        if val == 'Positive':
                            return 'color: green; font-weight: bold'
                        elif val == 'Negative':
                            return 'color: red; font-weight: bold'
                        return 'color: gray'

                    st.dataframe(display_df.style.applymap(color_sentiment, subset=['Sentiment']), use_container_width=True)

            except ValueError as ve:
                st.error(f"Configuration Error: {ve}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
