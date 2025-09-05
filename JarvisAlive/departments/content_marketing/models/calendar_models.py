"""Data models for content calendar and planning."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from .content_models import Content, ContentGap, ContentType


@dataclass
class ContentPlan:
    """Individual content plan item in the calendar."""
    # Planning info
    planned_date: str  # ISO date string
    content_type: ContentType
    title: str
    topic: str
    
    # Content details
    target_keywords: List[str]
    target_audience: str
    content_goal: str  # "lead_generation", "brand_awareness", "education"
    
    # Production info
    assigned_author: str = ""
    estimated_hours: float = 0.0
    priority_level: str = "medium"  # "high", "medium", "low"
    
    # Dependencies
    requires_research: bool = False
    requires_design: bool = False
    requires_approval: bool = False
    
    # Distribution
    planned_channels: List[str] = None
    
    # Status
    status: str = "planned"  # "planned", "in_progress", "completed", "cancelled"
    
    # Metadata
    plan_id: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if self.target_keywords is None:
            self.target_keywords = []
        if self.planned_channels is None:
            self.planned_channels = ["website", "blog"]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.plan_id:
            import uuid
            self.plan_id = str(uuid.uuid4())


@dataclass
class ContentCalendar:
    """Content calendar with planning and scheduling."""
    # Calendar info
    calendar_name: str
    start_date: str
    end_date: str
    
    # Content plans
    content_plans: List[ContentPlan]
    
    # Calendar metrics (calculated automatically)
    total_pieces_planned: int = 0
    pieces_per_week: float = 0.0
    content_type_distribution: Dict[ContentType, int] = None
    
    # Goals and targets
    monthly_traffic_goal: int = 0
    monthly_leads_goal: int = 0
    target_keywords_count: int = 0
    
    # Status tracking
    completed_pieces: int = 0
    in_progress_pieces: int = 0
    overdue_pieces: int = 0
    
    # Metadata
    calendar_id: str = ""
    created_at: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if self.content_plans is None:
            self.content_plans = []
        if self.content_type_distribution is None:
            self.content_type_distribution = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if not self.calendar_id:
            import uuid
            self.calendar_id = str(uuid.uuid4())
        
        # Calculate metrics
        self.total_pieces_planned = len(self.content_plans)
        
        # Calculate pieces per week
        if self.start_date and self.end_date:
            try:
                start = datetime.fromisoformat(self.start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(self.end_date.replace('Z', '+00:00'))
                weeks = (end - start).days / 7
                self.pieces_per_week = self.total_pieces_planned / weeks if weeks > 0 else 0
            except:
                self.pieces_per_week = 0
        
        # Calculate content type distribution
        type_counts = {}
        for plan in self.content_plans:
            type_counts[plan.content_type] = type_counts.get(plan.content_type, 0) + 1
        self.content_type_distribution = type_counts


@dataclass
class ContentMarketingResult:
    """Complete result from content marketing operation."""
    success: bool
    operation_type: str  # "gap_analysis", "seo_optimization", "calendar_planning", "content_distribution"
    
    # Results by operation type
    content_gaps_identified: List[ContentGap] = None
    seo_analyses_completed: List[Dict[str, Any]] = None
    content_calendar_created: Optional[ContentCalendar] = None
    content_published: List[Content] = None
    
    # Performance metrics
    total_content_pieces: int = 0
    avg_seo_score: float = 0.0
    total_target_keywords: int = 0
    estimated_monthly_traffic: int = 0
    
    # Recommendations
    priority_actions: List[str] = None
    content_recommendations: List[str] = None
    seo_improvements: List[str] = None
    
    # Metadata
    operation_duration_seconds: float = 0.0
    tools_used: List[str] = None
    error_message: Optional[str] = None
    completed_at: str = ""
    
    def __post_init__(self):
        if self.content_gaps_identified is None:
            self.content_gaps_identified = []
        if self.seo_analyses_completed is None:
            self.seo_analyses_completed = []
        if self.content_published is None:
            self.content_published = []
        if self.priority_actions is None:
            self.priority_actions = []
        if self.content_recommendations is None:
            self.content_recommendations = []
        if self.seo_improvements is None:
            self.seo_improvements = []
        if self.tools_used is None:
            self.tools_used = []
        if not self.completed_at:
            self.completed_at = datetime.now().isoformat()
