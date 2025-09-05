#!/usr/bin/env python3
"""
Communication Control Interface

This script demonstrates how to interact with the communication monitoring system
through semantic commands and direct agent calls.

Usage:
    python communication_control.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from departments.communication.email_orchestration_agent import EmailOrchestrationAgent
from orchestration.persistent.message_bus import MessageBus, MessageType
from orchestration.persistent.base_agent import TaskRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommunicationController:
    """Interface for controlling the communication system."""
    
    def __init__(self):
        """Initialize the controller."""
        self.message_bus = None
        self.orchestration_agent = None
        
    async def initialize(self):
        """Initialize the controller."""
        logger.info("🔧 Initializing Communication Controller...")
        
        # Initialize message bus
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.message_bus = MessageBus(redis_url)
        await self.message_bus.connect()
        
        # Initialize orchestration agent
        self.orchestration_agent = EmailOrchestrationAgent()
        await self.orchestration_agent.initialize()
        
        logger.info("✅ Communication Controller initialized")
    
    async def get_monitoring_status(self):
        """Get status from the monitoring agent."""
        logger.info("📊 Getting monitoring system status...")
        
        # Try to get real status from monitoring agent via message bus
        try:
            # Check if monitoring agent is actually running
            # This would normally query the actual monitoring agent
            logger.info("🔍 Checking for active monitoring agent...")
            
            # For now, show real service availability but zero metrics until monitoring starts
            status = {
                'agent_id': 'communication_monitoring_agent',
                'running': False,  # Will be True only if monitoring agent is actually running
                'services': {
                    'gmail': bool(os.getenv('GMAIL_CREDENTIALS_PATH') and 
                                os.path.exists(os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json'))),
                    'whatsapp': bool(os.getenv('WHATSAPP_ACCESS_TOKEN')),
                    'linkedin': bool(os.getenv('LINKEDIN_EMAIL')),
                    'ai_classification': bool(os.getenv('ANTHROPIC_API_KEY'))
                },
                'metrics': {
                    'total_messages_monitored': 0,  # Real data starts at 0
                    'messages_by_channel': {},      # Empty until monitoring starts
                    'messages_by_classification': {}  # Empty until monitoring starts
                }
            }
            
            logger.info("ℹ️  Note: Metrics will be populated once monitoring agent is started")
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            status = {
                'agent_id': 'communication_monitoring_agent',
                'running': False,
                'error': str(e)
            }
        
        logger.info("📈 Monitoring Status:")
        logger.info(f"  Running: {'✅' if status['running'] else '❌'}")
        logger.info("  Services:")
        for service, enabled in status['services'].items():
            logger.info(f"    {service}: {'✅' if enabled else '❌'}")
        logger.info("  Metrics:")
        logger.info(f"    Total messages: {status['metrics']['total_messages_monitored']}")
        logger.info(f"    By channel: {status['metrics']['messages_by_channel']}")
        logger.info(f"    By classification: {status['metrics']['messages_by_classification']}")
        
        return status
    
    async def send_email_sequence(self, contact_email: str, contact_name: str, sequence_type: str = "lead_nurture"):
        """Send an email sequence to a contact."""
        logger.info(f"📧 Sending {sequence_type} sequence to {contact_name} ({contact_email})")
        
        # Prepare contact data
        contact_data = {
            'id': f'contact_{hash(contact_email)}',
            'name': contact_name,
            'email': contact_email,
            'company': 'Unknown Company',
            'title': 'Unknown Title'
        }
        
        # Send sequence via orchestration agent
        result = await self.orchestration_agent.run({
            'task_type': 'send_email_sequence',
            'contact_data': contact_data,
            'sequence_name': sequence_type
        })
        
        if result['success']:
            logger.info(f"✅ Email sequence started successfully!")
            logger.info(f"   Contact: {result.get('contact_id', 'N/A')}")
            logger.info(f"   Sequence: {result.get('sequence', 'N/A')}")
        else:
            logger.error(f"❌ Failed to start email sequence: {result.get('error', 'Unknown error')}")
        
        return result
    
    async def create_campaign(self, campaign_name: str, target_contacts: list):
        """Create a new communication campaign."""
        logger.info(f"🎯 Creating campaign: {campaign_name}")
        
        campaign_data = {
            'name': campaign_name,
            'description': f'Campaign created via communication controller',
            'target_contacts': target_contacts
        }
        
        result = await self.orchestration_agent.run({
            'task_type': 'create_campaign',
            'campaign_data': campaign_data
        })
        
        if result['success']:
            logger.info(f"✅ Campaign created successfully!")
            logger.info(f"   Campaign ID: {result.get('campaign_id', 'N/A')}")
            logger.info(f"   Message: {result.get('message', 'N/A')}")
        else:
            logger.error(f"❌ Failed to create campaign: {result.get('error', 'Unknown error')}")
        
        return result
    
    async def personalize_email(self, template: str, contact_data: dict):
        """Personalize an email template."""
        logger.info("✨ Personalizing email template...")
        
        result = await self.orchestration_agent.run({
            'task_type': 'personalize_email',
            'template': template,
            'contact_data': contact_data
        })
        
        if result['success']:
            logger.info("✅ Email personalized successfully!")
            logger.info(f"Original: {template}")
            logger.info(f"Personalized: {result.get('personalized_message', 'N/A')}")
        else:
            logger.error(f"❌ Failed to personalize email: {result.get('error', 'Unknown error')}")
        
        return result
    
    async def demo_semantic_commands(self):
        """Demonstrate semantic command capabilities."""
        logger.info("\n🤖 Semantic Command Demonstrations")
        logger.info("=" * 50)
        
        # Demo 1: Get system status
        logger.info("\n1️⃣ Command: 'Show me communication metrics'")
        await self.get_monitoring_status()
        
        # Demo 2: Send email sequence
        logger.info("\n2️⃣ Command: 'Send a follow-up sequence to john@example.com'")
        await self.send_email_sequence(
            contact_email="john@example.com",
            contact_name="John Doe",
            sequence_type="lead_nurture"
        )
        
        # Demo 3: Create campaign
        logger.info("\n3️⃣ Command: 'Create a lead nurture campaign for my prospects'")
        await self.create_campaign(
            campaign_name="Q4 Lead Nurture Campaign",
            target_contacts=["john@example.com", "jane@example.com"]
        )
        
        # Demo 4: Personalize email
        logger.info("\n4️⃣ Command: 'Personalize this email for John at TechCorp'")
        await self.personalize_email(
            template="Hi {name}, I hope you're doing well at {company}. I wanted to follow up on our conversation about {topic}.",
            contact_data={
                'name': 'John',
                'company': 'TechCorp',
                'topic': 'automation solutions'
            }
        )
    
    async def interactive_mode(self):
        """Run interactive command mode."""
        logger.info("\n🎮 Interactive Communication Control")
        logger.info("=" * 40)
        logger.info("Available commands:")
        logger.info("  1. status - Get monitoring system status")
        logger.info("  2. sequence <email> <name> - Send email sequence")
        logger.info("  3. campaign <name> - Create campaign")
        logger.info("  4. demo - Run all demos")
        logger.info("  5. quit - Exit")
        logger.info("")
        
        while True:
            try:
                command = input("📝 Enter command: ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'status':
                    await self.get_monitoring_status()
                elif command.startswith('sequence'):
                    parts = command.split()
                    if len(parts) >= 3:
                        email = parts[1]
                        name = ' '.join(parts[2:])
                        await self.send_email_sequence(email, name)
                    else:
                        logger.info("Usage: sequence <email> <name>")
                elif command.startswith('campaign'):
                    parts = command.split()
                    if len(parts) >= 2:
                        name = ' '.join(parts[1:])
                        await self.create_campaign(name, ["demo@example.com"])
                    else:
                        logger.info("Usage: campaign <name>")
                elif command == 'demo':
                    await self.demo_semantic_commands()
                else:
                    logger.info("Unknown command. Type 'quit' to exit.")
                    
                logger.info("")  # Add spacing
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
        
        logger.info("👋 Goodbye!")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.orchestration_agent:
            await self.orchestration_agent.cleanup()
        if self.message_bus:
            await self.message_bus.disconnect()


async def main():
    """Main entry point."""
    controller = CommunicationController()
    
    try:
        await controller.initialize()
        
        # Check if monitoring system is running
        logger.info("🔍 Checking if monitoring system is running...")
        logger.info("ℹ️  Make sure to start the monitoring system first:")
        logger.info("   python start_communication_monitoring.py")
        logger.info("")
        
        # Run demo or interactive mode
        if len(sys.argv) > 1 and sys.argv[1] == '--demo':
            await controller.demo_semantic_commands()
        else:
            await controller.interactive_mode()
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await controller.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 