#!/usr/bin/env python3
"""Test all exit command levels in the interactive approval system."""

import asyncio
import os
import sys
from rich.console import Console
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent, AgentExitException, SystemExitException

console = Console()

async def test_exit_commands():
    """Test all different exit command levels."""
    console.print("🚪 [bold blue]Testing All Exit Command Levels[/bold blue]")
    console.print("=" * 60)
    
    test_state = {
        'business_idea': 'A modern coffee shop with co-working space',
        'user_request': 'Create a brand with logo'
    }
    
    exit_scenarios = [
        {
            'name': 'Skip Logo Generation',
            'command': 'no',
            'expected': 'logo_skipped',
            'description': 'Skips logo generation entirely, continues with branding'
        },
        {
            'name': 'Exit Prompt (Use Original)',
            'command': 'exit prompt',
            'expected': 'original_prompt_used',
            'description': 'Exits approval loop, uses original prompt'
        },
        {
            'name': 'Exit Agent',
            'command': 'exit agent',
            'expected': 'agent_exit',
            'description': 'Exits branding agent completely'
        },
        {
            'name': 'Quit System',
            'command': 'quit',
            'expected': 'system_exit',
            'description': 'Quits entire HeyJarvis system'
        },
        {
            'name': 'Normal Approval',
            'command': 'yes',
            'expected': 'approved',
            'description': 'Normal workflow - approves logo prompt'
        }
    ]
    
    for scenario in exit_scenarios:
        console.print(f"\n📋 [bold yellow]Testing: {scenario['name']}[/bold yellow]")
        console.print(f"   Command: [cyan]'{scenario['command']}'[/cyan]")
        console.print(f"   Expected: {scenario['description']}")
        
        try:
            # Create fresh agent for each test
            agent = BrandingAgent(config={'interactive_approval': True})
            
            # Mock the user input
            with patch('rich.prompt.Prompt.ask', return_value=scenario['command']):
                result = await agent.run(test_state)
            
            # Check results
            if scenario['expected'] == 'logo_skipped':
                logo_prompt = result.get('logo_prompt', '')
                if not logo_prompt:
                    console.print("   ✅ [green]PASS - Logo generation skipped[/green]")
                else:
                    console.print("   ❌ [red]FAIL - Expected no logo prompt[/red]")
                    
            elif scenario['expected'] == 'original_prompt_used':
                logo_prompt = result.get('logo_prompt', '')
                if logo_prompt and 'modern, professional logo' in logo_prompt:
                    console.print("   ✅ [green]PASS - Original prompt used[/green]")
                else:
                    console.print("   ❌ [red]FAIL - Expected original prompt[/red]")
                    
            elif scenario['expected'] == 'agent_exit':
                if result.get('agent_exit_requested'):
                    console.print("   ✅ [green]PASS - Agent exit flag set[/green]")
                else:
                    console.print("   ❌ [red]FAIL - Expected agent exit flag[/red]")
                    
            elif scenario['expected'] == 'system_exit':
                if result.get('system_exit_requested'):
                    console.print("   ✅ [green]PASS - System exit flag set[/green]")
                else:
                    console.print("   ❌ [red]FAIL - Expected system exit flag[/red]")
                    
            elif scenario['expected'] == 'approved':
                logo_prompt = result.get('logo_prompt', '')
                if logo_prompt:
                    console.print("   ✅ [green]PASS - Logo prompt approved[/green]")
                else:
                    console.print("   ❌ [red]FAIL - Expected approved prompt[/red]")
                    
        except AgentExitException:
            if scenario['expected'] == 'agent_exit':
                console.print("   ✅ [green]PASS - AgentExitException caught[/green]")
            else:
                console.print("   ❌ [red]FAIL - Unexpected AgentExitException[/red]")
                
        except SystemExitException:
            if scenario['expected'] == 'system_exit':
                console.print("   ✅ [green]PASS - SystemExitException caught[/green]")
            else:
                console.print("   ❌ [red]FAIL - Unexpected SystemExitException[/red]")
                
        except Exception as e:
            console.print(f"   ❌ [red]ERROR - {e}[/red]")
    
    console.print(f"\n🎉 [bold green]All exit command tests completed![/bold green]")

def show_exit_command_reference():
    """Show reference for all available exit commands."""
    console.print(f"\n" + "="*60)
    console.print("📖 [bold blue]Exit Command Reference[/bold blue]")
    console.print("=" * 60)
    
    commands = [
        ("🔄 [green]Normal Commands[/green]", [
            ("yes, looks good, perfect", "Approve and proceed with logo generation"),
            ("no, skip", "Skip logo generation entirely"),
            ("try again, redo", "Generate a new logo prompt variation"),
        ]),
        ("🚪 [yellow]Exit Commands[/yellow]", [
            ("exit prompt, exit", "Use original prompt and continue"),
            ("exit agent, quit agent", "Quit branding agent completely"),
            ("quit, quit system", "Quit entire HeyJarvis system"),
        ]),
    ]
    
    for category, command_list in commands:
        console.print(f"\n{category}")
        for cmd, desc in command_list:
            console.print(f"  • [cyan]{cmd}[/cyan] → {desc}")
    
    console.print(f"\n💡 [yellow]Notes:[/yellow]")
    console.print("• Commands are case-insensitive")
    console.print("• No timeout - you can regenerate as many times as needed")
    console.print("• Exit commands provide clean workflow termination")
    console.print("• System maintains state for orchestrator handling")

if __name__ == "__main__":
    async def run_all_tests():
        await test_exit_commands()
        show_exit_command_reference()
    
    asyncio.run(run_all_tests())