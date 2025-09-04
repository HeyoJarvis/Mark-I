#!/usr/bin/env python3
"""
Test script for Branding Agent Orchestration Integration

This script tests the complete orchestration integration to ensure
all components work together correctly.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig


async def test_orchestration_integration():
    """Test the complete orchestration integration."""
    print("🧪 Testing Branding Agent Orchestration Integration")
    print("=" * 60)
    
    try:
        # Test 1: Initialize orchestrator
        print("\n📋 Test 1: Initializing Orchestrator")
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
            print("✅ Orchestrator initialized successfully")
        else:
            print("❌ Orchestrator initialization failed")
            return
        
        # Test 2: Intent parsing
        print("\n📋 Test 2: Intent Parsing")
        test_requests = [
            "I need help coming up with a name for my eco-friendly pen business",
            "Can you design a logo for my coffee shop?",
            "Help me find leads for my SaaS product"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n  Request {i}: {request}")
            
            try:
                response = await orchestrator.process_request(
                    user_request=request,
                    session_id=f"test_session_{i}"
                )
                
                status = response.get('status', 'unknown')
                intent_category = response.get('orchestration', {}).get('intent_category', 'unknown')
                
                print(f"    ✅ Status: {status}")
                print(f"    ✅ Intent Category: {intent_category}")
                
                if status == 'success' and intent_category == 'branding':
                    brand_name = response.get('brand_name', 'N/A')
                    print(f"    ✅ Brand Name: {brand_name}")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # Test 3: Health check
        print("\n📋 Test 3: Health Check")
        try:
            health = await orchestrator.health_check()
            print(f"✅ Health Status: {health.get('status')}")
            print(f"✅ Components: {list(health.get('components', {}).keys())}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test 4: Metrics
        print("\n📋 Test 4: Metrics")
        try:
            metrics = await orchestrator.get_metrics()
            print(f"✅ Total Requests: {metrics.total_requests}")
            print(f"✅ Successful Requests: {metrics.successful_requests}")
            print(f"✅ Failed Requests: {metrics.failed_requests}")
            print(f"✅ Average Response Time: {metrics.average_response_time_ms:.2f}ms")
        except Exception as e:
            print(f"❌ Metrics failed: {e}")
        
        # Test 5: Cleanup
        print("\n📋 Test 5: Cleanup")
        try:
            await orchestrator.cleanup()
            print("✅ Cleanup completed successfully")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


async def test_basic_functionality():
    """Test basic functionality without Redis dependency."""
    print("\n🔧 Testing Basic Functionality (No Redis)")
    print("-" * 50)
    
    try:
        # Test intent parser directly
        from orchestration.intent_parser import IntentParser
        
        parser = IntentParser()
        print("✅ Intent parser created successfully")
        
        # Test rule-based parsing
        test_request = "I need a brand name for my coffee business"
        result = await parser.parse_intent(test_request)
        
        print(f"✅ Intent parsed: {result.primary_intent}")
        print(f"✅ Confidence: {result.confidence}")
        print(f"✅ Suggested agents: {result.suggested_agents}")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Orchestration Integration Tests")
    print("Make sure Redis is running: redis-server --daemonize yes")
    print()
    
    try:
        # Run basic functionality test first
        asyncio.run(test_basic_functionality())
        
        # Run full integration test
        asyncio.run(test_orchestration_integration())
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc() 