"""
Advanced Email Orchestration Models

This module defines sophisticated models for advanced email orchestration features:
- Email sequence management
- AI personalization
- Send time optimization
- Reply detection
- Bounce/unsubscribe handling
- Email warming
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
import uuid


class EmailStatus(str, Enum):
    """Email delivery status."""
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    FAILED = "failed"


class BounceType(str, Enum):
    """Types of email bounces."""
    HARD_BOUNCE = "hard_bounce"  # Permanent failure
    SOFT_BOUNCE = "soft_bounce"  # Temporary failure
    BLOCK_BOUNCE = "block_bounce"  # Blocked by recipient
    SPAM_BOUNCE = "spam_bounce"   # Marked as spam


class SendTimeStrategy(str, Enum):
    """Send time optimization strategies."""
    IMMEDIATE = "immediate"
    OPTIMAL_TIME = "optimal_time"
    RECIPIENT_TIMEZONE = "recipient_timezone"
    ENGAGEMENT_BASED = "engagement_based"
    A_B_TEST = "a_b_test"


class WarmupPhase(str, Enum):
    """Email warming phases."""
    INITIAL = "initial"      # 1-50 emails/day
    RAMP_UP = "ramp_up"      # 51-200 emails/day
    SCALING = "scaling"      # 201-500 emails/day
    MATURE = "mature"        # 500+ emails/day


class AdvancedEmailSequence(BaseModel):
    """Advanced email sequence with sophisticated features."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Sequence configuration
    messages: List[Dict[str, Any]]
    delay_strategy: str = "fixed"  # fixed, dynamic, optimal
    delay_hours: List[int] = Field(default_factory=list)
    
    # Advanced features
    personalization_enabled: bool = True
    send_time_optimization: SendTimeStrategy = SendTimeStrategy.OPTIMAL_TIME
    reply_detection_enabled: bool = True
    bounce_handling_enabled: bool = True
    
    # A/B testing
    ab_test_enabled: bool = False
    ab_test_variants: List[Dict[str, Any]] = Field(default_factory=list)
    ab_test_split_ratio: float = 0.5
    
    # Targeting
    target_audience: str
    audience_filters: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance tracking
    open_rate_threshold: float = 0.2
    reply_rate_threshold: float = 0.05
    bounce_rate_threshold: float = 0.05
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailTemplate(BaseModel):
    """Advanced email template with AI personalization."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject_template: str
    body_template: str
    
    # Personalization
    personalization_variables: List[str] = Field(default_factory=list)
    ai_personalization_enabled: bool = True
    personalization_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Dynamic content
    dynamic_content_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    conditional_content: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance data
    average_open_rate: float = 0.0
    average_click_rate: float = 0.0
    average_reply_rate: float = 0.0
    
    # Metadata
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SendTimeOptimization(BaseModel):
    """Send time optimization configuration and data."""
    contact_id: str
    
    # Timezone and preferences
    timezone: Optional[str] = None
    preferred_send_times: List[str] = Field(default_factory=list)  # ["09:00", "14:00"]
    preferred_days: List[str] = Field(default_factory=list)  # ["monday", "tuesday"]
    
    # Engagement history
    historical_open_times: List[datetime] = Field(default_factory=list)
    historical_click_times: List[datetime] = Field(default_factory=list)
    historical_reply_times: List[datetime] = Field(default_factory=list)
    
    # Calculated optimal times
    optimal_send_time: Optional[str] = None  # "14:30"
    optimal_send_day: Optional[str] = None   # "tuesday"
    confidence_score: float = 0.0
    
    # A/B test results
    ab_test_results: Dict[str, float] = Field(default_factory=dict)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ReplyDetection(BaseModel):
    """Reply detection and classification."""
    email_id: str
    thread_id: str
    
    # Reply analysis
    is_reply: bool = False
    reply_type: Optional[str] = None  # positive, negative, neutral, question, out_of_office
    reply_sentiment: Optional[str] = None  # positive, negative, neutral
    reply_intent: Optional[str] = None  # interested, not_interested, meeting_request, question
    
    # AI analysis
    ai_classification: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    
    # Actions taken
    sequence_paused: bool = False
    follow_up_scheduled: bool = False
    human_review_required: bool = False
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class BounceHandling(BaseModel):
    """Bounce and unsubscribe management."""
    contact_id: str
    email_address: str
    
    # Bounce information
    bounce_type: Optional[BounceType] = None
    bounce_reason: Optional[str] = None
    bounce_count: int = 0
    last_bounce_date: Optional[datetime] = None
    
    # Unsubscribe information
    is_unsubscribed: bool = False
    unsubscribe_date: Optional[datetime] = None
    unsubscribe_reason: Optional[str] = None
    unsubscribe_source: Optional[str] = None  # email_link, reply, manual
    
    # Status management
    is_suppressed: bool = False
    suppression_reason: Optional[str] = None
    can_resubscribe: bool = True
    
    # Compliance
    gdpr_compliant: bool = True
    can_spam_compliant: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailWarmupPlan(BaseModel):
    """Email account warming plan and progress."""
    account_id: str
    email_address: str
    
    # Warmup configuration
    current_phase: WarmupPhase = WarmupPhase.INITIAL
    target_daily_volume: int = 50
    current_daily_volume: int = 0
    
    # Progress tracking
    days_in_current_phase: int = 0
    total_emails_sent: int = 0
    successful_deliveries: int = 0
    bounce_rate: float = 0.0
    spam_rate: float = 0.0
    
    # Phase thresholds
    phase_thresholds: Dict[str, Dict[str, int]] = Field(default_factory=lambda: {
        "initial": {"min_days": 7, "max_daily": 50, "min_success_rate": 0.95},
        "ramp_up": {"min_days": 14, "max_daily": 200, "min_success_rate": 0.93},
        "scaling": {"min_days": 21, "max_daily": 500, "min_success_rate": 0.90},
        "mature": {"min_days": 0, "max_daily": 1000, "min_success_rate": 0.88}
    })
    
    # Reputation metrics
    sender_reputation_score: float = 0.0
    domain_reputation_score: float = 0.0
    ip_reputation_score: float = 0.0
    
    # Warmup strategy
    warmup_strategy: str = "gradual"  # gradual, aggressive, conservative
    use_seed_list: bool = True
    seed_list_contacts: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None


class EmailAnalytics(BaseModel):
    """Comprehensive email analytics and performance metrics."""
    sequence_id: Optional[str] = None
    template_id: Optional[str] = None
    campaign_id: Optional[str] = None
    
    # Volume metrics
    emails_scheduled: int = 0
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_bounced: int = 0
    
    # Engagement metrics
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_unsubscribed: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    
    # Advanced metrics
    time_to_open: Optional[float] = None  # Average hours to open
    time_to_click: Optional[float] = None  # Average hours to click
    time_to_reply: Optional[float] = None  # Average hours to reply
    
    # A/B test results
    variant_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    winning_variant: Optional[str] = None
    statistical_significance: Optional[float] = None
    
    # Time-based analysis
    best_send_times: List[str] = Field(default_factory=list)
    best_send_days: List[str] = Field(default_factory=list)
    
    # Metadata
    analysis_period_start: datetime = Field(default_factory=datetime.utcnow)
    analysis_period_end: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class EmailOrchestrationConfig(BaseModel):
    """Configuration for advanced email orchestration."""
    
    # General settings
    max_daily_emails: int = 1000
    max_emails_per_sequence: int = 10
    min_delay_between_emails: int = 1  # hours
    
    # AI personalization
    ai_personalization_enabled: bool = True
    personalization_depth: str = "deep"  # basic, medium, deep
    fallback_to_template: bool = True
    
    # Send time optimization
    send_time_optimization_enabled: bool = True
    timezone_detection_enabled: bool = True
    engagement_learning_enabled: bool = True
    
    # Reply detection
    reply_detection_enabled: bool = True
    auto_pause_on_reply: bool = True
    auto_schedule_followup: bool = False
    
    # Bounce handling
    bounce_handling_enabled: bool = True
    auto_suppress_hard_bounces: bool = True
    max_soft_bounces: int = 3
    
    # Email warming
    email_warming_enabled: bool = True
    auto_adjust_volume: bool = True
    reputation_monitoring: bool = True
    
    # Compliance
    gdpr_compliance: bool = True
    can_spam_compliance: bool = True
    unsubscribe_link_required: bool = True
    
    # Performance thresholds
    min_open_rate: float = 0.15
    min_delivery_rate: float = 0.95
    max_bounce_rate: float = 0.05
    max_unsubscribe_rate: float = 0.02 