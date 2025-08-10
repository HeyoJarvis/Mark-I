"""
LogoGenerationAgent - DALL-E powered logo image generation

This agent takes logo design prompts and generates actual logo images using OpenAI's DALL-E API.
Works in coordination with the BrandingAgent to provide complete brand visualization.
"""

import base64
import logging
import os
import uuid
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from io import BytesIO

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class LogoImage:
    """Generated logo image data."""
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # base64 encoded
    filename: str = ""
    local_path: str = ""  # Local file path where image is saved
    prompt_used: str = ""
    style: str = ""
    dimensions: str = "1024x1024"


@dataclass
class LogoGenerationResult:
    """Result of logo generation."""
    success: bool
    brand_name: str
    logo_images: List[LogoImage]
    original_prompt: str
    enhanced_prompt: str
    generation_time_ms: int
    error_message: Optional[str] = None
    suggestions: List[str] = None


class LogoGenerationAgent:
    """
    AI agent for generating actual logo images using DALL-E.
    
    Takes logo design prompts from BrandingAgent and generates visual logos.
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LogoGenerationAgent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        self.use_real_dalle = False  # Will be set to True if real client works
        self._initialize_openai_client()
        
        # Configuration
        self.max_images = self.config.get('max_images', 3)
        self.image_size = self.config.get('image_size', '1024x1024')
        self.quality = self.config.get('quality', 'standard')  # standard or hd
        self.style = self.config.get('style', 'vivid')  # natural or vivid
        
        # Logo storage configuration
        self.logos_dir = Path(self.config.get('logos_dir', './generated_logos'))
        self.logos_dir.mkdir(exist_ok=True)
        
        self.logger.info("LogoGenerationAgent initialized successfully")
    
    def _initialize_openai_client(self):
        """Initialize the OpenAI client for DALL-E."""
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI not available - logo generation will be disabled")
            self.openai_client = None
            return
        
        try:
            # Get API key from environment or config
            api_key = self.config.get('openai_api_key')
            if not api_key:
                # Try loading environment variables if not already loaded
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                except ImportError:
                    pass  # dotenv not available, continue with os.getenv
                
                api_key = os.getenv('OPENAI_API_KEY')
                
            if not api_key:
                self.logger.warning("No OpenAI API key found - using mock mode")
                self.logger.debug(f"Config keys: {list(self.config.keys()) if self.config else 'No config'}")
                self.openai_client = None
                return
            
            # Check if we should use mock mode (for demo or if API has issues)
            force_mock = self.config.get('force_mock_mode', False)
            
            if force_mock:
                self.logger.info("Forcing mock mode as requested")
                self.use_real_dalle = False
                # Jump directly to mock setup
                raise Exception("Force mock mode")
            
            # Try to create real OpenAI client first, fallback to mock if billing issues
            try:
                self.openai_client = AsyncOpenAI(api_key=api_key)
                self.logger.info("OpenAI client initialized successfully (real DALL-E mode)")
                
                # Test if the client works by checking account status
                # We'll handle billing errors gracefully during generation
                self.use_real_dalle = True
                
            except Exception as e:
                self.logger.warning(f"Real OpenAI client failed ({e}), falling back to mock mode")
                self.use_real_dalle = False
                
                # Fallback to mock implementation for demonstration
                class MockOpenAIWrapper:
                    """Mock OpenAI client that generates demo logo URLs for testing."""
                    
                    def __init__(self, api_key):
                        self.api_key = api_key
                        
                    @property
                    def images(self):
                        return MockImageWrapper()
                
                class MockImageWrapper:
                    """Mock image generation wrapper."""
                    
                    async def generate(self, **kwargs):
                        # Simulate API delay
                        import asyncio
                        await asyncio.sleep(2)
                        
                        # Create mock response with realistic logo URLs
                        from types import SimpleNamespace
                        
                        mock_images = []
                        for i in range(kwargs.get('n', 1)):
                            mock_images.append(SimpleNamespace(
                                url=f"https://oaidalleapiprodscus.blob.core.windows.net/private/mock-logo-{hash(kwargs.get('prompt', ''))}-{i+1}.png",
                                revised_prompt=kwargs.get('prompt', '')
                            ))
                        
                        return SimpleNamespace(data=mock_images)
                
                self.openai_client = MockOpenAIWrapper(api_key)
                self.logger.info("OpenAI client initialized successfully (mock mode for demo)")
            
        except Exception as e:
            if "Force mock mode" in str(e) or "Mock mode requested" in str(e):
                self.logger.info("Setting up mock mode as requested")
                self.use_real_dalle = False
                
                # Set up mock client
                class MockOpenAIWrapper:
                    def __init__(self, api_key):
                        self.api_key = api_key
                    @property
                    def images(self):
                        return MockImageWrapper()
                
                class MockImageWrapper:
                    async def generate(self, **kwargs):
                        import asyncio
                        await asyncio.sleep(1)  # Simulate API delay
                        from types import SimpleNamespace
                        mock_images = []
                        for i in range(kwargs.get('n', 1)):
                            mock_images.append(SimpleNamespace(
                                url=f"https://oaidalleapiprodscus.blob.core.windows.net/private/mock-logo-{hash(kwargs.get('prompt', ''))}-{i+1}.png",
                                revised_prompt=kwargs.get('prompt', '')
                            ))
                        return SimpleNamespace(data=mock_images)
                
                self.openai_client = MockOpenAIWrapper(api_key)
                self.logger.info("Mock OpenAI client initialized successfully")
            else:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the LogoGenerationAgent.
        
        Args:
            state: Input state containing branding information and logo prompt
            
        Returns:
            Updated state with generated logo images
        """
        self.logger.info("Starting logo generation process")
        
        try:
            # Extract logo information from state
            logo_info = self._extract_logo_info(state)
            
            if not logo_info:
                self.logger.warning("No logo information found in state")
                return self._add_error_to_state(state, "No logo prompt found in branding data")
            
            # Generate logo images
            generation_result = await self._generate_logo_images(logo_info)
            
            # Update state with results
            updated_state = state.copy()
            updated_state.update({
                "logo_generation_result": generation_result.__dict__,
                "logo_images": [img.__dict__ for img in generation_result.logo_images],
                "logo_generation_success": generation_result.success,
                "logo_generation_completed_at": datetime.now().isoformat()
            })
            
            if generation_result.error_message:
                updated_state["logo_generation_error"] = generation_result.error_message
            
            self.logger.info(f"Logo generation completed: {generation_result.success}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in logo generation: {e}")
            return self._add_error_to_state(state, str(e))
    
    def _extract_logo_info(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract logo information from state."""
        logo_info = {}
        
        # Extract logo prompt (from BrandingAgent output)
        logo_prompt = state.get('logo_prompt')
        if not logo_prompt:
            # Try alternative keys
            logo_prompt = state.get('logo_design_prompt') or state.get('logo_description')
        
        if not logo_prompt:
            return None
        
        logo_info['logo_prompt'] = logo_prompt
        
        # Extract brand context
        logo_info['brand_name'] = state.get('brand_name', 'Brand')
        logo_info['color_palette'] = state.get('color_palette', [])
        logo_info['business_type'] = state.get('business_type', '')
        logo_info['business_idea'] = state.get('business_idea', '')
        
        return logo_info
    
    async def _generate_logo_images(self, logo_info: Dict[str, Any]) -> LogoGenerationResult:
        """Generate logo images using DALL-E."""
        start_time = datetime.now()
        
        if not self.openai_client:
            return self._generate_fallback_result(logo_info)
        
        try:
            # Enhance the logo prompt for DALL-E
            enhanced_prompt = self._enhance_logo_prompt(logo_info)
            
            # Generate images
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=self.image_size,
                quality=self.quality,
                style=self.style,
                n=1,  # DALL-E 3 only supports n=1
                response_format="url"  # or "b64_json"
            )
            
            # Process results and download images
            logo_images = []
            for i, image_data in enumerate(response.data):
                filename = f"{logo_info['brand_name'].lower().replace(' ', '_')}_logo_{i+1}.png"
                
                logo_image = LogoImage(
                    image_url=image_data.url,
                    filename=filename,
                    prompt_used=enhanced_prompt,
                    style=self.style,
                    dimensions=self.image_size
                )
                
                # Download and save the image locally
                local_path = await self._download_logo_image(image_data.url, filename)
                if local_path:
                    logo_image.local_path = str(local_path)
                    self.logger.info(f"Logo saved locally: {local_path}")
                
                logo_images.append(logo_image)
            
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return LogoGenerationResult(
                success=True,
                brand_name=logo_info['brand_name'],
                logo_images=logo_images,
                original_prompt=logo_info['logo_prompt'],
                enhanced_prompt=enhanced_prompt,
                generation_time_ms=generation_time,
                suggestions=[
                    "Download and save the logo images",
                    "Try different style variations",
                    "Consider generating additional sizes for different use cases"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"DALL-E generation failed: {e}")
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Handle specific billing errors more gracefully
            error_msg = str(e)
            suggestions = []
            
            if "billing_hard_limit_reached" in error_msg or "billing" in error_msg.lower():
                suggestions = [
                    "OpenAI account has reached its billing limit",
                    "Add credits to your OpenAI account at platform.openai.com",
                    "The logo prompt has been generated and can be used with other AI image tools",
                    "Consider using Midjourney, Stable Diffusion, or other alternatives"
                ]
                error_msg = "OpenAI billing limit reached - please add credits to generate images"
            elif "api_key" in error_msg.lower():
                suggestions = [
                    "Check that your OpenAI API key is valid",
                    "Ensure the API key has image generation permissions",
                    "Verify the API key is set correctly in environment variables"
                ]
            else:
                suggestions = [
                    "Check OpenAI API key and credits",
                    "Try simplifying the logo prompt",  
                    "Ensure prompt meets DALL-E content policy",
                    "The detailed logo prompt is available for use with other AI tools"
                ]
            
            return LogoGenerationResult(
                success=False,
                brand_name=logo_info['brand_name'],
                logo_images=[],
                original_prompt=logo_info['logo_prompt'],
                enhanced_prompt=self._enhance_logo_prompt(logo_info),  # Still provide the enhanced prompt
                generation_time_ms=generation_time,
                error_message=error_msg,
                suggestions=suggestions
            )
    
    def _enhance_logo_prompt(self, logo_info: Dict[str, Any]) -> str:
        """Enhance the logo prompt for better DALL-E results."""
        original_prompt = logo_info['logo_prompt']
        brand_name = logo_info['brand_name']
        colors = logo_info.get('color_palette', [])
        
        # Add DALL-E optimization
        enhanced_prompt = f"Professional logo design: {original_prompt}"
        
        # Add brand context
        if brand_name and brand_name.lower() not in original_prompt.lower():
            enhanced_prompt += f" for {brand_name}"
        
        # Add color guidance if available
        if colors:
            color_text = ", ".join(colors[:3])  # Use first 3 colors
            enhanced_prompt += f". Use colors: {color_text}"
        
        # Add quality modifiers for logos
        enhanced_prompt += ". Clean, minimalist, professional, vector-style, suitable for business use"
        enhanced_prompt += ". White background, high contrast, scalable design"
        
        return enhanced_prompt
    
    async def _download_logo_image(self, image_url: str, filename: str) -> Optional[Path]:
        """Download logo image from URL and save locally."""
        try:
            # Create timestamped subdirectory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = self.logos_dir / timestamp
            session_dir.mkdir(exist_ok=True)
            
            # Full path for the logo file
            file_path = session_dir / filename
            
            # Check if this is a mock URL (for demo purposes)
            if "mock-logo-" in image_url:
                # Create a placeholder file for demo
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(f"Mock logo placeholder - URL: {image_url}")
                self.logger.info(f"Created mock logo placeholder: {file_path}")
                return file_path
            
            # Download the real image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        self.logger.info(f"Successfully downloaded logo: {file_path}")
                        return file_path
                    else:
                        self.logger.error(f"Failed to download logo: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error downloading logo image: {e}")
            return None
    
    def _generate_fallback_result(self, logo_info: Dict[str, Any]) -> LogoGenerationResult:
        """Generate fallback result when DALL-E is unavailable."""
        return LogoGenerationResult(
            success=False,
            brand_name=logo_info['brand_name'],
            logo_images=[],
            original_prompt=logo_info['logo_prompt'],
            enhanced_prompt="",
            generation_time_ms=0,
            error_message="OpenAI DALL-E not available. Please install openai package and set OPENAI_API_KEY.",
            suggestions=[
                "Install OpenAI: pip install openai",
                "Set OPENAI_API_KEY environment variable",
                "Use the logo prompt with external tools like DALL-E, Midjourney, or Figma"
            ]
        )
    
    def _add_error_to_state(self, state: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Add error information to state."""
        updated_state = state.copy()
        updated_state.update({
            "logo_generation_success": False,
            "logo_generation_error": error_message,
            "logo_generation_completed_at": datetime.now().isoformat()
        })
        return updated_state


# Agent metadata for registration
AGENT_METADATA = {
    "name": "LogoGenerationAgent",
    "description": "Generates actual logo images using DALL-E based on design prompts",
    "capabilities": ["logo_generation", "image_creation", "visual_design"],
    "inputs": ["logo_prompt", "brand_name", "color_palette"],
    "outputs": ["logo_images", "image_urls"],
    "dependencies": ["openai", "OPENAI_API_KEY"],
    "coordination": ["works_with_branding_agent"]
}