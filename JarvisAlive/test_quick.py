#!/usr/bin/env python3
"""
Quick test of core semantic functionality
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_request_parser import SemanticRequestParser
from orchestration.semantic_orchestrator import SemanticOrchestrator


class MockAIEngine:
    async def generate(self, prompt):
        if "logo" in prompt.lower():
            return '{"business_goal": "Create logo", "user_intent_summary": "Logo design needed", "primary_capabilities": ["logo_generation"], "secondary_capabilities": [], "recommended_agents": ["logo_generation_agent"], "execution_strategy": "single_agent", "execution_plan": {}, "extracted_parameters": {}, "business_context": {}, "user_preferences": {}, "confidence_score": 0.9, "reasoning": "Clear logo request"}'
        return '{"business_goal": "General request", "user_intent_summary": "General help", "primary_capabilities": ["content_creation"], "secondary_capabilities": [], "recommended_agents": ["general_agent"], "execution_strategy": "single_agent", "execution_plan": {}, "extracted_parameters": {}, "business_context": {}, "user_preferences": {}, "confidence_score": 0.7, "reasoning": "General request"}'


async def main():
    print("🚀 Quick Semantic Test")
    print("=" * 30)
    
    # Test semantic parser
    parser = SemanticRequestParser(MockAIEngine())
    understanding = await parser.parse_request("Create a logo for my startup")
    
    print(f"✅ Parser Test:")
    print(f"   Goal: {understanding.business_goal}")
    print(f"   Agents: {understanding.recommended_agents}")
    print(f"   Confidence: {understanding.confidence_score}")
    
    # Test orchestrator  
    orchestrator = SemanticOrchestrator(MockAIEngine())
    workflow = await orchestrator.process_request("Create a logo", "test")
    
    print(f"✅ Orchestrator Test:")
    print(f"   Status: {workflow.overall_status}")
    print(f"   Agents: {list(workflow.agent_states.keys())}")
    
    print("\n🎉 Core semantic functionality works!")


if __name__ == "__main__":
    asyncio.run(main())