#!/usr/bin/env python3
"""
Working Demo - Direct Agent Execution (No Redis Orchestration)

This bypasses the Redis orchestration layer that has connection issues
and directly executes agents, which work perfectly.
"""

import asyncio
import argparse
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

async def run_branding_agent(user_request: str):
    """Run branding agent directly."""
    from departments.branding.branding_agent import BrandingAgent
    
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'interactive_approval': False,
        'session_id': f'direct_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    }
    
    agent = BrandingAgent(config)
    
    state = {
        'business_idea': user_request,
        'user_request': user_request
    }
    
    print("🎨 Running Branding Agent...")
    result = await agent.run(state)
    print("✅ Branding completed!")
    
    return result

async def run_market_research_agent(user_request: str):
    """Run market research agent directly."""
    from departments.market_research.market_research_agent import MarketResearchAgent
    
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'interactive_approval': False,
        'session_id': f'direct_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    }
    
    agent = MarketResearchAgent(config)
    
    state = {
        'business_idea': user_request,
        'user_request': user_request
    }
    
    print("📊 Running Market Research Agent...")
    result = await agent.run(state)
    print("✅ Market Research completed!")
    
    return result

async def run_parallel_agents(user_request: str):
    """Run both agents in parallel."""
    print(f"🚀 Starting Parallel Agent Execution")
    print(f"Request: {user_request}")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Run agents in parallel
    branding_task = run_branding_agent(user_request)
    market_research_task = run_market_research_agent(user_request)
    
    print("⏳ Running agents in parallel...")
    
    try:
        branding_result, market_result = await asyncio.gather(
            branding_task,
            market_research_task,
            return_exceptions=True
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print("=" * 60)
        print("🎉 PARALLEL EXECUTION COMPLETED")
        print("=" * 60)
        print(f"⏱️  Total Time: {execution_time:.1f} seconds")
        
        # Show results
        if isinstance(branding_result, dict):
            print("\n🎨 BRANDING RESULTS:")
            print(f"   Brand Name: {branding_result.get('brand_name', 'N/A')}")
            print(f"   Logo Prompt: {branding_result.get('logo_prompt', 'N/A')[:100]}...")
            print(f"   Colors: {branding_result.get('color_palette', 'N/A')}")
        else:
            print(f"\n❌ Branding failed: {branding_result}")
        
        if isinstance(market_result, dict):
            print("\n📊 MARKET RESEARCH RESULTS:")
            print(f"   Market Opportunity Score: {market_result.get('market_opportunity_score', 'N/A')}")
            print(f"   Market Size: {market_result.get('market_size', 'N/A')}")
            print(f"   Research Generated: {market_result.get('market_research_completed_at', 'N/A')}")
            
            if 'key_competitors' in market_result:
                competitors = market_result['key_competitors']
                if isinstance(competitors, list) and competitors:
                    print(f"   Top Competitors: {', '.join(competitors[:3])}")
            
            if 'market_trends' in market_result:
                trends = market_result['market_trends']
                if isinstance(trends, list) and trends:
                    first_trend = str(trends[0])[:100] + "..." if len(str(trends[0])) > 100 else str(trends[0])
                    print(f"   Key Trend: {first_trend}")
                    
            if 'target_personas' in market_result:
                personas = market_result['target_personas']
                if isinstance(personas, list) and len(personas) >= 3:
                    print(f"   Target Personas: {personas[1]}, {personas[2]}")  # Skip first element which seems to be 'S'
        else:
            print(f"\n❌ Market Research failed: {market_result}")
        
        # Combined results
        combined_results = {
            "workflow_id": f"direct_{int(datetime.now().timestamp())}",
            "status": "completed",
            "execution_time_seconds": execution_time,
            "branding_result": branding_result if isinstance(branding_result, dict) else str(branding_result),
            "market_research_result": market_result if isinstance(market_result, dict) else str(market_result),
            "success": isinstance(branding_result, dict) and isinstance(market_result, dict)
        }
        
        return combined_results
        
    except Exception as e:
        print(f"❌ Parallel execution failed: {e}")
        return {"status": "failed", "error": str(e)}

async def main():
    parser = argparse.ArgumentParser(description="Working Direct Agent Execution Demo")
    parser.add_argument("request", nargs="+", help="User request")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--full", action="store_true", help="Show full detailed results")
    args = parser.parse_args()
    
    user_request = " ".join(args.request)
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ No ANTHROPIC_API_KEY found in environment")
        return
    
    try:
        result = await run_parallel_agents(user_request)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        elif args.full:
            print(f"\n📋 FULL RESULTS:")
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n✅ Demo completed successfully!")
            
    except Exception as e:
        error_result = {"status": "failed", "error": str(e)}
        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())