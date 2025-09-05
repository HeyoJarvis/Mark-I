#!/usr/bin/env python3
"""
Start Communication Monitoring System

This script starts the always-on communication monitoring agent that:
- Monitors Gmail, WhatsApp, LinkedIn in the background
- Classifies messages with AI
- Publishes events to the message bus
- Responds to semantic agent commands

Usage:
    python start_communication_monitoring.py
"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from departments.communication.communication_monitoring_agent import CommunicationMonitoringAgent
from departments.communication.models.communication_models import MonitoringConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('communication_monitoring.log')
    ]
)
logger = logging.getLogger(__name__)


class CommunicationMonitoringSystem:
    """Production communication monitoring system."""
    
    def __init__(self):
        """Initialize the monitoring system."""
        self.monitoring_agent = None
        self.running = False
        
    async def start(self):
        """Start the monitoring system."""
        logger.info("🚀 Starting Jarvis Communication Monitoring System")
        logger.info("=" * 60)
        
        # Check prerequisites
        if not await self._check_prerequisites():
            logger.error("❌ Prerequisites not met. Please check your setup.")
            return False
        
        # Configure monitoring
        config = self._create_monitoring_config()
        logger.info("📋 Monitoring Configuration:")
        logger.info(f"  Gmail: {'✅' if config.gmail_enabled else '❌'}")
        logger.info(f"  WhatsApp: {'✅' if config.whatsapp_enabled else '❌'}")
        logger.info(f"  LinkedIn: {'✅' if config.linkedin_enabled else '❌'}")
        logger.info(f"  AI Classification: {'✅' if config.ai_classification_enabled else '❌'}")
        logger.info(f"  Monitoring Interval: {config.monitoring_interval_seconds}s")
        
        # Initialize monitoring agent
        self.monitoring_agent = CommunicationMonitoringAgent(config.model_dump())
        
        try:
            # Start the agent
            await self.monitoring_agent.on_start()
            self.running = True
            
            logger.info("✅ Communication Monitoring System started successfully!")
            logger.info("📡 System is now monitoring your communication channels...")
            logger.info("🤖 You can now use semantic commands to control the system")
            logger.info("")
            logger.info("Example commands you can use:")
            logger.info("  • 'Show me communication metrics'")
            logger.info("  • 'Send a follow-up sequence to john@example.com'")
            logger.info("  • 'Create a lead nurture campaign'")
            logger.info("  • 'What new messages do I have?'")
            logger.info("")
            logger.info("Press Ctrl+C to stop the monitoring system")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested by user")
        except Exception as e:
            logger.error(f"❌ Error in monitoring system: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the monitoring system."""
        logger.info("🔄 Stopping Communication Monitoring System...")
        self.running = False
        
        if self.monitoring_agent:
            await self.monitoring_agent.on_stop()
        
        logger.info("✅ Communication Monitoring System stopped")
    
    async def _check_prerequisites(self):
        """Check if all prerequisites are met."""
        logger.info("🔍 Checking prerequisites...")
        
        issues = []
        
        # Check Redis connection
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            r.ping()
            logger.info("✅ Redis connection: OK")
        except Exception as e:
            issues.append(f"Redis connection failed: {e}")
            logger.error(f"❌ Redis connection: {e}")
        
        # Check Gmail credentials
        gmail_creds = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')
        if os.path.exists(gmail_creds):
            logger.info("✅ Gmail credentials: Found")
        else:
            logger.warning("⚠️ Gmail credentials: Not found (Gmail monitoring disabled)")
        
        # Check Claude API key
        if os.getenv('ANTHROPIC_API_KEY'):
            logger.info("✅ Claude API key: Found")
        else:
            logger.warning("⚠️ Claude API key: Not found (AI classification disabled)")
        
        # Check WhatsApp credentials
        if os.getenv('WHATSAPP_ACCESS_TOKEN'):
            logger.info("✅ WhatsApp credentials: Found")
        else:
            logger.warning("⚠️ WhatsApp credentials: Not found (WhatsApp monitoring disabled)")
        
        if issues:
            logger.error("❌ Critical issues found:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("✅ Prerequisites check completed")
        return True
    
    def _create_monitoring_config(self):
        """Create monitoring configuration based on available credentials."""
        return MonitoringConfig(
            gmail_enabled=bool(os.getenv('GMAIL_CREDENTIALS_PATH') and 
                             os.path.exists(os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json'))),
            whatsapp_enabled=bool(os.getenv('WHATSAPP_ACCESS_TOKEN')),
            linkedin_enabled=bool(os.getenv('LINKEDIN_EMAIL')),
            monitoring_interval_seconds=int(os.getenv('MONITORING_INTERVAL', '30')),
            ai_classification_enabled=bool(os.getenv('ANTHROPIC_API_KEY')),
            auto_reply_enabled=os.getenv('AUTO_REPLY_ENABLED', 'false').lower() == 'true',
            
            # Gmail specific
            gmail_query_filter=os.getenv('GMAIL_QUERY_FILTER', 'is:unread'),
            gmail_max_results=int(os.getenv('GMAIL_MAX_RESULTS', '50')),
            
            # WhatsApp specific
            whatsapp_phone_number_id=os.getenv('WHATSAPP_PHONE_NUMBER_ID'),
            whatsapp_access_token=os.getenv('WHATSAPP_ACCESS_TOKEN')
        )


async def main():
    """Main entry point."""
    system = CommunicationMonitoringSystem()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"\n🛑 Received signal {signum}, initiating shutdown...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 