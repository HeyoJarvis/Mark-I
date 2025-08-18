#!/usr/bin/env python3
"""
Final test of concurrent mode with agent routing fix
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_concurrent_mode():
    """Test concurrent mode with real workflow."""
    
    print("🎯 Final Concurrent Mode Test")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from orchestration.persistent.persistent_system import create_development_persistent_system
        from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
        import uuid
        
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
        
        # Test concurrent workflow execution
        print("\\n2. 🚀 Testing Concurrent Workflow...")
        
        # Create and execute a simple workflow
        workflow_id = await enhanced_brain.create_business_workflow(
            business_idea="Coffee shop",
            user_id="test_user",
            session_id="test_session"
        )
        print(f"   Created workflow: {workflow_id}")
        
        # Start enhanced execution with timeout
        print("   Starting enhanced execution...")
        batch_id = await asyncio.wait_for(
            enhanced_brain.execute_workflow_enhanced(workflow_id),
            timeout=10.0  # Short timeout to avoid hanging
        )
        print(f"   Workflow submitted as batch: {batch_id}")
        
        # Monitor progress for a short time
        print("   Monitoring progress for 15 seconds...")
        for i in range(15):
            await asyncio.sleep(1)
            
            # Get batch status
            status = await persistent_system.get_batch_status(batch_id)
            if status:
                progress = status.get('progress_percentage', 0)
                print(f"     Progress: {progress:.1f}% ({status.get('status', 'unknown')})")
                
                if status.get('status') in ['completed', 'failed']:
                    print(f"   ✅ Workflow completed with status: {status.get('status')}")
                    break
            else:
                print(f"     No status available for batch {batch_id}")
        
        print("\\n🎉 CONCURRENT MODE TEST COMPLETE!")
        return True
        
    except asyncio.TimeoutError:
        print("\\n❌ Workflow execution timed out - this means the hanging issue persists")
        return False
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
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
    
    success = await test_concurrent_mode()
    
    if success:
        print("\\n🎉 Test completed successfully!")
        return 0
    else:
        print("\\n❌ Test failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)