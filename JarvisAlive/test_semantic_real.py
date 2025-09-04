#!/usr/bin/env python3
"""
Test semantic architecture with REAL AI engine

This uses your actual Anthropic API to test the semantic understanding.
Make sure you have ANTHROPIC_API_KEY in your environment.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_request_parser import SemanticRequestParser
from orchestration.semantic_integration import SemanticJarvis
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig


async def test_with_real_ai():
    """Test semantic architecture with real AI engine."""
    print("🚀 Testing Semantic Architecture with REAL AI")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("   Set your API key: export ANTHROPIC_API_KEY='your_key_here'")
        return False
    
    try:
        # Initialize real AI engine
        ai_engine = AnthropicEngine(AIEngineConfig())
        parser = SemanticRequestParser(ai_engine)
        jarvis = SemanticJarvis(ai_engine)
        
        print("✅ AI engine initialized successfully")
        
        # Test cases that were problematic before
        test_cases = [
            {
                "name": "Logo Generation (Previously Problematic)",
                "request": "Create a professional logo for my organic coffee roastery called Bean & Brew"
            },
            {
                "name": "Market Research (Previously Problematic)", 
                "request": "I need comprehensive market research for electric vehicle charging infrastructure in suburban areas"
            },
            {
                "name": "Multi-Agent Workflow",
                "request": "Create a complete brand package for my sustainable fashion startup: logo, brand strategy, market analysis, and website"
            },
            {
                "name": "Complex Business Request",
                "request": "Help me launch my B2B SaaS platform: conduct competitor analysis, create brand identity, build a landing page, and develop lead generation campaigns"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 TESTING: {test_case['name']}")
            print("-" * 60)
            print(f"Request: {test_case['request']}")
            
            try:
                # Test semantic understanding
                start_time = datetime.now()
                understanding = await parser.parse_request(test_case['request'])
                parse_duration = (datetime.now() - start_time).total_seconds()
                
                print(f"\n📊 SEMANTIC UNDERSTANDING (took {parse_duration:.2f}s):")
                print(f"  🎯 Business Goal: {understanding.business_goal}")
                print(f"  🏢 Domain: {understanding.business_domain}")
                print(f"  ⚡ Strategy: {understanding.execution_strategy.value}")
                print(f"  🤖 Agents: {understanding.recommended_agents}")
                print(f"  ⚙️  Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
                print(f"  📊 Confidence: {understanding.confidence_score:.2f}")
                print(f"  💭 Reasoning: {understanding.reasoning[:100]}...")
                
                # Test full Jarvis processing
                jarvis_start = datetime.now()
                response = await jarvis.process_request(test_case['request'], f"test_{len(results)}")
                jarvis_duration = (datetime.now() - jarvis_start).total_seconds()
                
                print(f"\n🧠 JARVIS PROCESSING (took {jarvis_duration:.2f}s):")
                print(f"  ✅ Success: {response['success']}")
                print(f"  📋 Workflow ID: {response.get('workflow_id', 'N/A')}")
                print(f"  📊 Progress: {response.get('progress', 0):.1%}")
                print(f"  🔧 Method: {response.get('method', 'N/A')}")
                
                if response.get('agent_details'):
                    print(f"  🤖 Agent Details:")
                    for agent_id, details in response['agent_details'].items():
                        print(f"     • {agent_id}: {details['status']} ({details.get('capability', 'N/A')})")
                
                results.append({
                    'test_name': test_case['name'],
                    'success': response['success'],
                    'parse_duration': parse_duration,
                    'total_duration': jarvis_duration,
                    'confidence': understanding.confidence_score,
                    'agents_count': len(understanding.recommended_agents),
                    'strategy': understanding.execution_strategy.value
                })
                
                print("✅ Test completed successfully")
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                results.append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 REAL AI TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in results if r.get('success', False)]
        success_rate = len(successful_tests) / len(results) if results else 0
        
        print(f"✅ Success Rate: {success_rate:.1%} ({len(successful_tests)}/{len(results)})")
        
        if successful_tests:
            avg_parse = sum(r['parse_duration'] for r in successful_tests) / len(successful_tests)
            avg_total = sum(r['total_duration'] for r in successful_tests) / len(successful_tests)
            avg_confidence = sum(r['confidence'] for r in successful_tests) / len(successful_tests)
            
            print(f"⏱️  Average Parse Time: {avg_parse:.2f}s")
            print(f"⏱️  Average Total Time: {avg_total:.2f}s")
            print(f"📊 Average Confidence: {avg_confidence:.2f}")
        
        print("\n📋 Individual Results:")
        for result in results:
            status = "✅" if result.get('success') else "❌"
            name = result['test_name'][:40] + "..." if len(result['test_name']) > 40 else result['test_name']
            if result.get('success'):
                print(f"  {status} {name:<45} {result['total_duration']:.2f}s")
            else:
                print(f"  {status} {name:<45} ERROR: {result.get('error', 'Unknown')}")
        
        if success_rate > 0.75:
            print("\n🎉 Semantic architecture working well with real AI!")
        else:
            print("\n⚠️  Some issues detected. Check errors above.")
        
        return success_rate > 0.5
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_with_real_ai())
    exit(0 if success else 1)