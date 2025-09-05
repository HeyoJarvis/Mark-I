"""
Social Listening Agent - Brand Monitoring and Social Intelligence

Monitors social media platforms for brand mentions, competitor discussions,
pain points, and engagement opportunities.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig
from .models.social_models import SocialMention, SentimentSummary
from .models.monitoring_models import MonitoringTask, EngagementOpportunity, SocialListeningResult
from .connectors.reddit_connector import RedditConnector
from .connectors.google_alerts_connector import GoogleAlertsConnector
from .connectors.hackernews_connector import HackerNewsConnector
from .utils.sentiment_analyzer import SentimentAnalyzer
from .utils.alert_manager import AlertManager
from .utils.content_classifier import ContentClassifier

logger = logging.getLogger(__name__)


class SocialListeningAgent:
    """
    AI agent for comprehensive social media monitoring and intelligence.
    
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Social Listening Agent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine
        self._initialize_ai_engine()
        
        # Initialize connectors
        self._initialize_connectors()
        
        # Initialize analysis utilities
        self._initialize_utilities()
        
        # Configuration
        self.max_mentions_per_source = self.config.get('max_mentions_per_source', 50)
        self.monitoring_time_range = self.config.get('monitoring_time_range_hours', 24)
        self.priority_threshold = self.config.get('priority_threshold', 0.7)
        
        self.logger.info("SocialListeningAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for content analysis."""
        try:
            api_key = self.config.get('anthropic_api_key') or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                config = AIEngineConfig(
                    api_key=api_key,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.3,  # Low temperature for consistent analysis
                    max_tokens=2000
                )
                self.ai_engine = AnthropicEngine(config)
                self.logger.info("AI engine initialized for social analysis")
            else:
                self.ai_engine = None
                self.logger.warning("No AI engine - using basic analysis")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    def _initialize_connectors(self):
        """Initialize social media platform connectors."""
        self.connectors = {}
        
        # Reddit connector
        reddit_config = self.config.get('reddit', {})
        self.connectors['reddit'] = RedditConnector(reddit_config)
        
        # Google Alerts connector
        google_config = self.config.get('google_alerts', {})
        self.connectors['google_alerts'] = GoogleAlertsConnector(google_config)
        
        # Hacker News connector
        hn_config = self.config.get('hackernews', {})
        self.connectors['hackernews'] = HackerNewsConnector(hn_config)
        
        self.logger.info(f"Initialized {len(self.connectors)} social media connectors")
    
    def _initialize_utilities(self):
        """Initialize analysis and processing utilities."""
        self.sentiment_analyzer = SentimentAnalyzer(self.ai_engine)
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.content_classifier = ContentClassifier(self.ai_engine)
        
        self.logger.info("Analysis utilities initialized")
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for social listening.
        
        Expected state format:
        {
            "monitoring_goal": "Monitor brand mentions and competitor discussions",
            "keywords": ["brand name", "product name"],
            "competitor_keywords": ["competitor1", "competitor2"],
            "sources": ["reddit", "google_alerts", "hackernews"],
            "max_mentions": 100,
            "time_range_hours": 24,
            "monitoring_focus": "brand_monitoring" | "competitor_analysis" | "pain_point_detection"
        }
        
        Returns state with:
        {
            "monitoring_success": True,
            "mentions_found": 47,
            "high_priority_alerts": [...],
            "engagement_opportunities": [...],
            "sentiment_summary": {...},
            "recommended_actions": [...]
        }
        """
        start_time = datetime.now()
        self.logger.info("Starting social listening process")
        
        try:
            # Step 1: Create monitoring task from state
            monitoring_task = self._create_monitoring_task(state)
            
            # Step 2: Collect mentions from all sources
            all_mentions = await self._collect_mentions(monitoring_task)
            
            # Step 3: Analyze sentiment for all mentions
            analyzed_mentions = await self._analyze_sentiment(all_mentions)
            
            # Step 4: Classify content and identify pain points
            classified_mentions = await self._classify_content(analyzed_mentions)
            
            # Step 5: Generate alerts for high-priority mentions
            alerts = self._generate_alerts(classified_mentions)
            
            # Step 6: Identify engagement opportunities
            opportunities = self._identify_opportunities(classified_mentions)
            
            # Step 7: Create comprehensive analysis
            analysis_results = self._create_analysis_results(
                classified_mentions, alerts, opportunities, monitoring_task
            )
            
            # Step 8: Generate recommendations
            recommendations = self._generate_recommendations(analysis_results)
            
            # Step 9: Create final result
            monitoring_duration = (datetime.now() - start_time).total_seconds()
            
            result = SocialListeningResult(
                success=True,
                monitoring_task=monitoring_task,
                mentions_found=len(classified_mentions),
                high_priority_mentions=self._get_high_priority_mentions(classified_mentions),
                alerts_generated=alerts,
                engagement_opportunities=opportunities,
                sentiment_summary=self.sentiment_analyzer.create_sentiment_summary(classified_mentions),
                trending_topics=self._extract_trending_topics(classified_mentions),
                competitor_mentions=self._count_competitor_mentions(classified_mentions),
                pain_points_detected=self._extract_pain_points(classified_mentions),
                monitoring_duration_seconds=monitoring_duration,
                sources_monitored=monitoring_task.sources
            )
            
            # Step 10: Update state with results
            result_state = state.copy()
            result_state.update({
                "monitoring_success": True,
                "mentions_found": result.mentions_found,
                "high_priority_alerts": [alert.__dict__ for alert in result.alerts_generated],
                "engagement_opportunities": [opp.__dict__ for opp in result.engagement_opportunities],
                "sentiment_summary": result.sentiment_summary.__dict__,
                "trending_topics": result.trending_topics,
                "competitor_mentions": result.competitor_mentions,
                "pain_points_detected": result.pain_points_detected,
                "recommended_actions": recommendations,
                "monitoring_completed_at": datetime.now().isoformat(),
                "sources_monitored": result.sources_monitored,
                "monitoring_duration_seconds": result.monitoring_duration_seconds
            })
            
            self.logger.info(f"Social listening completed: {result.mentions_found} mentions, {len(alerts)} alerts, {len(opportunities)} opportunities")
            return result_state
            
        except Exception as e:
            self.logger.error(f"Social listening failed: {e}")
            return self._create_error_response(state, str(e))
    
    def _create_monitoring_task(self, state: Dict[str, Any]) -> MonitoringTask:
        """Create monitoring task from input state."""
        
        # Extract parameters from state
        keywords = state.get("keywords", [])
        competitor_keywords = state.get("competitor_keywords", [])
        all_keywords = keywords + competitor_keywords
        
        # Default keywords if none provided
        if not all_keywords:
            monitoring_goal = state.get("monitoring_goal", "")
            if "brand" in monitoring_goal.lower():
                all_keywords = ["our company", "our product"]
            elif "competitor" in monitoring_goal.lower():
                all_keywords = ["competitor", "alternative"]
            else:
                all_keywords = ["business", "startup", "saas"]
        
        return MonitoringTask(
            task_id=f"social_listening_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_type=state.get("monitoring_focus", "brand_monitoring"),
            keywords=all_keywords,
            exclude_keywords=state.get("exclude_keywords", []),
            sources=state.get("sources", ["reddit", "google_alerts", "hackernews"]),
            subreddits=state.get("subreddits", ["entrepreneur", "SaaS", "startups", "marketing"]),
            max_results=state.get("max_mentions", 100),
            time_range_hours=state.get("time_range_hours", 24),
            priority_threshold=self.priority_threshold
        )
    
    async def _collect_mentions(self, task: MonitoringTask) -> List[SocialMention]:
        """Collect mentions from all configured sources."""
        all_mentions = []
        
        # Distribute quota across sources
        mentions_per_source = task.max_results // len(task.sources)
        
        # Collect from each source in parallel
        collection_tasks = []
        
        for source in task.sources:
            if source in self.connectors:
                if source == "reddit":
                    collection_task = self.connectors[source].search_mentions(
                        task.keywords, task.subreddits, mentions_per_source, task.time_range_hours
                    )
                else:
                    collection_task = self.connectors[source].search_mentions(
                        task.keywords, mentions_per_source, task.time_range_hours
                    )
                collection_tasks.append(collection_task)
        
        # Execute collection in parallel
        if collection_tasks:
            source_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            for result in source_results:
                if isinstance(result, list):
                    all_mentions.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Source collection failed: {result}")
        
        # Update task with actual run time
        task.last_run = datetime.now().isoformat()
        
        self.logger.info(f"Collected {len(all_mentions)} mentions from {len(task.sources)} sources")
        return all_mentions[:task.max_results]
    
    async def _analyze_sentiment(self, mentions: List[SocialMention]) -> List[SocialMention]:
        """Analyze sentiment for all collected mentions."""
        return await self.sentiment_analyzer.analyze_batch_sentiment(mentions)
    
    async def _classify_content(self, mentions: List[SocialMention]) -> List[SocialMention]:
        """Classify content and identify pain points."""
        return await self.content_classifier.identify_pain_points(mentions)
    
    def _generate_alerts(self, mentions: List[SocialMention]) -> List:
        """Generate alerts for high-priority mentions."""
        return self.alert_manager.generate_alerts(mentions)
    
    def _identify_opportunities(self, mentions: List[SocialMention]) -> List[EngagementOpportunity]:
        """Identify engagement opportunities."""
        return self.content_classifier.identify_engagement_opportunities(mentions)
    
    def _create_analysis_results(self, mentions, alerts, opportunities, task) -> Dict[str, Any]:
        """Create comprehensive analysis results."""
        
        # Analyze content themes
        content_themes = self.content_classifier.classify_content_themes(mentions)
        
        return {
            "total_mentions": len(mentions),
            "alerts_count": len(alerts),
            "opportunities_count": len(opportunities),
            "content_themes": {theme: len(theme_mentions) for theme, theme_mentions in content_themes.items()},
            "monitoring_task": task
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Alert-based recommendations
        if analysis["alerts_count"] > 0:
            recommendations.append(f"Review {analysis['alerts_count']} high-priority alerts requiring attention")
        
        # Opportunity-based recommendations
        if analysis["opportunities_count"] > 0:
            recommendations.append(f"Engage with {analysis['opportunities_count']} identified opportunities")
        
        # Content theme recommendations
        themes = analysis.get("content_themes", {})
        if themes.get("pain_point_discussions", 0) > 0:
            recommendations.append("Monitor pain point discussions for product development insights")
        
        if themes.get("competitor_discussions", 0) > 0:
            recommendations.append("Analyze competitor discussions for competitive intelligence")
        
        if themes.get("product_complaints", 0) > 0:
            recommendations.append("Address product complaints to improve customer satisfaction")
        
        # Default recommendation if no specific actions identified
        if not recommendations:
            recommendations.append("Continue monitoring for brand mentions and engagement opportunities")
        
        return recommendations
    
    def _get_high_priority_mentions(self, mentions: List[SocialMention]) -> List[SocialMention]:
        """Get high-priority mentions based on engagement and sentiment."""
        
        high_priority = []
        for mention in mentions:
            # High engagement
            if mention.upvotes > 20 or mention.comments_count > 10:
                high_priority.append(mention)
            # Strong negative sentiment
            elif mention.sentiment_score < -0.6:
                high_priority.append(mention)
            # Pain points detected
            elif mention.pain_point_detected:
                high_priority.append(mention)
        
        # Sort by priority score (combination of factors)
        return sorted(high_priority, key=lambda m: (
            m.upvotes + m.comments_count * 2 + 
            abs(m.sentiment_score) * 10 + 
            (10 if m.pain_point_detected else 0)
        ), reverse=True)[:10]  # Top 10
    
    def _extract_trending_topics(self, mentions: List[SocialMention]) -> List[str]:
        """Extract trending topics from mentions."""
        
        # Simple keyword frequency analysis
        word_counts = {}
        
        for mention in mentions:
            words = (mention.title + " " + mention.content).lower().split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top trending words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count > 1]
    
    def _count_competitor_mentions(self, mentions: List[SocialMention]) -> Dict[str, int]:
        """Count mentions by competitor."""
        
        competitors = ["hubspot", "salesforce", "pipedrive", "zoho", "monday.com"]
        competitor_counts = {}
        
        for mention in mentions:
            content_lower = (mention.content + " " + mention.title).lower()
            for competitor in competitors:
                if competitor in content_lower:
                    competitor_counts[competitor] = competitor_counts.get(competitor, 0) + 1
        
        return competitor_counts
    
    def _extract_pain_points(self, mentions: List[SocialMention]) -> List[str]:
        """Extract all detected pain points."""
        
        all_pain_points = []
        for mention in mentions:
            if mention.pain_point_detected and mention.buying_signals:
                all_pain_points.extend(mention.buying_signals)
        
        # Remove duplicates and return unique pain points
        return list(set(all_pain_points))
    
    def _create_error_response(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create standardized error response."""
        error_state = state.copy()
        error_state.update({
            "monitoring_success": False,
            "monitoring_error": error,
            "mentions_found": 0,
            "high_priority_alerts": [],
            "engagement_opportunities": [],
            "monitoring_completed_at": datetime.now().isoformat()
        })
        return error_state
