"""
PersistentLogoGenerationAgent - Long-running logo generation agent for concurrent execution.

Provides persistent logo generation capabilities with:
- DALL-E powered logo image creation
- Logo prompt enhancement and optimization
- Multiple logo variations
- File management and storage
- Context retention across tasks
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..base_agent import PersistentAgent, TaskRequest, TaskResponse
from departments.branding.logo_generation_agent import LogoGenerationAgent as CoreLogoGenerationAgent


class PersistentLogoGenerationAgent(PersistentAgent):
    """
    Persistent version of the LogoGenerationAgent for concurrent execution.
    
    Supports task types:
    - logo_generation
    - logo_design
    - visual_identity_creation
    - brand_visualization
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the persistent logo generation agent."""
        super().__init__(agent_id, config)
        
        # Initialize core logo generation agent
        self.core_agent: Optional[CoreLogoGenerationAgent] = None
        
        # Logo generation context and state
        self.logo_context: Dict[str, Any] = {}
        self.generated_logos: List[str] = []
        
        # Performance tracking
        self.successful_generations = 0
        self.failed_generations = 0

        # Logos directory
        self.logos_dir = Path(self.config.get('generated_logos_dir', './generated_logos'))
        self.logos_dir.mkdir(exist_ok=True)
    
    async def on_start(self):
        """Initialize logo generation agent components."""
        try:
            # Initialize core logo generation agent
            agent_config = self.config.copy()
            # Disable interactive features for persistent agents
            agent_config['interactive_approval'] = False
            
            self.core_agent = CoreLogoGenerationAgent(
                config=agent_config
            )
            
            self.logger.info(f"PersistentLogoGenerationAgent {self.agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize logo generation agent: {e}")
            raise
    
    async def on_stop(self):
        """Cleanup logo generation agent resources."""
        # Save any persistent state if needed
        self.logger.info(f"PersistentLogoGenerationAgent {self.agent_id} stopped")
    
    def get_supported_task_types(self) -> List[str]:
        """Return supported task types."""
        return [
            "logo_generation",
            "logo_design", 
            "visual_identity_creation",
            "brand_visualization"
        ]
    
    async def process_task(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a logo generation task."""
        self.logger.info(f"Processing {task_type} task")
        
        try:
            if task_type in ["logo_generation", "logo_design", "visual_identity_creation", "brand_visualization"]:
                return await self._handle_logo_generation(input_data)
            else:
                return {
                    "success": False,
                    "error_message": f"Unsupported task type: {task_type}",
                    "task_type": task_type
                }
                
        except Exception as e:
            self.logger.error(f"Error processing {task_type}: {e}")
            self.failed_generations += 1
            return {
                "success": False,
                "error_message": f"Logo generation failed: {str(e)}",
                "task_type": task_type
            }
    
    async def _handle_logo_generation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logo generation request."""
        self.logger.info("Starting logo generation")
        
        business_idea = input_data.get("business_idea", "")
        if not business_idea:
            return {
                "success": False,
                "error_message": "Business idea is required for logo generation"
            }
        
        try:
            # Create state for the core agent
            state = {
                "business_idea": business_idea,
                "style_preferences": input_data.get("style_preferences", ["modern", "professional"]),
                "logo_variations": input_data.get("logo_variations", 3),
                "format": input_data.get("format", "PNG"),
                "size": input_data.get("size", "1024x1024"),
                "business_type": input_data.get("business_type", "general")
            }
            
            # Use the core agent to generate logos
            if self.core_agent:
                result = await self.core_agent.run(state)
            else:
                # Fallback mock result
                result = self._create_mock_logo_result(state)
            
            if result.get("success", False):
                self.successful_generations += 1
                self.generated_logos.extend(result.get("logo_images", []))
                
                # Add metadata
                result.update({
                    "agent_id": self.agent_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_generated": len(self.generated_logos)
                })
                
                self.logger.info(f"Logo generation completed successfully for: {business_idea}")
            else:
                self.failed_generations += 1
                self.logger.warning(f"Logo generation failed for: {business_idea}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Logo generation error: {e}")
            self.failed_generations += 1
            return {
                "success": False,
                "error_message": f"Logo generation failed: {str(e)}",
                "business_idea": business_idea
            }
    
    def _create_mock_logo_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock logo generation result for demo purposes."""
        business_idea = state.get("business_idea", "Business")
        
        # Extract business name from idea
        business_name = business_idea.split()[0] if business_idea else "Business"
        
        # Create mock logo image data
        mock_logos = []
        variations = state.get("logo_variations", 3)
        
        for i in range(variations):
            logo_filename = f"logo_{business_name.lower()}_{i+1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            mock_logos.append({
                "filename": logo_filename,
                "local_path": str(self.logos_dir / logo_filename),
                "prompt_used": f"Modern professional logo for {business_name}",
                "style": state.get("style_preferences", ["modern"])[0] if state.get("style_preferences") else "modern",
                "dimensions": state.get("size", "1024x1024"),
                "mock": True  # Indicate this is a mock result
            })
        
        return {
            "success": True,
            "brand_name": business_name,
            "logo_images": mock_logos,
            "original_prompt": business_idea,
            "enhanced_prompt": f"Professional logo design for {business_name}",
            "generation_time_ms": 2000,  # Mock 2 second generation time
            "mock_mode": True
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        base_status = await super().get_health_status()
        base_status.update({
            "logo_generations": {
                "successful": self.successful_generations,
                "failed": self.failed_generations,
                "total": self.successful_generations + self.failed_generations
            },
            "generated_logos": len(self.generated_logos),
            "core_agent_ready": self.core_agent is not None
        })
        return base_status