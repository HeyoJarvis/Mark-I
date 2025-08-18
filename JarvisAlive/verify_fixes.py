#!/usr/bin/env python3
"""
Verify Intelligence Layer fixes without requiring interactive input.

This script tests the two key fixes:
1. Workflow continuation (doesn't exit after first step)  
2. Context awareness (recognizes follow-up commands)
"""

import asyncio
import os
import re
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()

async def verify_context_awareness():
    """Verify context awareness fix by testing command recognition."""
    console.print("[bold blue]🧠 Testing Context Awareness Fix[/bold blue]")
    console.print("="*50)
    
    # Import the context awareness function
    import sys
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_module", "main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    
    # Test commands
    test_cases = [
        # Should be recognized as continuation commands
        ("do step 2", True),
        ("next step", True), 
        ("continue", True),
        ("2", True),
        ("run option 1", True),
        ("execute step 3", True),
        ("proceed", True),
        ("step 1", True),
        
        # Should NOT be continuation commands  
        ("create a new business plan", False),
        ("help me start a company", False),
        ("what should I do for my startup", False),
        ("tell me about market research", False),
    ]
    
    # Mock workflow brain and current workflow
    class MockWorkflowBrain:
        def __init__(self):
            self.active_workflows = {"test123": {"status": "active"}}
    
    mock_brain = MockWorkflowBrain()
    current_workflow_id = "test123"
    
    console.print("\n📋 Testing command recognition:")
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for command, expected_is_continuation in test_cases:
        try:
            is_continuation = await main_module.is_workflow_continuation_command(
                command, current_workflow_id, mock_brain
            )
            
            status = "✅" if is_continuation == expected_is_continuation else "❌"
            result = "CONTINUATION" if is_continuation else "NEW WORKFLOW"
            expected = "CONTINUATION" if expected_is_continuation else "NEW WORKFLOW"
            
            console.print(f"   {status} '{command}' -> {result} (expected {expected})")
            
            if is_continuation == expected_is_continuation:
                correct_predictions += 1
                
        except Exception as e:
            console.print(f"   ❌ '{command}' -> ERROR: {e}")
    
    accuracy = (correct_predictions / total_tests) * 100
    console.print(f"\n📊 Context Awareness Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    if accuracy >= 90:
        console.print("[bold green]✅ Context awareness fix VERIFIED![/bold green]")
        return True
    else:
        console.print("[bold red]❌ Context awareness needs improvement[/bold red]") 
        return False


async def verify_workflow_logic():
    """Verify workflow continuation logic by checking the step result logic."""
    console.print("\n[bold blue]⚙️ Testing Workflow Continuation Logic[/bold blue]")
    console.print("="*50)
    
    # Import the workflow brain to check the fix
    from orchestration.intelligence.workflow_brain import WorkflowBrain
    from orchestration.intelligence.models import WorkflowStep, StepStatus
    
    # Create a mock workflow brain
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'redis_url': 'redis://localhost:6379'
    }
    
    workflow_brain = WorkflowBrain(config)
    
    console.print("📋 Testing step execution result logic...")
    
    # Create a mock successful orchestrator result
    mock_orchestrator_result = {
        'status': 'success',
        'response': {
            'result': {
                'step_completed': True,
                'output': 'Market research completed'
            }
        }
    }
    
    # Create a mock workflow step
    mock_step = WorkflowStep(
        step_id="test_step",
        step_type="market_research", 
        agent_id="market_research_agent",
        description="Test step",
        input_state={}
    )
    
    # Test the fixed conversion logic
    try:
        step_result = workflow_brain._convert_orchestrator_result(mock_orchestrator_result, mock_step)
        
        console.print(f"   📊 Step status: {mock_step.status.value}")
        console.print(f"   🔄 Is workflow complete: {step_result.is_complete}")
        console.print(f"   📋 Has output data: {step_result.output_data is not None}")
        console.print(f"   ❌ Has error: {step_result.has_error}")
        
        # Verify the fix
        if step_result.is_complete == False and mock_step.status == StepStatus.COMPLETED:
            console.print("[bold green]✅ Workflow continuation logic VERIFIED![/bold green]")
            console.print("   Individual steps complete but workflow continues")
            return True
        else:
            console.print("[bold red]❌ Workflow continuation logic issue detected[/bold red]")
            return False
            
    except Exception as e:
        console.print(f"[bold red]❌ Error testing workflow logic: {e}[/bold red]")
        return False


async def main():
    """Run verification tests for Intelligence Layer fixes."""
    console.print("[bold cyan]🔧 Intelligence Layer Fixes Verification[/bold cyan]")
    console.print("="*60)
    
    # Test both fixes
    context_test_passed = await verify_context_awareness()
    workflow_test_passed = await verify_workflow_logic()
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]📊 Verification Summary[/bold cyan]")
    
    status1 = "✅ PASS" if context_test_passed else "❌ FAIL"
    status2 = "✅ PASS" if workflow_test_passed else "❌ FAIL"
    
    console.print(f"   🧠 Context Awareness Fix: {status1}")
    console.print(f"   ⚙️  Workflow Continuation Fix: {status2}")
    
    if context_test_passed and workflow_test_passed:
        console.print("\n[bold green]🎉 ALL FIXES VERIFIED! Intelligence Layer is ready.[/bold green]")
        console.print("\n🚀 Next steps:")
        console.print("   • Test with: python main.py --intelligence")  
        console.print("   • Try commands: 'Create a coffee business' then 'do step 2'")
        console.print("   • Verify workflow continues through multiple steps")
    else:
        console.print("\n[bold red]❌ Some fixes need attention.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())