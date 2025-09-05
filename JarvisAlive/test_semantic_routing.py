#!/usr/bin/env python3
"""
Test Semantic Routing to Advanced Email Orchestration

This script tests if the semantic chat interface can properly route
email orchestration requests to our advanced agent.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_semantic_routing():
    """Test semantic routing to advanced email orchestration."""
    print("🧪 Testing Semantic Routing to Advanced Email Orchestration")
    print("=" * 60)
    
    try:
        # Test 1: Check if agent is in registry
        print("\n1️⃣ Checking Agent Registry...")
        from orchestration.agent_integration import AgentRegistry
        
        registry = AgentRegistry()
        advanced_agent_class = registry.get_agent("advanced_email_orchestration_agent")
        
        if advanced_agent_class:
            print("✅ Advanced Email Orchestration Agent found in registry")
            print(f"   Agent class: {advanced_agent_class}")
            
            # Test 2: Try to instantiate the agent
            print("\n2️⃣ Testing Agent Instantiation...")
            try:
                agent_instance = advanced_agent_class()
                print("✅ Agent instantiated successfully")
                
                # Test 3: Test the run method
                print("\n3️⃣ Testing Agent Run Method...")
                test_input = {
                    'user_input': 'create an AI-powered email sequence for tech executives',
                    'task_type': 'create_sequence',
                    'business_idea': 'Tech executive outreach',
                    'target_audience': 'tech executives'
                }
                
                result = await agent_instance.run(test_input)
                
                if result.get('success'):
                    print("✅ Agent run method executed successfully")
                    print(f"   Message: {result.get('message', 'No message')}")
                    print(f"   Result keys: {list(result.get('result', {}).keys())}")
                else:
                    print(f"⚠️ Agent run method returned: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Agent instantiation/execution failed: {e}")
                
        else:
            print("❌ Advanced Email Orchestration Agent NOT found in registry")
            
            # List available agents
            print("\n📋 Available agents in registry:")
            for agent_id in registry.agents.keys():
                print(f"   • {agent_id}")
        
        # Test 4: Check capability registry
        print("\n4️⃣ Checking Capability Registry...")
        from orchestration.semantic_request_parser import CapabilityAgentRegistry, CapabilityCategory
        
        cap_registry = CapabilityAgentRegistry()
        email_capabilities = cap_registry.capability_map.get(CapabilityCategory.EMAIL_ORCHESTRATION, [])
        
        if email_capabilities:
            print("✅ Email orchestration capabilities found")
            for cap in email_capabilities:
                print(f"   • Agent: {cap.agent_id}")
                print(f"     Skills: {cap.specific_skills}")
        else:
            print("❌ No email orchestration capabilities found")
            
            # List available capabilities
            print("\n📋 Available capabilities:")
            for cap_category, caps in cap_registry.capability_map.items():
                print(f"   • {cap_category.value}: {len(caps)} agents")
        
        # Test 5: Test semantic parser
        print("\n5️⃣ Testing Semantic Parser...")
        from orchestration.semantic_request_parser import SemanticRequestParser
        
        # Create parser (will use mock AI if no API key)
        parser = SemanticRequestParser()
        
        test_request = "create an AI-powered email sequence for tech executives"
        print(f"   Request: '{test_request}'")
        
        try:
            understanding = await parser.parse_request(test_request)
            print("✅ Semantic parsing completed")
            print(f"   Business Goal: {understanding.business_goal}")
            print(f"   Primary Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
            print(f"   Recommended Agents: {understanding.recommended_agents}")
            print(f"   Confidence: {understanding.confidence_score}")
            
            # Check if our agent is recommended
            if "advanced_email_orchestration_agent" in understanding.recommended_agents:
                print("✅ Advanced Email Orchestration Agent is recommended!")
            else:
                print("⚠️ Advanced Email Orchestration Agent NOT recommended")
                print(f"   Recommended instead: {understanding.recommended_agents}")
                
        except Exception as e:
            print(f"❌ Semantic parsing failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function."""
    await test_semantic_routing()
    
    print("\n" + "=" * 60)
    print("🎯 Summary")
    print("=" * 60)
    print("This test checks if:")
    print("1. ✅ Agent is registered in the system")
    print("2. ✅ Agent can be instantiated and executed")
    print("3. ✅ Capabilities are mapped correctly")
    print("4. ✅ Semantic parser recognizes email requests")
    print("5. ✅ Parser recommends our advanced agent")
    print("\nIf all tests pass, the integration should work in semantic chat!")

if __name__ == "__main__":
    asyncio.run(main()) 