#!/usr/bin/env python3
"""Test LogoGenerationAgent directly."""

import asyncio
import os
import sys
import json
from rich.console import Console

# Add the current directory to Python path for imports  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.logo_generation_agent import LogoGenerationAgent

console = Console()

async def test_logo_agent_direct():
    """Test the LogoGenerationAgent directly."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Create agent
        agent = LogoGenerationAgent()
        
        # Create test input state (what branding agent would pass)
        test_state = {
            'brand_name': 'TestBrand',
            'logo_prompt': 'Design a modern minimalist logo with clean lines and bold colors',
            'color_palette': ['#1B365C', '#E5B39E', '#F9F1E6'],
            'business_type': 'tech startup',
            'industry': 'technology'
        }
        
        console.print("🧪 Testing LogoGenerationAgent directly")
        console.print(f"Input state: {test_state}")
        console.print()
        
        # Run agent
        result = await agent.run(test_state)
        
        console.print("📋 Agent Result:")
        console.print(json.dumps(result, indent=2, default=str))
        
        # Check key fields
        console.print(f"\n✅ Result keys: {list(result.keys())}")
        console.print(f"Logo generation success: {result.get('logo_generation_success', 'NOT FOUND')}")
        console.print(f"Logo URLs: {result.get('logo_urls', 'NOT FOUND')}")
        console.print(f"Logo images: {result.get('logo_images', 'NOT FOUND')}")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_logo_agent_direct())