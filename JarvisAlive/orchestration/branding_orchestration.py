"""
Branding Agent Orchestration Integration

Main orchestration layer that integrates the BrandingAgent with the HeyJarvis
system, providing intent-driven routing, agent invocation, and response handling.
"""

import json
import logging
import asyncio
import uuid
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from pydantic import BaseModel, Field
import redis.asyncio as redis

# Import orchestration components
from .intent_parser import IntentParser, ParsedIntent
from .agent_integration import AgentExecutor, ResponseFormatter, FeedbackType, AgentStatus
from .agent_communication import AgentMessageBus, MessagePriority
from .state import OrchestratorState, DepartmentStatus

logger = logging.getLogger(__name__)


class OrchestrationConfig(BaseModel):
    """Configuration for the branding orchestration layer."""
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    max_concurrent_invocations: int = Field(default=10, description="Max concurrent agent invocations")
    response_cache_ttl_hours: int = Field(default=24, description="Response cache TTL in hours")
    enable_logging: bool = Field(default=True, description="Enable detailed logging")
    enable_metrics: bool = Field(default=True, description="Enable performance metrics")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key for intent parsing")


class OrchestrationMetrics(BaseModel):
    """Performance metrics for orchestration layer."""
    total_requests: int = Field(default=0, description="Total requests processed")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    intent_parsing_accuracy: float = Field(default=0.0, description="Intent parsing accuracy")
    agent_success_rate: float = Field(default=0.0, description="Agent success rate")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last metrics update")


class BrandingOrchestrator:
    """
    Main orchestration layer for BrandingAgent integration.
    
    Provides:
    - Intent-driven routing
    - Agent invocation and response handling
    - Feedback loops and revision support
    - Logging and traceability
    - Security and isolation
    """
    
    def __init__(self, config: OrchestrationConfig):
        """
        Initialize the branding orchestrator.
        
        Args:
            config: Orchestration configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.redis_client = None
        self.message_bus = None
        self.intent_parser = None
        self.agent_executor = None
        self.response_formatter = None
        
        # Metrics
        self.metrics = OrchestrationMetrics()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Task locking for security
        self.task_locks: Dict[str, asyncio.Lock] = {}
        
        self.logger.info("BrandingOrchestrator initialized")
    
    async def initialize(self) -> bool:
        """Initialize all orchestration components."""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
            
            # Initialize message bus
            self.message_bus = AgentMessageBus(self.redis_client)
            self.logger.info("Message bus initialized")
            
            # Initialize intent parser
            intent_config = {
                'anthropic_api_key': self.config.anthropic_api_key
            }
            self.intent_parser = IntentParser(intent_config)
            self.logger.info("Intent parser initialized")
            
            # Initialize agent executor
            self.agent_executor = AgentExecutor(self.redis_client, self.message_bus)
            self.logger.info("Agent executor initialized")
            
            # Initialize response formatter
            self.response_formatter = ResponseFormatter()
            self.logger.info("Response formatter initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestration: {e}")
            return False
    
    async def process_request(
        self, 
        user_request: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request through the orchestration layer.
        
        Args:
            user_request: User's request text
            session_id: Optional session identifier
            context: Optional context information
            
        Returns:
            Orchestration response with results
        """
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create task lock for this request
        task_lock = asyncio.Lock()
        self.task_locks[request_id] = task_lock
        
        try:
            async with task_lock:
                # Log request
                self._log_request(request_id, session_id, user_request, context)
                
                # Step 1: Parse intent
                parsed_intent = await self._parse_user_intent(user_request, context)
                
                # Step 2: Route to appropriate agent
                if parsed_intent.primary_intent == "branding":
                    result = await self._handle_branding_request(user_request, parsed_intent, session_id)
                else:
                    result = await self._handle_general_request(user_request, parsed_intent, session_id)
                
                # Step 3: Update metrics
                await self._update_metrics(start_time, True)
                
                # Step 4: Store session data
                await self._store_session_data(session_id, request_id, parsed_intent, result)
                
                return result
                
        except Exception as e:
            # Log error
            self.logger.error(f"Error processing request {request_id}: {e}")
            
            # Update metrics
            await self._update_metrics(start_time, False)
            
            # Return error response
            return {
                "status": "error",
                "message": f"Request processing failed: {str(e)}",
                "request_id": request_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Clean up task lock
            if request_id in self.task_locks:
                del self.task_locks[request_id]
    
    async def _parse_user_intent(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Parse user intent from request."""
        try:
            parsed_intent = await self.intent_parser.parse_intent(user_request, context)
            
            # Log intent parsing
            self.logger.info(f"Intent parsed: {parsed_intent.primary_intent} (confidence: {parsed_intent.confidence})")
            
            return parsed_intent
            
        except Exception as e:
            self.logger.error(f"Intent parsing failed: {e}")
            raise
    
    async def _handle_branding_request(
        self, 
        user_request: str, 
        parsed_intent: ParsedIntent,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle branding-specific requests with optional logo generation."""
        try:
            # Check if user wants actual logo generation
            wants_logo_generation = self._detect_logo_generation_request(user_request)
            
            # Extract business information from request
            business_info = self._extract_business_info(user_request, parsed_intent)
            
            # Step 1: Invoke branding agent
            branding_invocation_id = await self.agent_executor.invoke_agent(
                agent_id="branding_agent",
                input_state=business_info,
                context={
                    "user_request": user_request,
                    "parsed_intent": parsed_intent.dict(),
                    "session_id": session_id
                }
            )
            
            # Wait for branding response
            branding_response = await self._wait_for_response(branding_invocation_id, timeout_seconds=300)
            
            if not branding_response:
                return {
                    "status": "timeout",
                    "message": "Branding generation timed out",
                    "invocation_id": branding_invocation_id
                }
            
            # Step 2: Optionally invoke logo generation agent
            final_response = branding_response
            if wants_logo_generation and branding_response.status == AgentStatus.COMPLETED:
                try:
                    self.logger.info("Invoking logo generation agent for visual assets")
                    
                    # Use branding agent output as input for logo generation
                    logo_input_state = branding_response.output_state.copy()
                    
                    logo_invocation_id = await self.agent_executor.invoke_agent(
                        agent_id="logo_generation_agent",
                        input_state=logo_input_state,
                        context={
                            "user_request": user_request,
                            "branding_result": branding_response.output_state,
                            "session_id": session_id
                        }
                    )
                    
                    # Wait for logo generation response
                    logo_response = await self._wait_for_response(logo_invocation_id, timeout_seconds=60)
                    
                    if logo_response and logo_response.status == AgentStatus.COMPLETED:
                        # Combine both results
                        combined_output = branding_response.output_state.copy()
                        combined_output.update(logo_response.output_state)
                        
                        # Create combined response
                        final_response = branding_response
                        final_response.output_state = combined_output
                        final_response.metadata["multi_agent_coordination"] = {
                            "branding_invocation": branding_invocation_id,
                            "logo_invocation": logo_invocation_id,
                            "coordination_successful": True
                        }
                    else:
                        self.logger.warning("Logo generation failed, returning branding result only")
                        # Add logo generation failure info to branding response
                        final_response.output_state["logo_generation_attempted"] = True
                        final_response.output_state["logo_generation_success"] = False
                        final_response.output_state["logo_generation_error"] = "Logo generation timed out or failed"
                
                except Exception as e:
                    self.logger.error(f"Logo generation coordination failed: {e}")
                    # Return branding result with error info
                    final_response.output_state["logo_generation_attempted"] = True
                    final_response.output_state["logo_generation_success"] = False
                    final_response.output_state["logo_generation_error"] = str(e)
            
            # Format response
            formatted_response = self.response_formatter.format_response(final_response, "branding_agent")
            
            # Add orchestration metadata
            formatted_response.update({
                "orchestration": {
                    "intent_category": parsed_intent.primary_intent,
                    "confidence": parsed_intent.confidence,
                    "session_id": session_id,
                    "request_id": str(uuid.uuid4())
                }
            })
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Branding request handling failed: {e}")
            raise
    
    async def _handle_general_request(
        self, 
        user_request: str, 
        parsed_intent: ParsedIntent,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle general requests (non-branding)."""
        return {
            "status": "not_supported",
            "message": f"Agent category '{parsed_intent.primary_intent}' is not yet supported",
            "suggested_agents": parsed_intent.suggested_agents,
            "session_id": session_id
        }
    
    def _extract_business_info(self, user_request: str, parsed_intent: ParsedIntent) -> Dict[str, Any]:
        """Extract business information from user request and parsed intent."""
        # Clean up the business idea - remove campaign/branding request language
        cleaned_request = user_request.lower()
        
        # Remove branding campaign language to focus on business concept
        cleanup_patterns = [
            r"make\s+a?\s+branding\s+campaign?\s+(for|of)\s+",
            r"create\s+a?\s+brand\s+(for|of)\s+",
            r"design\s+branding\s+(for|of)\s+",
            r"branding\s+(for|of)\s+"
        ]
        
        for pattern in cleanup_patterns:
            cleaned_request = re.sub(pattern, "", cleaned_request).strip()
        
        business_info = {
            "business_idea": cleaned_request if cleaned_request else user_request
        }
        
        # Add extracted parameters from intent parsing
        if parsed_intent.extracted_parameters:
            business_info.update(parsed_intent.extracted_parameters)
        
        # Extract additional information using simple patterns
        
        # Extract product type and business type
        product_patterns = [
            r"(pen|pens)\s*(store|shop|retailer)",  # pen store
            r"(pen|pens|writing.*instrument)s?",    # general pens
            r"(coffee|beverage|drink)\s*(shop|store|bar|cafe)",
            r"(app|application|software)\s*(company|service)?",
            r"(service|platform|tool)\s*(company|business)?"
        ]
        
        # Also extract business type
        business_type_patterns = [
            r"(store|shop|retailer|marketplace)",
            r"(company|business|corporation)",
            r"(service|platform|agency)",
            r"(cafe|restaurant|bar)"
        ]
        
        for pattern in product_patterns:
            match = re.search(pattern, user_request.lower())
            if match:
                full_match = match.group(0)
                business_info["product_type"] = full_match
                # Extract just the product if it's combined (e.g., "pen store" -> "pen")
                if "store" in full_match or "shop" in full_match:
                    product_part = re.sub(r"\s*(store|shop|retailer).*", "", full_match).strip()
                    business_info["product_focus"] = product_part
                    business_info["business_type"] = "retail store"
                break
        
        # Extract business type if not already found
        if "business_type" not in business_info:
            for pattern in business_type_patterns:
                match = re.search(pattern, user_request.lower())
                if match:
                    business_info["business_type"] = match.group(0)
                    break
        
        # Extract target audience
        audience_patterns = [
            r"(?:professionals?|business.*people)",
            r"(?:students?|academics?)",
            r"(?:consumers?|customers?)",
            r"(?:developers?|engineers?)"
        ]
        
        for pattern in audience_patterns:
            if re.search(pattern, user_request.lower()):
                business_info["target_audience"] = re.search(pattern, user_request.lower()).group(0)
                break
        
        return business_info
    
    def _detect_logo_generation_request(self, user_request: str) -> bool:
        """Detect if the user wants actual logo generation, not just prompts."""
        request_lower = user_request.lower()
        
        # Keywords that indicate desire for actual logo images
        logo_generation_keywords = [
            "generate logo", "generate a logo", "generate the logo",
            "create logo image", "create a logo", "create the logo",
            "make logo", "make a logo", "make the logo",
            "design logo", "design a logo", "design the logo",
            "visual logo", "logo image", "actual logo", "logo design",
            "dall-e logo", "ai logo", "generate visual", "create visual",
            "logo artwork", "logo graphic", "show me logo", "see logo",
            "logo images", "logo for my", "logo for the"
        ]
        
        # Phrases that indicate logo generation
        logo_generation_phrases = [
            "and generate", "and create", "with visual", "with image",
            "actual logo", "real logo", "visual identity", "logo design",
            "logo images", "branding and actual", "actual logo images"
        ]
        
        # Check for direct keywords
        for keyword in logo_generation_keywords:
            if keyword in request_lower:
                return True
        
        # Check for phrases
        for phrase in logo_generation_phrases:
            if phrase in request_lower:
                return True
        
        # Check for questions about seeing/viewing logos
        if any(word in request_lower for word in ["show", "see", "view", "display"]) and "logo" in request_lower:
            return True
        
        return False
    
    async def _wait_for_response(self, invocation_id: str, timeout_seconds: int = 300) -> Optional[Any]:
        """Wait for agent response with timeout."""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
            response = await self.agent_executor.get_response(invocation_id)
            if response:
                return response
            
            # Wait before checking again
            await asyncio.sleep(0.5)
        
        return None
    
    async def submit_feedback(
        self, 
        invocation_id: str, 
        feedback_type: FeedbackType,
        feedback_text: Optional[str] = None,
        rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit user feedback for an agent response."""
        try:
            feedback_id = await self.agent_executor.submit_feedback(
                invocation_id=invocation_id,
                feedback_type=feedback_type,
                feedback_text=feedback_text,
                rating=rating
            )
            
            return {
                "status": "success",
                "feedback_id": feedback_id,
                "message": "Feedback submitted successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Feedback submission failed: {e}")
            return {
                "status": "error",
                "message": f"Feedback submission failed: {str(e)}"
            }
    
    async def get_response_status(self, invocation_id: str) -> Dict[str, Any]:
        """Get status of an agent invocation."""
        try:
            status = await self.agent_executor.get_invocation_status(invocation_id)
            response = await self.agent_executor.get_response(invocation_id)
            
            result = {
                "invocation_id": invocation_id,
                "status": status.value if status else "unknown"
            }
            
            if response:
                result["response"] = self.response_formatter.format_response(response, response.agent_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return {
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }
    
    def _log_request(self, request_id: str, session_id: str, user_request: str, context: Optional[Dict[str, Any]]):
        """Log request details for traceability."""
        log_entry = {
            "request_id": request_id,
            "session_id": session_id,
            "user_request": user_request[:200],  # Truncate for logging
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Processing request: {json.dumps(log_entry)}")
        
        # Store in Redis for audit trail
        if self.redis_client:
            asyncio.create_task(self._store_audit_log(log_entry))
    
    async def _store_audit_log(self, log_entry: Dict[str, Any]):
        """Store audit log entry in Redis."""
        try:
            audit_key = f"audit:request:{log_entry['request_id']}"
            await self.redis_client.setex(
                audit_key,
                86400,  # 24 hours TTL
                json.dumps(log_entry)
            )
        except Exception as e:
            self.logger.error(f"Failed to store audit log: {e}")
    
    async def _update_metrics(self, start_time: datetime, success: bool):
        """Update orchestration metrics."""
        try:
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update metrics
            self.metrics.total_requests += 1
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
            
            # Update average response time
            if self.metrics.total_requests > 0:
                current_avg = self.metrics.average_response_time_ms
                new_avg = (current_avg * (self.metrics.total_requests - 1) + response_time) / self.metrics.total_requests
                self.metrics.average_response_time_ms = new_avg
            
            self.metrics.last_updated = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    async def _store_session_data(self, session_id: str, request_id: str, parsed_intent: ParsedIntent, result: Dict[str, Any]):
        """Store session data for future reference."""
        try:
            session_data = {
                "session_id": session_id,
                "request_id": request_id,
                "parsed_intent": parsed_intent.dict(),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Redis
            session_key = f"session:{session_id}"
            await self.redis_client.setex(
                session_key,
                3600,  # 1 hour TTL
                json.dumps(session_data, cls=DateTimeEncoder)
            )
            
            # Update active sessions
            self.active_sessions[session_id] = session_data
            
        except Exception as e:
            self.logger.error(f"Failed to store session data: {e}")
    
    async def get_metrics(self) -> OrchestrationMetrics:
        """Get current orchestration metrics."""
        return self.metrics
    
    async def cleanup(self):
        """Clean up orchestration resources."""
        try:
            # Clean up old responses
            await self.agent_executor.cleanup_old_responses()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("Orchestration cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of orchestration components."""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
                health_status["components"]["redis"] = "healthy"
            else:
                health_status["components"]["redis"] = "unavailable"
            
            # Check intent parser
            if self.intent_parser:
                health_status["components"]["intent_parser"] = "healthy"
            else:
                health_status["components"]["intent_parser"] = "unavailable"
            
            # Check agent executor
            if self.agent_executor:
                health_status["components"]["agent_executor"] = "healthy"
            else:
                health_status["components"]["agent_executor"] = "unavailable"
            
            # Check overall health
            if any(status == "unavailable" for status in health_status["components"].values()):
                health_status["status"] = "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 