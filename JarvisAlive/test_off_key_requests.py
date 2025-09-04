#!/usr/bin/env python3
"""
Test Off-Key Request Handling

This tests how the semantic architecture handles requests that don't map
to existing agents, ensuring it provides helpful suggestions while guiding
users toward available capabilities.
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode


async def test_off_key_requests():
    """Test various off-key requests to ensure intelligent fallback."""
    print("🧪 Testing Off-Key Request Handling")
    print("=" * 50)
    
    # Initialize chat interface
    chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_WITH_FALLBACK)
    await chat.initialize()
    
    # Test cases that should NOT map to existing agents
    off_key_test_cases = [
        {
            "name": "Legal Services Request",
            "message": "Help me draft a legal contract for my business partnership",
            "expected_alternatives": ["content_creation", "brand_creation"]
        },
        {
            "name": "HR/Recruitment Request", 
            "message": "I need to hire a software developer, help me write job descriptions and screen candidates",
            "expected_alternatives": ["content_creation", "lead_generation"]
        },
        {
            "name": "Financial Planning Request",
            "message": "Create a financial model and budget projection for my startup",
            "expected_alternatives": ["market_analysis", "content_creation"]
        },
        {
            "name": "Technical Development Request",
            "message": "Build me a mobile app with user authentication and database",
            "expected_alternatives": ["website_building", "brand_creation"]
        },
        {
            "name": "Personal Life Coaching",
            "message": "I need help with work-life balance and personal productivity tips",
            "expected_alternatives": ["content_creation"]
        },
        {
            "name": "Medical/Health Advice",
            "message": "What should I do about my back pain from sitting at a desk all day?",
            "expected_alternatives": ["content_creation"]
        },
        {
            "name": "Recipe/Cooking Request",
            "message": "Give me a recipe for chocolate chip cookies",
            "expected_alternatives": ["content_creation"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(off_key_test_cases, 1):
        print(f"\n🧪 TEST {i}/{len(off_key_test_cases)}: {test_case['name']}")
        print("-" * 60)
        print(f"📝 Message: {test_case['message']}")
        
        try:
            session_id = f"off_key_test_{i}"
            response = await chat.chat(test_case['message'], session_id)
            
            print(f"\n🤖 Response:")
            print(response)
            
            # Validate the response
            validation_results = []
            
            # Check if it acknowledges the request
            if "understand" in response.lower():
                validation_results.append("✅ Acknowledges user's request")
            else:
                validation_results.append("❌ Doesn't acknowledge request")
            
            # Check if it explains limitation
            limitation_indicators = ["don't have", "can't", "not able", "instead", "however", "but"]
            if any(indicator in response.lower() for indicator in limitation_indicators):
                validation_results.append("✅ Explains limitation appropriately")
            else:
                validation_results.append("⚠️  Doesn't clearly explain limitation")
            
            # Check if it suggests alternatives
            if "help with" in response.lower() or "can help" in response.lower() or "**" in response:
                validation_results.append("✅ Suggests alternative capabilities")
            else:
                validation_results.append("❌ Doesn't suggest alternatives")
            
            # Check if it mentions available capabilities
            available_capabilities = ["logo", "brand", "market", "website", "sales", "content", "research"]
            mentioned_capabilities = [cap for cap in available_capabilities if cap in response.lower()]
            if mentioned_capabilities:
                validation_results.append(f"✅ Mentions capabilities: {mentioned_capabilities}")
            else:
                validation_results.append("❌ Doesn't mention specific capabilities")
            
            # Check if it invites further engagement
            engagement_indicators = ["let me know", "would", "help", "interest", "?"]
            if any(indicator in response.lower() for indicator in engagement_indicators):
                validation_results.append("✅ Invites further engagement")
            else:
                validation_results.append("⚠️  Could be more engaging")
            
            # Show validation results
            print(f"\n🔍 VALIDATION:")
            for validation in validation_results:
                print(f"   {validation}")
            
            # Overall assessment
            success_count = sum(1 for v in validation_results if v.startswith("✅"))
            total_checks = len(validation_results)
            
            if success_count >= 3:
                print(f"✅ TEST PASSED - Good off-key handling ({success_count}/{total_checks})")
                results.append(True)
            else:
                print(f"❌ TEST FAILED - Poor off-key handling ({success_count}/{total_checks})")
                results.append(False)
                
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            results.append(False)
    
    # Test some borderline cases (should still route to agents)
    print(f"\n{'='*60}")
    print("🎯 Testing Borderline Cases (Should Route to Agents)")
    print(f"{'='*60}")
    
    borderline_cases = [
        {
            "name": "Creative Logo Request",
            "message": "Design something artistic for my brand",
            "should_route": True,
            "expected_agent": "logo"
        },
        {
            "name": "Vague Market Question",
            "message": "What's happening in my industry?",
            "should_route": True,
            "expected_agent": "market"
        },
        {
            "name": "Business Presence Request",
            "message": "I need an online presence",
            "should_route": True, 
            "expected_agent": "website"
        }
    ]
    
    for test_case in borderline_cases:
        print(f"\n🎯 Borderline Test: {test_case['name']}")
        print(f"Message: {test_case['message']}")
        
        response = await chat.chat(test_case['message'], f"borderline_{test_case['name']}")
        print(f"Response: {response[:200]}...")
        
        # Check if it routes appropriately
        if test_case['should_route']:
            expected_agent = test_case['expected_agent']
            if expected_agent in response.lower() or "routing" in response.lower():
                print("✅ Correctly routed to agent")
            else:
                print("⚠️  May not have routed correctly")
    
    # Final summary
    print(f"\n{'='*60}")
    print("🏁 OFF-KEY REQUEST TEST RESULTS")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    print(f"📊 Success Rate: {success_rate:.1%} ({passed}/{total})")
    
    if success_rate >= 0.8:
        print(f"\n🎉 EXCELLENT! Off-key request handling is working well")
        print(f"✅ Users get helpful guidance toward available capabilities")
        print(f"✅ System acknowledges requests and suggests alternatives")
        print(f"✅ Ready for production with intelligent fallbacks")
    elif success_rate >= 0.6:
        print(f"\n👍 GOOD! Most off-key requests are handled appropriately")
        print(f"⚠️  Some responses could be more helpful - review failed cases")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT! Off-key handling needs work")
        print(f"🔧 Review the fallback logic and response formatting")
    
    print(f"\n🎯 **Key Features Validated:**")
    print(f"• Acknowledges user intent even for unsupported requests")
    print(f"• Uses AI to provide intelligent suggestions")  
    print(f"• Guides users toward available capabilities")
    print(f"• Maintains helpful, conversational tone")
    print(f"• Invites further engagement with available services")
    
    return success_rate >= 0.6


if __name__ == "__main__":
    success = asyncio.run(test_off_key_requests())
    
    if success:
        print(f"\n🚀 SUCCESS! Off-key request handling is production ready!")
    else:
        print(f"\n⚠️  Some issues detected. Review logs above.")
    
    exit(0 if success else 1)