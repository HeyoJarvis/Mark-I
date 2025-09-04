#!/usr/bin/env python3
"""
Demonstration of the Persistent Agent System - Phase 1 Implementation.

This demo shows:
- Persistent agent pool initialization
- Concurrent task execution
- Human-in-the-loop approval workflow  
- Real-time progress monitoring
- System health monitoring
- Inter-agent communication via message bus
"""

import asyncio
import logging
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
import time

from orchestration.persistent.persistent_system import (
    create_development_persistent_system,
    SystemIntegrationHelper
)
from orchestration.persistent.concurrent_orchestrator import ApprovalRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for output
console = Console()


class PersistentSystemDemo:
    """Demonstration of the persistent agent system capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.system = create_development_persistent_system()
        self.integration_helper = SystemIntegrationHelper(self.system)
        self.approval_requests = {}
        
        # Demo state
        self.demo_user_id = "demo_user"
        self.demo_session_id = "demo_session_001"
        self.demo_workflow_id = "workflow_001"
        
        # Progress tracking
        self.progress_updates = {}
    
    async def run_demo(self):
        """Run the complete persistent system demonstration."""
        console.print(Panel.fit(
            "[bold blue]Persistent Agent System - Phase 1 Demo[/bold blue]\n"
            "Demonstrating concurrent agents with human-in-the-loop approval",
            title="🚀 HeyJarvis Persistent System"
        ))
        
        try:
            # Step 1: Start the persistent system
            await self._demo_system_startup()
            
            # Step 2: Show system health
            await self._demo_system_health()
            
            # Step 3: Demonstrate concurrent task submission
            batch_id = await self._demo_concurrent_tasks()
            
            # Step 4: Handle approval workflow
            await self._demo_approval_workflow()
            
            # Step 5: Monitor execution progress
            await self._demo_progress_monitoring(batch_id)
            
            # Step 6: Show final results
            await self._demo_final_results(batch_id)
            
            # Step 7: System statistics
            await self._demo_system_statistics()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Demo error: {e}[/red]")
            logger.error(f"Demo error: {e}", exc_info=True)
        finally:
            # Cleanup
            await self._demo_system_shutdown()
    
    async def _demo_system_startup(self):
        """Demonstrate system startup process."""
        console.print("\n[bold green]Step 1: Starting Persistent System[/bold green]")
        
        with console.status("[bold green]Initializing components...") as status:
            # Set up callbacks
            self.system.set_approval_callback(self._handle_approval_request)
            self.system.set_progress_callback(self._handle_progress_update)
            
            status.update("[bold green]Starting message bus...")
            await asyncio.sleep(1)
            
            status.update("[bold green]Initializing agent pool...")
            await asyncio.sleep(1)
            
            status.update("[bold green]Starting persistent agents...")
            await self.system.start()
            
            status.update("[bold green]System ready!")
            await asyncio.sleep(0.5)
        
        console.print("✅ [green]Persistent system started successfully![/green]")
        console.print("   • Message bus connected")
        console.print("   • Agent pool initialized")
        console.print("   • Persistent agents ready")
        console.print("   • Concurrent orchestrator active")
    
    async def _demo_system_health(self):
        """Demonstrate system health monitoring."""
        console.print("\n[bold cyan]Step 2: System Health Check[/bold cyan]")
        
        health = await self.system.get_system_health()
        
        # Create health status table
        health_table = Table(title="System Health Status")
        health_table.add_column("Component", style="cyan", no_wrap=True)
        health_table.add_column("Status", style="green")
        health_table.add_column("Details", style="white")
        
        # System overview
        uptime = round(health.get('uptime_seconds', 0) / 60, 1)
        health_table.add_row(
            "System",
            "🟢 Running" if health['system_running'] else "🔴 Stopped",
            f"Uptime: {uptime} minutes"
        )
        
        # Component health
        components = health.get('components', {})
        
        if 'agent_pool' in components:
            pool_info = components['agent_pool']
            health_table.add_row(
                "Agent Pool",
                f"🟢 {pool_info['status'].title()}",
                f"{pool_info['healthy_agents']}/{pool_info['total_agents']} agents healthy"
            )
        
        if 'message_bus' in components:
            bus_info = components['message_bus']
            health_table.add_row(
                "Message Bus",
                "🟢 Connected" if bus_info.get('connected') else "🔴 Disconnected",
                f"{bus_info['active_subscriptions']} subscriptions"
            )
        
        if 'orchestrator' in components:
            orch_info = components['orchestrator']
            health_table.add_row(
                "Orchestrator",
                "🟢 Active",
                f"{orch_info['active_batches']} active batches"
            )
        
        console.print(health_table)
    
    async def _demo_concurrent_tasks(self):
        """Demonstrate concurrent task submission."""
        console.print("\n[bold yellow]Step 3: Submitting Concurrent Tasks[/bold yellow]")
        
        business_idea = "AI-powered personal fitness coaching app"
        
        console.print(f"[bold]Business Idea:[/bold] {business_idea}")
        console.print("\nSubmitting concurrent tasks:")
        
        # Submit business creation workflow
        batch_id = await self.integration_helper.process_business_creation_workflow(
            business_idea=business_idea,
            user_id=self.demo_user_id,
            session_id=self.demo_session_id,
            workflow_id=self.demo_workflow_id
        )
        
        console.print(f"✅ [green]Batch submitted: {batch_id}[/green]")
        console.print("   • Market opportunity analysis")
        console.print("   • Brand name generation")  
        console.print("   • Competitive analysis")
        
        return batch_id
    
    async def _demo_approval_workflow(self):
        """Demonstrate human-in-the-loop approval process."""
        console.print("\n[bold magenta]Step 4: Human-in-the-Loop Approval[/bold magenta]")
        
        console.print("Waiting for approval requests from agents...")
        
        # Wait for approval requests
        timeout = 30  # 30 second timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.approval_requests:
                break
            await asyncio.sleep(1)
        
        # Process approval requests
        if self.approval_requests:
            for request_id, request in list(self.approval_requests.items()):
                await self._process_approval_request(request_id, request)
        else:
            console.print("[yellow]No approval requests received in timeout period[/yellow]")
            console.print("[dim]This may indicate agents are processing without approval needs[/dim]")
    
    async def _demo_progress_monitoring(self, batch_id: str):
        """Demonstrate real-time progress monitoring."""
        console.print("\n[bold blue]Step 5: Progress Monitoring[/bold blue]")
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Executing batch...", total=100)
            
            while not progress.finished:
                status = await self.system.get_batch_status(batch_id)
                if not status:
                    break
                
                # Update progress
                progress_pct = status.get('progress_percentage', 0)
                progress.update(task, completed=progress_pct)
                
                # Show current status
                batch_status = status.get('status', 'unknown')
                completed = status.get('completed_tasks', 0)
                failed = status.get('failed_tasks', 0)
                total = status.get('total_tasks', 0)
                
                progress.console.print(
                    f"Status: {batch_status} | "
                    f"Completed: {completed} | "
                    f"Failed: {failed} | "
                    f"Total: {total}",
                    style="dim"
                )
                
                if batch_status in ['completed', 'failed', 'cancelled']:
                    progress.update(task, completed=100)
                    break
                
                await asyncio.sleep(2)
    
    async def _demo_final_results(self, batch_id: str):
        """Show final execution results."""
        console.print("\n[bold green]Step 6: Final Results[/bold green]")
        
        status = await self.system.get_batch_status(batch_id)
        if not status:
            console.print("[red]Could not retrieve batch status[/red]")
            return
        
        # Results summary table
        results_table = Table(title=f"Batch Results: {batch_id}")
        results_table.add_column("Task", style="cyan")
        results_table.add_column("Status", style="green")
        results_table.add_column("Agent", style="yellow")
        results_table.add_column("Duration", style="white")
        
        for task in status.get('tasks', []):
            task_status = task.get('status', 'unknown')
            status_emoji = "✅" if task_status == 'completed' else "❌" if task_status == 'failed' else "⏳"
            
            # Calculate duration
            started = task.get('started_at')
            completed = task.get('completed_at')
            duration = "N/A"
            if started and completed:
                # This would need proper datetime parsing in a real implementation
                duration = "< 1min"  # Simplified
            
            results_table.add_row(
                task.get('description', 'Unknown task'),
                f"{status_emoji} {task_status}",
                task.get('assigned_agent', 'None'),
                duration
            )
        
        console.print(results_table)
        
        # Overall summary
        batch_status = status.get('status', 'unknown')
        if batch_status == 'completed':
            console.print("🎉 [bold green]All tasks completed successfully![/bold green]")
        elif batch_status == 'failed':
            console.print("⚠️  [bold yellow]Some tasks failed but batch completed[/bold yellow]")
        else:
            console.print(f"ℹ️  [bold blue]Batch status: {batch_status}[/bold blue]")
    
    async def _demo_system_statistics(self):
        """Show system statistics."""
        console.print("\n[bold purple]Step 7: System Statistics[/bold purple]")
        
        health = await self.system.get_system_health()
        stats = health.get('system_statistics', {})
        
        stats_table = Table(title="System Performance Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Batches Processed", str(stats.get('total_batches', 0)))
        stats_table.add_row("Total Tasks Executed", str(stats.get('total_tasks', 0)))
        stats_table.add_row("Total Approvals Handled", str(stats.get('total_approvals', 0)))
        stats_table.add_row("System Uptime", f"{stats.get('system_uptime_hours', 0):.2f} hours")
        
        # Agent pool stats
        components = health.get('components', {})
        if 'agent_pool' in components:
            pool_stats = components['agent_pool']
            stats_table.add_row("Agent Success Rate", f"{pool_stats.get('success_rate', 0):.1f}%")
        
        console.print(stats_table)
    
    async def _demo_system_shutdown(self):
        """Demonstrate graceful system shutdown."""
        console.print("\n[bold red]System Shutdown[/bold red]")
        
        with console.status("[bold red]Shutting down gracefully...") as status:
            status.update("[bold red]Stopping orchestrator...")
            await asyncio.sleep(0.5)
            
            status.update("[bold red]Stopping agents...")
            await asyncio.sleep(0.5)
            
            status.update("[bold red]Disconnecting message bus...")
            await self.system.stop()
            
            status.update("[bold red]Cleanup complete")
            await asyncio.sleep(0.5)
        
        console.print("✅ [green]System shutdown completed successfully[/green]")
    
    async def _handle_approval_request(self, approval_request: ApprovalRequest):
        """Handle approval requests during demo."""
        self.approval_requests[approval_request.request_id] = approval_request
        
        console.print(f"\n🔔 [bold yellow]Approval Request Received[/bold yellow]")
        console.print(f"   Request ID: {approval_request.request_id}")
        console.print(f"   Task: {approval_request.task.description}")
        console.print(f"   Agent: {approval_request.task.preferred_agent or 'Auto-assigned'}")
    
    async def _handle_progress_update(self, batch_id: str, progress_data: Dict[str, Any]):
        """Handle progress updates during demo."""
        self.progress_updates[batch_id] = progress_data
    
    async def _process_approval_request(self, request_id: str, request: ApprovalRequest):
        """Process an approval request with user interaction simulation."""
        console.print(f"\n[bold yellow]Processing Approval: {request_id}[/bold yellow]")
        
        # Create approval details panel
        approval_panel = Panel(
            f"[bold]Task:[/bold] {request.task.description}\n"
            f"[bold]Type:[/bold] {request.task.task_type}\n"
            f"[bold]Agent:[/bold] {request.task.preferred_agent or 'Auto-assigned'}\n"
            f"[bold]Priority:[/bold] {request.task.priority}\n"
            f"[bold]Risk Assessment:[/bold] {request.risk_assessment}",
            title="🤖 Agent Task Approval",
            border_style="yellow"
        )
        console.print(approval_panel)
        
        # Simulate human decision (auto-approve for demo)
        console.print("[dim]Simulating human approval decision...[/dim]")
        await asyncio.sleep(2)
        
        # Auto-approve for demo purposes
        approved = True
        message = "Auto-approved for demo purposes"
        
        await self.system.approve_task(request_id, approved, message)
        
        status_msg = "[green]✅ APPROVED[/green]" if approved else "[red]❌ REJECTED[/red]"
        console.print(f"Decision: {status_msg} - {message}")
        
        # Remove from pending approvals
        self.approval_requests.pop(request_id, None)


async def main():
    """Main demo function."""
    console.print("[bold blue]Starting Persistent Agent System Demo...[/bold blue]")
    
    demo = PersistentSystemDemo()
    await demo.run_demo()
    
    console.print("\n[bold green]Demo completed! Thank you for trying the Persistent Agent System.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())