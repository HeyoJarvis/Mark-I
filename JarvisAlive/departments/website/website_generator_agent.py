"""
WebsiteGeneratorAgent - AI-powered website structure and content generation

This agent generates website architecture, content sections, copy, and style guides
based on business requirements and branding context. It creates comprehensive
website blueprints ready for development or no-code implementation.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Import AI engine infrastructure
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class WebsiteResult:
    """Result of website generation"""
    def __init__(
        self,
        sitemap: List[str],
        website_structure: List[Dict[str, Any]],
        homepage: Dict[str, Any],
        style_guide: Dict[str, Any],
        seo_recommendations: Optional[Dict[str, Any]] = None
    ):
        self.sitemap = sitemap
        self.website_structure = website_structure
        self.homepage = homepage
        self.style_guide = style_guide
        self.seo_recommendations = seo_recommendations or {}


class WebsiteGeneratorAgent:
    """
    AI agent for generating comprehensive website structure and content.
    
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the WebsiteGeneratorAgent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine
        self._initialize_ai_engine()
        
        # Website generation preferences
        self.max_pages = self.config.get('max_pages', 8)
        self.max_sections_per_page = self.config.get('max_sections_per_page', 6)
        self.include_seo = self.config.get('include_seo', True)
        
        # Output configuration
        self.outputs_dir = Path(self.config.get('website_outputs_dir', './website_outputs'))
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Export formats
        self.export_formats = self.config.get('export_formats', ['json', 'html'])  # json, html, react
        self.generate_full_site = self.config.get('generate_full_site', True)
        
        self.logger.info("WebsiteGeneratorAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize the Claude AI engine for website generation"""
        try:
            # Get API key from environment or config
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                # Try to get from environment
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using fallback mode")
                self.ai_engine = None
                return
            
            # Configure AI engine
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,  # Higher limit for comprehensive website content
                temperature=0.6,  # Balanced creativity for website copy
                enable_cache=False,  # Fresh content for each website
                timeout_seconds=180  # 3 minutes for comprehensive generation
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("AI engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the WebsiteGeneratorAgent.
        
        Args:
            state: Input state containing business and branding information
            
        Returns:
            Updated state with website structure and content
        """
        self.logger.info("Starting website generation")
        
        try:
            # Extract website requirements from state
            website_requirements = self._extract_website_requirements(state)
            
            if not website_requirements:
                self.logger.warning("No website requirements found in state")
                return state
            
            # Generate website structure and content
            website_result = await self._generate_website(website_requirements)
            
            # Save website output in multiple formats
            saved_paths = await self._save_website_outputs(website_result, website_requirements)
            
            # Update state with website results
            updated_state = state.copy()
            updated_state.update({
                "sitemap": website_result.sitemap,
                "website_structure": website_result.website_structure,
                "homepage": website_result.homepage,
                "style_guide": website_result.style_guide,
                "seo_recommendations": website_result.seo_recommendations,
                "website_generated_at": datetime.now().isoformat(),
                "analysis_type": "website_generation",
                "saved_paths": saved_paths,
                "export_formats": self.export_formats
            })
            
            self.logger.info(f"Website generation completed for: {website_requirements.get('brand_name', 'Unknown')}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in website generation: {e}")
            # Return original state on error
            return state
    
    def _extract_website_requirements(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate website requirements from state.
        
        Args:
            state: Input state dictionary
            
        Returns:
            Dictionary with website requirements or None if insufficient data
        """
        requirements = {}
        
        # Extract brand information
        brand_name = state.get('brand_name')
        if brand_name:
            requirements['brand_name'] = brand_name
        
        # Extract business idea
        business_idea = state.get('business_idea')
        if business_idea:
            requirements['business_idea'] = business_idea
        else:
            # Try to infer from other fields
            business_idea = state.get('description') or state.get('idea')
            if business_idea:
                requirements['business_idea'] = business_idea
        
        # Extract branding context
        color_palette = state.get('color_palette', [])
        if color_palette:
            requirements['color_palette'] = color_palette
        
        logo_prompt = state.get('logo_prompt')
        if logo_prompt:
            requirements['logo_prompt'] = logo_prompt
        
        # Extract business context
        for key in ['target_audience', 'industry', 'product_type', 'business_type']:
            if key in state and state[key]:
                requirements[key] = state[key]
        
        # Extract specific website requirements
        pages = state.get('pages', [])
        if pages:
            requirements['requested_pages'] = pages
        
        website_type = state.get('website_type')
        if website_type:
            requirements['website_type'] = website_type
        
        # Validate we have minimum requirements
        if not (requirements.get('brand_name') or requirements.get('business_idea')):
            self.logger.warning("No brand name or business idea found in state")
            return None
        
        self.logger.info(f"Extracted website requirements: {list(requirements.keys())}")
        return requirements
    
    async def _generate_website(self, requirements: Dict[str, Any]) -> WebsiteResult:
        """
        Generate comprehensive website structure and content.
        
        Args:
            requirements: Dictionary containing website requirements
            
        Returns:
            WebsiteResult with generated content
        """
        if not self.ai_engine:
            self.logger.warning("AI engine not available - using fallback website generation")
            return self._generate_fallback_website(requirements)
        
        try:
            # Create website generation prompt
            prompt = self._create_website_prompt(requirements)
            
            # Generate website using AI
            response = await self.ai_engine.generate(prompt)
            
            # Parse AI response
            website_data = self._parse_ai_response(response.content)
            
            # Create website result
            website_result = WebsiteResult(
                sitemap=website_data.get('sitemap', []),
                website_structure=website_data.get('website_structure', []),
                homepage=website_data.get('homepage', {}),
                style_guide=website_data.get('style_guide', {}),
                seo_recommendations=website_data.get('seo_recommendations', {})
            )
            
            self.logger.info("AI website generation completed successfully")
            return website_result
            
        except Exception as e:
            self.logger.error(f"Error in AI website generation: {e}")
            return self._generate_fallback_website(requirements)
    
    def _create_website_prompt(self, requirements: Dict[str, Any]) -> str:
        """
        Create a comprehensive prompt for AI website generation.
        
        Args:
            requirements: Dictionary containing website requirements
            
        Returns:
            Formatted prompt for website generation
        """
        brand_name = requirements.get('brand_name', '')
        business_idea = requirements.get('business_idea', '')
        target_audience = requirements.get('target_audience', '')
        industry = requirements.get('industry', '')
        color_palette = requirements.get('color_palette', [])
        requested_pages = requirements.get('requested_pages', [])
        website_type = requirements.get('website_type', 'business')
        
        # Add unique identifier to prevent caching issues
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        prompt = f"""[Generation ID: {unique_id}] You are a senior UX strategist and web copywriter.

Create a comprehensive website structure and content plan for this business:

BUSINESS CONTEXT:
- Brand Name: {brand_name}
- Business Idea: {business_idea}
- Target Audience: {target_audience}
- Industry: {industry}
- Brand Colors: {', '.join(color_palette) if color_palette else 'Not specified'}
- Website Type: {website_type}
- Requested Pages: {', '.join(requested_pages) if requested_pages else 'Not specified'}

Generate a complete website blueprint in this EXACT JSON format:

{{
  "sitemap": [
    "Home",
    "About",
    "Products/Services",
    "Pricing",
    "Contact"
  ],
  "website_structure": [
    {{
      "page": "Home",
      "purpose": "Convert visitors into leads/customers",
      "sections": [
        {{
          "id": "hero",
          "type": "hero_section",
          "headline": "Compelling main headline",
          "subheadline": "Supporting description that explains value",
          "primary_cta": "Primary call-to-action text",
          "secondary_cta": "Secondary action text",
          "background_style": "gradient|image|solid"
        }},
        {{
          "id": "value_proposition",
          "type": "features_section",
          "title": "Section title",
          "items": [
            {{
              "title": "Feature/Benefit 1",
              "description": "Detailed explanation",
              "icon": "relevant_icon_name"
            }}
          ]
        }},
        {{
          "id": "social_proof",
          "type": "testimonials_section",
          "title": "What Our Customers Say",
          "testimonials": [
            {{
              "quote": "Customer testimonial quote",
              "author": "Customer Name",
              "title": "Customer Title",
              "company": "Company Name"
            }}
          ]
        }},
        {{
          "id": "cta_section",
          "type": "call_to_action",
          "headline": "Final conversion headline",
          "description": "Urgency/value reinforcement",
          "cta_text": "Action button text"
        }}
      ]
    }}
  ],
  "homepage": {{
    "seo_title": "SEO-optimized page title (60 chars max)",
    "meta_description": "SEO meta description (160 chars max)",
    "hero": {{
      "headline": "Primary value proposition headline",
      "subheadline": "Supporting explanation of what you do",
      "primary_cta": "Get Started",
      "secondary_cta": "Learn More",
      "hero_copy": "Additional hero section copy if needed"
    }},
    "value_propositions": [
      "Key benefit 1",
      "Key benefit 2", 
      "Key benefit 3"
    ],
    "features": [
      {{
        "title": "Feature Name",
        "description": "Feature description",
        "benefit": "Customer benefit"
      }}
    ],
    "faq": [
      {{
        "question": "Common customer question?",
        "answer": "Clear, helpful answer"
      }}
    ]
  }},
  "style_guide": {{
    "brand_name": "{brand_name}",
    "colors": {json.dumps(color_palette) if color_palette else '["#1F2937", "#3B82F6", "#10B981"]'},
    "typography": {{
      "primary_font": "Modern sans-serif font name",
      "secondary_font": "Supporting font name",
      "heading_style": "Bold, modern",
      "body_style": "Clean, readable"
    }},
    "tone_of_voice": {{
      "personality": "professional|friendly|expert|casual",
      "writing_style": "Description of brand voice",
      "key_messages": ["Core message 1", "Core message 2"]
    }},
    "visual_style": {{
      "design_approach": "modern|minimal|bold|classic",
      "imagery_style": "Type of images/graphics to use",
      "layout_principles": ["principle 1", "principle 2"]
    }}
  }},
  "seo_recommendations": {{
    "target_keywords": ["primary keyword", "secondary keyword"],
    "content_strategy": "SEO content approach",
    "technical_recommendations": ["recommendation 1", "recommendation 2"],
    "local_seo": "Local SEO strategy if applicable"
  }}
}}

REQUIREMENTS:
1. Create 4-8 pages total (including Home)
2. Each page should have 3-6 sections maximum
3. Write conversion-focused copy that speaks to the target audience
4. Include specific, actionable CTAs
5. Make content industry-appropriate and professional
6. Ensure all JSON is valid and properly formatted
7. Focus on business results and customer value

Make the content specific to the business type and target audience. Avoid generic placeholder text.
[Request ID: {unique_id}]"""
        
        return prompt
    
    def _parse_ai_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the AI response and extract website data.
        
        Args:
            response_content: Raw AI response string
            
        Returns:
            Dictionary with parsed website data
        """
        try:
            # Clean the response
            cleaned_response = response_content.strip()
            
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                data = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['sitemap', 'website_structure', 'homepage', 'style_guide']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing required field: {field}")
                    data[field] = {} if field != 'sitemap' else []
            
            # Validate sitemap is a list
            if not isinstance(data['sitemap'], list):
                data['sitemap'] = []
            
            # Validate website_structure is a list
            if not isinstance(data['website_structure'], list):
                data['website_structure'] = []
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            self.logger.debug(f"Response content: {response_content[:500]}...")
            raise ValueError(f"Failed to parse AI response: {e}")
    
    def _generate_fallback_website(self, requirements: Dict[str, Any]) -> WebsiteResult:
        """
        Generate fallback website when AI is unavailable.
        
        Args:
            requirements: Dictionary containing website requirements
            
        Returns:
            WebsiteResult with fallback content
        """
        brand_name = requirements.get('brand_name', 'Your Business')
        business_idea = requirements.get('business_idea', 'We provide excellent solutions')
        industry = requirements.get('industry', 'business')
        color_palette = requirements.get('color_palette', ['#1F2937', '#3B82F6', '#10B981', '#F59E0B'])
        requested_pages = requirements.get('requested_pages', [])
        
        # Generate contextual fallback based on industry
        if any(term in business_idea.lower() for term in ['coffee', 'cafe', 'restaurant']):
            return self._generate_restaurant_fallback(brand_name, business_idea, color_palette)
        elif any(term in business_idea.lower() for term in ['tech', 'software', 'app', 'saas']):
            return self._generate_tech_fallback(brand_name, business_idea, color_palette)
        elif any(term in business_idea.lower() for term in ['retail', 'store', 'shop', 'ecommerce']):
            return self._generate_retail_fallback(brand_name, business_idea, color_palette)
        else:
            return self._generate_generic_fallback(brand_name, business_idea, color_palette, requested_pages)
    
    def _generate_generic_fallback(self, brand_name: str, business_idea: str, color_palette: List[str], requested_pages: List[str]) -> WebsiteResult:
        """Generate generic business website fallback."""
        sitemap = requested_pages[:self.max_pages] if requested_pages else [
            "Home", "About", "Services", "Pricing", "Contact"
        ]
        
        return WebsiteResult(
            sitemap=sitemap,
            website_structure=[
                {
                    "page": "Home",
                    "purpose": "Convert visitors into leads",
                    "sections": [
                        {
                            "id": "hero",
                            "type": "hero_section",
                            "headline": f"Welcome to {brand_name}",
                            "subheadline": business_idea,
                            "primary_cta": "Get Started",
                            "secondary_cta": "Learn More",
                            "background_style": "gradient"
                        },
                        {
                            "id": "features",
                            "type": "features_section",
                            "title": "Why Choose Us",
                            "items": [
                                {
                                    "title": "Quality Service",
                                    "description": "We deliver exceptional results",
                                    "icon": "check_circle"
                                },
                                {
                                    "title": "Expert Team",
                                    "description": "Professional and experienced",
                                    "icon": "users"
                                },
                                {
                                    "title": "Customer Focus",
                                    "description": "Your success is our priority",
                                    "icon": "heart"
                                }
                            ]
                        }
                    ]
                }
            ],
            homepage={
                "seo_title": f"{brand_name} - Professional Services",
                "meta_description": f"Discover {brand_name}'s professional services. Get started today.",
                "hero": {
                    "headline": f"Professional Solutions from {brand_name}",
                    "subheadline": "We help businesses succeed with our expert services",
                    "primary_cta": "Get Started",
                    "secondary_cta": "Learn More"
                },
                "value_propositions": [
                    "Professional expertise",
                    "Reliable service",
                    "Customer satisfaction"
                ],
                "features": [
                    {
                        "title": "Expert Solutions",
                        "description": "Professional approach to your needs",
                        "benefit": "Better results for your business"
                    }
                ],
                "faq": [
                    {
                        "question": "How do you ensure quality?",
                        "answer": "We follow industry best practices and maintain high standards."
                    }
                ]
            },
            style_guide={
                "brand_name": brand_name,
                "colors": color_palette,
                "typography": {
                    "primary_font": "Inter",
                    "secondary_font": "Inter",
                    "heading_style": "Bold, professional",
                    "body_style": "Clean, readable"
                },
                "tone_of_voice": {
                    "personality": "professional",
                    "writing_style": "Clear, trustworthy, and results-focused",
                    "key_messages": ["Quality service", "Customer success"]
                },
                "visual_style": {
                    "design_approach": "modern",
                    "imagery_style": "Professional business imagery",
                    "layout_principles": ["Clean layout", "Clear hierarchy"]
                }
            },
            seo_recommendations={
                "target_keywords": [f"{brand_name.lower()}", "professional services"],
                "content_strategy": "Focus on service benefits and customer success",
                "technical_recommendations": ["Optimize page speed", "Mobile responsive design"],
                "local_seo": "Include location-based keywords if serving local market"
            }
        )
    
    def _generate_restaurant_fallback(self, brand_name: str, business_idea: str, color_palette: List[str]) -> WebsiteResult:
        """Generate restaurant/cafe specific fallback."""
        return WebsiteResult(
            sitemap=["Home", "Menu", "About", "Location", "Contact", "Order Online"],
            website_structure=[
                {
                    "page": "Home",
                    "purpose": "Attract customers and drive orders",
                    "sections": [
                        {
                            "id": "hero",
                            "type": "hero_section",
                            "headline": f"Welcome to {brand_name}",
                            "subheadline": "Fresh, delicious food made with love",
                            "primary_cta": "Order Now",
                            "secondary_cta": "View Menu",
                            "background_style": "image"
                        },
                        {
                            "id": "specialties",
                            "type": "features_section",
                            "title": "Our Specialties",
                            "items": [
                                {
                                    "title": "Fresh Ingredients",
                                    "description": "Locally sourced, high-quality ingredients",
                                    "icon": "leaf"
                                },
                                {
                                    "title": "Expert Chefs",
                                    "description": "Experienced culinary professionals",
                                    "icon": "chef_hat"
                                }
                            ]
                        }
                    ]
                }
            ],
            homepage={
                "seo_title": f"{brand_name} - Fresh Food & Great Taste",
                "meta_description": f"Experience delicious food at {brand_name}. Fresh ingredients, expert preparation.",
                "hero": {
                    "headline": f"Delicious Food at {brand_name}",
                    "subheadline": "Made fresh daily with the finest ingredients",
                    "primary_cta": "Order Now",
                    "secondary_cta": "View Menu"
                },
                "value_propositions": [
                    "Fresh daily preparation",
                    "High-quality ingredients",
                    "Exceptional taste"
                ]
            },
            style_guide={
                "brand_name": brand_name,
                "colors": color_palette,
                "tone_of_voice": {
                    "personality": "warm and welcoming",
                    "writing_style": "Appetizing, friendly, and inviting"
                }
            }
        )
    
    def _generate_tech_fallback(self, brand_name: str, business_idea: str, color_palette: List[str]) -> WebsiteResult:
        """Generate tech/software specific fallback."""
        return WebsiteResult(
            sitemap=["Home", "Product", "Pricing", "Documentation", "Support", "About"],
            website_structure=[
                {
                    "page": "Home",
                    "purpose": "Convert visitors to trial users",
                    "sections": [
                        {
                            "id": "hero",
                            "type": "hero_section",
                            "headline": f"Powerful Solutions from {brand_name}",
                            "subheadline": "Streamline your workflow with our innovative technology",
                            "primary_cta": "Start Free Trial",
                            "secondary_cta": "Watch Demo",
                            "background_style": "gradient"
                        }
                    ]
                }
            ],
            homepage={
                "seo_title": f"{brand_name} - Innovative Technology Solutions",
                "meta_description": f"Discover {brand_name}'s powerful technology solutions. Start your free trial today.",
                "hero": {
                    "headline": f"Innovation Powered by {brand_name}",
                    "subheadline": "Transform your business with cutting-edge technology",
                    "primary_cta": "Start Free Trial",
                    "secondary_cta": "Watch Demo"
                }
            },
            style_guide={
                "brand_name": brand_name,
                "colors": color_palette,
                "tone_of_voice": {
                    "personality": "innovative and professional",
                    "writing_style": "Technical yet accessible, results-focused"
                }
            }
        )
    
    def _generate_retail_fallback(self, brand_name: str, business_idea: str, color_palette: List[str]) -> WebsiteResult:
        """Generate retail/ecommerce specific fallback."""
        return WebsiteResult(
            sitemap=["Home", "Shop", "Categories", "About", "Contact", "Cart"],
            website_structure=[
                {
                    "page": "Home",
                    "purpose": "Drive product discovery and sales",
                    "sections": [
                        {
                            "id": "hero",
                            "type": "hero_section",
                            "headline": f"Shop the Best at {brand_name}",
                            "subheadline": "Quality products, great prices, exceptional service",
                            "primary_cta": "Shop Now",
                            "secondary_cta": "Browse Categories",
                            "background_style": "image"
                        }
                    ]
                }
            ],
            homepage={
                "seo_title": f"{brand_name} - Quality Products & Great Service",
                "meta_description": f"Shop {brand_name} for quality products at great prices. Fast shipping and excellent service.",
                "hero": {
                    "headline": f"Quality Products from {brand_name}",
                    "subheadline": "Discover our curated collection of premium products",
                    "primary_cta": "Shop Now",
                    "secondary_cta": "Browse Categories"
                }
            },
            style_guide={
                "brand_name": brand_name,
                "colors": color_palette,
                "tone_of_voice": {
                    "personality": "friendly and trustworthy",
                    "writing_style": "Persuasive, customer-focused, and clear"
                }
            }
        )
    
    async def _save_website_outputs(self, website_result: WebsiteResult, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Save website output in multiple formats (JSON, HTML, React)."""
        saved_paths = {}
        
        # Create base filename
        brand_name = requirements.get('brand_name', 'website')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', brand_name.lower()).strip('_')[:30]
        base_name = f"website_{clean_name}_{timestamp}"
        
        try:
            # Save JSON (for developers/integration)
            if 'json' in self.export_formats:
                json_path = await self._save_json_output(website_result, requirements, base_name)
                if json_path:
                    saved_paths['json'] = json_path
            
            # Save HTML (ready-to-use website)
            if 'html' in self.export_formats:
                html_path = await self._save_html_output(website_result, requirements, base_name)
                if html_path:
                    saved_paths['html'] = html_path
            
            # Save React project (for developers)
            if 'react' in self.export_formats:
                react_path = await self._save_react_output(website_result, requirements, base_name)
                if react_path:
                    saved_paths['react'] = react_path
            
            self.logger.info(f"Website saved in {len(saved_paths)} formats: {list(saved_paths.keys())}")
            return saved_paths
            
        except Exception as e:
            self.logger.error(f"Failed to save website outputs: {e}")
            return {}
    
    async def _save_json_output(self, website_result: WebsiteResult, requirements: Dict[str, Any], base_name: str) -> str:
        """Save JSON blueprint for developers."""
        try:
            json_path = self.outputs_dir / f"{base_name}.json"
            
            website_data = {
                'generation_parameters': requirements,
                'website_results': {
                    'sitemap': website_result.sitemap,
                    'website_structure': website_result.website_structure,
                    'homepage': website_result.homepage,
                    'style_guide': website_result.style_guide,
                    'seo_recommendations': website_result.seo_recommendations
                },
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'agent_version': 'WebsiteGeneratorAgent_v1.0',
                    'ai_engine_used': self.ai_engine is not None,
                    'total_pages': len(website_result.sitemap),
                    'generation_mode': 'ai' if self.ai_engine else 'fallback'
                }
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(website_data, f, indent=2, ensure_ascii=False, default=str)
            
            return str(json_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON output: {e}")
            return ""
    
    async def _save_html_output(self, website_result: WebsiteResult, requirements: Dict[str, Any], base_name: str) -> str:
        """Generate and save actual HTML website."""
        try:
            # Create website directory
            site_dir = self.outputs_dir / f"{base_name}_site"
            site_dir.mkdir(exist_ok=True)
            
            # Generate CSS from style guide
            css_content = self._generate_css(website_result.style_guide)
            css_path = site_dir / "styles.css"
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            # Generate HTML pages
            html_files = []
            for page_data in website_result.website_structure:
                page_name = page_data.get('page', 'Unknown')
                html_content = self._generate_html_page(page_data, website_result)
                
                # Save HTML file
                html_filename = f"{page_name.lower().replace(' ', '_')}.html"
                html_path = site_dir / html_filename
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                html_files.append(str(html_path))
            
            # Generate index.html (homepage)
            if website_result.homepage:
                index_content = self._generate_index_html(website_result)
                index_path = site_dir / "index.html"
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_content)
                html_files.append(str(index_path))
            
            self.logger.info(f"Generated {len(html_files)} HTML files in {site_dir}")
            return str(site_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to save HTML output: {e}")
            return ""
    
    async def _save_react_output(self, website_result: WebsiteResult, requirements: Dict[str, Any], base_name: str) -> str:
        """Generate and save React/Vite project."""
        try:
            # Create React project directory
            react_dir = self.outputs_dir / f"{base_name}_react"
            react_dir.mkdir(exist_ok=True)
            
            # Create basic Vite project structure
            await self._create_vite_structure(react_dir, website_result, requirements)
            
            self.logger.info(f"Generated React/Vite project in {react_dir}")
            return str(react_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to save React output: {e}")
            return ""
    
    def _generate_css(self, style_guide: Dict[str, Any]) -> str:
        """Generate professional CSS based on the sample template."""
        colors = style_guide.get('colors', ['#271c17', '#b25a2f', '#faf7f2'])
        brand_name = style_guide.get('brand_name', 'Your Business')
        
        # Extract colors with fallbacks
        primary_color = colors[0] if len(colors) > 0 else '#271c17'  # Dark brown
        accent_color = colors[1] if len(colors) > 1 else '#b25a2f'   # Copper
        bg_color = colors[2] if len(colors) > 2 else '#faf7f2'       # Cream
        muted_color = '#6d594f'  # Muted brown
        line_color = '#eadfce'   # Light line
        card_color = '#ffffff'   # White cards
        
        return f"""/* Professional CSS for {brand_name} */
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;600;700;800&display=swap');

:root {{
  --paper: {bg_color};
  --ink: {primary_color};
  --muted: {muted_color};
  --copper: {accent_color};
  --copper-dark: #8f4422;
  --line: {line_color};
  --card: {card_color};
}}

* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}

body {{
  font-family: Manrope, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  background: var(--paper);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}

.container {{ 
  width: min(1120px, 92vw); 
  margin-inline: auto; 
}}

a {{ 
  color: var(--copper-dark); 
  text-decoration: none; 
}}

a:hover {{ 
  text-decoration: underline; 
}}

.site-header {{
  position: sticky; 
  top: 0; 
  z-index: 20; 
  background: rgba(250, 247, 242, .85);
  -webkit-backdrop-filter: saturate(180%) blur(10px);
  backdrop-filter: saturate(180%) blur(10px);
  border-bottom: 1px solid var(--line);
}}

.site-header-inner {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
}}

.brand {{
  display: flex;
  gap: 12px;
  align-items: center;
}}

.brand img {{
  width: 56px;
  height: 56px;
  object-fit: contain;
  border-radius: 12px;
  background: linear-gradient(145deg, #e0b199, #a45a3b);
  padding: 2px;
}}

.brand-text strong {{
  display: block;
  font-weight: 800;
  letter-spacing: .3px;
  font-size: 1.1rem;
}}

.brand-text span {{
  font-size: .9rem;
  color: var(--muted);
}}

.nav {{
  display: flex;
  gap: 22px;
  align-items: center;
}}

.nav a {{
  font-weight: 600;
  color: var(--ink);
}}

.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid var(--ink);
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s ease;
}}

.btn-primary {{
  background: var(--ink);
  color: white;
  border-color: var(--ink);
}}

.btn-ghost {{
  background: transparent;
  color: var(--ink);
  border-color: var(--line);
}}

.btn:hover {{
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}

.hero {{
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 140px 0 160px;
  background:
    radial-gradient(1200px 800px at 15% -20%, #ffe2cf 0, rgba(255,255,255,0) 60%),
    radial-gradient(1200px 800px at 85% -30%, #fff2e6 0, rgba(255,255,255,0) 60%);
}}

.hero:after {{
  content: "";
  position: absolute;
  inset: -20% -10% auto -10%;
  height: 60%;
  background: radial-gradient(60% 100% at 50% -10%, rgba(178,90,47,.25), rgba(0,0,0,0));
  transform: translateY(-10px);
  pointer-events: none;
  z-index: -1;
}}

.hero-inner {{
  display: grid;
  gap: 18px;
  text-align: center;
}}

.hero h1 {{
  font-size: clamp(44px, 8vw, 80px);
  line-height: 1.02;
  margin: 0;
  letter-spacing: -0.5px;
  font-weight: 800;
}}

.hero p {{
  font-size: clamp(18px, 2.4vw, 22px);
  margin: 0;
  color: var(--muted);
  max-width: 600px;
  margin-inline: auto;
}}

.accent {{
  color: var(--copper-dark);
}}

.cta-row {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 32px;
}}

.section {{
  padding: 84px 0;
}}

.section-dark {{
  background: linear-gradient(180deg, #f2e8dc, #eadbcb);
}}

.section-head {{
  text-align: center;
  margin-bottom: 48px;
}}

.section h2 {{
  font-size: clamp(30px, 3.7vw, 42px);
  margin: 0 0 8px;
  font-weight: 700;
}}

.note {{
  opacity: .7;
  text-align: center;
  margin-top: 16px;
  font-size: 0.9rem;
}}

.card {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(39,28,23,.06);
  margin-bottom: 24px;
}}

.split {{
  display: grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 28px;
  align-items: center;
}}

.card-photo {{
  min-height: 360px;
  background: linear-gradient(145deg, rgba(178,90,47,.20), rgba(178,90,47,.08));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--copper);
  font-size: 1.2rem;
  font-weight: 600;
}}

.features-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 48px;
}}

.feature-card {{
  text-align: center;
  padding: 32px 24px;
}}

.feature-card h3 {{
  color: var(--copper-dark);
  margin-bottom: 12px;
  font-weight: 700;
  font-size: 1.25rem;
}}

.feature-card p {{
  color: var(--muted);
  line-height: 1.6;
}}

.contact-section {{
  background: var(--ink);
  color: white;
  padding: 80px 0;
  text-align: center;
}}

.contact-section h2 {{
  color: white;
  margin-bottom: 24px;
}}

.contact-info {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
  margin-top: 48px;
}}

.contact-card {{
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 12px;
  padding: 24px;
}}

.contact-card h3 {{
  color: var(--copper);
  margin-bottom: 16px;
}}

.contact-card ul {{
  list-style: none;
  padding: 0;
  margin: 0;
}}

.contact-card li {{
  margin-bottom: 8px;
  color: rgba(255,255,255,0.9);
}}

footer {{
  background: var(--ink);
  color: white;
  text-align: center;
  padding: 40px 0;
  border-top: 1px solid var(--line);
}}

@media (max-width: 768px) {{
  .hero {{ padding: 80px 0 100px; }}
  .hero h1 {{ font-size: 36px; }}
  .split {{ grid-template-columns: 1fr; }}
  .nav {{ display: none; }}
  .site-header-inner {{ justify-content: center; }}
  .features-grid {{ grid-template-columns: 1fr; }}
  .contact-info {{ grid-template-columns: 1fr; }}
}}
"""
    
    def _generate_html_page(self, page_data: Dict[str, Any], website_result: WebsiteResult) -> str:
        """Generate professional HTML for a specific page."""
        page_name = page_data.get('page', 'Page')
        sections = page_data.get('sections', [])
        brand_name = website_result.style_guide.get('brand_name', 'Your Business')
        
        # Generate sections HTML
        sections_html = ""
        for section in sections:
            sections_html += self._generate_section_html(section)
        
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_name} - {brand_name}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="site-header-inner">
        <div class="brand">
          <div class="brand-text">
            <strong>{brand_name}</strong>
            <span>Excellence in Service</span>
          </div>
        </div>
        <nav class="nav">
          {self._generate_nav_links_professional(website_result.sitemap)}
          <a href="#contact" class="btn btn-primary">Get Started</a>
        </nav>
      </div>
    </div>
  </header>
  
  <main>
    <div class="container">
      {sections_html}
    </div>
  </main>
  
  <footer>
    <div class="container">
      <p>&copy; 2024 {brand_name}. All rights reserved.</p>
    </div>
  </footer>
</body>
</html>"""
    
    def _generate_index_html(self, website_result: WebsiteResult) -> str:
        """Generate professional homepage based on sample template."""
        homepage = website_result.homepage
        brand_name = website_result.style_guide.get('brand_name', 'Your Business')
        
        hero = homepage.get('hero', {})
        features = homepage.get('features', [])
        value_props = homepage.get('value_propositions', [])
        
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{homepage.get('seo_title', f'{brand_name} — Professional Service')}</title>
  <meta name="description" content="{homepage.get('meta_description', 'Professional service with excellence.')}" />
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="site-header-inner">
        <div class="brand">
          <div class="brand-text">
            <strong>{brand_name}</strong>
            <span>Excellence in Service</span>
          </div>
        </div>
        <nav class="nav">
          {self._generate_nav_links_professional(website_result.sitemap)}
          <a href="#contact" class="btn btn-primary">Get Started</a>
        </nav>
      </div>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="container">
        <div class="hero-inner">
          <h1>{hero.get('headline', f'Welcome to <span class="accent">{brand_name}</span>')}</h1>
          <p>{hero.get('subheadline', 'Professional service delivered with excellence and care.')}</p>
          <div class="cta-row">
            <a href="#contact" class="btn btn-primary">{hero.get('primary_cta', 'Get Started')}</a>
            <a href="#about" class="btn btn-ghost">{hero.get('secondary_cta', 'Learn More')}</a>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Why Choose {brand_name}</h2>
          <p class="note">Experience the difference quality makes</p>
        </div>
        <div class="features-grid">
          {self._generate_features_professional(features, value_props)}
        </div>
      </div>
    </section>

    <section class="section section-dark">
      <div class="container">
        <div class="card">
          <div class="split">
            <div>
              <h2>Ready to Get Started?</h2>
              <p>Contact us today to learn more about how we can help you achieve your goals.</p>
              <div class="cta-row">
                <a href="#contact" class="btn btn-primary">Contact Us</a>
              </div>
            </div>
            <div class="card-photo">
              Professional Service Excellence
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="contact-section" id="contact">
      <div class="container">
        <h2>Get in Touch</h2>
        <p>Ready to experience excellence? Contact us today.</p>
        <div class="contact-info">
          <div class="contact-card">
            <h3>Visit Us</h3>
            <ul>
              <li><strong>Address:</strong> 123 Business Street</li>
              <li><strong>City:</strong> Your City, State 12345</li>
              <li><strong>Hours:</strong> Mon-Fri 9AM-6PM</li>
            </ul>
          </div>
          <div class="contact-card">
            <h3>Contact Info</h3>
            <ul>
              <li><strong>Phone:</strong> (555) 123-4567</li>
              <li><strong>Email:</strong> <a href="mailto:hello@{brand_name.lower().replace(' ', '')}.com">hello@{brand_name.lower().replace(' ', '')}.com</a></li>
              <li><strong>Website:</strong> <a href="#" rel="noopener">www.{brand_name.lower().replace(' ', '')}.com</a></li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <p>&copy; 2024 {brand_name}. All rights reserved.</p>
    </div>
  </footer>
</body>
</html>"""
    
    def _generate_section_html(self, section: Dict[str, Any]) -> str:
        """Generate HTML for a website section."""
        section_type = section.get('type', 'default')
        section_id = section.get('id', 'section')
        
        if section_type == 'hero_section':
            return f"""
    <section class="hero" id="{section_id}">
        <h1>{section.get('headline', 'Welcome')}</h1>
        <p>{section.get('subheadline', 'Great service awaits')}</p>
        <a href="#" class="btn">{section.get('primary_cta', 'Get Started')}</a>
        <a href="#" class="btn btn-secondary">{section.get('secondary_cta', 'Learn More')}</a>
    </section>"""
        elif section_type == 'features_section':
            items_html = ""
            for item in section.get('items', []):
                items_html += f"""
                <div class="feature-card">
                    <h3>{item.get('title', 'Feature')}</h3>
                    <p>{item.get('description', 'Description')}</p>
                </div>"""
            return f"""
    <section class="features" id="{section_id}">
        <h2>{section.get('title', 'Features')}</h2>
        <div class="features-grid">{items_html}
        </div>
    </section>"""
        else:
            return f'<section id="{section_id}"><h2>Section Content</h2></section>'
    
    def _generate_nav_links_professional(self, sitemap: List[str]) -> str:
        """Generate professional navigation links."""
        nav_html = ""
        for page in sitemap:
            if page.lower() == "home":
                continue  # Skip home in nav
            href = f"#{page.lower().replace(' ', '-')}"
            nav_html += f'<a href="{href}">{page}</a>'
        return nav_html
    
    def _generate_features_professional(self, features: List[Dict[str, Any]], value_props: List[str]) -> str:
        """Generate professional features section."""
        features_html = ""
        
        # Use features if available, otherwise use value propositions
        items_to_use = features if features else []
        if not items_to_use and value_props:
            # Convert value props to feature format
            for prop in value_props[:3]:  # Max 3 features
                items_to_use.append({
                    'title': prop,
                    'description': f'We excel in {prop.lower()} to deliver outstanding results.'
                })
        
        # Default features if nothing available
        if not items_to_use:
            items_to_use = [
                {'title': 'Quality Service', 'description': 'We deliver exceptional results with attention to detail.'},
                {'title': 'Expert Team', 'description': 'Our experienced professionals ensure your success.'},
                {'title': 'Customer Focus', 'description': 'Your satisfaction is our top priority.'}
            ]
        
        for feature in items_to_use:
            features_html += f"""
          <div class="feature-card">
            <h3>{feature.get('title', 'Service')}</h3>
            <p>{feature.get('description', 'Professional service excellence.')}</p>
          </div>"""
        
        return features_html
    
    async def _create_vite_structure(self, react_dir: Path, website_result: WebsiteResult, requirements: Dict[str, Any]):
        """Create a complete Vite/React project structure."""
        brand_name = website_result.style_guide.get('brand_name', 'Website')
        
        # Create directories
        src_dir = react_dir / "src"
        components_dir = src_dir / "components"
        src_dir.mkdir(exist_ok=True)
        components_dir.mkdir(exist_ok=True)
        
        # Generate package.json
        package_json = {
            "name": f"{brand_name.lower().replace(' ', '-')}-website",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.66",
                "@types/react-dom": "^18.2.22",
                "@vitejs/plugin-react": "^4.2.1",
                "vite": "^5.2.0"
            }
        }
        
        with open(react_dir / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Generate vite.config.js
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
"""
        with open(react_dir / "vite.config.js", 'w') as f:
            f.write(vite_config)
        
        # Generate index.html
        index_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{website_result.homepage.get('seo_title', f'{brand_name} - Home')}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>"""
        with open(react_dir / "index.html", 'w') as f:
            f.write(index_html)
        
        # Generate main.jsx
        main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
        with open(src_dir / "main.jsx", 'w') as f:
            f.write(main_jsx)
        
        # Generate App.jsx
        app_jsx = self._generate_react_app(website_result)
        with open(src_dir / "App.jsx", 'w') as f:
            f.write(app_jsx)
        
        # Generate CSS
        css_content = self._generate_react_css(website_result.style_guide)
        with open(src_dir / "index.css", 'w') as f:
            f.write(css_content)
        
        # Generate README
        readme = f"""# {brand_name} Website

Generated by WebsiteGeneratorAgent

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Structure

- Homepage with hero section and features
- Responsive design
- Modern React/Vite setup
- Brand colors and typography integrated

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        with open(react_dir / "README.md", 'w') as f:
            f.write(readme)
    
    def _generate_react_app(self, website_result: WebsiteResult) -> str:
        """Generate React App.jsx component."""
        homepage = website_result.homepage
        hero = homepage.get('hero', {})
        features = homepage.get('features', [])
        brand_name = website_result.style_guide.get('brand_name', 'Website')
        
        features_jsx = ""
        for feature in features:
            features_jsx += f"""
        <div className="feature-card">
          <h3>{feature.get('title', 'Feature')}</h3>
          <p>{feature.get('description', 'Description')}</p>
        </div>"""
        
        return f"""import React from 'react'

function App() {{
  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-container">
          <h1 className="logo">{brand_name}</h1>
          <ul className="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </div>
      </nav>

      <main>
        <section className="hero" id="home">
          <h1>{hero.get('headline', f'Welcome to {brand_name}')}</h1>
          <p>{hero.get('subheadline', 'We provide excellent service')}</p>
          <div className="hero-buttons">
            <a href="#contact" className="btn primary">{hero.get('primary_cta', 'Get Started')}</a>
            <a href="#about" className="btn secondary">{hero.get('secondary_cta', 'Learn More')}</a>
          </div>
        </section>

        <section className="features" id="services">
          <h2>Why Choose {brand_name}</h2>
          <div className="features-grid">{features_jsx}
          </div>
        </section>

        <section className="contact" id="contact">
          <h2>Get Started Today</h2>
          <p>Ready to experience what {brand_name} can do for you?</p>
          <a href="#" className="btn primary">Contact Us</a>
        </section>
      </main>

      <footer>
        <p>&copy; 2024 {brand_name}. All rights reserved.</p>
      </footer>
    </div>
  )
}}

export default App
"""
    
    def _generate_react_css(self, style_guide: Dict[str, Any]) -> str:
        """Generate React-specific CSS."""
        colors = style_guide.get('colors', ['#1F2937', '#3B82F6', '#10B981'])
        return f"""/* React App Styles */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

:root {{
  --primary: {colors[0] if colors else '#1F2937'};
  --secondary: {colors[1] if len(colors) > 1 else '#3B82F6'};
  --accent: {colors[2] if len(colors) > 2 else '#10B981'};
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 1.6;
  color: #1F2937;
}}

.navbar {{
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}}

.nav-container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.logo {{
  color: var(--primary);
  font-size: 1.5rem;
  font-weight: 700;
}}

.nav-links {{
  display: flex;
  list-style: none;
  gap: 2rem;
}}

.nav-links a {{
  text-decoration: none;
  color: #6B7280;
  font-weight: 500;
  transition: color 0.2s;
}}

.nav-links a:hover {{
  color: var(--primary);
}}

.hero {{
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  padding: 6rem 2rem;
  text-align: center;
}}

.hero h1 {{
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}}

.hero p {{
  font-size: 1.25rem;
  margin-bottom: 3rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}}

.hero-buttons {{
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}}

.btn {{
  display: inline-block;
  padding: 1rem 2rem;
  border-radius: 0.5rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  border: 2px solid transparent;
}}

.btn.primary {{
  background: var(--accent);
  color: white;
}}

.btn.secondary {{
  background: transparent;
  color: white;
  border-color: white;
}}

.btn:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}}

.features {{
  padding: 6rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}}

.features h2 {{
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 4rem;
  color: var(--primary);
}}

.features-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 3rem;
}}

.feature-card {{
  text-align: center;
  padding: 2rem;
  border-radius: 1rem;
  background: white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}}

.feature-card:hover {{
  transform: translateY(-5px);
}}

.feature-card h3 {{
  color: var(--primary);
  margin-bottom: 1rem;
  font-size: 1.25rem;
}}

.contact {{
  background: var(--primary);
  color: white;
  padding: 4rem 2rem;
  text-align: center;
}}

.contact h2 {{
  font-size: 2.5rem;
  margin-bottom: 1rem;
}}

.contact p {{
  font-size: 1.125rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}}

footer {{
  background: #1F2937;
  color: white;
  text-align: center;
  padding: 2rem;
}}

@media (max-width: 768px) {{
  .hero h1 {{ font-size: 2.5rem; }}
  .hero-buttons {{ flex-direction: column; align-items: center; }}
  .features {{ padding: 3rem 1rem; }}
  .nav-container {{ flex-direction: column; gap: 1rem; }}
  .nav-links {{ flex-direction: column; text-align: center; }}
}}
"""


# Agent metadata for registration
AGENT_METADATA = {
    "name": "WebsiteGeneratorAgent",
    "description": "AI-powered website structure, content, and style guide generation",
    "capabilities": [
        "website_architecture", "content_generation", "seo_optimization", 
        "style_guide_creation", "conversion_optimization", "industry_customization"
    ],
    "inputs": [
        "brand_name", "business_idea", "color_palette", "target_audience", 
        "industry", "pages", "website_type"
    ],
    "outputs": [
        "sitemap", "website_structure", "homepage", "style_guide", "seo_recommendations"
    ],
    "interactive": False,
    "dependencies": ["anthropic", "ANTHROPIC_API_KEY"],
    "coordination": ["works_with_branding_agent", "uses_branding_context", "seo_optimized"]
} 