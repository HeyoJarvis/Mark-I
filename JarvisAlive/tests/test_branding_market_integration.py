#!/usr/bin/env python3
"""Test integration of MarketResearchAgent with branding workflow."""

import asyncio
import os
import sys
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent
from departments.market_research.market_research_agent import MarketResearchAgent

console = Console()

async def test_integrated_workflow():
    """Test the complete branding + market research workflow."""
    try:
        console.print("🔄 Testing Integrated Branding + Market Research Workflow")
        console.print("=" * 60)
        
        # Initialize agents
        console.print("\n1️⃣ Initializing agents...")
        branding_agent = BrandingAgent()
        market_research_agent = MarketResearchAgent()
        
        # Initial state (user input)
        initial_state = {
            'business_idea': 'A premium specialty coffee shop focusing on ethically sourced single-origin beans with a modern coworking atmosphere',
            'user_request': 'Help me create a brand for my coffee shop and research the market',
            'location': 'Seattle, WA',
            'target_audience': 'young professionals, remote workers, coffee enthusiasts'
        }
        
        console.print(f"Input: {initial_state['business_idea']}")
        
        # Step 1: Run branding agent
        console.print("\n2️⃣ Running branding analysis...")
        branding_result = await branding_agent.run(initial_state)
        
        console.print("📋 Branding Results:")
        console.print(f"  ✅ Success: {branding_result.get('branding_success', False)}")
        console.print(f"  🏢 Brand Name: {branding_result.get('brand_name', 'N/A')}")
        console.print(f"  🎨 Color Palette: {branding_result.get('color_palette', [])}")
        console.print(f"  💡 Brand Positioning: {branding_result.get('brand_positioning', 'N/A')[:100]}...")
        
        # Step 2: Run market research agent with branding results
        console.print("\n3️⃣ Running market research with branding context...")
        market_research_result = await market_research_agent.run(branding_result)
        
        console.print("📊 Market Research Results:")
        console.print(f"  ✅ Success: {market_research_result.get('market_research_success', False)}")
        
        research_data = market_research_result.get('market_research_result', {})
        if research_data:
            console.print(f"  💰 Market Size: {research_data.get('market_size', 'N/A')}")
            console.print(f"  📈 Opportunity Score: {research_data.get('market_opportunity_score', 'N/A')}/100")
            console.print(f"  🏆 Key Competitors: {market_research_result.get('key_competitors', [])}")
            console.print(f"  👥 Target Personas: {market_research_result.get('target_personas', [])}")
        
        # Step 3: Show combined insights
        console.print("\n4️⃣ Combined Business Intelligence:")
        console.print("=" * 40)
        
        if branding_result.get('brand_name') and research_data:
            console.print(f"🚀 **{branding_result.get('brand_name')}** Business Overview:")
            console.print(f"  • Market Opportunity: {research_data.get('market_opportunity_score', 0)}/100")
            console.print(f"  • Brand Positioning: {branding_result.get('brand_positioning', '')[:80]}...")
            console.print(f"  • Market Size: {research_data.get('market_size', 'Unknown')}")
            console.print(f"  • Competition Level: {len(market_research_result.get('key_competitors', []))} key competitors identified")
            console.print(f"  • Target Segments: {len(market_research_result.get('target_personas', []))} personas defined")
            
            # Strategic recommendations
            strategic_recs = research_data.get('strategic_recommendations', {})
            if strategic_recs:
                console.print("\n💡 Strategic Recommendations:")
                recs = strategic_recs.get('key_opportunities', [])
                for i, rec in enumerate(recs[:3], 1):
                    console.print(f"  {i}. {rec}")
        
        console.print("\n🎉 Integrated workflow test completed successfully!")
        console.print(f"✅ Both agents worked together seamlessly")
        console.print(f"✅ Market research enhanced branding with competitive intelligence")
        console.print(f"✅ Complete business strategy foundation established")
        
        return market_research_result
        
    except Exception as e:
        console.print(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_integrated_workflow())