"""Data models for content marketing and SEO."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    LANDING_PAGE = "landing_page"
    SOCIAL_POST = "social_post"
    EMAIL_CAMPAIGN = "email_campaign"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    WHITEPAPER = "whitepaper"
    CASE_STUDY = "case_study"
    EBOOK = "ebook"


class ContentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Content:
    """Individual content piece with SEO and performance data."""
    # Basic info
    title: str
    content_type: ContentType
    content_body: str
    meta_description: str
    
    # SEO data
    target_keywords: List[str]
    focus_keyword: str
    slug: str
    
    # Publishing info
    status: ContentStatus = ContentStatus.PLANNED
    publish_date: Optional[str] = None
    author: str = ""
    
    # Performance tracking
    page_views: int = 0
    organic_traffic: int = 0
    backlinks_count: int = 0
    social_shares: int = 0
    leads_generated: int = 0
    conversion_rate: float = 0.0
    
    # SEO metrics
    seo_score: float = 0.0
    keyword_density: float = 0.0
    readability_score: float = 0.0
    
    # Distribution
    published_channels: List[str] = None
    canonical_url: str = ""
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""
    content_id: str = ""
    
    def __post_init__(self):
        if self.target_keywords is None:
            self.target_keywords = []
        if self.published_channels is None:
            self.published_channels = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
        if not self.content_id:
            import uuid
            self.content_id = str(uuid.uuid4())


@dataclass
class ContentGap:
    """Identified content gap opportunity."""
    # Gap identification
    topic: str
    target_keywords: List[str]
    search_volume: int
    keyword_difficulty: float
    competition_level: str  # "low", "medium", "high"
    
    # Opportunity analysis
    gap_score: float  # 0.0 to 1.0 - how valuable this gap is
    content_type_recommendation: ContentType
    priority_level: str  # "high", "medium", "low"
    
    # Content strategy
    suggested_title: str
    content_outline: List[str]
    target_audience: str
    user_intent: str  # "informational", "commercial", "transactional"
    
    # Competitive analysis
    competitor_content_count: int
    top_ranking_urls: List[str]
    content_angle: str  # How to differentiate from competitors
    
    # Metadata
    identified_at: str = ""
    gap_id: str = ""
    
    def __post_init__(self):
        if self.content_outline is None:
            self.content_outline = []
        if self.top_ranking_urls is None:
            self.top_ranking_urls = []
        if not self.identified_at:
            self.identified_at = datetime.now().isoformat()
        if not self.gap_id:
            import uuid
            self.gap_id = str(uuid.uuid4())


@dataclass
class SEOAnalysis:
    """SEO analysis results for content."""
    content_id: str
    
    # Keyword analysis
    primary_keyword: str
    keyword_density: float
    keyword_placement_score: float
    related_keywords_found: List[str]
    
    # Technical SEO
    title_tag_optimized: bool
    meta_description_optimized: bool
    header_structure_score: float
    internal_links_count: int
    external_links_count: int
    
    # Content quality
    readability_score: float
    content_length: int
    content_uniqueness: float
    
    # Performance predictions
    ranking_potential: float  # 0.0 to 1.0
    traffic_potential: int
    
    # Recommendations
    seo_recommendations: List[str]
    content_improvements: List[str]
    
    # Overall score
    overall_seo_score: float
    
    # Metadata
    analyzed_at: str = ""
    analysis_id: str = ""
    
    def __post_init__(self):
        if self.related_keywords_found is None:
            self.related_keywords_found = []
        if self.seo_recommendations is None:
            self.seo_recommendations = []
        if self.content_improvements is None:
            self.content_improvements = []
        if not self.analyzed_at:
            self.analyzed_at = datetime.now().isoformat()
        if not self.analysis_id:
            import uuid
            self.analysis_id = str(uuid.uuid4())


@dataclass
class ContentAttribution:
    """Content attribution and lead tracking data."""
    content_id: str
    
    # Traffic attribution
    organic_traffic: int
    direct_traffic: int
    referral_traffic: int
    social_traffic: int
    
    # Lead attribution
    leads_generated: int
    lead_sources: Dict[str, int]  # {"organic": 5, "social": 2}
    conversion_events: List[Dict[str, Any]]
    
    # Engagement metrics
    time_on_page: float
    bounce_rate: float
    pages_per_session: float
    
    # Attribution period
    tracking_start_date: str
    tracking_end_date: str
    
    def __post_init__(self):
        if self.lead_sources is None:
            self.lead_sources = {}
        if self.conversion_events is None:
            self.conversion_events = []
