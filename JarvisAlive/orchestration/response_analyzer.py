"""
Context-Aware Response Analyzer

This module determines the appropriate response strategy for user messages:
- Direct answers from context/knowledge vs agent execution
- Intelligent routing based on conversation history and available context
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine

logger = logging.getLogger(__name__)


class ResponseType(str, Enum):
    """Types of responses the system can provide."""
    DIRECT_ANSWER = "direct_answer"      # Answer from context/knowledge
    AGENT_EXECUTION = "agent_execution"   # Execute agents for creation
    CLARIFICATION = "clarification"       # Need more information
    HYBRID = "hybrid"                     # Answer + suggest actions


@dataclass
class ResponseDecision:
    """Decision about how to respond to a user message."""
    response_type: ResponseType
    confidence: float
    reasoning: str
    context_sources: List[str]  # What context to use for answer
    suggested_agents: List[str]  # If agent execution needed
    answer_strategy: str        # How to formulate the answer
    requires_context_extraction: bool = False
    context_query: Optional[str] = None


class ContextAwareResponseAnalyzer:
    """Analyzes messages to determine appropriate response strategy."""
    
    def __init__(self, ai_engine: AnthropicEngine):
        self.ai_engine = ai_engine
        logger.info("Context-Aware Response Analyzer initialized")
    
    async def analyze_response_needed(
        self, 
        message: str, 
        conversation_context: Dict[str, Any]
    ) -> ResponseDecision:
        """Determine what type of response is appropriate for this message."""
        
        try:
            # Build analysis prompt
            analysis_prompt = self._build_response_analysis_prompt(message, conversation_context)
            
            # Get AI decision
            response = await self.ai_engine.generate(analysis_prompt)
            
            # Parse and return decision
            return self._parse_response_decision(response.content, message)
            
        except Exception as e:
            logger.error(f"Error analyzing response needed: {e}")
            # Fallback to agent execution for safety
            return ResponseDecision(
                response_type=ResponseType.AGENT_EXECUTION,
                confidence=0.5,
                reasoning=f"Analysis failed, defaulting to agent execution: {e}",
                context_sources=[],
                suggested_agents=[],
                answer_strategy="fallback_execution"
            )
    
    def _build_response_analysis_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Build prompt for response type analysis."""
        
        # Extract relevant context
        recent_workflows = context.get("completed_workflows", [])
        conversation_history = context.get("conversation_history", [])
        session_context = context.get("session_context", {})
        recent_deliverables = context.get("recent_deliverables", [])
        
        # Build context summary
        context_summary = self._build_context_summary(
            recent_workflows, conversation_history, session_context, recent_deliverables
        )
        
        return f"""You are a context-aware response analyzer. Determine how to respond to this user message.

USER MESSAGE: "{message}"

CONVERSATION CONTEXT:
{context_summary}

ANALYSIS INSTRUCTIONS:
Determine the appropriate response type based on the message and available context:

1. DIRECT_ANSWER: User is asking about previous work, general knowledge, or information
   - Examples: "What colors did you use?", "What food should restaurants serve?", "How does branding work?"
   - Use when: Context contains relevant information OR general knowledge can answer
   - Key indicators: Questions about past work, informational queries, "what", "how", "why" questions

2. AGENT_EXECUTION: User wants to create, build, generate something new
   - Examples: "Create a website", "Design a logo", "Research the market for electric cars", "Generate leads", "Find prospects"
   - Use when: Clear action request for new deliverables
   - Key indicators: "create", "build", "design", "generate", "make", "develop", "find", "get", "mine"

3. CLARIFICATION: Request is ambiguous or missing critical information
   - Use when: Cannot determine intent clearly
   - Key indicators: Vague requests, incomplete information

4. HYBRID: Can answer question AND suggest related actions
   - Example: "What colors work for restaurants?" → Answer + offer to create website/branding
   - Use when: Informational query that could lead to actionable work

CRITICAL DECISION RULES:
- If user references "you" or previous work (like "the website you made"), ALWAYS use DIRECT_ANSWER
- If user asks "what", "how", "why" questions about existing work, use DIRECT_ANSWER
- If user asks "what", "how", "why" questions about general topics, use DIRECT_ANSWER  
- If user says "create", "build", "make", "design", "generate", "find", "get", "mine", use AGENT_EXECUTION
- CRITICAL: "generate leads", "find prospects", "get customers", "find leads", "need leads" = AGENT_EXECUTION (not advice)
- CRITICAL: ANY request about finding, generating, or getting leads/prospects/customers = AGENT_EXECUTION
- Consider conversation history - if they just completed work, questions are likely about that work

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "response_type": "direct_answer",
    "confidence": 0.95,
    "reasoning": "Detailed explanation of decision and why this response type was chosen",
    "context_sources": ["conversation_history", "recent_workflows", "general_knowledge"],
    "suggested_agents": [],
    "answer_strategy": "How to formulate the response - be specific",
    "requires_context_extraction": true,
    "context_query": "What specific information to extract from context if needed"
}}

Valid response_type values: direct_answer, agent_execution, clarification, hybrid

Analyze the message carefully and provide your decision:"""
    
    def _build_context_summary(
        self, 
        recent_workflows: List[Dict[str, Any]], 
        conversation_history: List[Dict[str, Any]],
        session_context: Dict[str, Any],
        recent_deliverables: List[Dict[str, Any]]
    ) -> str:
        """Build a concise context summary for analysis."""
        
        summary_parts = []
        
        # Recent conversation
        if conversation_history:
            last_messages = conversation_history[-3:]  # Last 3 exchanges
            summary_parts.append("RECENT CONVERSATION:")
            for msg in last_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                summary_parts.append(f"  {role}: {content}")
        
        # Recent deliverables
        if recent_deliverables:
            summary_parts.append("\nRECENT WORK COMPLETED:")
            for deliverable in recent_deliverables[-3:]:  # Last 3 deliverables
                agent_type = deliverable.get("agent_type", "unknown")
                business_goal = deliverable.get("business_goal", "")
                deliverable_list = deliverable.get("deliverables", [])
                summary_parts.append(f"  {agent_type}: {business_goal}")
                for item in deliverable_list[:2]:  # Top 2 items
                    summary_parts.append(f"    - {item}")
        
        # Session context
        if session_context:
            last_result = session_context.get("last_result", {})
            if last_result:
                business_goal = last_result.get("business_goal", "")
                agents_used = last_result.get("agents_used", [])
                if business_goal:
                    summary_parts.append(f"\nLAST REQUEST: {business_goal}")
                if agents_used:
                    summary_parts.append(f"AGENTS USED: {', '.join(agents_used)}")
        
        return "\n".join(summary_parts) if summary_parts else "No significant context available"
    
    def _parse_response_decision(self, ai_response: str, original_message: str) -> ResponseDecision:
        """Parse AI response into ResponseDecision object."""
        
        try:
            # Try to extract JSON from response
            response_text = ai_response.strip()
            
            # Clean up the response text - remove any control characters
            import re
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
            
            # Find JSON content (sometimes wrapped in markdown)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif response_text.startswith("{"):
                json_text = response_text
            else:
                # Look for JSON-like content
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_text = response_text[start:end]
                else:
                    raise ValueError("No JSON found in response")
            
            # Clean JSON text
            json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
            
            # Parse JSON
            decision_data = json.loads(json_text)
            
            # Create ResponseDecision
            return ResponseDecision(
                response_type=ResponseType(decision_data.get("response_type", "agent_execution")),
                confidence=float(decision_data.get("confidence", 0.5)),
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                context_sources=decision_data.get("context_sources", []),
                suggested_agents=decision_data.get("suggested_agents", []),
                answer_strategy=decision_data.get("answer_strategy", "standard"),
                requires_context_extraction=decision_data.get("requires_context_extraction", False),
                context_query=decision_data.get("context_query")
            )
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"AI Response was: {ai_response}")
            
            # Fallback analysis based on simple heuristics
            return self._fallback_analysis(original_message)
    
    def _fallback_analysis(self, message: str) -> ResponseDecision:
        """Fallback analysis when AI parsing fails."""
        
        message_lower = message.lower().strip()
        
        # Simple heuristics for response type
        creation_keywords = ["create", "build", "make", "design", "generate", "develop", "write"]
        question_keywords = ["what", "how", "why", "which", "when", "where", "tell me"]
        reference_keywords = ["you", "your", "the website", "the logo", "the design", "that", "did you", "you used", "you created", "you built"]
        
        # Check for questions about previous work (highest priority)
        if any(keyword in message_lower for keyword in reference_keywords) or \
           any(combo in message_lower for combo in ["what colors", "what pages", "tell me about", "about the website", "about the logo"]):
            return ResponseDecision(
                response_type=ResponseType.DIRECT_ANSWER,
                confidence=0.8,
                reasoning="Fallback: Question about previous work detected",
                context_sources=["conversation_history", "recent_workflows"],
                suggested_agents=[],
                answer_strategy="answer_from_context"
            )
        
        # Check for general questions
        if any(keyword in message_lower for keyword in question_keywords):
            return ResponseDecision(
                response_type=ResponseType.DIRECT_ANSWER,
                confidence=0.7,
                reasoning="Fallback: General question detected",
                context_sources=["general_knowledge"],
                suggested_agents=[],
                answer_strategy="answer_from_knowledge"
            )
        
        # Check for creation intent
        if any(keyword in message_lower for keyword in creation_keywords):
            return ResponseDecision(
                response_type=ResponseType.AGENT_EXECUTION,
                confidence=0.6,
                reasoning="Fallback: Detected creation keywords",
                context_sources=[],
                suggested_agents=[],
                answer_strategy="execute_agents"
            )
        
        # Default to agent execution
        return ResponseDecision(
            response_type=ResponseType.AGENT_EXECUTION,
            confidence=0.4,
            reasoning="Fallback: Default to agent execution",
            context_sources=[],
            suggested_agents=[],
            answer_strategy="execute_agents"
        )
