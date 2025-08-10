# Branding Agent Orchestration Integration

This module provides a complete orchestration layer integration for the BrandingAgent, enabling intent-driven routing, agent invocation, response handling, and feedback loops within the HeyJarvis AI platform.

## 🎯 Overview

The orchestration integration provides:

- **Intent-Driven Routing**: AI-powered semantic understanding of user requests
- **Agent Invocation**: Structured agent execution with input/output handling
- **Response Processing**: User-friendly formatting of agent outputs
- **Feedback Loops**: Support for thumbs up/down and revision requests
- **Logging & Traceability**: Comprehensive audit trails and metrics
- **Security & Isolation**: Task locking, session isolation, and rate limiting

## 🏗️ Architecture

### Core Components

```
orchestration/
├── intent_parser.py              # Intent parsing and routing
├── agent_integration.py          # Agent invocation and response handling
├── agent_communication.py        # Message bus and communication
├── branding_orchestration.py     # Main orchestration layer
├── branding_orchestration_config.py  # Configuration and documentation
├── state.py                      # State management
└── README.md                     # This documentation
```

### Integration Flow

1. **User Request** → Intent Parser
2. **Intent Classification** → Agent Registry
3. **Agent Invocation** → Agent Executor
4. **Response Processing** → Response Formatter
5. **User Feedback** → Feedback Handler
6. **Revision Loop** → Agent Re-invocation

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig

async def main():
    # Initialize orchestrator
    config = OrchestrationConfig(
        redis_url="redis://localhost:6379",
        anthropic_api_key="your-api-key-here"
    )
    
    orchestrator = BrandingOrchestrator(config)
    await orchestrator.initialize()
    
    # Process a branding request
    response = await orchestrator.process_request(
        "I need help coming up with a name for my eco-friendly pen business"
    )
    
    print(f"Brand: {response.get('brand_name')}")
    print(f"Colors: {response.get('color_palette')}")
    print(f"Domains: {response.get('domain_suggestions')}")
    
    await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example Output

```json
{
  "status": "success",
  "brand_name": "EcoWrite",
  "logo_prompt": "Design a modern, eco-friendly logo for EcoWrite...",
  "color_palette": ["#2E8B57", "#90EE90", "#228B22", "#32CD32"],
  "domain_suggestions": ["ecowrite.com", "ecowrite.co", "ecowrite.ai"],
  "execution_time_ms": 1250,
  "orchestration": {
    "intent_category": "branding",
    "confidence": "high",
    "session_id": "user_123"
  }
}
```

## 🎯 Intent-Driven Routing

### Intent Categories

The system supports routing to different agent categories:

- **branding**: Brand names, logos, visual identity
- **sales**: Lead generation, prospecting, outreach
- **marketing**: Campaigns, content, advertising
- **engineering**: Code, development, technical
- **customer_support**: Help, issue resolution
- **legal**: Contracts, compliance, documents
- **logistics**: Shipping, inventory, supply chain
- **finance**: Accounting, budgeting, reporting
- **operations**: Process optimization, workflow
- **general**: General assistance, unclear requests

### Intent Parsing

Uses a hybrid approach combining:

1. **Rule-based Pattern Matching**: Fast, reliable for common intents
2. **AI-powered Semantic Understanding**: Handles complex, ambiguous requests
3. **Confidence Scoring**: Determines routing confidence
4. **Fallback Mechanisms**: Graceful degradation when parsing fails

### Example Intent Parsing

```python
# Rule-based patterns
"I need a brand name" → branding (high confidence)
"Design a logo" → branding (high confidence)
"Find leads" → sales (high confidence)

# AI-powered understanding
"I want to create a visual identity for my startup" → branding (high confidence)
"Help me come up with a memorable name" → branding (medium confidence)
```

## 🤖 Agent Integration

### Agent Registry

Centralized agent management with metadata:

```python
# Register agents
registry = AgentRegistry()
registry.register_agent(
    agent_id="branding_agent",
    agent_class=BrandingAgent,
    metadata={
        "name": "Branding Agent",
        "description": "Generates brand names, logos, and visual identity",
        "capabilities": ["brand_name_generation", "logo_prompt_creation"],
        "category": IntentCategory.BRANDING
    }
)
```

### Agent Invocation

Structured agent execution with:

- **Input State**: Structured data for agent processing
- **Context**: Additional metadata and session information
- **Priority**: Execution priority levels
- **Timeout**: Configurable execution timeouts
- **Error Handling**: Graceful failure handling

### Response Processing

User-friendly response formatting:

```python
# Format branding response
{
    "status": "success",
    "brand_name": "EcoWrite",
    "logo_prompt": "Design a modern, eco-friendly logo...",
    "color_palette": ["#2E8B57", "#90EE90"],
    "domain_suggestions": ["ecowrite.com", "ecowrite.co"],
    "execution_time_ms": 1250,
    "invocation_id": "inv_123"
}
```

## 🔄 Feedback Loops

### Feedback Types

- **thumbs_up**: Positive feedback
- **thumbs_down**: Negative feedback
- **revision_request**: Request for revision
- **clarification**: Request for clarification

### Feedback Processing

```python
# Submit feedback
feedback_result = await orchestrator.submit_feedback(
    invocation_id="inv_123",
    feedback_type="revision_request",
    feedback_text="Make the brand name more modern",
    rating=3
)

# Feedback triggers revision
if feedback_type == "revision_request":
    # Re-invoke agent with feedback context
    await agent_executor.invoke_agent(
        agent_id="branding_agent",
        input_state=original_input,
        context={"feedback": feedback_text}
    )
```

## 📊 Logging & Traceability

### Audit Logging

Comprehensive logging of all operations:

```python
# Log entry structure
{
    "request_id": "req_123",
    "session_id": "user_123",
    "user_request": "I need a brand name...",
    "context": {"industry": "tech"},
    "timestamp": "2025-08-05T21:14:12.764317",
    "intent_category": "branding",
    "confidence": "high",
    "execution_time_ms": 1250,
    "status": "success"
}
```

### Metrics Collection

Performance metrics tracking:

- Total requests processed
- Success/failure rates
- Average response times
- Intent parsing accuracy
- Agent success rates

### Health Monitoring

Component health checks:

```python
health = await orchestrator.health_check()
# Returns:
{
    "status": "healthy",
    "components": {
        "redis": "healthy",
        "intent_parser": "healthy",
        "agent_executor": "healthy"
    },
    "timestamp": "2025-08-05T21:14:12.764317"
}
```

## 🛡️ Security & Isolation

### Security Features

1. **Task Locking**: Prevents concurrent execution conflicts
2. **Session Isolation**: Separates user sessions and data
3. **Rate Limiting**: Limits request frequency per user
4. **Audit Logging**: Comprehensive operation logging
5. **Error Isolation**: Contains errors to prevent system failures

### Isolation Patterns

1. **Agent Registry**: Centralized agent management
2. **Message Bus**: Asynchronous agent communication
3. **Response Caching**: Prevents redundant execution
4. **Feedback Loops**: Structured feedback processing

### Configuration

```python
security_config = {
    "enable_task_locking": True,
    "max_concurrent_requests": 10,
    "request_timeout_seconds": 30,
    "enable_rate_limiting": True,
    "session_ttl_hours": 1,
    "audit_log_retention_hours": 24
}
```

## 🔌 API Integration

### REST API Examples

```python
# Process request
POST /orchestration/process
{
    "user_request": "I want to start a premium coffee brand",
    "session_id": "user_123",
    "context": {
        "industry": "food_and_beverage",
        "target_audience": "coffee_enthusiasts"
    }
}

# Submit feedback
POST /orchestration/feedback
{
    "invocation_id": "inv_123",
    "feedback_type": "revision_request",
    "feedback_text": "Make the brand name more unique",
    "rating": 3
}

# Get status
GET /orchestration/status/{invocation_id}
```

### WebSocket Integration

Real-time communication for long-running tasks:

```python
# WebSocket message format
{
    "type": "status_update",
    "invocation_id": "inv_123",
    "status": "running",
    "progress": 75,
    "message": "Generating brand suggestions..."
}
```

## 📋 Configuration

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key-here"
export REDIS_URL="redis://localhost:6379"

# Optional
export LOG_LEVEL="INFO"
export MAX_CONCURRENT_REQUESTS="10"
export REQUEST_TIMEOUT_SECONDS="30"
```

### Configuration Files

```python
# Development configuration
from orchestration.branding_orchestration_config import DEVELOPMENT_CONFIG

# Production configuration
from orchestration.branding_orchestration_config import PRODUCTION_CONFIG

# Custom configuration
config = BrandingAgentConfig(
    orchestration=OrchestrationConfig(
        redis_url="redis://redis:6379",
        max_concurrent_invocations=50,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    ),
    agent_settings={
        "max_domain_suggestions": 10,
        "color_palette_size": 5
    },
    security={
        "enable_task_locking": True,
        "max_concurrent_requests": 100
    }
)
```

## 🧪 Testing

### Unit Tests

```bash
# Run orchestration tests
python -m pytest tests/test_orchestration.py -v

# Run specific component tests
python -m pytest tests/test_intent_parser.py -v
python -m pytest tests/test_agent_integration.py -v
```

### Integration Tests

```bash
# Run integration demo
python demo_orchestration_integration.py

# Test with Redis
redis-server &
python demo_orchestration_integration.py
```

### Performance Testing

```python
# Load testing
async def load_test():
    tasks = []
    for i in range(100):
        task = orchestrator.process_request(f"Brand request {i}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

## 🔧 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Start Redis
   redis-server
   
   # Check connection
   redis-cli ping
   ```

2. **AI Parsing Not Working**
   ```bash
   # Set API key
   export ANTHROPIC_API_KEY="your-key"
   
   # Check environment
   echo $ANTHROPIC_API_KEY
   ```

3. **Agent Not Found**
   ```python
   # Check agent registry
   agents = orchestrator.agent_executor.agent_registry.list_agents()
   print(agents)
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug configuration
config = OrchestrationConfig(
    enable_logging=True,
    enable_metrics=True
)
```

## 📚 Documentation

### Additional Resources

- [BrandingAgent Documentation](../departments/branding/README.md)
- [Intent Parser Examples](branding_orchestration_config.py)
- [API Reference](demo_orchestration_integration.py)
- [Configuration Guide](branding_orchestration_config.py)

### Contributing

To extend the orchestration layer:

1. **Add New Agents**: Register in `AgentRegistry`
2. **Extend Intent Parsing**: Add patterns to `IntentParser`
3. **Custom Response Formatting**: Extend `ResponseFormatter`
4. **Add Security Features**: Implement in `BrandingOrchestrator`

## 🎉 Success Metrics

The orchestration integration successfully provides:

✅ **Scalability & Modularity**: Plug-and-play agent integration  
✅ **Intent-Driven Communication**: AI-powered semantic routing  
✅ **Agent Invocation & Response Handling**: Structured execution  
✅ **Feedback Loops**: Revision and improvement support  
✅ **Logging & Traceability**: Comprehensive audit trails  
✅ **Security & Isolation**: Task locking and session isolation  
✅ **Prompt Robustness**: Structured schemas and validation  

The integration is production-ready and can be immediately deployed for automated business branding generation within the HeyJarvis platform. 