#!/usr/bin/env python
# src/reddit_sentiment/main.py
"""
Reddit Sentiment Analysis Pipeline
Main entry point for extracting Reddit posts and performing sentiment analysis.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR, DEFAULT_SUBREDDITS
from services.reddit_scraper import RedditScraper
from services.text_processor import TextProcessor
from services.sentiment_analyzer import SentimentAnalyzer, save_sentiment_results


def run_sentiment_analysis(
    company_name: str,
    subreddits: Optional[List[str]] = None,
    posts_limit: int = 50,
    use_dummy_data: bool = False,
    save_output: bool = True,
    output_dir: Optional[Path] = None
) -> dict:
    """
    Run the complete Reddit sentiment analysis pipeline.
    
    Args:
        company_name: Name or ticker of the company to analyze
        subreddits: List of subreddits to search (defaults to configured list)
        posts_limit: Maximum posts to fetch per subreddit
        use_dummy_data: If True, use dummy data instead of making API calls
        save_output: If True, save results to JSON file
        output_dir: Custom output directory
    
    Returns:
        Dictionary containing analyzed posts and summary statistics
    """
    output_dir = output_dir or OUTPUT_DIR
    
    print("\n" + "=" * 60)
    print(f"🔍 Reddit Sentiment Analysis for: {company_name}")
    print("=" * 60)
    
    # ===== PHASE 1: Data Extraction =====
    print("\n📥 PHASE 1: Extracting Reddit Posts")
    print("-" * 40)
    
    scraper = RedditScraper(use_dummy_data=use_dummy_data)
    raw_posts = scraper.search_company(
        company_name=company_name,
        subreddits=subreddits or DEFAULT_SUBREDDITS,
        posts_per_subreddit=posts_limit
    )
    
    if not raw_posts:
        print("❌ No posts found for this company.")
        return {"error": "No posts found", "company": company_name}
    
    print(f"   ✅ Extracted {len(raw_posts)} posts")
    
    # ===== PHASE 2: Text Preprocessing =====
    print("\n🧹 PHASE 2: Preprocessing Text")
    print("-" * 40)
    
    processor = TextProcessor()
    processed_posts = processor.process_posts(raw_posts)
    
    # Filter valid posts
    valid_posts = [p for p in processed_posts if p.get("has_sufficient_text", True)]
    print(f"   ✅ Processed {len(valid_posts)} posts with sufficient text")
    
    # ===== PHASE 3: Sentiment Analysis =====
    print("\n💭 PHASE 3: Analyzing Sentiment")
    print("-" * 40)
    
    analyzer = SentimentAnalyzer()
    analyzed_posts = analyzer.analyze_posts(valid_posts)
    
    print(f"   ✅ Analyzed sentiment for {len(analyzed_posts)} posts")
    
    # ===== PHASE 4: Generate Summary =====
    print("\n📊 PHASE 4: Generating Summary")
    print("-" * 40)
    
    summary = analyzer.generate_summary(analyzed_posts)
    extreme_posts = analyzer.get_extreme_posts(analyzed_posts, top_n=3)
    
    # Display summary
    print(f"\n   📈 Sentiment Distribution:")
    dist = summary["sentiment_distribution"]
    print(f"      ✅ Positive: {dist['positive']} ({dist['positive_percentage']}%)")
    print(f"      ❌ Negative: {dist['negative']} ({dist['negative_percentage']}%)")
    print(f"      ➖ Neutral:  {dist['neutral']} ({dist['neutral_percentage']}%)")
    print(f"\n   📍 Average Sentiment Score: {summary['average_sentiment_score']:.4f}")
    print(f"   🎯 Overall Sentiment: {summary['overall_sentiment']}")
    
    # ===== PHASE 5: Save Results =====
    output_path = None
    if save_output:
        print("\n💾 PHASE 5: Saving Results")
        print("-" * 40)
        
        # Prepare final output
        final_output = {
            "company": company_name,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": summary,
            "extreme_posts": extreme_posts,
            "posts": analyzed_posts
        }
        
        # Save to file
        clean_name = company_name.replace(" ", "_").replace("/", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{clean_name}_sentiment_results_{timestamp}.json"
        filepath = Path(output_dir) / filename
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        
        output_path = str(filepath)
        print(f"   ✅ Results saved to: {output_path}")
    
    # ===== Complete =====
    print("\n" + "=" * 60)
    print("✅ Sentiment Analysis Complete!")
    print("=" * 60 + "\n")
    
    return {
        "company": company_name,
        "summary": summary,
        "extreme_posts": extreme_posts,
        "posts": analyzed_posts,
        "output_path": output_path
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Reddit Sentiment Analysis for Company Discussions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Tesla"
  python main.py "Apple" --subreddits stocks investing technology
  python main.py "Microsoft" --limit 100 --dummy
        """
    )
    
    parser.add_argument(
        "company",
        type=str,
        help="Company name or stock ticker to analyze"
    )
    
    parser.add_argument(
        "--subreddits", "-s",
        nargs="+",
        default=None,
        help="List of subreddits to search (default: predefined list)"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=50,
        help="Maximum posts to fetch per subreddit (default: 50)"
    )
    
    parser.add_argument(
        "--dummy", "-d",
        action="store_true",
        help="Use dummy data instead of making API calls (for testing)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Custom output directory"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    args = parser.parse_args()
    
    # Run analysis
    result = run_sentiment_analysis(
        company_name=args.company,
        subreddits=args.subreddits,
        posts_limit=args.limit,
        use_dummy_data=args.dummy,
        save_output=not args.no_save,
        output_dir=Path(args.output) if args.output else None
    )
    
    return result


if __name__ == "__main__":
    main()
