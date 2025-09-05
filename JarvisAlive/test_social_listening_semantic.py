"""Test Social Listening Agent through semantic interface."""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode


async def test_social_listening_semantic():
    """Test social listening through semantic chat interface."""
    
    print("🧪 Testing Social Listening Agent - Semantic Routing")
    print("=" * 60)
    
    # Initialize semantic chat
    try:
        chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
        await chat.initialize()
        print("✅ Semantic chat interface initialized")
    except Exception as e:
        print(f"❌ Failed to initialize semantic chat: {e}")
        return
    
    # Test cases for social listening
    test_requests = [
        "Monitor brand mentions on social media",
        "Track competitor discussions online",
        "Find people complaining about CRM software", 
        "Watch for mentions of our company",
        "Analyze social sentiment about marketing automation",
        "Alert me when people discuss our competitors"
    ]
    
    results = []
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🧪 Test {i}: '{request}'")
        print("-" * 40)
        
        try:
            response = await chat.chat(request, f"social_test_session_{i}")
            
            # Check if social listening was triggered
            response_lower = response.lower()
            
            if any(keyword in response_lower for keyword in [
                "social listening", "monitoring", "mentions", "brand monitoring",
                "sentiment", "alerts", "social media", "reddit", "hackernews"
            ]):
                print("✅ PASS: Social Listening Agent likely executed")
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
            
            print(f"📋 Response: {response[:150]}...")
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
    
    print("\n🎯 Social Listening Agent semantic integration test complete")
    return results


async def test_social_monitoring_triggers():
    """Test specific phrases that should trigger social monitoring."""
    
    print("\n🧪 Testing Social Monitoring Trigger Phrases")
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
        "monitor social media",
        "track brand mentions",
        "social listening",
        "watch competitors",
        "sentiment analysis",
        "social monitoring",
        "brand monitoring",
        "competitor tracking"
    ]
    
    for phrase in trigger_phrases:
        test_request = f"{phrase} for our company"
        print(f"\n🎯 Testing: '{test_request}'")
        
        try:
            response = await chat.chat(test_request, f"trigger_test_{phrase.replace(' ', '_')}")
            
            if any(keyword in response.lower() for keyword in ["social", "monitoring", "mentions", "sentiment"]):
                print("✅ Triggered social monitoring")
            else:
                print("❌ Did not trigger social monitoring")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_social_listening_semantic())
    asyncio.run(test_social_monitoring_triggers())
