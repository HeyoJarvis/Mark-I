# 🚀 Communication System Usage Guide

## Two-Layer Operation

### **Layer 1: Always-On Monitoring (Background)**
Runs continuously, monitoring all your communication channels.

### **Layer 2: Semantic Control (Interactive)**
You control the system through natural language or direct commands.

## 🎯 **Quick Start**

### **Step 1: Start the Monitoring System**
```bash
# Terminal 1 - Start background monitoring
python start_communication_monitoring.py
```

This will:
- ✅ Monitor Gmail, WhatsApp, LinkedIn in real-time
- 🤖 Classify messages with AI
- 📡 Publish events to message bus
- 📊 Collect metrics continuously

### **Step 2: Control via Semantic Interface**
```bash
# Terminal 2 - Interactive control
python communication_control.py
```

Or run demos:
```bash
python communication_control.py --demo
```

## 🎮 **Interactive Commands**

Once the controller is running, you can use these commands:

### **System Status**
```
📝 Enter command: status
```
Shows monitoring system status, active services, and metrics.

### **Send Email Sequences**
```
📝 Enter command: sequence john@example.com John Doe
```
Starts an AI-personalized email nurture sequence.

### **Create Campaigns**
```
📝 Enter command: campaign Q4 Lead Generation
```
Creates a new multi-channel communication campaign.

### **Run All Demos**
```
📝 Enter command: demo
```
Demonstrates all system capabilities.

## 🤖 **Semantic Chat Integration**

The system integrates with your existing semantic chat interface. You can say:

### **Natural Language Commands**
- *"Show me my communication metrics for today"*
- *"Send a follow-up sequence to the leads from yesterday"*
- *"Create a nurture campaign for LinkedIn connections"*
- *"What new messages do I have?"*
- *"Personalize this email template for my contact list"*

### **AI-Powered Responses**
The system will:
1. **Parse** your natural language request
2. **Route** to the appropriate agent (monitoring or orchestration)
3. **Execute** the task with AI assistance
4. **Return** results in conversational format

## 📊 **What Happens Automatically**

### **Message Monitoring**
- 📧 **Gmail**: Checks every 30 seconds for new emails
- 📱 **WhatsApp**: Real-time webhook notifications
- 💼 **LinkedIn**: Periodic message checking

### **AI Classification**
Messages are automatically classified as:
- 🎯 **LEAD**: Potential new business
- ✅ **INTERESTED_REPLY**: Customer showing interest
- 📅 **MEETING_REQUEST**: Request to schedule meeting
- ❓ **QUESTION**: General questions
- 🚨 **URGENT**: Requires immediate attention
- 📞 **CUSTOMER_SUPPORT**: Existing customer support

### **Automated Actions**
Based on classification, the system can:
- 🔄 **Auto-reply** to common questions
- 📧 **Start email sequences** for new leads
- 📊 **Update metrics** and dashboards
- 🔔 **Send notifications** for urgent messages

## 🛠️ **Configuration Options**

### **Environment Variables**
```bash
# Monitoring settings
export MONITORING_INTERVAL=30              # Check interval in seconds
export AUTO_REPLY_ENABLED=false           # Enable auto-replies
export GMAIL_QUERY_FILTER="is:unread"     # Gmail search filter
export GMAIL_MAX_RESULTS=50               # Max emails per check

# AI settings
export ANTHROPIC_API_KEY=your_key         # Claude AI for classification
```

### **Real-time Configuration**
You can adjust settings through semantic commands:
- *"Change monitoring interval to 60 seconds"*
- *"Enable auto-replies for customer support messages"*
- *"Set Gmail filter to only check priority emails"*

## 📈 **Monitoring & Metrics**

### **Real-time Metrics**
- 📊 Total messages monitored
- 📧 Messages by channel (Gmail, WhatsApp, LinkedIn)
- 🏷️ Messages by classification
- 📤 Email sequences sent
- 📈 Reply rates and engagement

### **Access Metrics**
```bash
# Via command interface
📝 Enter command: status

# Via semantic chat
"Show me communication metrics"

# Via log files
tail -f communication_monitoring.log
```

## 🔄 **Typical Workflow**

### **Morning Routine**
1. **Start monitoring**: `python start_communication_monitoring.py`
2. **Check overnight messages**: `python communication_control.py` → `status`
3. **Review classifications**: Check for leads, urgent messages
4. **Start sequences**: Send follow-ups to interested prospects

### **During the Day**
- **System runs automatically** in background
- **Notifications** for urgent/important messages
- **Use semantic chat** for quick commands
- **Monitor metrics** through dashboard

### **End of Day**
- **Review metrics**: Total messages, classifications, sequences sent
- **Plan follow-ups**: Schedule campaigns for tomorrow
- **System keeps running** overnight (optional)

## 🚨 **Troubleshooting**

### **Monitoring System Issues**
```bash
# Check if Redis is running
redis-cli ping

# Check log files
tail -f communication_monitoring.log

# Restart monitoring system
# Ctrl+C to stop, then restart
python start_communication_monitoring.py
```

### **Controller Issues**
```bash
# Test orchestration agent
python communication_control.py --demo

# Check message bus connection
# Look for Redis connection errors in logs
```

### **Gmail Issues**
```bash
# Test Gmail connection
python setup_gmail.py

# Re-authenticate if needed
rm gmail_token.json
python setup_gmail.py
```

## 🔐 **Security Notes**

- **Credentials**: Keep `gmail_credentials.json` and `gmail_token.json` private
- **Auto-replies**: Test thoroughly before enabling in production
- **Rate limits**: System respects API rate limits automatically
- **Data privacy**: Messages processed locally when possible

## 🚀 **Advanced Usage**

### **Custom Email Sequences**
Create custom sequences by modifying the orchestration agent:
```python
# Add new sequence types
custom_sequence = EmailSequence(
    id="custom_follow_up",
    name="Custom Follow-up",
    messages=[...],
    delay_hours=[24, 72, 168]  # 1 day, 3 days, 1 week
)
```

### **Custom Classifications**
Add new message classifications:
```python
# Extend MessageClassification enum
class MessageClassification(str, Enum):
    # ... existing classifications
    PARTNERSHIP_INQUIRY = "partnership_inquiry"
    MEDIA_REQUEST = "media_request"
```

### **Webhook Integration**
Set up webhooks for real-time notifications:
```python
# WhatsApp webhook endpoint
@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    # Handle incoming WhatsApp messages
    pass
```

## 📚 **Integration Examples**

### **With CRM Systems**
```python
# Sync contacts with CRM
async def sync_with_crm(contact_data):
    # Update CRM with communication data
    pass
```

### **With Calendar Systems**
```python
# Schedule meetings from meeting requests
async def schedule_meeting(meeting_request):
    # Create calendar event
    pass
```

### **With Analytics Platforms**
```python
# Send metrics to analytics
async def update_analytics(metrics):
    # Push to analytics dashboard
    pass
```

---

**🎉 You now have a fully automated, AI-powered communication system that monitors all your channels and responds intelligently to every message!** 