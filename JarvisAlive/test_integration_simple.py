#!/usr/bin/env python3
"""
Test integration with existing system
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_integration import SemanticJarvis, SemanticMigrationManager
from ai_engines.mock_engine import MockAIEngine


async def test_integration():
    """Test how semantic architecture integrates with existing system."""
    print("🔗 Testing Semantic Integration")
    print("=" * 40)
    
    # Create semantic jarvis
    jarvis = SemanticJarvis(MockAIEngine())
    migration_manager = SemanticMigrationManager()
    
    test_requests = [
        "Create a logo for my coffee shop",
        "Research market trends for electric vehicles",
        "Build a complete brand package with website"
    ]
    
    for request in test_requests:
        print(f"\n📋 Request: {request}")
        
        # Test semantic approach
        semantic_result = await jarvis.process_request(request, "test_session")
        print(f"  🔵 Semantic: {semantic_result['success']} - {semantic_result['method']}")
        print(f"     Agents: {semantic_result.get('agents_used', [])}")
        
        # Test legacy fallback
        legacy_result = await jarvis.process_request(request, "test_session", use_legacy=True)
        print(f"  🔴 Legacy: {legacy_result['success']} - {legacy_result['method']}")
        
        # Record stats
        await migration_manager.record_request_outcome("semantic", semantic_result['success'])
        await migration_manager.record_request_outcome("legacy", legacy_result['success'])
    
    # Show migration stats
    stats = await migration_manager.get_migration_stats()
    print(f"\n📊 Migration Stats:")
    print(f"  Semantic: {stats['semantic_requests']} requests, {stats['semantic_success_rate']:.1%} success")
    print(f"  Legacy: {stats['legacy_requests']} requests, {stats['legacy_success_rate']:.1%} success")

if __name__ == "__main__":
    asyncio.run(test_integration())