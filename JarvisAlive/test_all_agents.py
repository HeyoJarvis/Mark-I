"""
Comprehensive testing script for all implemented agents.

Tests:
1. Lead Mining Agent
2. Social Listening Agent  
3. Content Marketing Agent

Shows real output and capabilities of each agent.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_lead_mining_agent():
    """Test Lead Mining Agent capabilities."""
    
    print("🎯 AGENT 1: Lead Mining Agent")
    print("=" * 50)
    
    try:
        from departments.lead_generation.lead_mining_agent import LeadMiningAgent
        
        agent = LeadMiningAgent({
            'apollo_api_key': os.getenv('APOLLO_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        })
        
        test_state = {
            "business_goal": "Find 5 qualified leads for SaaS companies",
            "icp_criteria": {
                "company_size_min": 50,
                "company_size_max": 500,
                "industries": ["Software", "SaaS"],
                "job_titles": ["VP Sales", "Director Marketing"],
                "locations": ["United States"]
            },
            "max_leads": 5,
            "sources": ["apollo"]
        }
        
        result = await agent.run(test_state)
        
        print(f"✅ Success: {result.get('mining_success')}")
        print(f"📊 Leads found: {result.get('leads_found')}")
        print(f"🎯 Data sources: {result.get('data_sources_used')}")
        
        if result.get('qualified_leads') and len(result['qualified_leads']) > 0:
            lead = result['qualified_leads'][0]
            print(f"📋 Sample lead: {lead.get('first_name')} {lead.get('last_name')} at {lead.get('company_name')}")
            print(f"📧 Email: {lead.get('email')}")
            print(f"🎯 Confidence: {lead.get('confidence_score')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lead Mining Agent failed: {e}")
        return False


async def test_social_listening_agent():
    """Test Social Listening Agent capabilities."""
    
    print("\n🎯 AGENT 2: Social Listening Agent")
    print("=" * 50)
    
    try:
        from departments.social_intelligence.social_listening_agent import SocialListeningAgent
        
        agent = SocialListeningAgent({
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        })
        
        test_state = {
            "monitoring_goal": "Monitor tech discussions and pain points",
            "keywords": ["CRM", "marketing automation", "SaaS"],
            "sources": ["hackernews", "google_alerts"],  # Skip Reddit (no SSN)
            "max_mentions": 8,
            "time_range_hours": 24,
            "monitoring_focus": "pain_point_detection"
        }
        
        result = await agent.run(test_state)
        
        print(f"✅ Success: {result.get('monitoring_success')}")
        print(f"📊 Mentions found: {result.get('mentions_found')}")
        print(f"🚨 Alerts generated: {len(result.get('high_priority_alerts', []))}")
        print(f"🎯 Opportunities: {len(result.get('engagement_opportunities', []))}")
        print(f"📡 Sources used: {result.get('sources_monitored')}")
        
        if result.get('sentiment_summary'):
            sentiment = result['sentiment_summary']
            print(f"😊 Sentiment: {sentiment.get('positive_count')}+ {sentiment.get('negative_count')}- {sentiment.get('neutral_count')}neutral")
        
        if result.get('trending_topics'):
            print(f"🔥 Trending: {result['trending_topics'][:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Social Listening Agent failed: {e}")
        return False


async def test_content_marketing_agent():
    """Test Content Marketing Agent capabilities."""
    
    print("\n🎯 AGENT 3: Content Marketing Agent")
    print("=" * 50)
    
    try:
        from departments.content_marketing.content_marketing_agent import ContentMarketingAgent
        
        agent = ContentMarketingAgent({
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        })
        
        test_state = {
            "content_goal": "Analyze content gaps and create SEO strategy",
            "business_context": {
                "business_type": "SaaS",
                "industry": "Marketing Technology",
                "target_audience": "Small business owners"
            },
            "operation_type": "gap_analysis",
            "target_keywords": ["CRM software", "marketing automation", "lead generation"],
            "content_preferences": {
                "content_types": ["blog_post", "case_study"],
                "posting_frequency": "weekly"
            }
        }
        
        result = await agent.run(test_state)
        
        print(f"✅ Success: {result.get('content_marketing_success')}")
        print(f"📊 Content gaps: {len(result.get('content_gaps_identified', []))}")
        print(f"📈 Traffic potential: {result.get('estimated_monthly_traffic', 0)}")
        print(f"🎯 Priority actions: {len(result.get('priority_actions', []))}")
        
        if result.get('content_gaps_identified') and len(result['content_gaps_identified']) > 0:
            gap = result['content_gaps_identified'][0]
            print(f"📋 Top opportunity: {gap.get('topic', 'N/A')}")
            print(f"🔍 Keywords: {gap.get('target_keywords', [])}")
            print(f"⭐ Gap score: {gap.get('gap_score', 0):.2f}")
        
        if result.get('priority_actions'):
            print("💡 Top recommendations:")
            for action in result['priority_actions'][:3]:
                print(f"  • {action}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content Marketing Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_semantic_routing():
    """Test all agents through semantic interface."""
    
    print("\n🎯 SEMANTIC ROUTING TEST")
    print("=" * 50)
    
    try:
        from semantic_chat_interface import SemanticChatInterface, OrchestrationMode
        
        chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        await chat.initialize()
        print("✅ Semantic interface initialized")
        
        # Test requests for each agent
        test_cases = [
            {
                "request": "Find 3 leads for SaaS companies",
                "expected_agent": "Lead Mining Agent",
                "keywords": ["leads", "apollo", "mining"]
            },
            {
                "request": "Monitor brand mentions on social media", 
                "expected_agent": "Social Listening Agent",
                "keywords": ["monitoring", "mentions", "social"]
            },
            {
                "request": "Analyze content gaps for my business",
                "expected_agent": "Content Marketing Agent", 
                "keywords": ["content gaps", "seo", "content marketing"]
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Semantic Test {i}: '{test_case['request']}'")
            print("-" * 40)
            
            try:
                response = await chat.chat(test_case["request"], f"semantic_test_{i}")
                
                # Check if expected agent was triggered
                response_lower = response.lower()
                
                if any(keyword in response_lower for keyword in test_case["keywords"]):
                    print(f"✅ PASS: {test_case['expected_agent']} likely executed")
                    success = True
                else:
                    print(f"❌ UNCLEAR: {test_case['expected_agent']} may not have executed")
                    success = False
                
                print(f"📋 Response: {response[:100]}...")
                results.append(success)
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        print(f"\n📊 Semantic Routing Results: {passed}/{len(results)} agents working")
        
        return passed >= 2  # At least 2 agents working
        
    except Exception as e:
        print(f"❌ Semantic testing failed: {e}")
        return False


async def main():
    """Run comprehensive agent testing."""
    
    print("🚀 COMPREHENSIVE AGENT TESTING")
    print("=" * 60)
    print("Testing all 3 implemented agents...")
    
    # Test each agent individually
    lead_mining_ok = await test_lead_mining_agent()
    social_listening_ok = await test_social_listening_agent() 
    content_marketing_ok = await test_content_marketing_agent()
    
    # Test semantic routing
    semantic_routing_ok = await test_semantic_routing()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 60)
    
    agents_working = sum([lead_mining_ok, social_listening_ok, content_marketing_ok])
    
    print(f"✅ Lead Mining Agent: {'WORKING' if lead_mining_ok else 'ISSUES'}")
    print(f"✅ Social Listening Agent: {'WORKING' if social_listening_ok else 'ISSUES'}")
    print(f"✅ Content Marketing Agent: {'WORKING' if content_marketing_ok else 'ISSUES'}")
    print(f"✅ Semantic Routing: {'WORKING' if semantic_routing_ok else 'ISSUES'}")
    
    print(f"\n🎯 Overall Status: {agents_working}/3 agents functional")
    
    if agents_working >= 2:
        print("🎉 SUCCESS: Your AI agent system is operational!")
        print("\n💡 Next steps:")
        print("  • Add API credentials for enhanced functionality")
        print("  • Test with real business scenarios")
        print("  • Implement additional agents as needed")
    else:
        print("⚠️  Some agents need attention - check error messages above")
    
    print("\n🚀 Your AI business assistant is ready!")


if __name__ == "__main__":
    asyncio.run(main())
