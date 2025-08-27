#!/usr/bin/env python3
"""
Start Demo Script for Jarvis Coffee Shop Demo

This script builds the React frontend and starts the complete demo system
connecting the sophisticated React UI to the backend orchestration system.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors gracefully."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd.split(), 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def build_react_frontend():
    """Build the React frontend for production."""
    frontend_path = Path(__file__).parent / "frontend-react" / "tmpapp"
    
    print("🔨 Building React frontend...")
    
    if not frontend_path.exists():
        print(f"❌ Frontend directory not found: {frontend_path}")
        return False
    
    # Install dependencies
    print("📦 Installing React dependencies...")
    if not run_command("npm install", cwd=frontend_path):
        print("❌ Failed to install dependencies")
        return False
    
    # Build production version
    print("🏗️ Building production version...")
    if not run_command("npm run build", cwd=frontend_path):
        print("❌ Failed to build React app")
        return False
    
    print("✅ React frontend built successfully!")
    return True

def start_backend():
    """Start the backend server."""
    print("🚀 Starting Jarvis Demo Backend...")
    
    # Import and run the frontend server
    try:
        from frontend_server import app
        import uvicorn
        
        print("🎯 Demo Features:")
        print("  - Coffee shop creation with voice input")
        print("  - Real-time agent coordination (Alfred, Edith, Jarvis)")
        print("  - 3D office view with agent activities")
        print("  - Domain selection and logo generation")
        print("  - Website creation and deployment")
        print("  - WebSocket real-time updates")
        print("")
        print("📱 Access the demo at: http://localhost:8000")
        print("🔗 API docs at: http://localhost:8000/docs")
        print("")
        print("🎬 To trigger the demo, say or type:")
        print("   'HeyJarvis I want to create a Coffee Shop'")
        print("")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import backend modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def main():
    """Main demo startup function."""
    print("=" * 60)
    print("🚀 JARVIS COFFEE SHOP DEMO SYSTEM")
    print("=" * 60)
    print("")
    
    # Change to the script directory
    os.chdir(Path(__file__).parent)
    
    # Build React frontend
    if not build_react_frontend():
        print("❌ Frontend build failed. The demo will run with a fallback UI.")
        print("   You can still access API endpoints at http://localhost:8000/docs")
    
    # Start backend
    print("")
    print("🎯 Starting integrated demo system...")
    start_backend()

if __name__ == "__main__":
    main() 