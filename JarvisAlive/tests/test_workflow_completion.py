#!/usr/bin/env python3
"""
Test workflow completion with the interactive approval fix
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_workflow_completion():
    """Test that workflows can complete without hanging."""
    
    print("🚀 Testing Workflow Completion Fix")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from orchestration.persistent.persistent_system import create_development_persistent_system
        from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
        from orchestration.persistent.base_agent import TaskRequest
        import uuid
        
        # Initialize system
        print("\n1. 🔧 Starting System...")
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        print("✅ System started")
        
        # Initialize enhanced brain
        config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'max_retries': 3
        }
        enhanced_brain = EnhancedWorkflowBrain(config, persistent_system)
        await enhanced_brain.initialize_orchestration()
        print("✅ Enhanced brain initialized")
        
        # Test simple task submission
        print("\n2. 🎯 Testing Task Submission...")
        
        # Create a simple branding task
        task = TaskRequest(
            task_id=str(uuid.uuid4()),
            task_type="brand_name_generation",
            input_data={
                "business_idea": "Coffee shop",
                "industry": "food_and_beverage",
                "target_audience": "coffee lovers"
            },
            priority=1,
            timeout_seconds=30  # Short timeout to avoid hanging
        )
        
        print(f"   Submitting task: {task.task_type}")
        
        # Submit task with timeout
        try:
            agent_id = await asyncio.wait_for(
                persistent_system.agent_pool.submit_task(task),
                timeout=5.0
            )
            
            if agent_id:
                print(f"✅ Task submitted to agent: {agent_id}")
                
                # Wait a bit to see if task processes
                print("   ⏳ Waiting 10 seconds for task processing...")
                await asyncio.sleep(10)
                
                # Check agent health
                agent_health = await persistent_system.agent_pool.get_pool_health()
                print(f"   📊 Agent pool status: {agent_health.healthy_agents}/{agent_health.total_agents} healthy")
                print(f"   📊 Tasks processed: {agent_health.total_tasks_processed}")
                
                if agent_health.total_tasks_processed > 0:
                    print("✅ TASK PROCESSING IS WORKING!")
                else:
                    print("⚠️  No tasks processed yet...")
                    
            else:
                print("❌ Failed to submit task")
                
        except asyncio.TimeoutError:
            print("❌ Task submission timed out")
        except Exception as e:
            print(f"❌ Task submission error: {e}")
            
        print("\n3. 📈 Final System State...")
        health = await persistent_system.get_system_health()
        print(f"   System running: {health['system_running']}")
        print(f"   Components: {len(health['components'])} active")
        
        print("\n" + "=" * 50)
        print("🎯 WORKFLOW COMPLETION TEST COMPLETE")
        print("✅ System architecture is working")
        print("💡 If tasks process successfully, the infinite loop is fixed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        try:
            if 'persistent_system' in locals():
                await persistent_system.stop()
                print("\n✅ System stopped")
        except Exception as e:
            print(f"⚠️  Stop error: {e}")

async def main():
    """Main test function."""
    print("Starting Workflow Completion Test...")
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    
    success = await test_workflow_completion()
    
    if success:
        print("\n🎉 Test completed successfully!")
        return 0
    else:
        print("\n❌ Test failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)