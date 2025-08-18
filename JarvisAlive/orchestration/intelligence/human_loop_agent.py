"""
HumanLoopAgent - Interactive decision interface for Human-in-the-Loop workflows.

This agent handles all human interaction points in workflows, providing rich context
and gathering user decisions with support for autopilot bypass controls and 
intelligent workflow suggestions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.align import Align

from .models import (
    WorkflowState, 
    HumanDecision, 
    NextStepOption,
    AutoPilotMode,
    InteractionStyle,
    StepStatus,
    WorkflowStatus
)

logger = logging.getLogger(__name__)


class HumanLoopAgent:
    """
    Manages human interaction points in intelligent workflows.
    
    Provides rich, contextual interfaces for human decision-making while
    supporting various levels of automation and user control. Now enhanced
    with intelligent workflow suggestions.
    """
    
    def __init__(self, console: Optional[Console] = None, workflow_manager=None):
        """Initialize the Human Loop Agent."""
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        self.workflow_manager = workflow_manager
        
        # Interaction state
        self.active_sessions: Dict[str, WorkflowState] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("HumanLoopAgent initialized")
    
    def set_workflow_manager(self, workflow_manager):
        """Set the intelligent workflow manager for suggestions."""
        self.workflow_manager = workflow_manager
        self.logger.info("Workflow manager integrated with HumanLoopAgent")
    
    async def request_human_decision(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        decision_context: Optional[Dict[str, Any]] = None
    ) -> HumanDecision:
        """
        Request human decision with rich contextual interface and workflow suggestions.
        
        Args:
            workflow_state: Current workflow state
            ai_recommendations: AI-generated next step options
            decision_context: Additional context for decision making
            
        Returns:
            Human decision with chosen option and reasoning
        """
        self.logger.info(f"Requesting human decision for workflow {workflow_state.workflow_id}")
        
        # Update workflow state
        workflow_state.status = WorkflowStatus.AWAITING_HUMAN
        workflow_state.awaiting_decision = True
        workflow_state.updated_at = datetime.utcnow()
        
        try:
            # Display decision interface
            await self._display_decision_interface(workflow_state, ai_recommendations, decision_context)
            
            # Show intelligent workflow suggestions if available
            if self.workflow_manager and decision_context:
                await self._display_intelligent_suggestions(workflow_state, decision_context)
            
            # Get user input
            user_choice = await self._get_user_choice(workflow_state, ai_recommendations)
            
            # Process and validate choice
            decision = self._create_human_decision(
                workflow_state, 
                ai_recommendations, 
                user_choice,
                decision_context or {}
            )
            
            # Update workflow state
            workflow_state.add_human_decision(decision)
            workflow_state.awaiting_decision = False
            workflow_state.pending_human_input = False
            
            self.logger.info(f"Human decision recorded: {decision.human_choice}")
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in human decision request: {e}")
            # Create emergency fallback decision
            return self._create_fallback_decision(workflow_state, ai_recommendations, str(e))
    
    async def _display_decision_interface(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        decision_context: Optional[Dict[str, Any]]
    ):
        """Display rich decision interface with full context."""
        
        self.console.print("\n" + "="*80)
        self.console.print("🧠 [bold blue]Intelligence Layer: Next Step Decision Required[/bold blue]")
        self.console.print("="*80)
        
        # Show workflow progress
        self._display_progress_panel(workflow_state)
        
        # Show current context
        self._display_context_panel(workflow_state, decision_context)
        
        # Show AI recommendations
        self._display_recommendations_panel(ai_recommendations)
        
        # Show user options
        self._display_options_panel(workflow_state)
    
    def _display_progress_panel(self, workflow_state: WorkflowState):
        """Display workflow progress visualization."""
        
        # Create progress visualization
        progress_text = f"📊 WORKFLOW PROGRESS: {workflow_state.workflow_title}\n\n"
        
        # Show completed steps
        if workflow_state.completed_steps:
            progress_text += "✅ COMPLETED STEPS:\n"
            for i, step in enumerate(workflow_state.completed_steps[-3:], 1):  # Show last 3
                duration = f"({step.duration_seconds:.1f}s)" if step.duration_seconds else ""
                progress_text += f"   {i}. {step.description} {duration}\n"
        
        # Show current step
        if workflow_state.current_step:
            progress_text += f"\n🔄 CURRENT: {workflow_state.current_step.description}\n"
        
        # Show pending steps preview
        if workflow_state.pending_steps:
            progress_text += f"\n⏳ UPCOMING:\n"
            for i, step in enumerate(workflow_state.pending_steps[:2], 1):  # Show next 2
                progress_text += f"   {i}. {step.description}\n"
        
        # Progress percentage
        progress_text += f"\n📈 Progress: {workflow_state.progress_percentage:.1f}% complete"
        
        progress_panel = Panel(
            progress_text,
            title="Current Progress",
            title_align="left",
            border_style="green"
        )
        self.console.print(progress_panel)
    
    def _display_context_panel(self, workflow_state: WorkflowState, decision_context: Optional[Dict[str, Any]]):
        """Display relevant context for decision making."""
        
        context_text = ""
        
        # Show key context data
        if workflow_state.accumulated_data:
            key_data = []
            for key, value in workflow_state.accumulated_data.items():
                if key in ['market_size', 'brand_name', 'opportunity_score', 'key_competitors']:
                    if isinstance(value, (str, int, float)):
                        key_data.append(f"• {key.replace('_', ' ').title()}: {value}")
                    elif isinstance(value, list) and len(value) > 0:
                        key_data.append(f"• {key.replace('_', ' ').title()}: {len(value)} items")
            
            if key_data:
                context_text += "📋 KEY DATA AVAILABLE:\n" + "\n".join(key_data) + "\n\n"
        
        # Show decision context
        if decision_context:
            context_text += "🎯 DECISION CONTEXT:\n"
            for key, value in decision_context.items():
                if isinstance(value, str) and len(value) < 100:
                    context_text += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        if not context_text:
            context_text = "No specific context data available for this decision."
        
        context_panel = Panel(
            context_text,
            title="Decision Context",
            title_align="left", 
            border_style="blue"
        )
        self.console.print(context_panel)
    
    def _display_recommendations_panel(self, ai_recommendations: List[NextStepOption]):
        """Display AI recommendations in a structured format."""
        
        if not ai_recommendations:
            self.console.print("[yellow]⚠️ No AI recommendations available[/yellow]")
            return
        
        # Sort by confidence score
        sorted_recommendations = sorted(ai_recommendations, key=lambda x: x.confidence_score, reverse=True)
        
        self.console.print(f"\n🎯 [bold]AI RECOMMENDATIONS[/bold] (Top {len(sorted_recommendations)} options)")
        
        for i, option in enumerate(sorted_recommendations, 1):
            confidence_color = "green" if option.confidence_score > 0.8 else "yellow" if option.confidence_score > 0.6 else "red"
            
            recommendation_text = (
                f"[bold]{i}. {option.description}[/bold]\n"
                f"   📊 Confidence: [{confidence_color}]{option.confidence_score:.1%}[/{confidence_color}] | "
                f"⏱️ Time: ~{option.estimated_time_minutes}min | "
                f"🎯 Agent: {option.agent_id}\n"
            )
            
            if option.reasoning:
                recommendation_text += f"   💭 Reasoning: {option.reasoning}\n"
            
            if option.required_inputs:
                recommendation_text += f"   📥 Needs: {', '.join(option.required_inputs)}\n"
            
            recommendation_panel = Panel(
                recommendation_text,
                title=f"Option {i}",
                title_align="left",
                border_style=confidence_color
            )
            self.console.print(recommendation_panel)
    
    def _display_options_panel(self, workflow_state: WorkflowState):
        """Display user control options."""
        
        options_text = (
            "💭 [bold yellow]YOUR CONTROL OPTIONS:[/bold yellow]\n\n"
            "📋 STEP SELECTION:\n"
            "• Type '1', '2', '3', etc. to choose an AI recommendation\n"
            "• Type 'custom' to propose your own next step\n"
            "• Type 'skip' to skip this decision point\n\n"
            "⚙️ AUTOPILOT CONTROL:\n"
            "• Type 'autopilot on' to enable full automation\n"
            "• Type 'autopilot smart' to auto-proceed when AI confidence > 85%\n"
            "• Type 'autopilot off' to always ask for human input\n\n"
            "🔄 WORKFLOW CONTROL:\n"
            "• Type 'pause' to save progress and continue later\n" 
            "• Type 'status' to see detailed workflow information\n"
            "• Type 'explain' to get more details about recommendations\n"
            "• Type 'back' to return to the previous decision point\n\n"
            "🚨 EMERGENCY CONTROL:\n"
            "• Type 'emergency stop' to immediately halt processing\n"
            "• Type 'quit' to exit the workflow completely"
        )
        
        options_panel = Panel(
            options_text,
            title="User Controls",
            title_align="left",
            border_style="yellow"
        )
        self.console.print(options_panel)
    
    async def _get_user_choice(
        self, 
        workflow_state: WorkflowState, 
        ai_recommendations: List[NextStepOption]
    ) -> str:
        """Get and validate user choice with command processing."""
        
        while True:
            try:
                self.console.print()
                user_input = Prompt.ask(
                    "[bold]Your decision",
                    default="1" if ai_recommendations else "custom"
                ).strip().lower()
                
                # Process special commands
                if user_input in ['emergency stop', 'quit', 'exit']:
                    workflow_state.emergency_pause = True
                    return 'emergency_stop'
                
                elif user_input == 'pause':
                    workflow_state.user_requested_pause = True
                    return 'pause'
                
                elif user_input == 'status':
                    self._display_detailed_status(workflow_state)
                    continue
                
                elif user_input == 'explain':
                    self._display_detailed_explanations(ai_recommendations)
                    continue
                
                elif user_input.startswith('autopilot'):
                    self._handle_autopilot_command(user_input, workflow_state)
                    continue
                
                elif user_input == 'back':
                    return 'back'
                
                elif user_input == 'skip':
                    return 'skip'
                
                elif user_input == 'custom':
                    return self._get_custom_step_input()
                
                # Validate numeric choice
                elif user_input.isdigit():
                    choice_num = int(user_input)
                    if 1 <= choice_num <= len(ai_recommendations):
                        return f"option_{choice_num}"
                    else:
                        self.console.print(f"[red]Please enter a number between 1 and {len(ai_recommendations)}[/red]")
                        continue
                
                else:
                    self.console.print("[red]Invalid choice. Please try again or type 'quit' to exit.[/red]")
                    continue
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Workflow paused. Type 'continue' to resume.[/yellow]")
                workflow_state.user_requested_pause = True
                return 'pause'
            except Exception as e:
                self.console.print(f"[red]Error processing input: {e}[/red]")
                continue
    
    def _get_custom_step_input(self) -> str:
        """Get custom step input from user."""
        self.console.print("\n[bold blue]Describe your custom next step:[/bold blue]")
        custom_step = Prompt.ask("Custom step description")
        return f"custom:{custom_step}"
    
    def _handle_autopilot_command(self, command: str, workflow_state: WorkflowState):
        """Handle autopilot control commands."""
        if 'on' in command or 'full' in command:
            workflow_state.autopilot_mode = AutoPilotMode.FULL_AUTO
            self.console.print("[green]✅ Autopilot enabled - workflow will continue automatically[/green]")
        elif 'smart' in command:
            workflow_state.autopilot_mode = AutoPilotMode.SMART_AUTO
            self.console.print("[blue]🔄 Smart autopilot enabled - will auto-proceed when AI confidence > 85%[/blue]")
        elif 'off' in command:
            workflow_state.autopilot_mode = AutoPilotMode.HUMAN_CONTROL
            self.console.print("[yellow]🎮 Manual control enabled - will always ask for human input[/yellow]")
    
    async def _display_intelligent_suggestions(
        self,
        workflow_state: WorkflowState,
        decision_context: Dict[str, Any]
    ):
        """Display intelligent workflow suggestions based on current context."""
        try:
            # Build workflow context from current state
            workflow_context = self._build_workflow_context_from_state(workflow_state, decision_context)
            
            if workflow_context:
                suggestions = await self.workflow_manager.suggest_next_workflows(workflow_context, max_suggestions=3)
                
                if suggestions:
                    self.console.print("\n" + "="*60)
                    self.console.print("🤖 [bold blue]Intelligent Workflow Suggestions[/bold blue]")
                    self.console.print("="*60)
                    
                    for i, suggestion in enumerate(suggestions, 1):
                        confidence = suggestion.get('confidence', 0)
                        confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.5 else "red"
                        
                        self.console.print(f"\n[cyan]{i}.[/cyan] [bold]{suggestion['title']}[/bold]")
                        self.console.print(f"   [dim]Type: {suggestion['workflow_type']}[/dim]")
                        self.console.print(f"   [dim]Confidence: [{confidence_color}]{confidence:.1%}[/{confidence_color}][/dim]")
                        self.console.print(f"   [dim]Reason: {suggestion['reason']}[/dim]")
                        self.console.print(f"   [green]Suggested Prompt:[/green] \"{suggestion['suggested_prompt']}\"")
                        
                        if 'business_value' in suggestion:
                            self.console.print(f"   [blue]Business Value:[/blue] {suggestion['business_value']}")
                    
                    self.console.print("\n[dim]💡 These suggestions are based on your completed workflows and business context[/dim]")
                    self.console.print("="*60)
        
        except Exception as e:
            self.logger.error(f"Error displaying intelligent suggestions: {e}")
            # Don't fail the main decision flow
    
    def _build_workflow_context_from_state(
        self,
        workflow_state: WorkflowState,
        decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build workflow context from current workflow state for suggestions."""
        context = {}
        
        # Add completed steps as workflows
        for i, step in enumerate(workflow_state.completed_steps):
            step_id = f"{workflow_state.workflow_id}_step_{i}"
            context[step_id] = {
                'request': step.description,
                'type': step.step_type if hasattr(step, 'step_type') else 'unknown',
                'result': step.result if hasattr(step, 'result') else {},
                'timestamp': step.started_at if hasattr(step, 'started_at') else datetime.utcnow(),
                'success': step.status == StepStatus.COMPLETED
            }
        
        # Add current workflow as context
        if workflow_state.workflow_title:
            context[workflow_state.workflow_id] = {
                'request': workflow_state.workflow_title,
                'type': workflow_state.workflow_type if hasattr(workflow_state, 'workflow_type') else 'unknown',
                'result': decision_context,
                'timestamp': workflow_state.created_at,
                'success': workflow_state.status != WorkflowStatus.FAILED
            }
        
        return context
    
    async def request_workflow_selection(
        self,
        available_workflows: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Request user to select from suggested workflows.
        
        Args:
            available_workflows: List of workflow options with suggestions
            context: Additional context for decision making
            
        Returns:
            Selected workflow prompt or None if cancelled
        """
        self.console.print("\n" + "="*80)
        self.console.print("🤖 [bold blue]Intelligent Workflow Selection[/bold blue]")
        self.console.print("="*80)
        
        if not available_workflows:
            self.console.print("[dim]No workflow suggestions available[/dim]")
            return None
        
        # Display workflow options
        self.console.print("[bold cyan]Suggested Workflows:[/bold cyan]\n")
        
        for i, workflow in enumerate(available_workflows, 1):
            confidence = workflow.get('confidence', 0)
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.5 else "red"
            
            self.console.print(f"[cyan]{i}.[/cyan] [bold]{workflow['title']}[/bold]")
            self.console.print(f"   [dim]Confidence: [{confidence_color}]{confidence:.1%}[/{confidence_color}][/dim]")
            self.console.print(f"   [dim]Reason: {workflow['reason']}[/dim]")
            if 'business_value' in workflow:
                self.console.print(f"   [blue]Value:[/blue] {workflow['business_value']}")
            self.console.print(f"   [green]Prompt:[/green] \"{workflow['suggested_prompt']}\"\n")
        
        # Add option to enter custom workflow
        self.console.print(f"[cyan]{len(available_workflows) + 1}.[/cyan] [bold]Enter Custom Workflow[/bold]")
        self.console.print("   [dim]Define your own workflow request[/dim]\n")
        
        # Add cancel option
        self.console.print("[cyan]0.[/cyan] [bold]Cancel / Return to Main Menu[/bold]\n")
        
        # Get user selection
        while True:
            try:
                choice = self.console.input(
                    f"[bold cyan]Select workflow (0-{len(available_workflows) + 1}):[/bold cyan] "
                ).strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(available_workflows):
                    selected = available_workflows[choice_num - 1]
                    self.console.print(f"[green]✓ Selected:[/green] {selected['title']}")
                    return selected['suggested_prompt']
                
                elif choice_num == len(available_workflows) + 1:
                    # Custom workflow
                    custom_prompt = self.console.input(
                        "[bold cyan]Enter your custom workflow request:[/bold cyan] "
                    ).strip()
                    
                    if custom_prompt:
                        self.console.print(f"[green]✓ Custom workflow:[/green] {custom_prompt}")
                        return custom_prompt
                    else:
                        self.console.print("[yellow]Empty prompt, please try again[/yellow]")
                        continue
                
                else:
                    self.console.print(f"[red]Invalid choice. Please select 0-{len(available_workflows) + 1}[/red]")
                    continue
                    
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")
                continue
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Cancelled[/yellow]")
                return None
    
    async def display_workflow_suggestions_menu(
        self,
        workflow_context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Display a menu of intelligent workflow suggestions and get user selection.
        
        Args:
            workflow_context: Context from completed workflows
            
        Returns:
            Selected workflow prompt or None
        """
        if not self.workflow_manager:
            self.console.print("[red]Workflow manager not available[/red]")
            return None
        
        try:
            suggestions = await self.workflow_manager.suggest_next_workflows(workflow_context)
            
            if not suggestions:
                self.console.print("[dim]No intelligent suggestions available at this time[/dim]")
                return None
            
            return await self.request_workflow_selection(suggestions, workflow_context)
            
        except Exception as e:
            self.logger.error(f"Error in workflow suggestions menu: {e}")
            self.console.print(f"[red]Error generating suggestions:[/red] {e}")
            return None
    
    def _create_human_decision(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        user_choice: str,
        decision_context: Dict[str, Any]
    ) -> HumanDecision:
        """Create a HumanDecision object from user choice."""
        
        return HumanDecision(
            decision_id="",  # Will be auto-generated
            workflow_id=workflow_state.workflow_id,
            workflow_step=workflow_state.current_step_index,
            ai_recommendations=ai_recommendations,
            human_choice=user_choice,
            custom_input=user_choice.split(":", 1)[1] if user_choice.startswith("custom:") else None,
            decision_context=decision_context,
            reasoning=f"User chose: {user_choice}"
        )
    
    def _create_fallback_decision(
        self,
        workflow_state: WorkflowState,
        ai_recommendations: List[NextStepOption],
        error_message: str
    ) -> HumanDecision:
        """Create fallback decision when error occurs."""
        
        return HumanDecision(
            decision_id="",
            workflow_id=workflow_state.workflow_id,
            workflow_step=workflow_state.current_step_index,
            ai_recommendations=ai_recommendations,
            human_choice="fallback",
            reasoning=f"Fallback decision due to error: {error_message}"
        )


# Utility functions for decision processing
def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def calculate_confidence_color(confidence: float) -> str:
    """Get color for confidence score display."""
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.6:
        return "yellow"
    else:
        return "red"