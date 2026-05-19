"""
TF-IDF based keyword extraction from news articles.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer


class KeywordExtractor:
    """
    Extracts top keywords and trending terms using TF-IDF.
    CPU-friendly and suitable for modest article volumes.
    """

    def __init__(self, max_features: int = 500, top_n: int = 15):
        """
        Initialize extractor.

        Args:
            max_features: Maximum vocabulary size for TF-IDF.
            top_n: Number of top keywords to return.
        """
        self.max_features = max_features
        self.top_n = top_n

    def extract_keywords(self, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Extract top keywords from a corpus of cleaned documents.

        Args:
            documents: List of cleaned text strings.

        Returns:
            List of (keyword, score) tuples sorted by importance.
        """
        valid_docs = [d for d in documents if d and len(d.strip()) > 0]
        if not valid_docs:
            return []

        if len(valid_docs) == 1:
            tokens = valid_docs[0].split()
            freq: Dict[str, int] = {}
            for token in tokens:
                freq[token] = freq.get(token, 0) + 1
            ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            return [(word, float(count)) for word, count in ranked[: self.top_n]]

        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
        )

        try:
            matrix = vectorizer.fit_transform(valid_docs)
        except ValueError:
            return []

        scores = matrix.sum(axis=0).A1
        terms = vectorizer.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
        return [(term, float(score)) for term, score in ranked[: self.top_n]]

    def extract_from_articles(self, articles: List[Dict]) -> Dict:
        """
        Extract keywords from article list using cleaned_text field.

        Args:
            articles: Processed articles with cleaned_text.

        Returns:
            Dict with keywords list and keyword_scores map.
        """
        documents = [a.get("cleaned_text", "") for a in articles]
        keywords = self.extract_keywords(documents)

        return {
            "keywords": [k for k, _ in keywords],
            "keyword_scores": {k: v for k, v in keywords},
            "trending_terms": [k for k, _ in keywords[:10]],
        }
