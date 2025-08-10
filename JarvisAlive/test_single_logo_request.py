#!/usr/bin/env python3
"""Test a single logo generation request."""

import asyncio
import os
import sys
from datetime import datetime
from rich.console import Console

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig
from main import display_universal_result

console = Console()

async def test_single_logo_request():
    """Test a single logo generation request."""
    console.print("[bold cyan]🧪 Testing Single Logo Generation Request[/bold cyan]\n")
    
    try:
        # Initialize Universal Orchestrator
        config = UniversalOrchestratorConfig(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6380')
        )
        
        orchestrator = UniversalOrchestrator(config)
        await orchestrator.initialize()
        
        console.print("[green]✅ Universal Orchestrator initialized[/green]")
        
        # Test logo generation request
        test_query = "Generate a logo for my tech startup called InnovateAI"
        console.print(f"[yellow]Query: \"{test_query}\"[/yellow]\n")
        
        # Process the query
        result = await orchestrator.process_query(
            user_query=test_query,
            session_id="test_logo_session"
        )
        
        # Display results
        console.print("[bold green]📋 Results:[/bold green]")
        await display_universal_result(result)
        
        # Check if logo generation worked
        logo_generation = result.get('logo_generation', {})
        if logo_generation.get('attempted'):
            if logo_generation.get('success'):
                console.print("\n[green]🎉 Logo generation was successful![/green]")
                console.print(f"Generated {len(result.get('logo_urls', []))} logo images")
            else:
                console.print("\n[red]❌ Logo generation failed[/red]")
                console.print(f"Error: {logo_generation.get('error', 'Unknown')}")
        else:
            console.print("\n[yellow]⚠️ Logo generation was not attempted[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await orchestrator.close()
        except:
            pass

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_single_logo_request())