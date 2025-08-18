"""
DecisionEngine - Process human decisions and AI recommendations to determine optimal workflow paths.

This engine validates human decisions, handles custom inputs, and merges human intelligence
with AI recommendations to create optimal execution plans.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .models import (
    WorkflowState,
    WorkflowStep,
    HumanDecision,
    NextStepOption,
    AutoPilotMode,
    StepStatus,
    WorkflowStatus,
    RiskLevel
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Processes human decisions and AI recommendations to create optimal workflow execution plans.
    
    Key responsibilities:
    - Validate human decisions against workflow constraints
    - Process custom human inputs into actionable steps
    - Merge human intelligence with AI recommendations
    - Handle decision conflicts and edge cases
    - Provide decision explanations and reasoning
    """
    
    def __init__(self):
        """Initialize the Decision Engine."""
        self.logger = logging.getLogger(__name__)
        
        # Decision processing state
        self.decision_history: Dict[str, List[HumanDecision]] = {}
        self.validation_rules: Dict[str, Any] = {}
        
        self.logger.info("DecisionEngine initialized")
    
    async def process_human_decision(
        self,
        human_decision: HumanDecision,
        ai_recommendations: List[NextStepOption],
        workflow_state: WorkflowState
    ) -> WorkflowStep:
        """
        Process human decision and convert it to an executable workflow step.
        
        Args:
            human_decision: The decision made by the human
            ai_recommendations: Available AI-generated options
            workflow_state: Current workflow state
            
        Returns:
            WorkflowStep ready for execution
        """
        self.logger.info(f"Processing human decision: {human_decision.human_choice}")
        
        try:
            # Validate the human decision
            validation_result = await self._validate_human_decision(
                human_decision, ai_recommendations, workflow_state
            )
            
            if not validation_result.is_valid:
                self.logger.warning(f"Decision validation failed: {validation_result.reason}")
                # Fall back to safest AI recommendation
                return await self._create_fallback_step(ai_recommendations, workflow_state)
            
            # Process different types of decisions
            if human_decision.human_choice.startswith('option_'):
                return await self._process_ai_recommendation_choice(
                    human_decision, ai_recommendations, workflow_state
                )
            elif human_decision.human_choice.startswith('custom:'):
                return await self._process_custom_decision(
                    human_decision, workflow_state
                )
            elif human_decision.human_choice in ['pause', 'emergency_stop', 'skip', 'back']:
                return await self._process_control_command(
                    human_decision, workflow_state
                )
            else:
                return await self._create_fallback_step(ai_recommendations, workflow_state)
                
        except Exception as e:
            self.logger.error(f"Error processing human decision: {e}")
            return await self._create_fallback_step(ai_recommendations, workflow_state)
    
    async def _validate_human_decision(
        self,
        human_decision: HumanDecision,
        ai_recommendations: List[NextStepOption],
        workflow_state: WorkflowState
    ) -> 'ValidationResult':
        """Validate human decision against workflow constraints."""
        
        # Check for emergency states
        if workflow_state.emergency_pause:
            return ValidationResult(False, "Workflow is in emergency pause state")
        
        # Validate option selection
        if human_decision.human_choice.startswith('option_'):
            try:
                option_num = int(human_decision.human_choice.split('_')[1])
                if 1 <= option_num <= len(ai_recommendations):
                    return ValidationResult(True, "Valid AI recommendation selection")
                else:
                    return ValidationResult(False, f"Option {option_num} not available")
            except (ValueError, IndexError):
                return ValidationResult(False, "Invalid option format")
        
        # Validate custom input
        elif human_decision.human_choice.startswith('custom:'):
            if not human_decision.custom_input or len(human_decision.custom_input.strip()) < 5:
                return ValidationResult(False, "Custom input too short or empty")
            return ValidationResult(True, "Valid custom input")
        
        # Validate control commands
        elif human_decision.human_choice in ['pause', 'emergency_stop', 'skip', 'back']:
            return ValidationResult(True, "Valid control command")
        
        else:
            return ValidationResult(False, f"Unrecognized decision type: {human_decision.human_choice}")
    
    async def _process_ai_recommendation_choice(
        self,
        human_decision: HumanDecision,
        ai_recommendations: List[NextStepOption],
        workflow_state: WorkflowState
    ) -> WorkflowStep:
        """Process human selection of an AI recommendation."""
        
        option_num = int(human_decision.human_choice.split('_')[1])
        chosen_option = ai_recommendations[option_num - 1]
        
        self.logger.info(f"Human chose AI recommendation {option_num}: {chosen_option.description}")
        
        # Create workflow step from AI recommendation
        workflow_step = WorkflowStep(
            step_id="",  # Auto-generated
            step_type=chosen_option.step_type,
            agent_id=chosen_option.agent_id,
            description=chosen_option.description,
            input_state=self._prepare_input_state(chosen_option, workflow_state),
            status=StepStatus.PENDING,
            human_decision_id=human_decision.decision_id,
            confidence_score=chosen_option.confidence_score
        )
        
        # Add human decision context
        workflow_step.input_state['human_decision'] = {
            'chosen_option_id': chosen_option.option_id,
            'decision_reasoning': human_decision.reasoning,
            'confidence_override': human_decision.confidence_override
        }
        
        return workflow_step
    
    async def _process_custom_decision(
        self,
        human_decision: HumanDecision,
        workflow_state: WorkflowState
    ) -> WorkflowStep:
        """Process custom human input into executable step."""
        
        custom_input = human_decision.custom_input
        self.logger.info(f"Processing custom decision: {custom_input}")
        
        # Parse custom input to determine step type and agent
        step_analysis = await self._analyze_custom_input(custom_input, workflow_state)
        
        # Create workflow step from custom input
        workflow_step = WorkflowStep(
            step_id="",  # Auto-generated
            step_type=step_analysis.step_type,
            agent_id=step_analysis.suggested_agent,
            description=f"Custom step: {custom_input}",
            input_state=self._prepare_custom_input_state(step_analysis, workflow_state),
            status=StepStatus.PENDING,
            human_decision_id=human_decision.decision_id,
            confidence_score=0.7  # Lower confidence for custom steps
        )
        
        # Add custom decision context
        workflow_step.input_state['custom_decision'] = {
            'original_input': custom_input,
            'parsed_intent': step_analysis.intent,
            'suggested_agent': step_analysis.suggested_agent,
            'confidence': step_analysis.confidence
        }
        
        return workflow_step
    
    async def _process_control_command(
        self,
        human_decision: HumanDecision,
        workflow_state: WorkflowState
    ) -> WorkflowStep:
        """Process workflow control commands (pause, stop, etc.)."""
        
        command = human_decision.human_choice
        self.logger.info(f"Processing control command: {command}")
        
        if command == 'pause':
            workflow_state.user_requested_pause = True
            workflow_state.status = WorkflowStatus.PAUSED
        elif command == 'emergency_stop':
            workflow_state.emergency_pause = True
            workflow_state.status = WorkflowStatus.CANCELLED
        elif command == 'skip':
            # Create a skip step
            pass
        elif command == 'back':
            # Handle going back to previous step
            pass
        
        # Create control step
        control_step = WorkflowStep(
            step_id="",
            step_type="control_command",
            agent_id="system",
            description=f"User requested: {command}",
            input_state={'command': command, 'workflow_id': workflow_state.workflow_id},
            status=StepStatus.COMPLETED,  # Control commands execute immediately
            human_decision_id=human_decision.decision_id,
            confidence_score=1.0  # User control commands have full confidence
        )
        
        return control_step
    
    async def _analyze_custom_input(
        self,
        custom_input: str,
        workflow_state: WorkflowState
    ) -> 'CustomStepAnalysis':
        """Analyze custom input to determine appropriate step type and agent."""
        
        # Simple keyword-based analysis (can be enhanced with NLP)
        input_lower = custom_input.lower()
        
        # Determine step type and agent based on keywords
        if any(keyword in input_lower for keyword in ['research', 'analyze', 'market', 'competitor']):
            return CustomStepAnalysis(
                step_type="market_research",
                suggested_agent="market_research_agent",
                intent="market_analysis",
                confidence=0.8
            )
        elif any(keyword in input_lower for keyword in ['brand', 'logo', 'design', 'name']):
            return CustomStepAnalysis(
                step_type="branding",
                suggested_agent="branding_agent",
                intent="branding_development",
                confidence=0.8
            )
        elif any(keyword in input_lower for keyword in ['strategy', 'plan', 'business']):
            return CustomStepAnalysis(
                step_type="business_planning",
                suggested_agent="jarvis",
                intent="strategic_planning",
                confidence=0.7
            )
        else:
            # Generic custom step
            return CustomStepAnalysis(
                step_type="custom_analysis",
                suggested_agent="universal_orchestrator",
                intent="general_processing",
                confidence=0.6
            )
    
    def _prepare_input_state(
        self,
        chosen_option: NextStepOption,
        workflow_state: WorkflowState
    ) -> Dict[str, Any]:
        """Prepare input state for chosen AI recommendation."""
        
        input_state = workflow_state.current_context.copy()
        
        # Add specific inputs required by the chosen option
        for required_input in chosen_option.required_inputs:
            if required_input in workflow_state.accumulated_data:
                input_state[required_input] = workflow_state.accumulated_data[required_input]
        
        # Add workflow metadata
        input_state['workflow_context'] = {
            'workflow_id': workflow_state.workflow_id,
            'step_index': workflow_state.current_step_index,
            'chosen_option_id': chosen_option.option_id,
            'estimated_time_minutes': chosen_option.estimated_time_minutes
        }
        
        return input_state
    
    def _prepare_custom_input_state(
        self,
        step_analysis: 'CustomStepAnalysis',
        workflow_state: WorkflowState
    ) -> Dict[str, Any]:
        """Prepare input state for custom human decision."""
        
        input_state = workflow_state.current_context.copy()
        
        # Add custom step context
        input_state['custom_context'] = {
            'workflow_id': workflow_state.workflow_id,
            'step_index': workflow_state.current_step_index,
            'custom_intent': step_analysis.intent,
            'analysis_confidence': step_analysis.confidence
        }
        
        return input_state
    
    async def _create_fallback_step(
        self,
        ai_recommendations: List[NextStepOption],
        workflow_state: WorkflowState
    ) -> WorkflowStep:
        """Create fallback step when decision processing fails."""
        
        # Use the highest confidence AI recommendation as fallback
        if ai_recommendations:
            best_option = max(ai_recommendations, key=lambda x: x.confidence_score)
            self.logger.info(f"Using fallback step: {best_option.description}")
            
            return WorkflowStep(
                step_id="",
                step_type=best_option.step_type,
                agent_id=best_option.agent_id,
                description=f"Fallback: {best_option.description}",
                input_state=self._prepare_input_state(best_option, workflow_state),
                status=StepStatus.PENDING,
                confidence_score=best_option.confidence_score * 0.8  # Reduce confidence for fallback
            )
        else:
            # Create minimal fallback step
            return WorkflowStep(
                step_id="",
                step_type="system_pause",
                agent_id="system",
                description="Workflow paused due to decision processing error",
                input_state={'workflow_id': workflow_state.workflow_id},
                status=StepStatus.PENDING,
                confidence_score=0.1
            )
    
    def should_bypass_human_input(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> Tuple[bool, str]:
        """
        Determine if human input should be bypassed based on autopilot settings.
        
        Returns:
            Tuple of (should_bypass, reason)
        """
        # Check autopilot mode
        if workflow_state.autopilot_mode == AutoPilotMode.FULL_AUTO:
            return True, "Full autopilot mode enabled"
        
        elif workflow_state.autopilot_mode == AutoPilotMode.HUMAN_CONTROL:
            return False, "Human control mode - always ask for input"
        
        elif workflow_state.autopilot_mode == AutoPilotMode.SMART_AUTO:
            if ai_recommendations:
                highest_confidence = max(rec.confidence_score for rec in ai_recommendations)
                if highest_confidence >= 0.85:  # Smart autopilot threshold
                    return True, f"Smart autopilot - high AI confidence ({highest_confidence:.1%})"
                else:
                    return False, f"Smart autopilot - low AI confidence ({highest_confidence:.1%})"
            else:
                return False, "Smart autopilot - no AI recommendations available"
        
        else:
            return False, "Unknown autopilot mode"


# Supporting data classes
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of decision validation."""
    is_valid: bool
    reason: str


@dataclass
class CustomStepAnalysis:
    """Analysis result for custom human input."""
    step_type: str
    suggested_agent: str
    intent: str
    confidence: float