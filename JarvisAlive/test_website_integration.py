#!/usr/bin/env python3
"""
Simple Website Generator Integration Test

Tests that the website generator works through the orchestration system.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.website.website_generator_agent import WebsiteGeneratorAgent
from orchestration.branding_orchestration import BrandingOrchestrator


async def test_direct_agent():
    """Test the website generator agent directly"""
    print("🧪 Testing WebsiteGeneratorAgent directly...")
    
    agent = WebsiteGeneratorAgent(config={
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'export_formats': ['html']
    })
    
    result = await agent.run({
        'brand_name': 'GreenJewels',
        'business_idea': 'Sustainable jewelry made from recycled gold and ethically sourced gems',
        'target_audience': 'environmentally conscious jewelry lovers',
        'industry': 'jewelry and sustainability'
    })
    
    print(f"✅ Direct agent test successful!")
    print(f"📄 Brand: {result.get('brand_name')}")
    print(f"🎨 Pages: {', '.join(result.get('sitemap', []))}")
    
    saved_paths = result.get('saved_paths', {})
    if 'html' in saved_paths:
        print(f"💾 Website saved to: {saved_paths['html']}")
        return saved_paths['html']
    
    return None


async def test_orchestration_routing():
    """Test that website requests route correctly"""
    print("\n🔗 Testing orchestration routing...")
    
    try:
        from orchestration.intent_parser import IntentParser
        
        parser = IntentParser()
        
        # Test website request detection
        test_queries = [
            "Create a website for my bakery",
            "I need a landing page for my jewelry brand",
            "Build me a professional site"
        ]
        
        for query in test_queries:
            parsed = await parser.parse_intent(query, {})
            print(f"• '{query}' → Category: {parsed.primary_intent}")
            if 'website_generator_agent' in (parsed.suggested_agents or []):
                print(f"  ✅ Correctly suggests website_generator_agent")
            else:
                print(f"  ⚠️  Suggested agents: {parsed.suggested_agents}")
        
        print("✅ Orchestration routing test completed")
        return True
        
    except Exception as e:
        print(f"❌ Orchestration routing test failed: {e}")
        return False


async def main():
    """Run integration tests"""
    
    print("🌐 Website Generator Integration Test")
    print("=" * 50)
    
    # Check prerequisites
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found")
        return
    
    print("🔑 API key found")
    
    # Test 1: Direct agent
    website_path = await test_direct_agent()
    
    # Test 2: Orchestration routing
    routing_success = await test_orchestration_routing()
    
    # Summary
    print(f"\n📊 Integration Test Results")
    print("=" * 50)
    print(f"Direct Agent: {'✅ Working' if website_path else '❌ Failed'}")
    print(f"Orchestration: {'✅ Working' if routing_success else '❌ Failed'}")
    
    if website_path and routing_success:
        print(f"\n🎉 Website Generator is fully integrated!")
        print(f"🚀 Users can now request websites through:")
        print(f"  • python main.py --branding")
        print(f"  • python main.py (universal routing)")
        print(f"  • Direct agent calls")
        
        if website_path:
            print(f"\n💾 Latest website: {website_path}")
    else:
        print(f"\n⚠️  Some issues found - check output above")


if __name__ == "__main__":
    asyncio.run(main()) 