#!/usr/bin/env python3
"""
Test the real AI chat interface (not mock) for interactive testing.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode


async def main():
    """Run real AI chat interface for interactive testing."""
    print("🚀 Starting REAL AI Semantic Chat Interface")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("❌ No valid Anthropic API key found in .env file")
        print("Please add your API key to .env: ANTHROPIC_API_KEY=your_key_here")
        return
    
    print(f"✅ Found API key: {api_key[:15]}...")
    
    # Initialize the chat interface with real AI
    chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_ONLY)
    
    print("\n🤖 Initializing real AI interface...")
    success = await chat.initialize()
    
    if not success:
        print("❌ Failed to initialize real AI interface")
        return
    
    print("✅ Real AI interface initialized successfully!")
    print("\n" + "=" * 60)
    print("🎯 REAL AI SEMANTIC CHAT INTERFACE - INTERACTIVE MODE")
    print("=" * 60)
    print("Chat with your AI business assistant using REAL AI!")
    print("Type 'quit', 'exit', or 'bye' to end the session.")
    print("Type 'help' to see what I can do.")
    print("-" * 60)
    
    # Start interactive chat
    await chat.interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())