#!/usr/bin/env python3
"""
Debug Semantic Processor Issues
Quick diagnostic to identify erroneous functionalities.
"""

import asyncio
import sys
import os
import traceback

sys.path.insert(0, os.getcwd())

async def diagnose_semantic_issues():
    """Run comprehensive diagnostic of semantic processor."""
    
    print("🔍 SEMANTIC PROCESSOR DIAGNOSTIC")
    print("=" * 60)
    
    issues_found = []
    
    # Test 1: Core imports
    print("\n1️⃣ Testing Core Imports...")
    try:
        from orchestration.semantic_request_parser import SemanticRequestParser
        print("✅ SemanticRequestParser imported")
        
        from orchestration.semantic_orchestrator import SemanticOrchestrator
        print("✅ SemanticOrchestrator imported")
        
        from orchestration.semantic_integration import SemanticJarvis
        print("✅ SemanticJarvis imported")
        
    except ImportError as e:
        issues_found.append(f"Core import failure: {e}")
        print(f"❌ Core import failed: {e}")
    
    # Test 2: Enhanced components
    print("\n2️⃣ Testing Enhanced Components...")
    try:
        from orchestration.response_analyzer import ContextAwareResponseAnalyzer
        print("✅ Response analyzer imported")
    except ImportError as e:
        issues_found.append(f"Response analyzer missing: {e}")
        print(f"⚠️ Response analyzer not available: {e}")
    
    try:
        from orchestration.workflow_result_store import WorkflowResultStore
        print("✅ Workflow store imported")
    except ImportError as e:
        issues_found.append(f"Workflow store missing: {e}")
        print(f"⚠️ Workflow store not available: {e}")
    
    # Test 3: Chat interface
    print("\n3️⃣ Testing Chat Interface...")
    try:
        from semantic_chat_interface import SemanticChatInterface, OrchestrationMode
        print("✅ Chat interface imported")
        
        # Test initialization
        chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        print("✅ Chat interface created")
        
        await chat.initialize()
        print("✅ Chat interface initialized")
        
    except Exception as e:
        issues_found.append(f"Chat interface failure: {e}")
        print(f"❌ Chat interface failed: {e}")
        traceback.print_exc()
    
    # Test 4: Real agent integration
    print("\n4️⃣ Testing Real Agent Integration...")
    try:
        from departments.branding.branding_agent import BrandingAgent
        from departments.website.website_generator_agent import WebsiteGeneratorAgent
        from departments.market_research.market_research_agent import MarketResearchAgent
        print("✅ Real agents imported")
        
        # Test instantiation
        branding_agent = BrandingAgent()
        website_agent = WebsiteGeneratorAgent()
        research_agent = MarketResearchAgent()
        print("✅ Real agents instantiated")
        
    except Exception as e:
        issues_found.append(f"Real agent integration failure: {e}")
        print(f"❌ Real agent integration failed: {e}")
    
    # Test 5: End-to-end functionality
    print("\n5️⃣ Testing End-to-End Functionality...")
    try:
        if 'chat' in locals():
            # Test simple request
            response = await chat.chat("Hello", "diagnostic_test")
            print("✅ Basic chat working")
            
            # Test business request
            response = await chat.chat("I need help with my business", "diagnostic_test")
            print("✅ Business request processing")
            
    except Exception as e:
        issues_found.append(f"End-to-end failure: {e}")
        print(f"❌ End-to-end test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if not issues_found:
        print("🎉 ALL TESTS PASSED - Semantic processor is working correctly!")
    else:
        print(f"❌ {len(issues_found)} ISSUES FOUND:")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
    
    return issues_found

if __name__ == "__main__":
    asyncio.run(diagnose_semantic_issues())
