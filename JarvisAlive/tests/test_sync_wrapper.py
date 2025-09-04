#!/usr/bin/env python3
"""Test the sync wrapper approach for OpenAI."""

import asyncio
import os
from dotenv import load_dotenv

async def test_sync_wrapper():
    load_dotenv()
    
    try:
        from openai import OpenAI
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ No API key")
            return
            
        print("✅ Creating sync client...")
        sync_client = OpenAI(api_key=api_key)
        print("✅ Sync client created successfully")
        
        # Create async wrapper
        class AsyncOpenAIWrapper:
            def __init__(self, sync_client):
                self.sync_client = sync_client
                self._executor = ThreadPoolExecutor(max_workers=2)
                
            @property
            def images(self):
                return AsyncImageWrapper(self.sync_client.images, self._executor)
        
        class AsyncImageWrapper:
            def __init__(self, sync_images, executor):
                self.sync_images = sync_images
                self.executor = executor
                
            async def generate(self, **kwargs):
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor, 
                    lambda: self.sync_images.generate(**kwargs)
                )
        
        async_client = AsyncOpenAIWrapper(sync_client)
        print("✅ Async wrapper created")
        
        # Test image generation
        print("🎨 Generating test image...")
        response = await async_client.images.generate(
            model="dall-e-3",
            prompt="A simple red circle on white background, clean minimalist design",
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        print(f"✅ SUCCESS! Generated {len(response.data)} logo images")
        for i, img in enumerate(response.data, 1):
            print(f"  Image {i}: {img.url}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync_wrapper())