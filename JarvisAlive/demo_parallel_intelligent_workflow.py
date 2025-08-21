#!/usr/bin/env python3
"""
Demo: Hierarchical Parallel Intelligence LangGraph

This script demonstrates the new hierarchical parallel workflow system that:

1. Intelligence Orchestrator Layer (Top):
   - Analyzes user request and plans execution
   - Assesses risks and determines approval requirements  
   - Handles clean Human-in-the-Loop approval

2. Parallel Agent Execution Layer (Middle):
   - Branding Agent (parallel)
   - Logo Generation Agent (parallel) 
   - Market Research Agent (parallel)
   - Website Generation Agent (parallel)

3. Result Consolidation Layer (Bottom):
   - Collects results as agents complete
   - Handles partial results and failures gracefully
   - Provides consolidated final results

Key Benefits:
- TRUE PARALLELISM: All agents run simultaneously
- NO BLOCKING: Logo generation doesn't block branding
- CLEAN HITL: Human approval at orchestrator level only
- GRACEFUL FAILURES: Partial results if some agents fail
- REAL-TIME PROGRESS: See results as they complete
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.langgraph.parallel_intelligent_graph import (
    create_parallel_intelligent_workflow,
    ParallelWorkflowState
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simple_approval_callback(approval_request: dict) -> dict:
    """
    Simple approval callback for demo purposes.
    In production, this would integrate with your UI/notification system.
    """
    print("\n" + "="*60)
    print("🤖 HUMAN APPROVAL REQUIRED")
    print("="*60)
    print(f"Workflow ID: {approval_request.get('workflow_id')}")
    print(f"Request: {approval_request.get('user_request')}")
    print(f"Required Agents: {', '.join(approval_request.get('required_agents', []))}")
    print(f"Estimated Duration: {approval_request.get('estimated_duration', 0)} seconds")
    print(f"Risk Level: {approval_request.get('risk_assessment', {}).get('level', 'unknown')}")
    
    risk_factors = approval_request.get('risk_assessment', {}).get('factors', [])
    if risk_factors:
        print("Risk Factors:")
        for factor in risk_factors:
            print(f"  ⚠️  {factor}")
    
    print("\nApprove this execution? (y/n): ", end="", flush=True)
    
    # For demo, auto-approve after showing the request
    import time
    time.sleep(2)  # Give user time to read
    print("y (auto-approved for demo)")
    
    return {
        "approved": True,
        "method": "demo_callback",
        "reason": "Auto-approved for demonstration",
        "timestamp": datetime.utcnow().isoformat(),
        "reviewer": "demo_system"
    }


async def demo_parallel_workflow(user_request: str, show_approval: bool = True):
    """Demonstrate the parallel intelligent workflow."""
    
    print(f"\n🚀 Starting Hierarchical Parallel Workflow Demo")
    print(f"Request: {user_request}")
    print("="*80)
    
    try:
        # Create the workflow system
        approval_callback = simple_approval_callback if show_approval else None
        app, persistent_system, workflow_brain = await create_parallel_intelligent_workflow(
            skip_approvals=not show_approval,
            approval_callback=approval_callback
        )
        
        # Create initial workflow state
        initial_state = ParallelWorkflowState(
            workflow_id=f"demo_{int(datetime.utcnow().timestamp())}",
            session_id="demo_session",
            user_request=user_request
        )
        
        print("✅ Workflow system initialized")
        print("🧠 Starting Intelligence Orchestrator...")
        
        # Execute the workflow
        start_time = datetime.utcnow()
        
        # Create config with thread_id for checkpointer and increased limits
        config = {
            "configurable": {
                "thread_id": f"thread_{initial_state.workflow_id}",
                "checkpoint_ns": "parallel_workflow"
            },
            "recursion_limit": 50,  # Increase recursion limit for complex workflows
            "max_execution_time": 300  # 5 minute max execution time
        }
        
        # Initialize final_state
        final_state = {}
        
        # Stream execution progress  
        async for state_update in app.astream(initial_state.__dict__, config=config):
            final_state = state_update  # Always update final state
            
            # Show raw state for now to debug
            print(f"\n📊 Status: {state_update.get('overall_status', 'unknown')}")
            
            # Try to extract key information without full state reconstruction
            if state_update.get('agent_statuses'):
                print("🤖 Agent Status:")
                for agent, status in state_update.get('agent_statuses', {}).items():
                    emoji = "✅" if status == "completed" else "⏳" if status == "running" else "❌"
                    print(f"   {emoji} {agent}: {status}")
            
            # Show progress if available
            progress = state_update.get('progress_percentage', 0)
            if progress > 0:
                print(f"📈 Progress: {progress:.1f}%")
            
            # Show any errors
            errors = state_update.get('errors', [])
            if errors:
                for error in errors[-1:]:  # Latest error
                    print(f"❌ Error: {error}")
            
            # Show execution plan if available
            execution_plan = state_update.get('execution_plan', {})
            if execution_plan and execution_plan.get('required_agents'):
                agents = execution_plan['required_agents']
                print(f"🎯 Required Agents: {', '.join(agents)}")
            
            # Break if completed or failed
            status = state_update.get('overall_status', '')
            if status in ["completed", "failed", "cancelled"]:
                print(f"🎯 Workflow Status: {status.upper()}")
                break
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Show final results
        print("\n" + "="*80)
        print("🎉 WORKFLOW COMPLETED")
        print("="*80)
        print(f"⏱️  Total Execution Time: {execution_time:.1f} seconds")
        print(f"📊 Overall Status: {final_state.get('overall_status', 'unknown')}")
        print(f"✅ Successful Agents: {len(final_state.get('completed_agents', []))}")
        print(f"❌ Failed Agents: {len(final_state.get('failed_agents', []))}")
        
        if final_state.get('completed_agents'):
            print("\n🎯 Completed Agents:")
            for agent in final_state.get('completed_agents', []):
                print(f"   ✅ {agent}")
                # Show key results
                agent_results = final_state.get('agent_results', {})
                result = agent_results.get(agent, {})
                if isinstance(result, dict):
                    # Show some key outputs
                    if agent == "branding" and "brand_names" in result:
                        names = result.get("brand_names", [])[:3]  # First 3
                        print(f"      📝 Generated names: {names}")
                    elif agent == "logo_generation" and "logo_images" in result:
                        images = result.get("logo_images", [])
                        print(f"      🎨 Generated {len(images)} logo image(s)")
                    elif agent == "market_research" and "market_analysis" in result:
                        print(f"      📊 Market analysis completed")
                    elif agent == "website_generation" and "website_structure" in result:
                        print(f"      🌐 Website structure created")
        
        if final_state.get('failed_agents'):
            print("\n❌ Failed Agents:")
            for agent in final_state.get('failed_agents', []):
                agent_errors = final_state.get('agent_errors', {})
                error = agent_errors.get(agent, "Unknown error")
                print(f"   ❌ {agent}: {error}")
        
        # Show artifacts (file paths, URLs, etc.)
        final_results = final_state.get('final_results', {})
        if final_results and final_results.get("artifacts"):
            print("\n📁 Generated Artifacts:")
            for artifact_name, artifact_path in final_results["artifacts"].items():
                print(f"   📄 {artifact_name}: {artifact_path}")
        
        # Show recommendations
        if final_results and final_results.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in final_results["recommendations"][:3]:  # Top 3
                print(f"   💡 {rec}")
        
        print("\n" + "="*80)
        
        # Cleanup
        await persistent_system.stop()
        
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        print(f"\n❌ Workflow execution failed: {e}")
        return None


async def demo_scenarios():
    """Run multiple demo scenarios to show different capabilities."""
    
    scenarios = [
        {
            "name": "Comprehensive Business Branding (All Agents)",
            "request": "Create a complete brand identity, logo, market analysis, and website for a modern coffee shop startup",
            "show_approval": True
        },
        {
            "name": "Branding + Logo Generation (Parallel)",
            "request": "Generate brand name and logo for TechFlow - a software development consultancy",
            "show_approval": False
        },
        {
            "name": "Market Research + Website (Business Focus)",
            "request": "Research the fitness app market and create a landing page for a new workout tracking app",
            "show_approval": False
        },
        {
            "name": "Logo-only Request (Single Agent)",
            "request": "Generate a logo for GreenLeaf - an eco-friendly packaging company",
            "show_approval": False
        }
    ]
    
    print("🎭 HIERARCHICAL PARALLEL WORKFLOW DEMO SUITE")
    print("=" * 80)
    print("This demo shows how the new system handles different types of requests:")
    print("• Intelligent routing to appropriate agents")
    print("• True parallel execution (no blocking)")
    print("• Clean human approval at orchestrator level")
    print("• Graceful handling of partial failures")
    print("• Real-time progress updates")
    print()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}/{len(scenarios)}: {scenario['name']}")
        print("-" * 60)
        
        # Run the scenario
        result = await demo_parallel_workflow(
            scenario["request"], 
            scenario["show_approval"]
        )
        
        if result and result.overall_status == "completed":
            print(f"✅ Scenario {i} completed successfully!")
        else:
            print(f"❌ Scenario {i} had issues")
        
        if i < len(scenarios):
            print("\n⏳ Waiting 3 seconds before next scenario...")
            await asyncio.sleep(3)
    
    print(f"\n🎉 Demo completed! All scenarios finished.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hierarchical Parallel Intelligence LangGraph Demo")
    parser.add_argument("--request", type=str, help="Custom user request to test")
    parser.add_argument("--approval", action="store_true", help="Enable human approval demo")
    parser.add_argument("--scenarios", action="store_true", help="Run all demo scenarios")
    
    args = parser.parse_args()
    
    if args.scenarios:
        # Run all demo scenarios
        asyncio.run(demo_scenarios())
    elif args.request:
        # Run single custom request
        asyncio.run(demo_parallel_workflow(args.request, args.approval))
    else:
        # Default: comprehensive business branding demo
        default_request = "Create complete branding, logo, and market analysis for a sustainable fashion startup called EcoThreads"
        print("Running default comprehensive demo...")
        print("To run custom requests: python demo_parallel_intelligent_workflow.py --request 'your request here'")
        print("To see all scenarios: python demo_parallel_intelligent_workflow.py --scenarios")
        print()
        asyncio.run(demo_parallel_workflow(default_request, show_approval=True))