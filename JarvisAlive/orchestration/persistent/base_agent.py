"""
Base PersistentAgent class for long-running agent instances.

This class provides:
- Agent lifecycle management
- Health monitoring
- State persistence
- Message queue handling
- Graceful shutdown
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from .message_bus import MessageType


class AgentState(str, Enum):
    """Agent operational states."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class AgentHealth:
    """Agent health status information."""
    state: AgentState
    last_heartbeat: datetime
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_processing_time_ms: float = 0.0
    current_task_id: Optional[str] = None
    error_message: Optional[str] = None
    memory_usage_mb: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        if self.total_tasks_processed == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks_processed) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        # Agent is healthy if:
        # 1. State is READY or BUSY
        # 2. Recent heartbeat (within last 30 seconds)
        # 3. Success rate > 80% (if has processed tasks)
        recent_heartbeat = datetime.utcnow() - self.last_heartbeat < timedelta(seconds=30)
        good_state = self.state in [AgentState.READY, AgentState.BUSY]
        good_success_rate = self.total_tasks_processed == 0 or self.success_rate >= 80.0
        
        return recent_heartbeat and good_state and good_success_rate


@dataclass
class TaskRequest:
    """Request for agent to process a task."""
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    priority: int = 1
    timeout_seconds: int = 300
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())[:8]


@dataclass
class TaskResponse:
    """Response from agent after processing task."""
    task_id: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: int = 0
    completed_at: datetime = field(default_factory=datetime.utcnow)


class PersistentAgent(ABC):
    """
    Base class for persistent agents that run continuously.
    
    Features:
    - Async task processing
    - Health monitoring
    - Graceful shutdown
    - Message queue handling
    - State persistence
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the persistent agent."""
        self.agent_id = agent_id
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Agent state
        self.state = AgentState.INITIALIZING
        self.health = AgentHealth(
            state=self.state,
            last_heartbeat=datetime.utcnow()
        )
        
        # Task processing
        self.task_queue = asyncio.Queue(maxsize=self.config.get('max_queue_size', 100))
        self.current_task: Optional[TaskRequest] = None
        self.processing_tasks: Dict[str, TaskRequest] = {}
        
        # Event loop and shutdown
        self._shutdown_event = asyncio.Event()
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.task_completed_callback: Optional[Callable] = None
        self.health_callback: Optional[Callable] = None
        
        self.logger.info(f"PersistentAgent {agent_id} initialized")
    
    async def start(self):
        """Start the persistent agent."""
        if self._running:
            self.logger.warning(f"Agent {self.agent_id} is already running")
            return
        
        self.logger.info(f"Starting agent {self.agent_id}")
        self._running = True
        self.state = AgentState.READY
        self._update_health()
        
        # Start main processing loop
        self._main_task = asyncio.create_task(self._main_loop())
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor())
        
        # Call agent-specific initialization
        await self.on_start()
    
    async def stop(self, timeout: float = 10.0):
        """Stop the persistent agent gracefully."""
        if not self._running:
            return
        
        self.logger.info(f"Stopping agent {self.agent_id}")
        self.state = AgentState.SHUTTING_DOWN
        self._update_health()
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for main task to complete
        if self._main_task:
            try:
                await asyncio.wait_for(self._main_task, timeout=timeout)
            except asyncio.TimeoutError:
                self.logger.warning(f"Agent {self.agent_id} shutdown timeout, cancelling")
                self._main_task.cancel()
        
        self._running = False
        self.state = AgentState.STOPPED
        self._update_health()
        
        # Call agent-specific cleanup
        await self.on_stop()
        
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def submit_task(self, task_request: TaskRequest) -> bool:
        """Submit a task to the agent's queue."""
        if not self._running or self.state == AgentState.ERROR:
            self.logger.warning(f"Cannot submit task to agent {self.agent_id} in state {self.state}")
            return False
        
        try:
            # Add to queue (non-blocking)
            self.task_queue.put_nowait(task_request)
            self.logger.debug(f"Task {task_request.task_id} queued for agent {self.agent_id}")
            return True
        except asyncio.QueueFull:
            self.logger.warning(f"Task queue full for agent {self.agent_id}")
            return False
    
    async def get_health(self) -> AgentHealth:
        """Get current agent health status."""
        return self.health
    
    def set_task_completed_callback(self, callback: Callable[[str, TaskResponse], None]):
        """Set callback for when tasks complete."""
        self.task_completed_callback = callback
    
    def set_health_callback(self, callback: Callable[[str, AgentHealth], None]):
        """Set callback for health status updates."""
        self.health_callback = callback
    
    async def _main_loop(self):
        """Main processing loop for the agent."""
        self.logger.info(f"Agent {self.agent_id} main loop started")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Wait for task or shutdown signal
                    task_request = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0  # Check shutdown every second
                    )
                    
                    # Process the task
                    await self._process_task(task_request)
                    
                except asyncio.TimeoutError:
                    # No task received, continue loop
                    continue
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    self.state = AgentState.ERROR
                    self.health.error_message = str(e)
                    self._update_health()
                    
                    # Wait before retrying
                    await asyncio.sleep(5.0)
                    
                    # Reset to ready state
                    self.state = AgentState.READY
                    self.health.error_message = None
                    self._update_health()
        
        except Exception as e:
            self.logger.error(f"Fatal error in agent {self.agent_id}: {e}")
            self.state = AgentState.ERROR
            self.health.error_message = str(e)
            self._update_health()
        
        self.logger.info(f"Agent {self.agent_id} main loop ended")
    
    async def _process_task(self, task_request: TaskRequest):
        """Process a single task."""
        self.logger.debug(f"Processing task {task_request.task_id}")
        
        start_time = datetime.utcnow()
        self.state = AgentState.BUSY
        self.current_task = task_request
        self.health.current_task_id = task_request.task_id
        self._update_health()
        
        try:
            # Add to processing tasks
            self.processing_tasks[task_request.task_id] = task_request
            
            # Execute the actual task processing
            result_data = await asyncio.wait_for(
                self.process_task(task_request.task_type, task_request.input_data),
                timeout=task_request.timeout_seconds
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create successful response
            response = TaskResponse(
                task_id=task_request.task_id,
                success=True,
                result_data=result_data,
                processing_time_ms=int(processing_time)
            )
            
            # Update health metrics
            self.health.total_tasks_processed += 1
            self.health.successful_tasks += 1
            self._update_average_processing_time(processing_time)
            
            self.logger.debug(f"Task {task_request.task_id} completed successfully in {processing_time:.1f}ms")
            
        except asyncio.TimeoutError:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_msg = f"Task timeout after {task_request.timeout_seconds}s"
            
            response = TaskResponse(
                task_id=task_request.task_id,
                success=False,
                error_message=error_msg,
                processing_time_ms=int(processing_time)
            )
            
            self.health.total_tasks_processed += 1
            self.health.failed_tasks += 1
            
            self.logger.warning(f"Task {task_request.task_id} timed out")
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            response = TaskResponse(
                task_id=task_request.task_id,
                success=False,
                error_message=str(e),
                processing_time_ms=int(processing_time)
            )
            
            self.health.total_tasks_processed += 1
            self.health.failed_tasks += 1
            
            self.logger.error(f"Task {task_request.task_id} failed: {e}")
            
        finally:
            # Clean up
            self.processing_tasks.pop(task_request.task_id, None)
            self.current_task = None
            self.health.current_task_id = None
            self.state = AgentState.READY
            self._update_health()
            
            # Call completion callback
            if self.task_completed_callback:
                try:
                    await self.task_completed_callback(self.agent_id, response)
                except Exception as e:
                    self.logger.error(f"Error in task completion callback: {e}")
            
            # Publish task completion event to message bus (if available)
            try:
                # Try to get message bus from config
                message_bus = getattr(self, '_message_bus', None)
                if not message_bus and hasattr(self, 'config') and self.config:
                    message_bus = self.config.get('message_bus')
                
                if message_bus:
                    # Publish completion event
                    topic = f"agent:{self.agent_id}:tasks"
                    
                    # Convert datetime objects to strings for JSON serialization
                    sanitized_result_data = self._sanitize_for_json(response.result_data) if response.result_data else {}
                    
                    await message_bus.publish(
                        topic=topic,
                        message_type=MessageType.TASK_COMPLETED if response.success else MessageType.TASK_FAILED,
                        source=self.agent_id,
                        payload={
                            'task_id': task_request.task_id,
                            'success': response.success,
                            'result_data': sanitized_result_data,
                            'error_message': response.error_message,
                            'processing_time_ms': response.processing_time_ms,
                            'completed_at': response.completed_at.isoformat()
                        }
                    )
                    self.logger.debug(f"Published completion event for task {task_request.task_id}")
            except Exception as e:
                self.logger.debug(f"Could not publish completion event: {e}")
            
            # Call task callback if provided
            if task_request.callback:
                try:
                    await task_request.callback(response)
                except Exception as e:
                    self.logger.error(f"Error in task callback: {e}")
    
    async def _health_monitor(self):
        """Monitor agent health and send periodic updates."""
        while not self._shutdown_event.is_set():
            try:
                # Update heartbeat
                self.health.last_heartbeat = datetime.utcnow()
                
                # Update memory usage (simplified)
                import psutil
                import os
                process = psutil.Process(os.getpid())
                self.health.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                
                # Call health callback
                if self.health_callback:
                    try:
                        await self.health_callback(self.agent_id, self.health)
                    except Exception as e:
                        self.logger.error(f"Error in health callback: {e}")
                
                # Wait before next health check
                await asyncio.sleep(10.0)  # Health check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(5.0)
    
    def _update_health(self):
        """Update health status."""
        self.health.state = self.state
        self.health.last_heartbeat = datetime.utcnow()
    
    def _update_average_processing_time(self, processing_time_ms: float):
        """Update running average of processing time."""
        if self.health.total_tasks_processed == 1:
            self.health.average_processing_time_ms = processing_time_ms
        else:
            # Running average
            total_tasks = self.health.total_tasks_processed
            current_avg = self.health.average_processing_time_ms
            self.health.average_processing_time_ms = (
                (current_avg * (total_tasks - 1)) + processing_time_ms
            ) / total_tasks
    
    def _sanitize_for_json(self, data):
        """Convert datetime objects and other non-JSON-serializable types to strings."""
        from datetime import datetime
        
        if isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool)):
            # Convert object to dict, then sanitize
            return self._sanitize_for_json(data.__dict__)
        else:
            return data
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    async def process_task(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific task. Must be implemented by subclasses."""
        pass
    
    async def on_start(self):
        """Called when agent starts. Override for custom initialization."""
        pass
    
    async def on_stop(self):
        """Called when agent stops. Override for custom cleanup."""
        pass
    
    def get_supported_task_types(self) -> List[str]:
        """Return list of supported task types. Override in subclasses."""
        return []
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information. Override for custom info."""
        return {
            'agent_id': self.agent_id,
            'state': self.state.value,
            'supported_tasks': self.get_supported_task_types(),
            'queue_size': self.task_queue.qsize(),
            'processing_tasks': len(self.processing_tasks),
            'health': self.health
        }