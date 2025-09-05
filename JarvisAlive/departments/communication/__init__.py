"""
Communication Department

This department handles multi-channel communication monitoring and orchestration
including Gmail, WhatsApp, and LinkedIn integration with AI-powered classification.
"""

from .communication_monitoring_agent import CommunicationMonitoringAgent
from .email_orchestration_agent import EmailOrchestrationAgent

__all__ = [
    'CommunicationMonitoringAgent',
    'EmailOrchestrationAgent'
] 