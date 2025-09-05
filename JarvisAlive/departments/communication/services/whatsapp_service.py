"""
WhatsApp Business API Monitoring Service

This service handles WhatsApp Business API integration for monitoring incoming messages,
sending messages, and managing WhatsApp communication events.
"""

import os
import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from fastapi import Request

from ..models.communication_models import (
    WhatsAppMessage, CommunicationEvent, CommunicationChannel, 
    MessageType, MessageClassification
)

logger = logging.getLogger(__name__)


class WhatsAppService:
    """WhatsApp Business API service for monitoring and sending messages."""
    
    def __init__(self):
        """Initialize WhatsApp service with API credentials."""
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        
        # WhatsApp API endpoints
        self.base_url = "https://graph.facebook.com/v18.0"
        self.messages_url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
    async def initialize(self) -> bool:
        """Initialize WhatsApp service and verify credentials."""
        if not all([self.access_token, self.phone_number_id]):
            self.logger.error("WhatsApp credentials not properly configured")
            return False
        
        try:
            # Test API connection by getting phone number info
            response = await self._make_api_request(
                f"{self.base_url}/{self.phone_number_id}",
                method="GET"
            )
            
            if response and response.get('verified_name'):
                self.logger.info(f"WhatsApp service initialized for {response['verified_name']}")
                return True
            else:
                self.logger.error("Failed to verify WhatsApp phone number")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp service: {e}")
            return False
    
    async def _make_api_request(self, url: str, method: str = "POST", data: Dict = None) -> Optional[Dict]:
        """Make rate-limited API request to WhatsApp."""
        # Simple rate limiting
        if self.last_request_time:
            elapsed = datetime.now().timestamp() - self.last_request_time
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            self.last_request_time = datetime.now().timestamp()
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error making WhatsApp API request: {e}")
            return None
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> List[WhatsAppMessage]:
        """Handle incoming WhatsApp webhook data."""
        messages = []
        
        try:
            # Parse webhook structure
            if 'entry' not in webhook_data:
                return messages
            
            for entry in webhook_data['entry']:
                if 'changes' not in entry:
                    continue
                
                for change in entry['changes']:
                    if change.get('field') != 'messages':
                        continue
                    
                    value = change.get('value', {})
                    
                    # Process incoming messages
                    if 'messages' in value:
                        for msg in value['messages']:
                            whatsapp_msg = self._parse_whatsapp_message(msg, value)
                            if whatsapp_msg:
                                messages.append(whatsapp_msg)
                    
                    # Process message status updates
                    if 'statuses' in value:
                        await self._handle_message_status_updates(value['statuses'])
            
            self.logger.info(f"Processed {len(messages)} WhatsApp messages from webhook")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error handling WhatsApp webhook: {e}")
            return messages
    
    def _parse_whatsapp_message(self, message: Dict[str, Any], value: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """Parse WhatsApp message from webhook data."""
        try:
            # Extract basic message info
            msg_id = message.get('id')
            from_number = message.get('from')
            timestamp_str = message.get('timestamp')
            msg_type = message.get('type', 'text')
            
            # Parse timestamp
            timestamp = datetime.now(timezone.utc)
            if timestamp_str:
                timestamp = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
            
            # Extract message content based on type
            content = ""
            media_url = None
            media_type = None
            
            if msg_type == 'text':
                content = message.get('text', {}).get('body', '')
            elif msg_type == 'image':
                image_data = message.get('image', {})
                content = image_data.get('caption', '[Image]')
                media_url = image_data.get('id')  # Media ID for download
                media_type = 'image'
            elif msg_type == 'document':
                doc_data = message.get('document', {})
                content = f"[Document: {doc_data.get('filename', 'Unknown')}]"
                media_url = doc_data.get('id')
                media_type = 'document'
            elif msg_type == 'audio':
                content = '[Audio Message]'
                media_url = message.get('audio', {}).get('id')
                media_type = 'audio'
            elif msg_type == 'video':
                video_data = message.get('video', {})
                content = video_data.get('caption', '[Video]')
                media_url = video_data.get('id')
                media_type = 'video'
            
            # Get recipient (our phone number)
            to_number = value.get('metadata', {}).get('display_phone_number', self.phone_number_id)
            
            return WhatsAppMessage(
                id=msg_id,
                from_number=from_number,
                to_number=to_number,
                content=content,
                message_type=msg_type,
                timestamp=timestamp,
                status='received',
                media_url=media_url,
                media_type=media_type
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing WhatsApp message: {e}")
            return None
    
    async def _handle_message_status_updates(self, statuses: List[Dict[str, Any]]):
        """Handle WhatsApp message status updates (delivered, read, etc.)."""
        for status in statuses:
            try:
                message_id = status.get('id')
                status_type = status.get('status')  # sent, delivered, read, failed
                timestamp = status.get('timestamp')
                
                self.logger.debug(f"Message {message_id} status: {status_type}")
                
                # Here you could update message status in database
                # For now, just log the status update
                
            except Exception as e:
                self.logger.error(f"Error handling status update: {e}")
    
    async def send_message(self, to_number: str, message: str, message_type: str = "text") -> Optional[str]:
        """Send a WhatsApp message."""
        try:
            # Clean phone number (remove any formatting)
            to_number = ''.join(filter(str.isdigit, to_number))
            
            # Prepare message data
            message_data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": message_type
            }
            
            if message_type == "text":
                message_data["text"] = {"body": message}
            else:
                self.logger.error(f"Unsupported message type: {message_type}")
                return None
            
            # Send message via API
            response = await self._make_api_request(self.messages_url, "POST", message_data)
            
            if response and 'messages' in response:
                message_id = response['messages'][0]['id']
                self.logger.info(f"WhatsApp message sent successfully to {to_number}, ID: {message_id}")
                return message_id
            else:
                self.logger.error(f"Failed to send WhatsApp message to {to_number}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {e}")
            return None
    
    async def send_template_message(self, to_number: str, template_name: str, language_code: str = "en_US", 
                                  parameters: List[str] = None) -> Optional[str]:
        """Send a WhatsApp template message."""
        try:
            to_number = ''.join(filter(str.isdigit, to_number))
            
            message_data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code}
                }
            }
            
            # Add parameters if provided
            if parameters:
                message_data["template"]["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                }]
            
            response = await self._make_api_request(self.messages_url, "POST", message_data)
            
            if response and 'messages' in response:
                message_id = response['messages'][0]['id']
                self.logger.info(f"WhatsApp template message sent to {to_number}, ID: {message_id}")
                return message_id
            else:
                self.logger.error(f"Failed to send WhatsApp template message to {to_number}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp template message: {e}")
            return None
    
    async def send_message_sequence(self, to_number: str, messages: List[Dict[str, Any]], 
                                  delay_minutes: List[int]) -> Dict[str, Any]:
        """Send a sequence of WhatsApp messages with delays."""
        results = {
            'total_messages': len(messages),
            'sent_successfully': 0,
            'failed': 0,
            'message_ids': [],
            'errors': []
        }
        
        for i, message_data in enumerate(messages):
            try:
                # Add delay between messages (except for the first one)
                if i > 0 and i < len(delay_minutes):
                    delay_seconds = delay_minutes[i-1] * 60  # Convert minutes to seconds
                    self.logger.info(f"Waiting {delay_minutes[i-1]} minutes before sending next WhatsApp message...")
                    await asyncio.sleep(delay_seconds)
                
                message_id = await self.send_message(
                    to_number=to_number,
                    message=message_data.get('content', ''),
                    message_type=message_data.get('type', 'text')
                )
                
                if message_id:
                    results['sent_successfully'] += 1
                    results['message_ids'].append(message_id)
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send message {i+1}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error sending message {i+1}: {str(e)}")
                self.logger.error(f"Error in WhatsApp sequence: {e}")
        
        return results
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook during setup."""
        if mode == "subscribe" and token == self.webhook_verify_token:
            self.logger.info("WhatsApp webhook verified successfully")
            return challenge
        else:
            self.logger.error("WhatsApp webhook verification failed")
            return None
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp."""
        try:
            # First, get media URL
            media_url = f"{self.base_url}/{media_id}"
            response = await self._make_api_request(media_url, "GET")
            
            if not response or 'url' not in response:
                self.logger.error(f"Failed to get media URL for {media_id}")
                return None
            
            # Download the actual media file
            media_file_url = response['url']
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            media_response = requests.get(media_file_url, headers=headers)
            
            if media_response.status_code == 200:
                return media_response.content
            else:
                self.logger.error(f"Failed to download media: {media_response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading media: {e}")
            return None
    
    def to_communication_event(self, whatsapp_message: WhatsAppMessage) -> CommunicationEvent:
        """Convert WhatsAppMessage to CommunicationEvent."""
        return CommunicationEvent(
            id=whatsapp_message.id,
            channel=CommunicationChannel.WHATSAPP,
            message_type=MessageType.RECEIVED,
            sender=whatsapp_message.from_number,
            recipient=whatsapp_message.to_number,
            content=whatsapp_message.content,
            timestamp=whatsapp_message.timestamp,
            metadata={
                'message_type': whatsapp_message.message_type,
                'status': whatsapp_message.status,
                'media_url': whatsapp_message.media_url,
                'media_type': whatsapp_message.media_type
            }
        ) 