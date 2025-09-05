"""
Communication Models for Multi-Channel Monitoring System

This module defines the data models for Gmail, WhatsApp, and LinkedIn
communication monitoring and orchestration.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass


class CommunicationChannel(str, Enum):
    """Supported communication channels."""
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"


class MessageType(str, Enum):
    """Types of messages."""
    RECEIVED = "received"
    SENT = "sent"
    REPLY = "reply"
    FORWARD = "forward"


class MessageClassification(str, Enum):
    """AI-powered message classifications."""
    INTERESTED_REPLY = "interested_reply"
    NOT_INTERESTED = "not_interested"
    MEETING_REQUEST = "meeting_request"
    QUESTION = "question"
    COMPLAINT = "complaint"
    SPAM = "spam"
    URGENT = "urgent"
    LEAD = "lead"
    CUSTOMER_SUPPORT = "customer_support"
    UNCLASSIFIED = "unclassified"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CommunicationEvent:
    """Base communication event structure."""
    id: str
    channel: CommunicationChannel
    message_type: MessageType
    sender: str
    recipient: str
    content: str
    timestamp: datetime
    thread_id: Optional[str] = None
    classification: Optional[MessageClassification] = None
    priority: Optional[MessagePriority] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class GmailMessage(BaseModel):
    """Gmail-specific message model."""
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    content: str
    snippet: str
    timestamp: datetime
    labels: List[str] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    is_unread: bool = True
    message_type: MessageType = MessageType.RECEIVED
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WhatsAppMessage(BaseModel):
    """WhatsApp-specific message model."""
    id: str
    from_number: str
    to_number: str
    content: str
    message_type: str  # text, image, document, etc.
    timestamp: datetime
    status: str  # sent, delivered, read, failed
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LinkedInMessage(BaseModel):
    """LinkedIn-specific message model."""
    id: str
    conversation_id: str
    sender_profile_id: str
    recipient_profile_id: str
    content: str
    timestamp: datetime
    sender_name: str
    sender_headline: Optional[str] = None
    is_connection_request: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailSequence(BaseModel):
    """Email sequence configuration."""
    id: str
    name: str
    description: str
    messages: List[Dict[str, Any]]
    delay_hours: List[int]  # Hours between each message
    target_audience: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class CommunicationContact(BaseModel):
    """Unified contact model across all channels."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_profile_id: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    lead_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CommunicationCampaign(BaseModel):
    """Multi-channel communication campaign."""
    id: str
    name: str
    description: str
    channels: List[CommunicationChannel]
    target_contacts: List[str]  # Contact IDs
    email_sequence_id: Optional[str] = None
    linkedin_template: Optional[str] = None
    whatsapp_template: Optional[str] = None
    status: str = "draft"  # draft, active, paused, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MonitoringConfig(BaseModel):
    """Configuration for communication monitoring."""
    gmail_enabled: bool = True
    whatsapp_enabled: bool = True
    linkedin_enabled: bool = True
    monitoring_interval_seconds: int = 30
    ai_classification_enabled: bool = True
    auto_reply_enabled: bool = False
    webhook_url: Optional[str] = None
    
    # Gmail specific
    gmail_query_filter: str = "is:unread"
    gmail_max_results: int = 50
    
    # WhatsApp specific
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    
    # LinkedIn specific
    linkedin_check_messages: bool = True
    linkedin_check_connection_requests: bool = True


class CommunicationMetrics(BaseModel):
    """Metrics for communication monitoring and orchestration."""
    total_messages_monitored: int = 0
    messages_by_channel: Dict[str, int] = Field(default_factory=dict)
    messages_by_classification: Dict[str, int] = Field(default_factory=dict)
    emails_sent: int = 0
    sequences_completed: int = 0
    reply_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 