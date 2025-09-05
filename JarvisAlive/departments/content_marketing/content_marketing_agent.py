"""
Content Marketing Agent - SEO-Optimized Content Strategy and Distribution

Integrates with WordPress, Webflow, SEMrush, and Ahrefs for comprehensive
content marketing automation and optimization.
"""

import asyncio
import logging
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig
from .models.content_models import Content, ContentGap, ContentType, ContentStatus
from .models.calendar_models import ContentCalendar, ContentPlan, ContentMarketingResult
from .connectors.wordpress_connector import WordPressConnector
from .utils.seo_analyzer import SEOAnalyzer
from .utils.content_gap_analyzer import ContentGapAnalyzer

logger = logging.getLogger(__name__)


class ContentMarketingAgent:
    """
    AI agent for comprehensive content marketing automation.
    
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Content Marketing Agent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine
        self._initialize_ai_engine()
        
        # Initialize connectors
        self._initialize_connectors()
        
        # Initialize utilities
        self._initialize_utilities()
        
        # Configuration
        self.max_content_gaps = self.config.get('max_content_gaps', 10)
        self.seo_score_threshold = self.config.get('seo_score_threshold', 0.7)
        self.content_calendar_weeks = self.config.get('content_calendar_weeks', 12)
        
        self.logger.info("ContentMarketingAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for content analysis and creation."""
        try:
            api_key = self.config.get('anthropic_api_key') or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                config = AIEngineConfig(
                    api_key=api_key,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.4,  # Moderate temperature for creative but consistent content
                    max_tokens=3000
                )
                self.ai_engine = AnthropicEngine(config)
                self.logger.info("AI engine initialized for content marketing")
            else:
                self.ai_engine = None
                self.logger.warning("No AI engine - using basic content marketing")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    def _initialize_connectors(self):
        """Initialize CMS and tool connectors."""
        self.connectors = {}
        
        # WordPress connector
        wordpress_config = self.config.get('wordpress', {})
        self.connectors['wordpress'] = WordPressConnector(wordpress_config)
        
        # Add other connectors as needed (Webflow, etc.)
        self.logger.info(f"Initialized {len(self.connectors)} content platform connectors")
    
    def _initialize_utilities(self):
        """Initialize content analysis utilities."""
        self.seo_analyzer = SEOAnalyzer(self.ai_engine)
        self.gap_analyzer = ContentGapAnalyzer(self.ai_engine)
        
        self.logger.info("Content marketing utilities initialized")
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for content marketing operations.
        
        Expected state format:
        {
            "content_goal": "Identify content gaps and create SEO-optimized content calendar",
            "business_context": {
                "business_type": "SaaS",
                "industry": "Marketing Technology",
                "target_audience": "Small business owners"
            },
            "operation_type": "gap_analysis" | "seo_optimization" | "calendar_planning" | "content_distribution",
            "target_keywords": ["CRM software", "marketing automation"],
            "content_preferences": {
                "content_types": ["blog_post", "case_study"],
                "posting_frequency": "weekly",
                "content_length": "long_form"
            }
        }
        
        Returns state with:
        {
            "content_marketing_success": True,
            "content_gaps_identified": [...],
            "seo_analyses_completed": [...],
            "content_calendar_created": {...},
            "recommended_actions": [...]
        }
        """
        start_time = datetime.now()
        self.logger.info("Starting content marketing process")
        
        try:
            # Extract operation type and business context
            operation_type = state.get("operation_type", "gap_analysis")
            business_context = state.get("business_context", {})
            
            # Execute based on operation type
            if operation_type == "gap_analysis":
                result = await self._perform_gap_analysis(state, business_context)
            elif operation_type == "seo_optimization":
                result = await self._perform_seo_optimization(state)
            elif operation_type == "calendar_planning":
                result = await self._create_content_calendar(state, business_context)
            elif operation_type == "content_distribution":
                result = await self._distribute_content(state)
            else:
                # Default: comprehensive content marketing analysis
                result = await self._comprehensive_content_marketing(state, business_context)
            
            # Calculate operation duration
            operation_duration = (datetime.now() - start_time).total_seconds()
            result.operation_duration_seconds = operation_duration
            
            # Update state with results
            result_state = state.copy()
            result_state.update({
                "content_marketing_success": result.success,
                "operation_type": result.operation_type,
                "content_gaps_identified": [gap.__dict__ for gap in result.content_gaps_identified],
                "seo_analyses_completed": result.seo_analyses_completed,
                "content_calendar_created": result.content_calendar_created.__dict__ if result.content_calendar_created else None,
                "total_content_pieces": result.total_content_pieces,
                "avg_seo_score": result.avg_seo_score,
                "estimated_monthly_traffic": result.estimated_monthly_traffic,
                "priority_actions": result.priority_actions,
                "content_recommendations": result.content_recommendations,
                "seo_improvements": result.seo_improvements,
                "tools_used": result.tools_used,
                "operation_duration_seconds": result.operation_duration_seconds,
                "content_marketing_completed_at": datetime.now().isoformat()
            })
            
            self.logger.info(f"Content marketing completed: {operation_type} - {result.total_content_pieces} pieces analyzed")
            return result_state
            
        except Exception as e:
            self.logger.error(f"Content marketing failed: {e}")
            return self._create_error_response(state, str(e))
    
    async def _perform_gap_analysis(self, state: Dict[str, Any], business_context: Dict[str, Any]) -> ContentMarketingResult:
        """Perform content gap analysis."""
        
        target_keywords = state.get("target_keywords", [])
        
        # Identify content gaps
        content_gaps = await self.gap_analyzer.identify_content_gaps(
            business_context, target_keywords
        )
        
        # Prioritize gaps
        prioritized_gaps = self.gap_analyzer.prioritize_content_gaps(content_gaps)
        
        # Generate recommendations
        recommendations = [
            f"Create {gap.content_type_recommendation.value} about '{gap.topic}'"
            for gap in prioritized_gaps[:5]
        ]
        
        return ContentMarketingResult(
            success=True,
            operation_type="gap_analysis",
            content_gaps_identified=prioritized_gaps,
            total_content_pieces=len(prioritized_gaps),
            priority_actions=recommendations,
            tools_used=["ai_analysis", "keyword_research"],
            estimated_monthly_traffic=sum(gap.search_volume for gap in prioritized_gaps[:5])
        )
    
    async def _perform_seo_optimization(self, state: Dict[str, Any]) -> ContentMarketingResult:
        """Perform SEO optimization on existing content."""
        
        # Get existing content from WordPress
        existing_posts = await self.connectors['wordpress'].get_existing_posts(max_posts=50)
        
        # Analyze SEO for each piece of content
        seo_analyses = []
        total_seo_score = 0.0
        
        for content in existing_posts[:10]:  # Limit to avoid too many API calls
            try:
                seo_analysis = await self.seo_analyzer.analyze_content_seo(content)
                seo_analyses.append(seo_analysis.__dict__)
                total_seo_score += seo_analysis.overall_seo_score
            except Exception as e:
                self.logger.error(f"SEO analysis failed for content {content.content_id}: {e}")
        
        avg_seo_score = total_seo_score / len(seo_analyses) if seo_analyses else 0.0
        
        # Generate SEO improvement recommendations
        seo_improvements = []
        low_scoring_content = [analysis for analysis in seo_analyses if analysis.get('overall_seo_score', 0) < 0.6]
        
        if low_scoring_content:
            seo_improvements.append(f"Optimize {len(low_scoring_content)} low-scoring content pieces")
        
        if avg_seo_score < 0.7:
            seo_improvements.append("Overall SEO score below target - focus on keyword optimization")
        
        return ContentMarketingResult(
            success=True,
            operation_type="seo_optimization",
            seo_analyses_completed=seo_analyses,
            total_content_pieces=len(existing_posts),
            avg_seo_score=avg_seo_score,
            seo_improvements=seo_improvements,
            tools_used=["wordpress_api", "seo_analysis", "ai_optimization"]
        )
    
    async def _create_content_calendar(self, state: Dict[str, Any], business_context: Dict[str, Any]) -> ContentMarketingResult:
        """Create a content calendar based on identified gaps and business goals."""
        
        # Get content gaps first
        content_gaps = await self.gap_analyzer.identify_content_gaps(
            business_context, state.get("target_keywords", [])
        )
        
        # Create content plans from gaps
        content_plans = []
        start_date = datetime.now()
        
        for i, gap in enumerate(content_gaps[:self.content_calendar_weeks]):
            planned_date = start_date + timedelta(weeks=i)
            
            plan = ContentPlan(
                planned_date=planned_date.isoformat(),
                content_type=gap.content_type_recommendation,
                title=gap.suggested_title,
                topic=gap.topic,
                target_keywords=gap.target_keywords,
                target_audience=gap.target_audience,
                content_goal="lead_generation" if gap.user_intent == "commercial" else "education",
                priority_level=gap.priority_level,
                estimated_hours=4.0 if gap.content_type_recommendation == ContentType.BLOG_POST else 8.0
            )
            content_plans.append(plan)
        
        # Create calendar
        calendar = ContentCalendar(
            calendar_name=f"Content Calendar - {datetime.now().strftime('%Y Q%m')}",
            start_date=start_date.isoformat(),
            end_date=(start_date + timedelta(weeks=self.content_calendar_weeks)).isoformat(),
            content_plans=content_plans,
            monthly_traffic_goal=sum(gap.search_volume for gap in content_gaps[:4]),
            monthly_leads_goal=50,  # Estimate based on content volume
            target_keywords_count=len(set(kw for gap in content_gaps for kw in gap.target_keywords))
        )
        
        return ContentMarketingResult(
            success=True,
            operation_type="calendar_planning",
            content_calendar_created=calendar,
            total_content_pieces=len(content_plans),
            estimated_monthly_traffic=calendar.monthly_traffic_goal,
            content_recommendations=[
                f"Plan {len(content_plans)} pieces over {self.content_calendar_weeks} weeks",
                f"Target {calendar.target_keywords_count} unique keywords",
                f"Focus on {calendar.monthly_leads_goal} monthly lead generation goal"
            ],
            tools_used=["ai_analysis", "calendar_planning", "gap_analysis"]
        )
    
    async def _distribute_content(self, state: Dict[str, Any]) -> ContentMarketingResult:
        """Distribute content across multiple channels."""
        
        content_to_distribute = state.get("content_to_distribute", [])
        distribution_channels = state.get("distribution_channels", ["wordpress", "social"])
        
        distribution_results = []
        
        for content_data in content_to_distribute:
            # Convert to Content object if needed
            if isinstance(content_data, dict):
                content = Content(**content_data)
            else:
                content = content_data
            
            # Distribute to each channel
            for channel in distribution_channels:
                if channel == "wordpress" and "wordpress" in self.connectors:
                    result = await self.connectors["wordpress"].publish_content(content)
                    distribution_results.append({
                        "content_id": content.content_id,
                        "channel": channel,
                        "success": result.get("success", False),
                        "url": result.get("url", "")
                    })
        
        return ContentMarketingResult(
            success=True,
            operation_type="content_distribution",
            total_content_pieces=len(content_to_distribute),
            content_recommendations=[
                f"Distributed {len(content_to_distribute)} pieces across {len(distribution_channels)} channels"
            ],
            tools_used=["wordpress_api", "content_distribution"]
        )
    
    async def _comprehensive_content_marketing(self, state: Dict[str, Any], business_context: Dict[str, Any]) -> ContentMarketingResult:
        """Perform comprehensive content marketing analysis and planning."""
        
        # Step 1: Gap analysis
        gap_result = await self._perform_gap_analysis(state, business_context)
        
        # Step 2: SEO optimization of existing content
        seo_result = await self._perform_seo_optimization(state)
        
        # Step 3: Create content calendar
        calendar_result = await self._create_content_calendar(state, business_context)
        
        # Combine results
        combined_recommendations = (
            gap_result.priority_actions +
            seo_result.seo_improvements +
            calendar_result.content_recommendations
        )
        
        return ContentMarketingResult(
            success=True,
            operation_type="comprehensive_analysis",
            content_gaps_identified=gap_result.content_gaps_identified,
            seo_analyses_completed=seo_result.seo_analyses_completed,
            content_calendar_created=calendar_result.content_calendar_created,
            total_content_pieces=gap_result.total_content_pieces + seo_result.total_content_pieces,
            avg_seo_score=seo_result.avg_seo_score,
            estimated_monthly_traffic=gap_result.estimated_monthly_traffic,
            priority_actions=combined_recommendations[:10],  # Top 10 actions
            tools_used=["ai_analysis", "wordpress_api", "seo_analysis", "gap_analysis", "calendar_planning"]
        )
    
    def _create_error_response(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create standardized error response."""
        error_state = state.copy()
        error_state.update({
            "content_marketing_success": False,
            "content_marketing_error": error,
            "content_gaps_identified": [],
            "seo_analyses_completed": [],
            "content_marketing_completed_at": datetime.now().isoformat()
        })
        return error_state
