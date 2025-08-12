#!/usr/bin/env python3
"""Test the UserResponseParser for logo prompt approval."""

import asyncio
import os
import sys
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.user_response_parser import UserResponseParser, ApprovalIntent

console = Console()

def test_response_parser():
    """Test various user responses and their interpretations."""
    parser = UserResponseParser()
    
    console.print("🧠 Testing User Response Parser")
    console.print("=" * 50)
    
    # Test cases covering different response types
    test_cases = [
        # Approval responses
        ("yes", ApprovalIntent.APPROVE),
        ("looks good", ApprovalIntent.APPROVE),
        ("use it", ApprovalIntent.APPROVE),
        ("perfect!", ApprovalIntent.APPROVE),
        ("ok", ApprovalIntent.APPROVE),
        ("y", ApprovalIntent.APPROVE),
        
        # Rejection responses  
        ("no", ApprovalIntent.REJECT),
        ("nope", ApprovalIntent.REJECT),
        ("don't like it", ApprovalIntent.REJECT),
        ("skip", ApprovalIntent.REJECT),
        ("n", ApprovalIntent.REJECT),
        
        # Regenerate responses
        ("try again", ApprovalIntent.REGENERATE),
        ("redo", ApprovalIntent.REGENERATE),
        ("generate new", ApprovalIntent.REGENERATE),
        ("something else", ApprovalIntent.REGENERATE),
        ("different", ApprovalIntent.REGENERATE),
        
        # Unclear responses
        ("maybe", ApprovalIntent.UNCLEAR),
        ("hmm", ApprovalIntent.UNCLEAR),
        ("", ApprovalIntent.UNCLEAR),
        ("what?", ApprovalIntent.UNCLEAR),
    ]
    
    console.print("📝 Testing response interpretations:")
    console.print()
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for user_input, expected_intent in test_cases:
        decision = parser.parse_approval_response(user_input)
        
        # Check if prediction matches expectation
        is_correct = decision.intent == expected_intent
        correct_predictions += is_correct
        
        # Format output with status indicator
        status = "✅" if is_correct else "❌"
        confidence_bar = "🟩" * int(decision.confidence * 10) + "⬜" * (10 - int(decision.confidence * 10))
        
        console.print(f"{status} '{user_input}' → {decision.intent.value} ({decision.confidence:.2f}) {confidence_bar}")
        
        if not is_correct:
            console.print(f"   Expected: {expected_intent.value}, Got: {decision.intent.value}")
    
    accuracy = (correct_predictions / total_tests) * 100
    console.print()
    console.print(f"📊 Test Results: {correct_predictions}/{total_tests} correct ({accuracy:.1f}% accuracy)")
    
    # Test high confidence detection
    console.print("\n🎯 Testing confidence thresholds:")
    high_confidence_inputs = ["yes", "no", "try again", "looks great"]
    for inp in high_confidence_inputs:
        decision = parser.parse_approval_response(inp)
        is_high_conf = parser.is_high_confidence(decision)
        console.print(f"  '{inp}' → High confidence: {is_high_conf} ({decision.confidence:.2f})")
    
    # Test clarification suggestions
    console.print("\n💡 Testing clarification suggestions:")
    unclear_inputs = ["maybe", "hmm", ""]
    for inp in unclear_inputs:
        decision = parser.parse_approval_response(inp)
        suggestion = parser.suggest_clarification(decision)
        if suggestion:
            console.print(f"  '{inp}' → {suggestion}")
    
    console.print(f"\n🎉 User Response Parser test completed!")
    return accuracy > 85  # Consider test passed if >85% accuracy

if __name__ == "__main__":
    test_response_parser()