"""Test Social Listening Agent directly."""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from departments.social_intelligence.social_listening_agent import SocialListeningAgent


async def test_social_listening_direct():
    """Test Social Listening Agent with direct execution."""
    
    print("🧪 Testing Social Listening Agent - Direct Execution")
    print("=" * 60)
    
    # Create agent with config
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'reddit': {
            'reddit_client_id': os.getenv('REDDIT_CLIENT_ID', 'your_client_id'),
            'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret'),
            'reddit_user_agent': 'SocialListening:v1.0'
        }
    }
    
    agent = SocialListeningAgent(config)
    
    # Test Case 1: Brand monitoring
    test_state_1 = {
        "monitoring_goal": "Monitor brand mentions and competitor discussions",
        "keywords": ["CRM", "marketing automation"],
        "competitor_keywords": ["HubSpot", "Salesforce"],
        "sources": ["reddit", "google_alerts", "hackernews"],
        "max_mentions": 20,
        "time_range_hours": 24,
        "monitoring_focus": "brand_monitoring"
    }
    
    print("\n🧪 Test 1: Brand Monitoring")
    print("-" * 40)
    result_1 = await agent.run(test_state_1)
    
    print(f"✅ Success: {result_1.get('monitoring_success')}")
    print(f"📊 Mentions found: {result_1.get('mentions_found')}")
    print(f"🚨 Alerts generated: {len(result_1.get('high_priority_alerts', []))}")
    print(f"🎯 Engagement opportunities: {len(result_1.get('engagement_opportunities', []))}")
    
    if result_1.get('sentiment_summary'):
        sentiment = result_1['sentiment_summary']
        print(f"😊 Sentiment: {sentiment.get('positive_count')}+ {sentiment.get('negative_count')}- {sentiment.get('neutral_count')}neutral")
    
    # Test Case 2: Pain point detection
    test_state_2 = {
        "monitoring_goal": "Find people discussing CRM problems",
        "keywords": ["CRM problems", "sales pipeline issues", "lead tracking"],
        "sources": ["reddit", "hackernews"],
        "max_mentions": 10,
        "monitoring_focus": "pain_point_detection"
    }
    
    print("\n🧪 Test 2: Pain Point Detection")
    print("-" * 40)
    result_2 = await agent.run(test_state_2)
    
    print(f"✅ Success: {result_2.get('monitoring_success')}")
    print(f"📊 Mentions found: {result_2.get('mentions_found')}")
    print(f"🔍 Pain points detected: {len(result_2.get('pain_points_detected', []))}")
    
    if result_2.get('pain_points_detected'):
        print("📋 Sample pain points:")
        for pain_point in result_2['pain_points_detected'][:3]:
            print(f"  • {pain_point}")
    
    # Test Case 3: Competitor tracking
    test_state_3 = {
        "monitoring_goal": "Track competitor mentions and sentiment",
        "competitor_keywords": ["HubSpot", "Salesforce", "Pipedrive"],
        "sources": ["reddit", "hackernews"],
        "max_mentions": 15,
        "monitoring_focus": "competitor_analysis"
    }
    
    print("\n🧪 Test 3: Competitor Tracking")
    print("-" * 40)
    result_3 = await agent.run(test_state_3)
    
    print(f"✅ Success: {result_3.get('monitoring_success')}")
    print(f"📊 Mentions found: {result_3.get('mentions_found')}")
    print(f"🏢 Competitor mentions: {result_3.get('competitor_mentions', {})}")
    
    if result_3.get('recommended_actions'):
        print("💡 Recommendations:")
        for action in result_3['recommended_actions'][:3]:
            print(f"  • {action}")
    
    print("\n" + "=" * 60)
    print("🎯 Social Listening Agent direct testing complete")
    
    return result_1, result_2, result_3


async def test_social_components():
    """Test individual social listening components."""
    print("\n🧪 Testing Social Listening Components")
    print("-" * 40)
    
    from departments.social_intelligence.utils.sentiment_analyzer import SentimentAnalyzer
    from departments.social_intelligence.utils.alert_manager import AlertManager
    from departments.social_intelligence.models.social_models import SocialMention, SocialSource
    
    # Test sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    test_contents = [
        "This product is amazing! Love how easy it is to use.",
        "Having trouble with this software. It's too complicated.",
        "Looking for alternatives to HubSpot. Current solution is expensive.",
        "Just launched our new feature. Excited to see user feedback."
    ]
    
    print("😊 Sentiment Analysis:")
    for content in test_contents:
        sentiment, score = analyzer._basic_sentiment_analysis(content)
        print(f"  '{content[:30]}...': {sentiment.value} ({score:.2f})")
    
    # Test alert manager
    alert_manager = AlertManager()
    
    # Create test mentions
    test_mentions = [
        SocialMention(
            content="This CRM is terrible! Worst customer service ever.",
            title="Frustrated with current CRM",
            url="https://reddit.com/test1",
            author="frustrated_user",
            source=SocialSource.REDDIT,
            platform_id="test1",
            upvotes=15,
            comments_count=8
        ),
        SocialMention(
            content="Love this new marketing tool! Game changer for our team.",
            title="Great marketing automation tool",
            url="https://reddit.com/test2", 
            author="happy_marketer",
            source=SocialSource.REDDIT,
            platform_id="test2",
            upvotes=25,
            comments_count=12
        )
    ]
    
    # Add sentiment to test mentions
    for mention in test_mentions:
        mention.sentiment, mention.sentiment_score = analyzer._basic_sentiment_analysis(mention.content)
    
    print(f"\n🚨 Alert Generation:")
    alerts = alert_manager.generate_alerts(test_mentions)
    print(f"  Generated {len(alerts)} alerts from {len(test_mentions)} test mentions")
    
    for alert in alerts:
        print(f"  • {alert.alert_type}: {alert.alert_reason} (priority: {alert.priority_score:.2f})")


if __name__ == "__main__":
    asyncio.run(test_social_listening_direct())
    asyncio.run(test_social_components())
