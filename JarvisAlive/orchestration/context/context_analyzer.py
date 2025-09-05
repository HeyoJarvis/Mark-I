"""
Context Analyzer - Determines when user is referencing previous work
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ai_engines.anthropic_engine import AnthropicEngine

logger = logging.getLogger(__name__)


@dataclass
class ContextReference:
    """Represents a reference to previous work."""
    references_previous_work: bool
    context_types: List[str]
    specific_data_needed: List[str]
    recency_requirement: str  # "current_session", "today", "this_week"
    cross_agent_synthesis: bool
    confidence: float
    reasoning: str


class ContextAnalyzer:
    """Analyzes user messages to detect references to previous work."""
    
    def __init__(self, ai_engine: AnthropicEngine):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        # Reference patterns we look for
        self.reference_patterns = {
            "lead_mining": ["those leads", "the leads", "these prospects", "my leads", "the contacts", "those prospects"],
            "branding": ["those colors", "the brand", "my logo", "the design", "that branding", "my brand"],
            "market_research": ["that research", "the analysis", "my market research", "those insights", "the market data"],
            "website": ["the website", "my site", "that page", "the homepage", "my website"],
            "content_marketing": ["that content", "the blog posts", "my content calendar", "the content strategy"],
            "social_intelligence": ["those mentions", "the sentiment", "social monitoring results", "the social data"]
        }
    
    async def analyze_context_needs(self, message: str, session_id: str) -> ContextReference:
        """Analyze if user message references previous work."""
        
        # Quick pattern check first (performance optimization)
        quick_check = self._quick_pattern_check(message)
        if not quick_check["likely_reference"]:
            return ContextReference(
                references_previous_work=False,
                context_types=[],
                specific_data_needed=[],
                recency_requirement="none",
                cross_agent_synthesis=False,
                confidence=0.0,
                reasoning="No reference patterns detected"
            )
        
        # Full AI analysis for potential references
        return await self._ai_context_analysis(message, quick_check["suggested_types"])
    
    def _quick_pattern_check(self, message: str) -> Dict[str, Any]:
        """Quick pattern matching to detect likely references."""
        message_lower = message.lower()
        
        likely_types = []
        for context_type, patterns in self.reference_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                likely_types.append(context_type)
        
        return {
            "likely_reference": len(likely_types) > 0,
            "suggested_types": likely_types
        }
    
    async def _ai_context_analysis(self, message: str, suggested_types: List[str]) -> ContextReference:
        """Use AI to analyze context needs in detail."""
        
        prompt = f"""
        Analyze this user message for references to previous work:
        
        Message: "{message}"
        Likely context types detected: {suggested_types}
        
        Available context types and their data:
        - branding: brand_name, color_palette, logo_prompt, domain_suggestions
        - market_research: market_analysis, competitors, opportunity_score, target_personas
        - lead_mining: qualified_leads, lead_count, icp_criteria, company_names
        - website: sitemap, homepage, style_guide, seo_recommendations
        - content_marketing: content_calendar, content_gaps, seo_keywords
        - social_intelligence: mentions, sentiment, engagement_opportunities
        
        Determine:
        1. Does this reference previous work? (vs new request)
        2. What type(s) of context are needed?
        3. What specific data should be retrieved?
        4. How recent should the context be?
        5. Does this need synthesis across multiple agent outputs?
        
        Examples:
        - "analyze those leads" → needs lead_mining context, current session
        - "use the brand colors from earlier" → needs branding context, today
        - "create content for those companies" → needs lead_mining + market_research, synthesis
        - "what was my website's homepage structure?" → needs website context, this_week
        
        Return JSON only:
        {{
            "references_previous_work": true/false,
            "context_types": ["lead_mining", "branding"],
            "specific_data_needed": ["qualified_leads", "color_palette"],
            "recency_requirement": "current_session|today|this_week",
            "cross_agent_synthesis": true/false,
            "confidence": 0.95,
            "reasoning": "User is asking to analyze specific leads mentioned earlier"
        }}
        """
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            # Extract JSON from response
            response_text = response.content.strip()
            if "{" in response_text and "}" in response_text:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                json_text = response_text[start_idx:end_idx]
            else:
                json_text = response_text
            
            data = json.loads(json_text)
            
            return ContextReference(
                references_previous_work=data.get("references_previous_work", False),
                context_types=data.get("context_types", []),
                specific_data_needed=data.get("specific_data_needed", []),
                recency_requirement=data.get("recency_requirement", "current_session"),
                cross_agent_synthesis=data.get("cross_agent_synthesis", False),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "")
            )
            
        except Exception as e:
            self.logger.error(f"Context analysis failed: {e}")
            return ContextReference(
                references_previous_work=False,
                context_types=[],
                specific_data_needed=[],
                recency_requirement="none",
                cross_agent_synthesis=False,
                confidence=0.0,
                reasoning=f"Analysis failed: {e}"
            )
