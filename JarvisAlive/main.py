"""Main entry point for HeyJarvis orchestrator."""

import asyncio
import logging
import os
import sys
import argparse
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from orchestration.orchestrator import HeyJarvisOrchestrator, OrchestratorConfig
from orchestration.jarvis import Jarvis, JarvisConfig
from orchestration.branding_orchestration import BrandingOrchestrator, OrchestrationConfig
from orchestration.universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.intelligence.models import AutoPilotMode, WorkflowStatus, HITLPreferences
from orchestration.persistent.persistent_system import create_development_persistent_system, PersistentSystem
from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
from orchestration.persistent.advanced_features import (
    InterAgentCommunicationManager, WorkflowTemplateManager, PerformanceAnalyticsEngine
)
from orchestration.intelligence.intelligent_workflow_manager import IntelligentWorkflowManager
from conversation.websocket_handler import websocket_handler, OperatingMode

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rich console for better UI
console = Console()


async def branding_mode():
    """Branding agent orchestration mode."""
    # Initialize branding orchestrator
    config = OrchestrationConfig(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        max_concurrent_invocations=int(os.getenv("MAX_CONCURRENT_INVOCATIONS", "5")),
        response_cache_ttl_hours=int(os.getenv("RESPONSE_CACHE_TTL_HOURS", "1")),
        enable_logging=os.getenv("ENABLE_LOGGING", "true").lower() == "true",
        enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    orchestrator = BrandingOrchestrator(config)
    success = await orchestrator.initialize()
    
    if not success:
        console.print("[red]Error: Failed to initialize branding orchestrator.[/red]")
        return
    
    console.print("[bold magenta]🎨 Branding Agent Mode Active[/bold magenta]")
    console.print("[dim]AI-powered brand creation and visual identity generation[/dim]\n")
    
    try:
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        
        # Show branding commands
        console.print("[dim]💡 Commands: 'health', 'metrics', 'demo', or describe your business idea[/dim]\n")
        
        while True:
            try:
                user_input = console.input("[bold magenta]You:[/bold magenta] ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye! Your branding session has been saved.[/yellow]")
                    break
                elif user_input.lower() == 'health':
                    health = await orchestrator.health_check()
                    console.print(f"[green]Health Status: {health.get('status')}[/green]")
                    console.print(f"[green]Components: {list(health.get('components', {}).keys())}[/green]")
                    continue
                elif user_input.lower() == 'metrics':
                    metrics = await orchestrator.get_metrics()
                    console.print(f"[blue]Total Requests: {metrics.total_requests}[/blue]")
                    console.print(f"[blue]Successful: {metrics.successful_requests}[/blue]")
                    console.print(f"[blue]Failed: {metrics.failed_requests}[/blue]")
                    console.print(f"[blue]Avg Response Time: {metrics.average_response_time_ms:.2f}ms[/blue]")
                    continue
                elif user_input.lower() == 'demo':
                    await branding_demo_mode(orchestrator, session_id)
                    continue
                
                # Process branding request
                console.print(f"\n[bold magenta]🎨 Branding Agent:[/bold magenta] Processing your brand creation request...\n")
                
                result = await orchestrator.process_request(user_input, session_id)
                
                # Display branding results
                await display_branding_result(result)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Type 'continue' to resume later.[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error(f"Branding mode error: {e}")
                
    finally:
        await orchestrator.cleanup()


async def jarvis_mode():
    """Business-level orchestration mode with Jarvis."""
    # Initialize Jarvis with existing config
    orchestrator_config = OrchestratorConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600"))
    )
    
    jarvis_config = JarvisConfig(
        orchestrator_config=orchestrator_config,
        max_concurrent_departments=int(os.getenv("MAX_DEPARTMENTS", "5")),
        enable_autonomous_department_creation=os.getenv("AUTO_DEPARTMENTS", "true").lower() == "true",
        enable_cross_department_coordination=os.getenv("CROSS_DEPT_COORD", "true").lower() == "true"
    )
    
    if not orchestrator_config.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please set your Anthropic API key in the .env file.")
        return
    
    jarvis = Jarvis(jarvis_config)
    await jarvis.initialize()
    
    # Reuse existing chat interface with Jarvis routing
    console.print("[bold cyan]💼 Jarvis Business Mode Active[/bold cyan]")
    console.print("[dim]Business-level orchestration with department coordination[/dim]\n")
    
    def progress_callback(node_name: str, progress: int, message: str):
        """Progress callback for real-time updates."""
        console.print(f"📊 Progress: {progress}% - {message}")
        # Send WebSocket update for Jarvis mode
        try:
            asyncio.create_task(websocket_handler.send_workflow_progress(
                session_id if 'session_id' in locals() else "unknown", 
                "Business Workflow", progress, message
            ))
        except:
            pass  # WebSocket updates are optional
    
    jarvis.set_progress_callback(progress_callback)
    
    try:
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        
        # Enhanced commands for Jarvis mode
        console.print("[dim]💡 Commands: 'insights', 'departments', 'business', 'demo', or any business request[/dim]\n")
        
        while True:
            try:
                user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye! Your business context has been saved.[/yellow]")
                    break
                elif user_input.lower() == 'demo':
                    await business_demo_mode(jarvis, session_id)
                    continue
                elif user_input.lower() == 'insights':
                    await show_business_insights(jarvis, session_id)
                    continue
                elif user_input.lower() == 'departments':
                    await show_departments(jarvis)
                    continue
                elif user_input.lower() == 'business':
                    await show_business_context(jarvis, session_id)
                    continue
                
                # Route requests based on mode
                # Check if this is a technical request that should go to agent builder
                if await is_technical_request(user_input):
                    console.print("[yellow]🔧 Technical request detected - forwarding to agent builder...[/yellow]")
                    result = await jarvis.process_business_request(user_input, session_id)
                else:
                    # Business request - use Jarvis for business-level orchestration
                    console.print(f"\n[bold cyan]💼 Jarvis:[/bold cyan] Processing business request with department coordination...\n")
                    result = await jarvis.process_business_request(user_input, session_id)
                
                await display_jarvis_result(result)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Type 'continue' to resume later.[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error(f"Jarvis mode error: {e}")
                
    finally:
        await jarvis.close()


async def jarvis_interface():
    """Interactive chat interface for Jarvis Meta-Orchestrator."""
    
    # Configuration for Jarvis
    orchestrator_config = OrchestratorConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600"))
    )
    
    jarvis_config = JarvisConfig(
        orchestrator_config=orchestrator_config,
        max_concurrent_departments=int(os.getenv("MAX_DEPARTMENTS", "5")),
        enable_autonomous_department_creation=os.getenv("AUTO_DEPARTMENTS", "true").lower() == "true",
        enable_cross_department_coordination=os.getenv("CROSS_DEPT_COORD", "true").lower() == "true"
    )
    
    if not orchestrator_config.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please set your Anthropic API key in the .env file.")
        return
    
    # Initialize Jarvis
    jarvis = Jarvis(jarvis_config)
    
    def progress_callback(node_name: str, progress: int, message: str):
        """Progress callback for real-time updates."""
        console.print(f"📊 Progress: {progress}% - {message}")
    
    jarvis.set_progress_callback(progress_callback)
    
    try:
        await jarvis.initialize()
        
        # Welcome message for Jarvis
        console.print("\n[bold magenta]🧠 Jarvis Meta-Orchestrator:[/bold magenta] Welcome! I'm your business-level AI orchestrator.")
        console.print("I can help you create individual agents or coordinate entire departments.")
        console.print("I understand your business context and can optimize for your company's goals.\n")
        
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        
        # Show additional Jarvis commands
        console.print("[dim]💡 Jarvis commands: 'insights', 'departments', 'business', or any agent request[/dim]\n")
        
        while True:
            try:
                # Get user input
                user_input = console.input("[bold magenta]You:[/bold magenta] ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye! Your business context has been saved.[/yellow]")
                    break
                    
                elif user_input.lower() == 'continue':
                    await handle_jarvis_continue_command(jarvis)
                    continue
                    
                elif user_input.lower() == 'sessions':
                    await show_jarvis_active_sessions(jarvis)
                    continue
                    
                elif user_input.lower() == 'insights':
                    await show_business_insights(jarvis, session_id)
                    continue
                    
                elif user_input.lower() == 'departments':
                    await show_departments(jarvis)
                    continue
                    
                elif user_input.lower() == 'business':
                    await show_business_context(jarvis, session_id)
                    continue
                
                # Process business request through Jarvis
                console.print(f"\n[bold magenta]🧠 Jarvis:[/bold magenta] I'll process your business request with full context awareness...\n")
                
                result = await jarvis.process_business_request(user_input, session_id)
                
                # Display results with Jarvis metadata
                await display_jarvis_result(result)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Type 'continue' to resume later.[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error(f"Jarvis interface error: {e}")
                
    finally:
        await jarvis.close()


async def intelligence_mode():
    """Intelligence Layer mode with Human-in-the-Loop workflow orchestration."""
    
    # Configuration for WorkflowBrain
    config = {
        'anthropic_api_key': os.getenv("ANTHROPIC_API_KEY"),
        'redis_url': os.getenv("REDIS_URL", "redis://localhost:6379")
    }
    
    if not config['anthropic_api_key']:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please set your Anthropic API key in the .env file.")
        return
    
    # Initialize WorkflowBrain
    workflow_brain = WorkflowBrain(config)
    
    try:
        await workflow_brain.initialize_orchestration()
        
        # Welcome message
        console.print("\n" + "="*80)
        console.print("[bold blue]🧠 Intelligence Layer: Human-in-the-Loop Workflow Orchestration[/bold blue]")
        console.print("="*80)
        console.print("\n[bold cyan]Welcome to the Intelligence Layer![/bold cyan]")
        console.print("I orchestrate complex workflows with AI guidance and human oversight.\n")
        
        console.print("[bold yellow]🎯 What I can do:[/bold yellow]")
        console.print("  • Create intelligent business workflows")
        console.print("  • Guide you through multi-step processes") 
        console.print("  • Provide AI recommendations with human control")
        console.print("  • Auto-pilot when you want, human control when you need it\n")
        
        console.print("[bold yellow]📋 Workflow Examples:[/bold yellow]")
        console.print("  • 'Create a sustainable coffee subscription business'")
        console.print("  • 'Launch a tech consulting service'")
        console.print("  • 'Build a comprehensive marketing strategy'\n")
        
        console.print("[bold yellow]⚙️ Control Commands:[/bold yellow]")
        console.print("  • 'autopilot on/off/smart' - Control automation level")
        console.print("  • 'status' - View current workflow progress")
        console.print("  • 'workflows' - List active workflows")
        console.print("  • 'help' - Show detailed command help\n")
        
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        
        # Track active workflows for this session
        active_workflows = {}
        current_workflow_id = None
        
        while True:
            try:
                # Get user input
                user_input = console.input("[bold blue]🧠 You:[/bold blue] ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye! Your workflow progress has been saved.[/yellow]")
                    break
                    
                elif user_input.lower() == 'help':
                    await show_intelligence_help()
                    continue
                    
                elif user_input.lower() == 'status':
                    await show_workflow_status(workflow_brain, active_workflows)
                    continue
                    
                elif user_input.lower() == 'workflows':
                    await show_active_workflows(workflow_brain, active_workflows)
                    continue
                    
                elif user_input.lower().startswith('autopilot'):
                    await handle_autopilot_command(user_input, active_workflows)
                    continue
                
                elif user_input.lower() == 'continue':
                    if current_workflow_id and current_workflow_id in workflow_brain.active_workflows:
                        await continue_workflow(workflow_brain, current_workflow_id, active_workflows)
                    else:
                        console.print("[yellow]No active workflow to continue.[/yellow]")
                    continue
                
                # Check if this is a workflow continuation command
                if await is_workflow_continuation_command(user_input, current_workflow_id, workflow_brain):
                    await handle_workflow_continuation(user_input, current_workflow_id, workflow_brain, active_workflows)
                    continue
                
                # Create new workflow
                console.print(f"\n[bold blue]🧠 Intelligence Layer:[/bold blue] Creating intelligent workflow for your request...\n")
                
                try:
                    # Create workflow
                    workflow_id = await workflow_brain.create_workflow(
                        user_id="human_user",
                        session_id=session_id,
                        workflow_type="business_creation", 
                        initial_request=user_input,
                        context={"session_mode": "interactive"}
                    )
                    
                    # Store workflow for session tracking
                    active_workflows[workflow_id] = {
                        'request': user_input,
                        'created_at': datetime.now(),
                        'last_activity': datetime.now()
                    }
                    
                    # Set as current active workflow
                    current_workflow_id = workflow_id
                    
                    console.print(f"[green]✅ Workflow created: {workflow_id}[/green]")
                    
                    # Execute workflow with Human-in-the-Loop
                    console.print("[bold yellow]🚀 Starting intelligent execution with human oversight...[/bold yellow]\n")
                    
                    result = await workflow_brain.execute_workflow(workflow_id)
                    
                    # Display results
                    await display_intelligence_result(result, workflow_brain.active_workflows[workflow_id])
                    
                    # Update session tracking
                    active_workflows[workflow_id]['last_activity'] = datetime.now()
                    active_workflows[workflow_id]['status'] = result.status.value
                    
                except Exception as e:
                    console.print(f"[red]Error creating workflow: {str(e)}[/red]")
                    logger.error(f"Intelligence mode error: {e}")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Workflow paused. Type 'continue' to resume or 'quit' to exit.[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error(f"Intelligence mode error: {e}")
                
    finally:
        # Cleanup would go here if needed
        console.print("[dim]Intelligence Layer session ended.[/dim]")


async def show_intelligence_help():
    """Show detailed help for Intelligence Layer."""
    console.print("\n[bold cyan]🧠 Intelligence Layer - Detailed Help[/bold cyan]")
    
    console.print("\n[bold yellow]🎯 WORKFLOW CREATION[/bold yellow]")
    console.print("Describe what you want to accomplish and I'll create an intelligent workflow:")
    console.print("  • Business creation and strategy")
    console.print("  • Product development and launch")
    console.print("  • Marketing campaigns and execution")
    console.print("  • Process automation and optimization")
    
    console.print("\n[bold yellow]⚙️ AUTOPILOT CONTROL[/bold yellow]")
    console.print("Control how much automation vs. human oversight you want:")
    console.print("  • 'autopilot off' - Always ask for human decisions")
    console.print("  • 'autopilot smart' - Auto-proceed when AI confidence > 85%")
    console.print("  • 'autopilot on' - Full automation with safety checks")
    
    console.print("\n[bold yellow]🔄 WORKFLOW COMMANDS[/bold yellow]")
    console.print("  • 'status' - View current workflow progress and context")
    console.print("  • 'workflows' - List all active workflows in this session")
    console.print("  • 'pause' - Pause current workflow")
    console.print("  • 'continue' - Resume paused workflow")
    
    console.print("\n[bold yellow]🚨 EMERGENCY CONTROLS[/bold yellow]")
    console.print("  • 'emergency stop' - Immediately halt all processing")
    console.print("  • Ctrl+C - Pause current operation")
    console.print("  • 'quit' - Exit Intelligence Layer")


async def show_workflow_status(workflow_brain: WorkflowBrain, active_workflows: dict):
    """Show status of active workflows."""
    if not active_workflows:
        console.print("[yellow]No active workflows in this session.[/yellow]")
        return
    
    table = Table(title="Active Workflows Status")
    table.add_column("Workflow ID", style="cyan")
    table.add_column("Request", style="white")
    table.add_column("Status", style="green")
    table.add_column("Progress", style="blue")
    table.add_column("Created", style="yellow")
    
    for workflow_id, workflow_info in active_workflows.items():
        if workflow_id in workflow_brain.active_workflows:
            workflow_state = workflow_brain.active_workflows[workflow_id]
            progress = f"{workflow_state.progress_percentage:.1f}%"
            status = workflow_state.status.value
        else:
            progress = "Unknown"
            status = workflow_info.get('status', 'Unknown')
        
        # Truncate long requests
        request = workflow_info['request']
        if len(request) > 40:
            request = request[:37] + "..."
            
        created = workflow_info['created_at'].strftime("%H:%M:%S")
        
        table.add_row(workflow_id, request, status, progress, created)
    
    console.print(table)


async def show_active_workflows(workflow_brain: WorkflowBrain, active_workflows: dict):
    """Show detailed view of active workflows."""
    if not active_workflows:
        console.print("[yellow]No active workflows in this session.[/yellow]")
        return
    
    for workflow_id, workflow_info in active_workflows.items():
        if workflow_id in workflow_brain.active_workflows:
            workflow_state = workflow_brain.active_workflows[workflow_id]
            
            console.print(f"\n[bold cyan]📋 Workflow: {workflow_id}[/bold cyan]")
            console.print(f"   Request: {workflow_info['request']}")
            console.print(f"   Status: {workflow_state.status.value}")
            console.print(f"   Progress: {workflow_state.progress_percentage:.1f}%")
            console.print(f"   Autopilot: {workflow_state.autopilot_mode.value}")
            console.print(f"   Steps completed: {len(workflow_state.completed_steps)}")
            console.print(f"   Human decisions: {len(workflow_state.human_decisions)}")


async def handle_autopilot_command(command: str, active_workflows: dict):
    """Handle autopilot control commands."""
    if 'on' in command.lower() or 'full' in command.lower():
        console.print("[green]✅ Autopilot set to FULL AUTO for new workflows[/green]")
    elif 'smart' in command.lower():
        console.print("[blue]🔄 Autopilot set to SMART AUTO for new workflows[/blue]")
    elif 'off' in command.lower():
        console.print("[yellow]🎮 Autopilot set to HUMAN CONTROL for new workflows[/yellow]")
    else:
        console.print("[red]Invalid autopilot command. Use 'on', 'smart', or 'off'[/red]")


async def display_intelligence_result(result, workflow_state):
    """Display the results of an Intelligence Layer workflow."""
    console.print(f"\n[bold green]🎉 Workflow Completed: {result.workflow_id}[/bold green]")
    
    # Show execution summary
    if result.execution_summary:
        console.print(f"\n[bold yellow]📊 Execution Summary:[/bold yellow]")
        summary = result.execution_summary
        console.print(f"   Total steps: {summary.get('total_steps', 0)}")
        console.print(f"   Human decisions: {summary.get('human_decisions', 0)}")
        console.print(f"   Duration: {summary.get('duration_seconds', 0):.1f} seconds")
        console.print(f"   Autopilot mode: {summary.get('autopilot_mode', 'unknown')}")
    
    # Show final outputs
    if result.final_outputs:
        console.print(f"\n[bold yellow]🎯 Key Results:[/bold yellow]")
        for key, value in result.final_outputs.items():
            if isinstance(value, (str, int, float)):
                console.print(f"   {key.replace('_', ' ').title()}: {value}")
            elif isinstance(value, list) and len(value) > 0:
                console.print(f"   {key.replace('_', ' ').title()}: {len(value)} items")
    
    # Show performance metrics
    if result.performance_metrics:
        console.print(f"\n[bold yellow]⚡ Performance:[/bold yellow]")
        metrics = result.performance_metrics
        console.print(f"   Success rate: {metrics.get('success_rate', 0):.1%}")
        console.print(f"   Efficiency score: {metrics.get('efficiency_score', 0):.1%}")
    
    # Show human interaction summary
    if result.human_interaction_summary:
        console.print(f"\n[bold yellow]👥 Human Interaction:[/bold yellow]")
        interaction = result.human_interaction_summary
        console.print(f"   Decision points: {interaction.get('decision_count', 0)}")
        if interaction.get('last_interaction'):
            console.print(f"   Last interaction: {interaction['last_interaction']}")


async def is_workflow_continuation_command(user_input: str, current_workflow_id: str, workflow_brain: WorkflowBrain) -> bool:
    """Check if user input is a workflow continuation command."""
    if not current_workflow_id or current_workflow_id not in workflow_brain.active_workflows:
        return False
    
    # Keywords that suggest workflow continuation
    continuation_keywords = [
        "step", "next", "continue", "proceed", "do", "run", "execute",
        "option", "choice", "select", "pick", "take", "go"
    ]
    
    # Number patterns (step 2, option 1, etc.)
    import re
    has_step_number = bool(re.search(r'\b(?:step|option|choice)\s*\d+\b', user_input.lower()))
    has_standalone_number = bool(re.search(r'^\s*\d+\s*$', user_input.strip()))
    has_continuation_keyword = any(keyword in user_input.lower() for keyword in continuation_keywords)
    
    return has_step_number or has_standalone_number or (has_continuation_keyword and len(user_input.split()) <= 4)


async def handle_workflow_continuation(user_input: str, current_workflow_id: str, workflow_brain: WorkflowBrain, active_workflows: dict):
    """Handle workflow continuation commands."""
    workflow_state = workflow_brain.active_workflows[current_workflow_id]
    
    console.print(f"\n[bold blue]🔄 Continuing workflow: {workflow_state.workflow_title}[/bold blue]")
    
    # Parse the continuation command
    import re
    
    # Check for step/option numbers
    step_match = re.search(r'(?:step|option|choice)\s*(\d+)', user_input.lower())
    number_match = re.search(r'^\s*(\d+)\s*$', user_input.strip())
    
    if step_match or number_match:
        # User specified a specific step/option number
        step_num = int((step_match or number_match).group(1))
        console.print(f"   📋 Executing step {step_num}...")
        
        # Continue workflow execution
        try:
            result = await workflow_brain.execute_workflow(current_workflow_id)
            await display_intelligence_result(result, workflow_state)
            
            # Update session tracking
            active_workflows[current_workflow_id]['last_activity'] = datetime.now()
            active_workflows[current_workflow_id]['status'] = result.status.value
            
        except Exception as e:
            console.print(f"[red]Error continuing workflow: {str(e)}[/red]")
    
    else:
        # General continuation command
        console.print(f"   🚀 Continuing with next step...")
        
        try:
            result = await workflow_brain.execute_workflow(current_workflow_id)
            await display_intelligence_result(result, workflow_state)
            
            # Update session tracking
            active_workflows[current_workflow_id]['last_activity'] = datetime.now()
            active_workflows[current_workflow_id]['status'] = result.status.value
            
        except Exception as e:
            console.print(f"[red]Error continuing workflow: {str(e)}[/red]")


async def continue_workflow(workflow_brain: WorkflowBrain, workflow_id: str, active_workflows: dict):
    """Continue an existing workflow."""
    try:
        console.print(f"\n[bold blue]🔄 Resuming workflow: {workflow_id}[/bold blue]")
        
        result = await workflow_brain.execute_workflow(workflow_id)
        
        workflow_state = workflow_brain.active_workflows[workflow_id]
        await display_intelligence_result(result, workflow_state)
        
        # Update session tracking
        active_workflows[workflow_id]['last_activity'] = datetime.now()
        active_workflows[workflow_id]['status'] = result.status.value
        
    except Exception as e:
        console.print(f"[red]Error continuing workflow: {str(e)}[/red]")


async def chat_interface():
    """Universal intelligent chat interface with automatic agent routing."""
    
    # Configuration for Universal Orchestrator
    config = UniversalOrchestratorConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        routing_confidence_threshold=float(os.getenv("ROUTING_CONFIDENCE_THRESHOLD", "0.7")),
        enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
        cache_ttl_minutes=int(os.getenv("CACHE_TTL_MINUTES", "30"))
    )
    
    if not config.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please set your Anthropic API key in the .env file.")
        return
    
    # Initialize Universal Orchestrator
    orchestrator = UniversalOrchestrator(config)
    
    # Note: Universal Orchestrator doesn't need progress callback
    # Individual orchestrators handle their own progress reporting
    
    try:
        await orchestrator.initialize()
        
        # Welcome message
        console.print("\n[bold magenta]🧠 Universal AI:[/bold magenta] Hi! I can help with branding, business strategy, or technical automation. What can I help you with?\n")
        console.print("[dim]💡 Branding Examples:[/dim]")
        console.print("[dim]  • 'Create a brand for my coffee shop'[/dim]")
        console.print("[dim]  • 'Generate a logo for my tech startup'[/dim]")
        console.print("[dim]  • 'Make branding and actual logo images for my pen store'[/dim]")
        console.print("[dim]💡 Other Examples: 'Help me grow my business', 'Monitor my email for urgent messages'[/dim]")
        
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        
        while True:
            try:
                # Get user input
                user_input = console.input("[bold green]You:[/bold green] ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye! Your session has been saved.[/yellow]")
                    break
                    
                elif user_input.lower() == 'continue':
                    await handle_continue_command(orchestrator)
                    continue
                    
                elif user_input.lower() == 'sessions':
                    await show_active_sessions(orchestrator)
                    continue
                    
                elif user_input.lower() in ['help', '?']:
                    await show_help_message()
                    continue
                
                # Process user request
                console.print(f"\n[bold magenta]🧠 Universal AI:[/bold magenta] Analyzing your request and routing to the best specialist...\n")
                
                result = await orchestrator.process_query(user_input, session_id)
                
                # Display results
                await display_universal_result(result)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Type 'continue' to resume later.[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error(f"Chat interface error: {e}")
                
    finally:
        await orchestrator.close()


async def handle_continue_command(orchestrator: HeyJarvisOrchestrator):
    """Handle the continue command to resume sessions."""
    sessions = await orchestrator.list_active_sessions()
    
    if not sessions:
        console.print("[yellow]No active sessions found.[/yellow]")
        return
    
    # Show available sessions in the expected format
    console.print("[bold cyan]💬 You have these sessions you can resume:[/bold cyan]\n")
    
    for i, session in enumerate(sessions, 1):
        # Calculate time ago (simplified)
        import datetime
        try:
            session_time = datetime.datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = now - session_time
            
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                time_ago = f"{int(time_diff.total_seconds() // 60)} minutes ago"
            else:
                time_ago = f"{int(time_diff.total_seconds() // 3600)} hour{'s' if time_diff.total_seconds() >= 7200 else ''} ago"
        except:
            time_ago = "Unknown time"
        
        # Determine completion percentage based on status
        if session['status'] == 'completed':
            completion = "100%"
        elif session['status'] == 'failed':
            completion = "0%"
        else:
            completion = "60%"  # Default for in-progress
            
        console.print(f"Session started {time_ago} ({completion} complete)")
    
    console.print(f"\nWhich would you like to continue? (1-{len(sessions)}):")
    
    # Let user select session
    try:
        choice = console.input("").strip()
        if not choice:
            return
            
        session_num = int(choice) - 1
        if 0 <= session_num < len(sessions):
            selected_session = sessions[session_num]
            console.print(f"[green]Resuming session {selected_session['session_id']}...[/green]")
            
            # Load and display session state
            state = await orchestrator.recover_session(selected_session['session_id'])
            if state:
                console.print(f"[cyan]Previous request:[/cyan] {state.get('user_request', 'Unknown')}")
                console.print(f"[cyan]Current status:[/cyan] {state.get('deployment_status', 'Unknown')}")
                
                # Continue processing if needed
                if state.get('deployment_status') != 'completed':
                    result = await orchestrator.process_request(
                        state['user_request'], 
                        selected_session['session_id']
                    )
                    await display_result(result)
                else:
                    console.print("[green]Session was already completed![/green]")
        else:
            console.print("[red]Invalid session number.[/red]")
            
    except ValueError:
        console.print("[red]Please enter a valid number.[/red]")
    except Exception as e:
        console.print(f"[red]Error resuming session: {str(e)}[/red]")


async def show_active_sessions(orchestrator: HeyJarvisOrchestrator):
    """Show all active sessions."""
    sessions = await orchestrator.list_active_sessions()
    
    if not sessions:
        console.print("[yellow]No active sessions found.[/yellow]")
        return
    
    table = Table(title="Active Sessions")
    table.add_column("Session ID", style="green")
    table.add_column("Request", style="cyan")
    table.add_column("Status", style="blue")
    table.add_column("Last Activity", style="yellow")
    
    for session in sessions:
        table.add_row(
            session['session_id'],
            session.get('request', 'Unknown')[:50] + "..." if len(session.get('request', '')) > 50 else session.get('request', 'Unknown'),
            session['status'],
            session['timestamp']
        )
    
    console.print(table)


async def show_help_message():
    """Display comprehensive help information including logo generation capabilities."""
    console.print("\n[bold cyan]🆘 HeyJarvis Universal AI - Help Guide[/bold cyan]")
    
    console.print("\n[bold yellow]💼 BRANDING & LOGO GENERATION[/bold yellow]")
    console.print("I can create complete brand identities including actual logo images!")
    
    console.print("\n[dim]📝 Brand Identity Examples:[/dim]")
    console.print("  • 'Create a brand for my coffee shop'")
    console.print("  • 'I need branding for my tech startup'")
    console.print("  • 'Brand identity for my consulting business'")
    
    console.print("\n[dim]🎨 Logo Generation Examples:[/dim]")
    console.print("  • 'Generate a logo for my bakery'")
    console.print("  • 'Create logo images for my app'")
    console.print("  • 'Make branding and actual logo for my store'")
    console.print("  • 'Design a visual logo for my agency'")
    
    console.print("\n[bold yellow]🏢 BUSINESS STRATEGY[/bold yellow]")
    console.print("  • 'Help me grow my business'")
    console.print("  • 'Create a marketing strategy'")
    console.print("  • 'Coordinate my sales and marketing teams'")
    
    console.print("\n[bold yellow]🤖 TECHNICAL AUTOMATION[/bold yellow]")
    console.print("  • 'Monitor my email for urgent messages'")
    console.print("  • 'Create a web scraper for product prices'")
    console.print("  • 'Build an agent to track social media'")
    
    console.print("\n[bold green]💡 SPECIAL FEATURES[/bold green]")
    console.print("  🖼️  DALL-E Logo Generation: Get actual logo images, not just prompts")
    console.print("  🎨  Complete Brand Packages: Colors, names, domains, and visuals")
    console.print("  🧠  Intelligent Routing: I automatically pick the right specialist")
    console.print("  📊  Multi-Agent Coordination: Complex workflows handled seamlessly")
    
    console.print("\n[bold cyan]⌨️ COMMANDS[/bold cyan]")
    console.print("  • Type 'help' or '?' - Show this help message")
    console.print("  • Type 'sessions' - View active sessions")
    console.print("  • Type 'continue' - Resume previous session")
    console.print("  • Type 'exit' or 'quit' - End conversation")
    
    console.print("\n[bold magenta]🚀 PRO TIPS[/bold magenta]")
    console.print("  • Be specific: 'tech startup' vs 'business'")
    console.print("  • Mention 'logo' if you want actual images generated")
    console.print("  • Include your industry for better brand targeting")
    console.print("  • Ask follow-up questions to refine results")
    
    console.print(f"\n[dim]Ready to help! What can I assist you with?[/dim]\n")


async def display_result(result: Dict[str, Any]):
    """Display the orchestrator result in a user-friendly format."""
    status = result.get('deployment_status')
    
    if hasattr(status, 'value'):
        status_str = status.value
    else:
        status_str = str(status)
    
    # Check if clarification is needed
    needs_clarification = result.get('needs_clarification', False)
    clarification_questions = result.get('clarification_questions', [])
    suggestions = result.get('suggestions', [])
    
    if needs_clarification and clarification_questions:
        # Pick the most important question (first one) and top 2 suggestions
        main_question = clarification_questions[0] if clarification_questions else "Could you provide more details?"
        top_suggestions = suggestions[:2] if suggestions else []
        
        console.print(f"[bold cyan]💬 HeyJarvis:[/bold cyan] {main_question}")
        
        # Show only top 2 suggestions to keep it concise
        if top_suggestions:
            console.print("\n[bold yellow]💡 For example:[/bold yellow]")
            for suggestion in top_suggestions:
                console.print(f"  • {suggestion}")
        
        console.print()
        return
    
    if status_str == 'completed':
        agent_spec = result.get('agent_spec')
        if agent_spec:
            # Success message
            console.print(f"[bold green]✅ Success! I've created '{agent_spec['name']}' for you.[/bold green]")
            console.print(f"It will: {agent_spec['description']}")
            console.print("[bold]Capabilities:[/bold]")
            for cap in agent_spec.get('capabilities', []):
                console.print(f"  • {cap}")
            console.print()
            
            # Ask what else they want to automate
            console.print("[bold cyan]💬 What else would you like to automate?[/bold cyan]")
        else:
            console.print("[green]Agent created successfully![/green]")
            
    elif status_str == 'failed':
        error_msg = result.get('error_message', 'Unknown error occurred')
        console.print(Panel(
            f"[bold red]❌ Agent Creation Failed[/bold red]\n\n"
            f"[red]{error_msg}[/red]\n\n"
            f"[dim]Would you like to try rephrasing your request?[/dim]",
            title="Error",
            border_style="red"
        ))
    else:
        console.print(f"[yellow]Status: {status_str}[/yellow]")
    
    console.print()  # Add spacing


def show_demo_menu(completed_demos: set):
    """Show the interactive demo menu with progress tracking."""
    console.clear()
    
    console.print(Panel.fit(
        "[bold blue]🎭 HeyJarvis Interactive Demo[/bold blue]\n\n"
        "Choose a demo scenario:",
        title="Interactive Demo Mode",
        border_style="blue"
    ))
    
    # Demo options with completion status
    demos = [
        ("basic", "📧 Basic: Create an email monitoring agent"),
        ("recovery", "🔄 Recovery: Resume an interrupted session"),
        ("clarification", "💬 Clarification: Handle ambiguous requests"),
        ("advanced", "🚀 Advanced: Multi-step agent creation"),
        ("error", "❌ Error Handling: See how errors are handled"),
        ("jarvis_sales", "💼 Jarvis: Grow revenue with Sales department"),
        ("jarvis_costs", "💰 Jarvis: Reduce operational costs")
    ]
    
    console.print()
    for i, (demo_key, description) in enumerate(demos, 1):
        status = "✅" if demo_key in completed_demos else "⭕"
        console.print(f"{i}. {status} {description}")
    
    console.print(f"\n[dim]Progress: {len(completed_demos)}/7 demos completed[/dim]")
    console.print("[dim]Type 'exit' to quit the demo[/dim]")


async def demo_mode():
    """Interactive demo mode showing HeyJarvis capabilities."""
    
    # Configuration
    config = OrchestratorConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        max_retries=int(os.getenv("MAX_RETRIES", "3"))
    )
    
    if not config.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please set your Anthropic API key in the .env file.")
        return
    
    orchestrator = HeyJarvisOrchestrator(config)
    
    def progress_callback(node_name: str, progress: int, message: str):
        console.print(f"📊 Progress: {progress}% - {message}")
    
    orchestrator.set_progress_callback(progress_callback)
    
    try:
        await orchestrator.initialize()
        completed_demos = set()
        
        while True:
            show_demo_menu(completed_demos)
            choice = console.input("\nEnter your choice (1-7, or 'exit'): ").strip().lower()
            
            if choice in ['exit', 'quit', 'q']:
                console.print("\n[yellow]Thanks for trying the HeyJarvis demo! 👋[/yellow]")
                break
            
            if choice == '1':
                await demo_basic_agent_creation(orchestrator)
                completed_demos.add('basic')
            elif choice == '2':
                await demo_session_recovery(orchestrator)
                completed_demos.add('recovery')
            elif choice == '3':
                await demo_clarification_flow(orchestrator)
                completed_demos.add('clarification')
            elif choice == '4':
                await demo_advanced_creation(orchestrator)
                completed_demos.add('advanced')
            elif choice == '5':
                await demo_error_handling(orchestrator)
                completed_demos.add('error')
            elif choice == '6':
                await jarvis_demo_sales_growth(orchestrator)
                completed_demos.add('jarvis_sales')
            elif choice == '7':
                await jarvis_demo_cost_reduction(orchestrator)
                completed_demos.add('jarvis_costs')
            else:
                console.print("[red]Invalid choice. Please select 1-7 or 'exit'.[/red]")
                console.input("\nPress Enter to continue...")
                continue
            
            # Check if all demos completed
            if len(completed_demos) == 7:
                console.print(Panel(
                    "[bold green]🎉 Congratulations! You've completed all demos![/bold green]\n\n"
                    "You've experienced all the key features of HeyJarvis:\n"
                    "• Basic agent creation\n"
                    "• Session recovery\n"
                    "• Clarification handling\n"
                    "• Advanced workflows\n"
                    "• Error handling\n"
                    "• Jarvis business automation\n"
                    "• Department coordination\n\n"
                    "Ready to use HeyJarvis? Run: [bold]python main.py[/bold]",
                    title="Demo Complete!",
                    border_style="green"
                ))
                console.input("\nPress Enter to exit...")
                break
            
            # Ask if they want to continue
            continue_choice = console.input("\n[dim]Press Enter to return to menu, or 'exit' to quit:[/dim] ").strip().lower()
            if continue_choice in ['exit', 'quit', 'q']:
                break
        
    finally:
        await orchestrator.close()


async def demo_basic_agent_creation(orchestrator: HeyJarvisOrchestrator):
    """Demo: Basic Agent Creation with user interaction."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]📧 Demo: Basic Agent Creation[/bold blue]\n\n"
        "Let's create your first agent together!\n"
        "This demo will show you how HeyJarvis understands natural language\n"
        "and creates intelligent agents from your descriptions.",
        title="Interactive Tutorial",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]💡 Tip:[/bold yellow] Try typing something like:")
    console.print("   [dim]'Monitor my email for urgent messages'[/dim]")
    console.print("   [dim]'Create a daily backup agent'[/dim]")
    console.print("   [dim]'Set up social media automation'[/dim]")
    
    # Get user input
    user_input = console.input("\n[bold green]You:[/bold green] ").strip()
    
    if not user_input:
        console.print("[yellow]No input provided. Let's try a sample request...[/yellow]")
        user_input = "Monitor my email for urgent messages"
        console.print(f"[dim]Using: {user_input}[/dim]")
    
    # Tutorial annotation
    console.print(Panel(
        "🎯 [bold]What's happening now:[/bold]\n"
        "HeyJarvis will analyze your request and break it down into steps.\n"
        "Watch the progress indicators to see each stage of agent creation!",
        style="dim yellow"
    ))
    
    console.print("\n[dim]→ Starting agent creation workflow...[/dim]")
    
    # Process the request
    session_id = "demo_basic_001"
    result = await orchestrator.process_request(user_input, session_id)
    
    # Show result with educational context
    await display_result(result)
    
    # Educational explanation
    console.print(Panel(
        "[bold green]✅ Great job! Here's what just happened:[/bold green]\n\n"
        "1. [bold]Understanding:[/bold] HeyJarvis parsed your natural language request\n"
        "2. [bold]Intent Analysis:[/bold] Determined you wanted to create an agent\n"
        "3. [bold]Specification:[/bold] Generated detailed agent capabilities\n"
        "4. [bold]Deployment:[/bold] Saved the agent to the system\n"
        "5. [bold]Ready to Use:[/bold] Your agent is now operational!\n\n"
        "💡 [bold]Key Feature:[/bold] Notice how HeyJarvis understood your intent\n"
        "without requiring technical specifications!",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def demo_session_recovery(orchestrator: HeyJarvisOrchestrator):
    """Demo: Session Recovery - simulate interruption and recovery."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]🔄 Demo: Session Recovery[/bold blue]\n\n"
        "This demo shows how HeyJarvis handles interruptions.\n"
        "We'll start creating an agent, simulate a disconnection,\n"
        "then show you how to resume exactly where you left off!",
        title="Interactive Tutorial",
        border_style="blue"
    ))
    
    # Start an agent creation
    console.print("\n[bold yellow]Step 1:[/bold yellow] Let's start creating an agent...")
    console.print("[dim]Creating a file backup automation agent...[/dim]")
    
    # Simulate starting a session
    session_id = "demo_recovery_001"
    
    # Create initial request
    user_request = "Create an agent that backs up my important files to cloud storage daily"
    console.print(f"\n[bold green]Request:[/bold green] {user_request}")
    
    # Start processing but we'll simulate interruption
    console.print("\n📊 Progress: 20% - 🔍 Understanding your request...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 40% - 🤔 Analyzing intent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 60% - 🔎 Checking existing agents...")
    
    # Simulate interruption
    console.print("\n[bold red]💥 Oh no! Let's simulate a disconnection...[/bold red]")
    console.print("[dim]Connection lost... Session interrupted at 60%[/dim]")
    
    console.input("\n[dim]Press Enter to see session recovery in action...[/dim]")
    
    # Show recovery process
    console.print("\n[bold yellow]Step 2:[/bold yellow] Recovering your session...")
    console.print("[bold cyan]💬 Type 'continue' to see session recovery:[/bold cyan]")
    
    recovery_input = console.input("\n[bold green]You:[/bold green] ").strip().lower()
    
    if recovery_input != 'continue':
        console.print("[yellow]For this demo, let's proceed with session recovery...[/yellow]")
    
    # Simulate showing available sessions
    console.print("\n[bold cyan]💬 You have these sessions you can resume:[/bold cyan]\n")
    console.print("Session started 2 minutes ago (60% complete)")
    console.print(f"Request: {user_request}")
    console.print("\nWhich would you like to continue? (1):")
    
    choice = console.input("").strip()
    if not choice:
        choice = "1"
    
    # Continue processing from where we left off
    console.print(f"\n[bold green]Resuming session...[/bold green]")
    console.print("📊 Progress: 80% - 🛠️ Creating your agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 100% - 🚀 Deploying agent...")
    
    # Complete the request
    result = await orchestrator.process_request(user_request, session_id)
    await display_result(result)
    
    # Educational explanation
    console.print(Panel(
        "[bold green]🎯 Session Recovery Demonstrated![/bold green]\n\n"
        "1. [bold]Persistence:[/bold] HeyJarvis saved your progress automatically\n"
        "2. [bold]Recovery:[/bold] 'continue' command showed available sessions\n"
        "3. [bold]Resume:[/bold] Picked up exactly where you left off (60%)\n"
        "4. [bold]Completion:[/bold] Finished the remaining 40% of work\n\n"
        "💡 [bold]Key Feature:[/bold] Never lose progress, even with interruptions!\n"
        "Sessions are automatically saved to Redis for persistence.",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def demo_clarification_flow(orchestrator: HeyJarvisOrchestrator):
    """Demo: Clarification Flow - handle ambiguous requests."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]💬 Demo: Clarification Flow[/bold blue]\n\n"
        "This demo shows how HeyJarvis handles vague or ambiguous requests.\n"
        "When your request needs clarification, HeyJarvis will ask\n"
        "intelligent follow-up questions to understand exactly what you want.",
        title="Interactive Tutorial",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]💡 Try typing something vague like:[/bold yellow]")
    console.print("   [dim]'set up monitoring'[/dim]")
    console.print("   [dim]'create automation'[/dim]")
    console.print("   [dim]'help with notifications'[/dim]")
    
    # Get ambiguous input
    user_input = console.input("\n[bold green]You:[/bold green] ").strip()
    
    if not user_input:
        console.print("[yellow]Let's try with a vague request...[/yellow]")
        user_input = "set up monitoring"
        console.print(f"[dim]Using: {user_input}[/dim]")
    
    # Tutorial annotation
    console.print(Panel(
        "🤔 [bold]HeyJarvis is analyzing your request...[/bold]\n"
        "Since this is somewhat vague, HeyJarvis will ask clarifying questions\n"
        "to understand exactly what type of monitoring you need.",
        style="dim yellow"
    ))
    
    # Simulate clarification process
    console.print(f"\n📊 Progress: 20% - 🔍 Understanding your request...")
    await asyncio.sleep(1)
    
    # Simulate HeyJarvis asking for clarification
    console.print("\n[bold cyan]💬 HeyJarvis:[/bold cyan] I'd love to help you set up monitoring! ")
    console.print("To create the best agent for you, I need a bit more detail:")
    console.print("\n[bold]What would you like to monitor?[/bold]")
    console.print("• 📧 Email inbox for important messages")
    console.print("• 💾 System resources (CPU, memory, disk)")
    console.print("• 🌐 Website uptime and performance")
    console.print("• 📁 File changes in specific directories")
    console.print("• 📊 Social media mentions or metrics")
    
    clarification = console.input("\n[bold green]You:[/bold green] ").strip()
    
    if not clarification:
        clarification = "email inbox for important messages"
        console.print(f"[dim]Using: {clarification}[/dim]")
    
    # Continue with clarified request
    refined_request = f"Monitor {clarification}"
    console.print(f"\n[bold cyan]💬 HeyJarvis:[/bold cyan] Perfect! I'll create an agent to monitor {clarification}.")
    
    # Continue processing
    console.print("\n📊 Progress: 40% - 🤔 Analyzing refined intent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 60% - 🔎 Checking existing agents...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 80% - 🛠️ Creating your agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 100% - 🚀 Deploying agent...")
    
    # Process the refined request
    session_id = "demo_clarification_001"
    result = await orchestrator.process_request(refined_request, session_id)
    await display_result(result)
    
    # Educational explanation
    console.print(Panel(
        "[bold green]💡 Clarification Flow Demonstrated![/bold green]\n\n"
        "1. [bold]Vague Input:[/bold] You provided a general request\n"
        "2. [bold]Smart Questions:[/bold] HeyJarvis asked specific clarifying questions\n"
        "3. [bold]Context Building:[/bold] Your responses refined the requirements\n"
        "4. [bold]Precise Creation:[/bold] Final agent matched your exact needs\n\n"
        "🎯 [bold]Key Feature:[/bold] HeyJarvis doesn't guess - it asks!\n"
        "This ensures you get exactly the agent you need.",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def demo_advanced_creation(orchestrator: HeyJarvisOrchestrator):
    """Demo: Advanced Multi-Step Agent Creation."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]🚀 Demo: Advanced Multi-Step Creation[/bold blue]\n\n"
        "This demo shows HeyJarvis handling complex, multi-step workflows.\n"
        "We'll create a sophisticated agent with multiple capabilities\n"
        "and show how context is preserved across interactions.",
        title="Interactive Tutorial",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]Scenario:[/bold yellow] Let's create a comprehensive social media management agent")
    console.print("[dim]This will involve multiple steps and refinements...[/dim]")
    
    # Step 1: Initial complex request
    console.print("\n[bold green]Step 1: Initial Request[/bold green]")
    initial_request = "Create a social media agent that posts content, tracks engagement, and responds to mentions"
    console.print(f"[bold green]Request:[/bold green] {initial_request}")
    
    session_id = "demo_advanced_001"
    console.print("\n[dim]→ Processing complex multi-capability request...[/dim]")
    
    result1 = await orchestrator.process_request(initial_request, session_id)
    await display_result(result1)
    
    # Step 2: Refinement
    console.print("\n[bold green]Step 2: Adding Requirements[/bold green]")
    console.print("[bold cyan]💬 HeyJarvis:[/bold cyan] Great! I can enhance this agent further.")
    console.print("Would you like to add any specific features or integrations?")
    
    console.print("\n[bold yellow]💡 Try adding:[/bold yellow] 'Also schedule posts for optimal times and create analytics reports'")
    
    refinement = console.input("\n[bold green]You:[/bold green] ").strip()
    
    if not refinement:
        refinement = "Also schedule posts for optimal times and create analytics reports"
        console.print(f"[dim]Using: {refinement}[/dim]")
    
    # Process refinement
    console.print(Panel(
        "🧠 [bold]Context Preservation in Action:[/bold]\n"
        "HeyJarvis remembers the existing agent and will enhance it\n"
        "rather than creating a completely new one.",
        style="dim yellow"
    ))
    
    enhanced_request = f"{initial_request}. {refinement}"
    result2 = await orchestrator.process_request(enhanced_request, session_id)
    await display_result(result2)
    
    # Step 3: Final customization
    console.print("\n[bold green]Step 3: Platform-Specific Customization[/bold green]")
    console.print("[bold cyan]💬 HeyJarvis:[/bold cyan] Which social media platforms should this agent support?")
    
    platforms = console.input("\n[bold green]You:[/bold green] ").strip()
    
    if not platforms:
        platforms = "Twitter, Instagram, and LinkedIn"
        console.print(f"[dim]Using: {platforms}[/dim]")
    
    final_request = f"{enhanced_request}. Focus on {platforms}"
    console.print(f"\n[dim]→ Customizing for specific platforms: {platforms}[/dim]")
    
    result3 = await orchestrator.process_request(final_request, session_id)
    await display_result(result3)
    
    # Educational explanation
    console.print(Panel(
        "[bold green]🚀 Advanced Creation Demonstrated![/bold green]\n\n"
        "1. [bold]Complex Input:[/bold] Started with multi-capability request\n"
        "2. [bold]Iterative Refinement:[/bold] Added features step-by-step\n"
        "3. [bold]Context Preservation:[/bold] Each step built on the previous\n"
        "4. [bold]Platform Customization:[/bold] Tailored to specific needs\n"
        "5. [bold]Unified Agent:[/bold] Single agent with all capabilities\n\n"
        "💡 [bold]Key Feature:[/bold] HeyJarvis handles complexity naturally!\n"
        "Build sophisticated agents through conversation.",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def demo_error_handling(orchestrator: HeyJarvisOrchestrator):
    """Demo: Error Handling and Recovery."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]❌ Demo: Error Handling[/bold blue]\n\n"
        "This demo shows how HeyJarvis gracefully handles various types\n"
        "of errors and provides helpful recovery suggestions.\n"
        "You'll see retry mechanisms and error recovery in action.",
        title="Interactive Tutorial",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]We'll demonstrate several error scenarios:[/bold yellow]")
    console.print("1. 🤔 Ambiguous requests that need clarification")
    console.print("2. 🚫 Invalid or impossible requests")
    console.print("3. 🔄 Network/service interruptions")
    console.print("4. ♻️ Automatic retry mechanisms")
    
    # Error Type 1: Ambiguous/unclear request
    console.print("\n[bold green]Error Demo 1: Handling Unclear Requests[/bold green]")
    unclear_request = "do something with my computer"
    console.print(f"[bold green]Request:[/bold green] {unclear_request}")
    
    console.print(Panel(
        "🎯 [bold]What should happen:[/bold]\n"
        "HeyJarvis will recognize this is too vague and ask for clarification\n"
        "rather than making assumptions or failing silently.",
        style="dim yellow"
    ))
    
    session_id = "demo_error_001"
    
    # This will likely trigger clarification flow
    console.print("\n[dim]→ Processing unclear request...[/dim]")
    result1 = await orchestrator.process_request(unclear_request, session_id)
    
    if result1.get('error_message'):
        console.print(f"[yellow]Expected behavior: {result1['error_message']}[/yellow]")
    else:
        await display_result(result1)
    
    # Error Type 2: Impossible request
    console.print("\n[bold green]Error Demo 2: Impossible Requests[/bold green]")
    impossible_request = "create an agent that can travel back in time"
    console.print(f"[bold green]Request:[/bold green] {impossible_request}")
    
    console.print(Panel(
        "🎯 [bold]What should happen:[/bold]\n"
        "HeyJarvis will recognize this is impossible and suggest\n"
        "alternative approaches or clarify what you really need.",
        style="dim yellow"
    ))
    
    console.print("\n[dim]→ Processing impossible request...[/dim]")
    result2 = await orchestrator.process_request(impossible_request, "demo_error_002")
    
    if result2.get('error_message'):
        console.print(f"[yellow]Graceful handling: {result2['error_message']}[/yellow]")
    else:
        await display_result(result2)
    
    # Error Type 3: Demonstrate retry mechanism
    console.print("\n[bold green]Error Demo 3: Retry Mechanism[/bold green]")
    console.print("[dim]Demonstrating how HeyJarvis retries on temporary failures...[/dim]")
    
    # Simulate a request that might need retries
    retry_request = "create a complex integration agent"
    console.print(f"[bold green]Request:[/bold green] {retry_request}")
    
    console.print("\n📊 Progress: 20% - 🔍 Understanding your request...")
    await asyncio.sleep(1)
    console.print("⚠️  [yellow]Temporary issue encountered... retrying (1/3)[/yellow]")
    await asyncio.sleep(1)
    console.print("📊 Progress: 40% - 🤔 Analyzing intent... (retry successful)")
    await asyncio.sleep(1)
    console.print("📊 Progress: 60% - 🔎 Checking existing agents...")
    await asyncio.sleep(1)
    
    result3 = await orchestrator.process_request(retry_request, "demo_error_003")
    await display_result(result3)
    
    # Error Type 4: Recovery suggestions
    console.print("\n[bold green]Error Demo 4: Recovery Suggestions[/bold green]")
    console.print("[bold cyan]💬 HeyJarvis:[/bold cyan] When errors occur, I provide helpful suggestions:")
    
    suggestions = [
        "🔄 Try rephrasing your request with more specific details",
        "🎯 Break complex requests into smaller steps", 
        "💬 Use the clarification flow to refine requirements",
        "📞 Check if external services are available",
        "🔍 Review similar successful agent examples"
    ]
    
    for suggestion in suggestions:
        console.print(f"  • {suggestion}")
    
    # Educational explanation
    console.print(Panel(
        "[bold green]❌ Error Handling Demonstrated![/bold green]\n\n"
        "1. [bold]Unclear Requests:[/bold] Asks for clarification instead of guessing\n"
        "2. [bold]Impossible Tasks:[/bold] Explains limitations and suggests alternatives\n"
        "3. [bold]Retry Logic:[/bold] Automatically retries transient failures\n"
        "4. [bold]Helpful Messages:[/bold] Provides actionable recovery suggestions\n"
        "5. [bold]Graceful Degradation:[/bold] Fails safely with useful feedback\n\n"
        "💡 [bold]Key Feature:[/bold] HeyJarvis never leaves you stuck!\n"
        "Every error includes guidance on how to proceed.",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def handle_jarvis_continue_command(jarvis: Jarvis):
    """Handle the continue command for Jarvis sessions."""
    sessions = await jarvis.list_active_sessions()
    
    if not sessions:
        console.print("[yellow]No active sessions found.[/yellow]")
        return
    
    # Show available sessions
    console.print("[bold magenta]🧠 Jarvis:[/bold magenta] You have these sessions you can resume:\n")
    
    for i, session in enumerate(sessions, 1):
        # Calculate time ago (simplified)
        import datetime
        try:
            session_time = datetime.datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = now - session_time
            
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                time_ago = f"{int(time_diff.total_seconds() // 60)} minutes ago"
            else:
                time_ago = f"{int(time_diff.total_seconds() // 3600)} hour{'s' if time_diff.total_seconds() >= 7200 else ''} ago"
        except:
            time_ago = "Unknown time"
        
        # Determine completion percentage based on status
        if session['status'] == 'completed':
            completion = "100%"
        elif session['status'] == 'failed':
            completion = "0%"
        else:
            completion = "60%"  # Default for in-progress
            
        console.print(f"Session started {time_ago} ({completion} complete)")
    
    console.print(f"\nWhich would you like to continue? (1-{len(sessions)}):")
    
    # Let user select session
    try:
        choice = console.input("").strip()
        if not choice:
            return
            
        session_num = int(choice) - 1
        if 0 <= session_num < len(sessions):
            selected_session = sessions[session_num]
            console.print(f"[green]Resuming session {selected_session['session_id']}...[/green]")
            
            # Load and display session state
            state = await jarvis.recover_session(selected_session['session_id'])
            if state:
                console.print(f"[magenta]Previous request:[/magenta] {state.get('user_request', 'Unknown')}")
                console.print(f"[magenta]Current status:[/magenta] {state.get('deployment_status', 'Unknown')}")
                
                # Continue processing if needed
                if state.get('deployment_status') != 'completed':
                    result = await jarvis.process_business_request(
                        state['user_request'], 
                        selected_session['session_id']
                    )
                    await display_jarvis_result(result)
                else:
                    console.print("[green]Session was already completed![/green]")
        else:
            console.print("[red]Invalid session number.[/red]")
            
    except ValueError:
        console.print("[red]Please enter a valid number.[/red]")
    except Exception as e:
        console.print(f"[red]Error resuming session: {str(e)}[/red]")


async def show_jarvis_active_sessions(jarvis: Jarvis):
    """Show all active Jarvis sessions."""
    sessions = await jarvis.list_active_sessions()
    
    if not sessions:
        console.print("[yellow]No active sessions found.[/yellow]")
        return
    
    table = Table(title="Active Jarvis Sessions")
    table.add_column("Session ID", style="green")
    table.add_column("Request", style="cyan")
    table.add_column("Status", style="blue")
    table.add_column("Last Activity", style="yellow")
    
    for session in sessions:
        table.add_row(
            session['session_id'],
            session.get('request', 'Unknown')[:50] + "..." if len(session.get('request', '')) > 50 else session.get('request', 'Unknown'),
            session['status'],
            session['timestamp']
        )
    
    console.print(table)


async def show_business_insights(jarvis: Jarvis, session_id: str):
    """Show business insights and optimization suggestions."""
    try:
        insights = await jarvis.get_business_insights(session_id)
        
        if "error" in insights:
            console.print(f"[yellow]Business insights not available: {insights['error']}[/yellow]")
            console.print("[dim]Tip: Create some agents first to build business context[/dim]")
            return
        
        business_data = insights.get("business_insights", {})
        
        # Show optimization suggestions
        suggestions = business_data.get("optimization_suggestions", [])
        if suggestions:
            console.print("\n[bold blue]💡 Business Optimization Suggestions:[/bold blue]")
            for suggestion in suggestions[:3]:  # Show top 3
                priority_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}.get(suggestion.get("priority", "medium"), "white")
                console.print(f"[{priority_color}]• {suggestion.get('title', 'Unknown')}[/{priority_color}]")
                console.print(f"  {suggestion.get('description', '')}")
                if suggestion.get('action'):
                    console.print(f"  [dim]Action: {suggestion['action']}[/dim]")
                console.print()
        
        # Show goal progress
        goal_progress = business_data.get("goal_progress", [])
        if goal_progress:
            console.print("[bold blue]🎯 Goal Progress:[/bold blue]")
            for goal in goal_progress[:3]:  # Show top 3
                progress = goal.get("progress", 0) * 100
                status = goal.get("status", "unknown")
                status_color = {"completed": "green", "on_track": "blue", "at_risk": "yellow", "overdue": "red"}.get(status, "white")
                console.print(f"[{status_color}]• {goal.get('title', 'Unknown')} ({progress:.0f}%)[/{status_color}]")
                console.print(f"  Priority: {goal.get('priority', 'unknown').title()}")
                console.print()
        
        # Show context summary
        context = business_data.get("context_summary", {})
        if context.get("company"):
            company = context["company"]
            console.print("[bold blue]🏢 Company Context:[/bold blue]")
            console.print(f"• Stage: {company.get('stage', 'unknown').title()}")
            console.print(f"• Industry: {company.get('industry', 'unknown').title()}")
            console.print(f"• Team Size: {company.get('team_size', 'unknown')}")
            console.print()
        
        # Show active departments
        departments = business_data.get("active_departments", {})
        if departments:
            console.print("[bold blue]🏛️ Active Departments:[/bold blue]")
            for dept_id, dept_info in departments.items():
                console.print(f"• {dept_info.get('name', dept_id)}: {dept_info.get('active_agents', 0)} agents")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error getting business insights: {str(e)}[/red]")


async def show_departments(jarvis: Jarvis):
    """Show all active departments."""
    try:
        departments = await jarvis.list_departments()
        
        if not departments:
            console.print("[yellow]No active departments found.[/yellow]")
            console.print("[dim]Departments will be created automatically as you build complex workflows[/dim]")
            return
        
        table = Table(title="Active Departments")
        table.add_column("Name", style="green")
        table.add_column("Status", style="blue")
        table.add_column("Agents", style="cyan")
        table.add_column("Last Activity", style="yellow")
        
        for dept in departments:
            status_color = {"active": "green", "coordinating": "blue", "paused": "yellow", "error": "red"}.get(dept.get("status", "unknown"), "white")
            table.add_row(
                dept.get("name", "Unknown"),
                f"[{status_color}]{dept.get('status', 'unknown').title()}[/{status_color}]",
                str(dept.get("agent_count", 0)),
                dept.get("last_activity", "Unknown")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error getting departments: {str(e)}[/red]")


async def show_business_context(jarvis: Jarvis, session_id: str):
    """Show detailed business context."""
    console.print("[bold blue]📊 Business Context Management[/bold blue]\n")
    console.print("This feature allows you to set company profile, metrics, and goals.")
    console.print("Currently showing available context...\n")
    
    try:
        insights = await jarvis.get_business_insights(session_id)
        
        if "error" not in insights:
            business_data = insights.get("business_insights", {})
            context = business_data.get("context_summary", {})
            
            if context.get("has_profile"):
                console.print("[green]✅ Company profile configured[/green]")
            else:
                console.print("[yellow]⭕ Company profile not set[/yellow]")
                
            if context.get("has_metrics"):
                console.print("[green]✅ Business metrics tracked[/green]")
            else:
                console.print("[yellow]⭕ Business metrics not set[/yellow]")
                
            if context.get("goal_count", 0) > 0:
                console.print(f"[green]✅ {context['goal_count']} business goals defined[/green]")
            else:
                console.print("[yellow]⭕ No business goals set[/yellow]")
        else:
            console.print("[yellow]Business context not yet available[/yellow]")
        
        console.print("\n[dim]Future versions will allow interactive business context setup[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error accessing business context: {str(e)}[/red]")


async def display_branding_result(result: Dict[str, Any]):
    """Display branding agent result in a user-friendly format."""
    status = result.get('status', 'unknown')
    
    if status == 'success':
        # Check if this includes market research
        analysis_type = result.get('analysis_type', 'branding_only')
        market_research = result.get('market_research', {})
        
        if analysis_type == 'branding_and_market_research' and market_research:
            # Show comprehensive results including market research
            console.print("[bold green]✅ Brand and Market Research Completed![/bold green]\n")
            
            # Show branding assets
            brand_name = result.get('brand_name', 'N/A')
            if brand_name and brand_name != 'N/A':
                console.print(f"[bold magenta]🎨 Brand Name:[/bold magenta] {brand_name}")
            
            # Show market research summary
            console.print(f"\n[bold blue]📊 Market Research Summary:[/bold blue]")
            
            # Market size
            market_size = market_research.get('market_size', {})
            if market_size:
                console.print(f"  📈 Total Market Size: {market_size.get('total_market_size', 'N/A')}")
                console.print(f"  🎯 Addressable Market: {market_size.get('addressable_market', 'N/A')}")
                console.print(f"  📈 Growth Rate: {market_size.get('growth_rate', 'N/A')}")
            
            # Competitive landscape
            competitive = market_research.get('competitive_landscape', {})
            if competitive:
                competitors = competitive.get('major_competitors', [])
                console.print(f"  🏢 Major Competitors: {len(competitors)} identified")
                console.print(f"  ⚔️ Competitive Intensity: {competitive.get('competitive_intensity', 'N/A')}")
            
            # Opportunity assessment
            opportunity = market_research.get('opportunity_assessment', {})
            if opportunity:
                console.print(f"  💡 Market Opportunity: {opportunity.get('market_opportunity', 'N/A')}")
                console.print(f"  🎯 Competitive Advantage: {opportunity.get('competitive_advantage', 'N/A')}")
            
            # Pricing analysis
            pricing = market_research.get('pricing_analysis', {})
            if pricing:
                console.print(f"  💰 Recommended Pricing: {pricing.get('recommended_pricing', 'N/A')}")
            
            # Show detailed market research
            console.print(f"\n[bold yellow]📋 Detailed Market Research:[/bold yellow]")
            console.print("• Market segmentation and target customers")
            console.print("• Competitive landscape analysis")
            console.print("• Pricing strategy recommendations")
            console.print("• Geographic market assessment")
            console.print("• Trends and future forecasts")
            
        else:
            # Show branding assets only
            console.print("[bold green]✅ Brand Created Successfully![/bold green]\n")
            
            # Brand name
            brand_name = result.get('brand_name', 'N/A')
            if brand_name and brand_name != 'N/A':
                console.print(f"[bold magenta]🎨 Brand Name:[/bold magenta] {brand_name}")
            
            # Logo prompt
            logo_prompt = result.get('logo_prompt', '')
            if logo_prompt:
                console.print(f"\n[bold blue]🎭 Logo Design Prompt:[/bold blue]")
                console.print(f"{logo_prompt}")
            
            # Color palette
            color_palette = result.get('color_palette', [])
            if color_palette:
                console.print(f"\n[bold yellow]🎨 Color Palette:[/bold yellow]")
                for i, color in enumerate(color_palette, 1):
                    console.print(f"  {i}. {color}")
            
            # Domain suggestions
            domain_suggestions = result.get('domain_suggestions', [])
            if domain_suggestions:
                console.print(f"\n[bold cyan]🌐 Domain Suggestions:[/bold cyan]")
                for domain in domain_suggestions[:5]:  # Show top 5
                    console.print(f"  • {domain}")
            
            # Logo generation results - check multiple possible locations for logo data
            logo_generation_success = False
            logo_images = []
            logo_urls = []
            
            # Check if logo generation data exists in response
            response_data = result.get('response', result)  # Try nested response first, fallback to result
            
            if response_data.get('logo_generation_success'):
                logo_generation_success = True
                logo_images = response_data.get('logo_images', [])
                # Extract URLs from logo_images
                logo_urls = [img.get('image_url') for img in logo_images if isinstance(img, dict) and img.get('image_url')]
            
            # Also check for legacy logo_generation structure
            legacy_logo_gen = result.get('logo_generation', {})
            if legacy_logo_gen.get('attempted'):
                if legacy_logo_gen.get('success'):
                    logo_generation_success = True
                    logo_urls.extend(result.get('logo_urls', []))
                    logo_images.extend(legacy_logo_gen.get('images', []))
            
            # Display logo generation results if we found any
            if logo_generation_success or logo_images or logo_urls:
                console.print(f"\n[bold magenta]🖼️ Logo Generation Results:[/bold magenta]")
                
                if logo_generation_success:
                    console.print("[green]✅ Logo generation successful![/green]")
                    
                    # Display image URLs
                    if logo_urls:
                        console.print(f"\n[bold blue]📸 Generated Logo Images:[/bold blue]")
                        for i, url in enumerate(logo_urls, 1):
                            if url:  # Only show non-empty URLs
                                console.print(f"  {i}. {url}")
                    
                    # Display logo details
                    if logo_images:
                        console.print(f"\n[bold cyan]🎨 Logo Details:[/bold cyan]")
                        for i, img in enumerate(logo_images, 1):
                            if isinstance(img, dict):
                                filename = img.get('filename', f'logo_{i}')
                                dimensions = img.get('dimensions', '1024x1024')
                                local_path = img.get('local_path', '')
                                
                                console.print(f"  • {filename} ({dimensions})")
                                if local_path:
                                    console.print(f"    📁 Saved to: {local_path}")
                else:
                    console.print("[red]❌ Logo generation failed[/red]")
                    
                    # Show error if available
                    error = response_data.get('logo_generation_error') or legacy_logo_gen.get('error')
                    if error:
                        console.print(f"[red]Error: {error}[/red]")
                    
                    # Show enhanced prompt that can be used elsewhere
                    enhanced_prompt = response_data.get('logo_generation_result', {}).get('enhanced_prompt', '')
                    if enhanced_prompt:
                        console.print(f"\n[bold blue]🎨 Enhanced Logo Prompt (for other AI tools):[/bold blue]")
                        console.print(f"{enhanced_prompt}")
                    
                    # Show suggestions if available
                    suggestions = response_data.get('logo_generation_result', {}).get('suggestions', [])
                    if suggestions:
                        console.print(f"\n[yellow]💡 Suggestions:[/yellow]")
                        for suggestion in suggestions:
                            console.print(f"  • {suggestion}")
        
        # Orchestration metadata
        orchestration = result.get('orchestration', {})
        if orchestration:
            intent_category = orchestration.get('intent_category', 'unknown')
            confidence = orchestration.get('confidence', 'unknown')
            console.print(f"\n[dim]Intent Category: {intent_category} (Confidence: {confidence})[/dim]")
        
        # Next steps
        if analysis_type == 'branding_and_market_research':
            console.print("\n[bold green]💡 What's next?[/bold green]")
            console.print("• Review detailed market research for strategic decisions")
            console.print("• Use branding assets for visual identity")
            console.print("• Develop business strategy based on market insights")
            console.print("• Consider competitive positioning opportunities")
        else:
            console.print("\n[bold green]💡 What's next?[/bold green]")
            console.print("• Use the logo prompt with DALL·E or Midjourney")
            console.print("• Check domain availability for the suggestions")
            console.print("• Refine your brand with additional details")
            console.print("• Request market research with 'research the market'")
        
    elif status == 'not_supported':
        console.print("[yellow]⚠️ This request doesn't seem to be branding-related.[/yellow]")
        console.print("Try describing your business idea or brand requirements.")
        
    elif status == 'error':
        error_msg = result.get('message', 'Unknown error occurred')
        console.print(f"[red]❌ Branding failed: {error_msg}[/red]")
        console.print("Try rephrasing your request with more details about your business.")
        
    else:
        console.print(f"[yellow]Status: {status}[/yellow]")
    
    console.print()


async def branding_demo_mode(orchestrator: BrandingOrchestrator, session_id: str):
    """Demo mode for branding agent."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]🎨 Branding Agent Demo[/bold blue]\n\n"
        "Experience AI-powered brand creation with multiple examples.\n"
        "Watch how the agent understands business ideas and generates\n"
        "complete brand identities with names, logos, and colors.",
        title="Branding Demo Mode",
        border_style="blue"
    ))
    
    # Demo examples
    demo_examples = [
        {
            "business": "Eco-friendly coffee shop for professionals",
            "description": "Sustainable coffee for busy professionals"
        },
        {
            "business": "Tech startup building AI tools for small businesses",
            "description": "AI automation platform for SMBs"
        },
        {
            "business": "Artisanal pen company using recycled materials",
            "description": "Premium writing instruments with eco-conscious design"
        }
    ]
    
    console.print("\n[bold yellow]Demo Examples:[/bold yellow]")
    for i, example in enumerate(demo_examples, 1):
        console.print(f"{i}. {example['business']}")
    
    console.print("\n[dim]Let's run through these examples automatically...[/dim]")
    console.input("\n[dim]Press Enter to start the demo...[/dim]")
    
    for i, example in enumerate(demo_examples, 1):
        console.print(f"\n[bold green]Demo {i}: {example['business']}[/bold green]")
        console.print(f"[dim]{example['description']}[/dim]")
        
        # Process the request
        result = await orchestrator.process_request(
            f"I need a brand name and logo for my {example['business']}",
            f"{session_id}_demo_{i}"
        )
        
        # Display results
        await display_branding_result(result)
        
        if i < len(demo_examples):
            console.input("\n[dim]Press Enter for next demo...[/dim]")
    
    # Show educational summary
    console.print(Panel(
        "[bold green]🎓 Demo Summary:[/bold green]\n\n"
        "You've seen how the Branding Agent:\n"
        "• [bold]Understands Context:[/bold] Parses business descriptions intelligently\n"
        "• [bold]Generates Names:[/bold] Creates memorable, relevant brand names\n"
        "• [bold]Designs Logos:[/bold] Provides detailed logo design prompts\n"
        "• [bold]Selects Colors:[/bold] Curates cohesive color palettes\n"
        "• [bold]Suggests Domains:[/bold] Offers relevant domain name options\n\n"
        "💡 [bold]Key Feature:[/bold] Works with any business idea, from coffee shops to tech startups!",
        style="green"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def display_jarvis_result(result: Dict[str, Any]):
    """Display Jarvis orchestrator result in a user-friendly format."""
    # First display the normal result
    await display_result(result)
    
    # Then show Jarvis-specific metadata
    jarvis_metadata = result.get('jarvis_metadata', {})
    if jarvis_metadata:
        console.print("[bold blue]🧠 Jarvis Analysis:[/bold blue]")
        
        processing_time = jarvis_metadata.get('processing_time_ms', 0)
        console.print(f"• Processing time: {processing_time}ms")
        
        # Show business intent analysis
        business_intent = jarvis_metadata.get('business_intent', {})
        if business_intent:
            category = business_intent.get('category', 'unknown')
            confidence = business_intent.get('confidence', 0)
            complexity = business_intent.get('complexity', 'unknown')
            timeline = business_intent.get('estimated_timeline', 'unknown')
            
            # Color code by category
            category_colors = {
                "GROW_REVENUE": "green",
                "REDUCE_COSTS": "blue",
                "IMPROVE_EFFICIENCY": "yellow",
                "LAUNCH_PRODUCT": "magenta",
                "CUSTOM_AUTOMATION": "cyan"
            }
            category_color = category_colors.get(category, "white")
            
            console.print(f"• 🎯 Intent: [{category_color}]{category.replace('_', ' ').title()}[/{category_color}] ({confidence:.0%} confidence)")
            console.print(f"• 📊 Complexity: {complexity.title()} ({timeline})")
        
        if jarvis_metadata.get('business_context_available'):
            console.print("• ✅ Business context applied")
        else:
            console.print("• ⭕ Business context not available")
        
        active_depts = jarvis_metadata.get('active_departments', [])
        if active_depts:
            console.print(f"• 🏛️ Active departments: {len(active_depts)}")
        
        if jarvis_metadata.get('error_handled_by_jarvis'):
            console.print("• 🛡️ Error handled gracefully by Jarvis")
        
        console.print()
    
    # Show business guidance if available
    business_guidance = result.get('business_guidance', {})
    if business_guidance and not business_guidance.get('note'):
        console.print("[bold blue]📋 Business Guidance:[/bold blue]")
        
        intent_category = business_guidance.get('intent_category', '')
        if intent_category:
            console.print(f"• Category: {intent_category.replace('_', ' ').title()}")
        
        suggested_depts = business_guidance.get('suggested_departments', [])
        if suggested_depts:
            console.print(f"• Suggested departments: {', '.join(suggested_depts)}")
        
        key_metrics = business_guidance.get('key_metrics', [])
        if key_metrics:
            console.print(f"• Key metrics to track: {', '.join(key_metrics[:3])}")
        
        reasoning = business_guidance.get('reasoning', '')
        if reasoning:
            console.print(f"• Strategic purpose: {reasoning}")
        
        console.print()


async def display_market_research_result(result: Dict[str, Any]):
    """Display comprehensive market research analysis results."""
    if result.get("status") == "error":
        console.print(f"[red]❌ Market research failed: {result.get('error', 'Unknown error')}[/red]")
        return
    
    if result.get("status") != "completed":
        console.print(f"[yellow]⚠️ Market research status: {result.get('status', 'unknown')}[/yellow]")
        return
    
    research_data = result.get("result", {})
    if not research_data:
        console.print("[yellow]⚠️ No market research data available[/yellow]")
        return
    
    # Check if research was successful
    if not research_data.get("market_research_success"):
        error_msg = research_data.get("market_research_error", "Unknown error")
        console.print(f"[red]❌ Market research failed: {error_msg}[/red]")
        return
    
    # Display executive summary
    console.print("[bold green]📊 MARKET RESEARCH ANALYSIS COMPLETE[/bold green]\n")
    
    # Key metrics at the top
    opportunity_score = research_data.get("market_opportunity_score", 0)
    market_size = research_data.get("market_size", "Not available")
    competitors_count = len(research_data.get("key_competitors", []))
    
    console.print(f"[bold]🎯 Market Opportunity Score:[/bold] [bold green]{opportunity_score}/100[/bold green]")
    console.print(f"[bold]💰 Market Size:[/bold] {market_size}")
    console.print(f"[bold]🏢 Key Competitors Identified:[/bold] {competitors_count}")
    
    # Display key findings
    key_findings = research_data.get("key_findings", [])
    if key_findings:
        console.print(f"\n[bold]🔍 KEY FINDINGS:[/bold]")
        for i, finding in enumerate(key_findings[:3], 1):
            console.print(f"   {i}. {finding}")
    
    # Display competitors
    key_competitors = research_data.get("key_competitors", [])
    if key_competitors:
        console.print(f"\n[bold]🏢 TOP COMPETITORS:[/bold]")
        for i, competitor in enumerate(key_competitors[:5], 1):
            # Handle both string and dict formats
            if isinstance(competitor, str):
                console.print(f"   {i}. {competitor}")
            else:
                console.print(f"   {i}. {competitor}")
    
    # Display market trends
    market_trends = research_data.get("market_trends", [])
    if market_trends:
        console.print(f"\n[bold]📈 MARKET TRENDS:[/bold]")
        for i, trend in enumerate(market_trends[:3], 1):
            # Clean up trend text
            clean_trend = str(trend).strip()
            if len(clean_trend) > 5:  # Skip very short or empty trends
                console.print(f"   {i}. {clean_trend}")
    
    # Display target personas  
    target_personas = research_data.get("target_personas", [])
    if target_personas:
        console.print(f"\n[bold]👥 TARGET PERSONAS:[/bold]")
        for i, persona in enumerate(target_personas[:3], 1):
            # Handle both string and dict formats
            clean_persona = str(persona).strip()
            if len(clean_persona) > 5:  # Skip very short or empty personas
                console.print(f"   {i}. {clean_persona}")
    
    # Show full research availability
    research_result = research_data.get("market_research_result")
    if research_result:
        console.print(f"\n[dim]📋 Comprehensive analysis includes: market landscape, competitive intelligence, customer insights, trend analysis, and strategic recommendations[/dim]")
        console.print(f"[dim]📁 Full report saved to market research reports directory[/dim]")
    
    console.print(f"\n[bold green]✅ Market research completed successfully![/bold green]")


async def display_universal_result(result: Dict[str, Any]):
    """Display Universal Orchestrator result with routing information."""
    if result.get("status") == "error":
        console.print(f"[red]❌ Error: {result.get('error_message', 'Unknown error')}[/red]")
        return
    
    # Show routing information
    routing_info = result.get("routing_info", {})
    if routing_info:
        orchestrator = routing_info.get("orchestrator", "unknown")
        intent = routing_info.get("intent", "unknown")
        confidence = routing_info.get("confidence", 0)
        reasoning = routing_info.get("reasoning", "")
        
        # Map orchestrator types to display names and emojis
        orchestrator_display = {
            "branding": ("🎨 Branding Specialist", "magenta"),
            "market_research": ("📊 Market Research", "green"),
            "jarvis_business": ("🧠 Business Strategy", "blue"),
            "heyjarvis_technical": ("⚙️ Technical Automation", "cyan")
        }
        
        display_name, color = orchestrator_display.get(orchestrator, ("🤖 AI Assistant", "white"))
        
        console.print(f"\n[bold {color}]🎯 Routed to: {display_name}[/bold {color}]")
        console.print(f"[dim]Intent: {intent} (Confidence: {confidence:.1%})[/dim]")
        if reasoning:
            console.print(f"[dim]Reasoning: {reasoning}[/dim]")
        console.print()
    
    # Display the actual response from the orchestrator
    orchestrator_response = result.get("response", {})
    
    # Route to appropriate display function based on orchestrator type
    if routing_info.get("orchestrator") == "branding":
        await display_branding_result(orchestrator_response)
    elif routing_info.get("orchestrator") == "market_research":
        await display_market_research_result(orchestrator_response)
    elif routing_info.get("orchestrator") == "jarvis_business":
        await display_jarvis_result(orchestrator_response)
    else:
        # Default to technical result display
        await display_result(orchestrator_response)
    
    # Show metadata
    metadata = result.get("metadata", {})
    if metadata:
        processing_time = metadata.get("processing_time_ms", 0)
        timestamp = metadata.get("timestamp", "")
        
        console.print(f"[dim]⏱️ Processing time: {processing_time}ms | Session: {metadata.get('session_id', 'unknown')}[/dim]")
        console.print()


async def is_technical_request(user_input: str) -> bool:
    """Determine if a request is technical (agent builder) vs business (Jarvis)."""
    technical_keywords = [
        'create agent', 'build agent', 'agent that', 'automation for',
        'monitor', 'sync', 'backup', 'email agent', 'file agent',
        'integration', 'webhook', 'api'
    ]
    
    business_keywords = [
        'grow sales', 'increase revenue', 'reduce costs', 'improve efficiency',
        'sales department', 'marketing', 'hire', 'scale', 'business',
        'profit', 'customers', 'leads', 'pipeline', 'department', 'for sales'
    ]
    
    user_lower = user_input.lower()
    
    # Check for business keywords first (higher priority)
    if any(keyword in user_lower for keyword in business_keywords):
        return False  # Business request
    
    # Check for technical keywords, but be more specific
    technical_score = sum(1 for keyword in technical_keywords if keyword in user_lower)
    
    # If we have strong technical indicators and no business context, treat as technical
    if technical_score >= 2 or ('create agent' in user_lower or 'build agent' in user_lower):
        return True  # Technical request
    elif technical_score == 1 and 'technical' in user_lower and 'business' not in user_lower:
        return True  # Single technical keyword with explicit "technical"
    
    # Default to business request in Jarvis mode
    return False


async def jarvis_demo_sales_growth(orchestrator: HeyJarvisOrchestrator):
    """Demo: Jarvis Sales Growth - business department coordination."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]💼 Jarvis Demo: Sales Growth[/bold blue]\n\n"
        "Experience how Jarvis transforms business requests into coordinated\n"
        "department actions with real-time metrics and insights.\n\n"
        "This demo shows business-level orchestration vs technical agent creation.",
        title="Business Automation Demo",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]📈 Business Scenario:[/bold yellow]")
    console.print("Company wants to grow revenue 30% this quarter")
    console.print("Current revenue: $2.5M → Target: $3.25M")
    console.print("Timeline: Q4 2024 (3 months remaining)")
    
    console.print("\n[dim]Let's see how Jarvis handles this business challenge...[/dim]")
    console.input("\n[dim]Press Enter to start the demo...[/dim]")
    
    # Simulate user business request
    business_request = "I need to grow revenue 30% this quarter"
    console.print(f"\n[bold green]You:[/bold green] {business_request}")
    
    # Show Jarvis analyzing business context
    console.print(Panel(
        "🧠 [bold]Jarvis is analyzing your business request:[/bold]\n\n"
        "• Identifying intent: Revenue growth (30% increase)\n"
        "• Business context: Quarterly target, $750K additional revenue needed\n"
        "• Department assessment: Sales capacity and current pipeline\n"
        "• Strategic planning: Multi-agent coordination required",
        style="dim yellow"
    ))
    
    # Simulate progress with business context
    console.print("\n[bold magenta]🧠 Jarvis:[/bold magenta] I'll activate the Sales department to achieve your 30% revenue growth target...\n")
    
    # Progress updates with business context
    progress_updates = [
        (20, "🔍 Analyzing current sales pipeline ($2.5M revenue)"),
        (35, "🎯 Identifying growth opportunities and bottlenecks"),
        (50, "🏢 Activating Sales Department with 4 specialized agents"),
        (65, "📊 Setting up revenue tracking and KPI monitoring"),
        (80, "🤝 Coordinating lead generation and pipeline optimization"),
        (95, "✅ Sales Department operational with 30% growth target"),
        (100, "🚀 Real-time revenue tracking activated")
    ]
    
    for progress, message in progress_updates:
        console.print(f"📊 Progress: {progress}% - {message}")
        await asyncio.sleep(0.8)
    
    # Show department activation results
    console.print("\n[bold green]✅ Sales Department Activated![/bold green]")
    
    # Create a metrics table
    metrics_table = Table(title="Live Business Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Current", style="white")
    metrics_table.add_column("Target", style="green")
    metrics_table.add_column("Progress", style="yellow")
    
    metrics_table.add_row("Revenue", "$2.5M", "$3.25M", "🎯 Target Set")
    metrics_table.add_row("Lead Pipeline", "150 leads", "250 leads", "📈 +67% needed")
    metrics_table.add_row("Conversion Rate", "12%", "15%", "🔄 Optimizing")
    metrics_table.add_row("Avg Deal Size", "$16.7K", "$20K", "💰 Upselling")
    
    console.print(metrics_table)
    
    # Show activated agents
    console.print(Panel(
        "[bold green]🤖 Sales Department Agents Deployed:[/bold green]\n\n"
        "• [bold]Lead Scanner Agent[/bold] - Identifying high-value prospects\n"
        "• [bold]Outreach Composer Agent[/bold] - Personalizing sales communications\n"
        "• [bold]Meeting Scheduler Agent[/bold] - Optimizing demo scheduling\n"
        "• [bold]Pipeline Tracker Agent[/bold] - Monitoring deal progression\n\n"
        "💡 [bold]Coordination:[/bold] All agents share data and optimize together",
        style="green"
    ))
    
    # Simulate live metrics updates
    console.print("\n[bold yellow]📊 Simulating live metrics (5 seconds)...[/bold yellow]")
    
    live_updates = [
        "💼 Lead Scanner found 8 qualified prospects (Score: 8.5/10)",
        "📧 Outreach Composer sent 15 personalized emails (18% response rate)", 
        "📅 Meeting Scheduler booked 3 demos for this week",
        "💰 Pipeline Tracker: $45K in new opportunities added",
        "🎯 Revenue projection: +$125K this month (on track for 30% growth)"
    ]
    
    for update in live_updates:
        await asyncio.sleep(1)
        console.print(f"  {update}")
    
    # Show projected impact
    console.print(Panel(
        "[bold green]📈 Projected Business Impact:[/bold green]\n\n"
        "• [bold]Revenue Growth:[/bold] On track for 32% increase ($800K additional)\n"
        "• [bold]Timeline:[/bold] Target achievable 2 weeks ahead of schedule\n"
        "• [bold]Efficiency:[/bold] 40% improvement in sales process automation\n"
        "• [bold]ROI:[/bold] $800K revenue / $50K automation cost = 1600% ROI\n\n"
        "🚀 [bold]Key Difference:[/bold] Jarvis coordinates business outcomes,\n"
        "not just individual agent tasks!",
        style="green"
    ))
    
    # Educational comparison
    console.print(Panel(
        "[bold blue]🎭 Demo Comparison: Jarvis vs Traditional Agents[/bold blue]\n\n"
        "[bold yellow]Traditional Approach:[/bold yellow]\n"
        "• Create individual agents one by one\n"
        "• Manual coordination between agents\n"
        "• Technical focus: 'Create a lead generation agent'\n"
        "• Limited business context awareness\n\n"
        "[bold magenta]Jarvis Approach:[/bold magenta]\n"
        "• Business goal: 'Grow revenue 30%'\n"
        "• Automatic department activation\n"
        "• Coordinated multi-agent strategy\n"
        "• Real-time business metrics tracking\n"
        "• Strategic business outcome focus",
        style="dim"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def jarvis_demo_cost_reduction(orchestrator: HeyJarvisOrchestrator):
    """Demo: Jarvis Cost Reduction - operational efficiency."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]💰 Jarvis Demo: Cost Reduction[/bold blue]\n\n"
        "See how Jarvis identifies cost-saving opportunities across\n"
        "multiple departments and implements coordinated efficiency solutions.\n\n"
        "This demo showcases cross-department optimization.",
        title="Operational Efficiency Demo", 
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]💸 Business Challenge:[/bold yellow]")
    console.print("Operational costs too high: $500K/month")
    console.print("Target: Reduce costs by 20% ($100K/month savings)")
    console.print("Focus: Automation and process optimization")
    
    console.print("\n[dim]Let's see Jarvis analyze and optimize operational costs...[/dim]")
    console.input("\n[dim]Press Enter to start cost analysis...[/dim]")
    
    # Simulate business request
    cost_request = "Reduce our operational costs by 20% through automation"
    console.print(f"\n[bold green]You:[/bold green] {cost_request}")
    
    # Show Jarvis cost analysis
    console.print(Panel(
        "🧠 [bold]Jarvis Cost Analysis in Progress:[/bold]\n\n"
        "• Scanning operational expenses across all departments\n"
        "• Identifying automation opportunities\n"
        "• Calculating potential savings and ROI\n"
        "• Planning cross-department efficiency improvements",
        style="dim yellow"
    ))
    
    console.print("\n[bold magenta]🧠 Jarvis:[/bold magenta] I've identified cost reduction opportunities across multiple departments...\n")
    
    # Cost analysis progress
    analysis_steps = [
        (15, "📊 Analyzing current operational costs ($500K/month)"),
        (30, "🔍 Identifying inefficiencies in manual processes"),
        (45, "🤖 Planning automation for repetitive tasks"),
        (60, "🏢 Activating Operations Department for efficiency"),
        (75, "📈 Coordinating with HR and IT for process optimization"),
        (90, "💰 Calculating projected savings and implementation timeline"),
        (100, "✅ Cost reduction strategy activated")
    ]
    
    for progress, message in analysis_steps:
        console.print(f"📊 Progress: {progress}% - {message}")
        await asyncio.sleep(0.7)
    
    # Show cost breakdown analysis
    cost_table = Table(title="Cost Reduction Analysis")
    cost_table.add_column("Department", style="cyan")
    cost_table.add_column("Current Cost", style="red")
    cost_table.add_column("Automation Savings", style="green")
    cost_table.add_column("Efficiency Gain", style="yellow")
    
    cost_table.add_row("HR Operations", "$80K/month", "$24K/month", "30% faster hiring")
    cost_table.add_row("Customer Service", "$120K/month", "$36K/month", "50% fewer manual tickets")
    cost_table.add_row("Data Processing", "$60K/month", "$24K/month", "80% automated reports")
    cost_table.add_row("Administrative", "$90K/month", "$18K/month", "40% less manual work")
    cost_table.add_row("[bold]Total", "[bold]$350K/month", "[bold]$102K/month", "[bold]20.4% reduction")
    
    console.print(cost_table)
    
    # Show department coordination
    console.print(Panel(
        "[bold green]🏢 Multi-Department Coordination:[/bold green]\n\n"
        "• [bold]Operations Dept:[/bold] Process automation and workflow optimization\n"
        "• [bold]HR Dept:[/bold] Automated recruiting and onboarding systems\n"
        "• [bold]IT Dept:[/bold] Infrastructure optimization and tool consolidation\n"
        "• [bold]Finance Dept:[/bold] Automated reporting and expense tracking\n\n"
        "💡 [bold]Smart Coordination:[/bold] Departments share data and optimize together",
        style="green"
    ))
    
    # Simulate implementation progress
    console.print("\n[bold yellow]⚙️  Implementing cost reduction measures...[/bold yellow]")
    
    implementation_updates = [
        "🤖 HR: Automated candidate screening (saves 15 hours/week)",
        "📞 Customer Service: Chatbot handling 60% of routine inquiries",
        "📊 Finance: Automated expense reporting (saves 8 hours/week)",
        "💻 IT: Consolidated 5 tools into 1 platform (saves $12K/month)",
        "📈 Operations: Workflow automation reduces processing time by 45%"
    ]
    
    for update in implementation_updates:
        await asyncio.sleep(1)
        console.print(f"  {update}")
    
    # Show savings projection
    savings_table = Table(title="Projected Monthly Savings")
    savings_table.add_column("Category", style="cyan")
    savings_table.add_column("Savings", style="green")
    savings_table.add_column("Implementation", style="yellow")
    
    savings_table.add_row("Labor Cost Reduction", "$78K", "✅ Active")
    savings_table.add_row("Tool Consolidation", "$15K", "✅ Active") 
    savings_table.add_row("Process Efficiency", "$9K", "✅ Active")
    savings_table.add_row("[bold]Total Monthly Savings", "[bold]$102K", "[bold]20.4% reduction")
    
    console.print(savings_table)
    
    # Show business impact
    console.print(Panel(
        "[bold green]💰 Business Impact Summary:[/bold green]\n\n"
        "• [bold]Cost Reduction:[/bold] $102K/month ($1.2M annually)\n"
        "• [bold]Target Achievement:[/bold] 102% of 20% reduction goal\n"
        "• [bold]Efficiency Gains:[/bold] 40% improvement in operational speed\n"
        "• [bold]Employee Satisfaction:[/bold] Less repetitive work, more strategic focus\n"
        "• [bold]ROI Timeline:[/bold] Implementation cost recovered in 2 months\n\n"
        "🎯 [bold]Strategic Value:[/bold] Sustainable, scalable cost optimization!",
        style="green"
    ))
    
    # Educational insights
    console.print(Panel(
        "[bold blue]🎓 Key Learning: Cross-Department Optimization[/bold blue]\n\n"
        "[bold]Traditional Approach:[/bold]\n"
        "• Department silos optimize independently\n"
        "• Limited visibility into cross-department impacts\n"
        "• Suboptimal overall results\n\n"
        "[bold]Jarvis Approach:[/bold]\n"
        "• Holistic view of entire organization\n"
        "• Coordinated optimization across departments\n"
        "• Synergistic effects amplify savings\n"
        "• Sustainable long-term efficiency gains",
        style="dim"
    ))
    
    console.input("\n[dim]Press Enter to continue...[/dim]")


async def business_demo_mode(jarvis: Jarvis, session_id: str):
    """Business demo mode showing sales growth scenario."""
    console.clear()
    
    console.print(Panel(
        "[bold blue]💼 Business Demo: Sales Growth[/bold blue]\n\n"
        "Experience how Jarvis coordinates departments to achieve business goals.\n"
        "Demo scenario: 'Grow sales by 30%' → Sales activation → Show metrics",
        title="Jarvis Business Demo",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]Demo Scenario:[/bold yellow] Your company wants to grow sales by 30% this quarter")
    console.print("[dim]Watch as Jarvis activates the Sales Department and coordinates multiple agents...[/dim]")
    
    console.input("\n[dim]Press Enter to start the demo...[/dim]")
    
    # Demo: "Grow sales by 30%" request
    demo_request = "Grow sales by 30% this quarter"
    console.print(f"\n[bold cyan]💼 Demo Request:[/bold cyan] {demo_request}")
    
    # Show Jarvis analyzing the request
    console.print("\n📊 Progress: 10% - 🧠 Jarvis analyzing business intent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 20% - 🎯 Intent identified: GROW_REVENUE")
    await asyncio.sleep(1)
    console.print("📊 Progress: 30% - 🏛️ Activating Sales Department...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 40% - 🤖 Initializing Lead Scanner Agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 50% - 📧 Initializing Outreach Composer Agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 60% - 📅 Initializing Meeting Scheduler Agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 70% - 📊 Initializing Pipeline Tracker Agent...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 80% - ⚙️ Configuring department coordination...")
    await asyncio.sleep(1)
    console.print("📊 Progress: 90% - 🚀 Sales Department operational!")
    await asyncio.sleep(1)
    console.print("📊 Progress: 100% - ✅ Business goal workflow activated!")
    
    # Display business KPI dashboard
    console.print("\n" + "="*60)
    console.print("[bold green]🎯 SALES DEPARTMENT ACTIVATED[/bold green]")
    console.print("="*60)
    
    # Show metrics updating
    metrics_table = Table(title="Live Business KPIs")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Current", style="yellow")
    metrics_table.add_column("Target", style="green")
    metrics_table.add_column("Progress", style="blue")
    
    metrics_table.add_row("Monthly Leads", "45", "100", "45%")
    metrics_table.add_row("Meetings Booked", "12", "20", "60%")
    metrics_table.add_row("Pipeline Value", "$125K", "$200K", "62%")
    metrics_table.add_row("Conversion Rate", "15%", "20%", "75%")
    
    console.print(metrics_table)
    
    console.print("\n[bold blue]🤖 Active Sales Agents:[/bold blue]")
    console.print("• 🔍 Lead Scanner Agent: Monitoring LinkedIn, Sales Navigator")
    console.print("• 📧 Outreach Composer Agent: Generating personalized emails")
    console.print("• 📅 Meeting Scheduler Agent: Coordinating calendars")
    console.print("• 📊 Pipeline Tracker Agent: Monitoring CRM, tracking deals")
    
    console.print("\n[bold green]📈 Projected Impact:[/bold green]")
    console.print("• Lead generation: +120% (estimated 25 new leads/week)")
    console.print("• Meeting booking: +85% (estimated 8 additional meetings/week)")
    console.print("• Pipeline velocity: +40% (faster deal progression)")
    console.print("• Overall sales growth: +30% (target achievement likely)")
    
    console.print("\n[bold yellow]⚡ Real-time Activities:[/bold yellow]")
    console.print("• Lead Scanner found 8 new qualified prospects")
    console.print("• Outreach Composer sent 15 personalized emails")
    console.print("• Meeting Scheduler booked 3 discovery calls")
    console.print("• Pipeline Tracker identified 2 at-risk deals")
    
    console.input("\n[dim]Press Enter to see department coordination...[/dim]")
    
    # Show department coordination
    console.print("\n[bold blue]🔄 Department Coordination in Action:[/bold blue]")
    console.print("1. 🔍 Lead Scanner → 📧 Outreach Composer: 'New qualified lead: TechCorp VP Engineering'")
    console.print("2. 📧 Outreach Composer → 📅 Meeting Scheduler: 'Positive response from TechCorp, needs meeting'")
    console.print("3. 📅 Meeting Scheduler → 📊 Pipeline Tracker: 'Demo scheduled for $50K opportunity'")
    console.print("4. 📊 Pipeline Tracker → 🔍 Lead Scanner: 'Focus on enterprise accounts like TechCorp'")
    
    console.print("\n[bold green]🎯 Business Impact Tracking:[/bold green]")
    console.print("• Automation time saved: 160 hours/month")
    console.print("• Cost per lead reduced: $150 → $85 (43% improvement)")
    console.print("• Sales cycle shortened: 65 → 45 days (31% faster)")
    console.print("• Team productivity increased: +75% effective selling time")
    
    console.input("\n[dim]Press Enter to continue...[/dim]")
    
    # Show next quarter projections
    console.print("\n[bold magenta]🔮 AI-Powered Forecasting:[/bold magenta]")
    console.print("Based on current agent performance and market conditions:")
    console.print("• Q1 sales target: $500K (90% confidence)")
    console.print("• Lead quality score: 8.5/10 (improving)")
    console.print("• Pipeline health: Excellent (low risk)")
    console.print("• Recommended actions: Scale outreach, hire 1 sales rep")
    
    console.print(Panel(
        "[bold green]🎉 Demo Complete![/bold green]\n\n"
        "This is the power of Jarvis:\n"
        "• [bold]Business Intent Understanding:[/bold] 'Grow sales by 30%' → Department activation\n"
        "• [bold]Autonomous Coordination:[/bold] 4 agents working together seamlessly\n"
        "• [bold]Real-time Metrics:[/bold] Live KPI tracking and business impact\n"
        "• [bold]Intelligent Forecasting:[/bold] AI-driven predictions and recommendations\n\n"
        "Ready to activate your own departments? Try: 'Reduce operational costs by 20%'",
        title="Jarvis Business Demo Summary",
        border_style="green"
    ))


async def concurrent_mode():
    """Concurrent persistent agent mode with enhanced capabilities."""
    console.print("[bold cyan]🚀 Concurrent Persistent Agent Mode[/bold cyan]")
    console.print("[dim]Enhanced Intelligence Layer with concurrent multi-agent execution[/dim]\n")
    
    try:
        # Initialize persistent system
        persistent_system = create_development_persistent_system()
        
        with console.status("[bold cyan]Initializing persistent agent system...") as status:
            status.update("[cyan]Starting message bus...")
            await asyncio.sleep(1)
            
            status.update("[cyan]Initializing agent pool...")
            await asyncio.sleep(1)
            
            status.update("[cyan]Starting persistent agents...")
            await persistent_system.start()
            
            status.update("[cyan]System ready!")
            await asyncio.sleep(0.5)
        
        console.print("✅ [green]Persistent system started successfully![/green]")
        
        # Initialize enhanced workflow brain
        config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'max_retries': 3,
            'enable_optimization': True
        }
        
        enhanced_brain = EnhancedWorkflowBrain(config, persistent_system)
        await enhanced_brain.initialize_orchestration()
        
        # Initialize advanced features
        template_manager = WorkflowTemplateManager()
        analytics_engine = PerformanceAnalyticsEngine()
        
        # Initialize intelligent workflow manager
        workflow_manager = IntelligentWorkflowManager(enhanced_brain, config)
        
        console.print("🧠 [green]Enhanced WorkflowBrain initialized![/green]")
        console.print("📊 [green]Advanced analytics enabled![/green]")
        console.print("🤖 [green]Intelligent Workflow Manager ready![/green]\n")
        
        # Display system status
        await _display_system_status(persistent_system, enhanced_brain, analytics_engine)
        
        # Main interaction loop with multi-prompt support
        session_id = str(uuid.uuid4())[:8]
        active_workflows: Dict[str, asyncio.Task] = {}
        workflow_context: Dict[str, Any] = {}
        
        console.print(f"[dim]Session ID: {session_id}[/dim]")
        console.print("[dim]💡 Commands: 'status', 'multi', 'suggest', 'analytics', 'health', or describe your business goal[/dim]")
        console.print("[dim]💡 Multi-prompt mode: Use 'multi' then enter multiple prompts (one per line, empty line to execute)[/dim]\n")
        
        while True:
            try:
                try:
                    user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
                except EOFError:
                    # Handle EOF gracefully - exit the loop
                    console.print("\n[yellow]EOF detected, exiting...[/yellow]")
                    break
                
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Shutting down concurrent system...[/yellow]")
                    # Cancel all active workflows
                    for workflow_id, task in active_workflows.items():
                        task.cancel()
                        console.print(f"[yellow]Cancelled workflow {workflow_id}[/yellow]")
                    break
                
                # Handle system commands
                elif user_input.lower() == 'status':
                    await _display_system_status(persistent_system, enhanced_brain, analytics_engine)
                    await _display_active_workflows(active_workflows)
                    continue
                    
                elif user_input.lower() == 'templates':
                    await _display_workflow_templates(template_manager)
                    continue
                    
                elif user_input.lower() == 'analytics':
                    await _display_analytics_dashboard(analytics_engine, enhanced_brain)
                    continue
                    
                elif user_input.lower() == 'health':
                    await _display_health_dashboard(persistent_system)
                    continue
                
                # Handle multi-prompt mode
                elif user_input.lower() == 'multi':
                    prompts = await _collect_multi_prompts()
                    if prompts:
                        await _execute_multi_prompts(
                            prompts, enhanced_brain, template_manager, analytics_engine,
                            workflow_manager, session_id, active_workflows, workflow_context
                        )
                    continue
                
                # Handle intelligent suggestions
                elif user_input.lower() == 'suggest':
                    suggestions = await workflow_manager.suggest_next_workflows(workflow_context)
                    selected_prompt = await _display_workflow_suggestions(suggestions, workflow_manager)
                    if selected_prompt:
                        # Execute the selected suggestion as a new workflow
                        await _execute_single_workflow(
                            selected_prompt, enhanced_brain, template_manager, analytics_engine,
                            workflow_manager, session_id, active_workflows, workflow_context
                        )
                    continue
                    
                elif user_input.lower().startswith('cancel'):
                    workflow_id = user_input.split()[-1] if len(user_input.split()) > 1 else None
                    await _cancel_workflow(workflow_id, active_workflows)
                    continue
                
                # Process single workflow request
                await _execute_single_workflow(
                    user_input, enhanced_brain, template_manager, analytics_engine,
                    workflow_manager, session_id, active_workflows, workflow_context
                )
                
            except KeyboardInterrupt:
                console.print(f"\n[yellow]Interrupting active workflows...[/yellow]")
                for workflow_id, task in active_workflows.items():
                    task.cancel()
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
                logger.error(f"Error in concurrent mode: {e}", exc_info=True)
    
    except Exception as e:
        console.print(f"[red]Failed to start concurrent mode:[/red] {e}")
        logger.error(f"Concurrent mode startup failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        try:
            if 'persistent_system' in locals():
                await persistent_system.stop()
            console.print("[green]Concurrent system shutdown complete.[/green]")
        except Exception as e:
            console.print(f"[red]Error during shutdown:[/red] {e}")


async def _collect_multi_prompts() -> List[str]:
    """Collect multiple prompts from the user."""
    console.print("[bold cyan]Multi-Prompt Mode:[/bold cyan] Enter multiple prompts (one per line)")
    console.print("[dim]Press Enter on empty line to execute all prompts concurrently[/dim]\n")
    
    prompts = []
    while True:
        prompt = console.input(f"[cyan]Prompt {len(prompts) + 1}:[/cyan] ").strip()
        if not prompt:
            break
        prompts.append(prompt)
    
    if prompts:
        console.print(f"\n[green]Collected {len(prompts)} prompts for concurrent execution![/green]")
    
    return prompts


async def _execute_multi_prompts(
    prompts: List[str],
    enhanced_brain,
    template_manager,
    analytics_engine,
    workflow_manager,
    session_id: str,
    active_workflows: Dict[str, asyncio.Task],
    workflow_context: Dict[str, Any]
):
    """Execute multiple prompts concurrently."""
    console.print(f"[bold cyan]🚀 Executing {len(prompts)} workflows concurrently...[/bold cyan]\n")
    
    # Create tasks for all prompts
    tasks = []
    for i, prompt in enumerate(prompts):
        task = asyncio.create_task(
            _execute_workflow_with_tracking(
                prompt, enhanced_brain, template_manager, analytics_engine,
                workflow_manager, session_id, active_workflows, workflow_context, i + 1
            )
        )
        tasks.append(task)
    
    # Wait for all workflows to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Display completion summary
    successful = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - successful
    
    console.print(f"\n[bold green]Multi-Prompt Execution Complete![/bold green]")
    console.print(f"✅ Successful: {successful}")
    if failed > 0:
        console.print(f"❌ Failed: {failed}")
    
    # Generate intelligent suggestions based on results
    await _generate_follow_up_suggestions(
        workflow_manager, workflow_context, results,
        enhanced_brain, template_manager, analytics_engine, session_id, active_workflows
    )


async def _execute_single_workflow(
    user_input: str,
    enhanced_brain,
    template_manager,
    analytics_engine,
    workflow_manager,
    session_id: str,
    active_workflows: Dict[str, asyncio.Task],
    workflow_context: Dict[str, Any]
):
    """Execute a single workflow."""
    await _execute_workflow_with_tracking(
        user_input, enhanced_brain, template_manager, analytics_engine,
        workflow_manager, session_id, active_workflows, workflow_context, 1
    )


async def _execute_workflow_with_tracking(
    user_input: str,
    enhanced_brain,
    template_manager,
    analytics_engine,
    workflow_manager,
    session_id: str,
    active_workflows: Dict[str, asyncio.Task],
    workflow_context: Dict[str, Any],
    prompt_number: int = 1
):
    """Execute a workflow with full tracking and context management."""
    prefix = f"[{prompt_number}] " if prompt_number > 1 else ""
    
    try:
        console.print(f"\n{prefix}[bold cyan]🧠 Enhanced WorkflowBrain:[/bold cyan] Analyzing your request...\n")
        
        # Determine workflow type and recommend template
        workflow_type = _infer_workflow_type(user_input)
        recommended_template = await template_manager.recommend_template(
            workflow_type=workflow_type,
            user_requirements={'max_duration': 3600},  # 1 hour
            complexity_preference='medium'
        )
        
        if recommended_template:
            console.print(f"{prefix}[blue]💡 Recommended template:[/blue] {recommended_template.name}")
            console.print(f"{prefix}[dim]   Estimated duration: {recommended_template.estimated_duration // 60} minutes[/dim]")
            console.print(f"{prefix}[dim]   Complexity: {recommended_template.complexity_score:.1f}/10[/dim]\n")
        
        # Create workflow
        workflow_id = await enhanced_brain.create_workflow(
            user_id="concurrent_user",
            session_id=session_id,
            workflow_type=workflow_type,
            initial_request=user_input
        )
        
        console.print(f"{prefix}[green]Created workflow:[/green] {workflow_id}")
        
        # Execute with concurrent capabilities
        console.print(f"{prefix}[bold cyan]Executing with concurrent persistent agents...[/bold cyan]")
        
        # Start execution in background
        execution_task = asyncio.create_task(
            enhanced_brain.execute_workflow_enhanced(
                workflow_id=workflow_id,
                use_concurrent_execution=True,
                autopilot_mode=AutoPilotMode.SMART_AUTO
            )
        )
        
        # Track active workflow
        active_workflows[workflow_id] = execution_task
        
        # Monitor progress
        await _monitor_workflow_execution(enhanced_brain, workflow_id, execution_task, prefix)
        
        # Get result and update context
        result = await execution_task
        workflow_context[workflow_id] = {
            'request': user_input,
            'type': workflow_type,
            'result': result,
            'timestamp': datetime.utcnow(),
            'success': result.status == WorkflowStatus.COMPLETED
        }
        
        # Update template metrics if used
        if recommended_template:
            try:
                success = result.status == WorkflowStatus.COMPLETED
                duration = result.execution_summary.get('total_execution_time_seconds', 0)
                template_manager.update_template_metrics(
                    recommended_template.template_id,
                    success,
                    duration
                )
            except:
                pass  # Don't fail on metrics update
        
        # Remove from active workflows
        active_workflows.pop(workflow_id, None)
        
        console.print(f"{prefix}[green]✅ Workflow {workflow_id} completed![/green]\n")
        
        return result
        
    except Exception as e:
        console.print(f"{prefix}[red]❌ Workflow failed:[/red] {e}")
        active_workflows.pop(workflow_id, None) if 'workflow_id' in locals() else None
        raise


async def _display_active_workflows(active_workflows: Dict[str, asyncio.Task]):
    """Display currently active workflows."""
    if not active_workflows:
        console.print("[dim]No active workflows[/dim]")
        return
    
    console.print(f"\n[bold cyan]Active Workflows ({len(active_workflows)}):[/bold cyan]")
    for workflow_id, task in active_workflows.items():
        status = "Running" if not task.done() else "Completed"
        console.print(f"  • {workflow_id}: [cyan]{status}[/cyan]")


async def _cancel_workflow(workflow_id: Optional[str], active_workflows: Dict[str, asyncio.Task]):
    """Cancel a specific workflow or all workflows."""
    if not workflow_id:
        # Cancel all
        for wf_id, task in active_workflows.items():
            task.cancel()
            console.print(f"[yellow]Cancelled workflow {wf_id}[/yellow]")
        active_workflows.clear()
    elif workflow_id in active_workflows:
        active_workflows[workflow_id].cancel()
        console.print(f"[yellow]Cancelled workflow {workflow_id}[/yellow]")
        active_workflows.pop(workflow_id)
    else:
        console.print(f"[red]Workflow {workflow_id} not found[/red]")


async def _generate_follow_up_suggestions(
    workflow_manager,
    workflow_context: Dict[str, Any],
    results: List[Any],
    enhanced_brain=None,
    template_manager=None,
    analytics_engine=None,
    session_id=None,
    active_workflows=None
):
    """Generate intelligent follow-up suggestions based on completed workflows."""
    if not workflow_context:
        return
    
    console.print("\n[bold blue]🤖 Intelligent Follow-up Suggestions:[/bold blue]")
    
    try:
        suggestions = await workflow_manager.suggest_next_workflows(workflow_context)
        selected_prompt = await _display_workflow_suggestions(suggestions, workflow_manager)
        
        if selected_prompt and all([enhanced_brain, template_manager, analytics_engine, session_id, active_workflows is not None]):
            # Execute the selected suggestion as a new workflow
            console.print("\n[bold cyan]🚀 Executing selected follow-up workflow...[/bold cyan]")
            await _execute_single_workflow(
                selected_prompt, enhanced_brain, template_manager, analytics_engine,
                workflow_manager, session_id, active_workflows, workflow_context
            )
            
    except Exception as e:
        console.print(f"[red]Error generating suggestions:[/red] {e}")


async def _display_workflow_suggestions(suggestions: List[Dict[str, Any]], workflow_manager):
    """Display intelligent workflow suggestions to the user."""
    if not suggestions:
        console.print("[dim]No suggestions available at this time[/dim]")
        return None
    
    console.print("[bold cyan]Suggested Next Workflows:[/bold cyan]")
    
    for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
        confidence = suggestion.get('confidence', 0)
        reason = suggestion.get('reason', 'No reason provided')
        confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.5 else "red"
        
        console.print(f"\n[cyan]{i}.[/cyan] [bold]{suggestion['title']}[/bold]")
        console.print(f"   [dim]Type: {suggestion.get('workflow_type', 'unknown')}[/dim]")
        console.print(f"   [dim]Confidence: [{confidence_color}]{confidence:.1%}[/{confidence_color}][/dim]")
        console.print(f"   [dim]Reason: {reason}[/dim]")
        if 'business_value' in suggestion:
            console.print(f"   [blue]Business Value:[/blue] {suggestion['business_value']}")
        console.print(f"   [green]Prompt:[/green] \"{suggestion['suggested_prompt']}\"")
    
    # Ask if user wants to execute any suggestions
    choice = console.input(f"\n[cyan]Execute suggestion (1-{len(suggestions[:5])}) or press Enter to continue:[/cyan] ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(suggestions[:5]):
        selected = suggestions[int(choice) - 1]
        console.print(f"[green]✓ Executing suggestion:[/green] {selected['suggested_prompt']}")
        return selected['suggested_prompt']
    
    return None


async def _display_system_status(persistent_system: PersistentSystem, enhanced_brain, analytics_engine):
    """Display comprehensive system status."""
    
    # Get system health
    health = await persistent_system.get_system_health()
    
    # Create status table
    status_table = Table(title="🚀 Concurrent System Status")
    status_table.add_column("Component", style="cyan", no_wrap=True)
    status_table.add_column("Status", style="green")
    status_table.add_column("Metrics", style="white")
    
    # System overview
    uptime = round(health.get('uptime_seconds', 0) / 60, 1)
    status_table.add_row(
        "System",
        "🟢 Running" if health['system_running'] else "🔴 Stopped",
        f"Uptime: {uptime} min"
    )
    
    # Components
    components = health.get('components', {})
    
    if 'agent_pool' in components:
        pool_info = components['agent_pool']
        status_table.add_row(
            "Agent Pool",
            f"🟢 {pool_info['status'].title()}",
            f"{pool_info['healthy_agents']}/{pool_info['total_agents']} healthy"
        )
    
    if 'message_bus' in components:
        bus_info = components['message_bus']
        status_table.add_row(
            "Message Bus",
            "🟢 Connected" if bus_info.get('connected') else "🔴 Disconnected",
            f"{bus_info.get('messages_published', 0)} messages sent"
        )
    
    if 'orchestrator' in components:
        orch_info = components['orchestrator']
        status_table.add_row(
            "Orchestrator",
            "🟢 Active",
            f"{orch_info.get('active_batches', 0)} active batches"
        )
    
    # Enhanced features
    status_table.add_row(
        "Enhanced Brain",
        "🟢 Active",
        "Concurrent execution enabled"
    )
    
    status_table.add_row(
        "Analytics",
        "🟢 Active",
        "Performance monitoring enabled"
    )
    
    console.print(status_table)


async def _display_workflow_templates(template_manager: WorkflowTemplateManager):
    """Display available workflow templates."""
    
    templates_table = Table(title="📋 Available Workflow Templates")
    templates_table.add_column("Template", style="cyan")
    templates_table.add_column("Type", style="yellow")
    templates_table.add_column("Duration", style="green")
    templates_table.add_column("Complexity", style="blue")
    templates_table.add_column("Usage", style="white")
    
    for template in template_manager.templates.values():
        duration_min = template.estimated_duration // 60
        templates_table.add_row(
            template.name,
            template.workflow_type,
            f"{duration_min} min",
            f"{template.complexity_score:.1f}/10",
            f"{template.usage_count} times"
        )
    
    console.print(templates_table)
    
    # Display analytics
    analytics = template_manager.get_template_analytics()
    if analytics:
        console.print(f"\n[blue]Template Analytics:[/blue]")
        console.print(f"  Most popular: {analytics.get('most_popular_template', 'N/A')}")
        console.print(f"  Average complexity: {analytics.get('average_complexity', 0):.1f}/10")


async def _display_analytics_dashboard(analytics_engine: PerformanceAnalyticsEngine, enhanced_brain):
    """Display analytics dashboard."""
    
    # Get performance summary
    performance_summary = enhanced_brain.get_system_performance_summary()
    
    console.print(Panel.fit(
        f"[bold blue]System Performance Summary[/bold blue]\n\n"
        f"[green]Workflows Processed:[/green] {performance_summary['workflow_metrics']['total_processed']}\n"
        f"[green]Success Rate:[/green] {performance_summary['workflow_metrics']['success_rate']:.1f}%\n"
        f"[green]Avg Execution Time:[/green] {performance_summary['workflow_metrics']['average_execution_time']:.1f}s\n"
        f"[green]Avg Tasks per Workflow:[/green] {performance_summary['workflow_metrics']['average_tasks_per_workflow']:.1f}\n\n"
        f"[cyan]Concurrent Execution:[/cyan]\n"
        f"  • Workflows routed: {performance_summary['concurrent_execution_stats'].get('workflows_processed', 0)}\n"
        f"  • Tasks distributed: {performance_summary['concurrent_execution_stats'].get('tasks_routed', 0)}\n"
        f"  • Active workflows: {performance_summary['concurrent_execution_stats'].get('active_workflows', 0)}",
        title="📊 Analytics Dashboard"
    ))


async def _display_health_dashboard(persistent_system: PersistentSystem):
    """Display detailed health dashboard."""
    
    health = await persistent_system.get_system_health()
    
    console.print(Panel.fit(
        f"[bold green]System Health Dashboard[/bold green]\n\n"
        f"[white]Uptime:[/white] {health.get('uptime_seconds', 0) // 60} minutes\n"
        f"[white]System Status:[/white] {'🟢 Healthy' if health['system_running'] else '🔴 Unhealthy'}\n\n"
        f"[cyan]Component Health:[/cyan]\n" +
        "\n".join([
            f"  • {component}: {'🟢' if info.get('status') == 'running' else '🟡'} {info.get('status', 'unknown')}"
            for component, info in health.get('components', {}).items()
        ]) +
        f"\n\n[yellow]System Statistics:[/yellow]\n" +
        "\n".join([
            f"  • {key}: {value}"
            for key, value in health.get('system_statistics', {}).items()
        ]),
        title="🏥 Health Dashboard"
    ))


def _infer_workflow_type(user_input: str) -> str:
    """Infer workflow type from user input."""
    
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ['business', 'company', 'startup', 'launch']):
        return 'business_creation'
    elif any(word in input_lower for word in ['market', 'research', 'analysis', 'competitor']):
        return 'market_analysis'
    elif any(word in input_lower for word in ['brand', 'logo', 'design', 'identity']):
        return 'branding'
    else:
        return 'general'


async def _monitor_workflow_execution(enhanced_brain, workflow_id: str, execution_task: asyncio.Task, prefix: str = ""):
    """Monitor workflow execution with progress updates."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        
        task = progress.add_task(f"Executing workflow... {prefix}", total=100)
        
        while not execution_task.done():
            try:
                # Get progress
                workflow_progress = await enhanced_brain.get_enhanced_workflow_status(workflow_id)
                
                if workflow_progress and 'concurrent_execution' in workflow_progress:
                    concurrent_info = workflow_progress['concurrent_execution']
                    if concurrent_info:
                        progress_pct = concurrent_info.get('progress_percentage', 0)
                        status = concurrent_info.get('status', 'unknown')
                        
                        progress.update(task, completed=progress_pct, description=f"Status: {status} {prefix}")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.debug(f"Error monitoring workflow: {e}")
                await asyncio.sleep(2)
        
        progress.update(task, completed=100, description=f"Workflow completed! {prefix}")
    
    try:
        result = await execution_task
        
        # Display results
        console.print(f"\n[bold green]🎉 Workflow Completed![/bold green]")
        console.print(f"Status: {result.status.value}")
        console.print(f"Duration: {result.execution_summary.get('total_execution_time_seconds', 0):.1f} seconds")
        
        if result.final_outputs:
            console.print(f"\n[bold blue]Results:[/bold blue]")
            for key, value in result.final_outputs.items():
                if isinstance(value, dict) and 'summary' in value:
                    console.print(f"  • {key}: {value['summary']}")
                else:
                    console.print(f"  • {key}: Available")
        
    except Exception as e:
        console.print(f"{prefix}[red]Workflow execution failed:[/red] {e}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="HeyJarvis AI Agent Orchestrator")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode")
    parser.add_argument("--jarvis", action="store_true", 
                       help="Enable business-level orchestration with Jarvis")
    parser.add_argument("--branding", action="store_true",
                       help="Enable branding agent orchestration")
    parser.add_argument("--intelligence", action="store_true",
                       help="Enable Intelligence Layer with Human-in-the-Loop workflows")
    parser.add_argument("--concurrent", action="store_true",
                       help="Enable concurrent persistent agent system with enhanced capabilities")
    args = parser.parse_args()
    
    if args.demo:
        asyncio.run(demo_mode())
    elif args.jarvis:
        asyncio.run(jarvis_mode())
    elif args.branding:
        asyncio.run(branding_mode())
    elif args.intelligence:
        asyncio.run(intelligence_mode())
    elif args.concurrent:
        asyncio.run(concurrent_mode())
    else:
        asyncio.run(chat_interface())


if __name__ == "__main__":
    main()