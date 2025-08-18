#!/usr/bin/env python3
"""
Demo script for WebsiteGeneratorAgent

Shows how to use the WebsiteGeneratorAgent to generate website structure,
content, and design for different business types.
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env automatically
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.website.website_generator_agent import WebsiteGeneratorAgent


async def demo_website_generation():
    """Demonstrate website generation for different business types"""
    
    print("🌐 WebsiteGeneratorAgent Demo")
    print("=" * 60)
    
    # Initialize the agent
    agent = WebsiteGeneratorAgent()
    print("✅ WebsiteGeneratorAgent initialized")
    
    # Demo business scenarios
    business_scenarios = [
        {
            "name": "Coffee Shop",
            "state": {
                "brand_name": "BrewCraft Coffee",
                "business_idea": "Artisanal coffee shop specializing in locally roasted beans and handcrafted beverages",
                "color_palette": ["#8B4513", "#D2691E", "#F5DEB3", "#FFFFFF"],
                "target_audience": "coffee enthusiasts and remote workers",
                "industry": "food and beverage"
            }
        },
        {
            "name": "Tech Startup",
            "state": {
                "brand_name": "DataFlow AI",
                "business_idea": "AI-powered data analytics platform for small businesses",
                "color_palette": ["#1F2937", "#3B82F6", "#10B981", "#F59E0B"],
                "target_audience": "small business owners and data analysts",
                "industry": "technology"
            }
        },
        {
            "name": "Eco Products",
            "state": {
                "brand_name": "GreenLife",
                "business_idea": "Sustainable household products made from recycled materials",
                "color_palette": ["#2D5A27", "#4A7C59", "#8FBC8F", "#F0FFF0"],
                "target_audience": "environmentally conscious families",
                "industry": "sustainability",
                "pages": ["Home", "Products", "About", "Sustainability", "Contact", "Shop"]
            }
        },
        {
            "name": "Fitness Studio",
            "state": {
                "brand_name": "FitZone Studio",
                "business_idea": "Modern fitness studio offering personal training and group classes",
                "color_palette": ["#FF6B35", "#F7931E", "#FFD23F", "#06FFA5"],
                "target_audience": "fitness enthusiasts and busy professionals",
                "industry": "health and fitness",
                "website_type": "service"
            }
        }
    ]
    
    # Process each business scenario
    for i, scenario in enumerate(business_scenarios, 1):
        print(f"\n🏢 Business Scenario {i}: {scenario['name']}")
        print("-" * 50)
        
        try:
            # Generate website
            result_state = await agent.run(scenario['state'])
            
            # Display key results
            print(f"✅ Website generated successfully!")
            print(f"🎯 Brand: {result_state.get('brand_name', 'N/A')}")
            print(f"📄 Pages: {', '.join(result_state.get('sitemap', []))}")
            print(f"🎨 SEO Title: {result_state.get('homepage', {}).get('seo_title', 'N/A')}")
            
            # Show homepage hero section
            hero = result_state.get('homepage', {}).get('hero', {})
            if hero:
                print(f"🚀 Hero Headline: {hero.get('headline', 'N/A')}")
                print(f"📝 Hero Subheadline: {hero.get('subheadline', 'N/A')}")
                print(f"🔘 Primary CTA: {hero.get('primary_cta', 'N/A')}")
            
            # Show style guide
            style_guide = result_state.get('style_guide', {})
            if style_guide:
                tone = style_guide.get('tone_of_voice', {})
                print(f"🎭 Brand Personality: {tone.get('personality', 'N/A')}")
            
            # Show website structure summary
            structure = result_state.get('website_structure', [])
            if structure:
                home_page = structure[0] if structure else {}
                sections = home_page.get('sections', [])
                print(f"📋 Homepage Sections: {len(sections)} sections")
                for section in sections[:3]:  # Show first 3 sections
                    print(f"   • {section.get('id', 'Unknown')}: {section.get('type', 'Unknown type')}")
            
            print(f"⏰ Generated At: {result_state.get('website_generated_at', 'N/A')}")
            
            # Optionally save full output to file
            if i == 1:  # Save first example for inspection
                output_file = f"website_demo_output_{scenario['name'].lower().replace(' ', '_')}.json"
                with open(output_file, 'w') as f:
                    json.dump(result_state, f, indent=2, default=str)
                print(f"💾 Full output saved to: {output_file}")
        
        except Exception as e:
            print(f"❌ Error generating website: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)


async def demo_direct_agent_usage():
    """Show direct agent usage patterns"""
    print("\n🔧 Direct Agent Usage Examples")
    print("=" * 60)
    
    agent = WebsiteGeneratorAgent()
    
    # Example 1: Minimal input
    print("\n📋 Example 1: Minimal Input")
    minimal_state = {
        "business_idea": "Online tutoring platform for high school students"
    }
    result = await agent.run(minimal_state)
    print(f"✅ Generated {len(result.get('sitemap', []))} pages")
    print(f"🎯 SEO Title: {result.get('homepage', {}).get('seo_title', 'N/A')}")
    
    # Example 2: With branding context
    print("\n📋 Example 2: With Branding Context")
    branded_state = {
        "brand_name": "TechLearn",
        "business_idea": "Online tutoring platform for high school students",
        "color_palette": ["#4F46E5", "#06B6D4", "#10B981"],
        "logo_prompt": "Modern graduation cap with digital elements"
    }
    result = await agent.run(branded_state)
    print(f"✅ Generated {len(result.get('sitemap', []))} pages")
    print(f"🎨 Brand Colors: {', '.join(result.get('style_guide', {}).get('colors', []))}")


async def demo_error_handling():
    """Demonstrate error handling"""
    print("\n🛡️ Error Handling Demo")
    print("=" * 60)
    
    agent = WebsiteGeneratorAgent()
    
    # Test with empty state
    print("\n📋 Test: Empty State")
    empty_state = {}
    result = await agent.run(empty_state)
    print(f"✅ Handled empty state gracefully: {result == empty_state}")
    
    # Test with minimal valid state
    print("\n📋 Test: Minimal Valid State")
    minimal_state = {"business_idea": "Test business"}
    result = await agent.run(minimal_state)
    print(f"✅ Has sitemap: {'sitemap' in result}")
    print(f"✅ Has homepage: {'homepage' in result}")
    print(f"✅ Has style_guide: {'style_guide' in result}")


async def demo_integration_patterns():
    """Show how the agent integrates with the orchestration system"""
    print("\n🔗 Integration Patterns")
    print("=" * 60)
    
    print("1. 🌐 Through Universal Orchestrator:")
    print("   Query: 'Create a landing page for my eco bottle brand'")
    print("   → Routes to Branding Orchestrator")
    print("   → Detects website keywords")
    print("   → Invokes WebsiteGeneratorAgent")
    print("   → Returns formatted response")
    
    print("\n2. 🎨 Through Branding Orchestrator:")
    print("   Query: 'Build a website for my coffee shop'")
    print("   → Branding orchestrator detects website request")
    print("   → Extracts business context")
    print("   → Calls website generator with context")
    
    print("\n3. 🤖 Direct Agent Invocation:")
    print("   AgentExecutor.invoke_agent('website_generator_agent', state)")
    print("   → Direct execution with full control")
    
    print("\n4. 🧠 Intelligence Layer Integration:")
    print("   WorkflowBrain can include website generation as a step")
    print("   → Multi-step workflows with HITL approval")
    print("   → Autopilot vs human control")


async def main():
    try:
        await demo_website_generation()
        await demo_direct_agent_usage()
        await demo_error_handling()
        await demo_integration_patterns()
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. Run the main system: python main.py")
        print("   2. Try branding mode: python main.py --branding")
        print("   3. Try intelligence layer: python main.py --intelligence")
        print("   4. Use queries like:")
        print("      • 'Create a website for my bakery'")
        print("      • 'Build a landing page for my SaaS product'")
        print("      • 'Generate a sitemap for my online store'")
        
        print("\n🔧 Environment Setup:")
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print("   ✅ ANTHROPIC_API_KEY is configured")
        else:
            print("   ⚠️  ANTHROPIC_API_KEY not found - agent will use fallback mode")
            print("   💡 Set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 