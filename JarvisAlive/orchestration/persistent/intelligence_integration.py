"""
Intelligence Integration - Bridges Intelligence Layer with Persistent Agent System.

This integration provides:
- WorkflowBrain integration with concurrent execution
- Intelligent agent selection and routing
- Context-aware task distribution
- Workflow-aware performance optimization
- Enhanced planning with concurrent capabilities
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .persistent_system import PersistentSystem
from .concurrent_orchestrator import ConcurrentTask, ExecutionBatch, ApprovalRequest
from ..intelligence.workflow_brain import WorkflowBrain
from ..intelligence.models import (
    WorkflowState, WorkflowStep, NextStepOption, 
    WorkflowStatus, StepStatus, AutoPilotMode
)


@dataclass
class IntelligentTask:
    """Enhanced task with intelligence layer metadata."""
    base_task: ConcurrentTask
    workflow_context: Dict[str, Any]
    intelligence_metadata: Dict[str, Any]
    step_dependencies: List[str]
    expected_outputs: List[str]
    confidence_score: float
    priority_score: float


class IntelligentAgentSelector:
    """Intelligently selects agents based on workflow context and performance."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_performance_history: Dict[str, Dict[str, float]] = {}
        self.workload_tracker: Dict[str, int] = {}
        self.task_type_specialization: Dict[str, List[str]] = {
            'branding': ['brand_name_generation', 'logo_prompt_creation', 'visual_identity_design'],
            'market_research': ['market_opportunity_analysis', 'competitive_analysis', 'target_audience_research'],
            'analysis': ['data_analysis', 'trend_analysis', 'performance_analysis'],
            'strategy': ['business_strategy', 'go_to_market', 'strategic_planning']
        }
    
    async def select_optimal_agent(
        self, 
        task: IntelligentTask, 
        available_agents: List[str],
        workflow_context: Dict[str, Any]
    ) -> Optional[str]:
        """Select the most suitable agent for a task."""
        
        if not available_agents:
            return None
        
        # Score each agent
        agent_scores = {}
        for agent_id in available_agents:
            score = await self._calculate_agent_score(agent_id, task, workflow_context)
            agent_scores[agent_id] = score
        
        # Select highest scoring agent
        best_agent = max(agent_scores, key=agent_scores.get)
        self.logger.info(f"Selected agent {best_agent} for task {task.base_task.task_type} (score: {agent_scores[best_agent]:.2f})")
        
        return best_agent
    
    async def _calculate_agent_score(
        self, 
        agent_id: str, 
        task: IntelligentTask, 
        context: Dict[str, Any]
    ) -> float:
        """Calculate suitability score for an agent."""
        
        base_score = 5.0
        
        # Specialization bonus
        task_type = task.base_task.task_type
        for specialization, task_types in self.task_type_specialization.items():
            if task_type in task_types and specialization in agent_id:
                base_score += 3.0
                break
        
        # Performance history bonus
        if agent_id in self.agent_performance_history:
            perf = self.agent_performance_history[agent_id]
            success_rate = perf.get('success_rate', 0.8)
            avg_time = perf.get('avg_processing_time', 60)
            
            base_score += (success_rate - 0.5) * 2  # Success rate bonus
            base_score += max(0, (120 - avg_time) / 120)  # Speed bonus
        
        # Workload penalty
        current_workload = self.workload_tracker.get(agent_id, 0)
        base_score -= min(2.0, current_workload * 0.5)
        
        # Context relevance bonus
        workflow_type = context.get('workflow_type', '')
        if workflow_type in agent_id:
            base_score += 1.5
        
        return max(0, base_score)
    
    def record_task_completion(
        self, 
        agent_id: str, 
        task_type: str, 
        success: bool, 
        processing_time: float
    ):
        """Record task completion for performance tracking."""
        
        if agent_id not in self.agent_performance_history:
            self.agent_performance_history[agent_id] = {
                'success_rate': 0.8,
                'avg_processing_time': 60,
                'total_tasks': 0
            }
        
        history = self.agent_performance_history[agent_id]
        history['total_tasks'] += 1
        
        # Update success rate with exponential moving average
        current_success_rate = history['success_rate']
        alpha = 0.1  # Learning rate
        new_success_rate = (1 - alpha) * current_success_rate + alpha * (1 if success else 0)
        history['success_rate'] = new_success_rate
        
        # Update average processing time
        current_avg_time = history['avg_processing_time']
        new_avg_time = (1 - alpha) * current_avg_time + alpha * processing_time
        history['avg_processing_time'] = new_avg_time
    
    def update_workload(self, agent_id: str, delta: int):
        """Update agent workload tracking."""
        if agent_id not in self.workload_tracker:
            self.workload_tracker[agent_id] = 0
        self.workload_tracker[agent_id] = max(0, self.workload_tracker[agent_id] + delta)


class WorkflowTaskRouter:
    """Routes workflow steps to appropriate concurrent tasks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.routing_patterns = {
            'market_research': {
                'parallel_tasks': ['market_opportunity_analysis', 'competitive_analysis'],
                'sequential_dependencies': {'revenue_estimation': ['market_opportunity_analysis']},
                'optimization_hints': {'cache_duration': 3600}
            },
            'branding': {
                'parallel_tasks': ['brand_name_generation', 'visual_identity_design'],
                'sequential_dependencies': {'logo_prompt_creation': ['brand_name_generation']},
                'optimization_hints': {'requires_approval': True}
            },
            'business_creation': {
                'parallel_tasks': ['market_research', 'branding', 'competitive_analysis'],
                'sequential_dependencies': {'business_plan': ['market_research', 'branding']},
                'optimization_hints': {'high_priority': True}
            }
        }
    
    def create_intelligent_tasks(
        self, 
        workflow_steps: List[WorkflowStep],
        workflow_context: Dict[str, Any]
    ) -> List[IntelligentTask]:
        """Convert workflow steps to intelligent tasks."""
        
        intelligent_tasks = []
        workflow_type = workflow_context.get('workflow_type', 'general')
        
        for step in workflow_steps:
            # Merge workflow context with step input data to ensure business idea is passed
            step_input_data = step.input_state or {}
            
            # Debug: Log workflow context (remove after testing)
            # self.logger.info(f"Workflow context keys: {list(workflow_context.keys())}")
            # self.logger.info(f"Workflow context: {workflow_context}")
            
            # Extract business idea from initial_request or workflow_title
            business_idea = workflow_context.get('initial_request', '')
            if not business_idea:
                # Extract from workflow_title if initial_request is not available
                workflow_title = workflow_context.get('workflow_title', '')
                if workflow_title and ': ' in workflow_title:
                    business_idea = workflow_title.split(': ', 1)[1]
                elif workflow_title:
                    business_idea = workflow_title
                    
            # Ensure critical workflow context is always available to tasks
            workflow_data = {
                'business_idea': business_idea,
                'workflow_type': workflow_type,
                'user_id': workflow_context.get('user_id', ''),
                'session_id': workflow_context.get('session_id', ''),
                'industry': workflow_context.get('industry', 'General'),
                'location': workflow_context.get('location', 'Global')
            }
            
            # self.logger.info(f"Extracted business_idea: '{workflow_data['business_idea']}'")
            
            # Merge with step-specific data (step data takes precedence)
            merged_input_data = {**workflow_data, **step_input_data}
            
            # Normalize step type to a supported agent task when planner used a generic label
            normalized_step_type = step.step_type
            try:
                step_text = f"{merged_input_data.get('business_idea','')} {step.description}".lower()
                if step.step_type == 'analysis':
                    if 'market' in step_text:
                        normalized_step_type = 'market_research'
                    elif any(k in step_text for k in ['brand', 'logo', 'identity', 'design']):
                        normalized_step_type = 'branding'
            except Exception:
                pass
            
            # Create base concurrent task
            base_task = ConcurrentTask(
                task_id=step.step_id or str(uuid.uuid4())[:8],
                task_type=normalized_step_type,
                description=step.description,
                input_data=merged_input_data,
                priority=self._calculate_step_priority(step, workflow_context),
                requires_approval=self._requires_approval(step, workflow_type),
                timeout_seconds=self._calculate_timeout(step, workflow_context)
            )
            
            # Create intelligent task wrapper
            intelligent_task = IntelligentTask(
                base_task=base_task,
                workflow_context=workflow_context,
                intelligence_metadata={
                    'step_type': step.step_type,
                    'agent_preference': step.agent_id,
                    'confidence_score': getattr(step, 'confidence_score', 0.7),
                    'workflow_type': workflow_type,
                    'creation_timestamp': datetime.utcnow().isoformat()
                },
                step_dependencies=self._extract_dependencies(step, workflow_steps),
                expected_outputs=self._predict_outputs(step, workflow_context),
                confidence_score=getattr(step, 'confidence_score', 0.7),
                priority_score=self._calculate_priority_score(step, workflow_context)
            )
            
            intelligent_tasks.append(intelligent_task)
        
        # Optimize task ordering and dependencies
        intelligent_tasks = self._optimize_task_execution_order(intelligent_tasks, workflow_type)
        
        return intelligent_tasks
    
    def _calculate_step_priority(self, step: WorkflowStep, context: Dict[str, Any]) -> int:
        """Calculate priority for a workflow step."""
        base_priority = 1
        
        # Critical path steps get higher priority
        critical_steps = ['market_research', 'competitive_analysis', 'branding']
        if step.step_type in critical_steps:
            base_priority += 1
        
        # User-requested steps get highest priority
        if context.get('user_priority_step') == step.step_type:
            base_priority += 2
        
        return base_priority
    
    def _requires_approval(self, step: WorkflowStep, workflow_type: str) -> bool:
        """Determine if step requires human approval."""
        
        # High-risk operations always require approval
        high_risk_steps = ['data_modification', 'external_api_calls', 'financial_analysis']
        if step.step_type in high_risk_steps:
            return True
        
        # Check workflow-specific patterns
        patterns = self.routing_patterns.get(workflow_type, {})
        hints = patterns.get('optimization_hints', {})
        if hints.get('requires_approval', False):
            return True
        
        # Default based on step confidence
        confidence = getattr(step, 'confidence_score', 0.7)
        return confidence < 0.8
    
    def _calculate_timeout(self, step: WorkflowStep, context: Dict[str, Any]) -> int:
        """Calculate appropriate timeout for step."""
        
        # Base timeouts by step type
        timeout_map = {
            'market_research': 300,
            'branding': 180,
            'competitive_analysis': 240,
            'data_analysis': 120,
            'report_generation': 600
        }
        
        base_timeout = timeout_map.get(step.step_type, 180)
        
        # Adjust for complexity
        complexity_factors = context.get('complexity_factors', {})
        if complexity_factors.get('high_complexity', False):
            base_timeout *= 1.5
        
        return int(base_timeout)
    
    def _extract_dependencies(
        self, 
        step: WorkflowStep, 
        all_steps: List[WorkflowStep]
    ) -> List[str]:
        """Extract dependencies between workflow steps."""
        
        dependencies = []
        
        # Check explicit dependencies
        if hasattr(step, 'dependencies') and step.dependencies:
            dependencies.extend(step.dependencies)
        
        # Infer logical dependencies
        if step.step_type == 'logo_prompt_creation':
            # Logo creation depends on brand name
            brand_steps = [s.step_id for s in all_steps if s.step_type == 'brand_name_generation']
            dependencies.extend(brand_steps)
        
        elif step.step_type == 'business_plan':
            # Business plan depends on research and branding
            research_steps = [s.step_id for s in all_steps if 'research' in s.step_type]
            brand_steps = [s.step_id for s in all_steps if 'brand' in s.step_type]
            dependencies.extend(research_steps + brand_steps)
        
        return list(set(dependencies))
    
    def _predict_outputs(self, step: WorkflowStep, context: Dict[str, Any]) -> List[str]:
        """Predict expected outputs from a step."""
        
        output_predictions = {
            'market_research': ['market_size', 'target_audience', 'growth_potential'],
            'competitive_analysis': ['competitors', 'competitive_advantages', 'market_positioning'],
            'brand_name_generation': ['brand_names', 'rationale', 'trademark_considerations'],
            'logo_prompt_creation': ['logo_prompt', 'design_rationale', 'color_palette'],
            'business_plan': ['executive_summary', 'financial_projections', 'strategy']
        }
        
        return output_predictions.get(step.step_type, ['result_data'])
    
    def _calculate_priority_score(self, step: WorkflowStep, context: Dict[str, Any]) -> float:
        """Calculate numeric priority score for optimization."""
        
        base_score = 5.0
        
        # Factor in step importance
        importance_map = {
            'market_research': 9.0,
            'competitive_analysis': 8.0,
            'branding': 8.5,
            'business_plan': 10.0,
            'financial_analysis': 7.5
        }
        
        importance = importance_map.get(step.step_type, 5.0)
        base_score += (importance - 5.0)
        
        # Factor in user preferences
        user_priority = context.get('user_priority_boost', {})
        if step.step_type in user_priority:
            base_score += 2.0
        
        # Factor in confidence score
        confidence = getattr(step, 'confidence_score', 0.7)
        base_score += (confidence - 0.5) * 2
        
        return base_score
    
    def _optimize_task_execution_order(
        self, 
        tasks: List[IntelligentTask], 
        workflow_type: str
    ) -> List[IntelligentTask]:
        """Optimize task execution order for efficiency."""
        
        # Get routing patterns
        patterns = self.routing_patterns.get(workflow_type, {})
        parallel_tasks = patterns.get('parallel_tasks', [])
        
        # Sort by priority score (higher first)
        tasks.sort(key=lambda t: t.priority_score, reverse=True)
        
        # Group parallel tasks together
        parallel_task_objects = [t for t in tasks if t.base_task.task_type in parallel_tasks]
        sequential_task_objects = [t for t in tasks if t.base_task.task_type not in parallel_tasks]
        
        # Return optimized order: high-priority parallel tasks first, then sequential
        optimized_tasks = parallel_task_objects + sequential_task_objects
        
        self.logger.info(f"Optimized {len(tasks)} tasks for {workflow_type} workflow")
        return optimized_tasks


class IntelligenceIntegrator:
    """Main integration class that bridges Intelligence Layer with Persistent System."""
    
    def __init__(self, persistent_system: PersistentSystem, workflow_brain: WorkflowBrain):
        self.persistent_system = persistent_system
        self.workflow_brain = workflow_brain
        self.logger = logging.getLogger(__name__)
        
        # Integration components
        self.agent_selector = IntelligentAgentSelector()
        self.task_router = WorkflowTaskRouter()
        
        # State tracking
        self.active_workflow_batches: Dict[str, str] = {}  # workflow_id -> batch_id
        self.batch_workflow_mapping: Dict[str, str] = {}  # batch_id -> workflow_id
        
        # Performance tracking
        self.integration_metrics = {
            'workflows_processed': 0,
            'tasks_routed': 0,
            'average_workflow_time': 0,
            'success_rate': 0
        }
    
    async def execute_workflow_concurrently(
        self,
        workflow_id: str,
        user_id: str,
        session_id: str,
        autopilot_mode: AutoPilotMode = AutoPilotMode.SMART_AUTO
    ) -> str:
        """Execute a workflow using concurrent persistent agents."""
        
        self.logger.info(f"Starting concurrent execution of workflow {workflow_id}")
        
        # Get workflow state from WorkflowBrain
        workflow_state = self.workflow_brain.active_workflows.get(workflow_id)
        if not workflow_state:
            raise ValueError(f"Workflow {workflow_id} not found in WorkflowBrain")
        
        try:
            # Convert workflow steps to intelligent tasks
            intelligent_tasks = self.task_router.create_intelligent_tasks(
                workflow_steps=workflow_state.pending_steps,
                workflow_context={
                    'workflow_id': workflow_id,
                    'workflow_type': workflow_state.workflow_type,
                    'user_id': user_id,
                    'session_id': session_id,
                    'autopilot_mode': autopilot_mode.value,
                    'accumulated_data': workflow_state.accumulated_data,
                    'workflow_title': workflow_state.workflow_title
                }
            )
            
            # Convert to concurrent tasks with intelligent routing
            concurrent_tasks = []
            for intelligent_task in intelligent_tasks:
                # Select optimal agent
                available_agents = await self._get_available_agents_for_task(
                    intelligent_task.base_task.task_type
                )
                
                optimal_agent = await self.agent_selector.select_optimal_agent(
                    task=intelligent_task,
                    available_agents=available_agents,
                    workflow_context=intelligent_task.workflow_context
                )
                
                self.logger.info(f"Task {intelligent_task.base_task.task_type}: available_agents={available_agents}, selected={optimal_agent}")
                
                if optimal_agent:
                    intelligent_task.base_task.preferred_agent = optimal_agent
                    self.agent_selector.update_workload(optimal_agent, 1)
                else:
                    self.logger.warning(f"No optimal agent found for task {intelligent_task.base_task.task_type}")
                
                # Convert to dictionary format for submission
                task_dict = {
                    'task_type': intelligent_task.base_task.task_type,
                    'description': intelligent_task.base_task.description,
                    'input_data': intelligent_task.base_task.input_data,
                    'preferred_agent': intelligent_task.base_task.preferred_agent,
                    'priority': intelligent_task.base_task.priority,
                    'requires_approval': intelligent_task.base_task.requires_approval,
                    'timeout_seconds': intelligent_task.base_task.timeout_seconds,
                    'dependencies': intelligent_task.step_dependencies
                }
                concurrent_tasks.append(task_dict)
            
            # Submit to persistent system
            batch_id = await self.persistent_system.submit_concurrent_tasks(
                tasks=concurrent_tasks,
                user_id=user_id,
                session_id=session_id,
                workflow_id=workflow_id,
                requires_approval=(autopilot_mode != AutoPilotMode.FULL_AUTO)
            )
            
            # Track mapping
            self.active_workflow_batches[workflow_id] = batch_id
            self.batch_workflow_mapping[batch_id] = workflow_id
            
            # Set up completion callback
            self.persistent_system.set_completion_callback(self._handle_batch_completion)
            
            self.integration_metrics['workflows_processed'] += 1
            self.integration_metrics['tasks_routed'] += len(concurrent_tasks)
            
            self.logger.info(f"Workflow {workflow_id} submitted as batch {batch_id} with {len(concurrent_tasks)} tasks")
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow concurrently: {e}")
            raise
    
    async def handle_workflow_step_completion(
        self,
        step_id: str,
        success: bool,
        result_data: Dict[str, Any],
        processing_time: float,
        agent_id: str
    ):
        """Handle completion of individual workflow steps."""
        
        # Record performance metrics
        task_type = result_data.get('task_type', 'unknown')
        self.agent_selector.record_task_completion(
            agent_id=agent_id,
            task_type=task_type,
            success=success,
            processing_time=processing_time
        )
        
        # Update agent workload
        self.agent_selector.update_workload(agent_id, -1)
        
        self.logger.info(f"Step {step_id} completed by {agent_id} (success: {success})")
    
    async def get_workflow_progress(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a workflow."""
        
        batch_id = self.active_workflow_batches.get(workflow_id)
        if not batch_id:
            return None
        
        # Get batch status from persistent system
        batch_status = await self.persistent_system.get_batch_status(batch_id)
        if not batch_status:
            return None
        
        # Enhance with workflow-specific information
        workflow_progress = {
            'workflow_id': workflow_id,
            'batch_id': batch_id,
            'progress_percentage': batch_status.get('progress_percentage', 0),
            'status': batch_status.get('status', 'unknown'),
            'completed_tasks': batch_status.get('completed_tasks', 0),
            'failed_tasks': batch_status.get('failed_tasks', 0),
            'total_tasks': batch_status.get('total_tasks', 0),
            'task_details': batch_status.get('tasks', []),
            'workflow_enhanced': True,
            'intelligence_metrics': {
                'agent_utilization': await self._calculate_agent_utilization(),
                'average_confidence': await self._calculate_average_confidence(batch_id),
                'optimization_score': await self._calculate_optimization_score(batch_id)
            }
        }
        
        return workflow_progress
    
    async def cancel_workflow(self, workflow_id: str):
        """Cancel a running workflow."""
        
        batch_id = self.active_workflow_batches.get(workflow_id)
        if batch_id:
            await self.persistent_system.cancel_batch(batch_id)
            
            # Clean up tracking
            self.active_workflow_batches.pop(workflow_id, None)
            self.batch_workflow_mapping.pop(batch_id, None)
            
            self.logger.info(f"Cancelled workflow {workflow_id} (batch {batch_id})")
    
    async def _get_available_agents_for_task(self, task_type: str) -> List[str]:
        """Get list of available agents that can handle a task type."""
        
        # Get actual registered agents from the agent pool
        try:
            system_health = await self.persistent_system.get_system_health()
            agent_pool_info = system_health.get('components', {}).get('agent_pool', {})
            
            # Get all available agents from the pool
            available_agents = []
            
            # Query actual agents in the pool by checking task type mappings
            if hasattr(self.persistent_system, 'agent_pool') and hasattr(self.persistent_system.agent_pool, 'task_type_mapping'):
                # Use actual task type mappings from the agent pool
                for registered_task_type, agent_ids in self.persistent_system.agent_pool.task_type_mapping.items():
                    # Check if the requested task type matches any registered task types
                    if (task_type == registered_task_type or 
                        any(keyword in registered_task_type for keyword in task_type.split('_')) or
                        any(keyword in task_type for keyword in registered_task_type.split('_'))):
                        available_agents.extend(agent_ids)
            
            # Fallback: Map task types to known agent types if pool mapping is empty
            if not available_agents:
                if 'brand' in task_type or 'logo' in task_type or 'visual' in task_type:
                    # Check if branding agent exists
                    if 'branding_agent' in getattr(self.persistent_system.agent_pool, 'agents', {}):
                        available_agents.append('branding_agent')
                
                if ('market' in task_type or 'competitive' in task_type or 'research' in task_type or
                    'business' in task_type or 'strategy' in task_type):
                    # Check if market research agent exists - handles business strategy too
                    if 'market_research_agent' in getattr(self.persistent_system.agent_pool, 'agents', {}):
                        available_agents.append('market_research_agent')
            
            # Remove duplicates and return
            return list(set(available_agents))
            
        except Exception as e:
            self.logger.error(f"Error getting available agents: {e}")
            # Final fallback to known agent IDs
            return ['branding_agent', 'market_research_agent']
    
    async def _handle_batch_completion(self, batch: ExecutionBatch):
        """Handle completion of a batch execution."""
        
        workflow_id = self.batch_workflow_mapping.get(batch.batch_id)
        if not workflow_id:
            return
        
        try:
            # Update workflow state in WorkflowBrain
            workflow_state = self.workflow_brain.active_workflows.get(workflow_id)
            if workflow_state:
                # Process completed tasks and update workflow
                for task in batch.tasks:
                    if task.status.value == 'completed' and task.result_data:
                        # Update workflow context with results
                        workflow_state.update_context(task.result_data)
                
                # Update workflow status
                if batch.status.value == 'completed':
                    workflow_state.status = WorkflowStatus.COMPLETED
                elif batch.status.value == 'failed':
                    workflow_state.status = WorkflowStatus.FAILED
            
            # Clean up tracking
            self.active_workflow_batches.pop(workflow_id, None)
            self.batch_workflow_mapping.pop(batch.batch_id, None)
            
            self.logger.info(f"Completed workflow {workflow_id} processing")
            
        except Exception as e:
            self.logger.error(f"Error handling batch completion: {e}")
    
    async def _calculate_agent_utilization(self) -> Dict[str, float]:
        """Calculate current agent utilization metrics."""
        
        utilization = {}
        for agent_id, workload in self.agent_selector.workload_tracker.items():
            # Simplified utilization calculation
            max_capacity = 5  # Assume max 5 concurrent tasks per agent
            utilization[agent_id] = min(1.0, workload / max_capacity)
        
        return utilization
    
    async def _calculate_average_confidence(self, batch_id: str) -> float:
        """Calculate average confidence score for batch tasks."""
        
        # This would be enhanced with actual confidence tracking
        return 0.75  # Placeholder
    
    async def _calculate_optimization_score(self, batch_id: str) -> float:
        """Calculate optimization effectiveness score."""
        
        # This would include metrics like:
        # - Task parallelization efficiency
        # - Agent selection accuracy
        # - Dependency resolution effectiveness
        return 0.85  # Placeholder
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get integration performance metrics."""
        
        return {
            **self.integration_metrics,
            'active_workflows': len(self.active_workflow_batches),
            'agent_performance_tracked': len(self.agent_selector.agent_performance_history),
            'current_agent_workloads': dict(self.agent_selector.workload_tracker)
        }