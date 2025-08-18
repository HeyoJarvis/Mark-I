"""
Universal Orchestrator - Intelligent Agent Routing System

This orchestrator provides a unified entry point that intelligently routes
user queries to the appropriate specialized orchestrator (Branding, Jarvis, HeyJarvis)
while maintaining backward compatibility with existing modes.
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, Any, Optional, Union, Literal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


from pydantic import BaseModel, Field
import redis.asyncio as redis
from langchain_anthropic import ChatAnthropic

# Import existing orchestrators
from .branding_orchestration import BrandingOrchestrator, OrchestrationConfig
from .jarvis import Jarvis, JarvisConfig
from .orchestrator import HeyJarvisOrchestrator, OrchestratorConfig

# Import AI components
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class RoutingIntent(str, Enum):
    """Intent types for orchestrator routing."""
    BRANDING = "branding"
    MARKET_RESEARCH = "market_research"
    JARVIS_BUSINESS = "jarvis_business" 
    HEYJARVIS_TECHNICAL = "heyjarvis_technical"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Decision made by the routing system."""
    intent: RoutingIntent
    confidence: float
    reasoning: str
    orchestrator_type: str
    fallback_intent: Optional[RoutingIntent] = None


class UniversalOrchestratorConfig(BaseModel):
    """Configuration for Universal Orchestrator."""
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    redis_url: str = Field(default="redis://localhost:6380", description="Redis connection URL")
    
    # Individual orchestrator configs
    branding_config: Optional[Dict[str, Any]] = Field(default=None)
    jarvis_config: Optional[Dict[str, Any]] = Field(default=None)
    heyjarvis_config: Optional[Dict[str, Any]] = Field(default=None)
    
    # Routing config
    routing_confidence_threshold: float = Field(default=0.7, description="Minimum confidence for routing")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_minutes: int = Field(default=30, description="Cache TTL in minutes")


class UniversalOrchestrator:
    """
    Universal orchestrator that intelligently routes queries to specialized orchestrators.
    
    Key Features:
    - Intelligent intent classification using LLM
    - Routes to existing orchestrators (preserves all functionality)
    - Unified response formatting
    - Conversation context management  
    - Backward compatibility with --branding, --jarvis modes
    """
    
    def __init__(self, config: UniversalOrchestratorConfig):
        """Initialize the Universal Orchestrator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.redis_client: Optional[redis.Redis] = None
        self.ai_engine: Optional[AnthropicEngine] = None
        
        # Orchestrator instances
        self.branding_orchestrator: Optional[BrandingOrchestrator] = None
        self.jarvis: Optional[Jarvis] = None
        self.heyjarvis_orchestrator: Optional[HeyJarvisOrchestrator] = None
        
        # Routing state
        self.conversation_context: Dict[str, Any] = {}
        self.routing_history: Dict[str, RoutingDecision] = {}
        
        self.logger.info("UniversalOrchestrator initialized")
    
    async def initialize(self) -> bool:
        """Initialize all components and orchestrators."""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
            
            # Initialize AI engine for routing decisions
            await self._initialize_ai_engine()
            
            # Initialize orchestrators lazily (on-demand)
            self.logger.info("UniversalOrchestrator initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UniversalOrchestrator: {e}")
            return False
    
    async def _initialize_ai_engine(self):
        """Initialize AI engine for intent classification."""
        try:
            engine_config = AIEngineConfig(
                api_key=self.config.anthropic_api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.2,  # Low temperature for consistent routing
                enable_cache=self.config.enable_caching
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("AI engine initialized for routing decisions")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    async def process_query(
        self, 
        user_query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        force_orchestrator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with intelligent routing.
        
        Args:
            user_query: The user's question/request
            session_id: Optional session identifier
            context: Optional context information
            force_orchestrator: Force routing to specific orchestrator (for backward compatibility)
            
        Returns:
            Response from the appropriate orchestrator
        """
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Determine routing decision
            if force_orchestrator:
                # Backward compatibility - forced routing
                routing_decision = RoutingDecision(
                    intent=RoutingIntent(force_orchestrator),
                    confidence=1.0,
                    reasoning=f"Forced routing to {force_orchestrator}",
                    orchestrator_type=force_orchestrator
                )
            else:
                # Intelligent routing
                routing_decision = await self._classify_intent(user_query, session_id, context)
            
            self.logger.info(f"Routing decision: {routing_decision.intent} (confidence: {routing_decision.confidence:.2f})")
            
            # Step 2: Route to appropriate orchestrator
            response = await self._route_to_orchestrator(
                routing_decision, 
                user_query, 
                session_id, 
                context
            )
            
            # Step 3: Format unified response
            unified_response = await self._format_response(
                response, 
                routing_decision, 
                start_time
            )
            
            # Step 4: Store conversation context
            await self._store_context(session_id, user_query, unified_response, routing_decision)
            
            return unified_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _classify_intent(
        self, 
        user_query: str, 
        session_id: str, 
        context: Optional[Dict[str, Any]]
    ) -> RoutingDecision:
        """Classify user intent using AI to determine routing."""
        
        # Get conversation history for context
        conversation_history = await self._get_conversation_context(session_id)
        
        if not self.ai_engine:
            # TODO: Remove rule-based fallback - force NLP usage
            self.logger.error("AI engine not available - cannot classify intent without NLP")
            return RoutingDecision(
                intent=RoutingIntent.UNKNOWN,
                confidence=0.0,
                reasoning="AI engine not available for NLP classification",
                orchestrator_type="unknown"
            )
        
        try:
            prompt = self._create_classification_prompt(user_query, conversation_history, context)
            response = await self.ai_engine.generate(prompt)
            
            return self._parse_classification_response(response.content)
            
        except Exception as e:
            self.logger.error(f"AI classification failed: {e}")
            # TODO: Remove rule-based fallback - should fix NLP issues instead
            self.logger.warning("Forcing NLP-only classification - fix AI issues instead of fallback")
            return RoutingDecision(
                intent=RoutingIntent.UNKNOWN,
                confidence=0.0,
                reasoning=f"NLP classification failed: {str(e)}",
                orchestrator_type="unknown"
            )
    
    def _create_classification_prompt(
        self, 
        user_query: str, 
        conversation_history: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for AI-powered intent classification."""
        
        context_str = ""
        if conversation_history.get("recent_interactions"):
            context_str = f"Previous interactions: {conversation_history['recent_interactions']}"
        
        prompt = f"""
You are an intelligent routing system that classifies user queries to determine which specialized AI agent should handle them.

Available Orchestrators:
1. BRANDING - Brand creation, logo design, color palettes, business identity (NOT market research)
   Examples: "Create a brand for my coffee shop", "Design a logo", "I need brand colors"

2. MARKET_RESEARCH - Market analysis, competitor research, industry insights, customer analysis, pricing trends
   Examples: "Analyze the EV market", "Competitor analysis for fintech", "Market size for sustainable fashion"

3. JARVIS_BUSINESS - High-level business strategy, department coordination, multi-agent workflows
   Examples: "Help me grow my business", "Coordinate marketing and sales", "Business insights"

4. HEYJARVIS_TECHNICAL - Technical agent creation, automation, monitoring, coding tasks
   Examples: "Create an email monitoring agent", "Build a web scraper", "Monitor stock prices"

User Query: "{user_query}"

{context_str}

Classify this query and respond in JSON format:
{{
  "intent": "BRANDING|MARKET_RESEARCH|JARVIS_BUSINESS|HEYJARVIS_TECHNICAL",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this classification was chosen",
  "key_indicators": ["words or phrases that influenced the decision"],
  "fallback_intent": "alternative intent if confidence is low"
}}

Focus on the PRIMARY intent - what is the user ultimately trying to accomplish?
"""
        return prompt
    
    def _parse_classification_response(self, response_content: str) -> RoutingDecision:
        """Parse AI classification response."""
        try:
            import json
            import re
            
            # Extract JSON from response - handle multiple formats
            # First try to find JSON block
            json_match = re.search(r'\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to extract everything between first { and last }
                start = response_content.find('{')
                end = response_content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = response_content[start:end+1]
                else:
                    json_str = response_content.strip()
            
            # Clean up common issues
            json_str = json_str.strip()
            
            data = json.loads(json_str)
            
            intent = RoutingIntent(data["intent"].lower())
            confidence = float(data["confidence"])
            reasoning = data["reasoning"]
            fallback = None
            
            if data.get("fallback_intent"):
                fallback = RoutingIntent(data["fallback_intent"].lower())
            
            return RoutingDecision(
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
                orchestrator_type=intent.value,
                fallback_intent=fallback
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse classification response: {e}")
            # TODO: Remove rule-based fallback
            return RoutingDecision(
                intent=RoutingIntent.UNKNOWN,
                confidence=0.0,
                reasoning=f"Failed to parse NLP response: {str(e)}",
                orchestrator_type="unknown"
            )
    
    # TODO: DEPRECATED - Remove this method after confirming NLP works
    def _rule_based_classification_DEPRECATED(self, user_query: str) -> RoutingDecision:
        """Fallback rule-based classification."""
        query_lower = user_query.lower()
        
        # Branding keywords
        branding_keywords = [
            "brand", "logo", "colors", "palette", "design", "identity", 
            "name", "domain", "visual", "creative"
        ]
        
        # Market research keywords
        market_research_keywords = [
            "market research", "competitor analysis", "market size", 
            "industry analysis", "customer insights", "pricing analysis",
            "market trends", "competitive landscape", "market opportunity",
            "feasibility study", "business intelligence", "pricing trends",
            "analyze", "research"
        ]
        
        # Business strategy keywords  
        business_keywords = [
            "business", "strategy", "department", "coordinate", "insights",
            "grow", "expansion", "revenue", "customers", "market", "sales",
            "profit", "income", "lead", "conversion", "pipeline", "growth"
        ]
        
        # Technical/automation keywords
        technical_keywords = [
            "agent", "monitor", "automate", "scrape", "email", "api",
            "code", "build", "create", "technical", "system"
        ]
        
        branding_score = sum(1 for keyword in branding_keywords if keyword in query_lower)
        market_research_score = sum(1 for keyword in market_research_keywords if keyword in query_lower)
        business_score = sum(1 for keyword in business_keywords if keyword in query_lower)  
        technical_score = sum(1 for keyword in technical_keywords if keyword in query_lower)
        
        # Market research gets priority if detected
        if market_research_score > 0:
            return RoutingDecision(
                intent=RoutingIntent.MARKET_RESEARCH,
                confidence=0.8,
                reasoning="Rule-based classification detected market research keywords",
                orchestrator_type="market_research"
            )
        elif branding_score >= business_score and branding_score >= technical_score:
            return RoutingDecision(
                intent=RoutingIntent.BRANDING,
                confidence=0.6,
                reasoning="Rule-based classification detected branding-related keywords",
                orchestrator_type="branding"
            )
        elif business_score >= technical_score:
            return RoutingDecision(
                intent=RoutingIntent.JARVIS_BUSINESS,
                confidence=0.6,
                reasoning="Rule-based classification detected business strategy keywords",
                orchestrator_type="jarvis_business"
            )
        else:
            return RoutingDecision(
                intent=RoutingIntent.HEYJARVIS_TECHNICAL,
                confidence=0.5,
                reasoning="Default routing to technical agent",
                orchestrator_type="heyjarvis_technical"
            )
    
    async def _route_to_orchestrator(
        self,
        routing_decision: RoutingDecision,
        user_query: str,
        session_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Route the query to the appropriate orchestrator."""
        
        if routing_decision.intent == RoutingIntent.BRANDING:
            return await self._route_to_branding(user_query, session_id, context)
        elif routing_decision.intent == RoutingIntent.MARKET_RESEARCH:
            return await self._route_to_market_research(user_query, session_id, context)
        elif routing_decision.intent == RoutingIntent.JARVIS_BUSINESS:
            return await self._route_to_jarvis(user_query, session_id, context)
        elif routing_decision.intent == RoutingIntent.HEYJARVIS_TECHNICAL:
            return await self._route_to_heyjarvis(user_query, session_id, context)
        else:
            # Default fallback
            return await self._route_to_heyjarvis(user_query, session_id, context)
    
    async def _route_to_branding(self, user_query: str, session_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Route to branding orchestrator."""
        if not self.branding_orchestrator:
            await self._initialize_branding_orchestrator()
        
        return await self.branding_orchestrator.process_request(user_query, session_id, context)
    
    async def _route_to_market_research(self, user_query: str, session_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Route to market research agent via agent integration system."""
        # For now, route market research through the agent integration system
        # In the future, we could create a dedicated market research orchestrator
        if not hasattr(self, 'agent_executor'):
            # Initialize agent executor with proper dependencies
            from .agent_integration import AgentExecutor, AgentMessageBus
            import redis.asyncio as redis
            
            # Initialize Redis client
            redis_client = redis.from_url(self.config.redis_url)
            
            # Initialize message bus
            message_bus = AgentMessageBus(redis_client)
            
            # Initialize agent executor
            self.agent_executor = AgentExecutor(redis_client, message_bus)
        
        # Invoke market research agent and await response
        try:
            response = await self.agent_executor.invoke_agent_and_wait(
                agent_id="market_research_agent",
                input_state={
                    "business_idea": user_query,
                    "user_request": user_query,
                    "session_id": session_id
                },
                context={"orchestrator": "universal", "routing_intent": "market_research"}
            )
            
            return {
                "status": "completed",
                "orchestrator": "market_research",
                "agent_used": "market_research_agent", 
                "invocation_id": response.invocation_id,
                "result": response.output_state,
                "agent_status": response.status.value,
                "execution_time_ms": response.execution_time_ms,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Market research routing failed: {e}")
            return {
                "status": "error",
                "orchestrator": "market_research",
                "error": f"Market research failed: {str(e)}",
                "session_id": session_id
            }
    
    async def _route_to_jarvis(self, user_query: str, session_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Route to Jarvis orchestrator."""
        if not self.jarvis:
            await self._initialize_jarvis()
        
        return await self.jarvis.process_business_request(user_query, session_id)
    
    async def _route_to_heyjarvis(self, user_query: str, session_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Route to HeyJarvis orchestrator."""
        if not self.heyjarvis_orchestrator:
            await self._initialize_heyjarvis()
        
        # Convert to the expected format
        return await self.heyjarvis_orchestrator.process_request(user_query, session_id)
    
    async def _initialize_branding_orchestrator(self):
        """Initialize branding orchestrator on-demand."""
        config = OrchestrationConfig(
            redis_url=self.config.redis_url,
            anthropic_api_key=self.config.anthropic_api_key,
            max_concurrent_invocations=5,
            response_cache_ttl_hours=1,
            enable_logging=True,
            enable_metrics=True
        )
        
        self.branding_orchestrator = BrandingOrchestrator(config)
        await self.branding_orchestrator.initialize()
        self.logger.info("Branding orchestrator initialized")
    
    async def _initialize_jarvis(self):
        """Initialize Jarvis orchestrator on-demand."""
        orchestrator_config = OrchestratorConfig(
            anthropic_api_key=self.config.anthropic_api_key,
            redis_url=self.config.redis_url,
            max_retries=3,
            session_timeout=3600
        )
        
        jarvis_config = JarvisConfig(
            orchestrator_config=orchestrator_config,
            max_concurrent_departments=5,
            enable_autonomous_department_creation=True,
            enable_cross_department_coordination=True
        )
        
        self.jarvis = Jarvis(jarvis_config)
        await self.jarvis.initialize()
        self.logger.info("Jarvis orchestrator initialized")
    
    async def _initialize_heyjarvis(self):
        """Initialize HeyJarvis orchestrator on-demand."""
        config = OrchestratorConfig(
            anthropic_api_key=self.config.anthropic_api_key,
            redis_url=self.config.redis_url,
            max_retries=3,
            session_timeout=3600
        )
        
        self.heyjarvis_orchestrator = HeyJarvisOrchestrator(config)
        await self.heyjarvis_orchestrator.initialize()
        self.logger.info("HeyJarvis orchestrator initialized")
    
    async def _format_response(
        self, 
        response: Dict[str, Any], 
        routing_decision: RoutingDecision, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Format response with unified metadata."""
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "response": response,
            "routing_info": {
                "orchestrator": routing_decision.orchestrator_type,
                "intent": routing_decision.intent.value,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning
            },
            "metadata": {
                "processing_time_ms": int(processing_time),
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": response.get("session_id"),
                "version": "universal_v1.0"
            },
            "status": "success"
        }
    
    async def _store_context(
        self, 
        session_id: str, 
        query: str, 
        response: Dict[str, Any], 
        routing_decision: RoutingDecision
    ):
        """Store conversation context for future routing decisions."""
        try:
            context_key = f"universal_context:{session_id}"
            context_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query[:200],  # Truncate for storage
                "intent": routing_decision.intent.value,
                "orchestrator": routing_decision.orchestrator_type,
                "success": response.get("status") == "success"
            }
            
            # Store as JSON with TTL
            await self.redis_client.lpush(context_key, json.dumps(context_entry, cls=DateTimeEncoder))
            await self.redis_client.ltrim(context_key, 0, 9)  # Keep last 10 interactions
            await self.redis_client.expire(context_key, 3600)  # 1 hour TTL
            
        except Exception as e:
            self.logger.error(f"Failed to store context: {e}")
    
    async def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieve conversation context for routing decisions."""
        try:
            context_key = f"universal_context:{session_id}"
            entries = await self.redis_client.lrange(context_key, 0, 4)  # Last 5 interactions
            
            recent_interactions = []
            for entry in entries:
                try:
                    interaction = json.loads(entry.decode())
                    recent_interactions.append(interaction)
                except:
                    continue
            
            return {
                "recent_interactions": recent_interactions,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation context: {e}")
            return {}
    
    async def close(self):
        """Clean up resources."""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.branding_orchestrator:
            await self.branding_orchestrator.close()
        
        if self.jarvis:
            await self.jarvis.close()
        
        # HeyJarvisOrchestrator doesn't have close method yet
        
        self.logger.info("UniversalOrchestrator closed")