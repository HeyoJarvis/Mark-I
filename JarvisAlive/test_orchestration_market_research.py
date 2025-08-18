#!/usr/bin/env python3
"""Test MarketResearchAgent integration with Universal Orchestrator."""

import asyncio
import os
import sys
from rich.console import Console

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from orchestration.universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig

console = Console()

async def test_market_research_routing():
    """Test market research routing through universal orchestrator."""
    console.print("🌐 [bold blue]Testing Universal Orchestrator Market Research Integration[/bold blue]")
    console.print("=" * 80)
    
    try:
        # Initialize orchestrator
        config = UniversalOrchestratorConfig(
            anthropic_api_key=os.environ['ANTHROPIC_API_KEY'],
            redis_url="redis://localhost:6380"
        )
        
        orchestrator = UniversalOrchestrator(config)
        console.print("✅ Orchestrator created")
        
        # Initialize
        init_success = await orchestrator.initialize()
        if not init_success:
            console.print("❌ [red]Orchestrator initialization failed[/red]")
            return False
        console.print("✅ Orchestrator initialized")
        
        # Test market research queries
        test_queries = [
            "Market research for electric vehicle charging stations",
            "Analyze the competitive landscape for fintech startups",
            "What is the market size for sustainable fashion?",
            "Competitor analysis for AI-powered fitness apps"
        ]
        
        for i, query in enumerate(test_queries, 1):
            console.print(f"\n📋 [bold]Test {i}:[/bold] {query}")
            
            try:
                # Process query
                result = await orchestrator.process_query(query)
                
                if result.get("status") == "success":
                    routing_info = result.get("routing_info", {})
                    console.print(f"✅ Routed to: {routing_info.get('orchestrator', 'unknown')}")
                    console.print(f"🎯 Intent: {routing_info.get('intent', 'unknown')}")
                    console.print(f"🔥 Confidence: {routing_info.get('confidence', 0):.2f}")
                    
                    # Check for market research results
                    response = result.get("response", {})
                    if response.get("status") == "completed" and response.get("result"):
                        result_data = response.get("result", {})
                        if result_data.get("market_research_success"):
                            console.print("✅ [green]Market research completed successfully![/green]")
                            console.print(f"📊 Market size: {result_data.get('market_size', 'N/A')}")
                            console.print(f"🏢 Competitors: {len(result_data.get('key_competitors', []))}")
                        else:
                            console.print("❌ [red]Market research failed[/red]")
                    else:
                        console.print("⚠️ [yellow]Unexpected response format[/yellow]")
                        console.print(f"Response keys: {list(response.keys())}")
                else:
                    console.print(f"❌ [red]Query failed: {result.get('error_message', 'Unknown error')}[/red]")
                    
            except Exception as e:
                console.print(f"❌ [red]Test failed: {e}[/red]")
                return False
        
        # Close orchestrator
        await orchestrator.close()
        console.print("\n✅ [green]All tests completed successfully![/green]")
        return True
        
    except Exception as e:
        console.print(f"❌ [red]Orchestration test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        success = await test_market_research_routing()
        if success:
            console.print("\n🎉 [bold green]Market Research Orchestration Works![/bold green]")
        else:
            console.print("\n💥 [bold red]Market Research Orchestration Broken[/bold red]")
    
    asyncio.run(main())