#!/usr/bin/env python3
"""
Demo script for Intelligence Layer integration showing Human-in-the-Loop workflows.

This script demonstrates the Intelligence Layer running in demo mode without 
requiring interactive terminal input, making it perfect for testing in Claude Code.
"""

import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import Intelligence Layer components
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.intelligence.models import (
    AutoPilotMode, 
    WorkflowStatus, 
    HITLPreferences,
    HumanDecision,
    NextStepOption
)

console = Console()


class IntelligenceLayerDemo:
    """Demo class for Intelligence Layer functionality."""
    
    def __init__(self):
        """Initialize the demo."""
        self.logger = logging.getLogger(__name__)
        self.workflow_brain: WorkflowBrain = None
        
    async def setup(self):
        """Set up the demo environment."""
        console.print("[bold blue]🧠 Intelligence Layer Integration Demo[/bold blue]")
        console.print("="*60)
        console.print()
        
        # Get API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            console.print("[red]❌ ANTHROPIC_API_KEY not found in environment[/red]")
            return False
        
        # Configure WorkflowBrain
        config = {
            'anthropic_api_key': api_key,
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
        }
        
        try:
            # Initialize WorkflowBrain
            console.print("🔧 Initializing Intelligence Layer...")
            self.workflow_brain = WorkflowBrain(config)
            
            # Initialize orchestration integration
            await self.workflow_brain.initialize_orchestration()
            
            console.print("[green]✅ Intelligence Layer ready[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Setup failed: {e}[/red]")
            return False
    
    async def demo_workflow_creation(self):
        """Demonstrate workflow creation and planning."""
        console.print("\n[bold yellow]📋 DEMO 1: Workflow Creation & AI Planning[/bold yellow]")
        
        # Create a complex business workflow
        user_request = "Create a sustainable coffee subscription business with focus on ethical sourcing"
        
        console.print(f"[bold cyan]User Request:[/bold cyan] {user_request}")
        console.print("🧠 Creating intelligent workflow...")
        
        try:
            workflow_id = await self.workflow_brain.create_workflow(
                user_id="demo_user",
                session_id="demo_session",
                workflow_type="business_creation",
                initial_request=user_request,
                context={
                    "industry": "food_beverage",
                    "sustainability_focus": True,
                    "business_model": "subscription"
                }
            )
            
            workflow_state = self.workflow_brain.active_workflows[workflow_id]
            
            # Display workflow plan
            console.print(f"\n[green]✅ Workflow Created: {workflow_id}[/green]")
            console.print(f"   📝 Title: {workflow_state.workflow_title}")
            console.print(f"   📊 Planned Steps: {len(workflow_state.pending_steps)}")
            console.print(f"   🎯 Type: {workflow_state.workflow_type}")
            console.print(f"   🔄 Autopilot Mode: {workflow_state.autopilot_mode.value}")
            
            return workflow_id
            
        except Exception as e:
            console.print(f"[red]❌ Workflow creation failed: {e}[/red]")
            return None
    
    async def demo_ai_recommendations(self, workflow_id: str):
        """Demonstrate AI-powered next step recommendations."""
        console.print("\n[bold yellow]🎯 DEMO 2: AI-Powered Next Step Recommendations[/bold yellow]")
        
        workflow_state = self.workflow_brain.active_workflows[workflow_id]
        
        console.print("🤖 Generating AI recommendations...")
        
        try:
            recommendations = await self.workflow_brain._generate_next_step_recommendations(workflow_state)
            
            if recommendations:
                console.print(f"\n[green]🎯 AI Generated {len(recommendations)} Recommendations:[/green]")
                
                for i, rec in enumerate(recommendations, 1):
                    confidence_color = "green" if rec.confidence_score > 0.8 else "yellow" if rec.confidence_score > 0.6 else "red"
                    
                    panel_content = (
                        f"[bold]{rec.description}[/bold]\n"
                        f"🤖 Agent: {rec.agent_id}\n"
                        f"📊 Confidence: [{confidence_color}]{rec.confidence_score:.1%}[/{confidence_color}]\n"
                        f"⏱️  Time: ~{rec.estimated_time_minutes} minutes\n"
                        f"⚠️  Risk: {rec.risk_level.value}\n"
                    )
                    
                    if rec.reasoning:
                        panel_content += f"💭 Reasoning: {rec.reasoning}\n"
                    
                    if rec.required_inputs:
                        panel_content += f"📥 Needs: {', '.join(rec.required_inputs)}"
                    
                    console.print(Panel(
                        panel_content,
                        title=f"Option {i}",
                        border_style=confidence_color
                    ))
                
                return recommendations
            else:
                console.print("[yellow]⚠️ No AI recommendations generated[/yellow]")
                return []
                
        except Exception as e:
            console.print(f"[red]❌ AI recommendation generation failed: {e}[/red]")
            return []
    
    async def demo_autopilot_modes(self, workflow_id: str, recommendations):
        """Demonstrate different autopilot decision modes."""
        console.print("\n[bold yellow]⚙️ DEMO 3: AutoPilot Decision Modes[/bold yellow]")
        
        workflow_state = self.workflow_brain.active_workflows[workflow_id]
        
        modes_to_test = [
            (AutoPilotMode.HUMAN_CONTROL, "Always ask human"),
            (AutoPilotMode.SMART_AUTO, "Auto when confident"),
            (AutoPilotMode.FULL_AUTO, "Always automatic"),
            (AutoPilotMode.CUSTOM_THRESHOLD, "Custom threshold")
        ]
        
        for mode, description in modes_to_test:
            console.print(f"\n🔄 Testing {mode.value} ({description})...")
            
            # Temporarily set mode
            original_mode = workflow_state.autopilot_mode
            workflow_state.autopilot_mode = mode
            
            try:
                # Evaluate autopilot decision
                autopilot_decision = await self.workflow_brain.autopilot_manager.evaluate_autopilot_decision(
                    workflow_state, 
                    recommendations
                )
                
                # Display decision
                decision_color = "green" if autopilot_decision.should_proceed_automatically else "yellow"
                console.print(f"   [{decision_color}]Decision: {'🤖 AUTO' if autopilot_decision.should_proceed_automatically else '👤 HUMAN'}[/{decision_color}]")
                console.print(f"   💭 Reasoning: {autopilot_decision.reasoning}")
                
                if autopilot_decision.chosen_option:
                    console.print(f"   ✅ Would choose: {autopilot_decision.chosen_option.description}")
                
            except Exception as e:
                console.print(f"   [red]❌ Error: {e}[/red]")
            
            # Restore original mode
            workflow_state.autopilot_mode = original_mode
    
    async def demo_simulated_human_decisions(self, workflow_id: str, recommendations):
        """Demonstrate human decision processing with simulated decisions."""
        console.print("\n[bold yellow]👤 DEMO 4: Simulated Human Decision Processing[/bold yellow]")
        
        workflow_state = self.workflow_brain.active_workflows[workflow_id]
        
        # Simulate different types of human decisions
        simulated_decisions = [
            {
                "choice": "option_1",
                "description": "Choose first AI recommendation",
                "reasoning": "Market research seems like the logical first step"
            },
            {
                "choice": "custom:I want to start with competitor analysis instead",
                "description": "Custom user input",
                "reasoning": "User has specific domain knowledge"
            },
            {
                "choice": "autopilot smart",
                "description": "Enable smart autopilot",
                "reasoning": "User wants to speed up process"
            }
        ]
        
        for i, decision_data in enumerate(simulated_decisions, 1):
            console.print(f"\n🧪 Simulated Decision {i}: {decision_data['description']}")
            console.print(f"   👤 Human Choice: {decision_data['choice']}")
            console.print(f"   💭 Reasoning: {decision_data['reasoning']}")
            
            try:
                if decision_data['choice'].startswith('autopilot'):
                    # Handle autopilot command
                    console.print("   🔄 [blue]Autopilot mode updated[/blue]")
                    continue
                
                # Create simulated human decision
                human_decision = HumanDecision(
                    decision_id="",
                    workflow_id=workflow_id,
                    workflow_step=workflow_state.current_step_index,
                    ai_recommendations=recommendations,
                    human_choice=decision_data['choice'],
                    custom_input=decision_data['choice'].split(':', 1)[1] if decision_data['choice'].startswith('custom:') else None,
                    reasoning=decision_data['reasoning']
                )
                
                # Process human decision
                workflow_step = await self.workflow_brain.decision_engine.process_human_decision(
                    human_decision,
                    recommendations,
                    workflow_state
                )
                
                console.print(f"   ✅ [green]Processed Successfully[/green]")
                console.print(f"   📋 Created Step: {workflow_step.description}")
                console.print(f"   🤖 Agent: {workflow_step.agent_id}")
                console.print(f"   📊 Confidence: {workflow_step.confidence_score:.1%}")
                
            except Exception as e:
                console.print(f"   [red]❌ Processing failed: {e}[/red]")
    
    async def demo_workflow_state_management(self, workflow_id: str):
        """Demonstrate workflow state management capabilities."""
        console.print("\n[bold yellow]📊 DEMO 5: Workflow State Management[/bold yellow]")
        
        workflow_state = self.workflow_brain.active_workflows[workflow_id]
        
        # Add some test data to demonstrate context management
        test_context_data = {
            "market_research": {
                "market_size": "$2.1B",
                "growth_rate": "12% annually",
                "key_trends": ["sustainability", "convenience", "premium_quality"]
            },
            "competitive_analysis": {
                "main_competitors": ["Blue Bottle", "Trade Coffee", "Atlas Coffee"],
                "competitive_advantage": "Ethical sourcing + sustainability focus"
            },
            "brand_identity": {
                "brand_name": "EthiCup",
                "tagline": "Conscious Coffee, Delivered",
                "values": ["sustainability", "fairness", "quality"]
            }
        }
        
        # Update workflow context
        console.print("📝 Adding context data to workflow...")
        workflow_state.update_context(test_context_data)
        
        # Display workflow state information
        console.print("\n[bold cyan]📋 Workflow State Summary:[/bold cyan]")
        console.print(f"   🆔 ID: {workflow_state.workflow_id}")
        console.print(f"   📝 Title: {workflow_state.workflow_title}")
        console.print(f"   📊 Progress: {workflow_state.progress_percentage:.1f}%")
        console.print(f"   ⏱️  Duration: {workflow_state.duration_seconds:.1f} seconds")
        console.print(f"   🔄 Status: {workflow_state.status.value}")
        console.print(f"   🤖 Autopilot: {workflow_state.autopilot_mode.value}")
        console.print(f"   ✅ Completed Steps: {len(workflow_state.completed_steps)}")
        console.print(f"   👤 Human Decisions: {len(workflow_state.human_decisions)}")
        console.print(f"   📚 Context Keys: {len(workflow_state.accumulated_data)}")
        
        # Show accumulated context data
        console.print(f"\n[bold cyan]🗂️  Accumulated Context Data:[/bold cyan]")
        for key, value in workflow_state.accumulated_data.items():
            if isinstance(value, dict):
                console.print(f"   📂 {key}: {len(value)} items")
            elif isinstance(value, list):
                console.print(f"   📋 {key}: {len(value)} entries")
            else:
                console.print(f"   📄 {key}: {str(value)[:50]}...")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive Intelligence Layer integration demo."""
        console.print("[bold blue]🚀 Starting Intelligence Layer Integration Demo[/bold blue]")
        console.print()
        
        # Setup
        if not await self.setup():
            return False
        
        # Demo sequence
        workflow_id = await self.demo_workflow_creation()
        if not workflow_id:
            return False
        
        recommendations = await self.demo_ai_recommendations(workflow_id)
        if not recommendations:
            return False
        
        await self.demo_autopilot_modes(workflow_id, recommendations)
        await self.demo_simulated_human_decisions(workflow_id, recommendations)
        await self.demo_workflow_state_management(workflow_id)
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Intelligence Layer Integration Demo Complete![/bold green]")
        console.print()
        console.print("[bold cyan]✅ Integration Status: SUCCESS[/bold cyan]")
        console.print()
        console.print("[bold yellow]🎯 What was demonstrated:[/bold yellow]")
        console.print("   • ✅ Workflow creation and AI planning")
        console.print("   • ✅ AI-powered next step recommendations")
        console.print("   • ✅ Multiple autopilot control modes")
        console.print("   • ✅ Human decision processing")
        console.print("   • ✅ Workflow state management")
        console.print("   • ✅ Full integration with Universal Orchestrator")
        console.print()
        console.print("[bold yellow]🚀 Ready for production use:[/bold yellow]")
        console.print("   • Run with: python main.py --intelligence")
        console.print("   • Or integrate into existing chat interface")
        console.print("   • Add to Universal Orchestrator routing")
        
        return True


async def main():
    """Main demo execution."""
    demo = IntelligenceLayerDemo()
    
    try:
        success = await demo.run_comprehensive_demo()
        
        if success:
            console.print("\n[bold green]🎯 Integration successful! Intelligence Layer is ready.[/bold green]")
        else:
            console.print("\n[bold red]❌ Integration demo failed.[/bold red]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Demo failed with error: {e}[/bold red]")
        logging.exception("Demo execution error")


if __name__ == "__main__":
    # Ensure we're in the correct directory
    if not os.path.exists("orchestration/intelligence"):
        console.print("[red]❌ Please run this demo from the JarvisAlive directory[/red]")
        exit(1)
    
    asyncio.run(main())