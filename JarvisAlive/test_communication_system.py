#!/usr/bin/env python3
"""
Test Communication System

This script demonstrates the two-layer communication architecture:
- Layer 1: Communication Monitoring Agent (always-on background monitoring)
- Layer 2: Email Orchestration Agent (on-demand email campaigns and sequences)

Supports Gmail, WhatsApp, and LinkedIn with AI-powered classification.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from departments.communication.communication_monitoring_agent import CommunicationMonitoringAgent
from departments.communication.email_orchestration_agent import EmailOrchestrationAgent
from departments.communication.models.communication_models import (
    MonitoringConfig, CommunicationContact, CommunicationChannel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommunicationSystemDemo:
    """Demo class for the communication system."""
    
    def __init__(self):
        """Initialize the demo."""
        self.monitoring_agent = None
        self.orchestration_agent = None
        
    async def setup_environment(self):
        """Setup environment variables and check prerequisites."""
        logger.info("Setting up environment...")
        
        # Check for required environment variables
        required_vars = {
            'ANTHROPIC_API_KEY': 'Claude AI API key for message classification',
            'GMAIL_CREDENTIALS_PATH': 'Path to Gmail API credentials JSON file',
            'WHATSAPP_ACCESS_TOKEN': 'WhatsApp Business API access token (optional)',
            'WHATSAPP_PHONE_NUMBER_ID': 'WhatsApp phone number ID (optional)',
            'LINKEDIN_EMAIL': 'LinkedIn email for web scraping (optional)',
            'LINKEDIN_PASSWORD': 'LinkedIn password for web scraping (optional)'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"  {var}: {description}")
        
        if missing_vars:
            logger.warning("Missing environment variables:")
            for var in missing_vars:
                logger.warning(var)
            logger.warning("Some features may not work without proper credentials.")
        
        # Set default values for demo
        if not os.getenv('REDIS_URL'):
            os.environ['REDIS_URL'] = 'redis://localhost:6379'
            logger.info("Using default Redis URL: redis://localhost:6379")
    
    async def initialize_agents(self):
        """Initialize both communication agents."""
        logger.info("Initializing communication agents...")
        
        # Configure monitoring
        monitoring_config = MonitoringConfig(
            gmail_enabled=bool(os.getenv('GMAIL_CREDENTIALS_PATH')),
            whatsapp_enabled=bool(os.getenv('WHATSAPP_ACCESS_TOKEN')),
            linkedin_enabled=bool(os.getenv('LINKEDIN_EMAIL')),
            monitoring_interval_seconds=30,
            ai_classification_enabled=bool(os.getenv('ANTHROPIC_API_KEY')),
            auto_reply_enabled=False  # Disabled for demo safety
        )
        
        # Initialize monitoring agent (Layer 1)
        self.monitoring_agent = CommunicationMonitoringAgent(monitoring_config.model_dump())
        
        # Initialize orchestration agent (Layer 2)
        self.orchestration_agent = EmailOrchestrationAgent()
        
        # Start agents
        logger.info("Starting Communication Monitoring Agent...")
        await self.monitoring_agent.on_start()
        
        logger.info("Starting Email Orchestration Agent...")
        await self.orchestration_agent.initialize()
        
        logger.info("Both agents initialized successfully!")
    
    async def demo_monitoring_capabilities(self):
        """Demonstrate monitoring capabilities."""
        logger.info("\n" + "="*50)
        logger.info("DEMO: Communication Monitoring Capabilities")
        logger.info("="*50)
        
        # Get agent status
        status_task = {
            'task_id': 'demo_status',
            'task_data': {'task_type': 'get_status'}
        }
        
        from orchestration.persistent.base_agent import TaskRequest
        task_request = TaskRequest(
            task_id=status_task['task_id'],
            task_type='get_status',
            input_data=status_task['task_data']
        )
        
        response = await self.monitoring_agent.process_task(task_request)
        
        if response.success:
            logger.info("Monitoring Agent Status:")
            status = response.result_data
            logger.info(f"  Agent ID: {status['agent_id']}")
            logger.info(f"  Running: {status['running']}")
            logger.info("  Services:")
            for service, enabled in status['services'].items():
                logger.info(f"    {service}: {'✓' if enabled else '✗'}")
            logger.info(f"  Active monitoring tasks: {status['monitoring_tasks']}")
        else:
            logger.error(f"Failed to get status: {response.error_message}")
        
        # Get metrics
        metrics_task = TaskRequest(
            task_id='demo_metrics',
            task_type='get_metrics',
            input_data={'task_type': 'get_metrics'}
        )
        
        response = await self.monitoring_agent.process_task(metrics_task)
        
        if response.success:
            logger.info("\nMonitoring Metrics:")
            metrics = response.result_data
            logger.info(f"  Total messages monitored: {metrics['total_messages_monitored']}")
            logger.info(f"  Messages by channel: {metrics['messages_by_channel']}")
            logger.info(f"  Messages by classification: {metrics['messages_by_classification']}")
            logger.info(f"  Last updated: {metrics['last_updated']}")
        else:
            logger.error(f"Failed to get metrics: {response.error_message}")
    
    async def demo_email_orchestration(self):
        """Demonstrate email orchestration capabilities."""
        logger.info("\n" + "="*50)
        logger.info("DEMO: Email Orchestration Capabilities")
        logger.info("="*50)
        
        # Demo contact data
        demo_contact = {
            'id': 'demo_contact_1',
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'company': 'Demo Corp',
            'title': 'CEO',
            'industry': 'Technology'
        }
        
        # Test email personalization
        logger.info("Testing email personalization...")
        personalization_state = {
            'task_type': 'personalize_email',
            'template': 'Hi {name}, I hope this email finds you well at {company}. As a {title} in the {industry} industry, you might be interested in our latest solution.',
            'contact_data': demo_contact
        }
        
        result = await self.orchestration_agent.run(personalization_state)
        
        if result['success']:
            logger.info("✓ Email personalization successful!")
            logger.info(f"Original: {personalization_state['template']}")
            logger.info(f"Personalized: {result['personalized_message']}")
        else:
            logger.error(f"✗ Email personalization failed: {result['error']}")
        
        # Test campaign creation
        logger.info("\nTesting campaign creation...")
        campaign_state = {
            'task_type': 'create_campaign',
            'campaign_data': {
                'name': 'Demo Lead Nurture Campaign',
                'description': 'Test campaign for demo purposes',
                'target_contacts': ['demo_contact_1']
            }
        }
        
        result = await self.orchestration_agent.run(campaign_state)
        
        if result['success']:
            logger.info("✓ Campaign creation successful!")
            logger.info(f"Campaign ID: {result['campaign_id']}")
            logger.info(f"Message: {result['message']}")
        else:
            logger.error(f"✗ Campaign creation failed: {result['error']}")
        
        # Test email sequence (dry run - won't actually send emails)
        logger.info("\nTesting email sequence setup...")
        sequence_state = {
            'task_type': 'send_email_sequence',
            'contact_data': demo_contact,
            'sequence_name': 'lead_nurture'
        }
        
        # Note: This would normally send emails, but we'll just test the setup
        logger.info("Email sequence would be configured with:")
        logger.info("  - Welcome email (immediate)")
        logger.info("  - Case study email (after 24 hours)")
        logger.info("  - Follow-up email (after 72 hours)")
        logger.info("  - Final follow-up (after 120 hours)")
        logger.info("  All emails would be AI-personalized for the contact")
    
    async def demo_semantic_integration(self):
        """Demonstrate semantic chat integration."""
        logger.info("\n" + "="*50)
        logger.info("DEMO: Semantic Chat Integration")
        logger.info("="*50)
        
        logger.info("The communication system integrates with the semantic chat interface.")
        logger.info("Users can interact with it using natural language:")
        logger.info("")
        logger.info("Example queries:")
        logger.info("  • 'Monitor my Gmail for new leads'")
        logger.info("  • 'Send a follow-up email sequence to john@example.com'")
        logger.info("  • 'Show me communication metrics for this week'")
        logger.info("  • 'Create a nurture campaign for new LinkedIn connections'")
        logger.info("  • 'Personalize this email template for my contact list'")
        logger.info("")
        logger.info("The system will:")
        logger.info("  1. Parse the natural language request")
        logger.info("  2. Route to appropriate agent (monitoring or orchestration)")
        logger.info("  3. Execute the task with AI assistance")
        logger.info("  4. Return results in conversational format")
    
    async def demo_ai_classification(self):
        """Demonstrate AI classification capabilities."""
        logger.info("\n" + "="*50)
        logger.info("DEMO: AI Message Classification")
        logger.info("="*50)
        
        if not os.getenv('ANTHROPIC_API_KEY'):
            logger.warning("ANTHROPIC_API_KEY not set - AI classification demo skipped")
            return
        
        # Sample messages for classification
        sample_messages = [
            {
                'content': 'Hi, I\'m interested in your services. Can you send me more information about pricing?',
                'sender': 'prospect@example.com',
                'expected': 'INTERESTED_REPLY'
            },
            {
                'content': 'Thanks for reaching out, but we\'re not interested at this time.',
                'sender': 'notinterested@example.com',
                'expected': 'NOT_INTERESTED'
            },
            {
                'content': 'Can we schedule a call to discuss this further? I\'m available next week.',
                'sender': 'meeting@example.com',
                'expected': 'MEETING_REQUEST'
            },
            {
                'content': 'URGENT: Our system is down and we need immediate support!',
                'sender': 'support@example.com',
                'expected': 'URGENT'
            }
        ]
        
        logger.info("Testing AI classification on sample messages...")
        
        from departments.communication.services.ai_classification_service import AIClassificationService
        from departments.communication.models.communication_models import CommunicationEvent, CommunicationChannel, MessageType
        
        ai_service = AIClassificationService(os.getenv('ANTHROPIC_API_KEY'))
        
        for i, sample in enumerate(sample_messages, 1):
            logger.info(f"\nSample {i}:")
            logger.info(f"  Message: {sample['content']}")
            logger.info(f"  Expected: {sample['expected']}")
            
            # Create communication event
            event = CommunicationEvent(
                id=f"demo_{i}",
                channel=CommunicationChannel.GMAIL,
                message_type=MessageType.RECEIVED,
                sender=sample['sender'],
                recipient='demo@example.com',
                content=sample['content'],
                timestamp=datetime.utcnow()
            )
            
            try:
                # Classify the message
                classification = await ai_service.classify_message(event)
                
                logger.info(f"  AI Result: {classification['classification'].value}")
                logger.info(f"  Priority: {classification['priority'].value}")
                logger.info(f"  Confidence: {classification['confidence']:.2f}")
                logger.info(f"  Reasoning: {classification['reasoning']}")
                logger.info(f"  Actions: {', '.join(classification['suggested_actions'])}")
                
                # Check if classification matches expectation
                if classification['classification'].value.upper() == sample['expected']:
                    logger.info("  ✓ Classification matches expectation!")
                else:
                    logger.info("  ⚠ Classification differs from expectation")
                    
            except Exception as e:
                logger.error(f"  ✗ Classification failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("\nCleaning up...")
        
        if self.monitoring_agent:
            await self.monitoring_agent.on_stop()
        
        if self.orchestration_agent:
            await self.orchestration_agent.cleanup()
        
        logger.info("Cleanup completed")
    
    async def run_demo(self):
        """Run the complete demo."""
        try:
            logger.info("🚀 Starting Communication System Demo")
            logger.info("="*60)
            
            await self.setup_environment()
            await self.initialize_agents()
            
            # Run demo sections
            await self.demo_monitoring_capabilities()
            await self.demo_email_orchestration()
            await self.demo_ai_classification()
            await self.demo_semantic_integration()
            
            logger.info("\n" + "="*60)
            logger.info("✅ Communication System Demo Completed Successfully!")
            logger.info("="*60)
            
            logger.info("\nNext Steps:")
            logger.info("1. Set up your Gmail API credentials")
            logger.info("2. Configure WhatsApp Business API (optional)")
            logger.info("3. Set up LinkedIn credentials (optional)")
            logger.info("4. Configure Redis for message bus")
            logger.info("5. Start the monitoring agent in production")
            logger.info("6. Integrate with semantic chat interface")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    demo = CommunicationSystemDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main()) 