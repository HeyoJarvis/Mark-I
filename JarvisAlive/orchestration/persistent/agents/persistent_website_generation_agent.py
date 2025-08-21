"""
PersistentWebsiteGenerationAgent - Long-running website generation agent for concurrent execution.

Provides persistent website generation capabilities with:
- AI-powered website structure and content creation
- Sitemap and navigation planning
- SEO-optimized content generation
- Responsive design recommendations
- Context retention across tasks
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..base_agent import PersistentAgent, TaskRequest, TaskResponse
from departments.website.website_generator_agent import WebsiteGeneratorAgent as CoreWebsiteGeneratorAgent


class PersistentWebsiteGenerationAgent(PersistentAgent):
    """
    Persistent version of the WebsiteGeneratorAgent for concurrent execution.
    
    Supports task types:
    - website_generation
    - website_design
    - site_structure_creation
    - web_content_generation
    - landing_page_creation
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the persistent website generation agent."""
        super().__init__(agent_id, config)
        
        # Initialize core website generation agent
        self.core_agent: Optional[CoreWebsiteGeneratorAgent] = None
        
        # Website generation context and state
        self.website_context: Dict[str, Any] = {}
        self.generated_websites: List[str] = []
        
        # Performance tracking
        self.successful_generations = 0
        self.failed_generations = 0

        # Websites directory
        self.websites_dir = Path(self.config.get('generated_websites_dir', './generated_websites'))
        self.websites_dir.mkdir(exist_ok=True)
    
    async def on_start(self):
        """Initialize website generation agent components."""
        try:
            # Initialize core website generation agent
            agent_config = self.config.copy()
            # Disable interactive features for persistent agents
            agent_config['interactive_approval'] = False
            
            self.core_agent = CoreWebsiteGeneratorAgent(
                config=agent_config
            )
            
            self.logger.info(f"PersistentWebsiteGenerationAgent {self.agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize website generation agent: {e}")
            raise
    
    async def on_stop(self):
        """Cleanup website generation agent resources."""
        # Save any persistent state if needed
        self.logger.info(f"PersistentWebsiteGenerationAgent {self.agent_id} stopped")
    
    def get_supported_task_types(self) -> List[str]:
        """Return supported task types."""
        return [
            "website_generation",
            "website_design", 
            "site_structure_creation",
            "web_content_generation",
            "landing_page_creation"
        ]
    
    async def process_task(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a website generation task."""
        self.logger.info(f"Processing {task_type} task")
        
        try:
            if task_type in ["website_generation", "website_design", "site_structure_creation", "web_content_generation", "landing_page_creation"]:
                return await self._handle_website_generation(input_data)
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
                "error_message": f"Website generation failed: {str(e)}",
                "task_type": task_type
            }
    
    async def _handle_website_generation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle website generation request."""
        self.logger.info("Starting website generation")
        
        business_idea = input_data.get("business_idea", "")
        if not business_idea:
            return {
                "success": False,
                "error_message": "Business idea is required for website generation"
            }
        
        try:
            # Create state for the core agent
            state = {
                "business_idea": business_idea,
                "site_type": input_data.get("site_type", "business"),
                "include_seo": input_data.get("include_seo", True),
                "include_sitemap": input_data.get("include_sitemap", True),
                "include_copy": input_data.get("include_copy", True),
                "include_cta": input_data.get("include_cta", True),
                "responsive": input_data.get("responsive", True)
            }
            
            # Use the core agent to generate website
            if self.core_agent:
                result = await self.core_agent.run(state)
            else:
                # Fallback mock result
                result = self._create_mock_website_result(state)
            
            if result.get("success", False):
                self.successful_generations += 1
                self.generated_websites.append(business_idea)
                
                # Add metadata
                result.update({
                    "agent_id": self.agent_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_generated": len(self.generated_websites)
                })
                
                self.logger.info(f"Website generation completed successfully for: {business_idea}")
            else:
                self.failed_generations += 1
                self.logger.warning(f"Website generation failed for: {business_idea}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Website generation error: {e}")
            self.failed_generations += 1
            return {
                "success": False,
                "error_message": f"Website generation failed: {str(e)}",
                "business_idea": business_idea
            }
    
    def _create_mock_website_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock website generation result for demo purposes."""
        business_idea = state.get("business_idea", "Business")
        
        # Extract business name from idea
        business_name = business_idea.split()[0] if business_idea else "Business"
        
        # Create mock website structure
        mock_sitemap = [
            "Home",
            "About",
            "Services",
            "Contact",
            "Blog"
        ]
        
        mock_website_structure = [
            {
                "page": "Home",
                "url": "/",
                "title": f"Welcome to {business_name}",
                "meta_description": f"Professional {business_idea.lower()} services",
                "sections": ["Hero", "Features", "Testimonials", "CTA"]
            },
            {
                "page": "About",
                "url": "/about",
                "title": f"About {business_name}",
                "meta_description": f"Learn more about {business_name} and our mission",
                "sections": ["About Us", "Team", "Mission"]
            },
            {
                "page": "Services",
                "url": "/services",
                "title": f"{business_name} Services",
                "meta_description": f"Professional services offered by {business_name}",
                "sections": ["Service Overview", "Pricing", "FAQ"]
            }
        ]
        
        mock_homepage = {
            "hero_section": {
                "headline": f"Professional {business_name} Services",
                "subheadline": f"Expert solutions for your {business_idea.lower()} needs",
                "cta_text": "Get Started Today",
                "cta_url": "/contact"
            },
            "features": [
                "Professional Service",
                "Expert Team",
                "Customer Focused"
            ],
            "testimonial": f"Excellent work from {business_name}!",
            "contact_cta": "Ready to get started? Contact us today!"
        }
        
        mock_style_guide = {
            "color_palette": {
                "primary": "#2563eb",
                "secondary": "#64748b",
                "accent": "#f59e0b"
            },
            "typography": {
                "primary_font": "Inter",
                "heading_font": "Inter",
                "body_font": "Inter"
            },
            "layout": {
                "max_width": "1200px",
                "responsive": True,
                "mobile_first": True
            }
        }
        
        mock_seo = {
            "title_template": f"{business_name} - [Page Title]",
            "meta_description_template": f"Professional {business_idea.lower()} services by {business_name}",
            "keywords": [business_name.lower(), "professional", "services"],
            "structured_data": "organization",
            "social_media": {
                "og_image": f"/images/{business_name.lower()}-social.jpg",
                "twitter_card": "summary_large_image"
            }
        }
        
        # Create website filename
        website_filename = f"website_{business_name.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        website_path = self.websites_dir / website_filename
        
        # Save mock website data
        website_data = {
            "sitemap": mock_sitemap,
            "website_structure": mock_website_structure,
            "homepage": mock_homepage,
            "style_guide": mock_style_guide,
            "seo_recommendations": mock_seo
        }
        
        return {
            "success": True,
            "sitemap": mock_sitemap,
            "website_structure": mock_website_structure,
            "homepage": mock_homepage,
            "style_guide": mock_style_guide,
            "seo_recommendations": mock_seo,
            "website_file": str(website_path),
            "generation_time_ms": 1500,  # Mock 1.5 second generation time
            "mock_mode": True
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        base_status = await super().get_health_status()
        base_status.update({
            "website_generations": {
                "successful": self.successful_generations,
                "failed": self.failed_generations,
                "total": self.successful_generations + self.failed_generations
            },
            "generated_websites": len(self.generated_websites),
            "core_agent_ready": self.core_agent is not None
        })
        return base_status