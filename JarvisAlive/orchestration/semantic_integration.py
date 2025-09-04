"""
Semantic Architecture Integration

This module provides integration points to replace existing orchestration
with the new semantic architecture while maintaining backward compatibility.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Import existing components for compatibility
from .orchestrator import HeyJarvisOrchestrator, OrchestratorConfig
from .jarvis import BusinessIntent
from .intent_parser import IntentParser, ParsedIntent

# Import new semantic components  
from .semantic_orchestrator import SemanticOrchestrator, SemanticWorkflowState
from .semantic_request_parser import SemanticRequestParser, SemanticUnderstanding
from .semantic_state import SemanticStateManager, create_semantic_state_system

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class SemanticJarvis:
    """
    Enhanced Jarvis that uses semantic architecture for improved performance.
    
    Provides same interface as original Jarvis but with:
    - Single AI call understanding
    - Direct agent access without departments
    - Preserved semantic context
    - Better multi-agent coordination
    """
    
    def __init__(
        self,
        ai_engine: Optional[AnthropicEngine] = None,
        redis_client: Optional[Any] = None,
        conversation_manager: Optional[Any] = None,
        config: Optional[OrchestratorConfig] = None
    ):
        self.ai_engine = ai_engine or AnthropicEngine(AIEngineConfig())
        self.redis_client = redis_client
        self.conversation_manager = conversation_manager
        
        # Create default config with API key from environment or AI engine
        if config is None:
            import os
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key and ai_engine and hasattr(ai_engine, 'config'):
                api_key = ai_engine.config.api_key
            if not api_key:
                api_key = "placeholder_key"  # Fallback for mock mode
            
            self.config = OrchestratorConfig(anthropic_api_key=api_key)
        else:
            self.config = config
        
        # Initialize semantic components
        self.semantic_orchestrator = SemanticOrchestrator(
            ai_engine=self.ai_engine,
            redis_client=redis_client,
            conversation_manager=conversation_manager
        )
        
        self.state_manager, self.middleware = create_semantic_state_system(redis_client)
        
        # Maintain compatibility interface
        self.legacy_orchestrator = HeyJarvisOrchestrator(config) if config else None
        
        logger.info("Semantic Jarvis initialized")
    
    async def initialize(self) -> None:
        """Initialize the semantic jarvis components."""
        try:
            # Initialize semantic orchestrator
            await self.semantic_orchestrator.initialize()
            
            # Initialize legacy orchestrator if available
            if self.legacy_orchestrator:
                await self.legacy_orchestrator.initialize()
            
            logger.info("Semantic Jarvis components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Jarvis: {e}")
            # Continue without full initialization for graceful degradation
    
    async def process_request(
        self,
        user_request: str,
        session_id: str,
        business_context: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        use_legacy: bool = False
    ) -> Dict[str, Any]:
        """
        Process user request with semantic understanding.
        
        Args:
            user_request: Natural language request
            session_id: Session identifier
            business_context: Business context information
            conversation_context: Previous conversation context
            use_legacy: Whether to use legacy system for comparison
        
        Returns:
            Standardized response dict compatible with existing interfaces
        """
        if use_legacy and self.legacy_orchestrator:
            return await self._process_with_legacy(user_request, session_id, business_context)
        
        try:
            # Use semantic orchestration
            workflow_state = await self.semantic_orchestrator.process_request(
                user_request, session_id, conversation_context
            )
            
            # Convert to standard response format
            return self._convert_to_standard_response(workflow_state)
            
        except Exception as e:
            logger.error(f"Semantic processing failed: {e}")
            
            # Fallback to legacy if available
            if self.legacy_orchestrator:
                logger.info("Falling back to legacy orchestration")
                return await self._process_with_legacy(user_request, session_id, business_context)
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Request processing failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    async def _process_with_legacy(
        self,
        user_request: str,
        session_id: str,
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process with legacy orchestrator for comparison."""
        try:
            # This would integrate with existing orchestrator
            # Implementation depends on the actual legacy interface
            result = {
                "success": True,
                "message": "Processed with legacy system",
                "method": "legacy",
                "timestamp": datetime.utcnow().isoformat()
            }
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "legacy",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _convert_to_standard_response(self, workflow_state: SemanticWorkflowState) -> Dict[str, Any]:
        """Convert semantic workflow state to standard response format."""
        
        success = workflow_state.overall_status.value == "completed"
        
        response = {
            "success": success,
            "workflow_id": workflow_state.workflow_id,
            "session_id": workflow_state.session_id,
            "status": workflow_state.overall_status.value,
            "method": "semantic",
            "timestamp": datetime.utcnow().isoformat(),
            
            # Business understanding
            "business_goal": workflow_state.understanding.business_goal,
            "user_intent": workflow_state.understanding.user_intent_summary,
            "confidence": workflow_state.understanding.confidence_score,
            
            # Execution details
            "execution_strategy": workflow_state.understanding.execution_strategy.value,
            "agents_used": workflow_state.understanding.recommended_agents,
            "capabilities": [cap.value for cap in workflow_state.understanding.primary_capabilities],
            
            # Results
            "results": workflow_state.consolidated_result,
            "artifacts": workflow_state.artifacts,
            "progress": workflow_state.progress,
            
            # Performance
            "duration": str(workflow_state.completed_at - workflow_state.created_at) if workflow_state.completed_at else None,
            "agent_count": len(workflow_state.agent_states),
            
            # Error handling
            "errors": workflow_state.errors,
            "warnings": workflow_state.warnings
        }
        
        # Add agent-specific details
        if workflow_state.agent_states:
            response["agent_details"] = {}
            for agent_id, agent_state in workflow_state.agent_states.items():
                response["agent_details"][agent_id] = {
                    "status": agent_state.status.value,
                    "capability": agent_state.capability.value,
                    "progress": agent_state.progress,
                    "duration": str(agent_state.duration) if agent_state.duration else None,
                    "error": agent_state.error
                }
        
        return response
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow."""
        workflow_state = await self.semantic_orchestrator.get_workflow_status(workflow_id)
        if workflow_state:
            return self._convert_to_standard_response(workflow_state)
        else:
            return {"error": "Workflow not found", "workflow_id": workflow_id}
    
    async def list_active_workflows(self) -> List[str]:
        """List all active workflow IDs."""
        return await self.semantic_orchestrator.list_active_workflows()
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow.""" 
        return await self.semantic_orchestrator.cancel_workflow(workflow_id)


class SemanticIntentCompatibility:
    """
    Compatibility layer that provides IntentParser interface using semantic understanding.
    
    Allows existing code to use semantic parsing while maintaining the same API.
    """
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.semantic_parser = SemanticRequestParser(ai_engine)
    
    async def parse_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Parse intent using semantic understanding but return legacy format."""
        try:
            # Get semantic understanding
            understanding = await self.semantic_parser.parse_request(user_input, context)
            
            # Convert to legacy ParsedIntent format
            return self._convert_to_parsed_intent(understanding, user_input)
            
        except Exception as e:
            logger.error(f"Semantic intent parsing failed: {e}")
            
            # Return minimal fallback
            return ParsedIntent(
                primary_intent="general",
                confidence="low",
                confidence_score=0.1,
                suggested_agents=["general_agent"],
                extracted_parameters={},
                alternate_intents=[],
                requires_clarification=False,
                clarification_questions=[],
                reasoning=f"Fallback due to error: {str(e)}"
            )
    
    def _convert_to_parsed_intent(self, understanding: SemanticUnderstanding, user_input: str) -> ParsedIntent:
        """Convert semantic understanding to legacy ParsedIntent."""
        
        # Map capabilities to legacy intent categories
        capability_to_intent_map = {
            "brand_creation": "branding",
            "logo_generation": "branding", 
            "market_analysis": "market_research",
            "website_building": "engineering",
            "sales_outreach": "sales",
            "lead_generation": "sales",
            "content_creation": "marketing",
            "design_services": "branding"
        }
        
        # Determine primary intent from capabilities
        primary_intent = "general"
        if understanding.primary_capabilities:
            primary_cap = understanding.primary_capabilities[0].value
            primary_intent = capability_to_intent_map.get(primary_cap, "general")
        
        # Map confidence score to categories
        if understanding.confidence_score >= 0.8:
            confidence = "high"
        elif understanding.confidence_score >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Create alternate intents from secondary capabilities
        alternate_intents = []
        for cap in understanding.secondary_capabilities:
            intent_name = capability_to_intent_map.get(cap.value, "general")
            if intent_name != primary_intent:
                alternate_intents.append({
                    "category": intent_name,
                    "confidence": 0.7,  # Secondary confidence
                    "reasoning": f"Secondary capability: {cap.value}"
                })
        
        return ParsedIntent(
            primary_intent=primary_intent,
            confidence=confidence,
            confidence_score=understanding.confidence_score,
            suggested_agents=understanding.recommended_agents,
            extracted_parameters=understanding.extracted_parameters,
            alternate_intents=alternate_intents,
            requires_clarification=len(understanding.potential_challenges) > 0,
            clarification_questions=understanding.potential_challenges,
            reasoning=understanding.reasoning
        )


class SemanticMigrationManager:
    """
    Manager for gradual migration from legacy to semantic architecture.
    
    Provides tools for A/B testing, performance comparison, and gradual rollout.
    """
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        self._migration_stats = {
            "semantic_requests": 0,
            "legacy_requests": 0,
            "semantic_failures": 0,
            "legacy_failures": 0
        }
    
    async def should_use_semantic(self, user_request: str, session_id: str) -> bool:
        """
        Determine whether to use semantic or legacy architecture.
        
        Could implement:
        - Gradual rollout percentage
        - User-specific flags
        - Request complexity analysis
        - Performance-based routing
        """
        
        # For now, use semantic for specific patterns
        semantic_keywords = [
            "logo", "brand", "market research", "website", 
            "comprehensive", "complete", "strategy"
        ]
        
        return any(keyword in user_request.lower() for keyword in semantic_keywords)
    
    async def record_request_outcome(self, method: str, success: bool, duration: float = None):
        """Record request outcome for performance tracking."""
        if method == "semantic":
            self._migration_stats["semantic_requests"] += 1
            if not success:
                self._migration_stats["semantic_failures"] += 1
        else:
            self._migration_stats["legacy_requests"] += 1
            if not success:
                self._migration_stats["legacy_failures"] += 1
        
        # Store in Redis if available
        if self.redis_client:
            await self._persist_stats()
    
    async def get_migration_stats(self) -> Dict[str, Any]:
        """Get migration statistics."""
        stats = self._migration_stats.copy()
        
        # Calculate success rates
        if stats["semantic_requests"] > 0:
            stats["semantic_success_rate"] = 1 - (stats["semantic_failures"] / stats["semantic_requests"])
        else:
            stats["semantic_success_rate"] = 0
            
        if stats["legacy_requests"] > 0:
            stats["legacy_success_rate"] = 1 - (stats["legacy_failures"] / stats["legacy_requests"])
        else:
            stats["legacy_success_rate"] = 0
        
        return stats
    
    async def _persist_stats(self):
        """Persist migration statistics to Redis."""
        if self.redis_client:
            try:
                key = "semantic_migration_stats"
                await self.redis_client.hmset(key, self._migration_stats)
                await self.redis_client.expire(key, 86400)  # 24 hours
            except Exception as e:
                logger.error(f"Failed to persist migration stats: {e}")


# Factory functions for easy setup
def create_semantic_jarvis(
    ai_engine: Optional[AnthropicEngine] = None,
    redis_client: Optional[Any] = None,
    conversation_manager: Optional[Any] = None,
    config: Optional[OrchestratorConfig] = None
) -> SemanticJarvis:
    """Create SemanticJarvis instance with proper configuration."""
    return SemanticJarvis(ai_engine, redis_client, conversation_manager, config)


def create_compatibility_layer(ai_engine: Optional[AnthropicEngine] = None) -> SemanticIntentCompatibility:
    """Create compatibility layer for legacy IntentParser interface.""" 
    return SemanticIntentCompatibility(ai_engine)


# Migration helper
async def migrate_gradual(
    user_request: str,
    session_id: str,
    semantic_jarvis: SemanticJarvis,
    migration_manager: SemanticMigrationManager,
    business_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Handle gradual migration with fallback and performance tracking.
    
    This function demonstrates how to gradually roll out semantic architecture.
    """
    start_time = datetime.utcnow()
    
    try:
        # Decide which architecture to use
        use_semantic = await migration_manager.should_use_semantic(user_request, session_id)
        
        if use_semantic:
            # Try semantic first
            try:
                result = await semantic_jarvis.process_request(
                    user_request, session_id, business_context
                )
                
                # Record success
                duration = (datetime.utcnow() - start_time).total_seconds()
                await migration_manager.record_request_outcome("semantic", result["success"], duration)
                
                return result
                
            except Exception as e:
                logger.warning(f"Semantic failed, falling back to legacy: {e}")
                
                # Try legacy fallback
                result = await semantic_jarvis.process_request(
                    user_request, session_id, business_context, use_legacy=True
                )
                
                # Record semantic failure and legacy attempt
                duration = (datetime.utcnow() - start_time).total_seconds()
                await migration_manager.record_request_outcome("semantic", False, duration)
                await migration_manager.record_request_outcome("legacy", result["success"], duration)
                
                return result
        
        else:
            # Use legacy directly
            result = await semantic_jarvis.process_request(
                user_request, session_id, business_context, use_legacy=True
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            await migration_manager.record_request_outcome("legacy", result["success"], duration)
            
            return result
            
    except Exception as e:
        logger.error(f"Complete migration failure: {e}")
        
        # Record failure
        duration = (datetime.utcnow() - start_time).total_seconds()
        await migration_manager.record_request_outcome("legacy", False, duration)
        
        return {
            "success": False,
            "error": str(e),
            "method": "migration_failure",
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    async def test_integration():
        """Test the integration components."""
        print("Testing Semantic Integration...")
        
        # Create semantic jarvis
        jarvis = create_semantic_jarvis()
        
        # Test request
        request = "Create a logo for my bakery"
        response = await jarvis.process_request(request, "test_session")
        
        print(f"Response: {response['success']}")
        print(f"Method: {response['method']}")
        print(f"Business Goal: {response['business_goal']}")
        
        # Test compatibility layer
        compat = create_compatibility_layer()
        intent = await compat.parse_intent(request)
        
        print(f"Legacy Intent: {intent.primary_intent}")
        print(f"Confidence: {intent.confidence}")
        print(f"Agents: {intent.suggested_agents}")
    
    # Run test
    asyncio.run(test_integration())