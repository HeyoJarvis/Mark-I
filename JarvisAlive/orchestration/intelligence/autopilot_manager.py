"""
AutoPilotManager - Controls automatic vs. human-controlled workflow execution.

This manager handles user-configurable autopilot settings, smart autopilot based on confidence scores,
emergency human intervention triggers, and workflow-specific automation rules.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .models import (
    WorkflowState,
    NextStepOption,
    AutoPilotMode,
    HITLPreferences,
    RiskLevel,
    WorkflowStatus
)

logger = logging.getLogger(__name__)


@dataclass
class AutoPilotSettings:
    """AutoPilot configuration settings."""
    mode: AutoPilotMode
    confidence_threshold: float = 0.85
    risk_threshold: RiskLevel = RiskLevel.MEDIUM
    max_consecutive_auto_steps: int = 5
    require_human_for_high_risk: bool = True
    emergency_intervention_triggers: List[str] = None
    
    def __post_init__(self):
        if self.emergency_intervention_triggers is None:
            self.emergency_intervention_triggers = [
                "repeated_failures",
                "high_resource_cost", 
                "critical_risk_level",
                "user_data_modification"
            ]


@dataclass
class AutoPilotDecision:
    """Result of autopilot decision-making process."""
    should_proceed_automatically: bool
    chosen_option: Optional[NextStepOption]
    reasoning: str
    confidence_score: float
    requires_human_confirmation: bool = False
    emergency_stop: bool = False


class AutoPilotManager:
    """
    Manages automatic vs. human-controlled workflow execution.
    
    Key responsibilities:
    - Evaluate when to engage autopilot vs. human control
    - Apply user-configurable autopilot rules
    - Monitor workflow health and trigger interventions
    - Handle emergency stop conditions
    - Provide transparency in autopilot decisions
    """
    
    def __init__(self):
        """Initialize the AutoPilot Manager."""
        self.logger = logging.getLogger(__name__)
        
        # User autopilot preferences
        self.user_settings: Dict[str, AutoPilotSettings] = {}
        
        # Autopilot monitoring state
        self.consecutive_auto_steps: Dict[str, int] = {}
        self.failed_auto_attempts: Dict[str, List[datetime]] = {}
        self.intervention_history: Dict[str, List[str]] = {}
        
        # Emergency conditions
        self.emergency_triggers = {
            "repeated_failures": self._check_repeated_failures,
            "high_resource_cost": self._check_high_resource_cost,
            "critical_risk_level": self._check_critical_risk,
            "user_data_modification": self._check_user_data_modification,
            "infinite_loop_detection": self._check_infinite_loop
        }
        
        self.logger.info("AutoPilotManager initialized")
    
    async def evaluate_autopilot_decision(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        user_preferences: Optional[HITLPreferences] = None
    ) -> AutoPilotDecision:
        """
        Evaluate whether to proceed automatically or request human input.
        
        Args:
            workflow_state: Current workflow state
            ai_recommendations: Available AI recommendations
            user_preferences: User's HITL preferences
            
        Returns:
            AutoPilotDecision with recommendation and reasoning
        """
        self.logger.info(f"Evaluating autopilot decision for workflow {workflow_state.workflow_id}")
        
        try:
            # Get autopilot settings for user
            settings = self._get_autopilot_settings(workflow_state.user_id, user_preferences)
            
            # Check for emergency conditions first
            emergency_check = await self._check_emergency_conditions(workflow_state, ai_recommendations)
            if emergency_check.emergency_required:
                return AutoPilotDecision(
                    should_proceed_automatically=False,
                    chosen_option=None,
                    reasoning=f"Emergency intervention required: {emergency_check.reason}",
                    confidence_score=0.0,
                    emergency_stop=True
                )
            
            # Apply autopilot mode logic
            if workflow_state.autopilot_mode == AutoPilotMode.HUMAN_CONTROL:
                return AutoPilotDecision(
                    should_proceed_automatically=False,
                    chosen_option=None,
                    reasoning="User has disabled autopilot - always request human input",
                    confidence_score=0.0
                )
            
            elif workflow_state.autopilot_mode == AutoPilotMode.FULL_AUTO:
                return await self._evaluate_full_auto(workflow_state, ai_recommendations, settings)
            
            elif workflow_state.autopilot_mode == AutoPilotMode.SMART_AUTO:
                return await self._evaluate_smart_auto(workflow_state, ai_recommendations, settings)
            
            elif workflow_state.autopilot_mode == AutoPilotMode.CUSTOM_THRESHOLD:
                return await self._evaluate_custom_threshold(workflow_state, ai_recommendations, settings)
            
            else:
                return AutoPilotDecision(
                    should_proceed_automatically=False,
                    chosen_option=None,
                    reasoning="Unknown autopilot mode",
                    confidence_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"Error evaluating autopilot decision: {e}")
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=None,
                reasoning=f"Error in autopilot evaluation: {str(e)}",
                confidence_score=0.0,
                emergency_stop=True
            )
    
    async def _evaluate_full_auto(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        settings: AutoPilotSettings
    ) -> AutoPilotDecision:
        """Evaluate full automatic mode with safety checks."""
        
        if not ai_recommendations:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=None,
                reasoning="Full auto mode but no AI recommendations available",
                confidence_score=0.0
            )
        
        # Choose highest confidence recommendation
        best_option = max(ai_recommendations, key=lambda x: x.confidence_score)
        
        # Apply safety checks even in full auto mode
        safety_check = self._apply_safety_checks(workflow_state, best_option, settings)
        if not safety_check.is_safe:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=best_option,
                reasoning=f"Full auto mode but safety check failed: {safety_check.reason}",
                confidence_score=best_option.confidence_score,
                requires_human_confirmation=True
            )
        
        return AutoPilotDecision(
            should_proceed_automatically=True,
            chosen_option=best_option,
            reasoning=f"Full auto mode - proceeding with highest confidence option ({best_option.confidence_score:.1%})",
            confidence_score=best_option.confidence_score
        )
    
    async def _evaluate_smart_auto(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        settings: AutoPilotSettings
    ) -> AutoPilotDecision:
        """Evaluate smart automatic mode based on confidence thresholds."""
        
        if not ai_recommendations:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=None,
                reasoning="Smart auto mode but no AI recommendations available",
                confidence_score=0.0
            )
        
        best_option = max(ai_recommendations, key=lambda x: x.confidence_score)
        
        # Check confidence threshold
        if best_option.confidence_score >= settings.confidence_threshold:
            # High confidence - check additional smart auto criteria
            smart_check = await self._apply_smart_auto_criteria(workflow_state, best_option, settings)
            
            if smart_check.should_auto:
                return AutoPilotDecision(
                    should_proceed_automatically=True,
                    chosen_option=best_option,
                    reasoning=f"Smart auto - high confidence ({best_option.confidence_score:.1%}) and criteria met",
                    confidence_score=best_option.confidence_score
                )
            else:
                return AutoPilotDecision(
                    should_proceed_automatically=False,
                    chosen_option=best_option,
                    reasoning=f"Smart auto - high confidence but criteria not met: {smart_check.reason}",
                    confidence_score=best_option.confidence_score
                )
        else:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=best_option,
                reasoning=f"Smart auto - confidence too low ({best_option.confidence_score:.1%} < {settings.confidence_threshold:.1%})",
                confidence_score=best_option.confidence_score
            )
    
    async def _evaluate_custom_threshold(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        settings: AutoPilotSettings
    ) -> AutoPilotDecision:
        """Evaluate custom threshold autopilot mode."""
        
        if not ai_recommendations:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=None,
                reasoning="Custom threshold mode but no AI recommendations available",
                confidence_score=0.0
            )
        
        best_option = max(ai_recommendations, key=lambda x: x.confidence_score)
        
        if best_option.confidence_score >= settings.confidence_threshold:
            return AutoPilotDecision(
                should_proceed_automatically=True,
                chosen_option=best_option,
                reasoning=f"Custom threshold ({settings.confidence_threshold:.1%}) met with {best_option.confidence_score:.1%} confidence",
                confidence_score=best_option.confidence_score
            )
        else:
            return AutoPilotDecision(
                should_proceed_automatically=False,
                chosen_option=best_option,
                reasoning=f"Custom threshold not met ({best_option.confidence_score:.1%} < {settings.confidence_threshold:.1%})",
                confidence_score=best_option.confidence_score
            )
    
    def _get_autopilot_settings(
        self,
        user_id: str,
        user_preferences: Optional[HITLPreferences]
    ) -> AutoPilotSettings:
        """Get autopilot settings for user."""
        
        if user_id in self.user_settings:
            return self.user_settings[user_id]
        
        # Create settings from preferences or defaults
        if user_preferences:
            settings = AutoPilotSettings(
                mode=user_preferences.default_autopilot_mode,
                confidence_threshold=user_preferences.confidence_threshold
            )
        else:
            settings = AutoPilotSettings(
                mode=AutoPilotMode.SMART_AUTO,
                confidence_threshold=0.85
            )
        
        self.user_settings[user_id] = settings
        return settings
    
    async def _check_emergency_conditions(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> 'EmergencyCheck':
        """Check for emergency conditions that require human intervention."""
        
        # Check each emergency trigger
        for trigger_name, trigger_func in self.emergency_triggers.items():
            if await trigger_func(workflow_state, ai_recommendations):
                return EmergencyCheck(
                    emergency_required=True,
                    reason=trigger_name,
                    details=f"Emergency trigger activated: {trigger_name}"
                )
        
        return EmergencyCheck(emergency_required=False, reason="", details="")
    
    async def _check_repeated_failures(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> bool:
        """Check for repeated failure patterns."""
        
        workflow_id = workflow_state.workflow_id
        
        # Count recent failures
        if workflow_id in self.failed_auto_attempts:
            recent_failures = [
                failure_time for failure_time in self.failed_auto_attempts[workflow_id]
                if failure_time > datetime.utcnow() - timedelta(minutes=30)
            ]
            
            if len(recent_failures) >= 3:  # 3 failures in 30 minutes
                return True
        
        return False
    
    async def _check_high_resource_cost(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> bool:
        """Check for high resource cost steps."""
        
        if ai_recommendations:
            max_cost = max(rec.resource_cost for rec in ai_recommendations)
            return max_cost > 8  # High cost threshold
        
        return False
    
    async def _check_critical_risk(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> bool:
        """Check for critical risk level steps."""
        
        if ai_recommendations:
            return any(rec.risk_level == RiskLevel.CRITICAL for rec in ai_recommendations)
        
        return False
    
    async def _check_user_data_modification(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> bool:
        """Check for steps that modify user data."""
        
        # Check if any recommendations involve data modification
        data_modification_types = [
            "user_data_update",
            "profile_modification", 
            "account_settings_change",
            "data_deletion"
        ]
        
        if ai_recommendations:
            return any(
                rec.step_type in data_modification_types
                for rec in ai_recommendations
            )
        
        return False
    
    async def _check_infinite_loop(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption]
    ) -> bool:
        """Check for potential infinite loop patterns."""
        
        # Simple check: too many consecutive automated steps
        workflow_id = workflow_state.workflow_id
        consecutive_count = self.consecutive_auto_steps.get(workflow_id, 0)
        
        return consecutive_count >= 10  # Max consecutive auto steps
    
    def _apply_safety_checks(
        self,
        workflow_state: WorkflowState,
        chosen_option: NextStepOption,
        settings: AutoPilotSettings
    ) -> 'SafetyCheck':
        """Apply safety checks to chosen option."""
        
        # Check risk level
        if settings.require_human_for_high_risk and chosen_option.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return SafetyCheck(
                is_safe=False,
                reason=f"High/critical risk level: {chosen_option.risk_level.value}"
            )
        
        # Check consecutive auto steps
        workflow_id = workflow_state.workflow_id
        consecutive_count = self.consecutive_auto_steps.get(workflow_id, 0)
        if consecutive_count >= settings.max_consecutive_auto_steps:
            return SafetyCheck(
                is_safe=False,
                reason=f"Too many consecutive auto steps: {consecutive_count}"
            )
        
        return SafetyCheck(is_safe=True, reason="Safety checks passed")
    
    async def _apply_smart_auto_criteria(
        self,
        workflow_state: WorkflowState,
        chosen_option: NextStepOption,
        settings: AutoPilotSettings
    ) -> 'SmartAutoCheck':
        """Apply smart autopilot criteria beyond confidence threshold."""
        
        # Check risk level
        if chosen_option.risk_level == RiskLevel.CRITICAL:
            return SmartAutoCheck(
                should_auto=False,
                reason="Critical risk level requires human oversight"
            )
        
        # Check resource cost
        if chosen_option.resource_cost > 5:  # High resource cost
            return SmartAutoCheck(
                should_auto=False,
                reason="High resource cost step"
            )
        
        # Check if step requires custom inputs
        if any("custom" in inp.lower() for inp in chosen_option.required_inputs):
            return SmartAutoCheck(
                should_auto=False,
                reason="Step requires custom user inputs"
            )
        
        return SmartAutoCheck(should_auto=True, reason="Smart auto criteria met")
    
    def update_autopilot_settings(
        self,
        user_id: str,
        new_settings: AutoPilotSettings
    ):
        """Update autopilot settings for a user."""
        self.user_settings[user_id] = new_settings
        self.logger.info(f"Updated autopilot settings for user {user_id}")
    
    def record_auto_step_success(self, workflow_id: str):
        """Record successful automated step."""
        if workflow_id not in self.consecutive_auto_steps:
            self.consecutive_auto_steps[workflow_id] = 0
        self.consecutive_auto_steps[workflow_id] += 1
    
    def record_auto_step_failure(self, workflow_id: str):
        """Record failed automated step."""
        # Reset consecutive counter
        self.consecutive_auto_steps[workflow_id] = 0
        
        # Record failure timestamp
        if workflow_id not in self.failed_auto_attempts:
            self.failed_auto_attempts[workflow_id] = []
        self.failed_auto_attempts[workflow_id].append(datetime.utcnow())
    
    def reset_autopilot_counters(self, workflow_id: str):
        """Reset autopilot counters (called on human intervention)."""
        self.consecutive_auto_steps.pop(workflow_id, None)
        self.failed_auto_attempts.pop(workflow_id, None)


# Supporting data classes
@dataclass
class EmergencyCheck:
    """Result of emergency condition check."""
    emergency_required: bool
    reason: str
    details: str


@dataclass
class SafetyCheck:
    """Result of safety check."""
    is_safe: bool
    reason: str


@dataclass
class SmartAutoCheck:
    """Result of smart autopilot criteria check."""
    should_auto: bool
    reason: str