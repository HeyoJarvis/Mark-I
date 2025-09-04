#!/usr/bin/env python3
"""Test MarketResearchAgent in complete isolation - no orchestration."""

import asyncio
import os
import sys
from rich.console import Console

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.market_research.market_research_agent import MarketResearchAgent

console = Console()

async def test_basic_initialization():
    """Test basic agent initialization."""
    console.print("🔧 [bold blue]Testing MarketResearchAgent Initialization[/bold blue]")
    console.print("=" * 60)
    
    try:
        agent = MarketResearchAgent()
        console.print("✅ [green]Agent initialized successfully[/green]")
        return True
    except Exception as e:
        console.print(f"❌ [red]Agent initialization failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_run():
    """Test basic agent.run() functionality."""
    console.print(f"\n📊 [bold blue]Testing Basic Agent Run[/bold blue]")
    console.print("=" * 60)
    
    try:
        agent = MarketResearchAgent()
        
        # Simple test state
        test_state = {
            'business_idea': 'Electric vehicle charging network',
            'user_request': 'I need market research for EV charging stations'
        }
        
        console.print("📋 Input state:")
        console.print(f"   Business: {test_state['business_idea']}")
        console.print(f"   Request: {test_state['user_request']}")
        
        # Run the agent
        result = await agent.run(test_state)
        
        if result:
            console.print("✅ [green]Agent.run() completed successfully![/green]")
            console.print(f"📊 Output keys: {list(result.keys())}")
            
            # Check for expected outputs
            if 'market_size' in result:
                console.print(f"💰 Market Size: {result['market_size'].get('total_market_size', 'N/A')}")
            if 'competitive_landscape' in result:
                competitive = result['competitive_landscape']
                console.print(f"🏢 Competitive Intensity: {competitive.get('competitive_intensity', 'N/A')}")
            if 'analysis_type' in result:
                console.print(f"📄 Analysis Type: {result['analysis_type']}")
            
            return True
        else:
            console.print("❌ [red]Agent.run() returned no result[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Agent.run() failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

async def test_different_business_types():
    """Test agent with different business types."""
    console.print(f"\n🎯 [bold blue]Testing Different Business Types[/bold blue]")
    console.print("=" * 60)
    
    test_cases = [
        {
            'business_idea': 'Sustainable fashion brand targeting Gen Z',
            'user_request': 'Market analysis for sustainable fashion'
        },
        {
            'business_idea': 'AI-powered fintech startup for small businesses',
            'user_request': 'Competitor research for fintech solutions'
        },
        {
            'business_idea': 'Plant-based food delivery service',
            'user_request': 'Market size and trends for plant-based food'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            console.print(f"\n📋 Test {i}: {test_case['business_idea'][:40]}...")
            
            agent = MarketResearchAgent()
            result = await agent.run(test_case)
            
            if result and 'market_size' in result:
                market_size = result['market_size'].get('total_market_size', 'Unknown')
                console.print(f"   ✅ Success - Market Size: {market_size}")
                results.append(True)
            else:
                console.print(f"   ❌ Failed - No market data returned")
                results.append(False)
                
        except Exception as e:
            console.print(f"   ❌ Error: {str(e)[:50]}...")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    console.print(f"\n📊 Success Rate: {success_rate:.0f}% ({sum(results)}/{len(results)})")
    
    return success_rate > 50  # At least 50% success rate

if __name__ == "__main__":
    async def run_standalone_tests():
        console.print("🧪 [bold cyan]MARKET RESEARCH AGENT STANDALONE TESTING[/bold cyan]")
        console.print("=" * 70)
        console.print("Testing the agent in complete isolation - no orchestration dependencies")
        console.print()
        
        # Run all tests
        init_ok = await test_basic_initialization()
        run_ok = await test_basic_run()
        variety_ok = await test_different_business_types()
        
        # Summary
        console.print(f"\n" + "="*70)
        console.print("📊 [bold green]STANDALONE TEST RESULTS[/bold green]")
        console.print("="*70)
        
        tests = [
            ("Basic Initialization", init_ok),
            ("Basic Agent Run", run_ok), 
            ("Multiple Business Types", variety_ok)
        ]
        
        all_passed = True
        for test_name, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            console.print(f"{status} - {test_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            console.print(f"\n🎉 [bold green]AGENT WORKS STANDALONE - READY FOR ORCHESTRATION[/bold green]")
        else:
            console.print(f"\n⚠️ [bold yellow]AGENT HAS ISSUES - FIX BEFORE ORCHESTRATION[/bold yellow]")
    
    asyncio.run(run_standalone_tests())