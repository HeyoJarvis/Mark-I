#!/usr/bin/env python3
"""
Test script to verify Anthropic API key functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anthropic_api():
    """Test the Anthropic API key"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}")
    print(f"   Length: {len(api_key)} characters")
    
    try:
        # Try to import and test anthropic
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        print("🧪 Testing API call...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say hello in exactly 3 words"}
            ]
        )
        
        print(f"✅ API Test Successful!")
        print(f"   Response: {response.content[0].text}")
        return True
        
    except ImportError:
        print("❌ Anthropic library not installed. Installing...")
        os.system("pip install anthropic")
        return test_anthropic_api()  # Retry after install
        
    except anthropic.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("   This suggests the API key is invalid or expired")
        return False
        
    except anthropic.PermissionDeniedError as e:
        print(f"❌ Permission Denied: {e}")
        print("   This suggests the API key doesn't have required permissions")
        return False
        
    except anthropic.BadRequestError as e:
        print(f"❌ Bad Request: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Anthropic API Key...")
    print("=" * 50)
    
    success = test_anthropic_api()
    
    print("=" * 50)
    if success:
        print("🎉 API key is working correctly!")
    else:
        print("💥 API key test failed - please check your key")
        
    sys.exit(0 if success else 1)