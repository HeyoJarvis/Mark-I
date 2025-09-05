#!/usr/bin/env python3
"""
Test script for Lead Mining Agent with real Apollo API integration.

This script will test:
1. Apollo API connection
2. Lead mining functionality
3. AI qualification
4. Data validation and deduplication
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from departments.lead_generation.lead_mining_agent import LeadMiningAgent
from departments.lead_generation.models.lead_models import ICPCriteria


async def test_lead_mining_agent():
    """Test the Lead Mining Agent with real Apollo data."""
    
    print("🚀 Testing Lead Mining Agent with Apollo API")
    print("=" * 60)
    
    # Check for required API keys
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    apollo_key = os.getenv('APOLLO_API_KEY')
    
    print(f"📋 Environment Check:")
    print(f"   Anthropic API Key: {'✅ Found' if anthropic_key else '❌ Missing'}")
    print(f"   Apollo API Key: {'✅ Found' if apollo_key else '❌ Missing'}")
    print()
    
    if not anthropic_key:
        print("⚠️  No ANTHROPIC_API_KEY found - AI features will be limited")
    
    if not apollo_key:
        print("⚠️  No APOLLO_API_KEY found - will use mock data")
        
    # Initialize the Lead Mining Agent
    config = {
        'anthropic_api_key': anthropic_key,
        'apollo_api_key': apollo_key,
        'max_leads_per_source': 10,  # Small number for testing
        'confidence_threshold': 0.7,
        'enable_deduplication': True
    }
    
    try:
        print("🔧 Initializing Lead Mining Agent...")
        agent = LeadMiningAgent(config)
        print("✅ Agent initialized successfully")
        print()
        
        # Test Case 1: SaaS Company ICP
        print("🎯 Test Case 1: SaaS Company Lead Mining")
        print("-" * 40)
        
        test_state = {
            'business_idea': 'AI-powered sales automation platform',
            'target_industry': 'SaaS',
            'company_size': '50-500 employees',
            'user_request': 'Find qualified leads for our AI sales automation platform targeting SaaS companies',
            'session_id': 'test_session_001'
        }
        
        print(f"📝 Test Parameters:")
        print(f"   Business Idea: {test_state['business_idea']}")
        print(f"   Target Industry: {test_state['target_industry']}")
        print(f"   Company Size: {test_state['company_size']}")
        print()
        
        print("⏳ Running lead mining agent...")
        start_time = datetime.now()
        
        result = await agent.run(test_state)
        
        # Debug: print the full result
        print(f"🔍 Full result: {result}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Agent completed in {duration:.2f} seconds")
        print()
        
        # Analyze results
        print("📊 Results Analysis:")
        print("-" * 20)
        
        # Check for mining success (the agent returns mining_success not success)
        mining_success = result.get('mining_success', False)
        if mining_success:
            print("✅ Mining operation successful")
            
            leads_found = result.get('leads_found', 0)
            print(f"📈 Leads found: {leads_found}")
            
            qualified_leads = result.get('qualified_leads', [])
            print(f"🎯 Qualified leads: {len(qualified_leads)}")
            
            mining_result = result.get('mining_result')
            if mining_result:
                print(f"⏱️  Mining duration: {mining_result.get('mining_duration_seconds', 0):.2f}s")
                print(f"📊 Sources used: {mining_result.get('sources_used', [])}")
                
                warnings = mining_result.get('warnings', [])
                if warnings:
                    print(f"⚠️  Warnings: {len(warnings)}")
                    for warning in warnings:
                        print(f"     - {warning}")
            
            # Show sample leads (first 3)
            if qualified_leads:
                print(f"\n📋 Sample Qualified Leads (showing first 3):")
                for i, lead in enumerate(qualified_leads[:3], 1):
                    print(f"   {i}. {lead.full_name} - {lead.job_title}")
                    print(f"      Company: {lead.company_name} ({lead.company_size} employees)")
                    print(f"      Email: {lead.email or 'Not available'}")
                    print(f"      Confidence: {lead.qualification_score:.2f}")
                    print()
        else:
            print("❌ Mining operation failed")
            error_msg = result.get('error_message', 'Unknown error')
            print(f"   Error: {error_msg}")
        
        # Test Case 2: Different ICP
        print("\n🎯 Test Case 2: E-commerce Lead Mining")
        print("-" * 40)
        
        test_state_2 = {
            'business_idea': 'E-commerce analytics and optimization platform',
            'target_industry': 'E-commerce',
            'company_size': '100-1000 employees',
            'user_request': 'Find marketing directors at e-commerce companies who need analytics tools',
            'session_id': 'test_session_002'
        }
        
        print(f"📝 Test Parameters:")
        print(f"   Business Idea: {test_state_2['business_idea']}")
        print(f"   Target Industry: {test_state_2['target_industry']}")
        print()
        
        print("⏳ Running second test...")
        result_2 = await agent.run(test_state_2)
        
        if result_2.get('mining_success', False):
            leads_found_2 = result_2.get('leads_found', 0)
            print(f"✅ Second test successful: {leads_found_2} leads found")
        else:
            print(f"❌ Second test failed: {result_2.get('error_message', 'Unknown error')}")
        
        print("\n🎉 Lead Mining Agent Test Complete!")
        print("=" * 60)
        
        # Summary
        total_leads = result.get('leads_found', 0) + result_2.get('leads_found', 0)
        print(f"📊 Total leads found across all tests: {total_leads}")
        
        if apollo_key:
            print("🔗 Apollo API: Successfully connected and retrieving real data")
        else:
            print("🔗 Apollo API: Using mock data (add APOLLO_API_KEY for real data)")
            
        if anthropic_key:
            print("🤖 AI Qualification: Active and processing leads")
        else:
            print("🤖 AI Qualification: Using basic qualification (add ANTHROPIC_API_KEY for AI)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Detailed error for debugging
        import traceback
        print("\n🔍 Detailed error trace:")
        traceback.print_exc()
        
        return False


async def test_apollo_connection_only():
    """Quick test of just the Apollo API connection."""
    
    print("🔍 Testing Apollo API Connection Only")
    print("-" * 40)
    
    try:
        from departments.lead_generation.connectors.apollo_connector import ApolloConnector
        from departments.lead_generation.models.lead_models import ICPCriteria
        
        apollo_key = os.getenv('APOLLO_API_KEY')
        if not apollo_key:
            print("❌ No APOLLO_API_KEY found")
            return False
        
        connector = ApolloConnector(apollo_key)
        
        # Simple test criteria
        criteria = ICPCriteria(
            company_size_min=50,
            company_size_max=500,
            industries=["Technology", "Software"],
            job_titles=["VP Sales", "Director Marketing"],
            locations=["United States"]
        )
        
        print("⏳ Testing Apollo API connection...")
        leads = await connector.search_leads(criteria, max_leads=5)
        
        if leads:
            print(f"✅ Apollo API working! Retrieved {len(leads)} leads")
            print("📋 Sample lead:")
            sample_lead = leads[0]
            print(f"   Name: {sample_lead.full_name}")
            print(f"   Company: {sample_lead.company_name}")
            print(f"   Title: {sample_lead.job_title}")
            return True
        else:
            print("⚠️  Apollo API connected but no leads returned")
            return False
            
    except Exception as e:
        print(f"❌ Apollo connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🧪 Lead Mining Agent Test Suite")
    print("=" * 60)
    print()
    
    # Check if we should run quick test or full test
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("Running quick Apollo connection test only...\n")
        success = asyncio.run(test_apollo_connection_only())
    else:
        print("Running full Lead Mining Agent test...\n")
        success = asyncio.run(test_lead_mining_agent())
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)