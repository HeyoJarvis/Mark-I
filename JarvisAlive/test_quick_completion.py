#!/usr/bin/env python3
"""
Quick test to verify task completion events work
"""
import asyncio
import logging
from orchestration.persistent.agents.persistent_branding_agent import PersistentBrandingAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_quick_task_completion():
    """Test that a simple branding task completes successfully"""
    
    print("🧪 Testing Quick Task Completion...")
    
    agent = PersistentBrandingAgent("test_agent", {
        'anthropic_api_key': 'dummy_key'
    })
    
    try:
        # Start agent
        await agent.on_start()
        
        # Submit a simple task
        print("📤 Submitting simple brand name generation task...")
        
        result = await agent.process_task("brand_name_generation", {
            'business_idea': 'coffee shop',
            'industry': 'Food & Beverage',
            'target_audience': 'Young professionals'
        })
        
        print("✅ Task completed successfully!")
        print(f"Result type: {type(result)}")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("🎉 TASK COMPLETION WORKING!")
            return True
        else:
            print("❌ Task failed")
            return False
            
    except Exception as e:
        print(f"❌ Task failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await agent.on_stop()

if __name__ == "__main__":
    success = asyncio.run(test_quick_task_completion())
    if success:
        print("✅ Task completion events are working correctly!")
        exit(0)
    else:
        print("❌ Task completion events still have issues")  
        exit(1)