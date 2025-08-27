#!/usr/bin/env python3
"""
Simplified Jarvis Demo Starter

Runs the backend server directly without React build,
providing API access and fallback HTML interface.
"""

import os
import sys
from pathlib import Path

def main():
    """Start the Jarvis demo backend directly."""
    print("=" * 60)
    print("🚀 JARVIS COFFEE SHOP DEMO SYSTEM (Backend)")
    print("=" * 60)
    print("")
    print("🎯 Demo Features:")
    print("  - Coffee shop creation API endpoints")
    print("  - Real-time agent coordination (Alfred, Edith, Jarvis)")  
    print("  - Domain selection and logo generation")
    print("  - WebSocket real-time updates")
    print("  - Complete orchestration system")
    print("")
    print("📱 Access points:")
    print("  - Main UI: http://localhost:8000")
    print("  - API docs: http://localhost:8000/docs")  
    print("  - WebSocket test: ws://localhost:8000/ws/demo_session")
    print("")
    print("🎬 Demo trigger phrase:")
    print("   'HeyJarvis I want to create a Coffee Shop'")
    print("")
    print("🚀 Starting backend server...")
    print("")
    
    # Change to the script directory  
    os.chdir(Path(__file__).parent)
    
    # Import and run the frontend server
    try:
        from frontend_server import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import backend modules: {e}")
        print("Make sure you're in the JarvisAlive directory and all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

if __name__ == "__main__":
    main() 