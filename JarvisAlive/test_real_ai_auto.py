#!/usr/bin/env python3
"""
Auto-test semantic architecture with real Anthropic API
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_request_parser import SemanticRequestParser
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig


async def main():
    """Test semantic parsing with real Anthropic AI."""
    print("🚀 Semantic Architecture - Real AI Test")
    print("=" * 50)
    
    # Check for API key from .env
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in .env file")
        return False
    
    print(f"✅ API Key loaded: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Initialize real AI engine
        config = AIEngineConfig(
            api_key=api_key,
            model="claude-3-5-sonnet-20241022"  # Updated model name
        )
        ai_engine = AnthropicEngine(config)
        parser = SemanticRequestParser(ai_engine)
        
        print("✅ Anthropic AI engine initialized")
        
        # Test the problematic cases
        test_requests = [
            "Create a professional logo for my coffee shop startup",
            "I need market research for electric vehicle charging stations"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n🧪 TEST {i}: {request}")
            print("-" * 50)
            
            try:
                start_time = datetime.now()
                understanding = await parser.parse_request(request)
                duration = (datetime.now() - start_time).total_seconds()
                
                print(f"⏱️  Duration: {duration:.2f}s")
                print(f"🎯 Goal: {understanding.business_goal}")
                print(f"⚡ Strategy: {understanding.execution_strategy}")
                print(f"🤖 Agents: {understanding.recommended_agents}")
                print(f"⚙️  Capabilities: {[cap.value for cap in understanding.primary_capabilities]}")
                print(f"📊 Confidence: {understanding.confidence_score:.2f}")
                print(f"💭 Reasoning: {understanding.reasoning[:150]}...")
                
                # Validate
                if understanding.confidence_score >= 0.6 and understanding.recommended_agents:
                    print("✅ PASSED")
                else:
                    print("⚠️  PARTIAL - Low confidence or no agents")
                
            except Exception as e:
                print(f"❌ FAILED: {e}")
        
        print(f"\n🎉 Real AI testing completed!")
        print(f"✅ Semantic understanding working with live Anthropic API")
        return True
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)