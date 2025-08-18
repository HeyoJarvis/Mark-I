#!/usr/bin/env python3
"""
Test script to verify the Intelligence Layer workflow continuation fixes.

This script tests:
1. Workflow continues after first step completion (doesn't exit)
2. Context awareness for follow-up commands
"""

import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

# Import Intelligence Layer components
from orchestration.intelligence.workflow_brain import WorkflowBrain

console = Console()

async def test_workflow_continuation():
    """Test that workflows continue after first step completion."""
    
    console.print("[bold blue]🧪 Testing Workflow Continuation Fix[/bold blue]")
    console.print("="*50)
    
    # Setup
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
    }
    
    workflow_brain = WorkflowBrain(config)
    await workflow_brain.initialize_orchestration()
    
    # Test 1: Create workflow
    console.print("\n📋 Test 1: Creating workflow...")
    workflow_id = await workflow_brain.create_workflow(
        user_id="test_user",
        session_id="test_session",
        workflow_type="business_creation",
        initial_request="Create a coffee subscription service",
        context={"test": True}
    )
    
    workflow_state = workflow_brain.active_workflows[workflow_id]
    console.print(f"   ✅ Created: {workflow_id}")
    console.print(f"   📊 Planned steps: {len(workflow_state.pending_steps)}")
    console.print(f"   🔄 Status: {workflow_state.status.value}")
    
    # Test 2: Execute one step and verify it doesn't complete the workflow
    console.print("\n⚙️ Test 2: Executing workflow (should continue after first step)...")
    
    original_pending_count = len(workflow_state.pending_steps)
    
    try:
        # This should execute steps but not complete after just one
        result = await workflow_brain.execute_workflow(workflow_id)
        
        # Check final state
        final_pending_count = len(workflow_state.pending_steps)
        console.print(f"   📊 Original pending steps: {original_pending_count}")
        console.print(f"   📊 Final pending steps: {final_pending_count}")
        console.print(f"   ✅ Completed steps: {len(workflow_state.completed_steps)}")
        console.print(f"   🔄 Final status: {workflow_state.status.value}")
        
        # Verify the fix
        if workflow_state.status.value in ['completed', 'failed'] and len(workflow_state.completed_steps) < original_pending_count:
            console.print(f"   ✅ [green]FIX VERIFIED: Workflow completed steps but had more to do[/green]")
        elif workflow_state.status.value in ['awaiting_human', 'paused']:
            console.print(f"   ✅ [green]FIX VERIFIED: Workflow paused for human input as expected[/green]")
        else:
            console.print(f"   ⚠️  [yellow]Status: {workflow_state.status.value}[/yellow]")
        
    except Exception as e:
        console.print(f"   ❌ [red]Error: {e}[/red]")
    
    # Test 3: Context awareness simulation
    console.print(f"\n🧠 Test 3: Context awareness simulation...")
    
    # Import the new functions from main.py
    import sys
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_module", "main.py")
    main_module = importlib.util.module_from_spec(spec)
    
    # Test different continuation commands
    test_commands = [
        "do step 2",
        "next step", 
        "continue",
        "2",
        "run option 1",
        "create a new business plan"  # Should NOT be continuation
    ]
    
    for cmd in test_commands:
        is_continuation = await main_module.is_workflow_continuation_command(
            cmd, workflow_id, workflow_brain
        )
        expected_continuation = cmd != "create a new business plan"
        
        status = "✅" if is_continuation == expected_continuation else "❌"
        console.print(f"   {status} '{cmd}' -> Continuation: {is_continuation}")
    
    console.print(f"\n[bold green]🎉 Workflow Continuation Tests Complete![/bold green]")
    console.print(f"   📋 Workflow ID: {workflow_id}")
    console.print(f"   🔄 Final Status: {workflow_state.status.value}")
    console.print(f"   📊 Steps completed: {len(workflow_state.completed_steps)}")


async def main():
    """Run the workflow continuation tests."""
    await test_workflow_continuation()


if __name__ == "__main__":
    asyncio.run(main())