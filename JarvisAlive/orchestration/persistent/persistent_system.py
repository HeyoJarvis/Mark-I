"""
Persistent System Integration - Main entry point for the persistent agent system.

This module provides:
- System initialization and configuration
- Agent registration and pool management
- Message bus setup and coordination
- Concurrent orchestrator integration
- System health monitoring and statistics
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid

from .agent_pool import AgentPool, AgentRegistration, PoolHealth
from .message_bus import MessageBus, MessageType
from .concurrent_orchestrator import ConcurrentOrchestrator, ExecutionBatch, ApprovalRequest
from .agents.persistent_branding_agent import PersistentBrandingAgent
from .agents.persistent_market_research_agent import PersistentMarketResearchAgent
from .agents.persistent_logo_generation_agent import PersistentLogoGenerationAgent
from .agents.persistent_website_generation_agent import PersistentWebsiteGenerationAgent


class PersistentSystemConfig:
    """Configuration for the persistent agent system."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        anthropic_api_key: Optional[str] = None,
        max_agents_per_type: int = 3,
        agent_restart_enabled: bool = True,
        approval_timeout_minutes: int = 5,
        health_check_interval: int = 15,
        enable_message_bus: bool = True,
        skip_approvals: bool = True
    ):
        self.redis_url = redis_url
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.max_agents_per_type = max_agents_per_type
        self.agent_restart_enabled = agent_restart_enabled
        self.approval_timeout_minutes = approval_timeout_minutes
        self.health_check_interval = health_check_interval
        self.enable_message_bus = enable_message_bus
        self.skip_approvals = skip_approvals


class PersistentSystem:
    """
    Main persistent agent system that orchestrates all components.
    
    This system provides:
    - Concurrent multi-agent execution
    - Human-in-the-loop approval workflows
    - Real-time progress streaming
    - Inter-agent communication
    - Health monitoring and auto-recovery
    """
    
    def __init__(self, config: Optional[PersistentSystemConfig] = None):
        """Initialize the persistent agent system."""
        self.config = config or PersistentSystemConfig()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.agent_pool: Optional[AgentPool] = None
        self.message_bus: Optional[MessageBus] = None
        self.orchestrator: Optional[ConcurrentOrchestrator] = None
        
        # System state
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        
        # Callbacks for integration
        self.approval_request_callback: Optional[Callable] = None
        self.progress_update_callback: Optional[Callable] = None
        self.system_event_callback: Optional[Callable] = None
        
        # Statistics
        self.system_stats = {
            'total_batches': 0,
            'total_tasks': 0,
            'total_approvals': 0,
            'system_uptime_hours': 0
        }
        
        self.logger.info("PersistentSystem initialized")
    
    async def start(self):
        """Start the persistent agent system."""
        if self.is_running:
            self.logger.warning("System is already running")
            return
        
        self.logger.info("Starting PersistentSystem...")
        
        try:
            # Initialize message bus
            if self.config.enable_message_bus:
                await self._initialize_message_bus()
            
            # Initialize agent pool
            await self._initialize_agent_pool()
            
            # Initialize concurrent orchestrator
            await self._initialize_orchestrator()
            
            # Start all components
            if self.message_bus:
                await self.message_bus.connect()
            
            await self.agent_pool.start_pool()
            
            if self.orchestrator:
                await self.orchestrator.start()
            
            # Subscribe to system events
            await self._subscribe_to_system_events()
            
            self.is_running = True
            self.startup_time = datetime.utcnow()
            
            self.logger.info("PersistentSystem started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start PersistentSystem: {e}")
            await self.stop()
            raise
    
    async def stop(self, timeout: float = 30.0):
        """Stop the persistent agent system."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping PersistentSystem...")
        
        try:
            # Stop orchestrator
            if self.orchestrator:
                await self.orchestrator.stop(timeout / 3)
            
            # Stop agent pool
            if self.agent_pool:
                await self.agent_pool.stop_pool(timeout / 3)
            
            # Disconnect message bus
            if self.message_bus:
                await self.message_bus.disconnect()
            
            self.is_running = False
            self.logger.info("PersistentSystem stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping PersistentSystem: {e}")
    
    async def submit_concurrent_tasks(
        self,
        tasks: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        requires_approval: bool = True
    ) -> str:
        """
        Submit tasks for concurrent execution.
        
        Args:
            tasks: List of task dictionaries
            user_id: User identifier
            session_id: Session identifier
            workflow_id: Optional workflow identifier
            requires_approval: Whether tasks require human approval
            
        Returns:
            Batch ID for tracking
        """
        if not self.orchestrator:
            raise RuntimeError("System not started or orchestrator unavailable")
        
        batch_id = await self.orchestrator.submit_batch(
            tasks=tasks,
            user_id=user_id,
            session_id=session_id,
            workflow_id=workflow_id,
            requires_approval=requires_approval
        )
        
        self.system_stats['total_batches'] += 1
        self.system_stats['total_tasks'] += len(tasks)
        
        return batch_id
    
    async def approve_task(self, request_id: str, approved: bool, message: Optional[str] = None):
        """Approve or reject a task execution."""
        if not self.orchestrator:
            raise RuntimeError("System not started or orchestrator unavailable")
        
        await self.orchestrator.approve_task(request_id, approved, message)
        self.system_stats['total_approvals'] += 1
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch execution."""
        if not self.orchestrator:
            return None
        
        return await self.orchestrator.get_batch_status(batch_id)
    
    async def cancel_batch(self, batch_id: str):
        """Cancel a batch execution."""
        if not self.orchestrator:
            raise RuntimeError("System not started or orchestrator unavailable")
        
        await self.orchestrator.cancel_batch(batch_id)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        health_info = {
            'system_running': self.is_running,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'uptime_seconds': (
                (datetime.utcnow() - self.startup_time).total_seconds() 
                if self.startup_time else 0
            ),
            'components': {}
        }
        
        # Agent pool health
        if self.agent_pool:
            pool_health = await self.agent_pool.get_pool_health()
            health_info['components']['agent_pool'] = {
                'status': pool_health.status.value,
                'total_agents': pool_health.total_agents,
                'healthy_agents': pool_health.healthy_agents,
                'success_rate': pool_health.success_rate
            }
        
        # Message bus health
        if self.message_bus:
            bus_stats = self.message_bus.get_stats()
            health_info['components']['message_bus'] = {
                'connected': True,  # Simplified
                'messages_published': bus_stats['messages_published'],
                'messages_received': bus_stats['messages_received'],
                'active_subscriptions': bus_stats['active_subscriptions']
            }
        
        # Orchestrator health
        if self.orchestrator:
            orchestrator_stats = self.orchestrator.get_statistics()
            health_info['components']['orchestrator'] = orchestrator_stats
        
        # System statistics
        health_info['system_statistics'] = self.system_stats.copy()
        if self.startup_time:
            uptime_hours = (datetime.utcnow() - self.startup_time).total_seconds() / 3600
            health_info['system_statistics']['system_uptime_hours'] = round(uptime_hours, 2)
        
        return health_info
    
    def set_approval_callback(self, callback: Callable[[ApprovalRequest], Any]):
        """Set callback for approval requests."""
        self.approval_request_callback = callback
        if self.orchestrator:
            self.orchestrator.set_approval_callback(callback)
    
    def set_progress_callback(self, callback: Callable[[str, Dict[str, Any]], Any]):
        """Set callback for progress updates."""
        self.progress_update_callback = callback
        if self.orchestrator:
            self.orchestrator.set_progress_callback(callback)
    
    def set_system_event_callback(self, callback: Callable[[str, Dict[str, Any]], Any]):
        """Set callback for system events."""
        self.system_event_callback = callback
    
    def set_completion_callback(self, callback: Callable[[Any], Any]):
        """Set callback for batch completion."""
        if self.orchestrator:
            self.orchestrator.set_completion_callback(callback)
    
    async def _initialize_message_bus(self):
        """Initialize the message bus."""
        self.message_bus = MessageBus(redis_url=self.config.redis_url)
        self.logger.info("Message bus initialized")
    
    async def _initialize_agent_pool(self):
        """Initialize the agent pool with registered agents."""
        pool_config = {
            'health_check_interval': self.config.health_check_interval,
            'auto_restart': self.config.agent_restart_enabled
        }
        
        self.agent_pool = AgentPool(pool_config)
        
        # Register persistent agents
        await self._register_persistent_agents()
        
        self.logger.info("Agent pool initialized with registered agents")
    
    async def _register_persistent_agents(self):
        """Register all persistent agent types."""
        agent_config = {
            'anthropic_api_key': self.config.anthropic_api_key,
            'max_queue_size': 50,
            'health_check_interval': self.config.health_check_interval,
            'message_bus': self.message_bus  # Add message bus for event publishing
        }
        
        # Register PersistentBrandingAgent
        self.agent_pool.register_agent(
            agent_id="branding_agent",
            agent_class=PersistentBrandingAgent,
            config=agent_config,
            supported_tasks=[
                "brand_name_generation",
                "logo_prompt_creation", 
                "visual_identity_design",
                "brand_validation",
                "branding_consultation",
                "branding"  # Add high-level branding task type
            ],
            max_instances=self.config.max_agents_per_type,
            auto_restart=self.config.agent_restart_enabled,
            priority=1
        )
        
        # Register PersistentMarketResearchAgent
        self.agent_pool.register_agent(
            agent_id="market_research_agent",
            agent_class=PersistentMarketResearchAgent,
            config=agent_config,
            supported_tasks=[
                "market_opportunity_analysis",
                "competitive_analysis",
                "target_audience_research",
                "industry_trend_analysis",
                "revenue_estimation",
                "market_validation",
                "market_consultation",
                "business_strategy",
                "market_research"  # Add high-level market_research task type
            ],
            max_instances=self.config.max_agents_per_type,
            auto_restart=self.config.agent_restart_enabled,
            priority=1
        )
        
        # Register Advanced Email Orchestration Agent
        try:
            from departments.communication.semantic_advanced_orchestrator import SemanticAdvancedEmailOrchestrator
            self.agent_pool.register_agent(
                agent_id="advanced_email_orchestration_agent",
                agent_class=SemanticAdvancedEmailOrchestrator,
                config=agent_config,
                supported_tasks=[
                    "advanced_email_sequences", "ai_personalization", "send_time_optimization",
                    "reply_detection", "bounce_handling", "email_warming", "comprehensive_analytics",
                    "ab_testing", "reputation_management", "compliance_automation", "enterprise_features",
                    "create_sequence", "personalize_advanced", "optimize_timing", "setup_warming", "analytics"
                ],
                max_instances=self.config.max_agents_per_type,
                auto_restart=self.config.agent_restart_enabled,
                priority=1
            )
        except ImportError as e:
            self.logger.warning(f"Advanced Email Orchestration Agent not available: {e}")
        
        # Register PersistentLogoGenerationAgent
        self.agent_pool.register_agent(
            agent_id="logo_generation_agent",
            agent_class=PersistentLogoGenerationAgent,
            config=agent_config,
            supported_tasks=[
                "logo_generation",
                "logo_design",
                "visual_identity_creation",
                "brand_visualization"
            ],
            max_instances=self.config.max_agents_per_type,
            auto_restart=self.config.agent_restart_enabled,
            priority=2  # Lower priority since it can be resource intensive
        )
        
        # Register PersistentWebsiteGenerationAgent
        self.agent_pool.register_agent(
            agent_id="website_generation_agent", 
            agent_class=PersistentWebsiteGenerationAgent,
            config=agent_config,
            supported_tasks=[
                "website_generation",
                "website_design",
                "site_structure_creation",
                "web_content_generation",
                "landing_page_creation"
            ],
            max_instances=self.config.max_agents_per_type,
            auto_restart=self.config.agent_restart_enabled,
            priority=1
        )
        
        self.logger.info("Persistent agents registered successfully")
    
    async def _initialize_orchestrator(self):
        """Initialize the concurrent orchestrator."""
        if not self.agent_pool:
            raise RuntimeError("Agent pool must be initialized first")
        
        orchestrator_config = {
            'approval_timeout_minutes': self.config.approval_timeout_minutes,
            'skip_approvals': self.config.skip_approvals
        }
        
        self.orchestrator = ConcurrentOrchestrator(
            agent_pool=self.agent_pool,
            message_bus=self.message_bus,
            config=orchestrator_config
        )
        
        # Set callbacks if already configured
        if self.approval_request_callback:
            self.orchestrator.set_approval_callback(self.approval_request_callback)
        if self.progress_update_callback:
            self.orchestrator.set_progress_callback(self.progress_update_callback)
        
        self.logger.info("Concurrent orchestrator initialized")
    
    async def _subscribe_to_system_events(self):
        """Subscribe to system-wide events."""
        if not self.message_bus:
            return
        
        # Subscribe to system events
        await self.message_bus.subscribe(
            "orchestrator:*",
            self._handle_system_event
        )
        
        # Subscribe to agent events
        await self.message_bus.subscribe_pattern(
            "agent:*:*",
            self._handle_agent_event
        )
        
        self.logger.info("Subscribed to system events")
    
    async def _handle_system_event(self, message):
        """Handle system-wide events."""
        if self.system_event_callback:
            try:
                await self.system_event_callback("system", message.payload)
            except Exception as e:
                self.logger.error(f"Error in system event callback: {e}")
    
    async def _handle_agent_event(self, message):
        """Handle agent-specific events."""
        if self.system_event_callback:
            try:
                await self.system_event_callback("agent", message.payload)
            except Exception as e:
                self.logger.error(f"Error in agent event callback: {e}")

    async def submit_task(
        self,
        task: Dict[str, Any],
        user_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        requires_approval: bool = True
    ) -> Dict[str, str]:
        """Submit a single task for execution and return identifiers.
        
        Returns a dict with 'batch_id' and 'task_id'.
        """
        if 'task_id' not in task:
            task['task_id'] = str(uuid.uuid4())[:8]
        batch_id = await self.submit_concurrent_tasks(
            tasks=[task],
            user_id=user_id,
            session_id=session_id,
            workflow_id=workflow_id,
            requires_approval=requires_approval
        )
        return {'batch_id': batch_id, 'task_id': task['task_id']}

    async def await_task_result(
        self,
        task_id: str,
        poll_interval_seconds: float = 1.0,
        timeout_seconds: int = 600
    ) -> Optional[Dict[str, Any]]:
        """Poll for a specific task result until available or timeout."""
        if not self.orchestrator:
            raise RuntimeError("System not started or orchestrator unavailable")
        end_time = datetime.utcnow().timestamp() + timeout_seconds
        while datetime.utcnow().timestamp() < end_time:
            result = await self.orchestrator.get_task_result(task_id)
            if result:
                return result
            await asyncio.sleep(poll_interval_seconds)
        return None

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result if completed, without waiting."""
        if not self.orchestrator:
            return None
        return await self.orchestrator.get_task_result(task_id)


# Factory functions for easy system creation
def create_standard_persistent_system(
    redis_url: str = "redis://localhost:6379",
    anthropic_api_key: Optional[str] = None,
    max_agents_per_type: int = 2
) -> PersistentSystem:
    """Create a standard persistent system configuration."""
    config = PersistentSystemConfig(
        redis_url=redis_url,
        anthropic_api_key=anthropic_api_key,
        max_agents_per_type=max_agents_per_type,
        agent_restart_enabled=True,
        approval_timeout_minutes=5,
        health_check_interval=15,
        enable_message_bus=True
    )
    
    return PersistentSystem(config)


def create_development_persistent_system(
    anthropic_api_key: Optional[str] = None
) -> PersistentSystem:
    """Create a development-focused persistent system."""
    config = PersistentSystemConfig(
        redis_url="redis://localhost:6379",
        anthropic_api_key=anthropic_api_key,
        max_agents_per_type=1,  # Reduced for development
        agent_restart_enabled=True,
        approval_timeout_minutes=10,  # Longer timeout for debugging
        health_check_interval=30,  # Less frequent health checks
        enable_message_bus=True,
        skip_approvals=True
    )
    
    return PersistentSystem(config)


def create_production_persistent_system(
    redis_url: str,
    anthropic_api_key: str,
    max_agents_per_type: int = 5
) -> PersistentSystem:
    """Create a production-ready persistent system."""
    config = PersistentSystemConfig(
        redis_url=redis_url,
        anthropic_api_key=anthropic_api_key,
        max_agents_per_type=max_agents_per_type,
        agent_restart_enabled=True,
        approval_timeout_minutes=3,  # Shorter timeout for production
        health_check_interval=10,  # More frequent health checks
        enable_message_bus=True,
        skip_approvals=False
    )
    
    return PersistentSystem(config)


# Example usage and integration helpers
class SystemIntegrationHelper:
    """Helper class for integrating the persistent system with existing applications."""
    
    def __init__(self, persistent_system: PersistentSystem):
        self.system = persistent_system
        self.logger = logging.getLogger(f"{__name__}.integration")
    
    async def process_business_creation_workflow(
        self,
        business_idea: str,
        user_id: str,
        session_id: str,
        workflow_id: Optional[str] = None
    ) -> str:
        """Process a complete business creation workflow concurrently."""
        tasks = [
            {
                'task_type': 'market_opportunity_analysis',
                'description': f'Analyze market opportunity for: {business_idea}',
                'input_data': {
                    'business_idea': business_idea,
                    'industry': 'General',
                    'location': 'Global'
                },
                'priority': 1,
                'requires_approval': True
            },
            {
                'task_type': 'brand_name_generation',
                'description': f'Generate brand names for: {business_idea}',
                'input_data': {
                    'business_idea': business_idea,
                    'industry': 'General'
                },
                'priority': 1,
                'requires_approval': True,
                'dependencies': []  # Can run in parallel
            },
            {
                'task_type': 'competitive_analysis',
                'description': f'Analyze competition for: {business_idea}',
                'input_data': {
                    'business_idea': business_idea,
                    'industry': 'General'
                },
                'priority': 2,
                'requires_approval': True
            }
        ]
        
        batch_id = await self.system.submit_concurrent_tasks(
            tasks=tasks,
            user_id=user_id,
            session_id=session_id,
            workflow_id=workflow_id,
            requires_approval=True
        )
        
        self.logger.info(f"Business creation workflow submitted: batch_id={batch_id}")
        return batch_id
    
    async def monitor_workflow_progress(
        self,
        batch_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Monitor workflow progress until completion."""
        while True:
            status = await self.system.get_batch_status(batch_id)
            if not status:
                break
            
            if progress_callback:
                await progress_callback(status)
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            await asyncio.sleep(2.0)
        
        return status
    
    def create_approval_handler(self, auto_approve: bool = False) -> Callable:
        """Create an approval handler for development/testing."""
        async def approval_handler(approval_request: ApprovalRequest):
            self.logger.info(
                f"Approval request: {approval_request.request_id} - "
                f"Task: {approval_request.task.description}"
            )
            
            if auto_approve:
                # Auto-approve for testing
                await asyncio.sleep(1.0)  # Simulate human decision time
                await self.system.approve_task(approval_request.request_id, True, "Auto-approved")
            else:
                # In a real implementation, this would prompt the user
                self.logger.info("Waiting for manual approval...")
        
        return approval_handler