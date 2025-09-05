"""
Communication Models

Data models for multi-channel communication system.
"""

from .communication_models import (
    CommunicationChannel,
    MessageType,
    MessageClassification,
    MessagePriority,
    CommunicationEvent,
    GmailMessage,
    WhatsAppMessage,
    LinkedInMessage,
    EmailSequence,
    CommunicationContact,
    CommunicationCampaign,
    MonitoringConfig,
    CommunicationMetrics
)

__all__ = [
    'CommunicationChannel',
    'MessageType', 
    'MessageClassification',
    'MessagePriority',
    'CommunicationEvent',
    'GmailMessage',
    'WhatsAppMessage',
    'LinkedInMessage',
    'EmailSequence',
    'CommunicationContact',
    'CommunicationCampaign',
    'MonitoringConfig',
    'CommunicationMetrics'
] 