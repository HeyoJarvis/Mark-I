"""
Agent Integration Layer for HeyJarvis Orchestration

Handles agent invocation, response processing, and feedback loops
for the orchestration layer.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field
import redis.asyncio as redis

# Import existing components
from .agent_communication import AgentMessageBus, MessageType, MessagePriority
from .intent_parser import ParsedIntent
from departments.branding.branding_agent import BrandingAgent
from departments.branding.logo_generation_agent import LogoGenerationAgent
from departments.market_research.market_research_agent import MarketResearchAgent
from departments.website.website_generator_agent import WebsiteGeneratorAgent

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Status of agent execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    """Types of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REVISION_REQUEST = "revision_request"
    CLARIFICATION = "clarification"


class AgentInvocation(BaseModel):
    """Agent invocation request."""
    invocation_id: str = Field(..., description="Unique invocation identifier")
    agent_id: str = Field(..., description="Agent identifier")
    input_state: Dict[str, Any] = Field(..., description="Input state for agent")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: MessagePriority = Field(default=MessagePriority.MEDIUM, description="Execution priority")
    timeout_seconds: int = Field(default=300, description="Execution timeout")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentResponse(BaseModel):
    """Agent execution response."""
    invocation_id: str = Field(..., description="Associated invocation ID")
    agent_id: str = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Execution status")
    output_state: Dict[str, Any] = Field(default_factory=dict, description="Output state")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UserFeedback(BaseModel):
    """User feedback on agent response."""
    feedback_id: str = Field(..., description="Unique feedback identifier")
    invocation_id: str = Field(..., description="Associated invocation ID")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    feedback_text: Optional[str] = Field(None, description="Additional feedback text")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Feedback timestamp")


class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, Any] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Register default agents
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register default agents."""
        # Register BrandingAgent
        self.register_agent(
            agent_id="branding_agent",
            agent_class=BrandingAgent,
            metadata={
                "name": "Branding Agent",
                "description": "Generates brand names, logos, and visual identity",
                "capabilities": ["brand_name_generation", "logo_prompt_creation", "color_palette_generation"],
                "input_schema": {
                    "business_idea": "string",
                    "product_type": "string (optional)",
                    "target_audience": "string (optional)",
                    "industry": "string (optional)"
                },
                "output_schema": {
                    "brand_name": "string",
                    "logo_prompt": "string",
                    "color_palette": "array of hex colors",
                    "domain_suggestions": "array of domain names"
                },
                "category": "branding"
            }
        )
        
        # Register LogoGenerationAgent
        self.register_agent(
            agent_id="logo_generation_agent",
            agent_class=LogoGenerationAgent,
            metadata={
                "name": "Logo Generation Agent",
                "description": "Generates actual logo images using DALL-E based on design prompts",
                "capabilities": ["logo_image_generation", "visual_design", "dall_e_integration"],
                "input_schema": {
                    "logo_prompt": "string",
                    "brand_name": "string",
                    "color_palette": "array of hex colors (optional)",
                    "business_type": "string (optional)"
                },
                "output_schema": {
                    "logo_images": "array of logo image objects",
                    "image_urls": "array of image URLs",
                    "generation_success": "boolean"
                },
                "category": "visual_design",
                "dependencies": ["openai", "OPENAI_API_KEY"],
                "coordination": ["works_with_branding_agent"]
            }
        )
        
        # Register MarketResearchAgent
        self.register_agent(
            agent_id="market_research_agent",
            agent_class=MarketResearchAgent,
            metadata={
                "name": "Market Research Agent",
                "description": "Comprehensive market intelligence, competitor analysis, and strategic insights",
                "capabilities": [
                    "market_analysis", "competitor_research", "customer_insights", 
                    "pricing_analysis", "opportunity_assessment", "trend_analysis"
                ],
                "input_schema": {
                    "business_idea": "string",
                    "industry": "string (optional)",
                    "target_market": "string (optional)",
                    "geographic_focus": "string (optional)"
                },
                "output_schema": {
                    "market_size": "object with total_market_size, growth_rate",
                    "competitive_landscape": "object with competitors, barriers_to_entry",
                    "customer_analysis": "object with profiles, pain_points, buying_behavior",
                    "pricing_analysis": "object with price_ranges, recommended_pricing",
                    "opportunity_assessment": "object with opportunities, risks, success_factors"
                },
                "category": "market_research",
                "coordination": ["works_with_branding_agent", "informs_business_strategy"]
            }
        )
        
        # Register WebsiteGeneratorAgent
        self.register_agent(
            agent_id="website_generator_agent",
            agent_class=WebsiteGeneratorAgent,
            metadata={
                "name": "Website Generator Agent",
                "description": "Generates website sitemap, structure, content, and style guide",
                "capabilities": [
                    "website_architecture", "content_generation", "seo_optimization", 
                    "style_guide_creation", "conversion_optimization", "industry_customization"
                ],
                "input_schema": {
                    "brand_name": "string (optional)",
                    "business_idea": "string",
                    "color_palette": "array of hex colors (optional)",
                    "target_audience": "string (optional)",
                    "industry": "string (optional)",
                    "pages": "array of desired page names (optional)",
                    "website_type": "string (optional)"
                },
                "output_schema": {
                    "sitemap": "array of page names",
                    "website_structure": "array of page objects with sections",
                    "homepage": "object with SEO and content details",
                    "style_guide": "object with branding and design guidelines",
                    "seo_recommendations": "object with SEO strategy"
                },
                "category": "branding",
                "coordination": ["works_with_branding_agent", "uses_branding_context", "seo_optimized"]
            }
        )
        
        # Add more agents here as they become available
        # self.register_agent("sales_agent", SalesAgent, {...})
        # self.register_agent("marketing_agent", MarketingAgent, {...})
    
    def register_agent(self, agent_id: str, agent_class: type, metadata: Dict[str, Any]):
        """
        Register an agent in the registry.
        
        Args:
            agent_id: Unique agent identifier
            agent_class: Agent class
            metadata: Agent metadata
        """
        self.agents[agent_id] = agent_class
        self.agent_metadata[agent_id] = metadata
        self.logger.info(f"Registered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[type]:
        """Get agent class by ID."""
        return self.agents.get(agent_id)
    
    def get_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent metadata by ID."""
        return self.agent_metadata.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "agent_id": agent_id,
                "metadata": metadata
            }
            for agent_id, metadata in self.agent_metadata.items()
        ]
    
    def get_agents_by_category(self, category: str) -> List[str]:
        """Get agent IDs by category."""
        return [
            agent_id for agent_id, metadata in self.agent_metadata.items()
            if metadata.get("category") == category
        ]


class AgentExecutor:
    """Executes agent invocations and manages responses."""
    
    def __init__(self, redis_client: redis.Redis, message_bus: AgentMessageBus):
        """
        Initialize the agent executor.
        
        Args:
            redis_client: Redis client for state management
            message_bus: Message bus for agent communication
        """
        self.redis_client = redis_client
        self.message_bus = message_bus
        self.agent_registry = AgentRegistry()
        self.logger = logging.getLogger(__name__)
        
        # Active invocations
        self.active_invocations: Dict[str, AgentInvocation] = {}
        
        # Response cache
        self.response_cache: Dict[str, AgentResponse] = {}
        
        # Feedback storage
        self.feedback_storage: Dict[str, List[UserFeedback]] = {}
    
    async def invoke_agent(
        self, 
        agent_id: str, 
        input_state: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.MEDIUM
    ) -> str:
        """
        Invoke an agent with the given input.
        
        Args:
            agent_id: Agent identifier
            input_state: Input state for the agent
            context: Additional context
            priority: Execution priority
            
        Returns:
            Invocation ID
        """
        # Validate agent exists
        agent_class = self.agent_registry.get_agent(agent_id)
        if not agent_class:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Create invocation
        invocation_id = str(uuid.uuid4())
        invocation = AgentInvocation(
            invocation_id=invocation_id,
            agent_id=agent_id,
            input_state=input_state,
            context=context or {},
            priority=priority
        )
        
        # Store invocation
        self.active_invocations[invocation_id] = invocation
        
        # Log invocation
        self.logger.info(f"Invoking agent {agent_id} with invocation {invocation_id}")
        
        # Execute agent asynchronously
        asyncio.create_task(self._execute_agent(invocation))
        
        return invocation_id
    
    async def invoke_agent_and_wait(
        self, 
        agent_id: str, 
        input_state: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.MEDIUM
    ) -> AgentResponse:
        """
        Invoke an agent and wait for the response.
        
        Args:
            agent_id: Agent identifier
            input_state: Input state for the agent
            context: Additional context
            priority: Execution priority
            
        Returns:
            Agent response
        """
        # Validate agent exists
        agent_class = self.agent_registry.get_agent(agent_id)
        if not agent_class:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Create invocation
        invocation_id = str(uuid.uuid4())
        invocation = AgentInvocation(
            invocation_id=invocation_id,
            agent_id=agent_id,
            input_state=input_state,
            context=context or {},
            priority=priority
        )
        
        # Store invocation
        self.active_invocations[invocation_id] = invocation
        
        # Log invocation
        self.logger.info(f"Invoking agent {agent_id} with invocation {invocation_id} and waiting")
        
        # Execute agent and await result
        await self._execute_agent(invocation)
        
        # Return the response
        response = self.response_cache.get(invocation_id)
        if not response:
            raise RuntimeError(f"No response found for invocation {invocation_id}")
        
        return response
    
    async def _execute_agent(self, invocation: AgentInvocation):
        """Execute an agent invocation."""
        start_time = datetime.utcnow()
        
        try:
            # Get agent class
            agent_class = self.agent_registry.get_agent(invocation.agent_id)
            
            # Create agent instance
            agent = agent_class()
            
            # Execute agent (handle both sync and async)
            if hasattr(agent.run, '__call__') and asyncio.iscoroutinefunction(agent.run):
                output_state = await agent.run(invocation.input_state)
            else:
                output_state = agent.run(invocation.input_state)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create response
            response = AgentResponse(
                invocation_id=invocation.invocation_id,
                agent_id=invocation.agent_id,
                status=AgentStatus.COMPLETED,
                output_state=output_state,
                execution_time_ms=int(execution_time),
                metadata={
                    "input_state_keys": list(invocation.input_state.keys()),
                    "output_state_keys": list(output_state.keys())
                }
            )
            
            # Store response
            self.response_cache[invocation.invocation_id] = response
            
            # Remove from active invocations
            if invocation.invocation_id in self.active_invocations:
                del self.active_invocations[invocation.invocation_id]
            
            # Log success
            self.logger.info(f"Agent {invocation.agent_id} completed successfully in {execution_time:.2f}ms")
            
        except Exception as e:
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create error response
            response = AgentResponse(
                invocation_id=invocation.invocation_id,
                agent_id=invocation.agent_id,
                status=AgentStatus.FAILED,
                error_message=str(e),
                execution_time_ms=int(execution_time)
            )
            
            # Store response
            self.response_cache[invocation.invocation_id] = response
            
            # Remove from active invocations
            if invocation.invocation_id in self.active_invocations:
                del self.active_invocations[invocation.invocation_id]
            
            # Log error
            self.logger.error(f"Agent {invocation.agent_id} failed: {e}")
    
    async def get_response(self, invocation_id: str) -> Optional[AgentResponse]:
        """Get agent response by invocation ID."""
        return self.response_cache.get(invocation_id)
    
    async def get_invocation_status(self, invocation_id: str) -> Optional[AgentStatus]:
        """Get invocation status."""
        if invocation_id in self.active_invocations:
            return AgentStatus.RUNNING
        elif invocation_id in self.response_cache:
            return self.response_cache[invocation_id].status
        else:
            return None
    
    async def submit_feedback(
        self, 
        invocation_id: str, 
        feedback_type: FeedbackType,
        feedback_text: Optional[str] = None,
        rating: Optional[int] = None
    ) -> str:
        """
        Submit user feedback for an agent response.
        
        Args:
            invocation_id: Invocation ID
            feedback_type: Type of feedback
            feedback_text: Additional feedback text
            rating: Optional rating (1-5)
            
        Returns:
            Feedback ID
        """
        feedback_id = str(uuid.uuid4())
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            invocation_id=invocation_id,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            rating=rating
        )
        
        # Store feedback
        if invocation_id not in self.feedback_storage:
            self.feedback_storage[invocation_id] = []
        self.feedback_storage[invocation_id].append(feedback)
        
        # Log feedback
        self.logger.info(f"Feedback submitted for invocation {invocation_id}: {feedback_type}")
        
        # Handle feedback-based actions
        await self._handle_feedback(feedback)
        
        return feedback_id
    
    async def _handle_feedback(self, feedback: UserFeedback):
        """Handle user feedback and trigger appropriate actions."""
        if feedback.feedback_type == FeedbackType.REVISION_REQUEST:
            # Trigger agent revision
            await self._trigger_agent_revision(feedback)
        elif feedback.feedback_type == FeedbackType.THUMBS_DOWN:
            # Log negative feedback for improvement
            self.logger.info(f"Negative feedback received for {feedback.invocation_id}")
        elif feedback.feedback_type == FeedbackType.THUMBS_UP:
            # Log positive feedback
            self.logger.info(f"Positive feedback received for {feedback.invocation_id}")
    
    async def _trigger_agent_revision(self, feedback: UserFeedback):
        """Trigger agent revision based on feedback."""
        # Get original invocation
        original_invocation = self.active_invocations.get(feedback.invocation_id)
        if not original_invocation:
            return
        
        # Create revision invocation with feedback context
        revision_context = {
            "original_invocation_id": feedback.invocation_id,
            "feedback": feedback.feedback_text,
            "feedback_type": feedback.feedback_type.value
        }
        
        # Invoke agent again with revision context
        await self.invoke_agent(
            agent_id=original_invocation.agent_id,
            input_state=original_invocation.input_state,
            context=revision_context
        )
    
    async def get_feedback_history(self, invocation_id: str) -> List[UserFeedback]:
        """Get feedback history for an invocation."""
        return self.feedback_storage.get(invocation_id, [])
    
    async def cleanup_old_responses(self, max_age_hours: int = 24):
        """Clean up old responses from cache."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for invocation_id, response in self.response_cache.items():
            if response.completed_at < cutoff_time:
                to_remove.append(invocation_id)
        
        for invocation_id in to_remove:
            del self.response_cache[invocation_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old responses")


class ResponseFormatter:
    """Formats agent responses for user consumption."""
    
    def __init__(self):
        """Initialize the response formatter."""
        self.logger = logging.getLogger(__name__)
    
    def format_branding_response(self, response: AgentResponse) -> Dict[str, Any]:
        """Format branding agent response for user display."""
        if response.status != AgentStatus.COMPLETED:
            return {
                "status": "error",
                "message": response.error_message or "Branding generation failed"
            }
        
        output = response.output_state
        
        formatted_response = {
            "status": "success",
            "brand_name": output.get("brand_name", "N/A"),
            "logo_prompt": output.get("logo_prompt", "N/A"),
            "color_palette": output.get("color_palette", []),
            "domain_suggestions": output.get("domain_suggestions", []),
            "generated_at": output.get("branding_generated_at", "N/A"),
            "execution_time_ms": response.execution_time_ms,
            "invocation_id": response.invocation_id
        }
        
        # Add logo generation results if available
        if output.get("logo_generation_attempted"):
            formatted_response["logo_generation"] = {
                "attempted": True,
                "success": output.get("logo_generation_success", False),
                "error": output.get("logo_generation_error"),
                "images": output.get("logo_images", []),
                "generation_result": output.get("logo_generation_result", {})
            }
            
            # If successful, add image URLs for easy access
            if output.get("logo_generation_success") and output.get("logo_images"):
                logo_images = output.get("logo_images", [])
                formatted_response["logo_urls"] = [
                    img.get("image_url") for img in logo_images if img.get("image_url")
                ]
        
        return formatted_response
    
    def format_general_response(self, response: AgentResponse) -> Dict[str, Any]:
        """Format general agent response."""
        if response.status != AgentStatus.COMPLETED:
            return {
                "status": "error",
                "message": response.error_message or "Agent execution failed"
            }
        
        return {
            "status": "success",
            "output": response.output_state,
            "execution_time_ms": response.execution_time_ms,
            "invocation_id": response.invocation_id
        }
    
    def format_response(self, response: AgentResponse, agent_id: str) -> Dict[str, Any]:
        """Format response based on agent type."""
        if agent_id == "branding_agent":
            return self.format_branding_response(response)
        elif agent_id == "website_generator_agent":
            return self.format_website_response(response)
        else:
            return self.format_general_response(response) 
    
    def format_website_response(self, response: AgentResponse) -> Dict[str, Any]:
        """Format website generator agent response for user display."""
        if response.status != AgentStatus.COMPLETED:
            return {
                "status": "error",
                "message": response.error_message or "Website generation failed"
            }
        
        output = response.output_state
        
        formatted_response = {
            "status": "success",
            "sitemap": output.get("sitemap", []),
            "website_structure": output.get("website_structure", []),
            "homepage": output.get("homepage", {}),
            "style_guide": output.get("style_guide", {}),
            "seo_recommendations": output.get("seo_recommendations", {}),
            "generated_at": output.get("website_generated_at", "N/A"),
            "execution_time_ms": response.execution_time_ms,
            "invocation_id": response.invocation_id
        }
        
        return formatted_response 