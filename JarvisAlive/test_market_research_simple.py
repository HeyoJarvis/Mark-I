#!/usr/bin/env python3
"""Simple test of MarketResearchAgent - just verify it works."""

import asyncio
import os
import sys
from rich.console import Console

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.market_research.market_research_agent import MarketResearchAgent

console = Console()

async def test_simple():
    """Test if agent runs without errors."""
    console.print("🔬 [bold blue]Simple MarketResearchAgent Test[/bold blue]")
    console.print("=" * 50)
    
    try:
        # Create agent
        agent = MarketResearchAgent()
        console.print("✅ Agent created")
        
        # Test with simple input
        test_state = {
            'business_idea': 'coffee shop',
            'user_request': 'market research for coffee shop'
        }
        
        console.print("📋 Running agent with coffee shop...")
        
        # Run agent
        result = await agent.run(test_state)
        
        if result:
            console.print("✅ [green]Agent completed successfully![/green]")
            console.print(f"📊 Returned {len(result)} fields")
            
            # Show some key fields (without assuming data structure)
            for key in ['market_research_success', 'analysis_type', 'market_size']:
                if key in result:
                    value = result[key]
                    console.print(f"   {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
            
            return True
        else:
            console.print("❌ [red]No result returned[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        success = await test_simple()
        if success:
            console.print("\n🎉 [bold green]MarketResearchAgent works standalone![/bold green]")
        else:
            console.print("\n💥 [bold red]MarketResearchAgent is broken[/bold red]")
    
    asyncio.run(main())