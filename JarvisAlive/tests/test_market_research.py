#!/usr/bin/env python3
"""Test Market Research Agent with coffee shop example."""

import asyncio
import os
import sys
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.market_research.market_research_agent import MarketResearchAgent

console = Console()

async def test_market_research():
    """Test market research agent with coffee shop example."""
    try:
        # Initialize agent
        console.print("🔍 Initializing Market Research Agent...")
        agent = MarketResearchAgent()
        
        # Create test input state (simulating from branding workflow)
        test_state = {
            'business_idea': 'A specialty coffee shop focusing on ethically sourced beans with a cozy atmosphere for remote workers',
            'business_type': 'coffee shop',
            'brand_name': 'Brew Haven',
            'target_market': 'remote workers, coffee enthusiasts, students',
            'location': 'urban downtown area',
            'price_range': 'premium',
            'unique_selling_proposition': 'ethically sourced beans, cozy workspace atmosphere',
            'market_research_requested': True
        }
        
        console.print("\n📊 Testing Market Research Agent")
        console.print(f"Business: {test_state['brand_name']} - {test_state['business_type']}")
        console.print(f"Idea: {test_state['business_idea']}")
        console.print()
        
        # Run market research
        console.print("🔄 Running market research analysis...")
        result = await agent.run(test_state)
        
        console.print("\n📋 Market Research Results:")
        console.print(f"✅ Success: {result.get('market_research_success', False)}")
        
        # Display market research result details
        research_result = result.get('market_research_result')
        if research_result and isinstance(research_result, dict):
            console.print(f"\n🏢 Market Size: {research_result.get('market_size', 'N/A')}")
            console.print(f"📊 Opportunity Score: {research_result.get('market_opportunity_score', 'N/A')}")
            console.print(f"🎯 Confidence: {research_result.get('confidence_score', 'N/A')}")
            console.print(f"📅 Research Date: {research_result.get('research_date', 'N/A')}")
            
            # Executive Summary
            exec_summary = research_result.get('executive_summary', {})
            if exec_summary:
                console.print(f"\n📄 Executive Summary:")
                console.print(f"  • Market Opportunity: {exec_summary.get('market_opportunity', 'N/A')}")
                console.print(f"  • Competition Level: {exec_summary.get('competition_level', 'N/A')}")
                console.print(f"  • Success Probability: {exec_summary.get('success_probability', 'N/A')}")
            
            # Market Landscape
            market_landscape = research_result.get('market_landscape', {})
            if market_landscape:
                console.print(f"\n🌍 Market Landscape:")
                console.print(f"  • Industry Size: {market_landscape.get('industry_size', 'N/A')}")
                console.print(f"  • Growth Rate: {market_landscape.get('growth_rate', 'N/A')}")
                
                # Market segments
                segments = market_landscape.get('segments', [])
                if segments:
                    console.print(f"  • Key Segments: {len(segments)} identified")
                    for i, segment in enumerate(segments[:3], 1):
                        if isinstance(segment, dict):
                            console.print(f"    {i}. {segment.get('name', 'N/A')} - {segment.get('size_percentage', 'N/A')}%")
            
            # Competitive Analysis
            competitive_analysis = research_result.get('competitive_analysis', {})
            if competitive_analysis:
                console.print(f"\n⚔️ Competitive Analysis:")
                console.print(f"  • Competition Intensity: {competitive_analysis.get('intensity_level', 'N/A')}")
                
                competitors = competitive_analysis.get('key_competitors', [])
                if competitors:
                    console.print(f"  • Key Competitors: {len(competitors)} identified")
                    for i, competitor in enumerate(competitors[:3], 1):
                        if isinstance(competitor, dict):
                            console.print(f"    {i}. {competitor.get('name', 'N/A')} - {competitor.get('market_share', 'N/A')} share")
            
            # Customer Insights
            customer_insights = research_result.get('customer_insights', {})
            if customer_insights:
                console.print(f"\n👥 Customer Insights:")
                
                personas = customer_insights.get('target_personas', [])
                if personas:
                    console.print(f"  • Target Personas: {len(personas)} identified")
                    for i, persona in enumerate(personas[:2], 1):
                        if isinstance(persona, dict):
                            console.print(f"    {i}. {persona.get('name', 'N/A')} - {persona.get('demographic', 'N/A')}")
            
            # Strategic Recommendations
            recommendations = research_result.get('strategic_recommendations', {})
            if recommendations:
                console.print(f"\n💡 Strategic Recommendations:")
                
                opportunities = recommendations.get('key_opportunities', [])
                if opportunities:
                    console.print(f"  • Key Opportunities:")
                    for i, opp in enumerate(opportunities[:3], 1):
                        console.print(f"    {i}. {opp}")
                
                risks = recommendations.get('potential_risks', [])
                if risks:
                    console.print(f"  • Potential Risks:")
                    for i, risk in enumerate(risks[:3], 1):
                        console.print(f"    {i}. {risk}")
        
        # Show file output if available
        if result.get('market_research_file_path'):
            console.print(f"\n📁 Research report saved: {result.get('market_research_file_path')}")
        
        console.print(f"\n🎉 Market research test completed successfully!")
        
        return result
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_market_research())