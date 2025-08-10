#!/usr/bin/env python3
"""Debug OpenAI client initialization."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import AsyncOpenAI
    print("✅ OpenAI import successful")
    
    # Check constructor signature
    import inspect
    sig = inspect.signature(AsyncOpenAI.__init__)
    print("\nAsyncOpenAI constructor parameters:")
    for name, param in sig.parameters.items():
        if name != 'self':
            print(f"  {name}: {param}")
    
    # Try basic initialization
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"\n✅ API key found: {api_key[:10]}...")
        try:
            client = AsyncOpenAI(api_key=api_key)
            print("✅ AsyncOpenAI client created successfully")
        except Exception as e:
            print(f"❌ AsyncOpenAI creation failed: {e}")
    else:
        print("❌ No OPENAI_API_KEY found")
        
except ImportError as e:
    print(f"❌ OpenAI import failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")