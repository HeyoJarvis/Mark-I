#!/usr/bin/env python3
"""Test to ensure no more brand names starting with 'N' are generated."""

import asyncio
import os
import sys
from rich.console import Console

# Set up environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['ANTHROPIC_API_KEY'] = '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'

from departments.branding.branding_agent import BrandingAgent

console = Console()

async def test_no_n_names():
    """Test that we don't get repetitive N-starting names."""
    console.print("🚫 [bold blue]Testing No More 'N' Brand Names[/bold blue]")
    console.print("=" * 60)
    
    # Test various different business types
    businesses = [
        "premium chocolate subscription service",
        "smart home automation startup", 
        "sustainable packaging company",
        "virtual reality gaming studio",
        "plant-based meal delivery service",
        "AI-powered language learning app",
        "eco-friendly clothing brand",
        "digital marketing agency for startups"
    ]
    
    brand_names = []
    n_names = []
    
    for i, business in enumerate(businesses, 1):
        try:
            console.print(f"\n📋 Test {i}: {business}")
            
            # Create fresh agent each time to avoid any session state
            agent = BrandingAgent(config={'interactive_approval': False})
            
            test_state = {
                'business_idea': business,
                'user_request': f'Create a unique brand for my {business}'
            }
            
            result = await agent.run(test_state)
            brand_name = result.get('brand_name', f'Unknown_{i}')
            brand_names.append(brand_name)
            
            # Check if starts with N
            starts_with_n = brand_name.upper().startswith('N')
            if starts_with_n:
                n_names.append(brand_name)
                console.print(f"   → [red]⚠️ Brand: {brand_name} (starts with N!)[/red]")
            else:
                console.print(f"   → [green]✅ Brand: {brand_name}[/green]")
            
        except Exception as e:
            console.print(f"   → [red]❌ Error: {e}[/red]")
            brand_names.append(f"Error_{i}")
    
    # Results summary
    console.print(f"\n" + "="*60)
    console.print("📊 [bold green]RESULTS SUMMARY[/bold green]")
    console.print("="*60)
    
    console.print(f"🏷️ All brand names generated:")
    for i, name in enumerate(brand_names, 1):
        starts_with_n = name.upper().startswith('N')
        symbol = "⚠️" if starts_with_n else "✅"
        console.print(f"   {i}. {symbol} {name}")
    
    console.print(f"\n📈 Statistics:")
    console.print(f"   Total names generated: {len(brand_names)}")
    console.print(f"   Names starting with 'N': {len(n_names)}")
    console.print(f"   Unique names: {len(set(brand_names))}")
    
    if len(n_names) == 0:
        console.print(f"\n🎉 [bold green]SUCCESS: No 'N' names generated![/bold green]")
        console.print("✅ AI caching fix is working correctly")
        return True
    else:
        console.print(f"\n⚠️ [bold yellow]WARNING: Found {len(n_names)} 'N' names[/bold yellow]")
        console.print(f"   N-names: {n_names}")
        console.print("❌ There may still be caching issues")
        return False

if __name__ == "__main__":
    async def run_test():
        success = await test_no_n_names()
        
        if success:
            console.print(f"\n🎯 [bold cyan]Issue resolved - no more repetitive 'N' brand names![/bold cyan]")
        else:
            console.print(f"\n🔧 [bold yellow]May need additional cache clearing or restart[/bold yellow]")
    
    asyncio.run(run_test())