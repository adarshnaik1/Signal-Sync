#!/usr/bin/env python
"""
Test script to verify Reddit API connection and credentials.
Run this to ensure your .env file is correctly configured.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("\n" + "=" * 60)
    print("📋 STEP 1: Checking Environment Variables")
    print("=" * 60)
    
    # Only these are required for read-only mode
    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT"
    ]
    
    # Optional vars (not needed for read-only)
    optional_vars = [
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var, "")
        if not value:
            print(f"   ❌ {var}: NOT SET (required)")
            all_set = False
        elif "dummy" in value.lower():
            print(f"   ⚠️  {var}: SET (but contains 'dummy' - likely placeholder)")
            all_set = False
        else:
            # Mask the value for security
            masked = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
            print(f"   ✅ {var}: {masked}")
    
    for var in optional_vars:
        value = os.getenv(var, "")
        if value:
            masked = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
            print(f"   ℹ️  {var}: {masked} (optional)")
        else:
            print(f"   ℹ️  {var}: NOT SET (optional - not needed for read-only)")
    
    if not all_set:
        print("\n   ⚠️  Some required variables are missing or contain placeholder values!")
        print("   📝 Please update your .env file with real credentials.")
    
    return all_set


def test_praw_import():
    """Test if PRAW is installed correctly."""
    print("\n" + "=" * 60)
    print("📋 STEP 2: Testing PRAW Installation")
    print("=" * 60)
    
    try:
        import praw
        print(f"   ✅ PRAW version: {praw.__version__}")
        return True
    except ImportError as e:
        print(f"   ❌ PRAW not installed: {e}")
        print("   📝 Run: pip install praw")
        return False


def test_reddit_connection():
    """Test the actual Reddit API connection in read-only mode."""
    print("\n" + "=" * 60)
    print("📋 STEP 3: Testing Reddit API Connection (Read-Only Mode)")
    print("=" * 60)
    
    try:
        import praw
        
        client_id = os.getenv("REDDIT_CLIENT_ID", "")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        user_agent = os.getenv("REDDIT_USER_AGENT", "")
        
        # Only need client_id, client_secret, and user_agent for read-only
        if not all([client_id, client_secret, user_agent]):
            print("   ⚠️  Missing credentials - skipping connection test")
            return False
        
        if "dummy" in client_id.lower():
            print("   ⚠️  Using placeholder credentials - skipping connection test")
            return False
        
        print("   🔄 Connecting to Reddit API (read-only mode)...")
        
        # Read-only mode - no username/password needed
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test by fetching a subreddit
        print("   🔄 Testing subreddit access...")
        subreddit = reddit.subreddit("stocks")
        print(f"   ✅ Successfully accessed r/{subreddit.display_name}")
        
        # Test search capability
        print("   🔄 Testing search capability...")
        posts = list(subreddit.search("Tesla", limit=3))
        print(f"   ✅ Successfully fetched {len(posts)} posts from r/stocks")
        
        if posts:
            print(f"\n   📝 Sample post: \"{posts[0].title[:50]}...\"")
        
        return True
        
    except praw.exceptions.OAuthException as e:
        print(f"   ❌ Authentication failed: {e}")
        print("\n   📝 Possible issues:")
        print("      - Incorrect client_id or client_secret")
        print("      - Wrong username or password")
        print("      - Account may require 2FA (disable it or use an app password)")
        return False
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def test_vader_sentiment():
    """Test VADER sentiment analyzer."""
    print("\n" + "=" * 60)
    print("📋 STEP 4: Testing VADER Sentiment Analyzer")
    print("=" * 60)
    
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        
        analyzer = SentimentIntensityAnalyzer()
        
        test_texts = [
            ("This stock is amazing!", "Positive"),
            ("Terrible company, avoid!", "Negative"),
            ("The company reported earnings.", "Neutral")
        ]
        
        all_correct = True
        for text, expected in test_texts:
            scores = analyzer.polarity_scores(text)
            compound = scores['compound']
            
            if compound >= 0.05:
                actual = "Positive"
            elif compound <= -0.05:
                actual = "Negative"
            else:
                actual = "Neutral"
            
            status = "✅" if actual == expected else "⚠️"
            print(f"   {status} \"{text}\" → {actual} (score: {compound:.2f})")
            
            if actual != expected:
                all_correct = False
        
        return all_correct
        
    except ImportError:
        print("   ❌ VADER not installed")
        print("   📝 Run: pip install vaderSentiment")
        return False


def print_setup_instructions():
    """Print instructions for getting Reddit API credentials."""
    print("\n" + "=" * 60)
    print("📝 HOW TO GET REAL REDDIT API CREDENTIALS")
    print("=" * 60)
    print("""
1. Go to: https://www.reddit.com/prefs/apps
   
2. Scroll down and click "create app" or "create another app"

3. Fill in the form:
   - Name: SentimentAnalyzer (or any name)
   - App type: Select "script"
   - Description: (optional)
   - About URL: (leave empty)
   - Redirect URI: http://localhost:8080

4. Click "create app"

5. You'll see your app listed. Copy these values:
   - client_id: The string under your app name (e.g., "abc123xyz")
   - client_secret: The "secret" field

6. Create a .env file in the reddit_sentiment folder:

   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   REDDIT_USER_AGENT=SentimentAnalyzer/1.0 by your_username

⚠️  IMPORTANT NOTES:
   - If you have 2FA enabled on Reddit, you may need to disable it
     OR create an "app password" in your Reddit settings
   - Keep your .env file private (it's gitignored by default)
   - Never share your credentials publicly
""")


def main():
    print("\n")
    print("🔍 " + "=" * 56 + " 🔍")
    print("   REDDIT SENTIMENT ANALYZER - CONNECTION TEST")
    print("🔍 " + "=" * 56 + " 🔍")
    
    # Run tests
    env_ok = test_environment_variables()
    praw_ok = test_praw_import()
    vader_ok = test_vader_sentiment()
    
    if env_ok and praw_ok:
        connection_ok = test_reddit_connection()
    else:
        connection_ok = False
        print("\n" + "=" * 60)
        print("📋 STEP 3: Testing Reddit API Connection")
        print("=" * 60)
        print("   ⏭️  Skipped (missing prerequisites)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"   Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"   PRAW Installation:     {'✅ PASS' if praw_ok else '❌ FAIL'}")
    print(f"   VADER Installation:    {'✅ PASS' if vader_ok else '❌ FAIL'}")
    print(f"   Reddit Connection:     {'✅ PASS' if connection_ok else '❌ FAIL'}")
    
    if connection_ok:
        print("\n   🎉 ALL TESTS PASSED! You're ready to use real Reddit data!")
        print("   Run: python main.py \"Company Name\"")
    else:
        print("\n   ⚠️  Some tests failed. The system will use DUMMY DATA until fixed.")
        print_setup_instructions()
    
    print("\n")
    return connection_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
