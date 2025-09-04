#!/usr/bin/env python3
"""
Test suite for Context-Aware Response System

Tests the new intelligent response system that can distinguish between:
- Direct answers from context/knowledge vs agent execution
- Context-aware responses using previous work
- Proper routing of different message types
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode
from orchestration.response_analyzer import ResponseType


class ContextAwareTestSuite:
    """Test suite for context-aware response system."""
    
    def __init__(self):
        self.chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        self.test_session_id = "test_context_aware"
        self.results = []
    
    async def initialize(self):
        """Initialize the chat interface for testing."""
        print("🚀 Initializing Context-Aware Test Suite...")
        success = await self.chat.initialize()
        if not success:
            print("⚠️  Running in mock mode for testing")
        print("✅ Test suite ready\n")
        return success
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        print("="*80)
        print("🧪 CONTEXT-AWARE RESPONSE SYSTEM - TEST SUITE")
        print("="*80)
        
        test_methods = [
            self.test_basic_workflow,
            self.test_context_questions,
            self.test_general_knowledge_questions,
            self.test_creation_requests,
            self.test_hybrid_responses,
            self.test_edge_cases
        ]
        
        for test_method in test_methods:
            await test_method()
            print()  # Add spacing between tests
        
        self.print_summary()
    
    async def test_basic_workflow(self):
        """Test basic workflow to establish context."""
        print("📋 Test 1: Basic Workflow - Establishing Context")
        print("-" * 50)
        
        # Create a website to establish context
        creation_message = "Create a website for my shawarma restaurant called Desert Spice"
        print(f"💬 User: {creation_message}")
        
        response = await self.chat.chat(creation_message, self.test_session_id)
        print(f"🤖 Assistant: {response[:150]}...")
        
        # Verify this triggered agent execution
        if "organizing" in response.lower() or "workflow" in response.lower() or "routing" in response.lower():
            self.log_result("✅ PASS", "Basic workflow", "Agent execution triggered correctly")
        else:
            self.log_result("❌ FAIL", "Basic workflow", "Should have triggered agent execution")
        
        # 🚀 NEW: Test with REAL website files - simulate workflow completion with actual file paths
        session = self.chat.get_or_create_session(self.test_session_id)
        
        # Use actual website output that exists
        actual_website_paths = [
            "website_outputs/website_website_20250903_214904_site/index.html",
            "website_outputs/website_website_20250903_214904_site/home.html"
        ]
        
        # Store workflow result with actual file paths
        if self.chat.workflow_store:
            await self.chat.workflow_store.store_workflow_result(
                workflow_id="test_website_001",
                session_id=self.test_session_id,
                agent_type="website_generator_agent",
                results={
                    "business_name": "Desert Spice",
                    "business_idea": "Shawarma restaurant",
                    "style_guide": {
                        "colors": ["#C87941", "#1B365C", "#F4E9D7"],
                        "color_scheme": "warm Middle Eastern palette"
                    },
                    "saved_paths": actual_website_paths,
                    "website_generated_at": datetime.now().isoformat()
                },
                business_goal="Create a website for Desert Spice shawarma restaurant"
            )
        
        # Also add to session for compatibility
        session.add_workflow_result(
            workflow_id="test_website_001",
            agent_type="website_generator_agent",
            results={
                "business_name": "Desert Spice",
                "business_idea": "Shawarma restaurant",
                "saved_paths": actual_website_paths,
                "website_generated_at": datetime.now().isoformat()
            }
        )
        print("✅ Simulated workflow completion with REAL website files for analysis")
        
        # 🚀 NEW: Also test with REAL market research file
        market_research_file = "market_research_reports/market_research_website_for_a_shawarma_restaurant_20250903_193816.json"
        if self.chat.workflow_store:
            await self.chat.workflow_store.store_workflow_result(
                workflow_id="test_market_research_001",
                session_id=self.test_session_id,
                agent_type="market_research_agent",
                results={
                    "industry": "restaurant",
                    "saved_file": market_research_file,
                    "business_idea": "Shawarma restaurant in NYC"
                },
                business_goal="Market research for shawarma restaurant"
            )
        print("✅ Added REAL market research file for analysis")
    
    async def test_context_questions(self):
        """Test questions that should be answered from context."""
        print("📋 Test 2: Context-Aware Questions")
        print("-" * 50)
        
        context_questions = [
            {
                "message": "What colors did you use in the website?",
                "expected_type": "direct_answer",
                "should_contain": ["color", "Desert Spice", "#"]  # Should find actual hex colors from CSS
            },
            {
                "message": "What pages did you create for my restaurant?",
                "expected_type": "direct_answer", 
                "should_contain": ["page", "Desert Spice", "Professional Services"]  # Should find actual page titles
            },
            {
                "message": "Tell me about the website you built",
                "expected_type": "direct_answer",
                "should_contain": ["Desert Spice", "website", "Professional"]  # Should reference actual content
            },
            {
                "message": "Who are the main competitors for my shawarma restaurant?",
                "expected_type": "direct_answer",
                "should_contain": ["Mamoun", "Halal Guys", "competitor"]  # Should find actual competitors from JSON
            },
            {
                "message": "What's the market size for shawarma restaurants?",
                "expected_type": "direct_answer",
                "should_contain": ["billion", "market", "$"]  # Should find actual market size from research
            }
        ]
        
        for i, test_case in enumerate(context_questions, 1):
            print(f"\n🧪 Context Test {i}: {test_case['message']}")
            
            response = await self.chat.chat(test_case["message"], self.test_session_id)
            print(f"🤖 Response: {response[:200]}...")
            
            # Check if it provided a direct answer (not agent execution)
            if any(keyword in response.lower() for keyword in ["organizing", "workflow", "routing"]):
                self.log_result("❌ FAIL", f"Context Q{i}", "Should answer directly, not execute agents")
            elif any(keyword.lower() in response.lower() for keyword in test_case["should_contain"]):
                self.log_result("✅ PASS", f"Context Q{i}", "Provided contextual answer with relevant details")
            else:
                self.log_result("⚠️  PARTIAL", f"Context Q{i}", "Answered directly but missing expected details")
    
    async def test_general_knowledge_questions(self):
        """Test questions that should be answered from general knowledge."""
        print("📋 Test 3: General Knowledge Questions")
        print("-" * 50)
        
        knowledge_questions = [
            {
                "message": "What are good color schemes for restaurants?",
                "expected_type": "direct_answer",
                "should_contain": ["color", "restaurant", "warm"]
            },
            {
                "message": "How does branding help small businesses?",
                "expected_type": "direct_answer",
                "should_contain": ["brand", "business", "customers"]
            },
            {
                "message": "What makes a good website design?",
                "expected_type": "direct_answer",
                "should_contain": ["design", "website", "user"]
            }
        ]
        
        for i, test_case in enumerate(knowledge_questions, 1):
            print(f"\n🧪 Knowledge Test {i}: {test_case['message']}")
            
            response = await self.chat.chat(test_case["message"], self.test_session_id)
            print(f"🤖 Response: {response[:200]}...")
            
            # Should provide knowledge-based answer, not execute agents
            if any(keyword in response.lower() for keyword in ["organizing", "workflow", "routing"]):
                self.log_result("❌ FAIL", f"Knowledge Q{i}", "Should answer from knowledge, not execute agents")
            elif len(response) > 50 and any(keyword.lower() in response.lower() for keyword in test_case["should_contain"]):
                self.log_result("✅ PASS", f"Knowledge Q{i}", "Provided informative knowledge-based answer")
            else:
                self.log_result("⚠️  PARTIAL", f"Knowledge Q{i}", "Response too short or missing key concepts")
    
    async def test_creation_requests(self):
        """Test requests that should trigger agent execution."""
        print("📋 Test 4: Creation Requests (Agent Execution)")
        print("-" * 50)
        
        creation_requests = [
            {
                "message": "Create a logo for Desert Spice",
                "should_execute": True,
                "type": "logo creation"
            },
            {
                "message": "Design a new menu layout",
                "should_execute": True,
                "type": "design request"
            },
            {
                "message": "Generate a marketing campaign",
                "should_execute": True,
                "type": "marketing creation"
            }
        ]
        
        for i, test_case in enumerate(creation_requests, 1):
            print(f"\n🧪 Creation Test {i}: {test_case['message']}")
            
            response = await self.chat.chat(test_case["message"], self.test_session_id)
            print(f"🤖 Response: {response[:200]}...")
            
            # Should trigger agent execution
            if any(keyword in response.lower() for keyword in ["organizing", "workflow", "routing", "specialist"]):
                self.log_result("✅ PASS", f"Creation {i}", f"Correctly triggered agent execution for {test_case['type']}")
            else:
                self.log_result("❌ FAIL", f"Creation {i}", f"Should have triggered agents for {test_case['type']}")
    
    async def test_hybrid_responses(self):
        """Test responses that could be both informational and actionable."""
        print("📋 Test 5: Hybrid Response Scenarios")
        print("-" * 50)
        
        hybrid_questions = [
            {
                "message": "What kind of marketing works for restaurants?",
                "should_answer": True,
                "might_suggest": True
            },
            {
                "message": "How can I improve my restaurant's online presence?",
                "should_answer": True,
                "might_suggest": True
            }
        ]
        
        for i, test_case in enumerate(hybrid_questions, 1):
            print(f"\n🧪 Hybrid Test {i}: {test_case['message']}")
            
            response = await self.chat.chat(test_case["message"], self.test_session_id)
            print(f"🤖 Response: {response[:300]}...")
            
            # Should provide information (not just execute agents)
            if any(keyword in response.lower() for keyword in ["organizing", "workflow", "routing"]) and len(response) < 100:
                self.log_result("⚠️  PARTIAL", f"Hybrid {i}", "Executed agents but should provide information first")
            elif len(response) > 100:
                self.log_result("✅ PASS", f"Hybrid {i}", "Provided informative response (hybrid approach)")
            else:
                self.log_result("❌ FAIL", f"Hybrid {i}", "Response too short for informational query")
    
    async def test_edge_cases(self):
        """Test edge cases and error scenarios."""
        print("📋 Test 6: Edge Cases and Error Handling")
        print("-" * 50)
        
        edge_cases = [
            {
                "message": "What?",
                "description": "Very vague question",
                "should_clarify": True
            },
            {
                "message": "Colors website logo branding help",
                "description": "Fragmented keywords",
                "should_handle": True
            },
            {
                "message": "What did you do yesterday for my business?",
                "description": "Reference to non-existent work",
                "should_handle": True
            }
        ]
        
        for i, test_case in enumerate(edge_cases, 1):
            print(f"\n🧪 Edge Case {i}: {test_case['message']} ({test_case['description']})")
            
            response = await self.chat.chat(test_case["message"], self.test_session_id)
            print(f"🤖 Response: {response[:200]}...")
            
            # Should handle gracefully without errors
            if "error" in response.lower() or "issue" in response.lower():
                self.log_result("⚠️  PARTIAL", f"Edge {i}", "Handled but showed error message")
            elif len(response) > 20:  # Some reasonable response
                self.log_result("✅ PASS", f"Edge {i}", "Handled edge case gracefully")
            else:
                self.log_result("❌ FAIL", f"Edge {i}", "Failed to handle edge case properly")
    
    def log_result(self, status: str, test_name: str, description: str):
        """Log test result."""
        result = {
            "status": status,
            "test": test_name,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"  {status}: {description}")
    
    def print_summary(self):
        """Print test summary."""
        print("="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        passed = len([r for r in self.results if r["status"] == "✅ PASS"])
        partial = len([r for r in self.results if r["status"] == "⚠️  PARTIAL"])
        failed = len([r for r in self.results if r["status"] == "❌ FAIL"])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️  Partial: {partial}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "❌ FAIL":
                    print(f"  • {result['test']}: {result['description']}")
        
        if partial > 0:
            print(f"\n⚠️  Partial Tests:")
            for result in self.results:
                if result["status"] == "⚠️  PARTIAL":
                    print(f"  • {result['test']}: {result['description']}")
        
        print("\n" + "="*80)
        
        # Overall assessment
        success_rate = (passed / total) * 100
        if success_rate >= 80:
            print("🎉 CONTEXT-AWARE SYSTEM: WORKING WELL!")
        elif success_rate >= 60:
            print("⚠️  CONTEXT-AWARE SYSTEM: NEEDS SOME IMPROVEMENTS")
        else:
            print("❌ CONTEXT-AWARE SYSTEM: SIGNIFICANT ISSUES DETECTED")
        
        print("="*80)


async def main():
    """Main function to run the test suite."""
    print("🚀 Starting Context-Aware Response System Tests")
    
    # Initialize test suite
    test_suite = ContextAwareTestSuite()
    await test_suite.initialize()
    
    # Run all tests
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
