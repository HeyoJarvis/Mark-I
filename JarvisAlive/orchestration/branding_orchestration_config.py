"""
Configuration and Documentation for Branding Agent Orchestration Integration

This module provides configuration examples and documentation for integrating
the BrandingAgent into the HeyJarvis orchestration layer.
"""

import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from .branding_orchestration import OrchestrationConfig, BrandingOrchestrator
from .intent_parser import IntentCategory


class BrandingAgentConfig(BaseModel):
    """Configuration for BrandingAgent integration."""
    
    # Core orchestration settings
    orchestration: OrchestrationConfig = Field(
        default=OrchestrationConfig(),
        description="Orchestration layer configuration"
    )
    
    # Agent-specific settings
    agent_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_domain_suggestions": 5,
            "color_palette_size": 4,
            "enable_fallback_mode": True,
            "ai_model": "claude-3-sonnet-20240229",
            "temperature": 0.8
        },
        description="BrandingAgent-specific configuration"
    )
    
    # Intent parsing settings
    intent_parsing: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enable_ai_parsing": True,
            "confidence_threshold": 0.3,
            "enable_clarification": True,
            "max_alternate_intents": 3
        },
        description="Intent parsing configuration"
    )
    
    # Logging and monitoring
    logging: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "enable_audit_logs": True,
            "enable_performance_logs": True,
            "log_retention_hours": 24
        },
        description="Logging configuration"
    )
    
    # Security settings
    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enable_task_locking": True,
            "max_concurrent_requests": 10,
            "request_timeout_seconds": 300,  # CRITICAL FIX: 5 minutes for regeneration calls
            "enable_rate_limiting": True
        },
        description="Security and isolation settings"
    )


# Configuration examples
DEFAULT_CONFIG = BrandingAgentConfig()

PRODUCTION_CONFIG = BrandingAgentConfig(
    orchestration=OrchestrationConfig(
        redis_url="redis://redis:6379",
        max_concurrent_invocations=50,
        response_cache_ttl_hours=48,
        enable_logging=True,
        enable_metrics=True,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    ),
    agent_settings={
        "max_domain_suggestions": 10,
        "color_palette_size": 5,
        "enable_fallback_mode": True,
        "ai_model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7
    },
    intent_parsing={
        "enable_ai_parsing": True,
        "confidence_threshold": 0.4,
        "enable_clarification": True,
        "max_alternate_intents": 5
    },
    logging={
        "level": "INFO",
        "enable_audit_logs": True,
        "enable_performance_logs": True,
        "log_retention_hours": 168  # 1 week
    },
    security={
        "enable_task_locking": True,
        "max_concurrent_requests": 100,
        "request_timeout_seconds": 300,  # CRITICAL FIX: 5 minutes for regeneration calls
        "enable_rate_limiting": True
    }
)

DEVELOPMENT_CONFIG = BrandingAgentConfig(
    orchestration=OrchestrationConfig(
        redis_url="redis://localhost:6379",
        max_concurrent_invocations=5,
        response_cache_ttl_hours=1,
        enable_logging=True,
        enable_metrics=True
    ),
    agent_settings={
        "max_domain_suggestions": 3,
        "color_palette_size": 3,
        "enable_fallback_mode": True,
        "ai_model": "claude-3-sonnet-20240229",
        "temperature": 0.9
    },
    intent_parsing={
        "enable_ai_parsing": False,  # Use rule-based only for development
        "confidence_threshold": 0.2,
        "enable_clarification": True,
        "max_alternate_intents": 2
    },
    logging={
        "level": "DEBUG",
        "enable_audit_logs": True,
        "enable_performance_logs": True,
        "log_retention_hours": 6
    },
    security={
        "enable_task_locking": False,  # Disable for easier debugging
        "max_concurrent_requests": 3,
        "request_timeout_seconds": 300,  # CRITICAL FIX: 5 minutes for regeneration calls
        "enable_rate_limiting": False
    }
)


class OrchestrationIntegrationGuide:
    """Integration guide for BrandingAgent orchestration."""
    
    @staticmethod
    def get_integration_steps() -> List[Dict[str, Any]]:
        """Get step-by-step integration guide."""
        return [
            {
                "step": 1,
                "title": "Install Dependencies",
                "description": "Ensure Redis and required Python packages are installed",
                "code": """
# Install Redis
sudo apt-get install redis-server

# Install Python dependencies
pip install redis aioredis pydantic
                """
            },
            {
                "step": 2,
                "title": "Configure Environment",
                "description": "Set up environment variables and configuration",
                "code": """
# Set environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
export REDIS_URL="redis://localhost:6379"

# Or use .env file
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
echo "REDIS_URL=redis://localhost:6379" >> .env
                """
            },
            {
                "step": 3,
                "title": "Initialize Orchestrator",
                "description": "Create and initialize the branding orchestrator",
                "code": """
from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig

# Create configuration
config = OrchestrationConfig(
    redis_url="redis://localhost:6379",
    anthropic_api_key="your-api-key-here"
)

# Initialize orchestrator
orchestrator = BrandingOrchestrator(config)
await orchestrator.initialize()
                """
            },
            {
                "step": 4,
                "title": "Process Requests",
                "description": "Handle user requests through the orchestration layer",
                "code": """
# Process a branding request
response = await orchestrator.process_request(
    user_request="I need help coming up with a name for my eco-friendly pen business",
    session_id="user_123"
)

print(f"Brand Name: {response.get('brand_name')}")
print(f"Logo Prompt: {response.get('logo_prompt')}")
print(f"Color Palette: {response.get('color_palette')}")
                """
            },
            {
                "step": 5,
                "title": "Handle Feedback",
                "description": "Process user feedback for continuous improvement",
                "code": """
# Submit feedback
feedback_result = await orchestrator.submit_feedback(
    invocation_id="inv_123",
    feedback_type="thumbs_up",
    feedback_text="Great brand name!",
    rating=5
)

# Request revision
revision_result = await orchestrator.submit_feedback(
    invocation_id="inv_123",
    feedback_type="revision_request",
    feedback_text="Can you make it more modern?",
    rating=3
)
                """
            }
        ]
    
    @staticmethod
    def get_api_examples() -> List[Dict[str, Any]]:
        """Get API usage examples."""
        return [
            {
                "endpoint": "POST /orchestration/process",
                "description": "Process a user request",
                "request": {
                    "user_request": "I want to start a premium coffee brand",
                    "session_id": "user_123",
                    "context": {
                        "industry": "food_and_beverage",
                        "target_audience": "coffee_enthusiasts"
                    }
                },
                "response": {
                    "status": "success",
                    "brand_name": "BrewCraft",
                    "logo_prompt": "Design a modern, minimalist logo for BrewCraft coffee brand...",
                    "color_palette": ["#2C1810", "#8B4513", "#D2691E", "#F4A460"],
                    "domain_suggestions": ["brewcraft.com", "brewcraft.co", "brewcraft.ai"],
                    "orchestration": {
                        "intent_category": "branding",
                        "confidence": "high",
                        "session_id": "user_123"
                    }
                }
            },
            {
                "endpoint": "POST /orchestration/feedback",
                "description": "Submit user feedback",
                "request": {
                    "invocation_id": "inv_123",
                    "feedback_type": "revision_request",
                    "feedback_text": "Make the brand name more unique",
                    "rating": 3
                },
                "response": {
                    "status": "success",
                    "feedback_id": "fb_456",
                    "message": "Feedback submitted successfully"
                }
            },
            {
                "endpoint": "GET /orchestration/status/{invocation_id}",
                "description": "Get invocation status",
                "response": {
                    "invocation_id": "inv_123",
                    "status": "completed",
                    "response": {
                        "status": "success",
                        "brand_name": "BrewCraft",
                        "logo_prompt": "...",
                        "color_palette": ["#2C1810", "#8B4513"],
                        "domain_suggestions": ["brewcraft.com", "brewcraft.co"]
                    }
                }
            }
        ]
    
    @staticmethod
    def get_intent_examples() -> List[Dict[str, Any]]:
        """Get intent parsing examples."""
        return [
            {
                "user_request": "I need help coming up with a name for my eco-friendly pen business",
                "expected_intent": IntentCategory.BRANDING,
                "confidence": "high",
                "extracted_parameters": {
                    "business_type": "business",
                    "industry": "eco-friendly",
                    "product_type": "pen"
                }
            },
            {
                "user_request": "Can you design a logo for my new coffee shop?",
                "expected_intent": IntentCategory.BRANDING,
                "confidence": "high",
                "extracted_parameters": {
                    "business_type": "business",
                    "industry": "food_and_beverage",
                    "product_type": "coffee"
                }
            },
            {
                "user_request": "I want to create a brand identity for my tech startup",
                "expected_intent": IntentCategory.BRANDING,
                "confidence": "high",
                "extracted_parameters": {
                    "business_type": "startup",
                    "industry": "tech",
                    "product_type": "service"
                }
            },
            {
                "user_request": "Help me find leads for my SaaS product",
                "expected_intent": IntentCategory.SALES,
                "confidence": "high",
                "extracted_parameters": {
                    "business_type": "business",
                    "industry": "tech",
                    "product_type": "saas"
                }
            }
        ]


class SecurityAndIsolationGuide:
    """Guide for security and isolation features."""
    
    @staticmethod
    def get_security_features() -> List[Dict[str, Any]]:
        """Get security features implemented."""
        return [
            {
                "feature": "Task Locking",
                "description": "Prevents concurrent execution of overlapping tasks",
                "implementation": "asyncio.Lock per request",
                "benefit": "Prevents race conditions and data corruption"
            },
            {
                "feature": "Session Isolation",
                "description": "Separates user sessions and data",
                "implementation": "Redis-based session storage with TTL",
                "benefit": "Prevents cross-session data leakage"
            },
            {
                "feature": "Rate Limiting",
                "description": "Limits request frequency per user/session",
                "implementation": "Redis-based rate limiting with sliding windows",
                "benefit": "Prevents abuse and ensures fair resource allocation"
            },
            {
                "feature": "Audit Logging",
                "description": "Comprehensive logging of all operations",
                "implementation": "Structured logging with Redis storage",
                "benefit": "Enables compliance and debugging"
            },
            {
                "feature": "Error Isolation",
                "description": "Contains errors to prevent system-wide failures",
                "implementation": "Try-catch blocks with graceful degradation",
                "benefit": "Maintains system stability during failures"
            }
        ]
    
    @staticmethod
    def get_isolation_patterns() -> List[Dict[str, Any]]:
        """Get isolation patterns for agent coordination."""
        return [
            {
                "pattern": "Agent Registry",
                "description": "Centralized agent management with metadata",
                "benefit": "Prevents agent conflicts and enables discovery"
            },
            {
                "pattern": "Message Bus",
                "description": "Asynchronous communication between agents",
                "benefit": "Decouples agents and enables scalability"
            },
            {
                "pattern": "Response Caching",
                "description": "Caches agent responses to prevent redundant execution",
                "benefit": "Improves performance and reduces resource usage"
            },
            {
                "pattern": "Feedback Loops",
                "description": "Structured feedback processing for continuous improvement",
                "benefit": "Enables learning and adaptation"
            }
        ]


# Configuration validation
def validate_config(config: BrandingAgentConfig) -> List[str]:
    """Validate configuration and return any issues."""
    issues = []
    
    # Check Redis URL
    if not config.orchestration.redis_url:
        issues.append("Redis URL is required")
    
    # Check API key if AI parsing is enabled
    if (config.intent_parsing.get("enable_ai_parsing", True) and 
        not config.orchestration.anthropic_api_key):
        issues.append("Anthropic API key is required for AI intent parsing")
    
    # Check timeout settings
    if config.security.get("request_timeout_seconds", 30) < 5:
        issues.append("Request timeout must be at least 5 seconds")
    
    # Check concurrent request limits
    if config.security.get("max_concurrent_requests", 10) < 1:
        issues.append("Max concurrent requests must be at least 1")
    
    return issues


# Usage examples
def get_quick_start_example() -> str:
    """Get a quick start example for the integration."""
    return '''
# Quick Start Example

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
        "I need a brand name for my eco-friendly water bottle company"
    )
    
    print(f"Brand: {response.get('brand_name')}")
    print(f"Colors: {response.get('color_palette')}")
    print(f"Domains: {response.get('domain_suggestions')}")
    
    # Submit feedback
    await orchestrator.submit_feedback(
        response.get('orchestration', {}).get('invocation_id'),
        "thumbs_up",
        "Great brand name!"
    )
    
    await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
    ''' 