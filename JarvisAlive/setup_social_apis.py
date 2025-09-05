"""
Setup guide and testing for Social Listening Agent API connections.

This script helps you set up and test real API connections for:
1. Reddit API (PRAW)
2. Hacker News API (already working - no auth required)
3. Google Custom Search API (optional)
4. Google Alerts RSS feeds (optional)
"""

import asyncio
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_setup_instructions():
    """Print detailed setup instructions for each API."""
    
    print("🔧 Social Listening Agent - API Setup Guide")
    print("=" * 60)
    
    print("\n1. 🔴 REDDIT API (Required for Reddit monitoring)")
    print("-" * 40)
    print("Steps to get Reddit API access:")
    print("1. Go to: https://www.reddit.com/prefs/apps/")
    print("2. Click 'Create App' or 'Create Another App'")
    print("3. Fill in details:")
    print("   - Name: Social Listening Agent")
    print("   - App type: script")
    print("   - Redirect URI: http://localhost:8080")
    print("4. Copy CLIENT_ID (under app name) and CLIENT_SECRET")
    print("5. Add to .env file:")
    print("   REDDIT_CLIENT_ID=your_client_id_here")
    print("   REDDIT_CLIENT_SECRET=your_client_secret_here")
    print("   REDDIT_USER_AGENT=SocialListening:v1.0:JarvisAI")
    
    print("\n2. ✅ HACKER NEWS API (Already working - no setup needed)")
    print("-" * 40)
    print("✅ No authentication required")
    print("✅ Uses public Firebase API")
    print("✅ Already pulling real data!")
    
    print("\n3. 🟡 GOOGLE CUSTOM SEARCH API (Optional - for web monitoring)")
    print("-" * 40)
    print("Steps to get Google Custom Search API:")
    print("1. Go to: https://console.developers.google.com/")
    print("2. Create a new project or select existing")
    print("3. Enable 'Custom Search API'")
    print("4. Create credentials (API key)")
    print("5. Set up Custom Search Engine at: https://cse.google.com/")
    print("6. Add to .env file:")
    print("   GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key_here")
    print("   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id")
    
    print("\n4. 🟢 GOOGLE ALERTS RSS (Alternative - easier setup)")
    print("-" * 40)
    print("Steps to use Google Alerts RSS:")
    print("1. Go to: https://www.google.com/alerts")
    print("2. Create alerts for your keywords")
    print("3. Set delivery to 'RSS feed'")
    print("4. Copy RSS feed URLs")
    print("5. Add to .env file:")
    print("   GOOGLE_ALERTS_RSS_FEEDS=https://google.com/alerts/feeds/...,https://...")


async def test_current_api_status():
    """Test current API status and connectivity."""
    
    print("\n🧪 Testing Current API Status")
    print("=" * 40)
    
    # Test environment variables
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    google_api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    google_rss_feeds = os.getenv('GOOGLE_ALERTS_RSS_FEEDS')
    
    print("📋 Environment Variables:")
    print(f"  REDDIT_CLIENT_ID: {'✅ Found' if reddit_client_id else '❌ Not found'}")
    print(f"  REDDIT_CLIENT_SECRET: {'✅ Found' if reddit_client_secret else '❌ Not found'}")
    print(f"  GOOGLE_CUSTOM_SEARCH_API_KEY: {'✅ Found' if google_api_key else '❌ Not found'}")
    print(f"  GOOGLE_ALERTS_RSS_FEEDS: {'✅ Found' if google_rss_feeds else '❌ Not found'}")
    
    # Test Reddit API
    print(f"\n🔴 Reddit API Test:")
    try:
        from departments.social_intelligence.connectors.reddit_connector import RedditConnector
        reddit_connector = RedditConnector()
        
        if reddit_connector.reddit:
            print("  ✅ Reddit API connection established")
            # Test with minimal search
            mentions = await reddit_connector.search_mentions(['test'], ['entrepreneur'], max_results=1, time_range_hours=24)
            print(f"  ✅ Test search returned {len(mentions)} mentions")
        else:
            print("  ❌ Reddit API not connected (using mock data)")
            print("  💡 Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env")
            
    except Exception as e:
        print(f"  ❌ Reddit test failed: {e}")
    
    # Test Hacker News API
    print(f"\n✅ Hacker News API Test:")
    try:
        from departments.social_intelligence.connectors.hackernews_connector import HackerNewsConnector
        hn_connector = HackerNewsConnector()
        
        mentions = await hn_connector.search_mentions(['AI'], max_results=2, time_range_hours=24)
        print(f"  ✅ Hacker News API working - found {len(mentions)} mentions")
        
        if mentions:
            print(f"  📋 Sample: {mentions[0].title[:50]}...")
            
    except Exception as e:
        print(f"  ❌ Hacker News test failed: {e}")
    
    # Test Google integration
    print(f"\n🟡 Google Integration Test:")
    try:
        from departments.social_intelligence.connectors.google_alerts_connector import GoogleAlertsConnector
        google_connector = GoogleAlertsConnector()
        
        mentions = await google_connector.search_mentions(['startup'], max_results=2, time_range_hours=24)
        print(f"  ✅ Google connector working - found {len(mentions)} mentions")
        
        if google_api_key:
            print("  ✅ Google Custom Search API configured")
        elif google_rss_feeds:
            print("  ✅ Google Alerts RSS feeds configured")
        else:
            print("  ❌ Using mock data (add Google API key or RSS feeds)")
            
    except Exception as e:
        print(f"  ❌ Google test failed: {e}")


async def test_social_listening_with_real_apis():
    """Test the complete Social Listening Agent with real API connections."""
    
    print("\n🚀 Testing Social Listening Agent with Real APIs")
    print("=" * 60)
    
    try:
        from departments.social_intelligence.social_listening_agent import SocialListeningAgent
        
        # Create agent with environment configuration
        config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'reddit': {
                'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
                'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'reddit_user_agent': os.getenv('REDDIT_USER_AGENT', 'SocialListening:v1.0:JarvisAI')
            }
        }
        
        agent = SocialListeningAgent(config)
        
        # Test with minimal request
        test_state = {
            "monitoring_goal": "Test API connections with minimal usage",
            "keywords": ["startup", "AI"],
            "sources": ["reddit", "hackernews", "google_alerts"],
            "max_mentions": 5,  # MINIMAL to avoid using too many API calls
            "time_range_hours": 24,
            "monitoring_focus": "api_test"
        }
        
        print("🧪 Running minimal test...")
        result = await agent.run(test_state)
        
        print(f"✅ Success: {result.get('monitoring_success')}")
        print(f"📊 Total mentions: {result.get('mentions_found')}")
        print(f"🚨 Alerts: {len(result.get('high_priority_alerts', []))}")
        print(f"🎯 Opportunities: {len(result.get('engagement_opportunities', []))}")
        print(f"📡 Sources used: {result.get('sources_monitored', [])}")
        
        if result.get('sentiment_summary'):
            sentiment = result['sentiment_summary']
            print(f"😊 Sentiment: {sentiment.get('positive_count')}+ {sentiment.get('negative_count')}- {sentiment.get('neutral_count')}neutral")
        
        print("\n🎉 Social Listening Agent working with available APIs!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print_setup_instructions()
    
    async def main():
        await test_current_api_status()
        await test_social_listening_with_real_apis()
    
    asyncio.run(main())
