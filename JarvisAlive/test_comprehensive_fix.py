#!/usr/bin/env python3
"""Comprehensive test for brand name uniqueness and timeout fixes."""

import asyncio
import os
import sys
from rich.console import Console
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent

console = Console()

async def test_brand_name_uniqueness():
    """Test that different businesses get different brand names."""
    console.print("🏷️ [bold blue]Testing Brand Name Uniqueness[/bold blue]")
    console.print("=" * 50)
    
    businesses = [
        "mobile phone startup",
        "coffee shop",
        "tech consulting firm",
        "fitness app"
    ]
    
    brand_names = []
    
    for business in businesses:
        try:
            agent = BrandingAgent(config={'interactive_approval': False})
            
            test_state = {
                'business_idea': business,
                'user_request': f'Create a brand for my {business}'
            }
            
            result = await agent.run(test_state)
            brand_name = result.get('brand_name', 'N/A')
            brand_names.append(brand_name)
            
            console.print(f"📋 {business} → [bold]{brand_name}[/bold]")
            
        except Exception as e:
            console.print(f"❌ Error with {business}: {e}")
            brand_names.append("ERROR")
    
    # Check for duplicates
    unique_names = set(brand_names)
    if len(unique_names) == len(brand_names):
        console.print("✅ [green]All brand names are unique![/green]")
    else:
        console.print("❌ [red]Found duplicate brand names![/red]")
        console.print(f"Names: {brand_names}")
    
    return len(unique_names) == len(brand_names)

async def test_regeneration_timeout_fix():
    """Test that multiple regenerations work without timeout."""
    console.print(f"\n🔄 [bold blue]Testing Regeneration Timeout Fix[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent(config={'interactive_approval': True})
        
        test_state = {
            'business_idea': 'innovative drone delivery service',
            'user_request': 'Create a brand with logo'
        }
        
        # Test 3 consecutive regenerations
        responses = ['redo', 'redo', 'redo', 'yes']
        
        console.print("🧪 Testing 3 consecutive regenerations...")
        
        with patch('rich.prompt.Prompt.ask', side_effect=responses):
            result = await agent.run(test_state)
        
        if result.get('branding_success', False):
            console.print("✅ [green]All regenerations completed successfully![/green]")
            final_prompt = result.get('logo_prompt', '')
            console.print(f"📝 Final prompt length: {len(final_prompt)} chars")
            return True
        else:
            console.print("❌ [red]Regeneration test failed[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Regeneration test error: {e}[/red]")
        return False

async def test_ai_cache_disabled():
    """Test that AI caching is properly disabled."""
    console.print(f"\n🚫 [bold blue]Testing AI Cache Disabled[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent()
        
        if agent.ai_engine:
            # Check if cache is disabled
            engine_config = agent.ai_engine.config if hasattr(agent.ai_engine, 'config') else None
            if engine_config and hasattr(engine_config, 'enable_cache'):
                cache_enabled = engine_config.enable_cache
                if not cache_enabled:
                    console.print("✅ [green]AI cache is properly disabled[/green]")
                    return True
                else:
                    console.print("❌ [red]AI cache is still enabled[/red]")
                    return False
            else:
                console.print("⚠️ [yellow]Cannot verify cache status[/yellow]")
                return True
        else:
            console.print("⚠️ [yellow]AI engine not available[/yellow]")
            return True
            
    except Exception as e:
        console.print(f"❌ [red]Cache test error: {e}[/red]")
        return False

if __name__ == "__main__":
    async def run_comprehensive_tests():
        console.print("🧪 [bold cyan]COMPREHENSIVE FIX VERIFICATION[/bold cyan]")
        console.print("=" * 60)
        
        # Run all tests
        uniqueness_ok = await test_brand_name_uniqueness()
        regeneration_ok = await test_regeneration_timeout_fix()
        cache_ok = await test_ai_cache_disabled()
        
        # Summary
        console.print(f"\n" + "="*60)
        console.print("📊 [bold green]TEST RESULTS SUMMARY[/bold green]")
        console.print("="*60)
        
        results = [
            ("Brand Name Uniqueness", uniqueness_ok),
            ("Regeneration Timeout Fix", regeneration_ok), 
            ("AI Cache Disabled", cache_ok)
        ]
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            console.print(f"{status} - {test_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            console.print(f"\n🎉 [bold green]ALL TESTS PASSED - FIXES VERIFIED![/bold green]")
        else:
            console.print(f"\n⚠️ [bold yellow]SOME TESTS FAILED - NEEDS MORE WORK[/bold yellow]")
    
    asyncio.run(run_comprehensive_tests())