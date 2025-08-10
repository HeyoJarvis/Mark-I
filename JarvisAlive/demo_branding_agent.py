#!/usr/bin/env python3
"""
Demo script for BrandingAgent

Shows how to use the BrandingAgent to generate branding assets
for different business ideas.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent


def demo_branding_generation():
    """Demonstrate branding generation for different business ideas"""
    
    print("🎨 BrandingAgent Demo")
    print("=" * 50)
    
    # Initialize the agent
    agent = BrandingAgent()
    print("✅ BrandingAgent initialized")
    
    # Demo business ideas
    business_ideas = [
        {
            "name": "Premium Pen Brand",
            "state": {
                "business_idea": "I want to start a premium pen brand that focuses on luxury writing instruments for professionals and collectors.",
                "product_type": "pens",
                "target_audience": "professionals and collectors",
                "industry": "luxury goods"
            }
        },
        {
            "name": "Eco-Friendly Water Bottles",
            "state": {
                "business_idea": "Creating sustainable, reusable water bottles made from recycled materials to reduce plastic waste.",
                "product_type": "water bottles",
                "target_audience": "environmentally conscious consumers",
                "industry": "sustainability"
            }
        },
        {
            "name": "AI-Powered Fitness App",
            "state": {
                "business_idea": "Developing a mobile app that uses AI to create personalized workout plans and track fitness progress.",
                "product_type": "mobile app",
                "target_audience": "fitness enthusiasts",
                "industry": "health and technology"
            }
        },
        {
            "name": "Artisan Coffee Subscription",
            "state": {
                "business_idea": "Launching a premium coffee subscription service that delivers freshly roasted beans from local roasters.",
                "product_type": "coffee subscription",
                "target_audience": "coffee enthusiasts",
                "industry": "food and beverage"
            }
        }
    ]
    
    # Process each business idea
    for i, idea in enumerate(business_ideas, 1):
        print(f"\n📋 Business Idea {i}: {idea['name']}")
        print("-" * 40)
        
        # Generate branding
        result_state = agent.run(idea['state'])
        
        # Display results
        print(f"🎯 Brand Name: {result_state.get('brand_name', 'N/A')}")
        print(f"🎨 Logo Prompt: {result_state.get('logo_prompt', 'N/A')}")
        print(f"🌈 Color Palette: {result_state.get('color_palette', [])}")
        print(f"🌐 Domain Suggestions: {result_state.get('domain_suggestions', [])}")
        print(f"⏰ Generated At: {result_state.get('branding_generated_at', 'N/A')}")
        
        # Show JSON output
        print(f"\n📄 Full JSON Output:")
        print(json.dumps(result_state, indent=2))
        
        print("\n" + "="*50)


def demo_error_handling():
    """Demonstrate error handling"""
    print("\n🛡️ Error Handling Demo")
    print("=" * 50)
    
    agent = BrandingAgent()
    
    # Test with empty state
    print("\n📋 Test: Empty State")
    empty_state = {}
    result = agent.run(empty_state)
    print(f"✅ Result: {result == empty_state}")
    
    # Test with minimal state
    print("\n📋 Test: Minimal State")
    minimal_state = {"business_idea": "Test business"}
    result = agent.run(minimal_state)
    print(f"✅ Has brand_name: {'brand_name' in result}")
    print(f"✅ Has logo_prompt: {'logo_prompt' in result}")
    print(f"✅ Has color_palette: {'color_palette' in result}")


def demo_ai_vs_fallback():
    """Demonstrate AI vs fallback mode"""
    print("\n🤖 AI vs Fallback Mode Demo")
    print("=" * 50)
    
    # Test with AI engine (if available)
    print("\n📋 Test: With AI Engine")
    agent_with_ai = BrandingAgent(config={'anthropic_api_key': 'test_key'})
    state = {"business_idea": "Premium pen brand", "product_type": "pens"}
    result_ai = agent_with_ai.run(state)
    print(f"✅ AI Mode Result: {result_ai.get('brand_name', 'N/A')}")
    
    # Test with fallback
    print("\n📋 Test: Fallback Mode")
    agent_fallback = BrandingAgent(config={})
    result_fallback = agent_fallback.run(state)
    print(f"✅ Fallback Mode Result: {result_fallback.get('brand_name', 'N/A')}")


if __name__ == "__main__":
    try:
        demo_branding_generation()
        demo_error_handling()
        demo_ai_vs_fallback()
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 To use with real AI, set the ANTHROPIC_API_KEY environment variable:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 