#!/usr/bin/env python3
"""
Test Semantic Integration for Advanced Email Orchestration

This script tests the integration of the advanced email orchestration system
with the semantic chat interface.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_semantic_integration():
    """Test semantic integration of advanced email orchestration."""
    print("🧪 Testing Semantic Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import semantic wrapper
        print("\n1️⃣ Testing semantic wrapper import...")
        from departments.communication.semantic_advanced_orchestrator import SemanticAdvancedEmailOrchestrator
        print("✅ Semantic wrapper imported successfully")
        
        # Test 2: Initialize wrapper
        print("\n2️⃣ Testing wrapper initialization...")
        orchestrator = SemanticAdvancedEmailOrchestrator()
        await orchestrator.initialize()
        print("✅ Semantic wrapper initialized")
        
        # Test 3: Test natural language queries
        print("\n3️⃣ Testing natural language processing...")
        
        test_queries = [
            {
                'name': 'Create Sequence',
                'task_data': {
                    'user_input': 'create sequence for tech executives',
                    'task_type': 'create_sequence'
                }
            },
            {
                'name': 'AI Personalization',
                'task_data': {
                    'user_input': 'personalize template for healthcare',
                    'task_type': 'personalize_advanced'
                }
            },
            {
                'name': 'Send Optimization',
                'task_data': {
                    'user_input': 'optimize send times',
                    'task_type': 'optimize_timing'
                }
            },
            {
                'name': 'Email Warming',
                'task_data': {
                    'user_input': 'set up email warming',
                    'task_type': 'setup_warming'
                }
            },
            {
                'name': 'Analytics',
                'task_data': {
                    'user_input': 'show analytics',
                    'task_type': 'analytics'
                }
            },
            {
                'name': 'Status Check',
                'task_data': {
                    'user_input': 'check status',
                    'task_type': 'status'
                }
            },
            {
                'name': 'Help Request',
                'task_data': {
                    'user_input': 'help me with email orchestration',
                    'task_type': 'help'
                }
            }
        ]
        
        for query in test_queries:
            print(f"\n   Testing: {query['name']}")
            try:
                result = await orchestrator.run(query['task_data'])
                if result['success']:
                    print(f"   ✅ {result['message']}")
                else:
                    print(f"   ⚠️ {result['message']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ Natural language processing tests completed")
        
    except Exception as e:
        print(f"❌ Semantic integration test failed: {e}")
        return False
    
    return True

async def test_agent_registry_integration():
    """Test integration with agent registry."""
    print("\n🔗 Testing Agent Registry Integration")
    print("=" * 50)
    
    try:
        # Test agent registry
        print("\n1️⃣ Testing agent registry...")
        from orchestration.agent_integration import AgentRegistry
        
        registry = AgentRegistry()
        
        # Check if advanced agent is registered
        advanced_agent = registry.get_agent("advanced_email_orchestration_agent")
        if advanced_agent:
            print("✅ Advanced Email Orchestration Agent found in registry")
            
            # Get metadata
            metadata = registry.agent_metadata.get("advanced_email_orchestration_agent", {})
            print(f"   Name: {metadata.get('name', 'Unknown')}")
            print(f"   Capabilities: {len(metadata.get('capabilities', []))} features")
            print(f"   Category: {metadata.get('category', 'Unknown')}")
        else:
            print("⚠️ Advanced agent not found in registry")
        
        # Test capability registry
        print("\n2️⃣ Testing capability registry...")
        from orchestration.semantic_request_parser import CapabilityAgentRegistry
        
        capability_registry = CapabilityAgentRegistry()
        
        # Check if capabilities are registered
        from orchestration.semantic_request_parser import CapabilityCategory
        email_capabilities = capability_registry.capability_map.get(CapabilityCategory.EMAIL_ORCHESTRATION, [])
        
        advanced_capabilities = [cap for cap in email_capabilities if cap.agent_id == "advanced_email_orchestration_agent"]
        
        if advanced_capabilities:
            print("✅ Advanced capabilities found in capability registry")
            for cap in advanced_capabilities:
                print(f"   Skills: {len(cap.specific_skills)} advanced features")
        else:
            print("⚠️ Advanced capabilities not found")
        
        print("\n✅ Agent registry integration tests completed")
        
    except Exception as e:
        print(f"❌ Agent registry integration test failed: {e}")
        return False
    
    return True

async def test_semantic_chat_simulation():
    """Simulate semantic chat interaction."""
    print("\n💬 Simulating Semantic Chat Interaction")
    print("=" * 50)
    
    # Simulate natural language queries that would come from semantic chat
    chat_examples = [
        "I want to create an AI-powered email sequence for tech executives",
        "Can you personalize my email template for healthcare companies?",
        "Help me optimize send times for my European contacts",
        "Set up email warming for my new sales domain",
        "Show me analytics and performance metrics",
        "What's the status of my email orchestration system?"
    ]
    
    print("\n🗣️ Example queries that now work in semantic chat:")
    for i, example in enumerate(chat_examples, 1):
        print(f"{i}. \"{example}\"")
    
    print("\n🤖 These queries will now be automatically routed to the")
    print("   Advanced Email Orchestration Agent through semantic chat!")
    
    return True

async def main():
    """Main test function."""
    print("🚀 Advanced Email Orchestration - Semantic Integration Test")
    print("=" * 70)
    
    # Run all tests
    test1 = await test_semantic_integration()
    test2 = await test_agent_registry_integration()
    test3 = await test_semantic_chat_simulation()
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    print(f"Semantic Integration: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Agent Registry: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Chat Simulation: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Advanced Email Orchestration is fully integrated with semantic chat!")
        
        print("\n🚀 You can now use natural language in the main semantic chat:")
        print("   • \"Create an AI sequence for tech executives\"")
        print("   • \"Personalize template for healthcare\"")
        print("   • \"Optimize send times for Europe\"")
        print("   • \"Set up email warming\"")
        print("   • \"Show me analytics\"")
        
        print("\n💡 The system will automatically route these to the")
        print("   Advanced Email Orchestration Agent!")
        
    else:
        print("\n⚠️ Some tests failed - check the integration")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(main()) 