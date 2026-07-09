from typing import Dict, Any
from .collector import NewsCollector
from .analyzer import SentimentAnalyzer
import logging

logger = logging.getLogger(__name__)

class NewsSentimentService:
    """Orchestrates news collection and sentiment analysis."""
    
    def __init__(self, collector: NewsCollector, analyzer: SentimentAnalyzer):
        self.collector = collector
        self.analyzer = analyzer

    def get_sentiment_analysis(self, query: str, days: int = 45) -> Dict[str, Any]:
        """Fetch news and analyze sentiment for the provided query."""
        logger.info(f"Starting sentiment analysis workflow for: {query} (Last {days} days)")
        
        try:
            news_items = self.collector.fetch_news(query, days=days)
            
            if not news_items:
                return {"status": "error", "message": f"No news found for '{query}' in the last {days} days."}

            headlines = [item.get("title", "") for item in news_items]
            
            logger.info(f"Analyzing sentiment for {len(headlines)} headlines")
            sentiment_results = self.analyzer.analyze_batch(headlines)

            analyzed_news = []
            for news, sentiment in zip(news_items, sentiment_results):
                label = sentiment["label"].lower()
                confidence = float(sentiment["score"])
                
                # --- SECOND LEVEL SENTIMENT EVALUATION ---
                # If headline is neutral, deep-analyze the full article text
                if label == "neutral" and news.get("link"):
                    logger.info(f"Headline neutral. Fetching full article: {news.get('link')}")
                    full_text = self.collector.fetch_article_text(news["link"])
                    if full_text and len(full_text) > 100:
                        # Re-evaluate the sentiment based on full article
                        new_sentiment = self.analyzer.analyze_batch([full_text])[0]
                        new_label = new_sentiment["label"].lower()
                        
                        if new_label != "neutral":
                            logger.info(f"Re-classified from neutral to {new_label} based on full text.")
                            label = new_label
                            confidence = float(new_sentiment["score"])
                            news["deep_analyzed"] = True
                
                if label == "positive":
                    score = 1
                elif label == "negative":
                    score = -1
                else:
                    score = 0
                    
                news_with_sentiment = {
                    **news, 
                    "sentiment_label": label, 
                    "sentiment_confidence": confidence, 
                    "sentiment_score": score
                }
                analyzed_news.append(news_with_sentiment)

            return self._aggregate_results(analyzed_news)
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis workflow: {e}")
            return {"status": "error", "message": str(e)}

    def _aggregate_results(self, analyzed_news: list) -> Dict[str, Any]:
        """Aggregate sentiment scores into a summary."""
        total = len(analyzed_news)
        if total == 0:
            return {"status": "error", "message": "No news to aggregate."}

        pos = sum(1 for n in analyzed_news if n["sentiment_score"] == 1)
        neg = sum(1 for n in analyzed_news if n["sentiment_score"] == -1)
        neu = sum(1 for n in analyzed_news if n["sentiment_score"] == 0)

        avg_score = sum(n["sentiment_score"] for n in analyzed_news) / total

        if avg_score > 0.1:
            overall = "Bullish"
        elif avg_score < -0.1:
            overall = "Bearish"
        else:
            overall = "Neutral"

        return {
            "status": "success",
            "overall_status": overall,
            "average_score": avg_score,
            "total_articles": total,
            "distribution": {
                "positive": pos,
                "negative": neg,
                "neutral": neu,
                "positive_pct": (pos / total) * 100 if total > 0 else 0,
                "negative_pct": (neg / total) * 100 if total > 0 else 0,
                "neutral_pct": (neu / total) * 100 if total > 0 else 0
            },
            "news": analyzed_news
        }
