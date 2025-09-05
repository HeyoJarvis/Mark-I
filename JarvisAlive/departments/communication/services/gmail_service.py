"""
Gmail Monitoring Service

This service handles Gmail API integration for monitoring incoming emails,
parsing messages, and triggering communication events.
"""

import os
import logging
import asyncio
import base64
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..models.communication_models import (
    GmailMessage, CommunicationEvent, CommunicationChannel, 
    MessageType, MessageClassification
)

logger = logging.getLogger(__name__)


class GmailService:
    """Gmail API service for monitoring and sending emails."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_path: str = 'gmail_credentials.json', token_path: str = 'gmail_token.json'):
        """Initialize Gmail service with authentication."""
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.last_check_time = None
        self.logger = logging.getLogger(__name__)
        
        # SMTP configuration for sending emails
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_address = None
        
    async def initialize(self) -> bool:
        """Initialize Gmail API service with authentication."""
        try:
            self.service = await self._authenticate()
            if self.service:
                # Get user's email address
                profile = self.service.users().getProfile(userId='me').execute()
                self.email_address = profile.get('emailAddress')
                self.logger.info(f"Gmail service initialized for {self.email_address}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            return False
    
    async def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    self.logger.error(f"Gmail credentials file not found: {self.credentials_path}")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    async def monitor_emails(self, query: str = "is:unread", max_results: int = 50) -> List[GmailMessage]:
        """Monitor Gmail for new emails."""
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []
        
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            gmail_messages = []
            
            for msg in messages:
                try:
                    # Get full message details
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    gmail_msg = self._parse_gmail_message(message)
                    if gmail_msg:
                        gmail_messages.append(gmail_msg)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing message {msg['id']}: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(gmail_messages)} Gmail messages")
            return gmail_messages
            
        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error monitoring emails: {e}")
            return []
    
    def _parse_gmail_message(self, message: Dict[str, Any]) -> Optional[GmailMessage]:
        """Parse Gmail API message into GmailMessage model."""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            sender = self._get_header_value(headers, 'From')
            recipient = self._get_header_value(headers, 'To')
            subject = self._get_header_value(headers, 'Subject')
            date_str = self._get_header_value(headers, 'Date')
            
            # Parse timestamp
            timestamp = datetime.now(timezone.utc)
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    timestamp = parsedate_to_datetime(date_str)
                except Exception:
                    pass
            
            # Extract message content
            content = self._extract_message_content(message['payload'])
            
            # Extract labels
            labels = message.get('labelIds', [])
            
            # Check if unread
            is_unread = 'UNREAD' in labels
            
            return GmailMessage(
                id=message['id'],
                thread_id=message['threadId'],
                sender=sender or '',
                recipient=recipient or '',
                subject=subject or '',
                content=content,
                snippet=message.get('snippet', ''),
                timestamp=timestamp,
                labels=labels,
                is_unread=is_unread,
                message_type=MessageType.RECEIVED
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing Gmail message: {e}")
            return None
    
    def _get_header_value(self, headers: List[Dict], name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None
    
    def _extract_message_content(self, payload: Dict[str, Any]) -> str:
        """Extract text content from Gmail message payload."""
        content = ""
        
        try:
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            content = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                    elif part['mimeType'] == 'text/html' and not content:
                        data = part['body'].get('data')
                        if data:
                            content = base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                # Single part message
                if payload['mimeType'] in ['text/plain', 'text/html']:
                    data = payload['body'].get('data')
                    if data:
                        content = base64.urlsafe_b64decode(data).decode('utf-8')
        
        except Exception as e:
            self.logger.error(f"Error extracting message content: {e}")
        
        return content
    
    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email via Gmail API."""
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return False
        
        try:
            # Create message
            if is_html:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'html'))
            else:
                message = MIMEText(body)
            
            message['to'] = to_email
            message['subject'] = subject
            message['from'] = self.email_address
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send via Gmail API
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Email sent successfully to {to_email}, message ID: {send_message['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_email_sequence(self, to_email: str, messages: List[Dict[str, Any]], delay_hours: List[int]) -> Dict[str, Any]:
        """Send a sequence of emails with delays."""
        results = {
            'total_messages': len(messages),
            'sent_successfully': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, message_data in enumerate(messages):
            try:
                # Add delay between emails (except for the first one)
                if i > 0 and i < len(delay_hours):
                    delay_seconds = delay_hours[i-1] * 3600  # Convert hours to seconds
                    self.logger.info(f"Waiting {delay_hours[i-1]} hours before sending next email...")
                    await asyncio.sleep(delay_seconds)
                
                success = await self.send_email(
                    to_email=to_email,
                    subject=message_data.get('subject', ''),
                    body=message_data.get('body', ''),
                    is_html=message_data.get('is_html', False)
                )
                
                if success:
                    results['sent_successfully'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send message {i+1}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error sending message {i+1}: {str(e)}")
                self.logger.error(f"Error in email sequence: {e}")
        
        return results
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a Gmail message as read."""
        if not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            self.logger.error(f"Error marking message as read: {e}")
            return False
    
    async def get_thread_messages(self, thread_id: str) -> List[GmailMessage]:
        """Get all messages in a Gmail thread."""
        if not self.service:
            return []
        
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            for message in thread.get('messages', []):
                gmail_msg = self._parse_gmail_message(message)
                if gmail_msg:
                    messages.append(gmail_msg)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting thread messages: {e}")
            return []
    
    def to_communication_event(self, gmail_message: GmailMessage) -> CommunicationEvent:
        """Convert GmailMessage to CommunicationEvent."""
        return CommunicationEvent(
            id=gmail_message.id,
            channel=CommunicationChannel.GMAIL,
            message_type=gmail_message.message_type,
            sender=gmail_message.sender,
            recipient=gmail_message.recipient,
            content=gmail_message.content,
            timestamp=gmail_message.timestamp,
            thread_id=gmail_message.thread_id,
            metadata={
                'subject': gmail_message.subject,
                'snippet': gmail_message.snippet,
                'labels': gmail_message.labels,
                'is_unread': gmail_message.is_unread
            }
        ) 