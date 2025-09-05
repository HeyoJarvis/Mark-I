"""Data models for monitoring tasks and opportunities."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from .social_models import SocialMention, Alert, SentimentSummary


@dataclass
class MonitoringTask:
    """Configuration for social monitoring task."""
    task_id: str
    task_type: str  # "brand_monitoring", "competitor_tracking", "pain_point_detection"
    
    # Search parameters
    keywords: List[str]
    exclude_keywords: List[str] = None
    sources: List[str] = None  # ["reddit", "google_alerts", "hackernews"]
    subreddits: List[str] = None  # For Reddit monitoring
    
    # Configuration
    max_results: int = 50
    time_range_hours: int = 24
    priority_threshold: float = 0.7
    
    # Status
    active: bool = True
    created_at: str = ""
    last_run: str = ""
    
    def __post_init__(self):
        if self.exclude_keywords is None:
            self.exclude_keywords = []
        if self.sources is None:
            self.sources = ["reddit", "google_alerts", "hackernews"]
        if self.subreddits is None:
            self.subreddits = ["entrepreneur", "SaaS", "startups", "marketing"]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class EngagementOpportunity:
    """Identified opportunity for social engagement."""
    mention: SocialMention
    opportunity_type: str  # "pain_point_discussion", "competitor_complaint", "product_question"
    engagement_score: float  # 0.0 to 1.0
    
    # Opportunity details
    pain_points: List[str]
    suggested_response: str
    engagement_timing: str  # "immediate", "within_hour", "within_day"
    
    # Context
    conversation_context: str
    user_profile_summary: str
    similar_opportunities_count: int = 0
    
    def __post_init__(self):
        if not self.pain_points:
            self.pain_points = []


@dataclass
class SocialListeningResult:
    """Complete result from social listening operation."""
    success: bool
    monitoring_task: MonitoringTask
    
    # Results
    mentions_found: int
    high_priority_mentions: List[SocialMention]
    alerts_generated: List[Alert]
    engagement_opportunities: List[EngagementOpportunity]
    
    # Analysis
    sentiment_summary: SentimentSummary
    trending_topics: List[str]
    competitor_mentions: Dict[str, int]
    pain_points_detected: List[str]
    
    # Metadata
    monitoring_duration_seconds: float
    sources_monitored: List[str]
    error_message: Optional[str] = None
    warnings: List[str] = None
    completed_at: str = ""
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if not self.completed_at:
            self.completed_at = datetime.now().isoformat()
