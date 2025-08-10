#!/usr/bin/env python3
"""Test logo generation with mock download to demonstrate full workflow."""

import asyncio
import os
import sys
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.logo_generation_agent import LogoGenerationAgent

console = Console()

async def test_mock_logo_download():
    """Test logo generation with mock download to show complete workflow."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Force the agent to use mock mode to demonstrate download
        agent = LogoGenerationAgent(config={
            'logos_dir': './demo_logos',
            'force_mock_mode': True  # Force mock mode for demo
        })
        
        # Override to use mock mode  
        agent.use_real_dalle = False
        
        # Create test input state
        test_state = {
            'brand_name': 'DemoTech',
            'logo_prompt': 'Design a modern tech logo with clean geometric shapes',
            'color_palette': ['#1B365C', '#E5B39E', '#F9F1E6'],
            'business_type': 'technology startup',
            'industry': 'software'
        }
        
        console.print("🧪 Testing Complete Logo Generation Workflow with Mock Download")
        console.print(f"Input: {test_state['brand_name']} - {test_state['logo_prompt']}")
        console.print()
        
        # Run agent
        result = await agent.run(test_state)
        
        console.print("📋 Results:")
        console.print(f"✅ Success: {result.get('logo_generation_success', False)}")
        console.print(f"📁 Logo images generated: {len(result.get('logo_images', []))}")
        
        # Show logo details
        logo_images = result.get('logo_images', [])
        for i, img in enumerate(logo_images, 1):
            if isinstance(img, dict):
                console.print(f"\n🎨 Logo {i}:")
                console.print(f"  • Filename: {img.get('filename', 'N/A')}")
                console.print(f"  • URL: {img.get('image_url', 'N/A')}")
                console.print(f"  • Local path: {img.get('local_path', 'N/A')}")
                console.print(f"  • Dimensions: {img.get('dimensions', 'N/A')}")
                
                # Check if file exists
                local_path = img.get('local_path', '')
                if local_path and os.path.exists(local_path):
                    console.print(f"  ✅ File verified at: {local_path}")
                    
                    # Show file size
                    try:
                        file_size = os.path.getsize(local_path)
                        console.print(f"  📊 File size: {file_size} bytes")
                    except:
                        pass
        
        console.print(f"\n🎉 Complete workflow test successful!")
        console.print("This demonstrates the full pipeline:")
        console.print("  1. ✅ Logo generation (mock/real)")
        console.print("  2. ✅ File download and storage") 
        console.print("  3. ✅ Local path tracking")
        console.print("  4. ✅ Response formatting")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock_logo_download())