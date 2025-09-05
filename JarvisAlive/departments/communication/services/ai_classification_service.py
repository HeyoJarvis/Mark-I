"""
AI Classification Service

This service uses Claude AI to classify and analyze communication messages
from Gmail, WhatsApp, and LinkedIn channels.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

from ..models.communication_models import (
    CommunicationEvent, MessageClassification, MessagePriority,
    CommunicationChannel
)

logger = logging.getLogger(__name__)


class AIClassificationService:
    """AI-powered message classification and analysis service."""
    
    def __init__(self, anthropic_api_key: str = None):
        """Initialize AI classification service with Claude."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Claude AI engine using existing infrastructure
        config = AIEngineConfig(
            api_key=anthropic_api_key,
            model="claude-3-haiku-20240307",  # Fast and cost-effective model
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=500
        )
        
        self.ai_engine = AnthropicEngine(config)
        
    async def classify_message(self, event: CommunicationEvent) -> Dict[str, Any]:
        """Classify a communication message using AI."""
        try:
            # Create classification prompt
            prompt = self._create_classification_prompt(event)
            
            # Get AI classification
            response = await self.ai_engine.generate_response(prompt)
            
            # Parse AI response
            classification_result = self._parse_classification_response(response, event)
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Error classifying message: {e}")
            return {
                'classification': MessageClassification.UNCLASSIFIED,
                'priority': MessagePriority.MEDIUM,
                'confidence': 0.0,
                'reasoning': f"Classification failed: {str(e)}",
                'suggested_actions': []
            }
    
    def _create_classification_prompt(self, event: CommunicationEvent) -> str:
        """Create AI prompt for message classification."""
        
        # Channel-specific context
        channel_context = ""
        if event.channel == CommunicationChannel.GMAIL:
            channel_context = "This is an email message."
        elif event.channel == CommunicationChannel.WHATSAPP:
            channel_context = "This is a WhatsApp message."
        elif event.channel == CommunicationChannel.LINKEDIN:
            channel_context = "This is a LinkedIn message."
        
        # Extract metadata for context
        subject = event.metadata.get('subject', '') if event.metadata else ''
        
        prompt = f"""
You are an AI assistant that classifies business communication messages. Analyze the following message and provide a classification.

{channel_context}

Message Details:
- Sender: {event.sender}
- Content: {event.content}
- Subject: {subject}
- Channel: {event.channel.value}
- Timestamp: {event.timestamp}

Please classify this message into one of these categories:
1. INTERESTED_REPLY - Customer/prospect showing interest in products/services
2. NOT_INTERESTED - Clear rejection or lack of interest
3. MEETING_REQUEST - Request to schedule a meeting or call
4. QUESTION - General question that needs an answer
5. COMPLAINT - Customer complaint or issue
6. SPAM - Spam or irrelevant message
7. URGENT - Requires immediate attention
8. LEAD - Potential new business opportunity
9. CUSTOMER_SUPPORT - Existing customer needing support
10. UNCLASSIFIED - Doesn't fit other categories

Also determine the priority level:
- LOW: Informational, no immediate action needed
- MEDIUM: Normal business communication
- HIGH: Important but not urgent
- URGENT: Requires immediate attention

Provide your response in this exact format:
CLASSIFICATION: [category]
PRIORITY: [priority_level]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
SUGGESTED_ACTIONS: [comma-separated list of suggested actions]

Example response:
CLASSIFICATION: INTERESTED_REPLY
PRIORITY: HIGH
CONFIDENCE: 0.85
REASONING: Customer is asking for pricing information and showing purchase intent
SUGGESTED_ACTIONS: Send pricing information, Schedule follow-up call, Add to CRM
"""
        
        return prompt
    
    def _parse_classification_response(self, ai_response: str, event: CommunicationEvent) -> Dict[str, Any]:
        """Parse AI classification response."""
        try:
            lines = ai_response.strip().split('\n')
            
            classification = MessageClassification.UNCLASSIFIED
            priority = MessagePriority.MEDIUM
            confidence = 0.5
            reasoning = "AI classification completed"
            suggested_actions = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('CLASSIFICATION:'):
                    classification_str = line.split(':', 1)[1].strip()
                    try:
                        classification = MessageClassification(classification_str.lower())
                    except ValueError:
                        self.logger.warning(f"Unknown classification: {classification_str}")
                
                elif line.startswith('PRIORITY:'):
                    priority_str = line.split(':', 1)[1].strip()
                    try:
                        priority = MessagePriority(priority_str.lower())
                    except ValueError:
                        self.logger.warning(f"Unknown priority: {priority_str}")
                
                elif line.startswith('CONFIDENCE:'):
                    confidence_str = line.split(':', 1)[1].strip()
                    try:
                        confidence = float(confidence_str)
                    except ValueError:
                        self.logger.warning(f"Invalid confidence: {confidence_str}")
                
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                
                elif line.startswith('SUGGESTED_ACTIONS:'):
                    actions_str = line.split(':', 1)[1].strip()
                    suggested_actions = [action.strip() for action in actions_str.split(',') if action.strip()]
            
            return {
                'classification': classification,
                'priority': priority,
                'confidence': confidence,
                'reasoning': reasoning,
                'suggested_actions': suggested_actions,
                'classified_at': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing AI classification response: {e}")
            return {
                'classification': MessageClassification.UNCLASSIFIED,
                'priority': MessagePriority.MEDIUM,
                'confidence': 0.0,
                'reasoning': f"Failed to parse AI response: {str(e)}",
                'suggested_actions': []
            }
    
    async def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of message content."""
        try:
            prompt = f"""
Analyze the sentiment of this message content:

"{content}"

Provide sentiment analysis in this format:
SENTIMENT: [positive/negative/neutral]
SCORE: [0.0-1.0 where 1.0 is most positive]
EMOTIONS: [comma-separated list of detected emotions]
TONE: [professional/casual/aggressive/friendly/etc.]
"""
            
            response = await self.ai_engine.generate_response(prompt)
            
            # Parse sentiment response
            sentiment_data = self._parse_sentiment_response(response)
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'emotions': [],
                'tone': 'unknown'
            }
    
    def _parse_sentiment_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI sentiment analysis response."""
        try:
            lines = ai_response.strip().split('\n')
            
            sentiment = 'neutral'
            score = 0.5
            emotions = []
            tone = 'unknown'
            
            for line in lines:
                line = line.strip()
                if line.startswith('SENTIMENT:'):
                    sentiment = line.split(':', 1)[1].strip().lower()
                elif line.startswith('SCORE:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('EMOTIONS:'):
                    emotions_str = line.split(':', 1)[1].strip()
                    emotions = [emotion.strip() for emotion in emotions_str.split(',') if emotion.strip()]
                elif line.startswith('TONE:'):
                    tone = line.split(':', 1)[1].strip().lower()
            
            return {
                'sentiment': sentiment,
                'score': score,
                'emotions': emotions,
                'tone': tone
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing sentiment response: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'emotions': [],
                'tone': 'unknown'
            }
    
    async def extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract entities from message content."""
        try:
            prompt = f"""
Extract important entities from this message:

"{content}"

Identify and extract:
- PERSON_NAMES: Names of people mentioned
- COMPANIES: Company names mentioned
- PRODUCTS: Product or service names
- DATES: Dates mentioned
- PHONE_NUMBERS: Phone numbers
- EMAIL_ADDRESSES: Email addresses
- LOCATIONS: Cities, countries, addresses
- MONEY_AMOUNTS: Prices, costs, budgets mentioned

Format your response as:
PERSON_NAMES: [comma-separated list]
COMPANIES: [comma-separated list]
PRODUCTS: [comma-separated list]
DATES: [comma-separated list]
PHONE_NUMBERS: [comma-separated list]
EMAIL_ADDRESSES: [comma-separated list]
LOCATIONS: [comma-separated list]
MONEY_AMOUNTS: [comma-separated list]
"""
            
            response = await self.ai_engine.generate_response(prompt)
            
            # Parse entity response
            entities = self._parse_entity_response(response)
            return entities
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return {}
    
    def _parse_entity_response(self, ai_response: str) -> Dict[str, List[str]]:
        """Parse AI entity extraction response."""
        try:
            lines = ai_response.strip().split('\n')
            entities = {}
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    entity_type, entity_values = line.split(':', 1)
                    entity_type = entity_type.strip().lower()
                    entity_values = entity_values.strip()
                    
                    if entity_values and entity_values != '[]':
                        entities[entity_type] = [
                            value.strip() for value in entity_values.split(',') 
                            if value.strip()
                        ]
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error parsing entity response: {e}")
            return {}
    
    async def generate_auto_reply(self, event: CommunicationEvent, classification: Dict[str, Any]) -> Optional[str]:
        """Generate an automatic reply based on message classification."""
        try:
            # Only generate auto-replies for certain classifications
            auto_reply_classifications = [
                MessageClassification.QUESTION,
                MessageClassification.CUSTOMER_SUPPORT,
                MessageClassification.MEETING_REQUEST
            ]
            
            if classification['classification'] not in auto_reply_classifications:
                return None
            
            prompt = f"""
Generate a professional auto-reply for this {event.channel.value} message:

Original message: "{event.content}"
Classification: {classification['classification'].value}
Sender: {event.sender}

Generate a helpful, professional response that:
1. Acknowledges their message
2. Provides relevant information or next steps
3. Is appropriate for the {event.channel.value} channel
4. Maintains a professional but friendly tone

Keep the response concise and actionable.
"""
            
            response = await self.ai_engine.generate_response(prompt)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating auto-reply: {e}")
            return None
    
    async def personalize_message(self, template: str, contact_data: Dict[str, Any]) -> str:
        """Personalize a message template using AI."""
        try:
            prompt = f"""
Personalize this message template using the provided contact information:

Template:
{template}

Contact Information:
{contact_data}

Instructions:
1. Replace placeholder variables with actual data
2. Make the message feel personal and relevant
3. Maintain the original tone and structure
4. Ensure all personalizations are accurate and appropriate

Return only the personalized message, no additional text.
"""
            
            response = await self.ai_engine.generate_response(prompt)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error personalizing message: {e}")
            # Fallback to simple template substitution
            personalized = template
            for key, value in contact_data.items():
                personalized = personalized.replace(f"{{{key}}}", str(value))
            return personalized 