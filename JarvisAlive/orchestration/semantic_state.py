"""
Semantic State Management - Context preservation throughout execution

This module manages state with semantic understanding, ensuring that business context
and user intent are preserved and enriched throughout the orchestration flow.
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

import redis.asyncio as redis
from pydantic import BaseModel, Field

from .semantic_request_parser import SemanticUnderstanding, CapabilityCategory, ExecutionStrategy

logger = logging.getLogger(__name__)


class SemanticContextType(str, Enum):
    """Types of semantic context to preserve."""
    BUSINESS_INTENT = "business_intent"      # Core business goals and objectives
    USER_PREFERENCES = "user_preferences"    # User's stated preferences and style
    DOMAIN_KNOWLEDGE = "domain_knowledge"    # Industry/domain specific context
    EXECUTION_CONTEXT = "execution_context"  # How the request should be executed
    RESULT_CONTEXT = "result_context"        # Context about generated results


@dataclass
class SemanticContext:
    """Rich semantic context that flows through the orchestration."""
    # Core understanding
    business_goal: str
    user_intent_summary: str
    domain: Optional[str] = None
    
    # Detailed context
    business_context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    execution_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Capability and agent context
    required_capabilities: List[CapabilityCategory] = field(default_factory=list)
    selected_agents: List[str] = field(default_factory=list)
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SINGLE_AGENT
    
    # Dynamic context (updated during execution)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    context_evolution: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_evolution_entry(self, change_type: str, description: str, data: Dict[str, Any] = None):
        """Track how context evolves during execution."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "change_type": change_type,
            "description": description,
            "data": data or {}
        }
        self.context_evolution.append(entry)
        self.updated_at = datetime.utcnow()
    
    def update_from_agent_result(self, agent_id: str, result: Dict[str, Any]):
        """Update context based on agent result."""
        self.intermediate_results[agent_id] = result
        
        # Extract learnings that might influence future agents
        if "preferences" in result:
            self.learned_preferences.update(result["preferences"])
        
        if "context_updates" in result:
            self.business_context.update(result["context_updates"])
        
        self.add_evolution_entry(
            "agent_result",
            f"Updated context from {agent_id} execution",
            {"agent_id": agent_id, "result_keys": list(result.keys())}
        )
    
    def to_agent_context(self, agent_id: str, capability: CapabilityCategory) -> Dict[str, Any]:
        """Generate rich context for agent execution."""
        return {
            # Core request info
            "original_request": f"Business Goal: {self.business_goal}",
            "business_goal": self.business_goal,
            "user_intent": self.user_intent_summary,
            
            # Rich context
            "business_context": self.business_context,
            "user_preferences": {**self.user_preferences, **self.learned_preferences},
            "execution_preferences": self.execution_preferences,
            "domain": self.domain,
            
            # Agent-specific info
            "agent_id": agent_id,
            "assigned_capability": capability.value,
            "execution_strategy": self.execution_strategy.value,
            
            # Previous work and context
            "previous_results": self.intermediate_results,
            "context_evolution": self.context_evolution,
            
            # Metadata
            "context_created_at": self.created_at.isoformat(),
            "context_updated_at": self.updated_at.isoformat()
        }


class SemanticStateManager:
    """
    Manages semantic state persistence and retrieval with Redis backend.
    
    Ensures that semantic understanding and context flow seamlessly through
    all orchestration layers without loss of meaning or intent.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._local_cache: Dict[str, SemanticContext] = {}
    
    async def create_semantic_context(
        self, 
        workflow_id: str,
        session_id: str,
        understanding: SemanticUnderstanding
    ) -> SemanticContext:
        """Create initial semantic context from understanding."""
        context = SemanticContext(
            business_goal=understanding.business_goal,
            user_intent_summary=understanding.user_intent_summary,
            domain=understanding.business_domain,
            business_context=understanding.business_context,
            user_preferences=understanding.user_preferences,
            required_capabilities=understanding.primary_capabilities + understanding.secondary_capabilities,
            selected_agents=understanding.recommended_agents,
            execution_strategy=understanding.execution_strategy
        )
        
        # Store in cache and Redis
        self._local_cache[workflow_id] = context
        await self._persist_context(workflow_id, session_id, context)
        
        return context
    
    async def get_semantic_context(self, workflow_id: str) -> Optional[SemanticContext]:
        """Retrieve semantic context for workflow."""
        # Check local cache first
        if workflow_id in self._local_cache:
            return self._local_cache[workflow_id]
        
        # Load from Redis
        if self.redis_client:
            try:
                context_data = await self.redis_client.get(f"semantic_context:{workflow_id}")
                if context_data:
                    data = json.loads(context_data)
                    context = self._deserialize_context(data)
                    self._local_cache[workflow_id] = context
                    return context
            except Exception as e:
                logger.error(f"Failed to load semantic context: {e}")
        
        return None
    
    async def update_semantic_context(
        self, 
        workflow_id: str, 
        session_id: str,
        context: SemanticContext
    ):
        """Update semantic context with new information."""
        context.updated_at = datetime.utcnow()
        self._local_cache[workflow_id] = context
        await self._persist_context(workflow_id, session_id, context)
    
    async def enrich_context_from_agent_result(
        self,
        workflow_id: str,
        session_id: str, 
        agent_id: str,
        result: Dict[str, Any]
    ):
        """Enrich context based on agent execution result."""
        context = await self.get_semantic_context(workflow_id)
        if context:
            context.update_from_agent_result(agent_id, result)
            await self.update_semantic_context(workflow_id, session_id, context)
    
    async def get_agent_execution_context(
        self, 
        workflow_id: str,
        agent_id: str,
        capability: CapabilityCategory
    ) -> Dict[str, Any]:
        """Get rich context for agent execution."""
        context = await self.get_semantic_context(workflow_id)
        if context:
            return context.to_agent_context(agent_id, capability)
        
        # Fallback minimal context
        return {
            "agent_id": agent_id,
            "assigned_capability": capability.value,
            "business_goal": "Context not available",
            "business_context": {},
            "user_preferences": {},
            "previous_results": {}
        }
    
    async def track_context_evolution(
        self,
        workflow_id: str,
        session_id: str,
        change_type: str,
        description: str,
        data: Dict[str, Any] = None
    ):
        """Track how context evolves during execution."""
        context = await self.get_semantic_context(workflow_id)
        if context:
            context.add_evolution_entry(change_type, description, data)
            await self.update_semantic_context(workflow_id, session_id, context)
    
    async def get_context_summary(self, workflow_id: str) -> Dict[str, Any]:
        """Get summary of context for monitoring/debugging."""
        context = await self.get_semantic_context(workflow_id)
        if not context:
            return {"error": "Context not found"}
        
        return {
            "business_goal": context.business_goal,
            "domain": context.domain,
            "execution_strategy": context.execution_strategy.value,
            "selected_agents": context.selected_agents,
            "capabilities": [cap.value for cap in context.required_capabilities],
            "evolution_entries": len(context.context_evolution),
            "intermediate_results": list(context.intermediate_results.keys()),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
    
    async def cleanup_context(self, workflow_id: str):
        """Clean up context after workflow completion."""
        # Remove from local cache
        self._local_cache.pop(workflow_id, None)
        
        # Optionally archive in Redis instead of deleting
        if self.redis_client:
            try:
                # Move to archived key
                context_key = f"semantic_context:{workflow_id}"
                archive_key = f"archived_context:{workflow_id}"
                
                await self.redis_client.rename(context_key, archive_key)
                await self.redis_client.expire(archive_key, 86400 * 7)  # Keep archived for 7 days
                
            except Exception as e:
                logger.error(f"Failed to archive context: {e}")
    
    async def _persist_context(self, workflow_id: str, session_id: str, context: SemanticContext):
        """Persist context to Redis."""
        if not self.redis_client:
            return
        
        try:
            context_data = self._serialize_context(context)
            key = f"semantic_context:{workflow_id}"
            
            # Store with expiration (24 hours)
            await self.redis_client.set(key, json.dumps(context_data), ex=86400)
            
            # Also maintain session mapping
            session_key = f"session_workflows:{session_id}"
            await self.redis_client.sadd(session_key, workflow_id)
            await self.redis_client.expire(session_key, 86400)
            
        except Exception as e:
            logger.error(f"Failed to persist semantic context: {e}")
    
    def _serialize_context(self, context: SemanticContext) -> Dict[str, Any]:
        """Serialize context for storage."""
        data = asdict(context)
        
        # Convert enums to strings
        data["execution_strategy"] = context.execution_strategy.value
        data["required_capabilities"] = [cap.value for cap in context.required_capabilities]
        
        # Convert datetime to ISO strings
        data["created_at"] = context.created_at.isoformat()
        data["updated_at"] = context.updated_at.isoformat()
        
        return data
    
    def _deserialize_context(self, data: Dict[str, Any]) -> SemanticContext:
        """Deserialize context from storage."""
        # Convert strings back to enums
        data["execution_strategy"] = ExecutionStrategy(data["execution_strategy"])
        data["required_capabilities"] = [CapabilityCategory(cap) for cap in data["required_capabilities"]]
        
        # Convert ISO strings back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return SemanticContext(**data)


class SemanticContextMiddleware:
    """
    Middleware that ensures semantic context flows through all orchestration layers.
    
    Acts as a bridge between the orchestrator and agents to maintain semantic
    understanding without manual context passing.
    """
    
    def __init__(self, state_manager: SemanticStateManager):
        self.state_manager = state_manager
    
    async def prepare_agent_execution(
        self,
        workflow_id: str,
        agent_id: str, 
        capability: CapabilityCategory,
        base_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Prepare enriched context for agent execution."""
        # Get semantic context
        semantic_context = await self.state_manager.get_agent_execution_context(
            workflow_id, agent_id, capability
        )
        
        # Merge with base context if provided
        if base_context:
            semantic_context.update(base_context)
        
        # Track context preparation
        await self.state_manager.track_context_evolution(
            workflow_id,
            "unknown",  # session_id not available at this level
            "context_preparation",
            f"Prepared context for {agent_id} execution",
            {"agent_id": agent_id, "capability": capability.value}
        )
        
        return semantic_context
    
    async def process_agent_result(
        self,
        workflow_id: str,
        agent_id: str,
        result: Dict[str, Any]
    ):
        """Process agent result and update semantic context."""
        await self.state_manager.enrich_context_from_agent_result(
            workflow_id, "unknown", agent_id, result
        )
        
        # Extract semantic insights from result
        insights = self._extract_semantic_insights(result)
        if insights:
            await self.state_manager.track_context_evolution(
                workflow_id,
                "unknown", 
                "semantic_insights",
                f"Extracted insights from {agent_id} result",
                insights
            )
    
    def _extract_semantic_insights(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic insights from agent result."""
        insights = {}
        
        # Look for common insight patterns
        if "brand_strategy" in result:
            insights["brand_insights"] = result["brand_strategy"]
        
        if "market_analysis" in result:
            insights["market_insights"] = result["market_analysis"]
        
        if "recommendations" in result:
            insights["recommendations"] = result["recommendations"]
        
        if "next_steps" in result:
            insights["next_steps"] = result["next_steps"]
        
        return insights


# Factory function for easy setup
def create_semantic_state_system(redis_client: Optional[redis.Redis] = None) -> Tuple[SemanticStateManager, SemanticContextMiddleware]:
    """Create complete semantic state management system."""
    state_manager = SemanticStateManager(redis_client)
    middleware = SemanticContextMiddleware(state_manager)
    return state_manager, middleware


# Example usage
if __name__ == "__main__":
    async def test_semantic_state():
        from .semantic_request_parser import SemanticUnderstanding, CapabilityCategory, ExecutionStrategy
        
        # Create test understanding
        understanding = SemanticUnderstanding(
            business_goal="Create a coffee shop brand",
            user_intent_summary="User wants comprehensive branding for new coffee shop",
            primary_capabilities=[CapabilityCategory.BRAND_CREATION, CapabilityCategory.LOGO_GENERATION],
            secondary_capabilities=[],
            recommended_agents=["branding_agent", "logo_generation_agent"],
            execution_strategy=ExecutionStrategy.PARALLEL_MULTI,
            execution_plan={"strategy": "parallel"},
            extracted_parameters={"business_type": "coffee_shop"},
            business_context={"industry": "food_service", "target": "local_community"},
            user_preferences={"style": "modern", "colors": "warm_tones"},
            confidence_score=0.9,
            reasoning="Clear branding request with specific business context"
        )
        
        # Test state management
        state_manager, middleware = create_semantic_state_system()
        
        workflow_id = "test_workflow"
        session_id = "test_session"
        
        # Create context
        context = await state_manager.create_semantic_context(
            workflow_id, session_id, understanding
        )
        print(f"Created context for: {context.business_goal}")
        
        # Simulate agent execution
        agent_context = await middleware.prepare_agent_execution(
            workflow_id, "branding_agent", CapabilityCategory.BRAND_CREATION
        )
        print(f"Agent context keys: {list(agent_context.keys())}")
        
        # Simulate agent result
        mock_result = {
            "brand_strategy": {"mission": "Great coffee for everyone"},
            "recommendations": ["Focus on local community", "Emphasize quality"]
        }
        
        await middleware.process_agent_result(workflow_id, "branding_agent", mock_result)
        
        # Check context evolution
        summary = await state_manager.get_context_summary(workflow_id)
        print(f"Context summary: {json.dumps(summary, indent=2)}")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_semantic_state())