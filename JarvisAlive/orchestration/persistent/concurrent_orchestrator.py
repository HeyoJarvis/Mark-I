"""
Concurrent Orchestrator - Manages concurrent execution of multiple agents with HITL approval.

This orchestrator provides:
- Concurrent multi-agent task execution
- Human-in-the-loop approval gates
- Real-time progress streaming
- Inter-agent communication
- Load balancing and health monitoring
- Task routing and coordination
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .base_agent import PersistentAgent, TaskRequest, TaskResponse, AgentState
from .agent_pool import AgentPool, PoolHealth, AgentRegistration
from .message_bus import MessageBus, MessageType, Message, AgentMessageBusInterface


class ExecutionStatus(str, Enum):
    """Concurrent execution status."""
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Human approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ConcurrentTask:
    """Task for concurrent execution across multiple agents."""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    preferred_agent: Optional[str] = None
    priority: int = 1
    requires_approval: bool = True
    timeout_seconds: int = 300
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Execution tracking
    status: ExecutionStatus = ExecutionStatus.PENDING
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Human approval request for task execution."""
    request_id: str
    task: ConcurrentTask
    agent_info: Dict[str, Any]
    estimated_duration: int  # seconds
    risk_assessment: str
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    human_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None


@dataclass
class ExecutionBatch:
    """Batch of tasks for concurrent execution."""
    batch_id: str
    tasks: List[ConcurrentTask]
    user_id: str
    session_id: str
    workflow_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Progress tracking
    status: ExecutionStatus = ExecutionStatus.PENDING
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @property
    def progress_percentage(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def is_complete(self) -> bool:
        return self.completed_tasks + self.failed_tasks >= self.total_tasks


class ConcurrentOrchestrator:
    """
    Manages concurrent execution of multiple agents with human-in-the-loop approval.
    
    Features:
    - Concurrent multi-agent task execution
    - Human approval gates with timeout handling
    - Real-time progress streaming via message bus
    - Inter-agent communication and data sharing
    - Load balancing across agent pool
    - Health monitoring and auto-recovery
    """
    
    def __init__(
        self,
        agent_pool: AgentPool,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the concurrent orchestrator."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.skip_approvals: bool = bool(self.config.get('skip_approvals', False))
        
        # Core components
        self.agent_pool = agent_pool
        self.message_bus = message_bus
        
        # Execution state
        self.active_batches: Dict[str, ExecutionBatch] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.execution_history: Dict[str, ExecutionBatch] = {}
        
        # Task routing and dependencies
        self.task_dependencies: Dict[str, List[str]] = {}
        self.completed_tasks: Dict[str, ConcurrentTask] = {}
        
        # Callbacks
        self.approval_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._approval_timeout_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.total_batches_processed = 0
        self.total_tasks_executed = 0
        self.total_approvals_requested = 0
        
        self.logger.info("ConcurrentOrchestrator initialized")
    
    async def start(self):
        """Start the concurrent orchestrator."""
        self.logger.info("Starting ConcurrentOrchestrator")
        
        # Start monitoring tasks
        self._monitoring_task = asyncio.create_task(self._monitor_executions())
        self._approval_timeout_task = asyncio.create_task(self._monitor_approval_timeouts())
        
        # Subscribe to message bus events
        await self._subscribe_to_events()
        
        self.logger.info("ConcurrentOrchestrator started successfully")
    
    async def stop(self, timeout: float = 30.0):
        """Stop the concurrent orchestrator."""
        self.logger.info("Stopping ConcurrentOrchestrator")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel monitoring tasks
        tasks_to_cancel = [
            self._monitoring_task,
            self._approval_timeout_task
        ]
        
        for task in tasks_to_cancel:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        if tasks_to_cancel:
            await asyncio.gather(*[t for t in tasks_to_cancel if t], return_exceptions=True)
        
        self.logger.info("ConcurrentOrchestrator stopped")
    
    async def submit_batch(
        self,
        tasks: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        requires_approval: bool = True
    ) -> str:
        """
        Submit a batch of tasks for concurrent execution.
        
        Args:
            tasks: List of task dictionaries with type, description, input_data
            user_id: User identifier
            session_id: Session identifier
            workflow_id: Optional workflow identifier
            requires_approval: Whether tasks require human approval
            
        Returns:
            Batch ID for tracking
        """
        batch_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Submitting batch {batch_id} with {len(tasks)} tasks")
        
        # Create concurrent tasks
        concurrent_tasks = []
        for task_data in tasks:
            task = ConcurrentTask(
                task_id=task_data.get('task_id', str(uuid.uuid4())[:8]),
                task_type=task_data.get('task_type', 'unknown'),
                description=task_data.get('description', ''),
                input_data=task_data.get('input_data', {}),
                preferred_agent=task_data.get('preferred_agent'),
                priority=task_data.get('priority', 1),
                requires_approval=task_data.get('requires_approval', requires_approval),
                timeout_seconds=task_data.get('timeout_seconds', 300),
                dependencies=task_data.get('dependencies', [])
            )
            concurrent_tasks.append(task)
        
        # Create execution batch
        batch = ExecutionBatch(
            batch_id=batch_id,
            tasks=concurrent_tasks,
            user_id=user_id,
            session_id=session_id,
            workflow_id=workflow_id
        )
        
        self.active_batches[batch_id] = batch
        
        # Start execution process
        asyncio.create_task(self._execute_batch(batch))
        
        # Publish batch created event
        await self.message_bus.publish(
            topic=f"orchestrator:batch:{batch_id}",
            message_type=MessageType.SYSTEM_EVENT,
            source="concurrent_orchestrator",
            payload={
                'batch_id': batch_id,
                'event': 'batch_created',
                'task_count': len(tasks),
                'user_id': user_id,
                'created_at': batch.created_at.isoformat(),
                'session_id': session_id,
                'workflow_id': workflow_id
            }
        )
        
        self.total_batches_processed += 1
        return batch_id
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch execution."""
        batch = self.active_batches.get(batch_id) or self.execution_history.get(batch_id)
        if not batch:
            return None
        
        return {
            'batch_id': batch_id,
            'status': batch.status.value,
            'progress_percentage': batch.progress_percentage,
            'total_tasks': batch.total_tasks,
            'completed_tasks': batch.completed_tasks,
            'failed_tasks': batch.failed_tasks,
            'created_at': batch.created_at.isoformat(),
            'tasks': [
                {
                    'task_id': task.task_id,
                    'type': task.task_type,
                    'description': task.description,
                    'status': task.status.value,
                    'assigned_agent': task.assigned_agent,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'error_message': task.error_message,
                    'result_data': task.result_data
                }
                for task in batch.tasks
            ]
        }
    
    async def approve_task(self, request_id: str, approved: bool, human_message: Optional[str] = None):
        """Process human approval for a task."""
        if request_id not in self.pending_approvals:
            self.logger.warning(f"Approval request {request_id} not found")
            return
        
        approval_request = self.pending_approvals[request_id]
        approval_request.approval_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval_request.human_message = human_message
        approval_request.approved_at = datetime.utcnow()
        
        # Publish approval event
        await self.message_bus.publish(
            topic=f"orchestrator:approval:{request_id}",
            message_type=MessageType.USER_EVENT,
            source="human_approver",
            payload={
                'request_id': request_id,
                'task_id': approval_request.task.task_id,
                'approved': approved,
                'human_message': human_message
            }
        )
        
        self.logger.info(f"Task approval {request_id}: {'approved' if approved else 'rejected'}")
    
    async def cancel_batch(self, batch_id: str):
        """Cancel a batch execution."""
        if batch_id not in self.active_batches:
            return
        
        batch = self.active_batches[batch_id]
        batch.status = ExecutionStatus.CANCELLED
        
        # Cancel pending tasks
        for task in batch.tasks:
            if task.status in [ExecutionStatus.PENDING, ExecutionStatus.AWAITING_APPROVAL, ExecutionStatus.APPROVED]:
                task.status = ExecutionStatus.CANCELLED
        
        # Publish cancellation event
        await self.message_bus.publish(
            topic=f"orchestrator:batch:{batch_id}",
            message_type=MessageType.SYSTEM_EVENT,
            source="concurrent_orchestrator",
            payload={
                'batch_id': batch_id,
                'event': 'batch_cancelled'
            }
        )
        
        self.logger.info(f"Batch {batch_id} cancelled")
    
    def set_approval_callback(self, callback: Callable[[ApprovalRequest], Any]):
        """Set callback for approval requests."""
        self.approval_callback = callback
    
    def set_progress_callback(self, callback: Callable[[str, Dict[str, Any]], Any]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[ExecutionBatch], Any]):
        """Set callback for batch completion."""
        self.completion_callback = callback
    
    async def _execute_batch(self, batch: ExecutionBatch):
        """Execute a batch of tasks concurrently."""
        self.logger.info(f"Executing batch {batch.batch_id} with {len(batch.tasks)} tasks")
        batch.status = ExecutionStatus.EXECUTING
        
        try:
            # Process tasks with dependency resolution
            execution_tasks = []
            for task in batch.tasks:
                execution_tasks.append(self._execute_single_task(task, batch))
            
            # Execute all tasks concurrently
            await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Update batch status
            if batch.failed_tasks > 0:
                batch.status = ExecutionStatus.FAILED
            else:
                batch.status = ExecutionStatus.COMPLETED
            
            # Move to history
            self.execution_history[batch.batch_id] = batch
            self.active_batches.pop(batch.batch_id, None)
            
            # Call completion callback
            if self.completion_callback:
                try:
                    await self.completion_callback(batch)
                except Exception as e:
                    self.logger.error(f"Error in completion callback: {e}")
            
            self.logger.info(f"Batch {batch.batch_id} execution completed")
            
        except Exception as e:
            self.logger.error(f"Batch execution failed: {e}")
            batch.status = ExecutionStatus.FAILED
    
    async def _execute_single_task(self, task: ConcurrentTask, batch: ExecutionBatch):
        """Execute a single task with approval flow."""
        try:
            # Wait for dependencies
            await self._wait_for_dependencies(task)
            
            # Request approval if required
            if task.requires_approval and not self.skip_approvals:
                approved = await self._request_approval(task, batch)
                if not approved:
                    task.status = ExecutionStatus.CANCELLED
                    return
            
            task.status = ExecutionStatus.EXECUTING
            task.started_at = datetime.utcnow()
            
            # Submit to agent pool
            self.logger.info(f"Submitting task {task.task_id} (type: {task.task_type}) to agent pool with preferred_agent: {task.preferred_agent}")
            
            agent_id = await self.agent_pool.submit_task(
                TaskRequest(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    input_data=task.input_data,
                    timeout_seconds=task.timeout_seconds
                ),
                preferred_agent=task.preferred_agent
            )
            
            if not agent_id:
                self.logger.error(f"No available agents for task execution. Task: {task.task_type}, Preferred: {task.preferred_agent}")
                raise Exception("No available agents for task execution")
            
            task.assigned_agent = agent_id
            
            # Wait for task completion (polling agent pool)
            result = await self._wait_for_task_completion(task, agent_id)
            
            if result.success:
                task.status = ExecutionStatus.COMPLETED
                task.result_data = result.result_data
                batch.completed_tasks += 1
                self.total_tasks_executed += 1
            else:
                task.status = ExecutionStatus.FAILED
                task.error_message = result.error_message
                batch.failed_tasks += 1
            
            task.completed_at = datetime.utcnow()
            self.completed_tasks[task.task_id] = task
            
            # Publish task completion event
            await self.message_bus.publish(
                topic=f"orchestrator:task:{task.task_id}",
                message_type=MessageType.TASK_COMPLETED if result.success else MessageType.TASK_FAILED,
                source="concurrent_orchestrator",
                payload={
                    'task_id': task.task_id,
                    'batch_id': batch.batch_id,
                    'success': result.success,
                    'agent_id': agent_id,
                    'result_data': task.result_data,
                    'error_message': task.error_message,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            task.status = ExecutionStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            batch.failed_tasks += 1
    
    async def _request_approval(self, task: ConcurrentTask, batch: ExecutionBatch) -> bool:
        """Request human approval for task execution."""
        request_id = str(uuid.uuid4())[:8]
        
        # Get agent info for approval context (ensure JSON serializable)
        agent_info = {}
        if task.preferred_agent:
            raw_agent_info = await self.agent_pool.get_agent_info(task.preferred_agent) or {}
            # Convert AgentHealth objects to dictionaries to make JSON serializable
            agent_info = self._sanitize_agent_info(raw_agent_info)
        
        # Create approval request
        approval_request = ApprovalRequest(
            request_id=request_id,
            task=task,
            agent_info=agent_info,
            estimated_duration=task.timeout_seconds,
            risk_assessment="Medium",  # Could be enhanced with risk analysis
            timeout_at=datetime.utcnow() + timedelta(minutes=5)  # 5 minute approval timeout
        )
        
        self.pending_approvals[request_id] = approval_request
        task.status = ExecutionStatus.AWAITING_APPROVAL
        
        # Call approval callback
        if self.approval_callback:
            try:
                await self.approval_callback(approval_request)
            except Exception as e:
                self.logger.error(f"Error in approval callback: {e}")
        
        # Publish approval request event
        await self.message_bus.publish(
            topic=f"orchestrator:approval_request",
            message_type=MessageType.USER_EVENT,
            source="concurrent_orchestrator",
            payload={
                'request_id': request_id,
                'task_id': task.task_id,
                'batch_id': batch.batch_id,
                'task_description': task.description,
                'estimated_duration': task.timeout_seconds,
                'agent_info': agent_info,
                'timeout_at': approval_request.timeout_at.isoformat(),
                'created_at': approval_request.created_at.isoformat()
            }
        )
        
        self.total_approvals_requested += 1
        
        # Wait for approval or timeout
        while approval_request.approval_status == ApprovalStatus.PENDING:
            if datetime.utcnow() > approval_request.timeout_at:
                approval_request.approval_status = ApprovalStatus.TIMEOUT
                break
            await asyncio.sleep(1.0)
        
        # Clean up
        self.pending_approvals.pop(request_id, None)
        
        return approval_request.approval_status == ApprovalStatus.APPROVED
    
    async def _wait_for_dependencies(self, task: ConcurrentTask):
        """Wait for task dependencies to complete."""
        if not task.dependencies:
            return
        
        while True:
            pending_deps = [
                dep for dep in task.dependencies 
                if dep not in self.completed_tasks
            ]
            
            if not pending_deps:
                break
            
            await asyncio.sleep(1.0)
    
    async def _wait_for_task_completion(self, task: ConcurrentTask, agent_id: str) -> TaskResponse:
        """Wait for task completion from agent using message bus events."""
        
        self.logger.info(f"Waiting for task {task.task_id} completion from agent {agent_id}")
        
        # Create a future to wait for the completion event
        completion_future = asyncio.Future()
        task_topic = f"agent:{agent_id}:tasks"

        # Subscribe to task events and filter by this task_id
        async def completion_handler(msg: Message):
            try:
                payload = msg.payload or {}
                if payload.get('task_id') == task.task_id and msg.type in (MessageType.TASK_COMPLETED, MessageType.TASK_FAILED):
                    if not completion_future.done():
                        completion_future.set_result(payload)
            except Exception as e:
                self.logger.error(f"Error in completion handler: {e}")
                if not completion_future.done():
                    completion_future.set_exception(e)

        # Subscribe to the message bus
        await self.message_bus.subscribe(task_topic, completion_handler)
        
        try:
            # Wait for completion with timeout
            result_payload = await asyncio.wait_for(
                completion_future, 
                timeout=task.timeout_seconds
            )
            
            # Unsubscribe from the message bus
            try:
                await self.message_bus.unsubscribe(task_topic, completion_handler)
            except Exception as e:
                self.logger.debug(f"Error unsubscribing from message bus: {e}")
            
            # Create proper TaskResponse
            return TaskResponse(
                task_id=task.task_id,
                success=result_payload.get('success', True),
                result_data=result_payload.get('result_data', {}),
                error_message=result_payload.get('error_message'),
                processing_time_ms=result_payload.get('processing_time_ms', 0)
            )
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Task {task.task_id} timed out after {task.timeout_seconds}s")
            
            # Unsubscribe from the message bus
            try:
                await self.message_bus.unsubscribe(task_topic, completion_handler)
            except Exception as e:
                self.logger.debug(f"Error unsubscribing from message bus: {e}")
            
            return TaskResponse(
                task_id=task.task_id,
                success=False,
                error_message=f"Task timed out after {task.timeout_seconds}s"
            )
        
        except Exception as e:
            self.logger.error(f"Error waiting for task completion: {e}")
            
            # Unsubscribe from the message bus
            try:
                await self.message_bus.unsubscribe(task_topic, completion_handler)
            except Exception as e2:
                self.logger.debug(f"Error unsubscribing from message bus: {e2}")
            
            return TaskResponse(
                task_id=task.task_id,
                success=False,
                error_message=f"Task execution error: {str(e)}"
            )
    
    async def _subscribe_to_events(self):
        """Subscribe to relevant message bus events."""
        # Subscribe to agent status updates (pattern-based)
        await self.message_bus.subscribe_pattern(
            "agent:*:status",
            self._handle_agent_status_update
        )
        
        # Subscribe to task events (pattern-based)
        await self.message_bus.subscribe_pattern(
            "agent:*:tasks",
            self._handle_agent_task_event
        )
    
    async def _handle_agent_status_update(self, message: Message):
        """Handle agent status updates."""
        # Could use this for better task completion tracking
        pass
    
    async def _handle_agent_task_event(self, message: Message):
        """Handle agent task events."""
        # Could use this for real-time task completion tracking
        pass
    
    async def _monitor_executions(self):
        """Monitor active executions and publish progress updates."""
        while not self._shutdown_event.is_set():
            try:
                for batch_id, batch in list(self.active_batches.items()):
                    # Publish progress update
                    await self.message_bus.publish(
                        topic=f"orchestrator:progress:{batch_id}",
                        message_type=MessageType.SYSTEM_EVENT,
                        source="concurrent_orchestrator",
                        payload={
                            'batch_id': batch_id,
                            'progress_percentage': batch.progress_percentage,
                            'completed_tasks': batch.completed_tasks,
                            'failed_tasks': batch.failed_tasks,
                            'total_tasks': batch.total_tasks,
                            'status': batch.status.value
                        }
                    )
                    
                    # Call progress callback
                    if self.progress_callback:
                        try:
                            await self.progress_callback(batch_id, {
                                'progress': batch.progress_percentage,
                                'status': batch.status.value
                            })
                        except Exception as e:
                            self.logger.error(f"Error in progress callback: {e}")
                
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in execution monitoring: {e}")
                await asyncio.sleep(5.0)
    
    async def _monitor_approval_timeouts(self):
        """Monitor approval request timeouts."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                
                for request_id, approval_request in list(self.pending_approvals.items()):
                    if (approval_request.approval_status == ApprovalStatus.PENDING and 
                        current_time > approval_request.timeout_at):
                        
                        approval_request.approval_status = ApprovalStatus.TIMEOUT
                        
                        # Publish timeout event
                        await self.message_bus.publish(
                            topic=f"orchestrator:approval:{request_id}",
                            message_type=MessageType.SYSTEM_EVENT,
                            source="concurrent_orchestrator",
                            payload={
                                'request_id': request_id,
                                'event': 'approval_timeout'
                            }
                        )
                
                await asyncio.sleep(10.0)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in approval timeout monitoring: {e}")
                await asyncio.sleep(10.0)
    
    def _sanitize_agent_info(self, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert non-JSON-serializable objects to dictionaries."""
        sanitized = {}
        for key, value in agent_info.items():
            if hasattr(value, '__dict__'):
                # Convert objects with __dict__ to dictionaries
                if hasattr(value, '_asdict'):
                    # Handle namedtuples
                    sanitized[key] = value._asdict()
                elif hasattr(value, 'to_dict'):
                    # Handle custom objects with to_dict method
                    sanitized[key] = value.to_dict()
                else:
                    # Convert object attributes to dict
                    try:
                        sanitized[key] = {
                            attr: getattr(value, attr) for attr in dir(value)
                            if not attr.startswith('_') and not callable(getattr(value, attr))
                        }
                    except Exception:
                        sanitized[key] = str(value)
            elif isinstance(value, (str, int, float, bool, list, dict, type(None))):
                # Keep JSON-serializable types as-is
                sanitized[key] = value
            else:
                # Convert everything else to string
                sanitized[key] = str(value)
        
        return sanitized
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            'total_batches_processed': self.total_batches_processed,
            'total_tasks_executed': self.total_tasks_executed,
            'total_approvals_requested': self.total_approvals_requested,
            'active_batches': len(self.active_batches),
            'pending_approvals': len(self.pending_approvals),
            'completed_batches': len(self.execution_history)
        }

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task by task_id."""
        task = self.completed_tasks.get(task_id)
        if not task:
            return None
        return {
            'task_id': task.task_id,
            'success': task.status == ExecutionStatus.COMPLETED,
            'result_data': task.result_data,
            'error_message': task.error_message,
            'assigned_agent': task.assigned_agent,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }