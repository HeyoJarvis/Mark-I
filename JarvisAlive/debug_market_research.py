#!/usr/bin/env python3
"""Debug market research agent JSON serialization issue."""

import asyncio
import os
import sys
import json
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.market_research.market_research_agent import MarketResearchAgent, CompetitorProfile

console = Console()

async def debug_serialization():
    """Debug the JSON serialization issue."""
    try:
        # Test basic serialization of our dataclasses
        console.print("🧪 Testing JSON serialization of dataclasses...")
        
        # Test CompetitorProfile
        competitor = CompetitorProfile(
            name="Test Competitor",
            website="test.com", 
            description="Test description"
        )
        
        console.print(f"CompetitorProfile created: {competitor.name}")
        
        # Test to_dict method
        competitor_dict = competitor.to_dict()
        console.print(f"CompetitorProfile to_dict: {type(competitor_dict)}")
        
        # Test JSON serialization of dict
        competitor_json = json.dumps(competitor_dict)
        console.print(f"✅ CompetitorProfile dict JSON serialization: OK")
        
        # Test direct JSON serialization (should fail)
        try:
            direct_json = json.dumps(competitor)
            console.print(f"❌ Direct CompetitorProfile serialization should have failed!")
        except TypeError as e:
            console.print(f"✅ Direct CompetitorProfile serialization correctly failed: {str(e)}")
        
        # Test the agent initialization
        console.print("\n🤖 Testing agent initialization...")
        agent = MarketResearchAgent()
        
        # Test parameter extraction
        test_state = {
            'business_idea': 'A specialty coffee shop',
            'business_type': 'coffee shop',
            'brand_name': 'Test Coffee'
        }
        
        params = agent._extract_research_params(test_state)
        console.print(f"✅ Parameters extracted: {params}")
        
        # Test JSON serialization of params
        try:
            params_json = json.dumps(params)
            console.print(f"✅ Parameters JSON serialization: OK")
        except TypeError as e:
            console.print(f"❌ Parameters JSON serialization failed: {str(e)}")
        
        console.print("\n🎉 Debug completed - basic serialization works!")
        
    except Exception as e:
        console.print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_serialization())