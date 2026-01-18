# src/reddit_sentiment/services/reddit_scraper.py
"""
Reddit Data Extraction Service using PRAW.
Fetches posts related to a company from specified subreddits.
"""

import praw
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import REDDIT_CONFIG, DEFAULT_SUBREDDITS, SEARCH_CONFIG, OUTPUT_DIR


class RedditScraper:
    """
    Scrapes Reddit for posts related to a specific company.
    Uses PRAW (Python Reddit API Wrapper) for data extraction.
    """
    
    def __init__(self, use_dummy_data: bool = False):
        """
        Initialize the Reddit scraper.
        
        Args:
            use_dummy_data: If True, uses dummy data instead of making API calls.
                           Useful for testing without valid credentials.
        """
        self.use_dummy_data = use_dummy_data
        self.reddit = None
        
        if not use_dummy_data:
            self._initialize_reddit_client()
    
    def _initialize_reddit_client(self) -> None:
        """Initialize the PRAW Reddit client in read-only mode."""
        try:
            # Use read-only mode - no username/password needed
            # This works with both "script" and "web app" types
            self.reddit = praw.Reddit(
                client_id=REDDIT_CONFIG["client_id"],
                client_secret=REDDIT_CONFIG["client_secret"],
                user_agent=REDDIT_CONFIG["user_agent"]
            )
            
            # Verify connection by fetching a subreddit (read-only operation)
            test_sub = self.reddit.subreddit("stocks")
            _ = test_sub.display_name  # This triggers the API call
            print("✅ Successfully connected to Reddit API (read-only mode)")
            
        except Exception as e:
            print(f"⚠️ Failed to connect to Reddit API: {e}")
            print("   Switching to dummy data mode...")
            self.use_dummy_data = True
    
    def search_company(
        self,
        company_name: str,
        subreddits: Optional[List[str]] = None,
        posts_per_subreddit: int = None,
        sort_by: str = None,
        time_filter: str = None
    ) -> List[Dict]:
        """
        Search for posts related to a company across multiple subreddits.
        
        Args:
            company_name: Name or ticker of the company to search for
            subreddits: List of subreddits to search (defaults to DEFAULT_SUBREDDITS)
            posts_per_subreddit: Number of posts to fetch per subreddit
            sort_by: Sort method (relevance, hot, top, new)
            time_filter: Time filter (all, year, month, week, day, hour)
        
        Returns:
            List of post dictionaries
        """
        subreddits = subreddits or DEFAULT_SUBREDDITS
        posts_per_subreddit = posts_per_subreddit or SEARCH_CONFIG["posts_per_subreddit"]
        sort_by = sort_by or SEARCH_CONFIG["sort_by"]
        time_filter = time_filter or SEARCH_CONFIG["time_filter"]
        
        if self.use_dummy_data:
            return self._get_dummy_data(company_name, len(subreddits) * 5)
        
        all_posts = []
        seen_post_ids = set()
        
        print(f"\n🔍 Searching for '{company_name}' across {len(subreddits)} subreddits...")
        
        for subreddit_name in subreddits:
            try:
                print(f"   📂 Searching r/{subreddit_name}...", end=" ")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for posts
                search_results = subreddit.search(
                    query=company_name,
                    sort=sort_by,
                    time_filter=time_filter,
                    limit=posts_per_subreddit
                )
                
                subreddit_posts = 0
                for post in search_results:
                    # Skip duplicates
                    if post.id in seen_post_ids:
                        continue
                    seen_post_ids.add(post.id)
                    
                    # Extract post data
                    post_data = self._extract_post_data(post, subreddit_name)
                    all_posts.append(post_data)
                    subreddit_posts += 1
                
                print(f"Found {subreddit_posts} posts")
                
                # Rate limiting - be nice to Reddit's API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        print(f"\n✅ Total posts extracted: {len(all_posts)}")
        return all_posts
    
    def _extract_post_data(self, post, subreddit_name: str) -> Dict:
        """
        Extract relevant data from a Reddit post.
        
        Args:
            post: PRAW Submission object
            subreddit_name: Name of the source subreddit
        
        Returns:
            Dictionary with post data
        """
        # Handle deleted authors
        author_name = "[deleted]"
        try:
            if post.author:
                author_name = post.author.name
        except:
            pass
        
        # Handle post body (selftext)
        post_text = post.selftext if hasattr(post, 'selftext') else ""
        if post_text == "[removed]" or post_text == "[deleted]":
            post_text = ""
        
        return {
            "post_id": post.id,
            "author_id": author_name,
            "title": post.title,
            "post_text": post_text,
            "score": post.score,
            "upvote_ratio": getattr(post, 'upvote_ratio', 0),
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "created_time": datetime.utcfromtimestamp(post.created_utc).isoformat() + "Z",
            "subreddit": subreddit_name,
            "url": f"https://reddit.com{post.permalink}",
            "is_self": post.is_self,  # True if text post, False if link post
            "link_url": post.url if not post.is_self else None
        }
    
    def _get_dummy_data(self, company_name: str, num_posts: int = 25) -> List[Dict]:
        """
        Generate dummy data for testing without API credentials.
        
        Args:
            company_name: Company name used in dummy posts
            num_posts: Number of dummy posts to generate
        
        Returns:
            List of dummy post dictionaries
        """
        print(f"\n📦 Using dummy data for '{company_name}' (API not connected)")
        
        dummy_posts = [
            {
                "post_id": "abc123",
                "author_id": "investor_john",
                "title": f"Why I'm bullish on {company_name} - Great earnings report!",
                "post_text": f"{company_name} just released their quarterly earnings and they exceeded expectations. Revenue is up 25% YoY and the guidance looks strong. I've been holding this stock for 2 years and I'm very happy with the results. The management team seems competent and transparent.",
                "score": 1250,
                "upvote_ratio": 0.92,
                "num_comments": 145,
                "created_utc": 1705400000,
                "created_time": "2024-01-16T10:00:00Z",
                "subreddit": "stocks",
                "url": "https://reddit.com/r/stocks/comments/abc123",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "def456",
                "author_id": "cautious_trader",
                "title": f"{company_name} - Red flags I noticed in the annual report",
                "post_text": f"I've been analyzing {company_name}'s annual report and found some concerning patterns. The debt-to-equity ratio has been increasing steadily. Also, the related party transactions section raised some questions. I'm not saying it's a bad investment, but do your own due diligence.",
                "score": 890,
                "upvote_ratio": 0.78,
                "num_comments": 234,
                "created_utc": 1705300000,
                "created_time": "2024-01-15T06:00:00Z",
                "subreddit": "investing",
                "url": "https://reddit.com/r/investing/comments/def456",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "ghi789",
                "author_id": "wsb_yolo",
                "title": f"🚀🚀🚀 {company_name} TO THE MOON! Diamond hands! 💎🙌",
                "post_text": f"Listen up fellow apes! {company_name} is about to explode! I put my entire life savings into this. The shorts are gonna get squeezed. This is not financial advice but you'd be stupid not to buy. YOLO! 🚀🚀🚀",
                "score": 3500,
                "upvote_ratio": 0.65,
                "num_comments": 890,
                "created_utc": 1705200000,
                "created_time": "2024-01-14T02:00:00Z",
                "subreddit": "wallstreetbets",
                "url": "https://reddit.com/r/wallstreetbets/comments/ghi789",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "jkl012",
                "author_id": "neutral_analyst",
                "title": f"{company_name} Q4 earnings discussion thread",
                "post_text": f"Let's discuss {company_name}'s latest quarterly results. Revenue: $5.2B (vs $5.1B expected). EPS: $1.23 (vs $1.20 expected). The company maintained their full-year guidance. What are your thoughts?",
                "score": 456,
                "upvote_ratio": 0.88,
                "num_comments": 89,
                "created_utc": 1705100000,
                "created_time": "2024-01-12T22:00:00Z",
                "subreddit": "StockMarket",
                "url": "https://reddit.com/r/StockMarket/comments/jkl012",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "mno345",
                "author_id": "angry_bagholder",
                "title": f"Lost 50% on {company_name} - This company is a scam!",
                "post_text": f"I bought {company_name} at the top and now I'm down 50%. The CEO keeps making promises they never deliver. The product launches are always delayed. I should have listened to the warnings. Stay away from this garbage stock!",
                "score": 234,
                "upvote_ratio": 0.55,
                "num_comments": 178,
                "created_utc": 1705000000,
                "created_time": "2024-01-11T18:00:00Z",
                "subreddit": "stocks",
                "url": "https://reddit.com/r/stocks/comments/mno345",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "pqr678",
                "author_id": "tech_enthusiast",
                "title": f"{company_name}'s new product looks amazing!",
                "post_text": f"Just watched the {company_name} product launch event. The new features are incredible! They're really innovating in this space. As both a customer and investor, I'm impressed. The stock might be volatile short-term but long-term looks solid.",
                "score": 678,
                "upvote_ratio": 0.85,
                "num_comments": 112,
                "created_utc": 1704900000,
                "created_time": "2024-01-10T14:00:00Z",
                "subreddit": "technology",
                "url": "https://reddit.com/r/technology/comments/pqr678",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "stu901",
                "author_id": "dividend_investor",
                "title": f"{company_name} announces dividend increase",
                "post_text": f"{company_name} just announced a 10% dividend increase. This is the 5th consecutive year of dividend growth. For income investors, this is great news. The payout ratio is sustainable at around 40%.",
                "score": 345,
                "upvote_ratio": 0.91,
                "num_comments": 67,
                "created_utc": 1704800000,
                "created_time": "2024-01-09T10:00:00Z",
                "subreddit": "dividends",
                "url": "https://reddit.com/r/dividends/comments/stu901",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "vwx234",
                "author_id": "skeptical_sam",
                "title": f"Is {company_name} overvalued at current levels?",
                "post_text": f"Looking at {company_name}'s P/E ratio of 45x, it seems quite expensive compared to peers. The growth is there but how much is already priced in? I'm on the sidelines waiting for a pullback. Anyone else feeling the same?",
                "score": 189,
                "upvote_ratio": 0.72,
                "num_comments": 156,
                "created_utc": 1704700000,
                "created_time": "2024-01-08T06:00:00Z",
                "subreddit": "ValueInvesting",
                "url": "https://reddit.com/r/ValueInvesting/comments/vwx234",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "yza567",
                "author_id": "insider_info",
                "title": f"Breaking: {company_name} CEO sells shares",
                "post_text": f"SEC filing shows {company_name} CEO sold $5M worth of shares last week. Should we be concerned? Or is this just routine diversification? The timing seems suspicious given the upcoming earnings.",
                "score": 567,
                "upvote_ratio": 0.68,
                "num_comments": 234,
                "created_utc": 1704600000,
                "created_time": "2024-01-07T02:00:00Z",
                "subreddit": "stocks",
                "url": "https://reddit.com/r/stocks/comments/yza567",
                "is_self": True,
                "link_url": None
            },
            {
                "post_id": "bcd890",
                "author_id": "long_term_holder",
                "title": f"5 years holding {company_name} - My journey",
                "post_text": f"I first bought {company_name} 5 years ago at $50. Today it's at $180. Through all the ups and downs, I held on. The key was understanding the business fundamentals and not panicking during corrections. Patient investing works.",
                "score": 1890,
                "upvote_ratio": 0.94,
                "num_comments": 278,
                "created_utc": 1704500000,
                "created_time": "2024-01-05T22:00:00Z",
                "subreddit": "investing",
                "url": "https://reddit.com/r/investing/comments/bcd890",
                "is_self": True,
                "link_url": None
            }
        ]
        
        # Return requested number of posts
        return dummy_posts[:num_posts]
    
    def save_raw_data(
        self,
        posts: List[Dict],
        company_name: str,
        output_dir: Path = None
    ) -> str:
        """
        Save raw extracted posts to a JSON file.
        
        Args:
            posts: List of post dictionaries
            company_name: Company name for filename
            output_dir: Output directory path
        
        Returns:
            Path to the saved file
        """
        output_dir = output_dir or OUTPUT_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean company name for filename
        clean_name = company_name.replace(" ", "_").replace("/", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{clean_name}_raw_posts_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Raw data saved to: {filepath}")
        return str(filepath)


# Standalone function for direct usage
def fetch_reddit_posts(
    company_name: str,
    subreddits: List[str] = None,
    posts_limit: int = 50,
    use_dummy: bool = False
) -> List[Dict]:
    """
    Fetch Reddit posts about a company.
    
    Args:
        company_name: Company name or ticker to search
        subreddits: Optional list of subreddits
        posts_limit: Max posts per subreddit
        use_dummy: If True, use dummy data
    
    Returns:
        List of post dictionaries
    """
    scraper = RedditScraper(use_dummy_data=use_dummy)
    return scraper.search_company(
        company_name=company_name,
        subreddits=subreddits,
        posts_per_subreddit=posts_limit
    )


# CLI test
if __name__ == "__main__":
    import sys
    company = sys.argv[1] if len(sys.argv) > 1 else "Tesla"
    
    # Use dummy data for testing
    posts = fetch_reddit_posts(company, use_dummy=True)
    print(f"\nFetched {len(posts)} posts")
    
    for i, post in enumerate(posts[:3], 1):
        print(f"\n--- Post {i} ---")
        print(f"Title: {post['title'][:60]}...")
        print(f"Score: {post['score']} | Comments: {post['num_comments']}")
        print(f"Subreddit: r/{post['subreddit']}")
