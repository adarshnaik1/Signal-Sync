# src/reddit_sentiment/services/text_processor.py
"""
Text Preprocessing Service for Reddit posts.
Cleans and normalizes text for sentiment analysis.
"""

import re
from typing import Dict, List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PREPROCESSING_CONFIG


class TextProcessor:
    """
    Preprocesses Reddit post text for sentiment analysis.
    Handles Reddit-specific formatting, URLs, and special characters.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the text processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or PREPROCESSING_CONFIG
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text for sentiment analysis.
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        cleaned = text
        
        # Remove URLs
        if self.config.get("remove_urls", True):
            cleaned = self._remove_urls(cleaned)
        
        # Remove Reddit-specific formatting
        if self.config.get("remove_reddit_formatting", True):
            cleaned = self._remove_reddit_formatting(cleaned)
        
        # Remove special characters (but keep basic punctuation)
        if self.config.get("remove_special_chars", True):
            cleaned = self._remove_special_chars(cleaned)
        
        # Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)
        
        # Convert to lowercase if configured
        if self.config.get("lowercase", True):
            cleaned = cleaned.lower()
        
        return cleaned.strip()
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        # Match http/https URLs
        url_pattern = r'https?://\S+|www\.\S+'
        text = re.sub(url_pattern, '', text)
        
        # Match Reddit-style links [text](url)
        reddit_link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
        text = re.sub(reddit_link_pattern, r'\1', text)
        
        return text
    
    def _remove_reddit_formatting(self, text: str) -> str:
        """Remove Reddit-specific formatting and elements."""
        # Remove subreddit references
        text = re.sub(r'/r/\w+', '', text)
        text = re.sub(r'r/\w+', '', text)
        
        # Remove user mentions
        text = re.sub(r'/u/\w+', '', text)
        text = re.sub(r'u/\w+', '', text)
        
        # Remove markdown formatting
        # Bold **text** or __text__
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        
        # Italic *text* or _text_
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Strikethrough ~~text~~
        text = re.sub(r'~~([^~]+)~~', r'\1', text)
        
        # Superscript ^text
        text = re.sub(r'\^(\S+)', r'\1', text)
        
        # Code blocks and inline code
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        
        # Blockquotes
        text = re.sub(r'^>+\s*', '', text, flags=re.MULTILINE)
        
        # Remove common Reddit phrases
        common_phrases = [
            r'TL;?DR:?\s*',
            r'EDIT\d*:?\s*',
            r'Edit\d*:?\s*',
            r'UPDATE:?\s*',
            r'Update:?\s*',
            r'ETA:?\s*',
            r'PS:?\s*',
            r'P\.S\.:?\s*',
            r'Source:?\s*',
            r'Sauce:?\s*',
        ]
        for phrase in common_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        # Remove [deleted] and [removed] placeholders
        text = re.sub(r'\[deleted\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[removed\]', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_special_chars(self, text: str) -> str:
        """
        Remove special characters while keeping basic punctuation.
        Preserves sentiment-relevant characters like ! and ?
        """
        # Keep letters, numbers, basic punctuation, and spaces
        # Allow: . , ! ? ' " - and common punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\'\"\-\:\;\(\)]', ' ', text)
        
        # Remove excessive punctuation (e.g., !!!!!!)
        text = re.sub(r'([!?.]){3,}', r'\1\1', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and newlines."""
        # Replace multiple newlines with single space
        text = re.sub(r'\n+', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def process_post(self, post: Dict) -> Dict:
        """
        Process a single Reddit post, cleaning title and body.
        
        Args:
            post: Post dictionary with 'title' and 'post_text' fields
        
        Returns:
            Post dictionary with added 'cleaned_title' and 'cleaned_text' fields
        """
        processed_post = post.copy()
        
        # Clean title
        title = post.get("title", "")
        processed_post["cleaned_title"] = self.clean_text(title)
        
        # Clean body text
        body = post.get("post_text", "")
        processed_post["cleaned_text"] = self.clean_text(body)
        
        # Create combined text for analysis
        combined = f"{title} {body}".strip()
        processed_post["combined_text"] = self.clean_text(combined)
        
        # Flag if text is too short
        min_length = self.config.get("min_text_length", 10)
        processed_post["has_sufficient_text"] = len(processed_post["combined_text"]) >= min_length
        
        return processed_post
    
    def process_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Process multiple Reddit posts.
        
        Args:
            posts: List of post dictionaries
        
        Returns:
            List of processed post dictionaries
        """
        processed_posts = []
        
        for post in posts:
            processed_post = self.process_post(post)
            processed_posts.append(processed_post)
        
        return processed_posts


# Standalone function for direct usage
def preprocess_text(text: str) -> str:
    """
    Clean text for sentiment analysis.
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    processor = TextProcessor()
    return processor.clean_text(text)


def preprocess_posts(posts: List[Dict]) -> List[Dict]:
    """
    Preprocess a list of Reddit posts.
    
    Args:
        posts: List of post dictionaries
    
    Returns:
        List of processed posts with cleaned text
    """
    processor = TextProcessor()
    return processor.process_posts(posts)


# CLI test
if __name__ == "__main__":
    # Test with sample text
    sample_texts = [
        "Check out this stock! 🚀🚀🚀 https://example.com/stock $TSLA to the moon!!!",
        "I found this on r/wallstreetbets from u/trader123. **Very bullish** on this one!",
        "TL;DR: Company is doing well. EDIT: Updated with more info. The CEO said...",
        "This is a [link](https://example.com) with some ~~strikethrough~~ text.",
    ]
    
    processor = TextProcessor()
    
    print("Text Preprocessing Examples:\n")
    for i, text in enumerate(sample_texts, 1):
        cleaned = processor.clean_text(text)
        print(f"--- Example {i} ---")
        print(f"Original: {text}")
        print(f"Cleaned:  {cleaned}")
        print()
