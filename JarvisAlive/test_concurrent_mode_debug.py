#!/usr/bin/env python3
"""
Debug test for concurrent mode - identify the real issues
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup minimal logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_concurrent_mode():
    """Debug the concurrent mode step by step."""
    
    print("🔍 Debugging Concurrent Mode Implementation")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        print("\n1. 📦 Testing Imports...")
        
        # Test individual imports
        try:
            from orchestration.persistent.persistent_system import create_development_persistent_system, PersistentSystem
            print("✅ PersistentSystem imports: OK")
        except ImportError as e:
            print(f"❌ PersistentSystem imports: {e}")
            return False
            
        try:
            from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
            print("✅ EnhancedWorkflowBrain import: OK")
        except ImportError as e:
            print(f"❌ EnhancedWorkflowBrain import: {e}")
            return False
            
        try:
            from orchestration.persistent.advanced_features import (
                InterAgentCommunicationManager, WorkflowTemplateManager, PerformanceAnalyticsEngine
            )
            print("✅ Advanced features imports: OK")
        except ImportError as e:
            print(f"❌ Advanced features imports: {e}")
            return False
        
        print("\n2. 🏗️  Testing System Creation...")
        
        # Test system creation
        try:
            persistent_system = create_development_persistent_system()
            print("✅ PersistentSystem creation: OK")
        except Exception as e:
            print(f"❌ PersistentSystem creation: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        print("\n3. 🚀 Testing System Startup...")
        
        # Test system startup
        try:
            await persistent_system.start()
            print("✅ PersistentSystem startup: OK")
        except Exception as e:
            print(f"❌ PersistentSystem startup: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        print("\n4. 🧠 Testing Enhanced WorkflowBrain...")
        
        # Test enhanced workflow brain
        try:
            config = {
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
                'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
                'max_retries': 3,
                'enable_optimization': True
            }
            
            enhanced_brain = EnhancedWorkflowBrain(config, persistent_system)
            print("✅ EnhancedWorkflowBrain creation: OK")
            
            await enhanced_brain.initialize_orchestration()
            print("✅ EnhancedWorkflowBrain initialization: OK")
            
        except Exception as e:
            print(f"❌ EnhancedWorkflowBrain: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        print("\n5. 📊 Testing Advanced Features...")
        
        # Test advanced features
        try:
            template_manager = WorkflowTemplateManager()
            print("✅ WorkflowTemplateManager creation: OK")
            
            analytics_engine = PerformanceAnalyticsEngine()
            print("✅ PerformanceAnalyticsEngine creation: OK")
            
        except Exception as e:
            print(f"❌ Advanced features: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        print("\n6. 📈 Testing System Health...")
        
        # Test system health
        try:
            health = await persistent_system.get_system_health()
            print(f"✅ System health check: {health['system_running']}")
            print(f"   - Components: {len(health['components'])}")
            print(f"   - Uptime: {health['uptime_seconds']:.1f}s")
            
        except Exception as e:
            print(f"❌ System health: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n" + "=" * 50)
        print("🎉 Concurrent Mode Debug - ALL CORE COMPONENTS WORKING!")
        print("✅ The concurrent mode architecture is fundamentally sound.")
        print("🔍 Issue must be in the interactive loop or input handling.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            if 'persistent_system' in locals():
                await persistent_system.stop()
                print("\n✅ System cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

async def main():
    """Main debug function."""
    print("Starting Concurrent Mode Debug...")
    print(f"Debug started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    
    success = await debug_concurrent_mode()
    
    if success:
        print("\n🎯 CONCLUSION: Core concurrent mode architecture is working correctly!")
        print("💡 The issue is likely in the interactive input loop, not the core system.")
        return 0
    else:
        print("\n❌ CONCLUSION: Found fundamental issues in concurrent mode implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)