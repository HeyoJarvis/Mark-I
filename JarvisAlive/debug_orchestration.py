#!/usr/bin/env python3
"""
Debug script for Branding Agent Orchestration Integration

This script helps debug the orchestration integration step by step.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig
from orchestration.intent_parser import IntentParser
from orchestration.agent_integration import AgentRegistry, AgentExecutor
from departments.branding.branding_agent import BrandingAgent


async def debug_step_by_step():
    """Debug the orchestration step by step."""
    print("🔍 Debugging Orchestration Integration")
    print("=" * 50)
    
    try:
        # Step 1: Test intent parser
        print("\n📋 Step 1: Testing Intent Parser")
        parser = IntentParser()
        test_request = "I need a brand name for my coffee shop"
        parsed_intent = await parser.parse_intent(test_request)
        print(f"✅ Intent: {parsed_intent.primary_intent}")
        print(f"✅ Confidence: {parsed_intent.confidence}")
        print(f"✅ Suggested agents: {parsed_intent.suggested_agents}")
        
        # Step 2: Test agent registry
        print("\n📋 Step 2: Testing Agent Registry")
        registry = AgentRegistry()
        branding_agent = registry.get_agent("branding_agent")
        print(f"✅ Branding agent found: {branding_agent is not None}")
        
        if branding_agent:
            metadata = registry.get_agent_metadata("branding_agent")
            print(f"✅ Agent metadata: {metadata.get('name')}")
        
        # Step 3: Test agent execution directly
        print("\n📋 Step 3: Testing Agent Execution")
        try:
            agent = BrandingAgent()
            test_state = {
                "business_idea": "I want to start a coffee shop",
                "product_type": "coffee",
                "target_audience": "professionals"
            }
            
            result = agent.run(test_state)
            print(f"✅ Agent execution successful")
            print(f"✅ Brand name: {result.get('brand_name', 'N/A')}")
            print(f"✅ Logo prompt: {result.get('logo_prompt', 'N/A')[:50]}...")
            
        except Exception as e:
            print(f"❌ Agent execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Test agent executor
        print("\n📋 Step 4: Testing Agent Executor")
        try:
            import redis
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            from orchestration.agent_communication import AgentMessageBus
            message_bus = AgentMessageBus(redis_client)
            
            executor = AgentExecutor(redis_client, message_bus)
            
            # Test invocation
            invocation_id = await executor.invoke_agent(
                agent_id="branding_agent",
                input_state=test_state
            )
            print(f"✅ Invocation ID: {invocation_id}")
            
            # Wait for response
            await asyncio.sleep(2)
            
            response = await executor.get_response(invocation_id)
            if response:
                print(f"✅ Response status: {response.status}")
                if response.status.value == "completed":
                    print(f"✅ Output state: {list(response.output_state.keys())}")
                else:
                    print(f"❌ Error: {response.error_message}")
            else:
                print("❌ No response received")
                
        except Exception as e:
            print(f"❌ Agent executor failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 5: Test full orchestrator
        print("\n📋 Step 5: Testing Full Orchestrator")
        try:
            config = OrchestrationConfig(
                redis_url="redis://localhost:6379",
                max_concurrent_invocations=5,
                response_cache_ttl_hours=1,
                enable_logging=True,
                enable_metrics=True
            )
            
            orchestrator = BrandingOrchestrator(config)
            success = await orchestrator.initialize()
            
            if success:
                print("✅ Orchestrator initialized")
                
                # Test request processing
                response = await orchestrator.process_request(
                    user_request="I need a brand name for my eco-friendly pen business",
                    session_id="debug_session"
                )
                
                print(f"✅ Response status: {response.get('status')}")
                print(f"✅ Intent category: {response.get('orchestration', {}).get('intent_category')}")
                
                if response.get('status') == 'success':
                    print(f"✅ Brand name: {response.get('brand_name', 'N/A')}")
                else:
                    print(f"❌ Error: {response.get('message')}")
                    
            else:
                print("❌ Orchestrator initialization failed")
                
        except Exception as e:
            print(f"❌ Full orchestrator test failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Orchestration Debug")
    print("Make sure Redis is running: redis-server --daemonize yes")
    print()
    
    try:
        asyncio.run(debug_step_by_step())
    except KeyboardInterrupt:
        print("\n⏹️ Debug interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        import traceback
        traceback.print_exc() 