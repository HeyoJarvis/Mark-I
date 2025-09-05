"""Real-time alert management for social mentions."""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import uuid

from ..models.social_models import SocialMention, Alert, Sentiment
from ..models.monitoring_models import EngagementOpportunity

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages real-time alerts for high-priority social mentions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Alert configuration
        self.priority_threshold = self.config.get('priority_threshold', 0.7)
        self.max_alerts_per_hour = self.config.get('max_alerts_per_hour', 10)
        
        # Alert callbacks (for real-time notifications)
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Alert history (for deduplication and rate limiting)
        self.recent_alerts: List[Alert] = []
        self.alert_keywords_seen = set()
        
        self.logger.info("AlertManager initialized")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add a callback function to be called when alerts are generated."""
        self.alert_callbacks.append(callback)
        self.logger.info(f"Added alert callback: {callback.__name__}")
    
    def generate_alerts(self, mentions: List[SocialMention]) -> List[Alert]:
        """Generate alerts from social mentions based on priority criteria."""
        alerts = []
        
        for mention in mentions:
            alert = self._evaluate_mention_for_alert(mention)
            if alert:
                alerts.append(alert)
        
        # Apply rate limiting
        alerts = self._apply_rate_limiting(alerts)
        
        # Trigger callbacks for new alerts
        for alert in alerts:
            self._trigger_alert_callbacks(alert)
        
        # Update alert history
        self.recent_alerts.extend(alerts)
        self._cleanup_old_alerts()
        
        self.logger.info(f"Generated {len(alerts)} alerts from {len(mentions)} mentions")
        return alerts
    
    def _evaluate_mention_for_alert(self, mention: SocialMention) -> Optional[Alert]:
        """Evaluate a single mention to determine if it warrants an alert."""
        
        alert_type = None
        priority_score = 0.0
        recommended_action = ""
        alert_reason = ""
        
        # Brand mention detection
        if self._is_brand_mention(mention):
            alert_type = "brand_mention"
            priority_score = 0.6
            
            if mention.sentiment == Sentiment.NEGATIVE:
                priority_score = 0.8
                recommended_action = "Monitor and consider responding to address concerns"
                alert_reason = "Negative brand mention detected"
            elif mention.sentiment == Sentiment.POSITIVE:
                priority_score = 0.5
                recommended_action = "Consider thanking the user or amplifying positive feedback"
                alert_reason = "Positive brand mention detected"
            else:
                recommended_action = "Monitor for context and potential engagement"
                alert_reason = "Brand mention detected"
        
        # Competitor mention detection
        elif self._is_competitor_mention(mention):
            alert_type = "competitor_mention"
            priority_score = 0.5
            
            if mention.sentiment == Sentiment.NEGATIVE:
                priority_score = 0.7
                recommended_action = "Potential opportunity to engage with dissatisfied competitor users"
                alert_reason = "Negative competitor mention - engagement opportunity"
            else:
                recommended_action = "Monitor competitor discussion for insights"
                alert_reason = "Competitor mentioned in discussion"
        
        # Pain point detection
        elif self._is_pain_point_discussion(mention):
            alert_type = "pain_point"
            priority_score = 0.6
            recommended_action = "Potential lead - user discussing relevant pain points"
            alert_reason = "Pain point discussion detected"
            
            # Higher priority for specific pain points we can solve
            if self._is_solvable_pain_point(mention):
                priority_score = 0.8
                recommended_action = "High-value engagement opportunity - user has pain point we solve"
        
        # Crisis detection (very negative sentiment with high engagement)
        elif (mention.sentiment == Sentiment.NEGATIVE and 
              mention.sentiment_score < -0.6 and 
              mention.upvotes > 10):
            alert_type = "crisis"
            priority_score = 0.9
            recommended_action = "URGENT: Potential crisis situation requiring immediate attention"
            alert_reason = "High-engagement negative content detected"
        
        # Check if priority meets threshold
        if alert_type and priority_score >= self.priority_threshold:
            # Check for recent similar alerts (deduplication)
            if not self._is_duplicate_alert(mention, alert_type):
                return Alert(
                    mention=mention,
                    alert_type=alert_type,
                    priority_score=priority_score,
                    recommended_action=recommended_action,
                    alert_reason=alert_reason
                )
        
        return None
    
    def _is_brand_mention(self, mention: SocialMention) -> bool:
        """Check if mention contains brand references."""
        # This would be configured with actual brand names
        brand_keywords = self.config.get('brand_keywords', [
            'jarvis', 'our company', 'our product', 'our service'
        ])
        
        content_lower = (mention.content + " " + mention.title).lower()
        return any(keyword.lower() in content_lower for keyword in brand_keywords)
    
    def _is_competitor_mention(self, mention: SocialMention) -> bool:
        """Check if mention contains competitor references."""
        competitor_keywords = self.config.get('competitor_keywords', [
            'hubspot', 'salesforce', 'pipedrive', 'zoho', 'monday.com'
        ])
        
        content_lower = (mention.content + " " + mention.title).lower()
        return any(keyword.lower() in content_lower for keyword in competitor_keywords)
    
    def _is_pain_point_discussion(self, mention: SocialMention) -> bool:
        """Check if mention discusses relevant pain points."""
        pain_point_indicators = [
            'struggling with', 'having trouble', 'need help', 'looking for',
            'alternatives to', 'better than', 'problems with', 'issues with',
            'frustrated with', 'can\'t figure out', 'difficult to', 'hard to'
        ]
        
        content_lower = (mention.content + " " + mention.title).lower()
        return any(indicator in content_lower for indicator in pain_point_indicators)
    
    def _is_solvable_pain_point(self, mention: SocialMention) -> bool:
        """Check if the pain point is something we can solve."""
        solvable_keywords = self.config.get('solvable_pain_points', [
            'crm', 'customer management', 'lead tracking', 'sales pipeline',
            'marketing automation', 'email marketing', 'lead generation'
        ])
        
        content_lower = (mention.content + " " + mention.title).lower()
        return any(keyword.lower() in content_lower for keyword in solvable_keywords)
    
    def _is_duplicate_alert(self, mention: SocialMention, alert_type: str) -> bool:
        """Check if we've already generated a similar alert recently."""
        
        # Check recent alerts for similar content
        recent_cutoff = datetime.now() - timedelta(hours=1)
        
        for alert in self.recent_alerts:
            alert_time = datetime.fromisoformat(alert.triggered_at.replace('Z', '+00:00'))
            
            if (alert_time > recent_cutoff and 
                alert.alert_type == alert_type and
                self._mentions_are_similar(mention, alert.mention)):
                return True
        
        return False
    
    def _mentions_are_similar(self, mention1: SocialMention, mention2: SocialMention) -> bool:
        """Check if two mentions are similar enough to be considered duplicates."""
        
        # Same author
        if mention1.author == mention2.author:
            return True
        
        # Same URL
        if mention1.url == mention2.url:
            return True
        
        # Similar content (simple check)
        content1_words = set(mention1.content.lower().split())
        content2_words = set(mention2.content.lower().split())
        
        if len(content1_words) > 0 and len(content2_words) > 0:
            overlap = len(content1_words.intersection(content2_words))
            similarity = overlap / min(len(content1_words), len(content2_words))
            
            if similarity > 0.7:  # 70% word overlap
                return True
        
        return False
    
    def _apply_rate_limiting(self, alerts: List[Alert]) -> List[Alert]:
        """Apply rate limiting to prevent alert spam."""
        
        # Count recent alerts
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_count = sum(1 for alert in self.recent_alerts 
                          if datetime.fromisoformat(alert.triggered_at.replace('Z', '+00:00')) > recent_cutoff)
        
        # Limit new alerts based on recent count
        available_slots = max(0, self.max_alerts_per_hour - recent_count)
        
        if len(alerts) <= available_slots:
            return alerts
        
        # Sort by priority and return top alerts
        sorted_alerts = sorted(alerts, key=lambda a: a.priority_score, reverse=True)
        limited_alerts = sorted_alerts[:available_slots]
        
        if len(alerts) > available_slots:
            self.logger.warning(f"Rate limiting applied: {len(alerts)} alerts reduced to {len(limited_alerts)}")
        
        return limited_alerts
    
    def _trigger_alert_callbacks(self, alert: Alert):
        """Trigger all registered alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
    
    def _cleanup_old_alerts(self):
        """Remove old alerts from history to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.recent_alerts = [
            alert for alert in self.recent_alerts
            if datetime.fromisoformat(alert.triggered_at.replace('Z', '+00:00')) > cutoff_time
        ]
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of alerts generated in the specified time period."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.recent_alerts
            if datetime.fromisoformat(alert.triggered_at.replace('Z', '+00:00')) > cutoff_time
        ]
        
        alert_types = {}
        for alert in recent_alerts:
            alert_types[alert.alert_type] = alert_types.get(alert.alert_type, 0) + 1
        
        return {
            "total_alerts": len(recent_alerts),
            "alert_types": alert_types,
            "average_priority": sum(alert.priority_score for alert in recent_alerts) / len(recent_alerts) if recent_alerts else 0,
            "time_period_hours": hours
        }
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self.recent_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"Alert {alert_id} acknowledged")
                return True
        
        return False
