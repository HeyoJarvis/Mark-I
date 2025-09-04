#!/usr/bin/env python3
"""
Demo of the chat interface showing both valid and off-key requests
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_chat_interface import SemanticChatInterface, OrchestrationMode


async def chat_demo():
    """Demo the chat interface with various request types."""
    print("🎭 SEMANTIC CHAT INTERFACE DEMO")
    print("=" * 50)
    
    # Initialize chat
    chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_WITH_FALLBACK)
    await chat.initialize()
    
    # Demo conversations
    demo_conversations = [
        {
            "name": "Greeting & Valid Business Request",
            "messages": [
                "Hi there!",
                "Create a professional logo for my artisan coffee roastery"
            ]
        },
        {
            "name": "Off-Key Request (Legal)",
            "messages": [
                "Help me write a legal contract for my business partnership"
            ]
        },
        {
            "name": "Off-Key Request (HR)",
            "messages": [
                "I need to hire a software developer, help me screen candidates"
            ]
        },
        {
            "name": "Valid Market Research",
            "messages": [
                "I need comprehensive market research for electric vehicle charging stations"
            ]
        },
        {
            "name": "Capabilities Question",
            "messages": [
                "What can you help me with?"
            ]
        }
    ]
    
    session_counter = 0
    
    for conversation in demo_conversations:
        session_counter += 1
        session_id = f"demo_session_{session_counter}"
        
        print(f"\n{'='*60}")
        print(f"🎬 {conversation['name']}")
        print(f"{'='*60}")
        
        for message in conversation['messages']:
            print(f"\n💬 User: {message}")
            
            # Get response
            response = await chat.chat(message, session_id, "Demo User")
            
            print(f"🤖 Assistant: {response}")
            
            # Small pause for readability
            await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print("🎉 DEMO COMPLETE")
    print(f"{'='*60}")
    print("✅ Natural conversation handling")
    print("✅ Valid requests route to agents")  
    print("✅ Off-key requests provide helpful suggestions")
    print("✅ Context maintained across conversation")
    print("\n🚀 Your chat interface is ready for users!")


if __name__ == "__main__":
    asyncio.run(chat_demo())