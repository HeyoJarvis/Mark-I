"""
Test Semantic Architecture with Known Problematic Cases

This test validates that the new semantic, capability-based architecture
solves the core problems:
1. Logo generation issues
2. Market research routing problems  
3. Multi-agent coordination
4. Context preservation
"""

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Import the new semantic architecture
from orchestration.semantic_request_parser import SemanticRequestParser
from orchestration.semantic_orchestrator import SemanticOrchestrator
from orchestration.semantic_state import SemanticStateManager, create_semantic_state_system

# Mock AI engine for testing
from ai_engines.mock_engine import MockAIEngine

logger = logging.getLogger(__name__)


class SemanticArchitectureTest:
    """Comprehensive test of the semantic architecture."""
    
    def __init__(self):
        # Use mock AI engine for testing
        self.ai_engine = MockAIEngine()
        self.orchestrator = SemanticOrchestrator(ai_engine=self.ai_engine)
        self.state_manager, self.middleware = create_semantic_state_system()
        
    async def test_logo_generation_case(self):
        """Test the problematic logo generation case."""
        print("\n=== Testing Logo Generation Case ===")
        
        request = "Create a professional logo for my tech startup called InnovateTech"
        session_id = "logo_test_session"
        
        try:
            # Process request with semantic architecture
            workflow_state = await self.orchestrator.process_request(request, session_id)
            
            print(f"Status: {workflow_state.overall_status}")
            print(f"Understanding: {workflow_state.understanding.business_goal}")
            print(f"Strategy: {workflow_state.understanding.execution_strategy}")
            print(f"Selected Agents: {workflow_state.understanding.recommended_agents}")
            print(f"Capabilities: {[cap.value for cap in workflow_state.understanding.primary_capabilities]}")
            
            # Validate direct routing
            assert "logo_generation_agent" in workflow_state.understanding.recommended_agents
            assert workflow_state.understanding.execution_strategy.value in ["single_agent", "parallel_multi"]
            
            # Check context preservation
            if workflow_state.agent_states:
                agent_id = list(workflow_state.agent_states.keys())[0]
                agent_state = workflow_state.agent_states[agent_id]
                assert agent_state.task_description is not None
                print(f"Task Description: {agent_state.task_description}")
            
            print("✓ Logo generation test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Logo generation test FAILED: {e}")
            return False
    
    async def test_market_research_case(self):
        """Test the problematic market research case."""
        print("\n=== Testing Market Research Case ===")
        
        request = "I need comprehensive market research for electric vehicle charging stations in urban areas"
        session_id = "market_test_session"
        
        try:
            # Test semantic parsing first
            parser = SemanticRequestParser(self.ai_engine)
            understanding = await parser.parse_request(request)
            
            print(f"Business Goal: {understanding.business_goal}")
            print(f"Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
            print(f"Agents: {understanding.recommended_agents}")
            print(f"Confidence: {understanding.confidence_score}")
            
            # Validate direct capability mapping
            from orchestration.semantic_request_parser import CapabilityCategory
            assert CapabilityCategory.MARKET_ANALYSIS in understanding.primary_capabilities
            
            # Test full orchestration
            workflow_state = await self.orchestrator.process_request(request, session_id)
            
            print(f"Execution Status: {workflow_state.overall_status}")
            print(f"Results Keys: {list(workflow_state.results.keys()) if workflow_state.results else 'None'}")
            
            # Validate no department routing
            assert workflow_state.understanding.execution_strategy != "department_routing"
            
            print("✓ Market research test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Market research test FAILED: {e}")
            return False
    
    async def test_multi_agent_coordination(self):
        """Test complex multi-agent workflow."""
        print("\n=== Testing Multi-Agent Coordination ===")
        
        request = "Create a complete brand package: logo, brand strategy, market research, and website for my sustainable fashion startup"
        session_id = "multi_agent_session"
        
        try:
            workflow_state = await self.orchestrator.process_request(request, session_id)
            
            print(f"Status: {workflow_state.overall_status}")
            print(f"Strategy: {workflow_state.understanding.execution_strategy}")
            print(f"Agent Count: {len(workflow_state.understanding.recommended_agents)}")
            print(f"Agents: {workflow_state.understanding.recommended_agents}")
            
            # Validate multi-agent coordination
            assert len(workflow_state.understanding.recommended_agents) > 1
            assert workflow_state.understanding.execution_strategy in ["parallel_multi", "sequential_multi", "hybrid"]
            
            # Check that all agents have appropriate capabilities
            capabilities = workflow_state.understanding.primary_capabilities
            print(f"Capabilities: {[cap.value for cap in capabilities]}")
            
            # Validate context preservation across agents
            if workflow_state.agent_states:
                for agent_id, agent_state in workflow_state.agent_states.items():
                    print(f"{agent_id}: {agent_state.status}, Progress: {agent_state.progress}")
            
            print("✓ Multi-agent coordination test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Multi-agent coordination test FAILED: {e}")
            return False
    
    async def test_context_preservation(self):
        """Test that semantic context is preserved throughout execution."""
        print("\n=== Testing Context Preservation ===")
        
        request = "Build a brand and website for my artisan coffee roastery targeting coffee enthusiasts who value sustainability"
        session_id = "context_test_session"
        
        try:
            # Create initial context
            parser = SemanticRequestParser(self.ai_engine)
            understanding = await parser.parse_request(request)
            
            workflow_id = "test_context_workflow"
            context = await self.state_manager.create_semantic_context(
                workflow_id, session_id, understanding
            )
            
            print(f"Initial Context - Goal: {context.business_goal}")
            print(f"Business Context: {context.business_context}")
            print(f"User Preferences: {context.user_preferences}")
            
            # Simulate agent execution and context evolution
            mock_branding_result = {
                "brand_strategy": {
                    "mission": "Sustainable coffee excellence",
                    "values": ["sustainability", "quality", "craftsmanship"]
                },
                "context_updates": {
                    "target_demographic": "eco-conscious coffee lovers",
                    "price_point": "premium"
                },
                "preferences": {
                    "color_palette": "earth_tones",
                    "brand_personality": "authentic_artisan"
                }
            }
            
            # Update context with result
            await self.state_manager.enrich_context_from_agent_result(
                workflow_id, session_id, "branding_agent", mock_branding_result
            )
            
            # Get enriched context for next agent
            website_context = await self.state_manager.get_agent_execution_context(
                workflow_id, "website_generator_agent", 
                understanding.primary_capabilities[0] if understanding.primary_capabilities else None
            )
            
            print(f"Enriched Context Keys: {list(website_context.keys())}")
            print(f"Previous Results: {list(website_context['previous_results'].keys())}")
            print(f"Updated Preferences: {website_context['user_preferences']}")
            
            # Validate context flow
            assert "branding_agent" in website_context["previous_results"]
            assert "color_palette" in website_context["user_preferences"]
            assert website_context["business_context"]["target_demographic"] == "eco-conscious coffee lovers"
            
            # Check context evolution tracking
            updated_context = await self.state_manager.get_semantic_context(workflow_id)
            print(f"Evolution Entries: {len(updated_context.context_evolution)}")
            
            print("✓ Context preservation test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Context preservation test FAILED: {e}")
            return False
    
    async def test_single_ai_call_efficiency(self):
        """Test that we use only one AI call for understanding."""
        print("\n=== Testing Single AI Call Efficiency ===")
        
        # Mock the AI engine to count calls
        call_count = 0
        original_generate = self.ai_engine.generate
        
        async def counting_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return await original_generate(*args, **kwargs)
        
        self.ai_engine.generate = counting_generate
        
        try:
            request = "Create a logo and conduct market research for my food delivery app"
            
            # Parse request
            parser = SemanticRequestParser(self.ai_engine)
            understanding = await parser.parse_request(request)
            
            print(f"AI Calls Made: {call_count}")
            print(f"Understanding Quality: {understanding.confidence_score}")
            print(f"Capabilities Found: {len(understanding.primary_capabilities)}")
            print(f"Agents Mapped: {len(understanding.recommended_agents)}")
            
            # Validate single call achieved comprehensive understanding
            assert call_count == 1, f"Expected 1 AI call, got {call_count}"
            assert understanding.confidence_score > 0.5
            assert len(understanding.primary_capabilities) > 0
            assert len(understanding.recommended_agents) > 0
            
            print("✓ Single AI call efficiency test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Single AI call efficiency test FAILED: {e}")
            return False
        finally:
            # Restore original method
            self.ai_engine.generate = original_generate
    
    async def test_direct_agent_access(self):
        """Test that agents are accessed directly without department routing."""
        print("\n=== Testing Direct Agent Access ===")
        
        request = "Generate a logo for my bakery"
        session_id = "direct_access_session"
        
        try:
            workflow_state = await self.orchestrator.process_request(request, session_id)
            
            # Check execution plan for direct access
            execution_plan = workflow_state.understanding.execution_plan
            print(f"Execution Plan: {json.dumps(execution_plan, indent=2)}")
            
            # Validate no department intermediaries
            assert "department" not in str(execution_plan).lower()
            assert "direct" in str(execution_plan).lower() or "agent_mappings" in execution_plan
            
            # Check that agents are selected based on capabilities
            agents = workflow_state.understanding.recommended_agents
            capabilities = workflow_state.understanding.primary_capabilities
            
            print(f"Direct Agent Selection: {agents}")
            print(f"Based on Capabilities: {[cap.value for cap in capabilities]}")
            
            # Validate capability-based selection
            from orchestration.semantic_request_parser import CapabilityCategory
            if CapabilityCategory.LOGO_GENERATION in capabilities:
                assert "logo_generation_agent" in agents
            
            print("✓ Direct agent access test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ Direct agent access test FAILED: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all semantic architecture tests."""
        print("🚀 Starting Semantic Architecture Tests")
        print("=" * 50)
        
        tests = [
            ("Single AI Call Efficiency", self.test_single_ai_call_efficiency()),
            ("Direct Agent Access", self.test_direct_agent_access()),
            ("Logo Generation Case", self.test_logo_generation_case()),
            ("Market Research Case", self.test_market_research_case()),
            ("Context Preservation", self.test_context_preservation()),
            ("Multi-Agent Coordination", self.test_multi_agent_coordination())
        ]
        
        results = []
        for test_name, test_coro in tests:
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ {test_name} CRASHED: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL" 
            print(f"{status:<8} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests PASSED! Semantic architecture is working correctly.")
        else:
            print("⚠️  Some tests failed. Review implementation.")
        
        return passed == total


# Performance comparison test
async def test_performance_comparison():
    """Compare performance of semantic vs traditional routing."""
    print("\n=== Performance Comparison ===")
    
    requests = [
        "Create a logo for my startup",
        "Research the market for electric vehicles",
        "Build a complete brand identity with logo and website",
        "Generate market research and create sales materials"
    ]
    
    # Test semantic architecture
    semantic_orchestrator = SemanticOrchestrator(MockAIEngine())
    
    for request in requests:
        start_time = datetime.utcnow()
        
        try:
            result = await semantic_orchestrator.process_request(request, "perf_test")
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            print(f"Request: {request[:50]}...")
            print(f"  Semantic Duration: {duration:.2f}s")
            print(f"  Status: {result.overall_status}")
            print(f"  Agents: {len(result.understanding.recommended_agents)}")
            print()
            
        except Exception as e:
            print(f"  Failed: {e}")


if __name__ == "__main__":
    async def main():
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Run comprehensive tests
        tester = SemanticArchitectureTest()
        success = await tester.run_all_tests()
        
        # Run performance comparison
        await test_performance_comparison()
        
        return success
    
    # Run tests
    success = asyncio.run(main())
    exit(0 if success else 1)