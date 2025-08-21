#!/usr/bin/env python3
"""
Debug script to identify x-api-key issues in the Anthropic engine
"""

import os
import sys
import json
from typing import Dict, Any

# Add the JarvisAlive path
sys.path.append('/home/sdalal/test/ProjectMarmalade/JarvisAlive')

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

def check_api_key_format(api_key: str) -> Dict[str, Any]:
    """Check if the API key has the correct format."""
    results = {
        'is_valid_format': False,
        'issues': [],
        'format_check': {}
    }
    
    if not api_key:
        results['issues'].append("API key is None or empty")
        return results
    
    # Check format
    if not isinstance(api_key, str):
        results['issues'].append(f"API key should be string, got {type(api_key)}")
        return results
    
    results['format_check']['length'] = len(api_key)
    results['format_check']['starts_with_correct_prefix'] = api_key.startswith('sk-ant-api03-')
    results['format_check']['has_sufficient_length'] = len(api_key) > 50
    
    if not api_key.startswith('sk-ant-api03-'):
        results['issues'].append("API key should start with 'sk-ant-api03-'")
    
    if len(api_key) < 50:
        results['issues'].append(f"API key seems too short (length: {len(api_key)})")
    
    if len(results['issues']) == 0:
        results['is_valid_format'] = True
    
    return results

def test_anthropic_configuration():
    """Test different ways the Anthropic engine gets configured."""
    print("🔍 Debugging Anthropic API Key Configuration")
    print("=" * 50)
    
    # 1. Check environment variable
    print("\n1. Environment Variable Check:")
    env_key = os.getenv('ANTHROPIC_API_KEY')
    if env_key:
        key_check = check_api_key_format(env_key)
        print(f"   ✅ ANTHROPIC_API_KEY found in environment")
        print(f"   📏 Length: {len(env_key)}")
        print(f"   🔑 Starts correctly: {env_key.startswith('sk-ant-api03-')}")
        print(f"   📝 Preview: {env_key[:15]}...{env_key[-8:]}")
        
        if not key_check['is_valid_format']:
            print(f"   ❌ Issues: {', '.join(key_check['issues'])}")
        else:
            print(f"   ✅ Format appears valid")
    else:
        print(f"   ❌ ANTHROPIC_API_KEY not found in environment")
    
    # 2. Test engine configuration
    print("\n2. Engine Configuration Test:")
    try:
        if env_key:
            config = AIEngineConfig(
                api_key=env_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7
            )
            
            engine = AnthropicEngine(config)
            print(f"   ✅ Engine created successfully")
            print(f"   🔧 Model: {config.model}")
            print(f"   🌡️  Temperature: {config.temperature}")
            
            # Test header preparation
            headers = engine._prepare_headers()
            print(f"   🔗 Headers prepared: {list(headers.keys())}")
            
            if 'x-api-key' in headers:
                header_key = headers['x-api-key']
                if header_key == env_key:
                    print(f"   ✅ x-api-key header matches environment variable")
                else:
                    print(f"   ❌ x-api-key header doesn't match environment variable")
            else:
                print(f"   ❌ x-api-key not found in headers")
                
        else:
            print(f"   ⏭️  Skipping - no API key available")
            
    except Exception as e:
        print(f"   ❌ Engine configuration failed: {e}")
    
    # 3. Test mock configuration
    print("\n3. Mock Configuration Test:")
    try:
        mock_config = AIEngineConfig(
            api_key=None,  # No API key for mock mode
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.7
        )
        
        mock_engine = AnthropicEngine(mock_config)
        print(f"   ✅ Mock engine created successfully")
        print(f"   🎭 This should work without API key for testing")
        
    except Exception as e:
        print(f"   ❌ Mock configuration failed: {e}")
    
    # 4. Quick API test (if key available)
    print("\n4. Quick API Test:")
    if env_key and check_api_key_format(env_key)['is_valid_format']:
        try:
            config = AIEngineConfig(
                api_key=env_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                temperature=0.1
            )
            
            engine = AnthropicEngine(config)
            
            # This would make an actual API call
            print(f"   🧪 Testing with simple prompt...")
            print(f"   ⚠️  Note: This will make a real API call if key is valid")
            
            # Uncomment to test actual API call:
            # result = await engine.generate_response("Hello, please respond with just 'API test successful'")
            # print(f"   ✅ API Response: {result[:50]}...")
            
        except Exception as e:
            print(f"   ❌ API test setup failed: {e}")
    else:
        print(f"   ⏭️  Skipping - invalid or missing API key")
    
    print("\n" + "=" * 50)
    print("🎯 **Recommendations:**")
    
    if not env_key:
        print("1. Set your API key: export ANTHROPIC_API_KEY='sk-ant-api03-...'")
    elif not check_api_key_format(env_key)['is_valid_format']:
        print("1. Check your API key format - should start with 'sk-ant-api03-'")
        print("2. Verify you copied the full key from Anthropic Console")
    else:
        print("1. API key format looks good!")
        print("2. If still getting errors, check network connectivity")
        print("3. Verify the API key is active in Anthropic Console")
    
    print("4. For testing without API key, the system supports mock mode")
    print("5. Check the full error traceback for more specific details")

if __name__ == "__main__":
    test_anthropic_configuration() 