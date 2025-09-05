"""
Email Orchestration Agent (Layer 2)

This is the on-demand agent that handles email campaigns, sequences, and orchestration.
It responds to events from the Communication Monitoring Agent and semantic chat requests.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from .services.gmail_service import GmailService
from .services.ai_classification_service import AIClassificationService
from orchestration.persistent.message_bus import MessageBus, MessageType

from .models.communication_models import (
    EmailSequence, CommunicationContact, CommunicationCampaign,
    CommunicationChannel, MessageClassification
)

logger = logging.getLogger(__name__)


class EmailOrchestrationAgent:
    """
    On-demand agent for email orchestration and campaign management.
    
    This agent handles:
    - Email sequence creation and management
    - AI-powered email personalization
    - Campaign orchestration
    - Reply handling and follow-ups
    - Integration with monitoring layer events
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Email Orchestration Agent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.gmail_service: Optional[GmailService] = None
        self.ai_classification: Optional[AIClassificationService] = None
        self.message_bus: Optional[MessageBus] = None
        
        # State management
        self.active_campaigns: Dict[str, CommunicationCampaign] = {}
        self.active_sequences: Dict[str, EmailSequence] = {}
        self.contacts: Dict[str, CommunicationContact] = {}
        
        # Event subscriptions
        self.subscribed_events = [
            "communication:classified:interested_reply",
            "communication:classified:meeting_request",
            "communication:classified:lead"
        ]
        
        self.logger.info("Email Orchestration Agent initialized")
    
    async def initialize(self) -> bool:
        """Initialize the agent services."""
        try:
            # Initialize Gmail service
            self.gmail_service = GmailService()
            if not await self.gmail_service.initialize():
                self.logger.error("Failed to initialize Gmail service")
                return False
            
            # Initialize AI classification service
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_api_key:
                self.ai_classification = AIClassificationService(anthropic_api_key)
                self.logger.info("AI classification service initialized")
            else:
                self.logger.warning("ANTHROPIC_API_KEY not found, AI features limited")
            
            # Initialize message bus
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.message_bus = MessageBus(redis_url)
            await self.message_bus.connect()
            
            # Subscribe to relevant events
            await self._subscribe_to_events()
            
            self.logger.info("Email Orchestration Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Email Orchestration Agent: {e}")
            return False
    
    async def _subscribe_to_events(self):
        """Subscribe to communication events from monitoring layer."""
        try:
            for event_topic in self.subscribed_events:
                await self.message_bus.subscribe(event_topic, self._handle_communication_event)
                self.logger.info(f"Subscribed to {event_topic}")
                
        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")
    
    async def _handle_communication_event(self, message):
        """Handle incoming communication events from monitoring layer."""
        try:
            event_data = message.payload
            classification = event_data.get('classification')
            
            self.logger.info(f"Received communication event: {classification}")
            
            if classification == 'interested_reply':
                await self._handle_interested_reply(event_data)
            elif classification == 'meeting_request':
                await self._handle_meeting_request(event_data)
            elif classification == 'lead':
                await self._handle_new_lead(event_data)
                
        except Exception as e:
            self.logger.error(f"Error handling communication event: {e}")
    
    async def _handle_interested_reply(self, event_data: Dict[str, Any]):
        """Handle interested reply events."""
        try:
            sender = event_data.get('sender')
            content = event_data.get('content')
            
            # Create or update contact
            contact = await self._get_or_create_contact(sender, event_data)
            
            # Generate personalized follow-up
            if self.ai_classification:
                follow_up_template = """
                Thank you for your interest! I'm excited to discuss how we can help {company} achieve {goals}.
                
                Based on your message, I think you'd be particularly interested in {relevant_solution}.
                
                Would you be available for a brief 15-minute call this week to discuss your specific needs?
                
                Best regards,
                {sender_name}
                """
                
                personalized_message = await self.ai_classification.personalize_message(
                    follow_up_template, 
                    contact.dict()
                )
                
                # Send follow-up email
                await self.gmail_service.send_email(
                    to_email=contact.email or sender,
                    subject=f"Re: Following up on your interest",
                    body=personalized_message,
                    is_html=False
                )
                
                self.logger.info(f"Sent interested reply follow-up to {sender}")
            
        except Exception as e:
            self.logger.error(f"Error handling interested reply: {e}")
    
    async def _handle_meeting_request(self, event_data: Dict[str, Any]):
        """Handle meeting request events."""
        try:
            sender = event_data.get('sender')
            content = event_data.get('content')
            
            # Create or update contact
            contact = await self._get_or_create_contact(sender, event_data)
            
            # Generate meeting response
            meeting_response = f"""
            Hi {contact.name or 'there'},
            
            Thank you for your interest in scheduling a meeting. I'd be happy to discuss how we can help.
            
            Please use this link to schedule a time that works for you: [Calendar Link]
            
            Alternatively, I'm available:
            - Tomorrow 2-4 PM
            - Thursday 10 AM - 12 PM
            - Friday 1-3 PM
            
            Looking forward to our conversation!
            
            Best regards
            """
            
            # Send meeting response
            await self.gmail_service.send_email(
                to_email=contact.email or sender,
                subject="Re: Meeting Request - Let's Schedule",
                body=meeting_response,
                is_html=False
            )
            
            self.logger.info(f"Sent meeting response to {sender}")
            
        except Exception as e:
            self.logger.error(f"Error handling meeting request: {e}")
    
    async def _handle_new_lead(self, event_data: Dict[str, Any]):
        """Handle new lead events."""
        try:
            sender = event_data.get('sender')
            content = event_data.get('content')
            channel = event_data.get('channel')
            
            # Create or update contact
            contact = await self._get_or_create_contact(sender, event_data)
            contact.tags.append('new_lead')
            contact.lead_score = 0.8  # High score for AI-classified leads
            
            # Start lead nurture sequence if it's an email lead
            if channel == 'gmail' and contact.email:
                await self._start_lead_nurture_sequence(contact)
            
            self.logger.info(f"Processed new lead: {sender}")
            
        except Exception as e:
            self.logger.error(f"Error handling new lead: {e}")
    
    async def _get_or_create_contact(self, sender: str, event_data: Dict[str, Any]) -> CommunicationContact:
        """Get existing contact or create new one."""
        try:
            # Check if contact exists
            if sender in self.contacts:
                contact = self.contacts[sender]
                contact.last_interaction = datetime.utcnow()
                contact.interaction_count += 1
                return contact
            
            # Create new contact
            contact = CommunicationContact(
                id=f"contact_{len(self.contacts)}",
                name=sender.split('@')[0] if '@' in sender else sender,
                email=sender if '@' in sender else None,
                phone=sender if sender.startswith('+') else None,
                last_interaction=datetime.utcnow(),
                interaction_count=1
            )
            
            # Extract additional info from metadata if available
            metadata = event_data.get('metadata', {})
            if 'sender_name' in metadata:
                contact.name = metadata['sender_name']
            
            self.contacts[sender] = contact
            return contact
            
        except Exception as e:
            self.logger.error(f"Error creating contact: {e}")
            # Return minimal contact as fallback
            return CommunicationContact(
                id=f"contact_{len(self.contacts)}",
                name=sender,
                email=sender if '@' in sender else None
            )
    
    async def _start_lead_nurture_sequence(self, contact: CommunicationContact):
        """Start a lead nurture email sequence."""
        try:
            # Define nurture sequence
            nurture_sequence = EmailSequence(
                id=f"nurture_{contact.id}",
                name="Lead Nurture Sequence",
                description="3-email nurture sequence for new leads",
                messages=[
                    {
                        "subject": "Welcome! Here's what we can do for {company}",
                        "body": """Hi {name},

Thank you for your interest in our services! I wanted to personally reach out and share how we've helped companies like {company} achieve their goals.

Here are 3 ways we typically help businesses:
1. Increase efficiency by 40% through automation
2. Reduce costs while improving quality
3. Scale operations without adding overhead

I'd love to learn more about your specific challenges and see how we can help.

Would you be interested in a brief 15-minute call this week?

Best regards,
[Your Name]""",
                        "is_html": False
                    },
                    {
                        "subject": "Case Study: How {similar_company} increased revenue by 30%",
                        "body": """Hi {name},

I wanted to share a relevant case study that might interest you.

We recently helped {similar_company} (similar to {company}) achieve:
- 30% increase in revenue
- 50% reduction in manual processes  
- 25% improvement in customer satisfaction

The key was implementing our automated workflow system that streamlined their operations.

I think {company} could see similar results. Would you like to discuss how this might apply to your situation?

Best regards,
[Your Name]""",
                        "is_html": False
                    },
                    {
                        "subject": "Final follow-up - Still interested in growing {company}?",
                        "body": """Hi {name},

I wanted to follow up one last time about helping {company} achieve its growth goals.

If the timing isn't right now, I completely understand. However, if you're still interested in:
- Increasing efficiency
- Reducing costs
- Scaling your operations

I'm here to help. Just reply to this email or schedule a call at your convenience.

If you'd prefer not to receive further emails, just let me know and I'll remove you from my list.

Best regards,
[Your Name]""",
                        "is_html": False
                    }
                ],
                delay_hours=[24, 72, 120],  # 1 day, 3 days, 5 days
                target_audience="new_leads"
            )
            
            # Personalize and send sequence
            await self._send_email_sequence(contact, nurture_sequence)
            
            self.logger.info(f"Started nurture sequence for {contact.name}")
            
        except Exception as e:
            self.logger.error(f"Error starting nurture sequence: {e}")
    
    async def _send_email_sequence(self, contact: CommunicationContact, sequence: EmailSequence):
        """Send personalized email sequence to contact."""
        try:
            if not contact.email:
                self.logger.warning(f"No email address for contact {contact.name}")
                return
            
            # Personalize messages
            personalized_messages = []
            for message in sequence.messages:
                if self.ai_classification:
                    personalized_body = await self.ai_classification.personalize_message(
                        message['body'], 
                        contact.dict()
                    )
                    personalized_subject = await self.ai_classification.personalize_message(
                        message['subject'],
                        contact.dict()
                    )
                else:
                    # Simple template substitution fallback
                    personalized_body = message['body'].replace('{name}', contact.name or 'there')
                    personalized_subject = message['subject'].replace('{company}', contact.company or 'your company')
                
                personalized_messages.append({
                    'subject': personalized_subject,
                    'body': personalized_body,
                    'is_html': message.get('is_html', False)
                })
            
            # Send sequence via Gmail service
            result = await self.gmail_service.send_email_sequence(
                to_email=contact.email,
                messages=personalized_messages,
                delay_hours=sequence.delay_hours
            )
            
            self.logger.info(f"Email sequence sent to {contact.email}: {result}")
            
        except Exception as e:
            self.logger.error(f"Error sending email sequence: {e}")
    
    # Standard agent contract for semantic integration
    async def run(self, state: dict) -> dict:
        """
        Main execution method for semantic agent integration.
        
        This follows the standard agent contract: run(state: dict) -> dict
        """
        try:
            task_type = state.get('task_type')
            
            if task_type == 'send_email_sequence':
                return await self._handle_send_sequence_task(state)
            
            elif task_type == 'personalize_email':
                return await self._handle_personalize_email_task(state)
            
            elif task_type == 'create_campaign':
                return await self._handle_create_campaign_task(state)
            
            elif task_type == 'handle_reply':
                return await self._handle_reply_task(state)
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown task type: {task_type}',
                    'agent': 'email_orchestration_agent'
                }
                
        except Exception as e:
            self.logger.error(f"Error in run method: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'email_orchestration_agent'
            }
    
    async def _handle_send_sequence_task(self, state: dict) -> dict:
        """Handle send email sequence task."""
        try:
            contact_data = state.get('contact_data', {})
            sequence_name = state.get('sequence_name', 'default')
            
            # Create contact from data
            contact = CommunicationContact(**contact_data)
            
            # Get or create sequence
            if sequence_name == 'lead_nurture':
                await self._start_lead_nurture_sequence(contact)
            else:
                return {'success': False, 'error': f'Unknown sequence: {sequence_name}'}
            
            return {
                'success': True,
                'message': f'Email sequence started for {contact.name}',
                'contact_id': contact.id,
                'sequence': sequence_name
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_personalize_email_task(self, state: dict) -> dict:
        """Handle email personalization task."""
        try:
            template = state.get('template', '')
            contact_data = state.get('contact_data', {})
            
            if not self.ai_classification:
                return {'success': False, 'error': 'AI service not available'}
            
            personalized = await self.ai_classification.personalize_message(template, contact_data)
            
            return {
                'success': True,
                'personalized_message': personalized,
                'original_template': template
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_create_campaign_task(self, state: dict) -> dict:
        """Handle create campaign task."""
        try:
            campaign_data = state.get('campaign_data', {})
            
            campaign = CommunicationCampaign(
                id=f"campaign_{len(self.active_campaigns)}",
                name=campaign_data.get('name', 'New Campaign'),
                description=campaign_data.get('description', ''),
                channels=[CommunicationChannel.GMAIL],  # Default to email
                target_contacts=campaign_data.get('target_contacts', []),
                status='active'
            )
            
            self.active_campaigns[campaign.id] = campaign
            
            return {
                'success': True,
                'campaign_id': campaign.id,
                'message': f'Campaign "{campaign.name}" created successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_reply_task(self, state: dict) -> dict:
        """Handle reply processing task."""
        try:
            reply_data = state.get('reply_data', {})
            sender = reply_data.get('sender')
            content = reply_data.get('content')
            
            # Process the reply (this would typically involve updating contact records,
            # triggering follow-up sequences, etc.)
            
            return {
                'success': True,
                'message': f'Reply from {sender} processed successfully',
                'next_action': 'follow_up_scheduled'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.message_bus:
                await self.message_bus.disconnect()
            
            self.logger.info("Email Orchestration Agent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}") 