from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Uses FinBERT to assign positive/neutral/negative sentiments to financial news."""
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        from transformers import pipeline
        logger.info(f"Loading FinBERT model: {model_name}")
        # Explicit truncation prevents FinBERT from crashing when passed full articles
        self.pipeline = pipeline("text-classification", model=model_name, truncation=True, max_length=512)
        logger.info("FinBERT model loaded successfully.")

    def analyze_batch(self, headlines: List[str], batch_size: int = 8) -> List[Dict[str, Any]]:
        """Perform sentiment analysis on a batch of headlines."""
        if not headlines:
            return []
            
        try:
            # HuggingFace pipeline handles batching natively if batch_size is provided
            results = self.pipeline(headlines, batch_size=batch_size)
            return results
        except Exception as e:
            logger.error(f"Error during sentiment analysis batch processing: {e}")
            # Fallback in case of failure to maintain array alignment
            return [{"label": "neutral", "score": 0.0} for _ in headlines]
