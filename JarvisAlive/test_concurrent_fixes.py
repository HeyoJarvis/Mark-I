#!/usr/bin/env python3
"""
Test that the concurrent mode fixes are working
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixes():
    """Test concurrent mode fixes."""
    
    print("🎯 Testing Concurrent Mode Fixes")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from orchestration.persistent.persistent_system import create_development_persistent_system
        from orchestration.persistent.intelligence_integration import IntelligenceIntegrator
        from orchestration.intelligence.workflow_brain import WorkflowBrain
        
        # Initialize system
        print("\\n1. 🔧 Starting System...")
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        print("✅ System started")
        
        # Test agent availability for all expected task types
        print("\\n2. 🔍 Testing Agent Availability...")
        workflow_brain = WorkflowBrain({
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
        })
        intelligence_integrator = IntelligenceIntegrator(persistent_system, workflow_brain)
        
        # Test all expected task types
        task_types = ['market_research', 'branding', 'business_strategy']
        all_good = True
        
        for task_type in task_types:
            agents = await intelligence_integrator._get_available_agents_for_task(task_type)
            print(f"   {task_type}: {agents}")
            
            if not agents:
                print(f"   ❌ No agents available for {task_type}")
                all_good = False
            else:
                # Verify agents actually exist
                valid_agents = [a for a in agents if a in persistent_system.agent_pool.agents]
                if not valid_agents:
                    print(f"   ❌ Available agents for {task_type} don't exist in pool")
                    all_good = False
                else:
                    print(f"   ✅ {task_type} properly routed")
        
        if all_good:
            print("\\n✅ All task types have valid agent routing!")
        else:
            print("\\n❌ Some task types still have routing issues")
            
        print("\\n3. 📋 Checking Task Type Registrations...")
        mappings = persistent_system.agent_pool.task_type_mapping
        print(f"   Total registered task types: {len(mappings)}")
        print(f"   business_strategy registered: {'business_strategy' in mappings}")
        
        if 'business_strategy' in mappings:
            print(f"   business_strategy agents: {mappings['business_strategy']}")
            
        print("\\n4. 🎉 Fix Verification Complete!")
        return all_good
        
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
    print("Testing Concurrent Mode Fixes...")
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\\n")
    
    success = await test_fixes()
    
    if success:
        print("\\n🎉 All fixes verified! Concurrent mode should work now.")
        return 0
    else:
        print("\\n❌ Some fixes still need work.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)