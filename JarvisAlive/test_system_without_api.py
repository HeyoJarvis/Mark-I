#!/usr/bin/env python3
"""
Test the enhanced parallel system with mock responses (no API key needed)
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from orchestration.langgraph.parallel_intelligent_graph import create_parallel_intelligent_workflow, ParallelWorkflowState
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_system_with_mock():
    """Test the enhanced system with mock mode"""
    
    print("🚀 Testing Enhanced Parallel Workflow System (Mock Mode)")
    print("=" * 60)
    
    # Set mock environment variables
    os.environ['USE_MOCK_RESPONSES'] = 'true'
    os.environ['ANTHROPIC_API_KEY'] = 'mock-key-for-testing'
    
    try:
        # Create the workflow system
        app, persistent_system, workflow_brain = await create_parallel_intelligent_workflow(
            skip_approvals=True,
            approval_callback=None
        )
        
        # Create initial workflow state
        initial_state = {
            'workflow_id': f"test_{int(datetime.utcnow().timestamp())}",
            'session_id': 'test_session',
            'user_request': 'Create a brand identity and market analysis for a boutique coffee roastery'
        }
        
        print("✅ Workflow system initialized")
        print("🧪 Testing parallel agent execution...")
        
        # Create config
        config = {
            "configurable": {
                "thread_id": f"thread_{initial_state['workflow_id']}",
                "checkpoint_ns": "test_workflow"
            },
            "recursion_limit": 25
        }
        
        # Execute workflow
        results = []
        async for state_update in app.astream(initial_state, config=config):
            results.append(state_update)
            status = state_update.get('overall_status', 'unknown')
            print(f"📊 Status: {status}")
            
            # Show agent progress
            if state_update.get('agent_statuses'):
                for agent, agent_status in state_update.get('agent_statuses', {}).items():
                    emoji = "✅" if agent_status == "completed" else "⏳" if agent_status == "running" else "❌"
                    print(f"   {emoji} {agent}: {agent_status}")
            
            if status in ["completed", "failed", "cancelled"]:
                print(f"🎯 Final Status: {status.upper()}")
                break
        
        # Show final results
        if results:
            final_result = results[-1]
            print("\n" + "=" * 60)
            print("🎉 ENHANCED SYSTEM TEST RESULTS")
            print("=" * 60)
            
            completed_agents = final_result.get('completed_agents', [])
            failed_agents = final_result.get('failed_agents', [])
            
            print(f"✅ Completed Agents: {len(completed_agents)}")
            for agent in completed_agents:
                print(f"   ✓ {agent}")
            
            if failed_agents:
                print(f"❌ Failed Agents: {len(failed_agents)}")
                for agent in failed_agents:
                    print(f"   ✗ {agent}")
            
            # Show any artifacts or reports
            artifacts = final_result.get('artifacts', {})
            if artifacts:
                print(f"\n📁 Generated Artifacts: {len(artifacts)}")
                for name, path in artifacts.items():
                    print(f"   📄 {name}: {path}")
        
        # Cleanup
        await persistent_system.stop()
        
        print("\n🎉 Enhanced system test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system_with_mock())
    sys.exit(0 if success else 1)