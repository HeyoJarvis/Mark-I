"""
WorkflowBrain - Main Intelligence Agent for Human-in-the-Loop Workflow Orchestration.

The WorkflowBrain serves as the meta-orchestrator that coordinates complex multi-step workflows
with intelligent human interaction points, providing AI-powered next step predictions while
maintaining user control and oversight.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Import AI engine infrastructure  
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

# Import existing orchestration components
from ..universal_orchestrator import UniversalOrchestrator
from ..agent_integration import AgentExecutor, AgentMessageBus

# Import Intelligence Layer components
from .models import (
    WorkflowState,
    WorkflowStep,
    NextStepOption,
    HumanDecision,
    HITLPreferences,
    AutoPilotMode,
    WorkflowStatus,
    StepStatus,
    WorkflowResult,
    RiskLevel
)
from .human_loop_agent import HumanLoopAgent
from .decision_engine import DecisionEngine
from .autopilot_manager import AutoPilotManager

logger = logging.getLogger(__name__)


class WorkflowBrain:
    """
    Main Intelligence Agent for orchestrating complex workflows with human oversight.
    
    The WorkflowBrain provides:
    - Multi-step workflow planning and execution
    - AI-powered next step prediction
    - Human-in-the-loop decision points
    - Intelligent autopilot with user control
    - Context-aware agent coordination
    - Learning from execution patterns
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Workflow Brain.
        
        Args:
            config: Configuration including API keys and orchestrator settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine for workflow intelligence
        self._initialize_ai_engine()
        
        # Initialize core components
        self.human_loop_agent = HumanLoopAgent()
        self.decision_engine = DecisionEngine()
        self.autopilot_manager = AutoPilotManager()
        
        # Initialize orchestrator integration
        self.universal_orchestrator: Optional[UniversalOrchestrator] = None
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Workflow state management
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: Dict[str, WorkflowResult] = {}
        
        # User preferences
        self.user_preferences: Dict[str, HITLPreferences] = {}
        
        # Workflow templates and patterns
        self.workflow_templates: Dict[str, Any] = {}
        self.execution_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
        self.logger.info("WorkflowBrain initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for workflow intelligence."""
        try:
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using rule-based fallbacks")
                self.ai_engine = None
                return
            
            # Configure AI engine for workflow intelligence
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistent workflow logic
                enable_cache=False,  # Fresh analysis for each workflow decision
                timeout_seconds=300
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("Workflow AI engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize workflow AI engine: {e}")
            self.ai_engine = None
    
    async def initialize_orchestration(self):
        """Initialize integration with existing orchestration layer."""
        try:
            # Initialize universal orchestrator for agent coordination
            from ..universal_orchestrator import UniversalOrchestratorConfig
            
            orchestrator_config = UniversalOrchestratorConfig(
                anthropic_api_key=self.config.get('anthropic_api_key'),
                redis_url=self.config.get('redis_url', 'redis://localhost:6379')
            )
            
            self.universal_orchestrator = UniversalOrchestrator(orchestrator_config)
            await self.universal_orchestrator.initialize()
            
            self.logger.info("Orchestration integration initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestration: {e}")
    
    async def create_workflow(
        self,
        user_id: str,
        session_id: str,
        workflow_type: str,
        initial_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new intelligent workflow.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workflow_type: Type of workflow (business_creation, agent_development, etc.)
            initial_request: User's initial request
            context: Additional context information
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"Creating workflow {workflow_id} for user {user_id}: {workflow_type}")
        
        try:
            # Analyze initial request and create workflow plan
            workflow_plan = await self._analyze_and_plan_workflow(
                user_id, workflow_type, initial_request, context or {}
            )
            
            # Create workflow state
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                user_id=user_id,
                session_id=session_id,
                workflow_type=workflow_type,
                workflow_title=workflow_plan['title'],
                status=WorkflowStatus.CREATED,
                total_estimated_steps=len(workflow_plan['steps']),
                initial_context={'initial_request': initial_request},
                current_context=context or {},
                pending_steps=[self._create_workflow_step(step_data) for step_data in workflow_plan['steps']],
                autopilot_mode=self._get_user_autopilot_preference(user_id)
            )
            
            # Store workflow
            self.active_workflows[workflow_id] = workflow_state
            
            self.logger.info(f"Workflow {workflow_id} created with {len(workflow_plan['steps'])} planned steps")
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def execute_workflow(self, workflow_id: str) -> WorkflowResult:
        """
        Execute a workflow with intelligent human-in-the-loop decision points.
        
        Args:
            workflow_id: ID of workflow to execute
            
        Returns:
            Final workflow result
        """
        self.logger.info(f"Starting execution of workflow {workflow_id}")
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_state = self.active_workflows[workflow_id]
        workflow_state.status = WorkflowStatus.IN_PROGRESS
        
        try:
            while workflow_state.is_active and not workflow_state.emergency_pause:
                # Execute next workflow step
                step_result = await self._execute_next_step(workflow_state)
                
                # Handle step result
                if step_result.requires_human_input:
                    workflow_state.status = WorkflowStatus.AWAITING_HUMAN
                    break
                elif step_result.should_pause:
                    workflow_state.status = WorkflowStatus.PAUSED
                    break
                elif step_result.is_complete:
                    workflow_state.status = WorkflowStatus.COMPLETED
                    break
                elif step_result.has_error:
                    await self._handle_workflow_error(workflow_state, step_result.error)
            
            # Generate final result
            final_result = await self._generate_workflow_result(workflow_state)
            self.workflow_history[workflow_id] = final_result
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            workflow_state.status = WorkflowStatus.FAILED
            raise
    
    async def _execute_next_step(self, workflow_state: WorkflowState) -> 'StepExecutionResult':
        """Execute the next step in the workflow with intelligent decision-making."""
        
        try:
            # Generate AI recommendations for next steps
            ai_recommendations = await self._generate_next_step_recommendations(workflow_state)
            
            # Check if autopilot should handle this step
            autopilot_decision = await self.autopilot_manager.evaluate_autopilot_decision(
                workflow_state, 
                ai_recommendations,
                self.user_preferences.get(workflow_state.user_id)
            )
            
            if autopilot_decision.should_proceed_automatically and autopilot_decision.chosen_option:
                # Automatic execution
                self.logger.info(f"Autopilot executing: {autopilot_decision.reasoning}")
                chosen_step = self._convert_option_to_step(autopilot_decision.chosen_option, workflow_state)
                
                # Record autopilot success
                self.autopilot_manager.record_auto_step_success(workflow_state.workflow_id)
                
            else:
                # Request human decision
                self.logger.info(f"Requesting human input: {autopilot_decision.reasoning}")
                
                human_decision = await self.human_loop_agent.request_human_decision(
                    workflow_state,
                    ai_recommendations,
                    {'autopilot_reasoning': autopilot_decision.reasoning}
                )
                
                # Process human decision
                chosen_step = await self.decision_engine.process_human_decision(
                    human_decision,
                    ai_recommendations,
                    workflow_state
                )
                
                # Reset autopilot counters on human intervention
                self.autopilot_manager.reset_autopilot_counters(workflow_state.workflow_id)
            
            # Execute the chosen step
            execution_result = await self._execute_workflow_step(chosen_step, workflow_state)
            
            # Update workflow state
            self._update_workflow_state(workflow_state, chosen_step, execution_result)
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow step: {e}")
            return StepExecutionResult(
                has_error=True,
                error=str(e),
                requires_human_input=False
            )
    
    async def _generate_next_step_recommendations(
        self,
        workflow_state: WorkflowState
    ) -> List[NextStepOption]:
        """Generate AI-powered recommendations for next workflow steps."""
        
        if not self.ai_engine:
            return self._generate_rule_based_recommendations(workflow_state)
        
        try:
            # Create analysis prompt
            prompt = self._create_next_step_analysis_prompt(workflow_state)
            
            # Get AI recommendations
            response = await self.ai_engine.generate(prompt)
            
            # Parse and validate recommendations
            recommendations = self._parse_ai_recommendations(response.content, workflow_state)
            
            self.logger.info(f"Generated {len(recommendations)} AI recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"AI recommendation generation failed: {e}")
            return self._generate_rule_based_recommendations(workflow_state)
    
    def _create_next_step_analysis_prompt(self, workflow_state: WorkflowState) -> str:
        """Create prompt for AI analysis of next workflow steps."""
        
        prompt = f"""
        Analyze the current workflow state and recommend optimal next steps.
        
        WORKFLOW CONTEXT:
        - Type: {workflow_state.workflow_type}
        - Title: {workflow_state.workflow_title}
        - Progress: {workflow_state.progress_percentage:.1f}% complete
        - Completed Steps: {len(workflow_state.completed_steps)}
        - Current Context: {workflow_state.current_context}
        - Accumulated Data: {list(workflow_state.accumulated_data.keys())}
        
        COMPLETED STEPS:
        {self._format_completed_steps(workflow_state)}
        
        PENDING STEPS:
        {self._format_pending_steps(workflow_state)}
        
        USER INFORMATION:
        - User ID: {workflow_state.user_id}
        - Autopilot Mode: {workflow_state.autopilot_mode.value}
        - Previous Human Decisions: {len(workflow_state.human_decisions)}
        
        Based on this context, provide 2-4 recommended next steps in this EXACT format:
        
        RECOMMENDATIONS:
        1. STEP_TYPE: [step_type]
           AGENT: [agent_id] 
           DESCRIPTION: [clear description of what this step does]
           ESTIMATED_TIME: [minutes]
           CONFIDENCE: [0.0-1.0]
           RISK_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
           REASONING: [why this step is recommended now]
           REQUIRED_INPUTS: [list of required data]
           EXPECTED_OUTPUTS: [list of expected results]
        
        2. [repeat format for each recommendation]
        
        Focus on the most logical next steps given the current state and user goals.
        Consider dependencies, available data, and workflow efficiency.
        """
        
        return prompt
    
    def _parse_ai_recommendations(
        self,
        ai_response: str,
        workflow_state: WorkflowState
    ) -> List[NextStepOption]:
        """Parse AI response into structured NextStepOption objects."""
        
        recommendations = []
        
        # Simple parsing - can be enhanced with more sophisticated NLP
        sections = ai_response.split('\n\n')
        
        for section in sections:
            if 'STEP_TYPE:' in section:
                try:
                    option = self._parse_single_recommendation(section, workflow_state)
                    if option:
                        recommendations.append(option)
                except Exception as e:
                    self.logger.warning(f"Failed to parse recommendation: {e}")
                    continue
        
        # Fallback if parsing failed
        if not recommendations:
            recommendations = self._generate_rule_based_recommendations(workflow_state)
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _parse_single_recommendation(self, section_text: str, workflow_state: WorkflowState) -> Optional[NextStepOption]:
        """Parse a single recommendation section."""
        
        lines = section_text.strip().split('\n')
        recommendation_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'step_type':
                    recommendation_data['step_type'] = value
                elif key == 'agent':
                    recommendation_data['agent_id'] = value
                elif key == 'description':
                    recommendation_data['description'] = value
                elif key == 'estimated_time':
                    try:
                        recommendation_data['estimated_time_minutes'] = int(value.split()[0])
                    except:
                        recommendation_data['estimated_time_minutes'] = 15
                elif key == 'confidence':
                    try:
                        recommendation_data['confidence_score'] = float(value)
                    except:
                        recommendation_data['confidence_score'] = 0.7
                elif key == 'risk_level':
                    recommendation_data['risk_level'] = RiskLevel(value.lower())
                elif key == 'reasoning':
                    recommendation_data['reasoning'] = value
                elif key == 'required_inputs':
                    recommendation_data['required_inputs'] = [inp.strip() for inp in value.split(',')]
                elif key == 'expected_outputs':
                    recommendation_data['expected_outputs'] = [out.strip() for out in value.split(',')]
        
        # Validate required fields
        required_fields = ['step_type', 'agent_id', 'description']
        if not all(field in recommendation_data for field in required_fields):
            return None
        
        return NextStepOption(
            option_id="",  # Auto-generated
            step_type=recommendation_data.get('step_type', 'unknown'),
            description=recommendation_data.get('description', ''),
            agent_id=recommendation_data.get('agent_id', 'unknown'),
            estimated_time_minutes=recommendation_data.get('estimated_time_minutes', 15),
            required_inputs=recommendation_data.get('required_inputs', []),
            expected_outputs=recommendation_data.get('expected_outputs', []),
            confidence_score=recommendation_data.get('confidence_score', 0.7),
            risk_level=recommendation_data.get('risk_level', RiskLevel.MEDIUM),
            reasoning=recommendation_data.get('reasoning', '')
        )
    
    def _generate_rule_based_recommendations(self, workflow_state: WorkflowState) -> List[NextStepOption]:
        """Generate rule-based recommendations when AI is unavailable."""
        
        recommendations = []
        
        # Basic rule-based logic based on workflow type and state
        if workflow_state.workflow_type == 'business_creation':
            if not workflow_state.accumulated_data.get('market_research'):
                recommendations.append(NextStepOption(
                    option_id="",
                    step_type="market_research", 
                    description="Conduct market research analysis",
                    agent_id="market_research_agent",
                    estimated_time_minutes=20,
                    required_inputs=['business_idea'],
                    expected_outputs=['market_size', 'competitors', 'trends'],
                    confidence_score=0.8,
                    risk_level=RiskLevel.LOW,
                    reasoning="Market research is essential for business planning"
                ))
            
            if not workflow_state.accumulated_data.get('brand_name'):
                recommendations.append(NextStepOption(
                    option_id="",
                    step_type="branding",
                    description="Generate brand name and visual identity", 
                    agent_id="branding_agent",
                    estimated_time_minutes=15,
                    required_inputs=['business_idea'],
                    expected_outputs=['brand_name', 'logo_prompt', 'color_palette'],
                    confidence_score=0.8,
                    risk_level=RiskLevel.LOW,
                    reasoning="Branding is important for business identity"
                ))
        
        return recommendations
    
    async def _execute_workflow_step(
        self,
        workflow_step: WorkflowStep,
        workflow_state: WorkflowState
    ) -> 'StepExecutionResult':
        """Execute a single workflow step through appropriate agent."""
        
        self.logger.info(f"Executing step: {workflow_step.description}")
        
        workflow_step.status = StepStatus.IN_PROGRESS
        workflow_step.started_at = datetime.utcnow()
        
        try:
            if workflow_step.agent_id == "system":
                # Handle system/control commands
                return await self._execute_system_step(workflow_step, workflow_state)
            
            elif self.universal_orchestrator:
                # Route through universal orchestrator
                result = await self.universal_orchestrator.process_query(
                    user_query=workflow_step.description,
                    session_id=workflow_state.session_id,
                    context=workflow_step.input_state
                )
                
                # Convert result to step execution result
                return self._convert_orchestrator_result(result, workflow_step)
            
            else:
                return StepExecutionResult(
                    has_error=True,
                    error="No orchestrator available for step execution"
                )
                
        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            workflow_step.status = StepStatus.FAILED
            workflow_step.error_message = str(e)
            
            return StepExecutionResult(
                has_error=True,
                error=str(e)
            )
        finally:
            workflow_step.completed_at = datetime.utcnow()
            if workflow_step.started_at:
                duration_ms = (workflow_step.completed_at - workflow_step.started_at).total_seconds() * 1000
                workflow_step.execution_time_ms = int(duration_ms)
    
    async def _execute_system_step(
        self,
        workflow_step: WorkflowStep,
        workflow_state: WorkflowState
    ) -> 'StepExecutionResult':
        """Execute system/control steps."""
        
        command = workflow_step.input_state.get('command', '')
        
        if command == 'pause':
            workflow_state.user_requested_pause = True
            return StepExecutionResult(should_pause=True)
        elif command == 'emergency_stop':
            workflow_state.emergency_pause = True
            return StepExecutionResult(has_error=True, error="Emergency stop requested")
        else:
            return StepExecutionResult(is_complete=False)
    
    def _convert_orchestrator_result(
        self,
        orchestrator_result: Dict[str, Any],
        workflow_step: WorkflowStep
    ) -> 'StepExecutionResult':
        """Convert orchestrator result to step execution result."""
        
        if orchestrator_result.get('status') == 'success':
            response = orchestrator_result.get('response', {})
            result = response.get('result', {})
            
            workflow_step.output_state = result
            workflow_step.status = StepStatus.COMPLETED
            
            return StepExecutionResult(
                is_complete=False,  # Individual step completed, but workflow continues
                output_data=result
            )
        else:
            error = orchestrator_result.get('error_message', 'Unknown orchestrator error')
            workflow_step.status = StepStatus.FAILED
            workflow_step.error_message = error
            
            return StepExecutionResult(
                has_error=True,
                error=error
            )
    
    def _update_workflow_state(
        self,
        workflow_state: WorkflowState,
        executed_step: WorkflowStep,
        execution_result: 'StepExecutionResult'
    ):
        """Update workflow state after step execution."""
        
        # Move completed step to completed list
        if executed_step.status == StepStatus.COMPLETED:
            workflow_state.mark_step_completed(executed_step)
            
            # Update context with step outputs
            if execution_result.output_data:
                workflow_state.update_context(execution_result.output_data)
        
        # Update overall workflow status
        if execution_result.should_pause:
            workflow_state.status = WorkflowStatus.PAUSED
        elif execution_result.has_error and not execution_result.requires_human_input:
            workflow_state.status = WorkflowStatus.FAILED
        elif len(workflow_state.pending_steps) == 0:
            workflow_state.status = WorkflowStatus.COMPLETED
        
        workflow_state.updated_at = datetime.utcnow()
    
    async def _analyze_and_plan_workflow(
        self,
        user_id: str,
        workflow_type: str,
        initial_request: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze request and create initial workflow plan."""
        
        # Simple workflow planning - can be enhanced with AI
        if workflow_type == 'business_creation':
            return {
                'title': f"Business Creation: {initial_request[:50]}",
                'steps': [
                    {
                        'step_type': 'market_research',
                        'agent_id': 'market_research_agent',
                        'description': 'Analyze market opportunity and competition'
                    },
                    {
                        'step_type': 'branding',
                        'agent_id': 'branding_agent',
                        'description': 'Create brand identity and visual design'
                    },
                    {
                        'step_type': 'business_strategy',
                        'agent_id': 'jarvis',
                        'description': 'Develop business strategy and implementation plan'
                    }
                ]
            }
        else:
            # Heuristic: map generic requests to closest supported agent tasks
            lower_req = initial_request.lower()
            if any(k in lower_req for k in ["brand", "logo", "identity", "design"]):
                return {
                    'title': f"Branding Request: {initial_request[:50]}",
                    'steps': [
                        {
                            'step_type': 'branding',
                            'agent_id': 'branding_agent',
                            'description': f'Generate branding assets for: {initial_request}'
                        }
                    ]
                }
            return {
                'title': f"Custom Workflow: {initial_request[:50]}",
                'steps': [
                    {
                        'step_type': 'analysis',
                        'agent_id': 'universal_orchestrator', 
                        'description': f'Process request: {initial_request}'
                    }
                ]
            }
    
    def _create_workflow_step(self, step_data: Dict[str, Any]) -> WorkflowStep:
        """Create WorkflowStep from step data."""
        
        return WorkflowStep(
            step_id="",
            step_type=step_data['step_type'],
            agent_id=step_data['agent_id'],
            description=step_data['description'],
            input_state={},
            status=StepStatus.PENDING
        )
    
    def _convert_option_to_step(self, option: NextStepOption, workflow_state: WorkflowState) -> WorkflowStep:
        """Convert NextStepOption to executable WorkflowStep."""
        
        return WorkflowStep(
            step_id="",
            step_type=option.step_type,
            agent_id=option.agent_id,
            description=option.description,
            input_state=workflow_state.current_context.copy(),
            status=StepStatus.PENDING,
            confidence_score=option.confidence_score
        )
    
    def _get_user_autopilot_preference(self, user_id: str) -> AutoPilotMode:
        """Get user's autopilot preference."""
        if user_id in self.user_preferences:
            return self.user_preferences[user_id].default_autopilot_mode
        return AutoPilotMode.SMART_AUTO
    
    def _format_completed_steps(self, workflow_state: WorkflowState) -> str:
        """Format completed steps for AI analysis."""
        if not workflow_state.completed_steps:
            return "None"
        
        return "\n".join([
            f"- {step.description} (Output: {list(step.output_state.keys())})"
            for step in workflow_state.completed_steps[-3:]  # Last 3 steps
        ])
    
    def _format_pending_steps(self, workflow_state: WorkflowState) -> str:
        """Format pending steps for AI analysis."""
        if not workflow_state.pending_steps:
            return "None planned"
        
        return "\n".join([
            f"- {step.description}"
            for step in workflow_state.pending_steps[:3]  # Next 3 steps
        ])
    
    async def _generate_workflow_result(self, workflow_state: WorkflowState) -> WorkflowResult:
        """Generate final workflow result."""
        
        return WorkflowResult(
            workflow_id=workflow_state.workflow_id,
            status=workflow_state.status,
            final_outputs=workflow_state.accumulated_data,
            execution_summary={
                'total_steps': len(workflow_state.completed_steps),
                'human_decisions': len(workflow_state.human_decisions),
                'duration_seconds': workflow_state.duration_seconds,
                'autopilot_mode': workflow_state.autopilot_mode.value
            },
            performance_metrics={
                'success_rate': 1.0 if workflow_state.status == WorkflowStatus.COMPLETED else 0.0,
                'efficiency_score': self._calculate_efficiency_score(workflow_state)
            },
            human_interaction_summary={
                'decision_count': len(workflow_state.human_decisions),
                'last_interaction': workflow_state.last_human_interaction.isoformat() if workflow_state.last_human_interaction else None
            }
        )
    
    def _calculate_efficiency_score(self, workflow_state: WorkflowState) -> float:
        """Calculate workflow efficiency score."""
        if not workflow_state.completed_steps:
            return 0.0
        
        # Simple efficiency calculation - can be enhanced
        total_time = sum(step.execution_time_ms or 0 for step in workflow_state.completed_steps)
        estimated_time = len(workflow_state.completed_steps) * 15 * 60 * 1000  # 15 min per step estimate
        
        if estimated_time == 0:
            return 1.0
        
        return min(1.0, estimated_time / max(total_time, 1))
    
    async def _handle_workflow_error(self, workflow_state: WorkflowState, error: str):
        """Handle workflow execution errors."""
        self.logger.error(f"Workflow error: {error}")
        
        # Record failure for autopilot learning
        self.autopilot_manager.record_auto_step_failure(workflow_state.workflow_id)
        
        # Could implement error recovery logic here
        workflow_state.status = WorkflowStatus.FAILED


# Supporting data classes
from dataclasses import dataclass

@dataclass
class StepExecutionResult:
    """Result of executing a workflow step."""
    is_complete: bool = False
    has_error: bool = False
    error: str = ""
    should_pause: bool = False
    requires_human_input: bool = False
    output_data: Optional[Dict[str, Any]] = None