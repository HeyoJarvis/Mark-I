#!/usr/bin/env python3
"""
Debug the market research agent to find the string/dict issue
"""
import asyncio
import logging
import traceback
from orchestration.persistent.agents.persistent_market_research_agent import PersistentMarketResearchAgent

# Setup logging
logging.basicConfig(level=logging.INFO)

async def debug_market_research():
    """Debug market research agent methods"""
    
    agent = PersistentMarketResearchAgent("debug_agent", {
        'anthropic_api_key': 'test_key'
    })
    
    try:
        await agent.on_start()
        
        # Test each method individually
        print("Testing market opportunity analysis...")
        try:
            result1 = await agent._analyze_market_opportunity({
                'business_idea': 'setup a coffee shop business',
                'industry': 'General', 
                'location': 'Global'
            })
            print(f"Market opportunity result type: {type(result1)}")
            print(f"Market opportunity result: {result1}")
            
        except Exception as e:
            print(f"Market opportunity failed: {e}")
            traceback.print_exc()
        
        print("\nTesting competitive analysis...")
        try:
            result2 = await agent._analyze_competition({
                'business_idea': 'setup a coffee shop business',
                'industry': 'General',
                'location': 'Global'
            })
            print(f"Competitive analysis result type: {type(result2)}")
            print(f"Competitive analysis result: {result2}")
            
        except Exception as e:
            print(f"Competitive analysis failed: {e}")
            traceback.print_exc()
        
        print("\nTesting target audience research...")
        try:
            result3 = await agent._research_target_audience({
                'business_idea': 'setup a coffee shop business',
                'industry': 'General',
                'geographic_focus': 'Global'
            })
            print(f"Target audience result type: {type(result3)}")
            print(f"Target audience result: {result3}")
            
        except Exception as e:
            print(f"Target audience research failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"Agent setup failed: {e}")
        traceback.print_exc()
    
    await agent.on_stop()

if __name__ == "__main__":
    asyncio.run(debug_market_research())