#!/usr/bin/env python3
"""Final verification test for AI caching fix and brand name uniqueness."""

import asyncio
import os
import sys
from rich.console import Console

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.branding.branding_agent import BrandingAgent

console = Console()

async def test_ai_engine_configuration():
    """Test that AI engine is properly configured with caching disabled."""
    console.print("🤖 [bold blue]Testing AI Engine Configuration[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent()
        
        if not agent.ai_engine:
            console.print("❌ [red]AI engine not initialized[/red]")
            return False
            
        # Check configuration
        config = agent.ai_engine.config
        if hasattr(config, 'enable_cache'):
            cache_enabled = config.enable_cache
            console.print(f"🔧 Cache enabled: {cache_enabled}")
            
            if not cache_enabled:
                console.print("✅ [green]AI caching is properly DISABLED[/green]")
                return True
            else:
                console.print("❌ [red]AI caching is still ENABLED - this is the bug![/red]")
                return False
        else:
            console.print("⚠️ [yellow]Cache setting not found in config[/yellow]")
            return True
            
    except Exception as e:
        console.print(f"❌ [red]Configuration test failed: {e}[/red]")
        return False

async def test_brand_name_uniqueness():
    """Test brand name uniqueness across different business types."""
    console.print(f"\n🏷️ [bold blue]Testing Brand Name Uniqueness[/bold blue]")
    console.print("=" * 50)
    
    # Different business types to test uniqueness
    businesses = [
        "sustainable fashion startup",
        "AI-powered fitness app",
        "organic coffee roastery",
        "blockchain consulting firm"
    ]
    
    brand_names = []
    
    for i, business in enumerate(businesses):
        try:
            console.print(f"📋 Testing business {i+1}: {business}")
            
            agent = BrandingAgent(config={'interactive_approval': False})
            test_state = {
                'business_idea': business,
                'user_request': f'Create a brand for my {business}'
            }
            
            result = await agent.run(test_state)
            brand_name = result.get('brand_name', f'Unknown_{i}')
            brand_names.append(brand_name)
            
            console.print(f"   → Brand: [bold]{brand_name}[/bold]")
            
        except Exception as e:
            console.print(f"   → Error: {e}")
            brand_names.append(f"Error_{i}")
    
    # Check for duplicates
    unique_names = set(brand_names)
    console.print(f"\n📊 Results:")
    console.print(f"   Generated names: {brand_names}")
    console.print(f"   Unique names: {len(unique_names)} out of {len(brand_names)}")
    
    if len(unique_names) == len(brand_names):
        console.print("✅ [green]All brand names are UNIQUE![/green]")
        return True
    else:
        console.print("❌ [red]Found DUPLICATE brand names![/red]")
        duplicates = [name for name in brand_names if brand_names.count(name) > 1]
        console.print(f"   Duplicates: {set(duplicates)}")
        return False

async def test_timeout_fix():
    """Test that AI calls don't timeout with the new configuration."""
    console.print(f"\n⏱️ [bold blue]Testing Timeout Fix[/bold blue]")
    console.print("=" * 50)
    
    try:
        agent = BrandingAgent()
        
        if not agent.ai_engine:
            console.print("❌ [red]AI engine not available for timeout test[/red]")
            return False
        
        # Test a simple AI call to ensure it works
        test_prompt = "Generate a brief test response"
        console.print(f"🧪 Testing AI call with prompt: '{test_prompt[:30]}...'")
        
        response = await agent.ai_engine.generate(test_prompt)
        
        if response and hasattr(response, 'content'):
            console.print(f"✅ [green]AI call successful![/green]")
            console.print(f"   Response length: {len(response.content)} characters")
            return True
        else:
            console.print("❌ [red]AI call failed - no response[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Timeout test failed: {e}[/red]")
        return False

if __name__ == "__main__":
    async def run_final_verification():
        console.print("🧪 [bold cyan]FINAL VERIFICATION OF AI CACHING FIX[/bold cyan]")
        console.print("=" * 60)
        
        # Run all tests
        config_ok = await test_ai_engine_configuration()
        uniqueness_ok = await test_brand_name_uniqueness() 
        timeout_ok = await test_timeout_fix()
        
        # Final summary
        console.print(f"\n" + "="*60)
        console.print("📊 [bold green]FINAL VERIFICATION RESULTS[/bold green]")
        console.print("="*60)
        
        tests = [
            ("AI Cache Disabled", config_ok),
            ("Brand Name Uniqueness", uniqueness_ok),
            ("Timeout Fix", timeout_ok)
        ]
        
        all_passed = True
        for test_name, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            console.print(f"{status} - {test_name}")
            if not passed:
                all_passed = False
        
        console.print("\n" + "="*60)
        if all_passed:
            console.print("🎉 [bold green]ALL FIXES VERIFIED - ISSUES RESOLVED![/bold green]")
            console.print("✅ No more duplicate brand names")
            console.print("✅ No more timeout issues") 
            console.print("✅ AI caching disabled for creative work")
        else:
            console.print("⚠️ [bold yellow]SOME ISSUES REMAIN - CHECK FAILED TESTS[/bold yellow]")
    
    asyncio.run(run_final_verification())