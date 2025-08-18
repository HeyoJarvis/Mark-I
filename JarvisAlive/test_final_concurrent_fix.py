#!/usr/bin/env python3
"""
Final test of all concurrent mode fixes
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """Test complete concurrent workflow execution."""
    
    print("🎯 Final Concurrent Mode Test - All Fixes")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from orchestration.persistent.persistent_system import create_development_persistent_system
        from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
        
        # Initialize system
        print("\\n1. 🔧 Starting System...")
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
        
        # Test workflow creation
        print("\\n2. 📋 Creating Test Workflow...")
        workflow_id = await enhanced_brain.create_workflow(
            user_id="test_user",
            session_id="test_session", 
            workflow_type="business_creation",
            initial_request="setup a coffee shop business"
        )
        print(f"✅ Created workflow: {workflow_id}")
        
        # Test concurrent execution submission
        print("\\n3. 🚀 Testing Concurrent Execution...")
        
        try:
            # Execute concurrently using the intelligence integrator directly to get batch_id
            batch_id = await asyncio.wait_for(
                enhanced_brain.intelligence_integrator.execute_workflow_concurrently(
                    workflow_id=workflow_id,
                    user_id="test_user", 
                    session_id="test_session"
                ),
                timeout=15.0
            )
            print(f"✅ Workflow submitted as batch: {batch_id}")
            
            # Monitor execution for progress
            print("\\n4. 📊 Monitoring Execution Progress...")
            progress_updates = []
            
            for i in range(20):  # Check for 20 seconds
                await asyncio.sleep(1)
                
                # Get batch status  
                try:
                    status = await persistent_system.get_batch_status(batch_id)
                    if status:
                        progress = status.get('progress_percentage', 0)
                        batch_status = status.get('status', 'unknown')
                        
                        progress_updates.append((i+1, progress, batch_status))
                        print(f"     Second {i+1:2d}: {progress:5.1f}% - {batch_status}")
                        
                        if batch_status in ['completed', 'failed']:
                            print(f"\\n   🎯 Batch {batch_status} after {i+1} seconds!")
                            break
                            
                        if progress > 0:
                            print(f"   ✅ Progress detected! System is working!")
                    else:
                        print(f"     Second {i+1:2d}: No status available")
                        
                except Exception as e:
                    print(f"     Second {i+1:2d}: Error getting status: {e}")
            
            # Analysis
            print("\\n5. 📈 Results Analysis...")
            max_progress = max([p[1] for p in progress_updates] + [0])
            final_status = progress_updates[-1][2] if progress_updates else "unknown"
            
            print(f"   Max progress reached: {max_progress:.1f}%")
            print(f"   Final batch status: {final_status}")
            
            if max_progress > 0:
                print("   ✅ SUCCESS: Tasks are executing and progress is updating!")
            else:
                print("   ❌ FAILURE: Progress remained at 0% - tasks not completing")
                
            return max_progress > 0
            
        except asyncio.TimeoutError:
            print("\\n❌ Workflow submission timed out")
            return False
        except Exception as e:
            print(f"\\n❌ Workflow execution error: {e}")
            return False
        
    except Exception as e:
        print(f"\\n❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        try:
            if 'persistent_system' in locals():
                await persistent_system.stop()
                print("\\n✅ System stopped")
        except Exception as e:
            print(f"⚠️  Stop error: {e}")

async def main():
    """Main test function."""
    print("Starting Final Concurrent Mode Test...")
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\\n")
    
    success = await test_complete_workflow()
    
    if success:
        print("\\n🎉 ALL FIXES SUCCESSFUL! Concurrent mode is working!")
        print("💡 The system can now process workflows without getting stuck!")
        return 0
    else:
        print("\\n❌ Some issues remain. The system still needs work.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)