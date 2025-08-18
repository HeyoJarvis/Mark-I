"""
AgentPool manages a collection of persistent agents with health monitoring and load balancing.

Features:
- Agent lifecycle management (start/stop/restart)
- Health monitoring and auto-recovery
- Load balancing across agent instances
- Task routing and distribution
- Agent registration and discovery
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .base_agent import PersistentAgent, AgentState, AgentHealth, TaskRequest, TaskResponse


class PoolStatus(str, Enum):
    """Agent pool operational status."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"  # Some agents unhealthy
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent_id: str
    agent_class: Type[PersistentAgent]
    config: Dict[str, Any]
    supported_tasks: List[str]
    max_instances: int = 1
    auto_restart: bool = True
    priority: int = 1


@dataclass
class PoolHealth:
    """Overall pool health status."""
    status: PoolStatus
    total_agents: int
    healthy_agents: int
    busy_agents: int
    error_agents: int
    total_tasks_processed: int
    successful_tasks: int
    failed_tasks: int
    average_response_time_ms: float
    last_updated: datetime
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_tasks_processed == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks_processed) * 100
    
    @property
    def health_percentage(self) -> float:
        """Calculate overall health percentage."""
        if self.total_agents == 0:
            return 0.0
        return (self.healthy_agents / self.total_agents) * 100


class AgentPool:
    """
    Manages a pool of persistent agents with health monitoring and load balancing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent pool."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Agent management
        self.registrations: Dict[str, AgentRegistration] = {}
        self.agents: Dict[str, PersistentAgent] = {}  # agent_id -> agent instance
        self.agent_health: Dict[str, AgentHealth] = {}
        
        # Task routing
        self.task_type_mapping: Dict[str, List[str]] = {}  # task_type -> [agent_ids]
        
        # Pool state
        self.status = PoolStatus.INITIALIZING
        self.pool_health = PoolHealth(
            status=self.status,
            total_agents=0,
            healthy_agents=0,
            busy_agents=0,
            error_agents=0,
            total_tasks_processed=0,
            successful_tasks=0,
            failed_tasks=0,
            average_response_time_ms=0.0,
            last_updated=datetime.utcnow()
        )
        
        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Callbacks
        self.health_callback: Optional[Callable] = None
        self.agent_status_callback: Optional[Callable] = None
        
        self.logger.info("AgentPool initialized")
    
    def register_agent(
        self,
        agent_id: str,
        agent_class: Type[PersistentAgent],
        config: Dict[str, Any],
        supported_tasks: List[str],
        max_instances: int = 1,
        auto_restart: bool = True,
        priority: int = 1
    ):
        """Register an agent type with the pool."""
        registration = AgentRegistration(
            agent_id=agent_id,
            agent_class=agent_class,
            config=config,
            supported_tasks=supported_tasks,
            max_instances=max_instances,
            auto_restart=auto_restart,
            priority=priority
        )
        
        self.registrations[agent_id] = registration
        
        # Update task type mapping
        for task_type in supported_tasks:
            if task_type not in self.task_type_mapping:
                self.task_type_mapping[task_type] = []
            if agent_id not in self.task_type_mapping[task_type]:
                self.task_type_mapping[task_type].append(agent_id)
        
        self.logger.info(f"Registered agent: {agent_id} supporting {supported_tasks}")
    
    async def start_pool(self):
        """Start all registered agents in the pool."""
        self.logger.info("Starting agent pool")
        self.status = PoolStatus.INITIALIZING
        
        # Start all registered agents
        start_tasks = []
        for agent_id, registration in self.registrations.items():
            for instance in range(registration.max_instances):
                instance_id = f"{agent_id}_{instance}" if registration.max_instances > 1 else agent_id
                start_tasks.append(self._start_agent(instance_id, registration))
        
        # Start agents concurrently
        if start_tasks:
            results = await asyncio.gather(*start_tasks, return_exceptions=True)
            
            # Check for startup errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to start agent: {result}")
        
        # Start health monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_pool_health())
        
        # Update status
        self.status = PoolStatus.RUNNING
        await self._update_pool_health()
        
        self.logger.info(f"Agent pool started with {len(self.agents)} agents")
    
    async def stop_pool(self, timeout: float = 30.0):
        """Stop all agents in the pool."""
        self.logger.info("Stopping agent pool")
        self.status = PoolStatus.STOPPING
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop all agents
        stop_tasks = []
        for agent_id, agent in self.agents.items():
            stop_tasks.append(agent.stop(timeout=timeout / len(self.agents)))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.agents.clear()
        self.agent_health.clear()
        self.status = PoolStatus.STOPPED
        
        self.logger.info("Agent pool stopped")
    
    async def submit_task(
        self,
        task_request: TaskRequest,
        preferred_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Submit a task to an appropriate agent.
        
        Args:
            task_request: Task to be processed
            preferred_agent: Preferred agent ID (optional)
            
        Returns:
            Agent ID that accepted the task, None if no agent available
        """
        # Find suitable agents for this task type
        suitable_agents = self._find_suitable_agents(task_request.task_type, preferred_agent)
        
        if not suitable_agents:
            self.logger.warning(f"No suitable agents found for task type: {task_request.task_type}")
            return None
        
        # Select best agent based on load balancing
        selected_agent_id = self._select_best_agent(suitable_agents)
        selected_agent = self.agents[selected_agent_id]
        
        # Submit task
        success = await selected_agent.submit_task(task_request)
        if success:
            self.logger.debug(f"Task {task_request.task_id} submitted to agent {selected_agent_id}")
            return selected_agent_id
        else:
            self.logger.warning(f"Failed to submit task {task_request.task_id} to agent {selected_agent_id}")
            return None
    
    async def get_pool_health(self) -> PoolHealth:
        """Get overall pool health status."""
        await self._update_pool_health()
        return self.pool_health
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent."""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        health = await agent.get_health()
        
        return {
            'agent_id': agent_id,
            'health': health,
            'info': agent.get_agent_info()
        }
    
    async def restart_agent(self, agent_id: str):
        """Restart a specific agent."""
        if agent_id not in self.agents:
            self.logger.warning(f"Agent {agent_id} not found for restart")
            return
        
        self.logger.info(f"Restarting agent {agent_id}")
        
        # Find registration
        base_agent_id = agent_id.split('_')[0]  # Handle instance IDs
        registration = self.registrations.get(base_agent_id)
        
        if not registration:
            self.logger.error(f"No registration found for agent {agent_id}")
            return
        
        # Stop current agent
        current_agent = self.agents[agent_id]
        await current_agent.stop()
        
        # Remove from tracking
        del self.agents[agent_id]
        self.agent_health.pop(agent_id, None)
        
        # Start new instance
        await self._start_agent(agent_id, registration)
        
        self.logger.info(f"Agent {agent_id} restarted successfully")
    
    def set_health_callback(self, callback: Callable[[PoolHealth], None]):
        """Set callback for pool health updates."""
        self.health_callback = callback
    
    def set_agent_status_callback(self, callback: Callable[[str, AgentHealth], None]):
        """Set callback for individual agent status updates."""
        self.agent_status_callback = callback
    
    async def _start_agent(self, agent_id: str, registration: AgentRegistration):
        """Start a single agent instance."""
        try:
            self.logger.debug(f"Starting agent {agent_id}")
            
            # Create agent instance
            agent = registration.agent_class(agent_id, registration.config)
            
            # Set callbacks
            agent.set_task_completed_callback(self._on_task_completed)
            agent.set_health_callback(self._on_agent_health_update)
            
            # Start agent
            await agent.start()
            
            # Add to pool
            self.agents[agent_id] = agent
            self.agent_health[agent_id] = await agent.get_health()
            
            self.logger.info(f"Agent {agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_id}: {e}")
            raise
    
    def _find_suitable_agents(self, task_type: str, preferred_agent: Optional[str] = None) -> List[str]:
        """Find agents suitable for the given task type."""
        if preferred_agent and preferred_agent in self.agents:
            # Check if preferred agent supports the task type
            agent = self.agents[preferred_agent]
            if task_type in agent.get_supported_task_types():
                return [preferred_agent]
        
        # Find all agents that support this task type
        suitable_agents = []
        agent_ids = self.task_type_mapping.get(task_type, [])
        
        for agent_id in agent_ids:
            # Check all instances of this agent type
            for instance_id in self.agents:
                if instance_id.startswith(agent_id):
                    health = self.agent_health.get(instance_id)
                    if health and health.state in [AgentState.READY, AgentState.BUSY]:
                        suitable_agents.append(instance_id)
        
        return suitable_agents
    
    def _select_best_agent(self, suitable_agents: List[str]) -> str:
        """Select the best agent based on load balancing."""
        if not suitable_agents:
            raise ValueError("No suitable agents available")
        
        if len(suitable_agents) == 1:
            return suitable_agents[0]
        
        # Load balancing - select agent with lowest current load
        best_agent = suitable_agents[0]
        best_score = float('inf')
        
        for agent_id in suitable_agents:
            agent = self.agents[agent_id]
            health = self.agent_health.get(agent_id)
            
            # Calculate load score (lower is better)
            queue_size = agent.task_queue.qsize()
            processing_tasks = len(agent.processing_tasks)
            
            # Factor in agent health and performance
            success_rate = health.success_rate if health else 0
            avg_time = health.average_processing_time_ms if health else 1000
            
            # Load score: queue + processing + time penalty - success bonus
            load_score = queue_size + processing_tasks + (avg_time / 1000) - (success_rate / 100)
            
            if load_score < best_score:
                best_score = load_score
                best_agent = agent_id
        
        return best_agent
    
    async def _monitor_pool_health(self):
        """Monitor pool health and handle agent failures."""
        while not self._shutdown_event.is_set():
            try:
                # Check each agent's health
                unhealthy_agents = []
                
                for agent_id, agent in self.agents.items():
                    health = await agent.get_health()
                    self.agent_health[agent_id] = health
                    
                    # Check if agent needs restart
                    if not health.is_healthy:
                        unhealthy_agents.append(agent_id)
                
                # Restart unhealthy agents if auto-restart is enabled
                for agent_id in unhealthy_agents:
                    base_agent_id = agent_id.split('_')[0]
                    registration = self.registrations.get(base_agent_id)
                    
                    if registration and registration.auto_restart:
                        self.logger.warning(f"Auto-restarting unhealthy agent: {agent_id}")
                        try:
                            await self.restart_agent(agent_id)
                        except Exception as e:
                            self.logger.error(f"Failed to auto-restart agent {agent_id}: {e}")
                
                # Update pool health
                await self._update_pool_health()
                
                # Wait before next health check
                await asyncio.sleep(15.0)  # Check every 15 seconds
                
            except Exception as e:
                self.logger.error(f"Error in pool health monitoring: {e}")
                await asyncio.sleep(5.0)
    
    async def _update_pool_health(self):
        """Update overall pool health status."""
        total_agents = len(self.agents)
        healthy_agents = 0
        busy_agents = 0
        error_agents = 0
        total_tasks = 0
        successful_tasks = 0
        failed_tasks = 0
        total_response_time = 0
        
        for health in self.agent_health.values():
            if health.state == AgentState.READY:
                healthy_agents += 1
            elif health.state == AgentState.BUSY:
                healthy_agents += 1
                busy_agents += 1
            elif health.state == AgentState.ERROR:
                error_agents += 1
            
            total_tasks += health.total_tasks_processed
            successful_tasks += health.successful_tasks
            failed_tasks += health.failed_tasks
            total_response_time += health.average_processing_time_ms
        
        # Calculate average response time
        avg_response_time = 0.0
        if len(self.agent_health) > 0:
            avg_response_time = total_response_time / len(self.agent_health)
        
        # Determine pool status
        if total_agents == 0:
            pool_status = PoolStatus.STOPPED
        elif error_agents > 0 or healthy_agents < total_agents * 0.8:
            pool_status = PoolStatus.DEGRADED
        else:
            pool_status = PoolStatus.RUNNING
        
        # Update pool health
        self.pool_health = PoolHealth(
            status=pool_status,
            total_agents=total_agents,
            healthy_agents=healthy_agents,
            busy_agents=busy_agents,
            error_agents=error_agents,
            total_tasks_processed=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            average_response_time_ms=avg_response_time,
            last_updated=datetime.utcnow()
        )
        
        # Call health callback
        if self.health_callback:
            try:
                await self.health_callback(self.pool_health)
            except Exception as e:
                self.logger.error(f"Error in health callback: {e}")
    
    async def _on_task_completed(self, agent_id: str, response: TaskResponse):
        """Handle task completion from agents."""
        self.logger.debug(f"Task {response.task_id} completed by agent {agent_id}")
        # This could trigger additional processing, metrics collection, etc.
    
    async def _on_agent_health_update(self, agent_id: str, health: AgentHealth):
        """Handle agent health updates."""
        self.agent_health[agent_id] = health
        
        # Call agent status callback
        if self.agent_status_callback:
            try:
                await self.agent_status_callback(agent_id, health)
            except Exception as e:
                self.logger.error(f"Error in agent status callback: {e}")


# Utility functions for agent pool management
async def create_standard_agent_pool(config: Dict[str, Any]) -> AgentPool:
    """Create a standard agent pool with common agents."""
    pool = AgentPool(config)
    
    # This will be populated with actual agent registrations
    # when we implement the specific persistent agents
    
    return pool