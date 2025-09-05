"""Content classification for pain points and engagement opportunities."""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine
from ..models.social_models import SocialMention
from ..models.monitoring_models import EngagementOpportunity

logger = logging.getLogger(__name__)


class ContentClassifier:
    """Classifies social content for pain points and engagement opportunities."""
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        if not self.ai_engine:
            self.logger.warning("No AI engine provided - using basic classification")
    
    async def identify_pain_points(self, mentions: List[SocialMention]) -> List[SocialMention]:
        """Identify and classify pain points in social mentions."""
        
        for mention in mentions:
            pain_points = await self._extract_pain_points(mention)
            mention.pain_point_detected = len(pain_points) > 0
            
            # Store pain points in buying_signals field for now
            if pain_points:
                mention.buying_signals = pain_points
        
        return mentions
    
    def identify_engagement_opportunities(self, mentions: List[SocialMention]) -> List[EngagementOpportunity]:
        """Identify high-value engagement opportunities from mentions."""
        
        opportunities = []
        
        for mention in mentions:
            opportunity = self._evaluate_engagement_opportunity(mention)
            if opportunity:
                opportunities.append(opportunity)
        
        self.logger.info(f"Identified {len(opportunities)} engagement opportunities from {len(mentions)} mentions")
        return opportunities
    
    async def _extract_pain_points(self, mention: SocialMention) -> List[str]:
        """Extract specific pain points from a mention."""
        
        if not self.ai_engine:
            return self._basic_pain_point_extraction(mention)
        
        try:
            return await self._ai_pain_point_extraction(mention)
        except Exception as e:
            self.logger.error(f"AI pain point extraction failed: {e}")
            return self._basic_pain_point_extraction(mention)
    
    async def _ai_pain_point_extraction(self, mention: SocialMention) -> List[str]:
        """Use AI to extract pain points from mention content."""
        
        prompt = f"""
Analyze this social media content and identify specific pain points or problems the user is experiencing.

Title: {mention.title}
Content: {mention.content}
Source: {mention.source.value}

Look for:
- Problems with current tools/solutions
- Frustrations with processes
- Unmet needs or requirements
- Complaints about cost, complexity, or functionality
- Requests for alternatives or improvements

Return a JSON array of specific pain points found:
[
    "Current CRM is too expensive for small team",
    "Difficult to track leads across multiple channels",
    "Integration with existing tools is complicated"
]

If no clear pain points are found, return an empty array: []

Return only the JSON array.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            pain_points = json.loads(response_text)
            
            if isinstance(pain_points, list):
                return pain_points
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"AI pain point extraction error: {e}")
            return self._basic_pain_point_extraction(mention)
    
    def _basic_pain_point_extraction(self, mention: SocialMention) -> List[str]:
        """Basic keyword-based pain point extraction."""
        
        pain_points = []
        content_lower = (mention.content + " " + mention.title).lower()
        
        # Define pain point patterns
        pain_patterns = {
            "cost_issues": ["too expensive", "costly", "overpriced", "budget", "cheaper alternative"],
            "complexity_issues": ["too complicated", "difficult to", "hard to", "confusing", "complex"],
            "functionality_issues": ["doesn't work", "not working", "broken", "missing feature", "lack of"],
            "integration_issues": ["doesn't integrate", "integration problems", "compatibility issues"],
            "support_issues": ["poor support", "no help", "unresponsive", "bad customer service"],
            "performance_issues": ["slow", "laggy", "crashes", "unreliable", "downtime"]
        }
        
        for category, keywords in pain_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    pain_points.append(f"{category.replace('_', ' ').title()}: {keyword}")
                    break  # Only add one per category
        
        return pain_points
    
    def _evaluate_engagement_opportunity(self, mention: SocialMention) -> Optional[EngagementOpportunity]:
        """Evaluate if a mention represents a good engagement opportunity."""
        
        # Basic scoring factors
        engagement_score = 0.0
        opportunity_type = ""
        pain_points = mention.buying_signals or []
        
        # Pain point discussion
        if mention.pain_point_detected or pain_points:
            engagement_score += 0.4
            opportunity_type = "pain_point_discussion"
        
        # Competitor complaint
        if self._mentions_competitors(mention) and mention.sentiment.value in ['negative', 'mixed']:
            engagement_score += 0.3
            opportunity_type = "competitor_complaint"
        
        # Product question or request for recommendations
        if self._is_product_question(mention):
            engagement_score += 0.3
            opportunity_type = "product_question"
        
        # High engagement content (more visibility)
        if mention.upvotes > 10 or mention.comments_count > 5:
            engagement_score += 0.2
        
        # Recent content (better for timely engagement)
        if self._is_recent_content(mention):
            engagement_score += 0.1
        
        # Only create opportunity if score is significant
        if engagement_score >= 0.5:
            return EngagementOpportunity(
                mention=mention,
                opportunity_type=opportunity_type,
                engagement_score=min(1.0, engagement_score),
                pain_points=pain_points,
                suggested_response=self._generate_suggested_response(mention, opportunity_type),
                engagement_timing=self._determine_engagement_timing(mention, engagement_score),
                conversation_context=self._extract_conversation_context(mention),
                user_profile_summary=self._analyze_user_profile(mention)
            )
        
        return None
    
    def _mentions_competitors(self, mention: SocialMention) -> bool:
        """Check if mention discusses competitors."""
        competitors = ["hubspot", "salesforce", "pipedrive", "zoho", "monday.com"]
        content_lower = (mention.content + " " + mention.title).lower()
        return any(comp in content_lower for comp in competitors)
    
    def _is_product_question(self, mention: SocialMention) -> bool:
        """Check if mention is asking for product recommendations."""
        question_indicators = [
            "what do you recommend", "any suggestions", "looking for", "need a tool",
            "best solution", "alternatives to", "recommendations for", "which tool"
        ]
        content_lower = (mention.content + " " + mention.title).lower()
        return any(indicator in content_lower for indicator in question_indicators)
    
    def _is_recent_content(self, mention: SocialMention) -> bool:
        """Check if content is recent (within last 24 hours)."""
        try:
            created_time = datetime.fromisoformat(mention.created_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - created_time.replace(tzinfo=None)
            return time_diff.total_seconds() < 86400  # 24 hours
        except:
            return True  # Assume recent if can't parse
    
    def _generate_suggested_response(self, mention: SocialMention, opportunity_type: str) -> str:
        """Generate a suggested response for the engagement opportunity."""
        
        if opportunity_type == "pain_point_discussion":
            return f"Hi {mention.author}, I noticed you're dealing with [specific pain point]. We've helped similar companies solve this with [solution approach]. Would you be interested in a brief chat about your current challenges?"
        
        elif opportunity_type == "competitor_complaint":
            return f"Hi {mention.author}, sorry to hear about your experience with [competitor]. We've designed our solution specifically to address these common issues. Happy to share how we approach [specific problem] differently."
        
        elif opportunity_type == "product_question":
            return f"Hi {mention.author}, for your use case, you might want to consider [solution]. We specialize in [relevant area] and have helped companies in similar situations. Would you like to learn more about how it works?"
        
        else:
            return f"Hi {mention.author}, thanks for sharing your thoughts on this topic. We have some experience in this area and would be happy to help if you have any questions."
    
    def _determine_engagement_timing(self, mention: SocialMention, engagement_score: float) -> str:
        """Determine optimal timing for engagement."""
        
        if engagement_score >= 0.8:
            return "immediate"
        elif engagement_score >= 0.6:
            return "within_hour"
        else:
            return "within_day"
    
    def _extract_conversation_context(self, mention: SocialMention) -> str:
        """Extract relevant context from the conversation."""
        
        # For now, return the mention content as context
        # In a full implementation, this would analyze thread context, related comments, etc.
        return f"Discussion in {mention.source.value}" + (f" - {mention.subreddit}" if mention.subreddit else "")
    
    def _analyze_user_profile(self, mention: SocialMention) -> str:
        """Analyze user profile for engagement context."""
        
        # Basic profile analysis based on available data
        profile_info = []
        
        if mention.source.value == "reddit":
            profile_info.append(f"Reddit user in r/{mention.subreddit}")
        elif mention.source.value == "hackernews":
            profile_info.append("Hacker News community member")
        
        if mention.upvotes > 20:
            profile_info.append("Active community participant")
        
        return " | ".join(profile_info) if profile_info else "Social media user"
    
    def classify_content_themes(self, mentions: List[SocialMention]) -> Dict[str, List[SocialMention]]:
        """Classify mentions by content themes."""
        
        themes = {
            "product_complaints": [],
            "feature_requests": [],
            "competitor_discussions": [],
            "industry_trends": [],
            "pain_point_discussions": [],
            "positive_feedback": [],
            "questions_and_help": []
        }
        
        for mention in mentions:
            content_lower = (mention.content + " " + mention.title).lower()
            
            # Classify by theme
            if any(word in content_lower for word in ["complaint", "problem", "issue", "bug"]):
                themes["product_complaints"].append(mention)
            elif any(word in content_lower for word in ["feature", "would be nice", "wish", "add"]):
                themes["feature_requests"].append(mention)
            elif self._mentions_competitors(mention):
                themes["competitor_discussions"].append(mention)
            elif any(word in content_lower for word in ["trend", "future", "industry", "market"]):
                themes["industry_trends"].append(mention)
            elif mention.pain_point_detected:
                themes["pain_point_discussions"].append(mention)
            elif mention.sentiment.value == "positive":
                themes["positive_feedback"].append(mention)
            elif any(word in content_lower for word in ["how", "what", "help", "question"]):
                themes["questions_and_help"].append(mention)
        
        return themes
