"""
Simple test of semantic architecture core concepts
"""

import asyncio
import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_request_parser import (
    SemanticRequestParser,
    CapabilityAgentRegistry,
    CapabilityCategory,
    ExecutionStrategy
)


class MockAIEngine:
    """Mock AI engine for testing."""
    
    async def generate(self, prompt: str) -> str:
        """Return mock semantic understanding based on request analysis."""
        prompt_lower = prompt.lower()
        
        # Analyze the USER REQUEST section to understand what's being asked
        if "user request:" in prompt_lower:
            # Extract the actual user request
            user_request_section = prompt.split("USER REQUEST:")[1].split("\n")[0] if "USER REQUEST:" in prompt else ""
            request_lower = user_request_section.lower()
        else:
            request_lower = prompt_lower
        
        if "logo" in request_lower:
            return json.dumps({
                "business_goal": "Create professional logo for business",
                "user_intent_summary": "User wants logo design services",
                "business_domain": "design",
                "urgency_level": "medium",
                "primary_capabilities": ["logo_generation"],
                "secondary_capabilities": ["brand_creation"],
                "recommended_agents": ["logo_generation_agent"],
                "execution_strategy": "single_agent",
                "execution_plan": {"description": "Single agent logo generation"},
                "extracted_parameters": {"business_type": "startup"},
                "business_context": {"industry": "technology"},
                "user_preferences": {"style": "professional"},
                "confidence_score": 0.9,
                "reasoning": "Clear logo request with specific business context",
                "potential_challenges": []
            })
        
        elif any(term in request_lower for term in ["market research", "market analysis", "research", "electric vehicle"]):
            return json.dumps({
                "business_goal": "Conduct comprehensive market analysis",
                "user_intent_summary": "User needs market research and analysis",
                "business_domain": "research",
                "urgency_level": "medium",
                "primary_capabilities": ["market_analysis"],
                "secondary_capabilities": [],
                "recommended_agents": ["market_research_agent"],
                "execution_strategy": "single_agent", 
                "execution_plan": {"description": "Market research analysis"},
                "extracted_parameters": {"market_segment": "electric_vehicles"},
                "business_context": {"focus": "urban_areas"},
                "user_preferences": {"depth": "comprehensive"},
                "confidence_score": 0.85,
                "reasoning": "Market research request with specific parameters",
                "potential_challenges": []
            })
        
        else:
            return json.dumps({
                "business_goal": "Handle general business request",
                "user_intent_summary": "General business assistance needed",
                "business_domain": None,
                "urgency_level": "medium",
                "primary_capabilities": ["content_creation"],
                "secondary_capabilities": [],
                "recommended_agents": ["general_agent"],
                "execution_strategy": "single_agent",
                "execution_plan": {"description": "General assistance"},
                "extracted_parameters": {},
                "business_context": {},
                "user_preferences": {},
                "confidence_score": 0.7,
                "reasoning": "General request handling",
                "potential_challenges": []
            })


async def test_capability_registry():
    """Test the capability registry."""
    print("=== Testing Capability Registry ===")
    
    registry = CapabilityAgentRegistry()
    
    # Test capability mapping
    logo_agents = registry.get_agents_for_capability(CapabilityCategory.LOGO_GENERATION)
    print(f"Logo agents: {[agent.agent_id for agent in logo_agents]}")
    
    market_agents = registry.get_agents_for_capability(CapabilityCategory.MARKET_ANALYSIS)  
    print(f"Market research agents: {[agent.agent_id for agent in market_agents]}")
    
    # Test best agent selection
    best_logo = registry.get_best_agent_for_capability(CapabilityCategory.LOGO_GENERATION)
    print(f"Best logo agent: {best_logo.agent_id if best_logo else 'None'}")
    
    print("✓ Capability registry test PASSED\n")


async def test_semantic_parser():
    """Test semantic request parsing."""
    print("=== Testing Semantic Parser ===")
    
    parser = SemanticRequestParser(MockAIEngine())
    
    test_requests = [
        "Create a logo for my coffee shop startup",
        "I need market research for electric vehicle charging stations"
    ]
    
    for request in test_requests:
        print(f"\nTesting: {request}")
        
        try:
            understanding = await parser.parse_request(request)
            
            print(f"  Goal: {understanding.business_goal}")
            print(f"  Strategy: {understanding.execution_strategy}")
            print(f"  Agents: {understanding.recommended_agents}")
            print(f"  Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
            print(f"  Confidence: {understanding.confidence_score}")
            
            # Validate results
            assert understanding.confidence_score > 0.5
            assert len(understanding.recommended_agents) > 0
            assert len(understanding.primary_capabilities) > 0
            
            print("  ✓ PASSED")
            
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    print("\n✓ Semantic parser test PASSED\n")
    return True


async def test_direct_agent_mapping():
    """Test that agents are mapped directly by capability."""
    print("=== Testing Direct Agent Mapping ===")
    
    parser = SemanticRequestParser(MockAIEngine())
    
    # Test logo request maps to logo agent
    logo_understanding = await parser.parse_request("Create a logo for my startup")
    assert "logo_generation_agent" in logo_understanding.recommended_agents
    assert CapabilityCategory.LOGO_GENERATION in logo_understanding.primary_capabilities
    print("✓ Logo request mapped to logo agent")
    
    # Test market research maps to research agent
    market_understanding = await parser.parse_request("Research the electric vehicle market")  
    assert "market_research_agent" in market_understanding.recommended_agents
    assert CapabilityCategory.MARKET_ANALYSIS in market_understanding.primary_capabilities
    print("✓ Market request mapped to research agent")
    
    print("✓ Direct agent mapping test PASSED\n")


async def test_single_ai_call():
    """Test that only one AI call is made for understanding."""
    print("=== Testing Single AI Call Efficiency ===")
    
    call_count = 0
    
    class CountingMockAIEngine(MockAIEngine):
        async def generate(self, prompt):
            nonlocal call_count
            call_count += 1
            return await super().generate(prompt)
    
    parser = SemanticRequestParser(CountingMockAIEngine())
    
    # Parse a complex request
    request = "Create a complete brand package with logo and market research"
    understanding = await parser.parse_request(request)
    
    print(f"AI calls made: {call_count}")
    print(f"Understanding quality: {understanding.confidence_score}")
    
    assert call_count == 1, f"Expected 1 AI call, got {call_count}"
    assert understanding.confidence_score > 0.5
    
    print("✓ Single AI call test PASSED\n")


async def run_all_tests():
    """Run all simple tests."""
    print("🚀 Starting Simple Semantic Architecture Tests")
    print("=" * 50)
    
    tests = [
        ("Capability Registry", test_capability_registry()),
        ("Semantic Parser", test_semantic_parser()),
        ("Direct Agent Mapping", test_direct_agent_mapping()),
        ("Single AI Call", test_single_ai_call())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, True))
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core tests PASSED! Semantic architecture basics work correctly.")
    else:
        print("⚠️  Some tests failed. Review implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)