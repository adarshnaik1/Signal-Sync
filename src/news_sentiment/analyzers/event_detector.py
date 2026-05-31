# src/news_sentiment/analyzers/event_detector.py
"""
Hybrid financial event detection pipeline.
Combines keyword detection, contextual phrase matching, and rule-based NLP.
Lightweight — CPU-only, no large LLMs.
"""

import re
from typing import Dict, List, Optional, Tuple

try:
    import nltk
    from nltk.tokenize import sent_tokenize

    for resource in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)
except ImportError:
    nltk = None
    sent_tokenize = None

try:
    import spacy

    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        _NLP = None
except ImportError:
    _NLP = None


# Stage 1: Financial keyword categories
EVENT_KEYWORDS = {
    "Fraud Investigation": {
        "keywords": ["fraud", "scam", "misappropriation", "embezzlement", "forensic audit"],
        "impact": "NEGATIVE",
        "weight": 0.9,
    },
    "Lawsuit": {
        "keywords": ["lawsuit", "litigation", "sued", "court case", "legal action", "arbitration"],
        "impact": "NEGATIVE",
        "weight": 0.75,
    },
    "Acquisition": {
        "keywords": ["acquisition", "acquire", "merger", "takeover", "buyout", "m&a"],
        "impact": "NEUTRAL",
        "weight": 0.8,
    },
    "Partnership": {
        "keywords": ["partnership", "collaboration", "joint venture", "alliance", "mou", "tie-up"],
        "impact": "POSITIVE",
        "weight": 0.7,
    },
    "Dividend": {
        "keywords": ["dividend", "interim dividend", "final dividend", "payout"],
        "impact": "POSITIVE",
        "weight": 0.65,
    },
    "Funding": {
        "keywords": ["funding", "fund raise", "investment round", "capital infusion", "pe investment"],
        "impact": "POSITIVE",
        "weight": 0.7,
    },
    "Penalty": {
        "keywords": ["penalty", "fine", "penalized", "regulatory action", "sanction"],
        "impact": "NEGATIVE",
        "weight": 0.85,
    },
    "SEBI Action": {
        "keywords": ["sebi", "securities and exchange board"],
        "impact": "NEGATIVE",
        "weight": 0.8,
    },
    "Bankruptcy": {
        "keywords": ["bankruptcy", "insolvency", "nclt", "liquidation", "ibc"],
        "impact": "NEGATIVE",
        "weight": 0.95,
    },
    "Layoffs": {
        "keywords": ["layoff", "layoffs", "job cuts", "workforce reduction", "retrenchment"],
        "impact": "NEGATIVE",
        "weight": 0.8,
    },
    "Profit Growth": {
        "keywords": ["profit growth", "net profit", "earnings beat", "revenue growth", "record profit"],
        "impact": "POSITIVE",
        "weight": 0.75,
    },
    "Loss": {
        "keywords": ["net loss", "loss widened", "earnings miss", "decline in profit"],
        "impact": "NEGATIVE",
        "weight": 0.8,
    },
}

# Stage 2: Contextual negation/denial patterns
DENIAL_PATTERNS = [
    r"\bdenies?\b",
    r"\bdenied\b",
    r"\brefutes?\b",
    r"\brefuted\b",
    r"\bno evidence\b",
    r"\bunfounded\b",
    r"\brumou?rs?\b",
    r"\bspeculat",
    r"\balleged\b",
    r"\bclaims?\s+(?:that|of)\b",
]

SPECULATIVE_PATTERNS = [
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bexpected to\b",
    r"\blikely to\b",
    r"\bsources say\b",
    r"\breportedly\b",
]

HISTORICAL_PATTERNS = [
    r"\blast year\b",
    r"\bpreviously\b",
    r"\bearlier\b",
    r"\bhistorical\b",
    r"\bin \d{4}\b",
]


class EventDetector:
    """Detect financial events with contextual confidence scoring."""

    def __init__(self):
        self.denial_re = [re.compile(p, re.IGNORECASE) for p in DENIAL_PATTERNS]
        self.speculative_re = [re.compile(p, re.IGNORECASE) for p in SPECULATIVE_PATTERNS]
        self.historical_re = [re.compile(p, re.IGNORECASE) for p in HISTORICAL_PATTERNS]

    def detect(self, text: str, source: str = "") -> Dict:
        """
        Detect the primary financial event in text.

        Returns event_type, impact, and confidence score (0-100).
        """
        if not text:
            return self._no_event()

        sentences = self._tokenize_sentences(text)
        best_event = None
        best_score = 0.0

        for event_type, config in EVENT_KEYWORDS.items():
            for sentence in sentences:
                score = self._score_sentence(sentence, config)
                if score > best_score:
                    best_score = score
                    best_event = {
                        "event_type": event_type,
                        "impact": config["impact"],
                        "confidence": int(min(score * 100, 100)),
                    }

        if best_event and best_score >= 0.35:
            if source:
                best_event["confidence"] = min(best_event["confidence"] + 5, 100)
            return best_event

        return self._no_event()

    def detect_all(self, text: str) -> List[str]:
        """Return all detected event types above threshold."""
        if not text:
            return []

        sentences = self._tokenize_sentences(text)
        detected = set()

        for event_type, config in EVENT_KEYWORDS.items():
            for sentence in sentences:
                if self._score_sentence(sentence, config) >= 0.4:
                    detected.add(event_type)
                    break

        return sorted(detected)

    def _tokenize_sentences(self, text: str) -> List[str]:
        if sent_tokenize:
            try:
                return sent_tokenize(text)
            except Exception:
                pass
        return re.split(r"[.!?]+", text)

    def _score_sentence(self, sentence: str, config: Dict) -> float:
        """Score a sentence for event relevance with context adjustments."""
        sentence_lower = sentence.lower()
        base_weight = config["weight"]

        keyword_hits = sum(1 for kw in config["keywords"] if kw in sentence_lower)
        if keyword_hits == 0:
            return 0.0

        score = base_weight * min(keyword_hits / 2, 1.0)

        # Stage 3: Contextual adjustments
        if self._matches_any(sentence, self.denial_re):
            score *= 0.3

        if self._matches_any(sentence, self.speculative_re):
            score *= 0.6

        if self._matches_any(sentence, self.historical_re):
            score *= 0.5

        # Stage 3b: spaCy dependency check for negation
        if _NLP and len(sentence) < 500:
            score = self._spacy_negation_adjust(sentence, score)

        return score

    def _spacy_negation_adjust(self, sentence: str, score: float) -> float:
        """Use spaCy to detect negated verbs near event keywords."""
        try:
            doc = _NLP(sentence)
            for token in doc:
                if token.dep_ == "neg":
                    score *= 0.4
                    break
        except Exception:
            pass
        return score

    def _matches_any(self, text: str, patterns: list) -> bool:
        return any(p.search(text) for p in patterns)

    def _no_event(self) -> Dict:
        return {
            "event_type": "General News",
            "impact": "NEUTRAL",
            "confidence": 30,
        }
