"""
Hierarchical Parallel LangGraph Implementation

This module implements a hierarchical LangGraph with:
1. Intelligence Orchestrator Layer (top) - routing, HITL, coordination
2. Parallel Agent Execution Layer (middle) - all department agents run simultaneously  
3. State Management Layer (bottom) - progress, results, error handling

Architecture ensures clean separation: 
- Intelligence layer handles all coordination and human approval
- Agent layer focuses purely on domain tasks in parallel
- No blocking between agents, maximum throughput
"""

from __future__ import annotations

import asyncio
import os
import logging
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    USE_LANGGRAPH = True
except Exception:
    USE_LANGGRAPH = False

# Import Intelligence Layer
from ..intelligence.workflow_brain import WorkflowBrain
from ..intelligence.models import (
    WorkflowState as IntelligenceWorkflowState, 
    HITLPreferences, 
    AutoPilotMode,
    NextStepOption,
    HumanDecision,
    RiskLevel
)

# Create a simple WorkflowStatus enum if not available
class WorkflowStatus:
    ANALYZING = "analyzing"
    PLANNED = "planned"
    EXECUTING = "executing"
    COMPLETED = "completed"
from ..intelligence.human_loop_agent import HumanLoopAgent

# Import Persistent System for agent execution
from ..persistent.persistent_system import PersistentSystem, PersistentSystemConfig
from ..reporting.workflow_reporter import WorkflowReporter
from ..resilience.error_handler import WorkflowErrorHandler

logger = logging.getLogger(__name__)


@dataclass
class ParallelWorkflowState:
    """Enhanced state for hierarchical parallel workflow execution."""
    # Core identification
    workflow_id: str
    session_id: str
    user_request: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Intelligence Orchestrator State
    intelligence_analysis: Dict[str, Any] = field(default_factory=dict)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    hitl_status: str = "pending"  # pending, approved, rejected, bypassed
    human_decision: Optional[Dict[str, Any]] = None
    
    # Parallel Agent Execution State
    agent_tasks: Dict[str, str] = field(default_factory=dict)  # agent_name -> task_id
    agent_statuses: Dict[str, str] = field(default_factory=dict)  # agent_name -> status
    agent_results: Dict[str, Any] = field(default_factory=dict)  # agent_name -> result
    agent_errors: Dict[str, str] = field(default_factory=dict)  # agent_name -> error_msg
    
    # Progress and Coordination
    overall_status: str = "initializing"
    progress_percentage: float = 0.0
    completed_agents: List[str] = field(default_factory=list)
    failed_agents: List[str] = field(default_factory=list)
    
    # Results and Artifacts
    final_results: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)  # file paths, urls, etc.
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """Add error and update status."""
        self.errors.append(message)
        if self.overall_status not in ["failed", "completed"]:
            self.overall_status = "error"
        self.updated_at = datetime.utcnow()
    
    def add_warning(self, message: str):
        """Add warning without changing status."""
        self.warnings.append(message)
        self.updated_at = datetime.utcnow()
    
    def update_progress(self):
        """Calculate and update progress based on agent completion."""
        total_agents = len(self.agent_tasks)
        if total_agents == 0:
            self.progress_percentage = 0.0
            return
            
        completed = len(self.completed_agents)
        self.progress_percentage = (completed / total_agents) * 100
        self.updated_at = datetime.utcnow()
        
        # Update overall status
        if completed == total_agents:
            self.overall_status = "completed"
        elif len(self.failed_agents) == total_agents:
            self.overall_status = "failed"
        elif completed > 0 or len(self.failed_agents) > 0:
            self.overall_status = "in_progress"


class IntelligenceOrchestratorNode:
    """
    Top-level Intelligence Orchestrator that handles:
    - Intent analysis and workflow planning
    - Risk assessment and approval requirements
    - Human-in-the-loop coordination
    - Agent task routing and coordination
    """
    
    def __init__(self, workflow_brain: WorkflowBrain):
        self.workflow_brain = workflow_brain
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def analyze_and_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user request and create execution plan."""
        self.logger.info(f"IntelligenceOrchestrator: Starting analysis with state keys: {list(state.keys())}")
        
        workflow_state = ParallelWorkflowState(**state)
        
        try:
            # 1. Analyze user request using WorkflowBrain
            self.logger.info(f"Analyzing request: {workflow_state.user_request}")
            
            # Skip complex intelligence state for now - use simple analysis
            
            # Use workflow brain for intelligent analysis (simplified for now)
            analysis = {
                "intent_category": "business_request",
                "complexity": "medium",
                "confidence": 0.8,
                "estimated_agents_needed": self._determine_required_agents(workflow_state.user_request, {}),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            workflow_state.intelligence_analysis = analysis
            
            # 2. Determine which agents to run in parallel
            required_agents = self._determine_required_agents(workflow_state.user_request, analysis)
            self.logger.info(f"Required agents determined: {required_agents}")
            
            # 3. Create execution plan
            execution_plan = {
                "required_agents": required_agents,
                "execution_mode": "parallel",
                "dependencies": {},  # No dependencies in parallel mode
                "estimated_duration": self._estimate_duration(required_agents),
                "resource_requirements": self._assess_resources(required_agents)
            }
            workflow_state.execution_plan = execution_plan
            self.logger.info(f"Execution plan created: {execution_plan}")
            
            # 4. Risk assessment
            risk_assessment = await self._assess_risks(workflow_state, required_agents)
            workflow_state.risk_assessment = risk_assessment
            
            # 5. Determine if human approval is needed
            needs_approval = self._needs_human_approval(risk_assessment, required_agents)
            workflow_state.hitl_status = "required" if needs_approval else "bypassed"
            
            workflow_state.overall_status = "planned"
            workflow_state.updated_at = datetime.utcnow()
            
            self.logger.info(f"Execution plan created: {len(required_agents)} agents, HITL: {workflow_state.hitl_status}")
            
            return workflow_state.__dict__
            
        except Exception as e:
            self.logger.error(f"Intelligence analysis failed: {e}")
            workflow_state.add_error(f"Planning failed: {str(e)}")
            return workflow_state.__dict__
    
    def _determine_required_agents(self, user_request: str, analysis: Dict[str, Any]) -> List[str]:
        """Determine which agents should run based on request analysis."""
        request_lower = user_request.lower()
        required_agents = []
        
        # Branding agent - for brand identity, naming, concepts
        if any(word in request_lower for word in ["brand", "identity", "name", "branding"]):
            required_agents.append("branding")
        
        # Logo generation - for visual logo creation
        if any(word in request_lower for word in ["logo", "visual", "image", "design", "dall-e", "generate logo"]):
            required_agents.append("logo_generation")
        
        # Market research - for analysis and competition
        if any(word in request_lower for word in ["market", "research", "competition", "analysis", "industry", "competitive"]):
            required_agents.append("market_research")
        
        # Website generation - for web presence
        if any(word in request_lower for word in ["website", "site", "web", "landing", "homepage", "page", "sitemap"]):
            required_agents.append("website_generation")
        
        # Smart defaults for comprehensive requests
        comprehensive_keywords = ["complete", "full", "entire", "comprehensive", "everything"]
        if any(word in request_lower for word in comprehensive_keywords):
            # For comprehensive requests, include all relevant agents
            if "business" in request_lower or "company" in request_lower or "startup" in request_lower:
                required_agents = ["branding", "logo_generation", "market_research", "website_generation"]
            elif "brand" in request_lower or "identity" in request_lower:
                required_agents = ["branding", "logo_generation"]
        
        # Business launch keywords - include core agents
        launch_keywords = ["business", "company", "startup", "launch", "new business"]
        if any(word in request_lower for word in launch_keywords) and len(required_agents) == 0:
            required_agents = ["branding", "market_research"]  # Core business agents
        
        # If still nothing specific, default to branding
        if len(required_agents) == 0:
            required_agents = ["branding"]
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(required_agents))
    
    def _estimate_duration(self, required_agents: List[str]) -> Dict[str, int]:
        """Estimate execution duration for each agent."""
        base_durations = {
            "branding": 60,  # 1 minute for branding analysis
            "logo_generation": 180,  # 3 minutes for DALL-E generation (can be slow)
            "market_research": 90,  # 1.5 minutes for market analysis  
            "website_generation": 75   # 1.25 minutes for website structure and content
        }
        
        return {
            agent: base_durations.get(agent, 60) 
            for agent in required_agents
        }
    
    def _assess_resources(self, required_agents: List[str]) -> Dict[str, Any]:
        """Assess resource requirements for parallel execution."""
        anthropic_agents = [a for a in required_agents if a in ["branding", "market_research", "website_generation"]]
        openai_agents = [a for a in required_agents if a in ["logo_generation"]]
        
        return {
            "concurrent_agents": len(required_agents),
            "api_calls_required": {
                "anthropic": len(anthropic_agents),
                "openai": len(openai_agents)
            },
            "estimated_tokens": {
                "branding": 3000,
                "market_research": 4000, 
                "website_generation": 5000,
                "logo_generation": 1000  # Mainly for prompt enhancement
            },
            "total_estimated_tokens": sum(
                {"branding": 3000, "market_research": 4000, "website_generation": 5000, "logo_generation": 1000}
                .get(agent, 2000) for agent in required_agents
            )
        }
    
    async def _assess_risks(self, workflow_state: ParallelWorkflowState, required_agents: List[str]) -> Dict[str, Any]:
        """Assess risks for the planned execution."""
        risk_factors = []
        risk_level = RiskLevel.LOW
        
        # API dependency risks
        if "logo_generation" in required_agents:
            risk_factors.append("DALL-E API dependency - may have billing limits")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        if len(required_agents) > 2:
            risk_factors.append("Multiple concurrent API calls - increased failure probability")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Content risks
        sensitive_patterns = ["medical", "legal", "financial", "political"]
        if any(pattern in workflow_state.user_request.lower() for pattern in sensitive_patterns):
            risk_factors.append("Sensitive content domain detected")
            risk_level = RiskLevel.HIGH
        
        return {
            "level": risk_level.value,
            "factors": risk_factors,
            "mitigation_strategies": self._get_mitigation_strategies(risk_factors),
            "approval_recommended": risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        }
    
    def _get_mitigation_strategies(self, risk_factors: List[str]) -> List[str]:
        """Get mitigation strategies for identified risks."""
        strategies = []
        
        if any("API" in factor for factor in risk_factors):
            strategies.append("Implement graceful fallback for API failures")
            strategies.append("Set appropriate timeouts and retry logic")
        
        if any("concurrent" in factor for factor in risk_factors):
            strategies.append("Stagger agent execution by 1-2 seconds")
            strategies.append("Monitor system resources during execution")
        
        if any("Sensitive" in factor for factor in risk_factors):
            strategies.append("Review content before final delivery")
            strategies.append("Apply content filtering and safety checks")
        
        return strategies
    
    def _needs_human_approval(self, risk_assessment: Dict[str, Any], required_agents: List[str]) -> bool:
        """Determine if human approval is required."""
        # High risk always requires approval
        if risk_assessment.get("level") == "HIGH":
            return True
        
        # Medium risk with multiple agents requires approval
        if risk_assessment.get("level") == "MEDIUM" and len(required_agents) > 2:
            return True
        
        # Logo generation might require approval for brand safety
        if "logo_generation" in required_agents and risk_assessment.get("level") != "LOW":
            return True
        
        return False


class HumanInTheLoopNode:
    """
    Clean Human-in-the-Loop approval gate at the orchestrator level.
    Handles all human interaction without blocking individual agents.
    """
    
    def __init__(self, human_loop_agent: HumanLoopAgent, approval_callback: Optional[Callable] = None):
        self.human_loop_agent = human_loop_agent
        self.approval_callback = approval_callback
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def process_approval(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle human approval process."""
        self.logger.info(f"HumanInTheLoop: Processing approval with state keys: {list(state.keys())}")
        
        workflow_state = ParallelWorkflowState(**state)
        
        # If HITL is bypassed, approve automatically
        if workflow_state.hitl_status == "bypassed":
            workflow_state.hitl_status = "approved"
            workflow_state.human_decision = {
                "approved": True,
                "method": "automatic",
                "reason": "Low risk execution",
                "timestamp": datetime.utcnow().isoformat()
            }
            return workflow_state.__dict__
        
        try:
            self.logger.info(f"Requesting human approval for workflow {workflow_state.workflow_id}")
            
            # Prepare approval request
            approval_request = {
                "workflow_id": workflow_state.workflow_id,
                "user_request": workflow_state.user_request,
                "execution_plan": workflow_state.execution_plan,
                "risk_assessment": workflow_state.risk_assessment,
                "estimated_duration": sum(workflow_state.execution_plan.get("estimated_duration", {}).values()),
                "required_agents": workflow_state.execution_plan.get("required_agents", [])
            }
            
            # Use callback if provided, otherwise use simple approval
            if self.approval_callback:
                decision = await self.approval_callback(approval_request)
            else:
                # Simple approval for demo
                decision = {
                    "approved": True,
                    "method": "auto_approval",
                    "reason": "Demo mode - auto approved",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Process decision
            workflow_state.human_decision = decision
            workflow_state.hitl_status = "approved" if decision.get("approved", False) else "rejected"
            
            if workflow_state.hitl_status == "rejected":
                workflow_state.overall_status = "cancelled"
                workflow_state.add_error("Execution cancelled by human reviewer")
            
            self.logger.info(f"Human decision: {workflow_state.hitl_status}")
            
            return workflow_state.__dict__
            
        except Exception as e:
            self.logger.error(f"Human approval process failed: {e}")
            # Default to requiring manual approval
            workflow_state.hitl_status = "approval_failed"
            workflow_state.add_error(f"Approval process failed: {str(e)}")
            return workflow_state.__dict__


class ParallelAgentExecutorNode:
    """
    Executes all required agents in parallel without blocking.
    Each agent runs independently and results are collected as they complete.
    """
    
    def __init__(self, persistent_system: PersistentSystem):
        self.persistent_system = persistent_system
        self.error_handler = WorkflowErrorHandler()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all required agents in parallel."""
        self.logger.info(f"ParallelAgentExecutor: Starting execution with state keys: {list(state.keys())}")
        
        workflow_state = ParallelWorkflowState(**state)
        
        # Check if execution is approved
        if workflow_state.hitl_status not in ["approved", "bypassed"]:
            workflow_state.add_error("Cannot execute - approval not granted")
            return workflow_state.__dict__
        
        required_agents = workflow_state.execution_plan.get("required_agents", [])
        self.logger.info(f"Execution plan received: {workflow_state.execution_plan}")
        self.logger.info(f"Required agents: {required_agents}")
        
        if not required_agents:
            self.logger.warning("No agents required for execution - completing workflow")
            workflow_state.add_warning("No agents required for execution")
            workflow_state.overall_status = "completed"
            return workflow_state.__dict__
        
        try:
            self.logger.info(f"Starting parallel execution of {len(required_agents)} agents")
            workflow_state.overall_status = "executing"
            
            # Submit all agent tasks in parallel (non-blocking)
            agent_tasks = {}
            for agent_name in required_agents:
                try:
                    task_data = self._prepare_agent_task(agent_name, workflow_state)
                    self.logger.info(f"Submitting task for {agent_name}: {task_data}")
                    
                    task_ids = await self.persistent_system.submit_task(
                        task=task_data,
                        user_id=workflow_state.session_id,
                        session_id=workflow_state.session_id,
                        workflow_id=workflow_state.workflow_id,
                        requires_approval=False  # Already approved at orchestrator level
                    )
                    self.logger.info(f"Task submitted for {agent_name}, received IDs: {task_ids}")
                    
                    task_id = task_ids.get("task_id")
                    if task_id:
                        agent_tasks[agent_name] = task_id
                        workflow_state.agent_tasks[agent_name] = task_id
                        workflow_state.agent_statuses[agent_name] = "submitted"
                        self.logger.info(f"Submitted {agent_name} task: {task_id}")
                    else:
                        workflow_state.agent_statuses[agent_name] = "failed"
                        workflow_state.agent_errors[agent_name] = "Failed to submit task"
                        
                except Exception as e:
                    self.logger.error(f"Failed to submit {agent_name} task: {e}")
                    
                    # Use error handler to determine recovery strategy
                    recovery_result = await self.error_handler.handle_workflow_error(
                        e, 
                        {"agent": agent_name, "task_data": task_data},
                        f"agent_submission_{agent_name}"
                    )
                    
                    if recovery_result.success:
                        self.logger.info(f"Recovery successful for {agent_name}: {recovery_result.message}")
                        workflow_state.agent_statuses[agent_name] = "recovered"
                    else:
                        workflow_state.agent_statuses[agent_name] = "failed"
                        workflow_state.agent_errors[agent_name] = f"{str(e)} | Recovery: {recovery_result.message}"
                        workflow_state.failed_agents.append(agent_name)
            
            # Update progress
            workflow_state.update_progress()
            
            # Don't wait for completion here - return immediately
            # Results will be collected by the ResultCollectorNode
            workflow_state.overall_status = "agents_running"
            
            self.logger.info(f"All agent tasks submitted. Running agents: {list(agent_tasks.keys())}")
            
            return workflow_state.__dict__
            
        except Exception as e:
            self.logger.error(f"Parallel agent execution failed: {e}")
            workflow_state.add_error(f"Agent execution failed: {str(e)}")
            return workflow_state.__dict__
    
    def _prepare_agent_task(self, agent_name: str, workflow_state: ParallelWorkflowState) -> Dict[str, Any]:
        """Prepare task data for specific agent."""
        base_data = {
            "business_idea": workflow_state.user_request,
            "session_id": workflow_state.session_id,
            "workflow_id": workflow_state.workflow_id
        }
        
        # Add agent-specific context and task configuration
        if agent_name == "branding":
            return {
                "task_type": "branding",
                "input_data": {
                    **base_data,
                    "comprehensive": True,
                    "include_logo_prompt": True,
                    "include_brand_guidelines": True
                }
            }
        elif agent_name == "logo_generation":
            return {
                "task_type": "logo_generation", 
                "input_data": {
                    **base_data,
                    "business_type": "general",
                    "style_preferences": ["modern", "professional", "clean"],
                    "logo_variations": 3,  # Generate 3 logo variations
                    "format": "PNG",
                    "size": "1024x1024"
                }
            }
        elif agent_name == "market_research":
            return {
                "task_type": "market_research",
                "input_data": {
                    **base_data,
                    "research_depth": "comprehensive",
                    "include_competitors": True,
                    "include_market_size": True,
                    "include_trends": True,
                    "target_analysis": True
                }
            }
        elif agent_name == "website_generation":
            return {
                "task_type": "website_generation",
                "input_data": {
                    **base_data,
                    "site_type": "business",
                    "include_seo": True,
                    "include_sitemap": True,
                    "include_copy": True,
                    "include_cta": True,
                    "responsive": True
                }
            }
        else:
            # Generic task fallback
            return {
                "task_type": agent_name,
                "input_data": base_data
            }


class ResultCollectorNode:
    """
    Collects results from parallel agent execution without blocking.
    Handles partial results, timeouts, and result consolidation.
    """
    
    def __init__(self, persistent_system: PersistentSystem):
        self.persistent_system = persistent_system
        self.workflow_reporter = WorkflowReporter()
        self.error_handler = WorkflowErrorHandler()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def collect_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect results from all running agents."""
        self.logger.info(f"ResultCollector: Starting collection with state keys: {list(state.keys())}")
        workflow_state = ParallelWorkflowState(**state)
        
        self.logger.info(f"Agent tasks to check: {workflow_state.agent_tasks}")
        if not workflow_state.agent_tasks:
            self.logger.warning("No agent tasks to collect results from - completing workflow")
            workflow_state.add_warning("No agent tasks to collect results from")
            workflow_state.overall_status = "completed"
            return workflow_state.__dict__
        
        try:
            self.logger.info(f"Collecting results from {len(workflow_state.agent_tasks)} agents")
            
            # Check results for each agent task
            for agent_name, task_id in workflow_state.agent_tasks.items():
                if agent_name in workflow_state.completed_agents:
                    continue  # Already completed
                
                try:
                    # Non-blocking result check
                    result = await self.persistent_system.get_task_result(task_id)
                    
                    if result is not None:
                        # Task completed
                        if result.get("success", False):
                            workflow_state.agent_results[agent_name] = result
                            workflow_state.agent_statuses[agent_name] = "completed"
                            workflow_state.completed_agents.append(agent_name)
                            self.logger.info(f"Agent {agent_name} completed successfully")
                        else:
                            # Task failed
                            error_msg = result.get("error", "Unknown error")
                            workflow_state.agent_errors[agent_name] = error_msg
                            workflow_state.agent_statuses[agent_name] = "failed"
                            workflow_state.failed_agents.append(agent_name)
                            self.logger.warning(f"Agent {agent_name} failed: {error_msg}")
                    else:
                        # Task still running
                        workflow_state.agent_statuses[agent_name] = "running"
                        
                except Exception as e:
                    self.logger.error(f"Error checking {agent_name} result: {e}")
                    workflow_state.agent_errors[agent_name] = str(e)
                    workflow_state.agent_statuses[agent_name] = "error"
                    workflow_state.failed_agents.append(agent_name)
            
            # Update progress
            workflow_state.update_progress()
            
            # Track collection attempts to prevent infinite loops
            current_attempts = state.get("collection_attempts", 0)
            workflow_state.__dict__["collection_attempts"] = current_attempts + 1
            
            # Check if all agents are done
            total_agents = len(workflow_state.agent_tasks)
            finished_agents = len(workflow_state.completed_agents) + len(workflow_state.failed_agents)
            
            if finished_agents >= total_agents:
                # All agents finished - handle partial failures if any
                if workflow_state.failed_agents:
                    workflow_state.overall_status = "handling_partial_failures"
                    workflow_state_dict = await self.error_handler.handle_partial_failure(
                        workflow_state.__dict__,
                        workflow_state.failed_agents,
                        workflow_state.completed_agents
                    )
                    # Update workflow state with recovery information
                    for key, value in workflow_state_dict.items():
                        if hasattr(workflow_state, key):
                            setattr(workflow_state, key, value)
                        else:
                            workflow_state.__dict__[key] = value
                
                workflow_state.overall_status = "consolidating"
                await self._consolidate_results(workflow_state)
            else:
                # Still waiting for some agents - add exponential backoff delay
                attempt = workflow_state.__dict__.get("collection_attempts", 1)
                delay = min(2.0 + (attempt * 0.1), 5.0)  # 2s to 5s max delay
                workflow_state.overall_status = "collecting_results"
                self.logger.info(f"Waiting for agents to complete (attempt {attempt}), adding {delay:.1f}s delay...")
                await asyncio.sleep(delay)
            
            self.logger.info(f"Result collection: {len(workflow_state.completed_agents)} completed, {len(workflow_state.failed_agents)} failed, {total_agents - finished_agents} running")
            
            return workflow_state.__dict__
            
        except Exception as e:
            self.logger.error(f"Result collection failed: {e}")
            workflow_state.add_error(f"Result collection failed: {str(e)}")
            return workflow_state.__dict__
    
    async def _consolidate_results(self, workflow_state: ParallelWorkflowState):
        """Consolidate results from all completed agents using enhanced reporting."""
        self.logger.info("Consolidating final results with enhanced reporting")
        
        try:
            # Use the WorkflowReporter for comprehensive result consolidation
            consolidated_report = await self.workflow_reporter.consolidate_workflow_results(workflow_state.__dict__)
            
            # Save reports in both JSON and HTML formats
            json_path = await self.workflow_reporter.save_consolidated_report(consolidated_report, "json")
            html_path = await self.workflow_reporter.save_consolidated_report(consolidated_report, "html")
            
            # Update the final results with enhanced data
            workflow_state.final_results = consolidated_report
            workflow_state.artifacts = {
                "consolidated_report_json": json_path,
                "consolidated_report_html": html_path,
                **consolidated_report.get("artifacts", {})
            }
            
            self.logger.info(f"Enhanced consolidation completed. Reports saved: JSON={json_path}, HTML={html_path}")
            
        except Exception as e:
            self.logger.error(f"Enhanced consolidation failed, falling back to basic consolidation: {e}")
            # Fallback to basic consolidation
            await self._basic_consolidate_results(workflow_state)
        
        workflow_state.overall_status = "completed"
    
    async def _basic_consolidate_results(self, workflow_state: ParallelWorkflowState):
        """Basic result consolidation fallback."""
        consolidated = {
            "workflow_summary": {
                "workflow_id": workflow_state.workflow_id,
                "user_request": workflow_state.user_request,
                "execution_plan": workflow_state.execution_plan,
                "total_agents": len(workflow_state.agent_tasks),
                "successful_agents": len(workflow_state.completed_agents),
                "failed_agents": len(workflow_state.failed_agents),
                "execution_time": (workflow_state.updated_at - workflow_state.created_at).total_seconds()
            },
            "agent_results": workflow_state.agent_results,
            "artifacts": {},
            "recommendations": []
        }
        
        # Extract artifacts from agent results
        for agent_name, result in workflow_state.agent_results.items():
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_path") or key.endswith("_url") or "file" in key.lower():
                        consolidated["artifacts"][f"{agent_name}_{key}"] = value
        
        # Generate basic recommendations
        recommendations = []
        if "branding" in workflow_state.completed_agents and "logo_generation" not in workflow_state.completed_agents:
            recommendations.append("Generate logo images using the created branding prompt")
        
        if len(workflow_state.completed_agents) > 0:
            recommendations.append("Review and refine generated content")
        
        consolidated["recommendations"] = recommendations
        workflow_state.final_results = consolidated


class ParallelIntelligentGraphBuilder:
    """
    Builds the complete hierarchical parallel LangGraph with intelligence orchestration.
    """
    
    def __init__(
        self, 
        redis_url: Optional[str] = None,
        skip_approvals: bool = False,
        approval_callback: Optional[Callable] = None
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.skip_approvals = skip_approvals
        self.approval_callback = approval_callback
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components (will be initialized)
        self.persistent_system: Optional[PersistentSystem] = None
        self.workflow_brain: Optional[WorkflowBrain] = None
        self.human_loop_agent: Optional[HumanLoopAgent] = None
    
    async def build(self):
        """Build the complete hierarchical parallel workflow graph."""
        if not USE_LANGGRAPH:
            raise RuntimeError("LangGraph is not installed. Install 'langgraph' to use this pipeline.")
        
        self.logger.info("Building hierarchical parallel LangGraph")
        
        # Initialize core systems
        await self._initialize_systems()
        
        # Create the hierarchical graph
        graph = StateGraph(dict)
        
        # Initialize nodes
        intelligence_node = IntelligenceOrchestratorNode(self.workflow_brain)
        hitl_node = HumanInTheLoopNode(self.human_loop_agent, self.approval_callback)
        executor_node = ParallelAgentExecutorNode(self.persistent_system)
        collector_node = ResultCollectorNode(self.persistent_system)
        
        # Add nodes to graph
        graph.add_node("intelligence_orchestrator", intelligence_node.analyze_and_plan)
        graph.add_node("human_approval", hitl_node.process_approval)
        graph.add_node("parallel_execution", executor_node.execute_agents)
        graph.add_node("result_collection", collector_node.collect_results)
        
        # Define workflow edges
        graph.add_edge(START, "intelligence_orchestrator")
        graph.add_edge("intelligence_orchestrator", "human_approval")
        
        # Conditional edge based on approval
        graph.add_conditional_edges(
            "human_approval",
            self._approval_condition,
            {
                "approved": "parallel_execution",
                "rejected": END,
                "error": END
            }
        )
        
        graph.add_edge("parallel_execution", "result_collection")
        
        # Conditional edge for result collection (may need to loop)
        graph.add_conditional_edges(
            "result_collection",
            self._collection_condition,
            {
                "completed": END,
                "collecting": "result_collection"  # Loop back to collect more results
            }
        )
        
        # Compile the graph with performance optimizations
        app = graph.compile(
            checkpointer=MemorySaver(),
            # Increase recursion limit for complex workflows
            # Set interrupt points for better control
        )
        
        self.logger.info("Hierarchical parallel LangGraph built successfully")
        return app, self.persistent_system, self.workflow_brain
    
    async def _initialize_systems(self):
        """Initialize all required systems."""
        # Initialize PersistentSystem
        config = PersistentSystemConfig(
            redis_url=self.redis_url,
            skip_approvals=self.skip_approvals
        )
        self.persistent_system = PersistentSystem(config)
        await self.persistent_system.start()
        
        # Initialize WorkflowBrain
        brain_config = {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "redis_url": self.redis_url
        }
        self.workflow_brain = WorkflowBrain(brain_config)
        
        # Initialize HumanLoopAgent
        self.human_loop_agent = HumanLoopAgent()
    
    def _approval_condition(self, state: Dict[str, Any]) -> str:
        """Determine next step based on approval status."""
        hitl_status = state.get("hitl_status", "pending")
        
        self.logger.info(f"Approval condition check: hitl_status={hitl_status}")
        
        if hitl_status in ["approved", "bypassed"]:
            self.logger.info("Routing to parallel_execution")
            return "approved"
        elif hitl_status == "rejected":
            self.logger.info("Routing to END (rejected)")
            return "rejected"
        else:
            self.logger.info(f"Routing to END (error) - unhandled status: {hitl_status}")
            return "error"
    
    def _collection_condition(self, state: Dict[str, Any]) -> str:
        """Determine if result collection is complete."""
        overall_status = state.get("overall_status", "unknown")
        
        # Check for max collection attempts to prevent infinite loops
        collection_attempts = state.get("collection_attempts", 0)
        max_attempts = 30  # Max 60 seconds of collection (30 * 2s delay)
        
        self.logger.info(f"Collection condition check: overall_status={overall_status}, attempts={collection_attempts}")
        
        if overall_status == "completed":
            self.logger.info("Collection complete - routing to END")
            return "completed"
        elif overall_status in ["collecting_results", "consolidating", "agents_running"]:
            if collection_attempts >= max_attempts:
                self.logger.warning(f"Max collection attempts ({max_attempts}) reached - ending collection")
                return "completed"
            self.logger.info("Collection continuing - routing back to result_collection")
            return "collecting"
        else:
            self.logger.info(f"Collection ending due to status: {overall_status}")
            return "completed"  # End on error states


# Convenience function for easy usage
async def create_parallel_intelligent_workflow(
    redis_url: Optional[str] = None,
    skip_approvals: bool = True,
    approval_callback: Optional[Callable] = None
):
    """Create a ready-to-use parallel intelligent workflow."""
    builder = ParallelIntelligentGraphBuilder(
        redis_url=redis_url,
        skip_approvals=skip_approvals, 
        approval_callback=approval_callback
    )
    return await builder.build()