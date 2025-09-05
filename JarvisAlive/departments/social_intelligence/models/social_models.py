"""Data models for social intelligence and monitoring."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SocialSource(str, Enum):
    REDDIT = "reddit"
    GOOGLE_ALERTS = "google_alerts"
    HACKERNEWS = "hackernews"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class SocialMention:
    """Individual social media mention or discussion."""
    # Content info
    content: str
    title: str
    url: str
    author: str
    
    # Platform info
    source: SocialSource
    platform_id: str  # post_id, comment_id, etc.
    subreddit: Optional[str] = None  # For Reddit
    
    # Analysis data
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 0.0  # -1.0 to 1.0
    engagement_score: float = 0.0  # 0.0 to 1.0
    pain_point_detected: bool = False
    buying_signals: List[str] = None
    
    # Metadata
    created_at: str = ""
    discovered_at: str = ""
    upvotes: int = 0
    comments_count: int = 0
    
    def __post_init__(self):
        if self.buying_signals is None:
            self.buying_signals = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.discovered_at:
            self.discovered_at = datetime.now().isoformat()


@dataclass
class Alert:
    """High-priority social mention alert."""
    mention: SocialMention
    alert_type: str  # "brand_mention", "competitor_mention", "pain_point", "crisis"
    priority_score: float  # 0.0 to 1.0
    recommended_action: str
    alert_reason: str
    
    # Alert metadata
    alert_id: str = ""
    triggered_at: str = ""
    acknowledged: bool = False
    
    def __post_init__(self):
        if not self.alert_id:
            import uuid
            self.alert_id = str(uuid.uuid4())
        if not self.triggered_at:
            self.triggered_at = datetime.now().isoformat()


@dataclass
class SentimentSummary:
    """Aggregated sentiment analysis results."""
    total_mentions: int
    positive_count: int
    negative_count: int
    neutral_count: int
    mixed_count: int
    average_sentiment_score: float
    
    @property
    def positive_percentage(self) -> float:
        return (self.positive_count / self.total_mentions * 100) if self.total_mentions > 0 else 0.0
    
    @property
    def negative_percentage(self) -> float:
        return (self.negative_count / self.total_mentions * 100) if self.total_mentions > 0 else 0.0
    
    @property
    def overall_sentiment(self) -> Sentiment:
        if self.average_sentiment_score > 0.2:
            return Sentiment.POSITIVE
        elif self.average_sentiment_score < -0.2:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
