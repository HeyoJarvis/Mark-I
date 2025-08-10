#!/usr/bin/env python3
"""
Demo: Branding Agent Orchestration Integration

This demo shows the complete integration of the BrandingAgent into the
HeyJarvis orchestration layer, demonstrating all the key features:
- Intent-driven routing
- Agent invocation and response handling
- Feedback loops and revision support
- Logging and traceability
- Security and isolation
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig
from orchestration.branding_orchestration_config import OrchestrationIntegrationGuide, SecurityAndIsolationGuide


class OrchestrationDemo:
    """Demo class for showcasing orchestration integration."""
    
    def __init__(self):
        """Initialize the demo."""
        self.orchestrator = None
        self.session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def setup(self):
        """Set up the orchestration demo."""
        print("🚀 Setting up Branding Agent Orchestration Demo")
        print("=" * 60)
        
        # Create configuration
        config = OrchestrationConfig(
            redis_url="redis://localhost:6379",
            max_concurrent_invocations=5,
            response_cache_ttl_hours=1,
            enable_logging=True,
            enable_metrics=True
        )
        
        # Initialize orchestrator
        self.orchestrator = BrandingOrchestrator(config)
        
        # Initialize components
        success = await self.orchestrator.initialize()
        if not success:
            print("❌ Failed to initialize orchestrator")
            return False
        
        print("✅ Orchestrator initialized successfully")
        return True
    
    async def demo_intent_parsing(self):
        """Demonstrate intent parsing capabilities."""
        print("\n🎯 Demo: Intent-Driven Routing")
        print("-" * 40)
        
        # Test cases for intent parsing
        test_cases = [
            {
                "request": "I need help coming up with a name for my eco-friendly pen business",
                "expected": "branding",
                "description": "Branding request with clear intent"
            },
            {
                "request": "Can you design a logo for my new coffee shop?",
                "expected": "branding", 
                "description": "Logo design request"
            },
            {
                "request": "I want to create a brand identity for my tech startup",
                "expected": "branding",
                "description": "Brand identity request"
            },
            {
                "request": "Help me find leads for my SaaS product",
                "expected": "sales",
                "description": "Sales request (should be routed to sales agent)"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['description']}")
            print(f"Request: {test_case['request']}")
            
            try:
                # Process request
                response = await self.orchestrator.process_request(
                    user_request=test_case['request'],
                    session_id=self.session_id
                )
                
                # Extract intent information
                orchestration_info = response.get('orchestration', {})
                intent_category = orchestration_info.get('intent_category', 'unknown')
                confidence = orchestration_info.get('confidence', 'unknown')
                
                print(f"✅ Intent Category: {intent_category}")
                print(f"✅ Confidence: {confidence}")
                print(f"✅ Status: {response.get('status', 'unknown')}")
                
                if intent_category == 'branding' and response.get('status') == 'success':
                    print(f"✅ Brand Name: {response.get('brand_name', 'N/A')}")
                    print(f"✅ Color Palette: {response.get('color_palette', [])}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def demo_agent_invocation(self):
        """Demonstrate agent invocation and response handling."""
        print("\n🤖 Demo: Agent Invocation & Response Handling")
        print("-" * 50)
        
        # Test different branding scenarios
        scenarios = [
            {
                "name": "Premium Pen Brand",
                "request": "I want to start a premium pen brand that focuses on luxury writing instruments for professionals and collectors",
                "context": {
                    "industry": "luxury_goods",
                    "target_audience": "professionals"
                }
            },
            {
                "name": "Eco-Friendly Water Bottles",
                "request": "Creating sustainable, reusable water bottles made from recycled materials to reduce plastic waste",
                "context": {
                    "industry": "sustainability",
                    "target_audience": "environmentally_conscious"
                }
            },
            {
                "name": "AI-Powered Fitness App",
                "request": "Developing a mobile app that uses AI to create personalized workout plans and track fitness progress",
                "context": {
                    "industry": "health_technology",
                    "target_audience": "fitness_enthusiasts"
                }
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📋 Scenario: {scenario['name']}")
            print(f"Request: {scenario['request']}")
            
            try:
                # Process request
                response = await self.orchestrator.process_request(
                    user_request=scenario['request'],
                    session_id=self.session_id,
                    context=scenario['context']
                )
                
                if response.get('status') == 'success':
                    print(f"✅ Brand Name: {response.get('brand_name')}")
                    print(f"✅ Logo Prompt: {response.get('logo_prompt', 'N/A')[:100]}...")
                    print(f"✅ Color Palette: {response.get('color_palette', [])}")
                    print(f"✅ Domain Suggestions: {response.get('domain_suggestions', [])}")
                    print(f"✅ Execution Time: {response.get('execution_time_ms', 0)}ms")
                else:
                    print(f"❌ Error: {response.get('message', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Exception: {e}")
    
    async def demo_feedback_loops(self):
        """Demonstrate feedback loops and revision support."""
        print("\n🔄 Demo: Feedback Loops & Revision Support")
        print("-" * 45)
        
        # Initial request
        initial_request = "I need a brand name for my coffee subscription service"
        print(f"📋 Initial Request: {initial_request}")
        
        try:
            # Process initial request
            initial_response = await self.orchestrator.process_request(
                user_request=initial_request,
                session_id=self.session_id
            )
            
            if initial_response.get('status') == 'success':
                print(f"✅ Initial Brand: {initial_response.get('brand_name')}")
                
                # Get invocation ID for feedback
                orchestration_info = initial_response.get('orchestration', {})
                invocation_id = orchestration_info.get('request_id')
                
                if invocation_id:
                    print(f"\n📝 Submitting feedback for revision...")
                    
                    # Submit revision request
                    feedback_response = await self.orchestrator.submit_feedback(
                        invocation_id=invocation_id,
                        feedback_type="revision_request",
                        feedback_text="Can you make the brand name more modern and unique?",
                        rating=3
                    )
                    
                    print(f"✅ Feedback Status: {feedback_response.get('status')}")
                    print(f"✅ Feedback ID: {feedback_response.get('feedback_id')}")
                    
                    # Wait a moment for revision to process
                    await asyncio.sleep(2)
                    
                    # Check if revision was triggered
                    status_response = await self.orchestrator.get_response_status(invocation_id)
                    print(f"✅ Status Check: {status_response.get('status')}")
                
            else:
                print(f"❌ Initial request failed: {initial_response.get('message')}")
                
        except Exception as e:
            print(f"❌ Feedback demo failed: {e}")
    
    async def demo_logging_and_traceability(self):
        """Demonstrate logging and traceability features."""
        print("\n📊 Demo: Logging & Traceability")
        print("-" * 35)
        
        # Get metrics
        metrics = await self.orchestrator.get_metrics()
        print(f"📈 Total Requests: {metrics.total_requests}")
        print(f"📈 Successful Requests: {metrics.successful_requests}")
        print(f"📈 Failed Requests: {metrics.failed_requests}")
        print(f"📈 Average Response Time: {metrics.average_response_time_ms:.2f}ms")
        
        # Health check
        health = await self.orchestrator.health_check()
        print(f"🏥 Overall Health: {health.get('status')}")
        print(f"🏥 Components: {json.dumps(health.get('components', {}), indent=2)}")
        
        # Show active sessions
        print(f"👥 Active Sessions: {len(self.orchestrator.active_sessions)}")
    
    async def demo_security_and_isolation(self):
        """Demonstrate security and isolation features."""
        print("\n🛡️ Demo: Security & Isolation")
        print("-" * 35)
        
        # Show security features
        security_features = SecurityAndIsolationGuide.get_security_features()
        print("🔒 Security Features Implemented:")
        for feature in security_features:
            print(f"  • {feature['feature']}: {feature['description']}")
        
        # Show isolation patterns
        isolation_patterns = SecurityAndIsolationGuide.get_isolation_patterns()
        print("\n🔒 Isolation Patterns:")
        for pattern in isolation_patterns:
            print(f"  • {pattern['pattern']}: {pattern['description']}")
        
        # Test concurrent request handling
        print(f"\n⚡ Testing concurrent request handling...")
        
        # Create multiple concurrent requests
        requests = [
            "I need a brand name for my tech startup",
            "Can you design a logo for my restaurant?",
            "I want to create a brand for my fitness app"
        ]
        
        tasks = []
        for i, request in enumerate(requests):
            task = asyncio.create_task(
                self.orchestrator.process_request(
                    user_request=request,
                    session_id=f"{self.session_id}_concurrent_{i}"
                )
            )
            tasks.append(task)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"✅ Concurrent requests completed:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ❌ Request {i+1}: {result}")
            else:
                status = result.get('status', 'unknown')
                print(f"  ✅ Request {i+1}: {status}")
    
    async def demo_api_integration(self):
        """Demonstrate API integration patterns."""
        print("\n🔌 Demo: API Integration Patterns")
        print("-" * 40)
        
        # Show API examples
        api_examples = OrchestrationIntegrationGuide.get_api_examples()
        
        for i, example in enumerate(api_examples, 1):
            print(f"\n📋 API Example {i}: {example['endpoint']}")
            print(f"Description: {example['description']}")
            print(f"Request: {json.dumps(example['request'], indent=2)}")
            print(f"Response: {json.dumps(example['response'], indent=2)}")
    
    async def demo_error_handling(self):
        """Demonstrate error handling and graceful degradation."""
        print("\n⚠️ Demo: Error Handling & Graceful Degradation")
        print("-" * 50)
        
        # Test various error scenarios
        error_scenarios = [
            {
                "name": "Empty Request",
                "request": "",
                "expected": "error or clarification"
            },
            {
                "name": "Unsupported Intent",
                "request": "Help me with my taxes",
                "expected": "not_supported status"
            },
            {
                "name": "Malformed Request",
                "request": "!@#$%^&*()",
                "expected": "fallback or error"
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n📋 Error Scenario: {scenario['name']}")
            print(f"Request: '{scenario['request']}'")
            print(f"Expected: {scenario['expected']}")
            
            try:
                response = await self.orchestrator.process_request(
                    user_request=scenario['request'],
                    session_id=self.session_id
                )
                
                print(f"✅ Actual Result: {response.get('status')}")
                if response.get('message'):
                    print(f"✅ Message: {response.get('message')}")
                
            except Exception as e:
                print(f"❌ Exception: {e}")
    
    async def run_complete_demo(self):
        """Run the complete orchestration demo."""
        print("🎭 Branding Agent Orchestration Integration Demo")
        print("=" * 60)
        print("This demo showcases the complete integration of the BrandingAgent")
        print("into the HeyJarvis orchestration layer.")
        print()
        
        # Setup
        if not await self.setup():
            return
        
        try:
            # Run all demos
            await self.demo_intent_parsing()
            await self.demo_agent_invocation()
            await self.demo_feedback_loops()
            await self.demo_logging_and_traceability()
            await self.demo_security_and_isolation()
            await self.demo_api_integration()
            await self.demo_error_handling()
            
            print("\n🎉 Demo completed successfully!")
            print("\n📚 Key Features Demonstrated:")
            print("  ✅ Intent-driven routing with AI-powered parsing")
            print("  ✅ Agent invocation and response handling")
            print("  ✅ Feedback loops and revision support")
            print("  ✅ Comprehensive logging and traceability")
            print("  ✅ Security and isolation mechanisms")
            print("  ✅ Error handling and graceful degradation")
            print("  ✅ API integration patterns")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            if self.orchestrator:
                await self.orchestrator.cleanup()
                print("\n🧹 Cleanup completed")


async def main():
    """Main demo function."""
    demo = OrchestrationDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    print("🚀 Starting Branding Agent Orchestration Integration Demo")
    print("Make sure Redis is running: redis-server")
    print("Set ANTHROPIC_API_KEY environment variable for AI features")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 