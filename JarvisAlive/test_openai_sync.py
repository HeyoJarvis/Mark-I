#!/usr/bin/env python3
"""Test OpenAI with synchronous client."""

import os

def test_openai_sync():
    try:
        from openai import OpenAI
        print("✅ Import successful")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ No API key")
            return
            
        print(f"✅ API key: {api_key[:10]}...")
        
        # Try synchronous client
        client = OpenAI(api_key=api_key)
        print("✅ Sync client created")
        
        # Try a simple API call
        response = client.images.generate(
            model="dall-e-3",
            prompt="A simple red circle on white background",
            size="1024x1024",
            quality="standard",
            n=1
        )
        print(f"✅ API call successful: {len(response.data)} images generated")
        for img in response.data:
            print(f"  Image URL: {img.url}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_openai_sync()