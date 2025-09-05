"""Test Content Marketing Agent directly."""

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

from departments.content_marketing.content_marketing_agent import ContentMarketingAgent


async def test_content_marketing_direct():
    """Test Content Marketing Agent with direct execution."""
    
    print("🧪 Testing Content Marketing Agent - Direct Execution")
    print("=" * 60)
    
    # Create agent with config
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'wordpress': {
            'wordpress_site_url': os.getenv('WORDPRESS_SITE_URL', ''),
            'wordpress_username': os.getenv('WORDPRESS_USERNAME', ''),
            'wordpress_app_password': os.getenv('WORDPRESS_APP_PASSWORD', '')
        }
    }
    
    agent = ContentMarketingAgent(config)
    
    # Test Case 1: Content Gap Analysis
    test_state_1 = {
        "content_goal": "Identify content gaps for SaaS business",
        "business_context": {
            "business_type": "SaaS",
            "industry": "Marketing Technology", 
            "target_audience": "Small business owners",
            "business_goal": "Generate leads through content marketing"
        },
        "operation_type": "gap_analysis",
        "target_keywords": ["CRM software", "marketing automation", "lead generation"],
        "content_preferences": {
            "content_types": ["blog_post", "case_study"],
            "posting_frequency": "weekly",
            "content_length": "long_form"
        }
    }
    
    print("\n🧪 Test 1: Content Gap Analysis")
    print("-" * 40)
    result_1 = await agent.run(test_state_1)
    
    print(f"✅ Success: {result_1.get('content_marketing_success')}")
    print(f"📊 Content gaps identified: {len(result_1.get('content_gaps_identified', []))}")
    print(f"📈 Estimated monthly traffic: {result_1.get('estimated_monthly_traffic', 0)}")
    print(f"🎯 Priority actions: {len(result_1.get('priority_actions', []))}")
    
    if result_1.get('content_gaps_identified'):
        gap = result_1['content_gaps_identified'][0]
        print(f"📋 Top gap: {gap.get('topic', 'N/A')}")
        print(f"🔍 Keywords: {gap.get('target_keywords', [])}")
        print(f"⭐ Score: {gap.get('gap_score', 0):.2f}")
    
    # Test Case 2: SEO Optimization
    test_state_2 = {
        "content_goal": "Optimize existing content for better SEO performance",
        "operation_type": "seo_optimization",
        "business_context": {
            "business_type": "SaaS",
            "industry": "Technology"
        }
    }
    
    print("\n🧪 Test 2: SEO Optimization")
    print("-" * 40)
    result_2 = await agent.run(test_state_2)
    
    print(f"✅ Success: {result_2.get('content_marketing_success')}")
    print(f"📊 Content pieces analyzed: {result_2.get('total_content_pieces', 0)}")
    print(f"📈 Average SEO score: {result_2.get('avg_seo_score', 0):.2f}")
    print(f"🔧 SEO improvements: {len(result_2.get('seo_improvements', []))}")
    
    if result_2.get('seo_improvements'):
        print("💡 Top SEO improvements:")
        for improvement in result_2['seo_improvements'][:3]:
            print(f"  • {improvement}")
    
    # Test Case 3: Content Calendar Planning
    test_state_3 = {
        "content_goal": "Create 12-week content calendar",
        "business_context": {
            "business_type": "Marketing Software",
            "industry": "SaaS",
            "target_audience": "Marketing managers"
        },
        "operation_type": "calendar_planning",
        "target_keywords": ["email marketing", "lead nurturing", "marketing automation"],
        "content_preferences": {
            "posting_frequency": "weekly",
            "content_types": ["blog_post", "case_study", "whitepaper"]
        }
    }
    
    print("\n🧪 Test 3: Content Calendar Planning")
    print("-" * 40)
    result_3 = await agent.run(test_state_3)
    
    print(f"✅ Success: {result_3.get('content_marketing_success')}")
    
    if result_3.get('content_calendar_created'):
        calendar = result_3['content_calendar_created']
        print(f"📅 Calendar created: {calendar.get('calendar_name', 'N/A')}")
        print(f"📊 Total pieces planned: {calendar.get('total_pieces_planned', 0)}")
        print(f"📈 Pieces per week: {calendar.get('pieces_per_week', 0):.1f}")
        print(f"🎯 Monthly traffic goal: {calendar.get('monthly_traffic_goal', 0)}")
        print(f"🔍 Target keywords: {calendar.get('target_keywords_count', 0)}")
    
    if result_3.get('content_recommendations'):
        print("💡 Content recommendations:")
        for rec in result_3['content_recommendations'][:3]:
            print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    print("🎯 Content Marketing Agent direct testing complete")
    
    return result_1, result_2, result_3


async def test_content_components():
    """Test individual content marketing components."""
    print("\n🧪 Testing Content Marketing Components")
    print("-" * 40)
    
    from departments.content_marketing.utils.seo_analyzer import SEOAnalyzer
    from departments.content_marketing.utils.content_gap_analyzer import ContentGapAnalyzer
    from departments.content_marketing.models.content_models import Content, ContentType
    
    # Test SEO analyzer
    seo_analyzer = SEOAnalyzer()
    
    test_content = Content(
        title="How to Choose the Best CRM for Your Business",
        content_type=ContentType.BLOG_POST,
        content_body="Choosing the right CRM software is crucial for business success. A good CRM helps you manage customer relationships, track sales, and improve customer satisfaction. In this comprehensive guide, we'll explore the key features to look for in CRM software and compare the top options available.",
        meta_description="Learn how to choose the best CRM software for your business with our comprehensive guide.",
        target_keywords=["CRM software", "best CRM", "CRM comparison"],
        focus_keyword="CRM software",
        slug="how-to-choose-best-crm-business"
    )
    
    print("🔍 SEO Analysis:")
    seo_analysis = await seo_analyzer.analyze_content_seo(test_content)
    print(f"  Overall SEO Score: {seo_analysis.overall_seo_score:.2f}")
    print(f"  Keyword Density: {seo_analysis.keyword_density:.1f}%")
    print(f"  Readability Score: {seo_analysis.readability_score:.2f}")
    print(f"  Ranking Potential: {seo_analysis.ranking_potential:.2f}")
    
    # Test content gap analyzer
    gap_analyzer = ContentGapAnalyzer()
    
    business_context = {
        "business_type": "SaaS",
        "industry": "Marketing Technology",
        "target_audience": "Small business owners"
    }
    
    print(f"\n📊 Content Gap Analysis:")
    content_gaps = await gap_analyzer.identify_content_gaps(business_context, ["CRM", "marketing automation"])
    print(f"  Gaps identified: {len(content_gaps)}")
    
    if content_gaps:
        top_gap = content_gaps[0]
        print(f"  Top gap: {top_gap.topic}")
        print(f"  Gap score: {top_gap.gap_score:.2f}")
        print(f"  Priority: {top_gap.priority_level}")
        print(f"  Content type: {top_gap.content_type_recommendation.value}")


if __name__ == "__main__":
    asyncio.run(test_content_marketing_direct())
    asyncio.run(test_content_components())
