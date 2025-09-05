"""Test Lead Mining Agent through semantic interface."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode


async def test_lead_mining_semantic():
    """Test lead mining through semantic chat interface."""
    
    print("🧪 Testing Lead Mining Agent - Semantic Routing")
    print("=" * 60)
    
    # Initialize semantic chat
    try:
        chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        await chat.initialize()
        print("✅ Semantic chat interface initialized")
    except Exception as e:
        print(f"❌ Failed to initialize semantic chat: {e}")
        return
    
    # Test cases
    test_requests = [
        "Find 10 leads for SaaS companies in the US",
        "Get me prospects for B2B software companies with 100-500 employees",
        "Search for VP Sales contacts at tech startups in California", 
        "I need qualified leads for my marketing automation software",
        "Help me find decision makers at mid-size technology companies"
    ]
    
    results = []
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🧪 Test {i}: '{request}'")
        print("-" * 40)
        
        try:
            response = await chat.chat(request, f"test_session_{i}")
            
            # Analyze response to determine if lead mining was triggered
            response_lower = response.lower()
            
            if any(keyword in response_lower for keyword in [
                "lead mining", "prospects", "qualified leads", "apollo", 
                "leads found", "mining_success", "icp criteria"
            ]):
                print("✅ PASS: Lead Mining Agent likely executed")
                success = True
            elif "mock" in response_lower or "sandbox failed" in response_lower:
                print("❌ FAIL: Using mock execution")
                success = False
            elif "error" in response_lower or "failed" in response_lower:
                print("⚠️  ERROR: Execution failed")
                success = False
            else:
                print("⚠️  UNCLEAR: Check response manually")
                success = None
            
            print(f"📋 Response: {response[:200]}...")
            results.append({
                "request": request,
                "success": success,
                "response": response
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "request": request,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    
    passed = sum(1 for r in results if r.get("success") is True)
    failed = sum(1 for r in results if r.get("success") is False)
    unclear = sum(1 for r in results if r.get("success") is None)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Unclear: {unclear}")
    print(f"🎯 Success Rate: {(passed / len(results)) * 100:.1f}%")
    
    print("\n🎯 Lead Mining Agent semantic integration test complete")
    return results


async def test_specific_lead_mining_phrases():
    """Test specific phrases that should trigger lead mining."""
    
    print("\n🧪 Testing Specific Lead Mining Trigger Phrases")
    print("-" * 50)
    
    # Initialize semantic chat
    try:
        chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        await chat.initialize()
    except Exception as e:
        print(f"❌ Failed to initialize semantic chat: {e}")
        return
    
    # Specific trigger phrases
    trigger_phrases = [
        "mine leads",
        "find prospects", 
        "search for leads",
        "get qualified leads",
        "lead generation",
        "prospect search",
        "find contacts",
        "lead discovery"
    ]
    
    for phrase in trigger_phrases:
        test_request = f"{phrase} for technology companies"
        print(f"\n🎯 Testing: '{test_request}'")
        
        try:
            response = await chat.chat(test_request, f"trigger_test_{phrase.replace(' ', '_')}")
            
            if "lead mining" in response.lower() or "prospects" in response.lower():
                print("✅ Triggered lead mining")
            else:
                print("❌ Did not trigger lead mining")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_lead_mining_semantic())
    asyncio.run(test_specific_lead_mining_phrases())
