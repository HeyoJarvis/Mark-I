#!/usr/bin/env python3
"""Demo of the interactive logo prompt approval system."""

import asyncio
import os
import sys
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent

console = Console()

async def demo_interactive_approval():
    """
    Demo the interactive logo prompt approval.
    
    This will show:
    1. Generated logo prompt
    2. Interactive approval interface 
    3. NLP parsing of user responses
    4. Different response handling (yes/no/try again)
    """
    console.print("🎨 [bold blue]Interactive Logo Prompt Approval Demo[/bold blue]")
    console.print("=" * 60)
    
    console.print("""
🎯 [bold yellow]What this demo shows:[/bold yellow]
• Generated logo prompt displayed clearly
• Interactive approval interface with options
• NLP parsing of your responses (yes, no, try again)  
• Regeneration of new prompts when requested
• Professional user experience

🎮 [bold green]Try different responses like:[/bold green]
• "yes" or "looks good" → Approve the prompt
• "no" or "skip" → Skip logo generation
• "try again" or "redo" → Generate a new prompt variation
• "maybe" → See clarification request
    
Press Enter to start the demo...
    """)
    input()
    
    try:
        # Initialize branding agent 
        branding_agent = BrandingAgent(config={
            'interactive_approval': True
        })
        
        # Demo business
        demo_state = {
            'business_idea': 'A premium artisanal coffee roastery specializing in single-origin beans with a cozy cafe atmosphere for creative professionals',
            'user_request': 'Create a brand identity and logo for my coffee business',
            'target_audience': 'creative professionals, coffee connoisseurs, remote workers'
        }
        
        console.print("☕ [bold]Demo Business:[/bold]")
        console.print(f"   {demo_state['business_idea']}")
        console.print()
        
        # Run the branding workflow with interactive approval
        result = await branding_agent.run(demo_state)
        
        # Show final results
        console.print("\n" + "="*60)
        console.print("🎉 [bold green]Demo Complete - Final Results:[/bold green]")
        console.print("="*60)
        
        console.print(f"✅ Success: {result.get('branding_success', False)}")
        console.print(f"🏢 Brand Name: {result.get('brand_name', 'N/A')}")
        console.print(f"🎨 Colors: {', '.join(result.get('color_palette', []))}")
        
        final_prompt = result.get('logo_prompt', '')
        if final_prompt:
            console.print(f"\n📝 [bold green]Your Approved Logo Prompt:[/bold green]")
            console.print(f"   📄 {final_prompt}")
            console.print(f"\n💡 [yellow]This prompt can now be used with:[/yellow]")
            console.print(f"   • DALL-E, Midjourney, or other AI image generators")
            console.print(f"   • Graphic designers for logo creation")
            console.print(f"   • The LogoGenerationAgent in this system")
        else:
            console.print(f"\n❌ [red]Logo generation was skipped (you chose not to proceed)[/red]")
        
        console.print(f"\n🎊 [bold blue]Interactive approval system successfully demonstrated![/bold blue]")
        
    except KeyboardInterrupt:
        console.print(f"\n\n👋 Demo interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_interactive_approval())