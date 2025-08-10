#!/usr/bin/env python3
"""Debug logo generation results to see what's in the response."""

import asyncio
import os
import sys
import json
from rich.console import Console

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.universal_orchestrator import UniversalOrchestrator, UniversalOrchestratorConfig

console = Console()

async def debug_logo_results():
    """Debug the exact contents of logo generation results."""
    try:
        config = UniversalOrchestratorConfig(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6380')
        )
        
        orchestrator = UniversalOrchestrator(config)
        await orchestrator.initialize()
        
        # Test logo generation request
        result = await orchestrator.process_query(
            user_query="Generate a logo for my bakery called Sweet Dreams",
            session_id="debug_session"
        )
        
        # Print raw result structure
        print("=== RAW RESULT STRUCTURE ===")
        print(json.dumps(result, indent=2, default=str))
        
        # Check specific fields
        print("\n=== LOGO GENERATION FIELDS ===")
        print(f"logo_generation key exists: {'logo_generation' in result}")
        print(f"logo_urls key exists: {'logo_urls' in result}")
        print(f"logo_images key exists: {'logo_images' in result}")
        
        if 'logo_generation' in result:
            logo_gen = result['logo_generation']
            print(f"logo_generation content: {logo_gen}")
            print(f"attempted: {logo_gen.get('attempted', 'NOT FOUND')}")
            print(f"success: {logo_gen.get('success', 'NOT FOUND')}")
            
        # Look in orchestrator_response for nested data
        if 'orchestrator_response' in result:
            orch_resp = result['orchestrator_response']
            print(f"\n=== ORCHESTRATOR_RESPONSE ===")
            print(f"Type: {type(orch_resp)}")
            if isinstance(orch_resp, dict):
                print("Keys:", list(orch_resp.keys()))
                print(f"logo_generation in orch_resp: {'logo_generation' in orch_resp}")
                print(f"logo_urls in orch_resp: {'logo_urls' in orch_resp}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await orchestrator.close()
        except:
            pass

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_logo_results())