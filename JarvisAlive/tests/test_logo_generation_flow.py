#!/usr/bin/env python3
"""
Test script for end-to-end branding + logo generation flow.

This script tests the complete workflow from user request to logo generation,
including Universal Orchestrator routing, BrandingAgent execution, and
LogoGenerationAgent coordination.
"""

import asyncio
import os
import sys
from datetime import datetime
from rich.console import Console

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig
from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig
from main import display_universal_result

console = Console()

async def test_logo_generation_flow():
    """Test the complete logo generation flow."""
    console.print("[bold cyan]🧪 Testing End-to-End Logo Generation Flow[/bold cyan]\n")
    
    # Test cases with logo generation requests
    test_cases = [
        {
            "name": "Direct Logo Request",
            "query": "Generate a logo for my tech startup called InnovateAI",
            "should_generate_logo": True
        },
        {
            "name": "Branding + Logo Request",
            "query": "Make branding and actual logo images for my coffee shop",
            "should_generate_logo": True
        },
        {
            "name": "Basic Branding Request (no logo)",
            "query": "Create a brand for my consulting business",
            "should_generate_logo": False
        }
    ]
    
    try:
        # Initialize Universal Orchestrator
        config = UniversalOrchestratorConfig(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6380')
        )
        
        orchestrator = UniversalOrchestrator(config)
        await orchestrator.initialize()
        
        console.print("[green]✅ Universal Orchestrator initialized successfully[/green]\n")
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            console.print(f"[bold yellow]Test {i}: {test_case['name']}[/bold yellow]")
            console.print(f"[dim]Query: \"{test_case['query']}\"[/dim]")
            
            try:
                # Process the query
                result = await orchestrator.process_query(
                    user_query=test_case['query'],
                    session_id=f"test_session_{i}"
                )
                
                # Check results
                if result.get('status') == 'success':
                    console.print("[green]✅ Request processed successfully[/green]")
                    
                    # Check if logo generation was attempted/successful
                    logo_generation = result.get('logo_generation', {})
                    if logo_generation.get('attempted'):
                        if logo_generation.get('success'):
                            console.print("[green]🎨 Logo generation: SUCCESS[/green]")
                            logo_urls = result.get('logo_urls', [])
                            console.print(f"[blue]📸 Generated {len(logo_urls)} logo image(s)[/blue]")
                        else:
                            console.print("[red]❌ Logo generation: FAILED[/red]")
                            error = logo_generation.get('error', 'Unknown error')
                            console.print(f"[red]Error: {error}[/red]")
                    else:
                        if test_case['should_generate_logo']:
                            console.print("[yellow]⚠️  Logo generation not attempted (may need more explicit keywords)[/yellow]")
                        else:
                            console.print("[blue]ℹ️  Logo generation not attempted (as expected)[/blue]")
                    
                    # Display formatted results
                    console.print("\n[dim]--- Full Response ---[/dim]")
                    await display_universal_result(result)
                    
                else:
                    console.print(f"[red]❌ Request failed: {result.get('message', 'Unknown error')}[/red]")
                
            except Exception as e:
                console.print(f"[red]❌ Test failed with error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            
            console.print(f"\n[dim]{'='*50}[/dim]\n")
        
        # Summary
        console.print("[bold green]🎯 Test Summary Complete[/bold green]")
        console.print("Review the results above to verify:")
        console.print("1. Universal Orchestrator correctly routes to Branding")
        console.print("2. BrandingAgent generates brand assets")
        console.print("3. LogoGenerationAgent creates actual logo images when requested")
        console.print("4. Multi-agent coordination works properly")
        console.print("5. Results are displayed correctly in the UI")
        
    except Exception as e:
        console.print(f"[red]❌ Test setup failed: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    finally:
        # Cleanup
        try:
            await orchestrator.close()
            console.print("\n[dim]Orchestrator cleanup completed[/dim]")
        except:
            pass

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check prerequisites
    if not os.getenv('ANTHROPIC_API_KEY'):
        console.print("[red]❌ ANTHROPIC_API_KEY not found in environment[/red]")
        sys.exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        console.print("[yellow]⚠️  OPENAI_API_KEY not found - logo generation will use fallback mode[/yellow]")
    
    # Run the test
    asyncio.run(test_logo_generation_flow())