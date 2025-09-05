# 📧 Communication System - Two-Layer Architecture

A sophisticated two-layer communication monitoring and orchestration system that integrates Gmail, WhatsApp, and LinkedIn with AI-powered message classification and automated responses.

## 🏗️ Architecture Overview

### Layer 1: Communication Monitoring Agent (Always-On)
- **Purpose**: Persistent background monitoring of communication channels
- **Channels**: Gmail, WhatsApp, LinkedIn
- **Features**: 
  - Real-time message monitoring
  - AI-powered message classification using Claude
  - Event publishing to message bus
  - Metrics collection and reporting

### Layer 2: Email Orchestration Agent (On-Demand)
- **Purpose**: Campaign management and email automation
- **Features**:
  - Email sequence automation
  - AI-powered personalization
  - Campaign management
  - Reply handling and follow-ups
  - Integration with monitoring layer events

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Redis** (for message bus)
3. **API Credentials**:
   - Anthropic API key (for Claude AI)
   - Gmail API credentials
   - WhatsApp Business API token (optional)
   - LinkedIn credentials (optional)

### Installation

```bash
# Install dependencies
pip install -r requirements_communication.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
GMAIL_CREDENTIALS_PATH=path/to/gmail_credentials.json
REDIS_URL=redis://localhost:6379

# Optional - WhatsApp
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# Optional - LinkedIn (use with caution)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create credentials (OAuth 2.0)
5. Download credentials JSON file
6. Set `GMAIL_CREDENTIALS_PATH` to the file path

### WhatsApp Business API Setup

1. Sign up for [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
2. Get your access token and phone number ID
3. Set up webhook URL for receiving messages
4. Configure environment variables

## 🎯 Usage Examples

### Running the Demo

```bash
python test_communication_system.py
```

### Starting the Monitoring Agent

```python
import asyncio
from departments.communication import CommunicationMonitoringAgent
from departments.communication.models.communication_models import MonitoringConfig

async def start_monitoring():
    config = MonitoringConfig(
        gmail_enabled=True,
        whatsapp_enabled=True,
        linkedin_enabled=False,  # Disabled by default
        monitoring_interval_seconds=30,
        ai_classification_enabled=True
    )
    
    agent = CommunicationMonitoringAgent(config.dict())
    await agent.on_start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.on_stop()

asyncio.run(start_monitoring())
```

### Using the Email Orchestration Agent

```python
import asyncio
from departments.communication import EmailOrchestrationAgent

async def send_email_sequence():
    agent = EmailOrchestrationAgent()
    await agent.initialize()
    
    # Send a lead nurture sequence
    result = await agent.run({
        'task_type': 'send_email_sequence',
        'contact_data': {
            'id': 'contact_1',
            'name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Example Corp'
        },
        'sequence_name': 'lead_nurture'
    })
    
    print(f"Sequence result: {result}")
    await agent.cleanup()

asyncio.run(send_email_sequence())
```

### Semantic Chat Integration

The system integrates with the semantic chat interface. Users can interact using natural language:

```
User: "Monitor my Gmail for new leads and send them a welcome sequence"
System: "I'll start monitoring your Gmail for potential leads and automatically send them our lead nurture sequence when detected."

User: "Show me communication metrics for this week"
System: "Here are your communication metrics: 45 emails monitored, 12 classified as leads, 8 sequences sent..."

User: "Personalize this email template for my contact list"
System: "I'll personalize that template using AI for each contact in your list."
```

## 📊 Features

### AI-Powered Classification

Messages are automatically classified into categories:
- **INTERESTED_REPLY**: Customer showing interest
- **NOT_INTERESTED**: Clear rejection
- **MEETING_REQUEST**: Request to schedule meeting
- **QUESTION**: General questions
- **COMPLAINT**: Customer complaints
- **SPAM**: Spam messages
- **URGENT**: Requires immediate attention
- **LEAD**: Potential new business
- **CUSTOMER_SUPPORT**: Existing customer support

### Email Sequences

Pre-built sequences include:
- **Lead Nurture**: 3-email sequence for new leads
- **Meeting Follow-up**: Post-meeting engagement
- **Customer Onboarding**: Welcome new customers
- **Re-engagement**: Win back inactive contacts

### Multi-Channel Support

| Channel | Monitoring | Sending | Status |
|---------|------------|---------|--------|
| Gmail | ✅ | ✅ | Production Ready |
| WhatsApp | ✅ | ✅ | Production Ready |
| LinkedIn | ⚠️ | ⚠️ | Use with Caution* |

*LinkedIn monitoring uses web scraping which may violate ToS

## 🔧 Configuration

### Monitoring Configuration

```python
from departments.communication.models.communication_models import MonitoringConfig

config = MonitoringConfig(
    gmail_enabled=True,
    whatsapp_enabled=True,
    linkedin_enabled=False,
    monitoring_interval_seconds=30,
    ai_classification_enabled=True,
    auto_reply_enabled=False,  # Set to True for auto-replies
    
    # Gmail specific
    gmail_query_filter="is:unread",
    gmail_max_results=50,
    
    # WhatsApp specific
    whatsapp_phone_number_id="your_phone_id",
    whatsapp_access_token="your_token"
)
```

### Custom Email Sequences

```python
from departments.communication.models.communication_models import EmailSequence

custom_sequence = EmailSequence(
    id="custom_sequence",
    name="Custom Follow-up",
    description="Custom email sequence",
    messages=[
        {
            "subject": "Thanks for your interest, {name}!",
            "body": "Hi {name}, thank you for reaching out...",
            "is_html": False
        }
    ],
    delay_hours=[24, 72],  # Send after 1 day, then 3 days
    target_audience="prospects"
)
```

## 🔒 Security & Privacy

### Data Protection
- All sensitive data encrypted at rest
- API keys stored securely in environment variables
- Message content processed locally when possible
- Optional data retention policies

### Rate Limiting
- Built-in rate limiting for all APIs
- Respects platform rate limits
- Configurable request intervals

### Compliance
- GDPR compliant data handling
- CAN-SPAM compliant email sending
- WhatsApp Business API compliance
- LinkedIn ToS considerations

## 📈 Monitoring & Metrics

### Available Metrics
- Total messages monitored
- Messages by channel (Gmail, WhatsApp, LinkedIn)
- Messages by classification
- Email sequences sent
- Reply rates
- Campaign performance

### Accessing Metrics

```python
# Get real-time metrics
metrics = await monitoring_agent.get_metrics()
print(f"Total messages: {metrics.total_messages_monitored}")
print(f"By channel: {metrics.messages_by_channel}")
```

## 🧪 Testing

### Run All Tests
```bash
python test_communication_system.py
```

### Test Individual Components
```bash
# Test Gmail service
python -m pytest tests/test_gmail_service.py

# Test AI classification
python -m pytest tests/test_ai_classification.py

# Test email orchestration
python -m pytest tests/test_email_orchestration.py
```

## 🚨 Troubleshooting

### Common Issues

**Gmail API Authentication**
```bash
# Delete existing token and re-authenticate
rm gmail_token.json
python test_communication_system.py
```

**WhatsApp Webhook Issues**
- Verify webhook URL is accessible
- Check webhook verify token matches
- Ensure HTTPS for production

**LinkedIn Rate Limiting**
- Increase delays between requests
- Use residential proxies if needed
- Consider official LinkedIn APIs

**Redis Connection**
```bash
# Check Redis is running
redis-cli ping
# Should return PONG
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed logs for troubleshooting
```

## 🔄 Integration with Existing System

The communication system integrates seamlessly with the existing Jarvis architecture:

### Semantic Orchestration
- Registered in `CapabilityAgentRegistry`
- Supports natural language requests
- Automatic agent routing

### Message Bus Integration
- Publishes events to Redis message bus
- Subscribes to relevant system events
- Event-driven architecture

### Persistent Agent Pool
- Monitoring agent runs in persistent pool
- Automatic restart on failure
- Health monitoring and alerts

## 📚 API Reference

### CommunicationMonitoringAgent

```python
class CommunicationMonitoringAgent(PersistentAgent):
    async def on_start() -> None
    async def process_task(task: TaskRequest) -> TaskResponse
    async def handle_whatsapp_webhook(webhook_data: Dict) -> Dict
    async def on_stop() -> None
```

### EmailOrchestrationAgent

```python
class EmailOrchestrationAgent:
    async def initialize() -> bool
    async def run(state: dict) -> dict
    async def cleanup() -> None
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is part of the Jarvis AI system and follows the same licensing terms.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the test examples

---

**Built with ❤️ using Claude AI, Gmail API, WhatsApp Business API, and modern Python async patterns.** 