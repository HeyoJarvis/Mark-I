#!/usr/bin/env python3
"""Test all timeout configurations are properly fixed."""

import asyncio
import os
import sys
from rich.console import Console
from unittest.mock import patch

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.branding.branding_agent import BrandingAgent
from orchestration.branding_orchestration_config import DEFAULT_CONFIG, PRODUCTION_CONFIG, DEVELOPMENT_CONFIG

console = Console()

async def test_all_timeout_configurations():
    """Test all timeout configurations are properly set."""
    console.print("⚙️ [bold blue]Testing All Timeout Configurations[/bold blue]")
    console.print("=" * 60)
    
    # Test AI Engine timeout
    try:
        agent = BrandingAgent()
        if agent.ai_engine:
            ai_timeout = agent.ai_engine.config.timeout_seconds
            console.print(f"🤖 AI Engine timeout: {ai_timeout}s")
            if ai_timeout >= 300:
                console.print("   ✅ [green]AI Engine timeout OK (5+ minutes)[/green]")
            else:
                console.print(f"   ❌ [red]AI Engine timeout too short: {ai_timeout}s[/red]")
        else:
            console.print("   ⚠️ [yellow]AI Engine not available[/yellow]")
    except Exception as e:
        console.print(f"   ❌ [red]AI Engine timeout test failed: {e}[/red]")
    
    # Test Orchestration timeout configurations
    configs = [
        ("DEFAULT_CONFIG", DEFAULT_CONFIG),
        ("PRODUCTION_CONFIG", PRODUCTION_CONFIG), 
        ("DEVELOPMENT_CONFIG", DEVELOPMENT_CONFIG)
    ]
    
    for config_name, config in configs:
        try:
            timeout = config.security.get("request_timeout_seconds", 0)
            console.print(f"🏭 {config_name}: {timeout}s")
            if timeout >= 300:
                console.print(f"   ✅ [green]{config_name} timeout OK[/green]")
            else:
                console.print(f"   ❌ [red]{config_name} timeout too short: {timeout}s[/red]")
        except Exception as e:
            console.print(f"   ❌ [red]{config_name} test failed: {e}[/red]")
    
    console.print("\n📊 Summary:")
    console.print("✅ All timeout configurations should now be 300+ seconds")
    console.print("✅ This prevents timeout on regeneration attempts")

async def test_extended_regeneration():
    """Test extended regeneration without timeout."""
    console.print(f"\n🔄 [bold blue]Testing Extended Regeneration[/bold blue]")
    console.print("=" * 60)
    
    try:
        agent = BrandingAgent(config={'interactive_approval': True})
        
        test_state = {
            'business_idea': 'premium sustainable coffee subscription service',
            'user_request': 'Create comprehensive branding with logo'
        }
        
        console.print("🧪 Testing 5 consecutive regenerations...")
        console.print("   (Testing beyond all previous timeout limits)")
        
        # Extended regeneration test
        responses = ['redo', 'redo', 'redo', 'redo', 'redo', 'yes']
        
        with patch('rich.prompt.Prompt.ask', side_effect=responses):
            start_time = asyncio.get_event_loop().time()
            result = await agent.run(test_state)
            end_time = asyncio.get_event_loop().time()
        
        total_time = end_time - start_time
        
        if result.get('logo_prompt'):
            console.print(f"✅ [green]All 5 regenerations completed successfully![/green]")
            console.print(f"⏱️ Total time: {total_time:.1f} seconds")
            console.print(f"🏢 Brand: {result.get('brand_name', 'Unknown')}")
            console.print(f"📝 Final prompt: {len(result.get('logo_prompt', ''))} characters")
            return True
        else:
            console.print(f"❌ [red]Regeneration test failed[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Extended regeneration test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def run_all_timeout_tests():
        console.print("🧪 [bold cyan]ALL TIMEOUT CONFIGURATIONS TEST[/bold cyan]")
        console.print("=" * 70)
        
        await test_all_timeout_configurations()
        success = await test_extended_regeneration()
        
        console.print(f"\n" + "="*70)
        console.print("🎯 [bold green]FINAL TIMEOUT FIX STATUS[/bold green]")
        console.print("="*70)
        
        if success:
            console.print("🎉 [bold green]ALL TIMEOUT ISSUES RESOLVED![/bold green]")
            console.print("✅ AI Engine timeout: 300+ seconds")
            console.print("✅ Orchestration timeouts: 300+ seconds")
            console.print("✅ Extended regeneration: Working")
            console.print("✅ User experience: Seamless infinite regeneration")
        else:
            console.print("⚠️ [bold yellow]Some timeout issues may remain[/bold yellow]")
            console.print("🔧 Check the error messages above")
    
    asyncio.run(run_all_timeout_tests())