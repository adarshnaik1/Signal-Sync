# src/reddit_sentiment/services/sentiment_analyzer.py
"""
Sentiment Analysis Service using VADER.
Analyzes text sentiment and classifies as Positive, Negative, or Neutral.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Tuple
from datetime import datetime
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SENTIMENT_THRESHOLDS, OUTPUT_DIR


class SentimentAnalyzer:
    """
    Performs sentiment analysis on text using VADER (Valence Aware Dictionary and sEntiment Reasoner).
    VADER is specifically attuned to social media text.
    """
    
    def __init__(self, thresholds: Dict = None):
        """
        Initialize the sentiment analyzer.
        
        Args:
            thresholds: Optional custom thresholds for sentiment classification
        """
        self.analyzer = SentimentIntensityAnalyzer()
        self.thresholds = thresholds or SENTIMENT_THRESHOLDS
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with sentiment scores and label
        """
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            return {
                "sentiment_label": "Neutral",
                "sentiment_score": 0.0,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0,
                "compound_score": 0.0
            }
        
        # Get VADER scores
        scores = self.analyzer.polarity_scores(text)
        
        # Classify based on compound score
        compound = scores["compound"]
        label = self._classify_sentiment(compound)
        
        return {
            "sentiment_label": label,
            "sentiment_score": compound,
            "positive_score": scores["pos"],
            "negative_score": scores["neg"],
            "neutral_score": scores["neu"],
            "compound_score": compound
        }
    
    def _classify_sentiment(self, compound_score: float) -> str:
        """
        Classify compound score into sentiment label.
        
        Args:
            compound_score: VADER compound score (-1 to +1)
        
        Returns:
            Sentiment label: "Positive", "Negative", or "Neutral"
        """
        positive_threshold = self.thresholds.get("positive", 0.05)
        negative_threshold = self.thresholds.get("negative", -0.05)
        
        if compound_score >= positive_threshold:
            return "Positive"
        elif compound_score <= negative_threshold:
            return "Negative"
        else:
            return "Neutral"
    
    def analyze_post(self, post: Dict) -> Dict:
        """
        Analyze sentiment of a Reddit post (title and body).
        
        Args:
            post: Post dictionary with 'cleaned_title', 'cleaned_text', and 'combined_text'
        
        Returns:
            Post dictionary enriched with sentiment data
        """
        enriched_post = post.copy()
        
        # Analyze title
        title_text = post.get("cleaned_title", post.get("title", ""))
        title_sentiment = self.analyze_text(title_text)
        enriched_post["title_sentiment_label"] = title_sentiment["sentiment_label"]
        enriched_post["title_sentiment_score"] = title_sentiment["sentiment_score"]
        
        # Analyze body
        body_text = post.get("cleaned_text", post.get("post_text", ""))
        body_sentiment = self.analyze_text(body_text)
        enriched_post["body_sentiment_label"] = body_sentiment["sentiment_label"]
        enriched_post["body_sentiment_score"] = body_sentiment["sentiment_score"]
        
        # Calculate overall sentiment
        combined_text = post.get("combined_text", f"{title_text} {body_text}")
        overall_sentiment = self.analyze_text(combined_text)
        
        enriched_post["sentiment_label"] = overall_sentiment["sentiment_label"]
        enriched_post["sentiment_score"] = overall_sentiment["sentiment_score"]
        enriched_post["positive_score"] = overall_sentiment["positive_score"]
        enriched_post["negative_score"] = overall_sentiment["negative_score"]
        enriched_post["neutral_score"] = overall_sentiment["neutral_score"]
        
        return enriched_post
    
    def analyze_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment of multiple posts.
        
        Args:
            posts: List of post dictionaries
        
        Returns:
            List of sentiment-enriched post dictionaries
        """
        analyzed_posts = []
        
        total = len(posts)
        for i, post in enumerate(posts, 1):
            if i % 10 == 0 or i == total:
                print(f"   Analyzing post {i}/{total}...")
            
            analyzed_post = self.analyze_post(post)
            analyzed_posts.append(analyzed_post)
        
        return analyzed_posts
    
    def generate_summary(self, posts: List[Dict]) -> Dict:
        """
        Generate summary statistics from analyzed posts.
        
        Args:
            posts: List of sentiment-analyzed posts
        
        Returns:
            Dictionary with summary statistics
        """
        if not posts:
            return {"error": "No posts to analyze"}
        
        total = len(posts)
        positive_count = sum(1 for p in posts if p.get("sentiment_label") == "Positive")
        negative_count = sum(1 for p in posts if p.get("sentiment_label") == "Negative")
        neutral_count = sum(1 for p in posts if p.get("sentiment_label") == "Neutral")
        
        scores = [p.get("sentiment_score", 0) for p in posts]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count by subreddit
        subreddit_counts = {}
        subreddit_sentiments = {}
        for post in posts:
            sub = post.get("subreddit", "unknown")
            subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
            
            if sub not in subreddit_sentiments:
                subreddit_sentiments[sub] = {"positive": 0, "negative": 0, "neutral": 0}
            
            label = post.get("sentiment_label", "Neutral").lower()
            subreddit_sentiments[sub][label] = subreddit_sentiments[sub].get(label, 0) + 1
        
        # Determine overall sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            overall_sentiment = "Positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Mixed/Neutral"
        
        return {
            "total_posts_analyzed": total,
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "positive_percentage": round(positive_count / total * 100, 1),
                "negative_percentage": round(negative_count / total * 100, 1),
                "neutral_percentage": round(neutral_count / total * 100, 1)
            },
            "average_sentiment_score": round(avg_score, 4),
            "overall_sentiment": overall_sentiment,
            "subreddit_breakdown": subreddit_counts,
            "subreddit_sentiments": subreddit_sentiments,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_extreme_posts(self, posts: List[Dict], top_n: int = 5) -> Dict:
        """
        Get the most positive and most negative posts.
        
        Args:
            posts: List of analyzed posts
            top_n: Number of posts to return for each category
        
        Returns:
            Dictionary with most positive and most negative posts
        """
        sorted_by_score = sorted(posts, key=lambda x: x.get("sentiment_score", 0))
        
        most_negative = sorted_by_score[:top_n]
        most_positive = sorted_by_score[-top_n:][::-1]
        
        def simplify_post(post):
            return {
                "post_id": post.get("post_id"),
                "title": post.get("title"),
                "sentiment_label": post.get("sentiment_label"),
                "sentiment_score": post.get("sentiment_score"),
                "score": post.get("score"),
                "subreddit": post.get("subreddit"),
                "url": post.get("url")
            }
        
        return {
            "most_positive": [simplify_post(p) for p in most_positive],
            "most_negative": [simplify_post(p) for p in most_negative]
        }


def save_sentiment_results(
    posts: List[Dict],
    summary: Dict,
    company_name: str,
    output_dir: Path = None
) -> str:
    """
    Save sentiment analysis results to JSON file.
    
    Args:
        posts: List of analyzed posts
        summary: Summary statistics
        company_name: Company name for filename
        output_dir: Output directory
    
    Returns:
        Path to saved file
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean company name for filename
    clean_name = company_name.replace(" ", "_").replace("/", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_sentiment_results_{timestamp}.json"
    filepath = output_dir / filename
    
    # Prepare output
    output = {
        "company": company_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "posts": posts
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Sentiment results saved to: {filepath}")
    return str(filepath)


# Standalone function for direct usage
def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Tuple of (sentiment_label, sentiment_score)
    """
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_text(text)
    return result["sentiment_label"], result["sentiment_score"]


# CLI test
if __name__ == "__main__":
    # Test with sample texts
    test_texts = [
        "I love this company! The products are amazing and the service is excellent!",
        "This is the worst stock ever. Lost all my money. Avoid at all costs.",
        "The company reported quarterly earnings. Revenue was $5 billion.",
        "🚀🚀🚀 TO THE MOON! Diamond hands baby! Best investment ever!",
        "Complete scam. Management is lying to investors. Stay away!",
    ]
    
    analyzer = SentimentAnalyzer()
    
    print("Sentiment Analysis Examples:\n")
    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"Text: {text[:60]}...")
        print(f"  Label: {result['sentiment_label']}")
        print(f"  Score: {result['sentiment_score']:.4f}")
        print(f"  (+): {result['positive_score']:.3f}  (-): {result['negative_score']:.3f}  (=): {result['neutral_score']:.3f}")
        print()
