"""
Communication Services

Service layer for handling different communication channels and AI classification.
"""

from .gmail_service import GmailService
from .whatsapp_service import WhatsAppService
from .linkedin_service import LinkedInService
from .ai_classification_service import AIClassificationService

__all__ = [
    'GmailService',
    'WhatsAppService', 
    'LinkedInService',
    'AIClassificationService'
] 