"""
User Response Parser - NLP layer for interpreting user approval responses

Handles yes/no/redo responses for interactive workflow steps like logo prompt approval.
Provides intent classification and confidence scoring for user decisions.
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ApprovalIntent(Enum):
    """User intent for approval decisions."""
    APPROVE = "approve"          # Yes, proceed with the prompt
    REJECT = "reject"            # No, don't use this prompt  
    REGENERATE = "regenerate"    # Redo/try again/generate new
    UNCLEAR = "unclear"          # Ambiguous response


@dataclass
class ApprovalDecision:
    """Parsed user approval decision."""
    intent: ApprovalIntent
    confidence: float  # 0.0 to 1.0
    original_input: str
    explanation: str = ""


class UserResponseParser:
    """
    NLP parser for user approval responses in interactive workflows.
    
    Handles various ways users might express:
    - Approval: "yes", "looks good", "use it", "proceed"
    - Rejection: "no", "don't like it", "skip"  
    - Regeneration: "try again", "redo", "generate new"
    """
    
    def __init__(self):
        """Initialize the response parser with pattern definitions."""
        self.logger = logging.getLogger(__name__)
        
        # Define response patterns with confidence weights
        self.approval_patterns = {
            # High confidence approval patterns
            r'\b(yes|yeah|yep|ok|okay|good|great|perfect|use it|proceed|go ahead)\b': 0.9,
            r'\b(looks? good|sounds? good|that works?|that\'s? fine)\b': 0.85,
            r'\b(approved?|accept|confirmed?)\b': 0.9,
            
            # Medium confidence approval patterns  
            r'\b(sure|fine|alright|right)\b': 0.7,
            r'^(y|👍|✅|✓)$': 0.8,
        }
        
        self.rejection_patterns = {
            # High confidence rejection patterns
            r'\b(no|nope|nah|don\'?t|skip|pass|reject)\b': 0.9,
            r'\b(don\'?t like|not good|bad|terrible|awful)\b': 0.85,
            r'\b(cancel|abort|stop)\b': 0.9,
            
            # Medium confidence rejection patterns
            r'^(n|👎|❌|✗)$': 0.8,
            r'\b(meh|not really)\b': 0.7,
        }
        
        self.regenerate_patterns = {
            # High confidence regenerate patterns
            r'\b(try again|redo|regenerate|generate new|make another)\b': 0.95,
            r'\b(different|another|new one|something else)\b': 0.8,
            r'\b(change|modify|adjust|improve)\b': 0.75,
            
            # Medium confidence regenerate patterns
            r'\b(again|more|other)\b': 0.6,
        }
        
        self.logger.info("UserResponseParser initialized with pattern matching")
    
    def parse_approval_response(self, user_input: str) -> ApprovalDecision:
        """
        Parse user input to determine approval intent.
        
        Args:
            user_input: Raw user response string
            
        Returns:
            ApprovalDecision with intent, confidence, and explanation
        """
        if not user_input or not user_input.strip():
            return ApprovalDecision(
                intent=ApprovalIntent.UNCLEAR,
                confidence=0.0,
                original_input=user_input,
                explanation="Empty or whitespace-only input"
            )
        
        # Normalize input for pattern matching
        normalized_input = user_input.lower().strip()
        self.logger.debug(f"Parsing user input: '{user_input}' -> '{normalized_input}'")
        
        # Check each pattern category and find best match
        approval_score = self._match_patterns(normalized_input, self.approval_patterns)
        rejection_score = self._match_patterns(normalized_input, self.rejection_patterns)
        regenerate_score = self._match_patterns(normalized_input, self.regenerate_patterns)
        
        self.logger.debug(f"Pattern scores - Approval: {approval_score}, Rejection: {rejection_score}, Regenerate: {regenerate_score}")
        
        # Determine intent based on highest scoring pattern
        max_score = max(approval_score, rejection_score, regenerate_score)
        
        if max_score < 0.5:
            return ApprovalDecision(
                intent=ApprovalIntent.UNCLEAR,
                confidence=max_score,
                original_input=user_input,
                explanation="No clear pattern match found"
            )
        
        if approval_score == max_score:
            intent = ApprovalIntent.APPROVE
            explanation = "Detected approval language"
        elif rejection_score == max_score:
            intent = ApprovalIntent.REJECT  
            explanation = "Detected rejection language"
        else:  # regenerate_score == max_score
            intent = ApprovalIntent.REGENERATE
            explanation = "Detected regeneration request"
        
        return ApprovalDecision(
            intent=intent,
            confidence=max_score,
            original_input=user_input,
            explanation=explanation
        )
    
    def _match_patterns(self, text: str, patterns: Dict[str, float]) -> float:
        """
        Match text against pattern dictionary and return best confidence score.
        
        Args:
            text: Normalized input text
            patterns: Dictionary of regex patterns to confidence scores
            
        Returns:
            Highest confidence score from matching patterns (0.0 if no match)
        """
        max_score = 0.0
        
        for pattern, confidence in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                max_score = max(max_score, confidence)
                self.logger.debug(f"Pattern match: '{pattern}' -> {confidence}")
        
        return max_score
    
    def is_high_confidence(self, decision: ApprovalDecision, threshold: float = 0.8) -> bool:
        """Check if decision has high confidence above threshold."""
        return decision.confidence >= threshold
    
    def suggest_clarification(self, decision: ApprovalDecision) -> str:
        """Provide clarification suggestions for unclear responses."""
        if decision.intent == ApprovalIntent.UNCLEAR:
            return "Please respond with 'yes' to proceed, 'no' to skip, or 'try again' to generate a new version."
        elif decision.confidence < 0.7:
            return f"I think you mean '{decision.intent.value}' - is that correct? (yes/no)"
        return ""


# Convenience functions for quick usage
def parse_user_approval(user_input: str) -> ApprovalDecision:
    """Quick function to parse user approval without instantiating parser."""
    parser = UserResponseParser()
    return parser.parse_approval_response(user_input)


def is_approval(user_input: str) -> bool:
    """Quick check if user input indicates approval."""
    decision = parse_user_approval(user_input)
    return decision.intent == ApprovalIntent.APPROVE and decision.confidence > 0.7


def is_rejection(user_input: str) -> bool:
    """Quick check if user input indicates rejection."""
    decision = parse_user_approval(user_input)
    return decision.intent == ApprovalIntent.REJECT and decision.confidence > 0.7


def is_regenerate_request(user_input: str) -> bool:
    """Quick check if user input requests regeneration."""
    decision = parse_user_approval(user_input)
    return decision.intent == ApprovalIntent.REGENERATE and decision.confidence > 0.7