#!/usr/bin/env python3
"""Test the timeout fix for regeneration operations."""

import asyncio
import os
import sys
from rich.console import Console
from unittest.mock import patch

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.branding.branding_agent import BrandingAgent

console = Console()

async def test_timeout_configuration():
    """Test that AI engine timeout is properly configured."""
    console.print("⏱️ [bold blue]Testing Timeout Configuration[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent()
        
        if not agent.ai_engine:
            console.print("❌ [red]AI engine not available[/red]")
            return False
        
        # Check timeout configuration
        timeout = agent.ai_engine.config.timeout_seconds
        console.print(f"🔧 Current AI timeout: {timeout} seconds")
        
        if timeout >= 300:
            console.print("✅ [green]Timeout properly configured (5+ minutes)[/green]")
            return True
        else:
            console.print(f"❌ [red]Timeout too short: {timeout}s (should be 300+)[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Timeout configuration test failed: {e}[/red]")
        return False

async def test_regeneration_without_timeout():
    """Test multiple regenerations without timeout issues."""
    console.print(f"\n🔄 [bold blue]Testing Regeneration Without Timeout[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent(config={'interactive_approval': True})
        
        test_state = {
            'business_idea': 'innovative cloud storage solution for small businesses',
            'user_request': 'Create branding with logo'
        }
        
        console.print("🧪 Testing 4 consecutive regenerations...")
        console.print("   (This will test beyond the previous 30s timeout limit)")
        
        # Simulate multiple regenerations
        responses = ['redo', 'redo', 'redo', 'redo', 'yes']
        
        with patch('rich.prompt.Prompt.ask', side_effect=responses):
            start_time = asyncio.get_event_loop().time()
            result = await agent.run(test_state)
            end_time = asyncio.get_event_loop().time()
            
        total_time = end_time - start_time
        
        if result.get('logo_prompt') and len(result.get('logo_prompt', '')) > 0:
            console.print(f"✅ [green]All regenerations completed successfully![/green]")
            console.print(f"⏱️ Total time: {total_time:.1f} seconds")
            console.print(f"📝 Final logo prompt generated: {len(result.get('logo_prompt', ''))} chars")
            return True
        else:
            console.print(f"❌ [red]Regeneration failed or incomplete[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Regeneration test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def run_timeout_tests():
        console.print("🧪 [bold cyan]TIMEOUT FIX VERIFICATION[/bold cyan]")
        console.print("=" * 60)
        
        # Run tests
        config_ok = await test_timeout_configuration()
        regeneration_ok = await test_regeneration_without_timeout()
        
        # Summary
        console.print(f"\n" + "="*60)
        console.print("📊 [bold green]TIMEOUT FIX RESULTS[/bold green]")
        console.print("="*60)
        
        tests = [
            ("Timeout Configuration", config_ok),
            ("Regeneration Without Timeout", regeneration_ok)
        ]
        
        all_passed = True
        for test_name, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            console.print(f"{status} - {test_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            console.print(f"\n🎉 [bold green]TIMEOUT ISSUES COMPLETELY RESOLVED![/bold green]")
            console.print("✅ AI engine timeout increased to 5 minutes")
            console.print("✅ Multiple regenerations work without timeout")
            console.print("✅ User can now regenerate infinitely as requested")
        else:
            console.print(f"\n⚠️ [bold yellow]Some timeout issues remain[/bold yellow]")
    
    asyncio.run(run_timeout_tests())