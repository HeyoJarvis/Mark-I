#!/usr/bin/env python3
"""
Manual testing script for semantic architecture

Run this to manually test different request types and see how
the semantic system handles them compared to the old approach.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_request_parser import SemanticRequestParser, CapabilityCategory
from orchestration.semantic_orchestrator import SemanticOrchestrator
from orchestration.semantic_integration import SemanticJarvis
from ai_engines.mock_engine import MockAIEngine


class InteractiveSemanticTest:
    """Interactive testing for semantic architecture."""
    
    def __init__(self):
        print("🚀 Semantic Architecture Manual Tester")
        print("=" * 50)
        
        # Use mock engine for testing
        self.ai_engine = MockAIEngine()
        self.parser = SemanticRequestParser(self.ai_engine)
        self.orchestrator = SemanticOrchestrator(self.ai_engine)
        self.jarvis = SemanticJarvis(self.ai_engine)
    
    async def test_request_understanding(self, request: str):
        """Test how well the system understands a request."""
        print(f"\n🔍 ANALYZING REQUEST: {request}")
        print("-" * 50)
        
        try:
            understanding = await self.parser.parse_request(request)
            
            print(f"📋 Business Goal: {understanding.business_goal}")
            print(f"🎯 Intent Summary: {understanding.user_intent_summary}")
            print(f"🏢 Domain: {understanding.business_domain or 'Not specified'}")
            print(f"⚡ Strategy: {understanding.execution_strategy.value}")
            print(f"🤖 Recommended Agents: {understanding.recommended_agents}")
            print(f"⚙️  Primary Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
            print(f"🔧 Secondary Capabilities: {[cap.value for cap in understanding.secondary_capabilities]}")
            print(f"📊 Confidence: {understanding.confidence_score:.2f}")
            print(f"💭 Reasoning: {understanding.reasoning}")
            
            if understanding.extracted_parameters:
                print(f"📝 Parameters: {understanding.extracted_parameters}")
            
            if understanding.business_context:
                print(f"🏪 Business Context: {understanding.business_context}")
                
            return understanding
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None
    
    async def test_full_orchestration(self, request: str):
        """Test complete orchestration flow."""
        print(f"\n🔄 FULL ORCHESTRATION TEST: {request}")
        print("-" * 60)
        
        try:
            start_time = datetime.now()
            workflow_state = await self.orchestrator.process_request(request, "manual_test")
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"📈 Status: {workflow_state.overall_status.value}")
            print(f"📊 Progress: {workflow_state.progress:.1%}")
            
            if workflow_state.agent_states:
                print("🤖 Agent Execution Details:")
                for agent_id, agent_state in workflow_state.agent_states.items():
                    print(f"   • {agent_id}: {agent_state.status.value} ({agent_state.progress:.1%})")
                    if agent_state.error:
                        print(f"     ❌ Error: {agent_state.error}")
            
            if workflow_state.results:
                print(f"📋 Results Generated: {list(workflow_state.results.keys())}")
            
            if workflow_state.consolidated_result:
                print("📄 Final Result Summary:")
                print(json.dumps(workflow_state.consolidated_result, indent=2))
            
            if workflow_state.errors:
                print(f"⚠️  Errors: {workflow_state.errors}")
                
            return workflow_state
            
        except Exception as e:
            print(f"❌ ORCHESTRATION ERROR: {e}")
            return None
    
    async def test_semantic_jarvis(self, request: str):
        """Test SemanticJarvis interface (production-ready)."""
        print(f"\n🧠 SEMANTIC JARVIS TEST: {request}")
        print("-" * 60)
        
        try:
            start_time = datetime.now()
            response = await self.jarvis.process_request(request, "jarvis_test")
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"✅ Success: {response['success']}")
            print(f"🔧 Method: {response['method']}")
            print(f"📋 Business Goal: {response.get('business_goal', 'N/A')}")
            print(f"🎯 User Intent: {response.get('user_intent', 'N/A')}")
            print(f"⚡ Strategy: {response.get('execution_strategy', 'N/A')}")
            print(f"🤖 Agents: {response.get('agents_used', [])}")
            print(f"📊 Confidence: {response.get('confidence', 0):.2f}")
            
            if response.get('results'):
                print("📋 Results:")
                print(json.dumps(response['results'], indent=2))
            
            if response.get('errors'):
                print(f"⚠️  Errors: {response['errors']}")
                
            return response
            
        except Exception as e:
            print(f"❌ JARVIS ERROR: {e}")
            return None
    
    async def compare_with_legacy(self, request: str):
        """Compare semantic vs legacy approach."""
        print(f"\n⚖️  SEMANTIC vs LEGACY COMPARISON: {request}")
        print("-" * 70)
        
        # Test semantic
        print("🔵 SEMANTIC APPROACH:")
        semantic_start = datetime.now()
        semantic_response = await self.jarvis.process_request(request, "comparison_semantic")
        semantic_duration = (datetime.now() - semantic_start).total_seconds()
        
        print(f"   Duration: {semantic_duration:.2f}s")
        print(f"   Success: {semantic_response['success']}")
        print(f"   Agents: {semantic_response.get('agents_used', [])}")
        
        # Test legacy fallback
        print("\n🔴 LEGACY FALLBACK:")
        legacy_start = datetime.now()
        legacy_response = await self.jarvis.process_request(request, "comparison_legacy", use_legacy=True)
        legacy_duration = (datetime.now() - legacy_start).total_seconds()
        
        print(f"   Duration: {legacy_duration:.2f}s")
        print(f"   Success: {legacy_response['success']}")
        print(f"   Method: {legacy_response.get('method', 'N/A')}")
        
        # Comparison
        print(f"\n📊 PERFORMANCE COMPARISON:")
        if semantic_duration > 0 and legacy_duration > 0:
            speedup = legacy_duration / semantic_duration
            print(f"   Speed improvement: {speedup:.1f}x faster")
        
        print(f"   Semantic agents: {len(semantic_response.get('agents_used', []))}")
        print(f"   Legacy equivalent: Traditional routing")
    
    async def run_preset_tests(self):
        """Run predefined test cases."""
        test_cases = [
            "Create a professional logo for my coffee shop",
            "I need comprehensive market research for electric vehicle charging stations",
            "Build a complete brand identity with logo, website, and market analysis for my sustainable fashion startup",
            "Generate sales leads and create outreach campaigns for my B2B software company",
            "Design a website and create marketing content for my local bakery",
        ]
        
        print("\n🧪 RUNNING PRESET TEST CASES")
        print("=" * 60)
        
        for i, request in enumerate(test_cases, 1):
            print(f"\n📋 TEST CASE {i}/{len(test_cases)}")
            await self.test_semantic_jarvis(request)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
    
    async def interactive_mode(self):
        """Interactive testing mode."""
        print("\n🎮 INTERACTIVE MODE")
        print("=" * 40)
        print("Enter requests to test (type 'quit' to exit)")
        print("Commands:")
        print("  'presets' - Run preset test cases")
        print("  'compare <request>' - Compare semantic vs legacy")
        print("  'parse <request>' - Test parsing only")
        print("  'orchestrate <request>' - Test full orchestration")
        print("  '<request>' - Test with SemanticJarvis")
        
        while True:
            try:
                user_input = input("\n💬 Your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'presets':
                    await self.run_preset_tests()
                elif user_input.startswith('compare '):
                    request = user_input[8:]
                    await self.compare_with_legacy(request)
                elif user_input.startswith('parse '):
                    request = user_input[6:]
                    await self.test_request_understanding(request)
                elif user_input.startswith('orchestrate '):
                    request = user_input[12:]
                    await self.test_full_orchestration(request)
                elif user_input:
                    await self.test_semantic_jarvis(user_input)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Thanks for testing the semantic architecture!")


async def main():
    """Main test runner."""
    tester = InteractiveSemanticTest()
    
    if len(sys.argv) > 1:
        # Command line mode
        request = ' '.join(sys.argv[1:])
        
        if request == '--presets':
            await tester.run_preset_tests()
        elif request.startswith('--compare'):
            test_request = request[10:] if len(request) > 10 else "Create a logo for my startup"
            await tester.compare_with_legacy(test_request)
        else:
            await tester.test_semantic_jarvis(request)
    else:
        # Interactive mode
        await tester.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())