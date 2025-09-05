"""Content gap analysis and opportunity identification."""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine
from ..models.content_models import ContentGap, ContentType

logger = logging.getLogger(__name__)


class ContentGapAnalyzer:
    """Identifies content gaps and opportunities using AI and SEO data."""
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        if not self.ai_engine:
            self.logger.warning("No AI engine provided - using basic gap analysis")
    
    async def identify_content_gaps(
        self, 
        business_context: Dict[str, Any],
        target_keywords: List[str] = None,
        competitor_analysis: List[Dict[str, Any]] = None
    ) -> List[ContentGap]:
        """Identify content gaps based on business context and keyword research."""
        
        if not self.ai_engine:
            return self._basic_content_gap_analysis(business_context, target_keywords or [])
        
        try:
            return await self._ai_content_gap_analysis(business_context, target_keywords, competitor_analysis)
        except Exception as e:
            self.logger.error(f"AI content gap analysis failed: {e}")
            return self._basic_content_gap_analysis(business_context, target_keywords or [])
    
    async def _ai_content_gap_analysis(
        self, 
        business_context: Dict[str, Any],
        target_keywords: List[str] = None,
        competitor_analysis: List[Dict[str, Any]] = None
    ) -> List[ContentGap]:
        """Use AI to identify sophisticated content gaps."""
        
        prompt = f"""
Analyze this business context and identify high-value content gaps and opportunities:

Business Context:
{json.dumps(business_context, indent=2)}

Target Keywords: {target_keywords or []}

Competitor Analysis: {competitor_analysis or []}

Identify 5-8 high-value content gaps that would help this business attract and convert customers. For each gap, provide:

{{
    "topic": "How to Choose the Right CRM for Small Businesses",
    "target_keywords": ["small business CRM", "CRM comparison", "best CRM"],
    "search_volume": 2400,
    "keyword_difficulty": 0.6,
    "competition_level": "medium",
    "gap_score": 0.85,
    "content_type_recommendation": "blog_post",
    "priority_level": "high",
    "suggested_title": "The Complete Guide to Choosing a CRM for Small Businesses in 2024",
    "content_outline": [
        "Introduction: Why small businesses need CRM",
        "Key features to look for",
        "Budget considerations",
        "Top 5 CRM options compared",
        "Implementation best practices",
        "Conclusion and next steps"
    ],
    "target_audience": "small business owners and managers",
    "user_intent": "commercial",
    "competitor_content_count": 15,
    "content_angle": "Focus on budget-conscious small businesses with practical implementation tips"
}}

Return a JSON array of content gap objects. Focus on gaps that:
- Address real customer pain points
- Have reasonable search volume and competition
- Align with the business goals
- Provide clear differentiation opportunities

Return only the JSON array.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            gaps_data = json.loads(response_text)
            
            content_gaps = []
            for gap_data in gaps_data:
                gap = ContentGap(
                    topic=gap_data.get('topic', ''),
                    target_keywords=gap_data.get('target_keywords', []),
                    search_volume=gap_data.get('search_volume', 0),
                    keyword_difficulty=gap_data.get('keyword_difficulty', 0.5),
                    competition_level=gap_data.get('competition_level', 'medium'),
                    gap_score=gap_data.get('gap_score', 0.5),
                    content_type_recommendation=ContentType(gap_data.get('content_type_recommendation', 'blog_post')),
                    priority_level=gap_data.get('priority_level', 'medium'),
                    suggested_title=gap_data.get('suggested_title', ''),
                    content_outline=gap_data.get('content_outline', []),
                    target_audience=gap_data.get('target_audience', ''),
                    user_intent=gap_data.get('user_intent', 'informational'),
                    competitor_content_count=gap_data.get('competitor_content_count', 0),
                    top_ranking_urls=[],  # Would be populated from SEO tools
                    content_angle=gap_data.get('content_angle', '')
                )
                content_gaps.append(gap)
            
            self.logger.info(f"AI identified {len(content_gaps)} content gaps")
            return content_gaps
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI gap analysis response: {e}")
            return self._basic_content_gap_analysis(business_context, target_keywords or [])
        except Exception as e:
            self.logger.error(f"AI gap analysis error: {e}")
            return self._basic_content_gap_analysis(business_context, target_keywords or [])
    
    def _basic_content_gap_analysis(self, business_context: Dict[str, Any], target_keywords: List[str]) -> List[ContentGap]:
        """Basic content gap analysis without AI."""
        
        business_type = business_context.get('business_type', 'business')
        industry = business_context.get('industry', 'technology')
        
        # Generate basic content gaps based on common business needs
        basic_gaps = [
            {
                "topic": f"How to Choose the Right {business_type} Solution",
                "keywords": [f"{business_type} comparison", f"best {business_type}"],
                "content_type": ContentType.BLOG_POST,
                "priority": "high"
            },
            {
                "topic": f"{industry} Industry Trends and Insights",
                "keywords": [f"{industry} trends", f"{industry} insights"],
                "content_type": ContentType.ARTICLE,
                "priority": "medium"
            },
            {
                "topic": f"Case Study: Success with {business_type}",
                "keywords": [f"{business_type} case study", f"{business_type} success"],
                "content_type": ContentType.CASE_STUDY,
                "priority": "high"
            },
            {
                "topic": f"Getting Started with {business_type}",
                "keywords": [f"{business_type} guide", f"how to {business_type}"],
                "content_type": ContentType.BLOG_POST,
                "priority": "medium"
            }
        ]
        
        content_gaps = []
        for i, gap_data in enumerate(basic_gaps):
            gap = ContentGap(
                topic=gap_data["topic"],
                target_keywords=gap_data["keywords"],
                search_volume=1000 + i * 500,  # Mock search volume
                keyword_difficulty=0.5 + i * 0.1,
                competition_level="medium",
                gap_score=0.7 - i * 0.1,
                content_type_recommendation=gap_data["content_type"],
                priority_level=gap_data["priority"],
                suggested_title=gap_data["topic"],
                content_outline=[
                    "Introduction",
                    "Main content section 1",
                    "Main content section 2",
                    "Conclusion and next steps"
                ],
                target_audience="business professionals",
                user_intent="informational",
                competitor_content_count=10 + i * 5,
                top_ranking_urls=[],  # Add required parameter
                content_angle=f"Focus on practical implementation for {business_type}"
            )
            content_gaps.append(gap)
        
        self.logger.info(f"Generated {len(content_gaps)} basic content gaps")
        return content_gaps
    
    def prioritize_content_gaps(self, gaps: List[ContentGap]) -> List[ContentGap]:
        """Prioritize content gaps by potential value."""
        
        def calculate_priority_score(gap: ContentGap) -> float:
            score = gap.gap_score
            
            # Boost score for high search volume
            if gap.search_volume > 2000:
                score += 0.1
            elif gap.search_volume > 1000:
                score += 0.05
            
            # Reduce score for high difficulty
            if gap.keyword_difficulty > 0.7:
                score -= 0.1
            elif gap.keyword_difficulty < 0.3:
                score += 0.05
            
            # Boost score for low competition
            if gap.competition_level == "low":
                score += 0.1
            elif gap.competition_level == "high":
                score -= 0.05
            
            # Boost score for commercial intent
            if gap.user_intent == "commercial":
                score += 0.15
            elif gap.user_intent == "transactional":
                score += 0.2
            
            return min(1.0, max(0.0, score))
        
        # Calculate priority scores and sort
        for gap in gaps:
            gap.gap_score = calculate_priority_score(gap)
        
        return sorted(gaps, key=lambda g: g.gap_score, reverse=True)
    
    async def analyze_content_performance_gaps(self, existing_content: List[Dict[str, Any]]) -> List[str]:
        """Analyze existing content to identify performance gaps."""
        
        performance_gaps = []
        
        if not existing_content:
            performance_gaps.append("No existing content found - need to create foundational content")
            return performance_gaps
        
        # Analyze content performance patterns
        low_traffic_content = [c for c in existing_content if c.get('page_views', 0) < 100]
        if len(low_traffic_content) > len(existing_content) * 0.5:
            performance_gaps.append("Over 50% of content has low traffic - SEO optimization needed")
        
        # Check content freshness
        old_content = [c for c in existing_content if self._is_content_old(c.get('publish_date', ''))]
        if len(old_content) > len(existing_content) * 0.3:
            performance_gaps.append("30%+ of content is outdated - content refresh campaign needed")
        
        # Check content type diversity
        content_types = set(c.get('content_type', 'blog_post') for c in existing_content)
        if len(content_types) < 3:
            performance_gaps.append("Limited content type diversity - expand beyond blog posts")
        
        # Check keyword targeting
        untargeted_content = [c for c in existing_content if not c.get('target_keywords')]
        if len(untargeted_content) > 0:
            performance_gaps.append(f"{len(untargeted_content)} pieces lack keyword targeting")
        
        return performance_gaps
    
    def _is_content_old(self, publish_date: str) -> bool:
        """Check if content is considered old (>6 months)."""
        if not publish_date:
            return True
        
        try:
            pub_date = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
            months_old = (datetime.now() - pub_date.replace(tzinfo=None)).days / 30
            return months_old > 6
        except:
            return True
