"""
Data models for the Intelligence Layer with Human-in-the-Loop workflow orchestration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class AutoPilotMode(str, Enum):
    """Autopilot control modes for workflow execution."""
    HUMAN_CONTROL = "human_control"      # Always ask human
    SMART_AUTO = "smart_auto"            # Auto when high confidence
    FULL_AUTO = "full_auto"              # Always automatic
    CUSTOM_THRESHOLD = "custom"          # User-defined confidence threshold


class WorkflowStatus(str, Enum):
    """Overall workflow execution status."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN = "awaiting_human"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Individual workflow step status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_HUMAN = "awaiting_human"


class RiskLevel(str, Enum):
    """Risk level for workflow steps."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InteractionStyle(str, Enum):
    """Human interaction style preferences."""
    MINIMAL = "minimal"      # Brief summaries, quick decisions
    DETAILED = "detailed"    # Full context, detailed explanations
    EXPERT = "expert"        # Technical details, confidence metrics


@dataclass
class NextStepOption:
    """Represents a potential next step in the workflow."""
    option_id: str
    step_type: str
    description: str
    agent_id: str
    estimated_time_minutes: int
    required_inputs: List[str]
    expected_outputs: List[str]
    confidence_score: float
    risk_level: RiskLevel
    resource_cost: int = 1
    dependencies: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    def __post_init__(self):
        if not self.option_id:
            self.option_id = str(uuid.uuid4())[:8]


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow execution."""
    step_id: str
    step_type: str
    agent_id: str
    description: str
    input_state: Dict[str, Any]
    output_state: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    human_decision_id: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if not self.step_id:
            self.step_id = str(uuid.uuid4())[:8]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class HumanDecision:
    """Represents a human decision point in the workflow."""
    decision_id: str
    workflow_id: str
    workflow_step: int
    ai_recommendations: List[NextStepOption]
    human_choice: str
    custom_input: Optional[str] = None
    decision_timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_override: bool = False
    reasoning: Optional[str] = None
    decision_context: Dict[str, Any] = field(default_factory=dict)
    user_satisfaction: Optional[int] = None  # 1-5 rating
    
    def __post_init__(self):
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())[:8]


@dataclass 
class HITLPreferences:
    """User preferences for Human-in-the-Loop interactions."""
    user_id: str
    default_autopilot_mode: AutoPilotMode = AutoPilotMode.SMART_AUTO
    confidence_threshold: float = 0.85
    interaction_style: InteractionStyle = InteractionStyle.DETAILED
    
    # Notification preferences
    notify_step_completion: bool = True
    notify_decision_needed: bool = True
    notify_error_alerts: bool = True
    notify_progress_updates: bool = False
    
    # Learning preferences
    learn_from_decisions: bool = True
    personalize_recommendations: bool = True
    
    # Workflow preferences
    preferred_workflow_types: List[str] = field(default_factory=list)
    avoided_agent_types: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowState:
    """Complete state of a workflow execution with HITL capabilities."""
    # Core workflow identification
    workflow_id: str
    user_id: str
    session_id: str
    workflow_type: str
    workflow_title: str
    
    # Workflow execution state
    status: WorkflowStatus = WorkflowStatus.CREATED
    current_step_index: int = 0
    total_estimated_steps: int = 0
    
    # Step management
    completed_steps: List[WorkflowStep] = field(default_factory=list)
    current_step: Optional[WorkflowStep] = None
    pending_steps: List[WorkflowStep] = field(default_factory=list)
    
    # Context and data
    initial_context: Dict[str, Any] = field(default_factory=dict)
    current_context: Dict[str, Any] = field(default_factory=dict)
    accumulated_data: Dict[str, Any] = field(default_factory=dict)
    
    # HITL-specific state
    autopilot_mode: AutoPilotMode = AutoPilotMode.SMART_AUTO
    human_decisions: List[HumanDecision] = field(default_factory=list)
    pending_human_input: bool = False
    awaiting_decision: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_human_interaction: Optional[datetime] = None
    
    # Control flags
    emergency_pause: bool = False
    user_requested_pause: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.workflow_id:
            self.workflow_id = str(uuid.uuid4())[:8]
    
    @property
    def progress_percentage(self) -> float:
        """Calculate workflow completion percentage."""
        if self.total_estimated_steps == 0:
            return 0.0
        completed_count = len(self.completed_steps)
        return min(100.0, (completed_count / self.total_estimated_steps) * 100)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total workflow duration in seconds."""
        return (self.updated_at - self.created_at).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Check if workflow is currently active."""
        return self.status in [
            WorkflowStatus.IN_PROGRESS, 
            WorkflowStatus.AWAITING_HUMAN
        ]
    
    @property
    def needs_human_input(self) -> bool:
        """Check if workflow is waiting for human input."""
        return (self.pending_human_input or 
                self.awaiting_decision or 
                self.status == WorkflowStatus.AWAITING_HUMAN)
    
    def add_human_decision(self, decision: HumanDecision):
        """Add a human decision to the workflow."""
        self.human_decisions.append(decision)
        self.last_human_interaction = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_context(self, new_data: Dict[str, Any]):
        """Update workflow context with new data."""
        self.current_context.update(new_data)
        self.accumulated_data.update(new_data)
        self.updated_at = datetime.utcnow()
    
    def mark_step_completed(self, step: WorkflowStep):
        """Mark a workflow step as completed."""
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.utcnow()
        
        if self.current_step and self.current_step.step_id == step.step_id:
            self.completed_steps.append(step)
            self.current_step = None
            self.current_step_index += 1
            
        self.updated_at = datetime.utcnow()


@dataclass
class WorkflowTemplate:
    """Template for creating standardized workflows."""
    template_id: str
    template_name: str
    description: str
    workflow_type: str
    estimated_steps: int
    estimated_duration_minutes: int
    required_agents: List[str]
    default_steps: List[Dict[str, Any]]
    decision_points: List[Dict[str, Any]]
    
    # Template metadata
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_rate: float = 0.0


# Workflow execution results
@dataclass
class WorkflowResult:
    """Final result of a completed workflow."""
    workflow_id: str
    status: WorkflowStatus
    final_outputs: Dict[str, Any]
    execution_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    human_interaction_summary: Dict[str, Any]
    completed_at: datetime = field(default_factory=datetime.utcnow)