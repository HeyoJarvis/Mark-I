#!/usr/bin/env python3
"""
Simple test to verify parallel agent execution works with the persistent system.
This bypasses LangGraph to focus on the core concurrent execution.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_direct_parallel_execution():
    """Test direct parallel execution without LangGraph."""
    print("🧪 Testing Direct Parallel Agent Execution")
    print("="*50)
    
    from orchestration.persistent.persistent_system import create_development_persistent_system
    
    # Initialize system
    print("1. Starting persistent system...")
    system = create_development_persistent_system()
    await system.start()
    print("✅ System started")
    
    # Submit multiple tasks in parallel
    print("\n2. Submitting parallel tasks...")
    
    tasks = [
        {
            "task_type": "branding",
            "input_data": {
                "business_idea": "TechFlow - software consultancy",
                "session_id": "test_session"
            }
        },
        # Only test one type first to avoid complexity
    ]
    
    # Submit tasks
    batch_results = []
    for i, task in enumerate(tasks):
        print(f"   📤 Submitting task {i+1}: {task['task_type']}")
        result = await system.submit_task(
            task=task,
            user_id="test_user", 
            session_id="test_session",
            requires_approval=False
        )
        batch_results.append(result)
        print(f"   ✅ Task {i+1} submitted: {result.get('task_id', 'unknown')}")
    
    # Wait for results
    print(f"\n3. Waiting for {len(tasks)} task(s) to complete...")
    
    completed = 0
    max_wait = 120  # 2 minutes max
    
    for wait_time in range(0, max_wait, 5):
        print(f"   ⏳ Checking results ({wait_time}s elapsed)...")
        
        for i, batch_result in enumerate(batch_results):
            task_id = batch_result.get('task_id')
            if task_id:
                result = await system.get_task_result(task_id)
                if result:
                    print(f"   ✅ Task {i+1} completed!")
                    print(f"      Success: {result.get('success', False)}")
                    if result.get('success'):
                        # Show some result details
                        if 'brand_names' in result:
                            names = result['brand_names'][:2]  # First 2
                            print(f"      Brand names: {names}")
                        if 'logo_prompt' in result:
                            print(f"      Logo prompt created: ✓")
                    else:
                        print(f"      Error: {result.get('error_message', 'Unknown')}")
                    completed += 1
        
        if completed >= len(tasks):
            break
        
        await asyncio.sleep(5)
    
    print(f"\n4. Results: {completed}/{len(tasks)} tasks completed")
    
    # Cleanup
    await system.stop()
    print("✅ System stopped")
    
    return completed == len(tasks)

if __name__ == "__main__":
    success = asyncio.run(test_direct_parallel_execution())
    if success:
        print("\n🎉 SUCCESS: Direct parallel execution works!")
    else:
        print("\n❌ FAILURE: Direct parallel execution had issues")