"""
Semantic Universal Orchestrator - Phase B Integration

This integrates the SemanticRequestParser with UniversalOrchestrator to provide:
1. Feature flag for old/new system toggle
2. Parallel execution for testing
3. Direct agent access with semantic understanding
4. Fallback to existing orchestrators when needed
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, Any, Optional, Union, Literal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import existing orchestrators (maintain compatibility)
from .universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig, RoutingIntent
from .branding_orchestration import BrandingOrchestrator
from .jarvis import Jarvis
from .orchestrator import HeyJarvisOrchestrator

# Import semantic components
from .semantic_request_parser import SemanticRequestParser, SemanticUnderstanding, ExecutionStrategy
from .semantic_orchestrator import SemanticOrchestrator, SemanticWorkflowState
from .semantic_integration import SemanticJarvis
from .semantic_state import SemanticStateManager, create_semantic_state_system

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class OrchestrationMode(str, Enum):
    """Orchestration execution modes."""
    LEGACY_ONLY = "legacy_only"        # Use only existing orchestrators
    SEMANTIC_ONLY = "semantic_only"    # Use only semantic architecture  
    PARALLEL_TEST = "parallel_test"    # Run both, compare results
    SEMANTIC_WITH_FALLBACK = "semantic_with_fallback"  # Semantic first, fallback to legacy
    GRADUAL_ROLLOUT = "gradual_rollout"  # Percentage-based rollout


@dataclass
class SemanticConfig:
    """Configuration for semantic features."""
    enabled: bool = False
    mode: OrchestrationMode = OrchestrationMode.LEGACY_ONLY
    rollout_percentage: float = 0.0  # 0.0 to 1.0
    bypass_orchestration: bool = True  # Skip orchestrator routing for direct agent access
    log_comparisons: bool = True
    fallback_timeout_seconds: float = 30.0


@dataclass  
class IntegrationResult:
    """Result from semantic integration."""
    success: bool
    method_used: str  # "semantic", "legacy", "parallel"
    semantic_result: Optional[Dict[str, Any]] = None
    legacy_result: Optional[Dict[str, Any]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    errors: Optional[Dict[str, str]] = None
    performance_metrics: Optional[Dict[str, float]] = None


class SemanticUniversalOrchestrator(UniversalOrchestrator):
    """
    Enhanced Universal Orchestrator with integrated semantic capabilities.
    
    Provides seamless transition from intent-based to semantic orchestration
    while maintaining full backward compatibility.
    """
    
    def __init__(self, config: UniversalOrchestratorConfig, semantic_config: Optional[SemanticConfig] = None):
        super().__init__(config)
        
        self.semantic_config = semantic_config or SemanticConfig()
        
        # Semantic components
        self.semantic_parser: Optional[SemanticRequestParser] = None
        self.semantic_orchestrator: Optional[SemanticOrchestrator] = None
        self.semantic_jarvis: Optional[SemanticJarvis] = None
        self.semantic_state_manager: Optional[SemanticStateManager] = None
        
        # Comparison tracking
        self.comparison_results: Dict[str, IntegrationResult] = {}
        
        logger.info(f"SemanticUniversalOrchestrator initialized with mode: {self.semantic_config.mode}")
    
    async def initialize(self) -> bool:
        """Initialize both legacy and semantic components."""
        # Initialize legacy components
        legacy_success = await super().initialize()
        if not legacy_success:
            logger.error("Failed to initialize legacy components")
            return False
        
        # Initialize semantic components if enabled
        if self.semantic_config.enabled:
            semantic_success = await self._initialize_semantic_components()
            if not semantic_success:
                logger.warning("Failed to initialize semantic components, falling back to legacy only")
                self.semantic_config.mode = OrchestrationMode.LEGACY_ONLY
        
        return True
    
    async def _initialize_semantic_components(self) -> bool:
        """Initialize semantic orchestration components."""
        try:
            # Use the same AI engine for consistency
            if self.ai_engine:
                self.semantic_parser = SemanticRequestParser(self.ai_engine)
                self.semantic_orchestrator = SemanticOrchestrator(
                    self.ai_engine, self.redis_client
                )
                self.semantic_jarvis = SemanticJarvis(
                    self.ai_engine, self.redis_client
                )
                self.semantic_state_manager, _ = create_semantic_state_system(self.redis_client)
                
                logger.info("Semantic components initialized successfully")
                return True
            else:
                logger.error("AI engine not available for semantic initialization")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize semantic components: {e}")
            return False
    
    async def process_query(
        self,
        user_query: str,
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None,
        force_mode: Optional[OrchestrationMode] = None
    ) -> IntegrationResult:
        """
        Process query with semantic integration and mode selection.
        
        Args:
            user_query: User's natural language request
            session_id: Session identifier
            user_context: Additional user context
            force_mode: Override default mode for testing
        
        Returns:
            IntegrationResult with execution details and results
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        # Determine execution mode
        execution_mode = force_mode or self._determine_execution_mode(user_query, session_id)
        
        logger.info(f"Processing query with mode: {execution_mode} - {user_query[:100]}...")
        
        try:
            if execution_mode == OrchestrationMode.LEGACY_ONLY:
                result = await self._process_legacy_only(user_query, session_id, user_context)
                
            elif execution_mode == OrchestrationMode.SEMANTIC_ONLY:
                result = await self._process_semantic_only(user_query, session_id, user_context)
                
            elif execution_mode == OrchestrationMode.PARALLEL_TEST:
                result = await self._process_parallel_test(user_query, session_id, user_context)
                
            elif execution_mode == OrchestrationMode.SEMANTIC_WITH_FALLBACK:
                result = await self._process_semantic_with_fallback(user_query, session_id, user_context)
                
            elif execution_mode == OrchestrationMode.GRADUAL_ROLLOUT:
                result = await self._process_gradual_rollout(user_query, session_id, user_context)
                
            else:
                raise ValueError(f"Unknown execution mode: {execution_mode}")
            
            # Add performance metrics
            duration = (datetime.now() - start_time).total_seconds()
            result.performance_metrics = {
                "total_duration": duration,
                "execution_mode": execution_mode.value
            }
            
            # Store comparison data if enabled
            if self.semantic_config.log_comparisons:
                self.comparison_results[request_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return IntegrationResult(
                success=False,
                method_used="error",
                errors={"main_error": str(e)},
                performance_metrics={"duration": (datetime.now() - start_time).total_seconds()}
            )
    
    def _determine_execution_mode(self, user_query: str, session_id: str) -> OrchestrationMode:
        """Determine which execution mode to use."""
        if not self.semantic_config.enabled:
            return OrchestrationMode.LEGACY_ONLY
        
        # Use configured mode
        mode = self.semantic_config.mode
        
        # Apply rollout percentage for gradual rollout
        if mode == OrchestrationMode.GRADUAL_ROLLOUT:
            # Simple hash-based rollout (consistent per session)
            import hashlib
            hash_value = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
            rollout_bucket = (hash_value % 100) / 100.0
            
            if rollout_bucket < self.semantic_config.rollout_percentage:
                return OrchestrationMode.SEMANTIC_WITH_FALLBACK
            else:
                return OrchestrationMode.LEGACY_ONLY
        
        return mode
    
    async def _process_legacy_only(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> IntegrationResult:
        """Process with legacy orchestration only."""
        try:
            legacy_result = await super().process_query(user_query, session_id, user_context)
            
            return IntegrationResult(
                success=True,
                method_used="legacy",
                legacy_result=legacy_result
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                method_used="legacy",
                errors={"legacy_error": str(e)}
            )
    
    async def _process_semantic_only(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> IntegrationResult:
        """Process with semantic orchestration only."""
        if not self.semantic_jarvis:
            return IntegrationResult(
                success=False,
                method_used="semantic",
                errors={"semantic_error": "Semantic components not initialized"}
            )
        
        try:
            semantic_result = await self.semantic_jarvis.process_request(
                user_query, session_id, user_context
            )
            
            return IntegrationResult(
                success=semantic_result.get("success", False),
                method_used="semantic",
                semantic_result=semantic_result
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                method_used="semantic",
                errors={"semantic_error": str(e)}
            )
    
    async def _process_parallel_test(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> IntegrationResult:
        """Process with both systems in parallel for comparison."""
        if not self.semantic_jarvis:
            # Fall back to legacy only
            return await self._process_legacy_only(user_query, session_id, user_context)
        
        try:
            # Run both systems in parallel
            legacy_task = asyncio.create_task(
                self._safe_legacy_call(user_query, session_id, user_context)
            )
            semantic_task = asyncio.create_task(
                self._safe_semantic_call(user_query, session_id, user_context)
            )
            
            # Wait for both to complete
            legacy_result, semantic_result = await asyncio.gather(
                legacy_task, semantic_task, return_exceptions=True
            )
            
            # Process results
            comparison_data = self._compare_results(legacy_result, semantic_result)
            
            # Determine primary result (prefer semantic if both successful)
            primary_result = semantic_result if isinstance(semantic_result, dict) and semantic_result.get("success") else legacy_result
            success = isinstance(primary_result, dict) and primary_result.get("success", False)
            
            return IntegrationResult(
                success=success,
                method_used="parallel",
                legacy_result=legacy_result if isinstance(legacy_result, dict) else None,
                semantic_result=semantic_result if isinstance(semantic_result, dict) else None,
                comparison_data=comparison_data,
                errors=self._extract_errors(legacy_result, semantic_result)
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                method_used="parallel",
                errors={"parallel_error": str(e)}
            )
    
    async def _process_semantic_with_fallback(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> IntegrationResult:
        """Process with semantic first, fallback to legacy on failure."""
        if not self.semantic_jarvis:
            return await self._process_legacy_only(user_query, session_id, user_context)
        
        # Try semantic first
        semantic_result = await self._safe_semantic_call(user_query, session_id, user_context)
        
        if isinstance(semantic_result, dict) and semantic_result.get("success"):
            return IntegrationResult(
                success=True,
                method_used="semantic",
                semantic_result=semantic_result
            )
        
        # Fallback to legacy
        logger.info("Semantic processing failed, falling back to legacy")
        legacy_result = await self._safe_legacy_call(user_query, session_id, user_context)
        
        return IntegrationResult(
            success=isinstance(legacy_result, dict) and legacy_result.get("success", False),
            method_used="fallback_to_legacy",
            legacy_result=legacy_result if isinstance(legacy_result, dict) else None,
            semantic_result=semantic_result if isinstance(semantic_result, dict) else None,
            errors={"semantic_failed": "Semantic processing failed, used legacy fallback"}
        )
    
    async def _process_gradual_rollout(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> IntegrationResult:
        """Process with gradual rollout logic."""
        # This is handled in _determine_execution_mode
        # Should not reach here, but fallback to semantic with fallback
        return await self._process_semantic_with_fallback(user_query, session_id, user_context)
    
    async def _safe_legacy_call(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> Union[Dict[str, Any], Exception]:
        """Safely call legacy orchestrator."""
        try:
            return await super().process_query(user_query, session_id, user_context)
        except Exception as e:
            logger.error(f"Legacy processing failed: {e}")
            return e
    
    async def _safe_semantic_call(
        self, user_query: str, session_id: str, user_context: Optional[Dict[str, Any]]
    ) -> Union[Dict[str, Any], Exception]:
        """Safely call semantic orchestrator."""
        try:
            return await self.semantic_jarvis.process_request(user_query, session_id, user_context)
        except Exception as e:
            logger.error(f"Semantic processing failed: {e}")
            return e
    
    def _compare_results(self, legacy_result: Any, semantic_result: Any) -> Dict[str, Any]:
        """Compare results from both systems."""
        comparison = {
            "both_successful": False,
            "results_similar": False,
            "performance_difference": None,
            "confidence_comparison": None
        }
        
        # Check if both succeeded
        legacy_success = isinstance(legacy_result, dict) and legacy_result.get("success", False)
        semantic_success = isinstance(semantic_result, dict) and semantic_result.get("success", False)
        
        comparison["both_successful"] = legacy_success and semantic_success
        
        if comparison["both_successful"]:
            # Compare performance
            legacy_duration = legacy_result.get("duration")
            semantic_duration = semantic_result.get("duration") 
            
            if legacy_duration and semantic_duration:
                comparison["performance_difference"] = semantic_duration - legacy_duration
            
            # Compare confidence/quality
            semantic_confidence = semantic_result.get("confidence", 0)
            comparison["confidence_comparison"] = semantic_confidence
            
            # Rough similarity check (could be enhanced)
            legacy_agents = legacy_result.get("agents_used", [])
            semantic_agents = semantic_result.get("agents_used", [])
            
            if legacy_agents and semantic_agents:
                # Check if similar agents were selected
                overlap = set(legacy_agents) & set(semantic_agents)
                similarity = len(overlap) / max(len(legacy_agents), len(semantic_agents))
                comparison["results_similar"] = similarity > 0.5
        
        return comparison
    
    def _extract_errors(self, *results) -> Optional[Dict[str, str]]:
        """Extract errors from results."""
        errors = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors[f"system_{i}_error"] = str(result)
            elif isinstance(result, dict) and not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                errors[f"system_{i}_error"] = error_msg
        
        return errors if errors else None
    
    async def get_comparison_stats(self) -> Dict[str, Any]:
        """Get statistics from parallel comparisons."""
        if not self.comparison_results:
            return {"message": "No comparison data available"}
        
        total_comparisons = len(self.comparison_results)
        semantic_successes = sum(1 for r in self.comparison_results.values() 
                                if r.semantic_result and r.semantic_result.get("success"))
        legacy_successes = sum(1 for r in self.comparison_results.values() 
                             if r.legacy_result and r.legacy_result.get("success"))
        
        both_successful = sum(1 for r in self.comparison_results.values() 
                            if r.comparison_data and r.comparison_data.get("both_successful"))
        
        return {
            "total_comparisons": total_comparisons,
            "semantic_success_rate": semantic_successes / total_comparisons if total_comparisons > 0 else 0,
            "legacy_success_rate": legacy_successes / total_comparisons if total_comparisons > 0 else 0,
            "both_successful_rate": both_successful / total_comparisons if total_comparisons > 0 else 0,
            "method_distribution": {
                result.method_used: sum(1 for r in self.comparison_results.values() if r.method_used == result.method_used)
                for result in self.comparison_results.values()
            }
        }
    
    async def set_semantic_mode(self, mode: OrchestrationMode, rollout_percentage: float = 0.0):
        """Update semantic configuration at runtime."""
        self.semantic_config.mode = mode
        self.semantic_config.rollout_percentage = rollout_percentage
        self.semantic_config.enabled = mode != OrchestrationMode.LEGACY_ONLY
        
        logger.info(f"Updated semantic mode to {mode} with rollout {rollout_percentage:.1%}")
        
        # Initialize semantic components if not already done
        if self.semantic_config.enabled and not self.semantic_jarvis:
            await self._initialize_semantic_components()


# Factory functions for easy setup
def create_semantic_universal_orchestrator(
    config: UniversalOrchestratorConfig,
    semantic_mode: OrchestrationMode = OrchestrationMode.LEGACY_ONLY,
    rollout_percentage: float = 0.0
) -> SemanticUniversalOrchestrator:
    """Create SemanticUniversalOrchestrator with specified mode."""
    semantic_config = SemanticConfig(
        enabled=(semantic_mode != OrchestrationMode.LEGACY_ONLY),
        mode=semantic_mode,
        rollout_percentage=rollout_percentage
    )
    
    return SemanticUniversalOrchestrator(config, semantic_config)


# Example usage and testing
if __name__ == "__main__":
    async def test_integration():
        """Test the semantic integration."""
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        # Create config (you'll need to adapt to your actual config structure)
        config = UniversalOrchestratorConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            redis_url="redis://localhost:6379"
        )
        
        # Create semantic orchestrator in parallel test mode
        orchestrator = create_semantic_universal_orchestrator(
            config, 
            OrchestrationMode.PARALLEL_TEST
        )
        
        await orchestrator.initialize()
        
        # Test requests
        test_requests = [
            "Create a logo for my coffee shop",
            "I need market research for electric vehicles"
        ]
        
        for request in test_requests:
            print(f"\nTesting: {request}")
            result = await orchestrator.process_query(request, "test_session")
            print(f"Success: {result.success}")
            print(f"Method: {result.method_used}")
            if result.comparison_data:
                print(f"Both successful: {result.comparison_data['both_successful']}")
        
        # Get comparison stats
        stats = await orchestrator.get_comparison_stats()
        print(f"\nComparison Stats: {stats}")
    
    # Run test
    asyncio.run(test_integration())