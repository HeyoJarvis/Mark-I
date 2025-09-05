"""
LinkedIn Monitoring Service

This service handles LinkedIn message monitoring using webhook and web scraping approaches.
Note: LinkedIn's official API has limited messaging capabilities, so this uses alternative methods.
"""

import os
import logging
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..models.communication_models import (
    LinkedInMessage, CommunicationEvent, CommunicationChannel, 
    MessageType, MessageClassification
)

logger = logging.getLogger(__name__)


class LinkedInService:
    """LinkedIn monitoring service using webhook and web scraping approaches."""
    
    def __init__(self):
        """Initialize LinkedIn service."""
        self.webhook_verify_token = os.getenv('LINKEDIN_WEBHOOK_VERIFY_TOKEN')
        self.linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        
        # Web scraping configuration
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting for web scraping
        self.last_request_time = None
        self.min_request_interval = 3.0  # Minimum seconds between requests
        
        # Browser driver (will be initialized when needed)
        self.driver = None
        self.is_logged_in = False
        
    async def initialize(self) -> bool:
        """Initialize LinkedIn service."""
        try:
            # Check if we have credentials for either approach
            if self.linkedin_access_token:
                self.logger.info("LinkedIn service initialized with API token")
                return True
            elif self.linkedin_email and self.linkedin_password:
                self.logger.info("LinkedIn service initialized for web scraping")
                return True
            else:
                self.logger.error("LinkedIn credentials not properly configured")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LinkedIn service: {e}")
            return False
    
    def _setup_browser(self) -> bool:
        """Setup Selenium browser for web scraping."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser: {e}")
            return False
    
    async def _login_to_linkedin(self) -> bool:
        """Login to LinkedIn via web scraping."""
        if not self.driver:
            if not self._setup_browser():
                return False
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            
            # Enter email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.send_keys(self.linkedin_email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.linkedin_password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(3)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "messaging" in self.driver.current_url:
                self.is_logged_in = True
                self.logger.info("Successfully logged into LinkedIn")
                return True
            else:
                self.logger.error("LinkedIn login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error logging into LinkedIn: {e}")
            return False
    
    async def monitor_messages_via_scraping(self) -> List[LinkedInMessage]:
        """Monitor LinkedIn messages via web scraping."""
        if not self.is_logged_in:
            if not await self._login_to_linkedin():
                return []
        
        messages = []
        
        try:
            # Navigate to messaging page
            self.driver.get("https://www.linkedin.com/messaging/")
            
            # Wait for messages to load
            wait = WebDriverWait(self.driver, 10)
            await asyncio.sleep(2)
            
            # Find conversation list
            conversations = self.driver.find_elements(By.CSS_SELECTOR, "[data-view-name='conversation-list-item']")
            
            for conversation in conversations[:10]:  # Limit to first 10 conversations
                try:
                    # Click on conversation
                    conversation.click()
                    await asyncio.sleep(1)
                    
                    # Extract messages from this conversation
                    conversation_messages = await self._extract_conversation_messages()
                    messages.extend(conversation_messages)
                    
                    # Rate limiting
                    await asyncio.sleep(self.min_request_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error processing conversation: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(messages)} LinkedIn messages via scraping")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error monitoring LinkedIn messages: {e}")
            return messages
    
    async def _extract_conversation_messages(self) -> List[LinkedInMessage]:
        """Extract messages from current LinkedIn conversation."""
        messages = []
        
        try:
            # Wait for messages to load
            await asyncio.sleep(2)
            
            # Find message elements
            message_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-view-name='conversation-thread-item']")
            
            for msg_element in message_elements[-5:]:  # Get last 5 messages
                try:
                    # Extract message data
                    message_data = self._parse_message_element(msg_element)
                    if message_data:
                        messages.append(message_data)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing message element: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error extracting conversation messages: {e}")
            return messages
    
    def _parse_message_element(self, element) -> Optional[LinkedInMessage]:
        """Parse a LinkedIn message element."""
        try:
            # Extract message text
            message_text_element = element.find_element(By.CSS_SELECTOR, "[data-view-name='conversation-thread-item-text']")
            content = message_text_element.text if message_text_element else ""
            
            # Extract sender info
            sender_element = element.find_element(By.CSS_SELECTOR, "[data-view-name='conversation-thread-item-sender']")
            sender_name = sender_element.text if sender_element else "Unknown"
            
            # Extract timestamp (this is tricky with LinkedIn's dynamic content)
            timestamp = datetime.now(timezone.utc)  # Fallback to current time
            
            # Generate message ID (since we don't have access to real IDs)
            message_id = f"linkedin_{int(timestamp.timestamp())}_{hash(content)}"
            
            return LinkedInMessage(
                id=message_id,
                conversation_id=f"conv_{int(timestamp.timestamp())}",
                sender_profile_id="unknown",
                recipient_profile_id="me",
                content=content,
                timestamp=timestamp,
                sender_name=sender_name,
                sender_headline=None,
                is_connection_request=False
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing message element: {e}")
            return None
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> List[LinkedInMessage]:
        """Handle incoming LinkedIn webhook data (if available)."""
        messages = []
        
        try:
            # LinkedIn webhook structure (theoretical - LinkedIn doesn't provide messaging webhooks)
            if 'messages' in webhook_data:
                for msg_data in webhook_data['messages']:
                    linkedin_msg = self._parse_webhook_message(msg_data)
                    if linkedin_msg:
                        messages.append(linkedin_msg)
            
            self.logger.info(f"Processed {len(messages)} LinkedIn messages from webhook")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error handling LinkedIn webhook: {e}")
            return messages
    
    def _parse_webhook_message(self, message_data: Dict[str, Any]) -> Optional[LinkedInMessage]:
        """Parse LinkedIn message from webhook data."""
        try:
            return LinkedInMessage(
                id=message_data.get('id', ''),
                conversation_id=message_data.get('conversation_id', ''),
                sender_profile_id=message_data.get('sender_profile_id', ''),
                recipient_profile_id=message_data.get('recipient_profile_id', ''),
                content=message_data.get('content', ''),
                timestamp=datetime.fromisoformat(message_data.get('timestamp', datetime.now().isoformat())),
                sender_name=message_data.get('sender_name', ''),
                sender_headline=message_data.get('sender_headline'),
                is_connection_request=message_data.get('is_connection_request', False)
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing LinkedIn webhook message: {e}")
            return None
    
    async def send_message(self, recipient_profile_id: str, message: str) -> bool:
        """Send a LinkedIn message (limited functionality)."""
        try:
            if not self.is_logged_in:
                if not await self._login_to_linkedin():
                    return False
            
            # Navigate to the recipient's profile or messaging
            # This is complex and may not work reliably due to LinkedIn's anti-automation measures
            self.logger.warning("LinkedIn message sending via automation is not recommended and may violate ToS")
            
            # For now, return False to indicate this feature is not implemented
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending LinkedIn message: {e}")
            return False
    
    async def send_connection_request(self, profile_url: str, message: str = "") -> bool:
        """Send a LinkedIn connection request."""
        try:
            if not self.is_logged_in:
                if not await self._login_to_linkedin():
                    return False
            
            # Navigate to profile
            self.driver.get(profile_url)
            await asyncio.sleep(3)
            
            # Find and click connect button
            connect_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Connect')]")
            connect_button.click()
            
            # If there's a message field, add the message
            if message:
                try:
                    message_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "message"))
                    )
                    message_field.send_keys(message)
                except TimeoutException:
                    pass  # No message field available
            
            # Send the connection request
            send_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Send')]")
            send_button.click()
            
            self.logger.info(f"Connection request sent to {profile_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending connection request: {e}")
            return False
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify LinkedIn webhook during setup."""
        if mode == "subscribe" and token == self.webhook_verify_token:
            self.logger.info("LinkedIn webhook verified successfully")
            return challenge
        else:
            self.logger.error("LinkedIn webhook verification failed")
            return None
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                self.logger.info("LinkedIn browser driver closed")
            except Exception as e:
                self.logger.error(f"Error closing browser driver: {e}")
    
    def to_communication_event(self, linkedin_message: LinkedInMessage) -> CommunicationEvent:
        """Convert LinkedInMessage to CommunicationEvent."""
        return CommunicationEvent(
            id=linkedin_message.id,
            channel=CommunicationChannel.LINKEDIN,
            message_type=MessageType.RECEIVED,
            sender=linkedin_message.sender_name,
            recipient="me",
            content=linkedin_message.content,
            timestamp=linkedin_message.timestamp,
            thread_id=linkedin_message.conversation_id,
            metadata={
                'sender_profile_id': linkedin_message.sender_profile_id,
                'recipient_profile_id': linkedin_message.recipient_profile_id,
                'sender_headline': linkedin_message.sender_headline,
                'is_connection_request': linkedin_message.is_connection_request
            }
        )
    
    # Alternative approach: Manual webhook setup instructions
    def get_webhook_setup_instructions(self) -> Dict[str, Any]:
        """Get instructions for manually setting up LinkedIn monitoring."""
        return {
            'method': 'manual_webhook',
            'instructions': [
                '1. LinkedIn does not provide official messaging webhooks',
                '2. Alternative approaches:',
                '   a. Use LinkedIn Sales Navigator API (paid)',
                '   b. Manual webhook setup with browser extension',
                '   c. Email notifications forwarding',
                '   d. Third-party LinkedIn automation tools (use with caution)'
            ],
            'webhook_url': 'https://your-app.com/linkedin-webhook',
            'limitations': [
                'LinkedIn actively blocks automation',
                'Web scraping may violate Terms of Service',
                'Rate limiting is essential',
                'Consider using official LinkedIn APIs where available'
            ]
        } 