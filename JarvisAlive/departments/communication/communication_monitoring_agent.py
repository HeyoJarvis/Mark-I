"""
Communication Monitoring Agent (Layer 1)

This is the always-on persistent agent that monitors Gmail, WhatsApp, and LinkedIn
for incoming messages, classifies them with AI, and publishes events to the message bus.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from orchestration.persistent.base_agent import PersistentAgent, TaskRequest, TaskResponse
from orchestration.persistent.message_bus import MessageBus, MessageType

from .services.gmail_service import GmailService
from .services.whatsapp_service import WhatsAppService
from .services.linkedin_service import LinkedInService
from .services.ai_classification_service import AIClassificationService

from .models.communication_models import (
    CommunicationEvent, CommunicationChannel, MonitoringConfig,
    CommunicationMetrics, MessageClassification
)

logger = logging.getLogger(__name__)


class CommunicationMonitoringAgent(PersistentAgent):
    """
    Persistent agent for monitoring communication channels.
    
    This agent runs continuously in the background, monitoring:
    - Gmail for new emails
    - WhatsApp for new messages  
    - LinkedIn for new messages
    
    It classifies messages using AI and publishes events for other agents to consume.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Communication Monitoring Agent."""
        super().__init__("communication_monitoring_agent", config)
        
        # Configuration
        self.monitoring_config = MonitoringConfig(**config) if config else MonitoringConfig()
        
        # Services
        self.gmail_service: Optional[GmailService] = None
        self.whatsapp_service: Optional[WhatsAppService] = None
        self.linkedin_service: Optional[LinkedInService] = None
        self.ai_classification: Optional[AIClassificationService] = None
        
        # Message bus for publishing events
        self.message_bus: Optional[MessageBus] = None
        
        # Monitoring state
        self.last_check_times: Dict[str, datetime] = {}
        self.metrics = CommunicationMetrics()
        
        # Background tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        self.logger.info("Communication Monitoring Agent initialized")
    
    async def on_start(self):
        """Initialize services when agent starts."""
        try:
            # Initialize message bus
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.message_bus = MessageBus(redis_url)
            await self.message_bus.connect()
            
            # Initialize AI classification service
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_api_key:
                self.ai_classification = AIClassificationService(anthropic_api_key)
                self.logger.info("AI classification service initialized")
            else:
                self.logger.warning("ANTHROPIC_API_KEY not found, AI classification disabled")
            
            # Initialize communication services based on configuration
            await self._initialize_services()
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            self.logger.info("Communication Monitoring Agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Communication Monitoring Agent: {e}")
            raise
    
    async def _initialize_services(self):
        """Initialize communication services based on configuration."""
        
        # Initialize Gmail service
        if self.monitoring_config.gmail_enabled:
            try:
                self.gmail_service = GmailService()
                if await self.gmail_service.initialize():
                    self.logger.info("Gmail service initialized successfully")
                else:
                    self.logger.error("Failed to initialize Gmail service")
                    self.gmail_service = None
            except Exception as e:
                self.logger.error(f"Error initializing Gmail service: {e}")
                self.gmail_service = None
        
        # Initialize WhatsApp service
        if self.monitoring_config.whatsapp_enabled:
            try:
                self.whatsapp_service = WhatsAppService()
                if await self.whatsapp_service.initialize():
                    self.logger.info("WhatsApp service initialized successfully")
                else:
                    self.logger.error("Failed to initialize WhatsApp service")
                    self.whatsapp_service = None
            except Exception as e:
                self.logger.error(f"Error initializing WhatsApp service: {e}")
                self.whatsapp_service = None
        
        # Initialize LinkedIn service
        if self.monitoring_config.linkedin_enabled:
            try:
                self.linkedin_service = LinkedInService()
                if await self.linkedin_service.initialize():
                    self.logger.info("LinkedIn service initialized successfully")
                else:
                    self.logger.error("Failed to initialize LinkedIn service")
                    self.linkedin_service = None
            except Exception as e:
                self.logger.error(f"Error initializing LinkedIn service: {e}")
                self.linkedin_service = None
    
    async def _start_monitoring_tasks(self):
        """Start background monitoring tasks for each enabled service."""
        
        # Gmail monitoring task
        if self.gmail_service:
            task = asyncio.create_task(self._monitor_gmail())
            self.monitoring_tasks.append(task)
            self.logger.info("Started Gmail monitoring task")
        
        # WhatsApp monitoring task (webhook-based, so just keep service ready)
        if self.whatsapp_service:
            self.logger.info("WhatsApp monitoring ready (webhook-based)")
        
        # LinkedIn monitoring task
        if self.linkedin_service:
            task = asyncio.create_task(self._monitor_linkedin())
            self.monitoring_tasks.append(task)
            self.logger.info("Started LinkedIn monitoring task")
        
        # Metrics update task
        metrics_task = asyncio.create_task(self._update_metrics_loop())
        self.monitoring_tasks.append(metrics_task)
    
    async def _monitor_gmail(self):
        """Monitor Gmail for new messages."""
        while self._running:
            try:
                # Get new Gmail messages
                messages = await self.gmail_service.monitor_emails(
                    query=self.monitoring_config.gmail_query_filter,
                    max_results=self.monitoring_config.gmail_max_results
                )
                
                # Process each message
                for gmail_message in messages:
                    try:
                        # Convert to communication event
                        event = self.gmail_service.to_communication_event(gmail_message)
                        
                        # Classify with AI if enabled
                        if self.ai_classification:
                            classification = await self.ai_classification.classify_message(event)
                            event.classification = classification['classification']
                            event.priority = classification['priority']
                        
                        # Publish event
                        await self._publish_communication_event(event, classification if self.ai_classification else None)
                        
                        # Update metrics
                        self.metrics.total_messages_monitored += 1
                        self.metrics.messages_by_channel['gmail'] = self.metrics.messages_by_channel.get('gmail', 0) + 1
                        if event.classification:
                            classification_key = event.classification.value
                            self.metrics.messages_by_classification[classification_key] = \
                                self.metrics.messages_by_classification.get(classification_key, 0) + 1
                        
                        # Mark as read if configured
                        if gmail_message.is_unread:
                            await self.gmail_service.mark_as_read(gmail_message.id)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing Gmail message {gmail_message.id}: {e}")
                
                # Wait before next check
                await asyncio.sleep(self.monitoring_config.monitoring_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Error in Gmail monitoring loop: {e}")
                await asyncio.sleep(60)  # Back off on errors
    
    async def _monitor_linkedin(self):
        """Monitor LinkedIn for new messages."""
        while self._running:
            try:
                # Get new LinkedIn messages (via scraping - use with caution)
                messages = await self.linkedin_service.monitor_messages_via_scraping()
                
                # Process each message
                for linkedin_message in messages:
                    try:
                        # Convert to communication event
                        event = self.linkedin_service.to_communication_event(linkedin_message)
                        
                        # Classify with AI if enabled
                        classification = None
                        if self.ai_classification:
                            classification = await self.ai_classification.classify_message(event)
                            event.classification = classification['classification']
                            event.priority = classification['priority']
                        
                        # Publish event
                        await self._publish_communication_event(event, classification)
                        
                        # Update metrics
                        self.metrics.total_messages_monitored += 1
                        self.metrics.messages_by_channel['linkedin'] = self.metrics.messages_by_channel.get('linkedin', 0) + 1
                        if event.classification:
                            classification_key = event.classification.value
                            self.metrics.messages_by_classification[classification_key] = \
                                self.metrics.messages_by_classification.get(classification_key, 0) + 1
                        
                    except Exception as e:
                        self.logger.error(f"Error processing LinkedIn message {linkedin_message.id}: {e}")
                
                # Wait before next check (longer for LinkedIn due to rate limits)
                await asyncio.sleep(self.monitoring_config.monitoring_interval_seconds * 3)
                
            except Exception as e:
                self.logger.error(f"Error in LinkedIn monitoring loop: {e}")
                await asyncio.sleep(300)  # 5 minute back off for LinkedIn errors
    
    async def handle_whatsapp_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook data."""
        try:
            if not self.whatsapp_service:
                return {'success': False, 'error': 'WhatsApp service not initialized'}
            
            # Process webhook data
            messages = await self.whatsapp_service.handle_webhook(webhook_data)
            
            processed_count = 0
            for whatsapp_message in messages:
                try:
                    # Convert to communication event
                    event = self.whatsapp_service.to_communication_event(whatsapp_message)
                    
                    # Classify with AI if enabled
                    classification = None
                    if self.ai_classification:
                        classification = await self.ai_classification.classify_message(event)
                        event.classification = classification['classification']
                        event.priority = classification['priority']
                    
                    # Publish event
                    await self._publish_communication_event(event, classification)
                    
                    # Update metrics
                    self.metrics.total_messages_monitored += 1
                    self.metrics.messages_by_channel['whatsapp'] = self.metrics.messages_by_channel.get('whatsapp', 0) + 1
                    if event.classification:
                        classification_key = event.classification.value
                        self.metrics.messages_by_classification[classification_key] = \
                            self.metrics.messages_by_classification.get(classification_key, 0) + 1
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing WhatsApp message {whatsapp_message.id}: {e}")
            
            return {
                'success': True,
                'messages_processed': processed_count,
                'total_messages': len(messages)
            }
            
        except Exception as e:
            self.logger.error(f"Error handling WhatsApp webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _publish_communication_event(self, event: CommunicationEvent, classification: Optional[Dict[str, Any]] = None):
        """Publish communication event to message bus."""
        try:
            if not self.message_bus:
                self.logger.error("Message bus not initialized")
                return
            
            # Prepare event data
            event_data = {
                'id': event.id,
                'channel': event.channel.value,
                'message_type': event.message_type.value,
                'sender': event.sender,
                'recipient': event.recipient,
                'content': event.content,
                'timestamp': event.timestamp.isoformat(),
                'thread_id': event.thread_id,
                'classification': event.classification.value if event.classification else None,
                'priority': event.priority.value if event.priority else None,
                'metadata': event.metadata
            }
            
            # Add classification details if available
            if classification:
                event_data['ai_classification'] = classification
            
            # Publish to general communication topic
            await self.message_bus.publish(
                topic="communication:message_received",
                message_type=MessageType.SYSTEM_EVENT,
                source=self.agent_id,
                payload=event_data
            )
            
            # Publish to channel-specific topic
            await self.message_bus.publish(
                topic=f"communication:{event.channel.value}:message_received",
                message_type=MessageType.SYSTEM_EVENT,
                source=self.agent_id,
                payload=event_data
            )
            
            # Publish to classification-specific topic if classified
            if event.classification and event.classification != MessageClassification.UNCLASSIFIED:
                await self.message_bus.publish(
                    topic=f"communication:classified:{event.classification.value}",
                    message_type=MessageType.SYSTEM_EVENT,
                    source=self.agent_id,
                    payload=event_data
                )
            
            self.logger.debug(f"Published communication event: {event.id} ({event.channel.value})")
            
        except Exception as e:
            self.logger.error(f"Error publishing communication event: {e}")
    
    async def _update_metrics_loop(self):
        """Periodically update metrics."""
        while self._running:
            try:
                self.metrics.last_updated = datetime.utcnow()
                
                # Publish metrics
                if self.message_bus:
                    await self.message_bus.publish(
                        topic="communication:metrics",
                        message_type=MessageType.SYSTEM_EVENT,
                        source=self.agent_id,
                        payload=self.metrics.model_dump()
                    )
                
                # Wait 5 minutes before next update
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(60)
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process incoming tasks."""
        try:
            task_type = task.input_data.get('task_type')
            
            if task_type == 'get_metrics':
                return TaskResponse(
                    task_id=task.task_id,
                    success=True,
                    result_data=self.metrics.model_dump()
                )
            
            elif task_type == 'get_status':
                status = {
                    'agent_id': self.agent_id,
                    'running': self._running,
                    'services': {
                        'gmail': self.gmail_service is not None,
                        'whatsapp': self.whatsapp_service is not None,
                        'linkedin': self.linkedin_service is not None,
                        'ai_classification': self.ai_classification is not None
                    },
                    'monitoring_tasks': len(self.monitoring_tasks),
                    'metrics': self.metrics.model_dump()
                }
                
                return TaskResponse(
                    task_id=task.task_id,
                    success=True,
                    result_data=status
                )
            
            elif task_type == 'whatsapp_webhook':
                # Handle WhatsApp webhook
                webhook_data = task.input_data.get('webhook_data', {})
                result = await self.handle_whatsapp_webhook(webhook_data)
                
                return TaskResponse(
                    task_id=task.task_id,
                    success=result['success'],
                    result_data=result
                )
            
            else:
                return TaskResponse(
                    task_id=task.task_id,
                    success=False,
                    error_message=f"Unknown task type: {task_type}"
                )
                
        except Exception as e:
            self.logger.error(f"Error processing task {task.task_id}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                success=False,
                error_message=str(e)
            )
    
    async def on_stop(self):
        """Cleanup when agent stops."""
        try:
            # Cancel monitoring tasks
            for task in self.monitoring_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            # Cleanup services
            if self.linkedin_service:
                await self.linkedin_service.cleanup()
            
            # Disconnect message bus
            if self.message_bus:
                await self.message_bus.disconnect()
            
            self.logger.info("Communication Monitoring Agent stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Communication Monitoring Agent: {e}")
    
    def get_supported_tasks(self) -> List[str]:
        """Get list of supported task types."""
        return [
            'get_metrics',
            'get_status',
            'whatsapp_webhook'
        ] 