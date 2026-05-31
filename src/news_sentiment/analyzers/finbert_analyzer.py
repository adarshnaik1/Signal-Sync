# src/news_sentiment/analyzers/finbert_analyzer.py
"""
FinBERT-based financial sentiment analysis.
Uses ProsusAI/finbert — optimized for financial news, CPU-friendly.
"""

from typing import Dict, Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FINBERT_MODEL, MAX_TEXT_LENGTH


class FinBERTAnalyzer:
    """Lazy-loaded FinBERT sentiment classifier."""

    _classifier = None

    def __init__(self, model_name: str = FINBERT_MODEL):
        self.model_name = model_name

    def _load_model(self):
        if FinBERTAnalyzer._classifier is None:
            from transformers import pipeline

            print("   Loading FinBERT model (first run may take a minute)...")
            FinBERTAnalyzer._classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                truncation=True,
                max_length=512,
            )
            print("   [OK] FinBERT model loaded")

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of financial text.

        Returns sentiment label (Positive/Negative/Neutral) and confidence score.
        """
        if not text or not text.strip():
            return {"sentiment": "Neutral", "score": 0.5}

        self._load_model()
        truncated = text[:MAX_TEXT_LENGTH]

        try:
            result = FinBERTAnalyzer._classifier(truncated)[0]
            label = result["label"].lower()
            score = round(result["score"], 4)

            sentiment_map = {
                "positive": "Positive",
                "negative": "Negative",
                "neutral": "Neutral",
            }
            return {
                "sentiment": sentiment_map.get(label, "Neutral"),
                "score": score,
            }
        except Exception as e:
            print(f"   [WARN] FinBERT analysis failed: {e}")
            return {"sentiment": "Neutral", "score": 0.5}

    def analyze_batch(self, texts: list) -> list:
        """Analyze sentiment for multiple texts."""
        return [self.analyze(text) for text in texts]
