"""
BrandingAgent - AI-powered brand creation, visual identity generation, and market research.

This agent understands user intent about business ideas and generates:
- Brand names, logos, color palettes, domain suggestions
- Market research and competitive analysis
- Industry analysis and opportunity assessment
- Target customer analysis and pricing strategies
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import AI engine infrastructure
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

# Import interactive approval system
from utils.user_response_parser import UserResponseParser, ApprovalIntent

logger = logging.getLogger(__name__)


class AgentExitException(Exception):
    """Exception to exit the entire branding agent."""
    pass


class SystemExitException(Exception):
    """Exception to exit the entire HeyJarvis system."""
    pass


class BrandingResult:
    """Result of branding generation and market research"""
    def __init__(
        self,
        brand_name: str,
        logo_prompt: str,
        color_palette: List[str],
        domain_suggestions: Optional[List[str]] = None,
        market_research: Optional[Dict[str, Any]] = None
    ):
        self.brand_name = brand_name
        self.logo_prompt = logo_prompt
        self.color_palette = color_palette
        self.domain_suggestions = domain_suggestions or []
        self.market_research = market_research or {}


class BrandingAgent:
    """
    AI agent for generating branding assets based on business intent.
    
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BrandingAgent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine
        self._initialize_ai_engine()
        
        # Branding preferences and constraints
        self.max_domain_suggestions = self.config.get('max_domain_suggestions', 5)
        self.color_palette_size = self.config.get('color_palette_size', 4)
        
        # Interactive approval settings
        self.interactive_approval = self.config.get('interactive_approval', True)
        self.response_parser = UserResponseParser()
        
        self.logger.info("BrandingAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize the Claude AI engine for branding generation"""
        try:
            # Get API key from environment or config
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                # Try to get from environment
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using mock mode")
                self.ai_engine = None
                return
            
            # Configure AI engine
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.8,  # Slightly creative for branding
                enable_cache=False,  # CRITICAL FIX: Disable cache for creative work
                timeout_seconds=300  # CRITICAL FIX: 5 minutes timeout - no rush for quality
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("AI engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the BrandingAgent.
        
        Args:
            state: Input state containing business information
            
        Returns:
            Updated state with branding assets and/or market research
        """
        self.logger.info("Starting branding and market research analysis")
        
        try:
            # Extract business information from state
            business_info = self._extract_business_info(state)
            
            if not business_info:
                self.logger.warning("No business information found in state")
                return state
            
            # Check if this is a market research request
            is_market_research = self._is_market_research_request(business_info)
            
            if is_market_research:
                # Generate market research analysis
                market_result = await self._generate_market_research(business_info)
                branding_result = await self._generate_branding_assets(business_info)
                
                # Update state with both branding and market research
                updated_state = state.copy()
                updated_state.update({
                    "brand_name": branding_result.brand_name,
                    "logo_prompt": branding_result.logo_prompt,
                    "color_palette": branding_result.color_palette,
                    "domain_suggestions": branding_result.domain_suggestions,
                    "market_research": market_result,
                    "analysis_type": "branding_and_market_research",
                    "branding_generated_at": datetime.now().isoformat()
                })
                
                self.logger.info(f"Market research and branding completed for: {business_info.get('business_idea', 'Unknown')}")
            else:
                # Generate branding assets only
                branding_result = await self._generate_branding_assets(business_info)
                
                # Update state with branding results
                updated_state = state.copy()
                updated_state.update({
                    "brand_name": branding_result.brand_name,
                    "logo_prompt": branding_result.logo_prompt,
                    "color_palette": branding_result.color_palette,
                    "domain_suggestions": branding_result.domain_suggestions,
                    "analysis_type": "branding_only",
                    "branding_generated_at": datetime.now().isoformat()
                })
                
                self.logger.info(f"Branding generation completed: {branding_result.brand_name}")
            
            return updated_state
            
        except AgentExitException as e:
            self.logger.info(f"Branding agent exit requested: {e}")
            # Return state with exit flag for orchestrator to handle
            updated_state = state.copy()
            updated_state.update({
                "agent_exit_requested": True,
                "exit_reason": "User requested to exit branding agent",
                "branding_success": False
            })
            return updated_state
            
        except SystemExitException as e:
            self.logger.info(f"System exit requested: {e}")
            # Return state with system exit flag
            updated_state = state.copy()  
            updated_state.update({
                "system_exit_requested": True,
                "exit_reason": "User requested to quit entire system", 
                "branding_success": False
            })
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in branding/market research generation: {e}")
            # Return original state on error
            return state
    
    def _extract_business_info(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate business information from state.
        
        Args:
            state: Input state dictionary
            
        Returns:
            Dictionary with business information or None if insufficient data
        """
        business_info = {}
        
        # Extract business idea
        business_idea = state.get('business_idea')
        if business_idea:
            business_info['business_idea'] = business_idea
        else:
            # Try to infer from other fields
            business_idea = state.get('description') or state.get('idea')
            if business_idea:
                business_info['business_idea'] = business_idea
        
        # Extract business type and product focus for better context
        business_type = state.get('business_type')
        if business_type:
            business_info['business_type'] = business_type
            
        product_focus = state.get('product_focus')
        if product_focus:
            business_info['product_focus'] = product_focus
        
        # Extract product type
        product_type = state.get('product_type')
        if product_type:
            business_info['product_type'] = product_type
        
        # Extract business name if provided
        business_name = state.get('business_name')
        if business_name:
            business_info['business_name'] = business_name
        
        # Extract target audience
        target_audience = state.get('target_audience')
        if target_audience:
            business_info['target_audience'] = target_audience
        
        # Extract industry/niche
        industry = state.get('industry') or state.get('niche')
        if industry:
            business_info['industry'] = industry
        
        # Validate we have at least a business idea
        if not business_info.get('business_idea'):
            self.logger.warning("No business idea found in state")
            return None
        
        self.logger.info(f"Extracted business info: {business_info}")
        return business_info
    
    def _is_market_research_request(self, business_info: Dict[str, Any]) -> bool:
        """
        Determine if the request is for market research analysis.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            True if market research is requested, False otherwise
        """
        business_idea = business_info.get('business_idea', '').lower()
        
        # Keywords that indicate market research requests
        market_research_keywords = [
            'research', 'market', 'analysis', 'competitor', 'industry',
            'opportunity', 'segmentation', 'target', 'customer', 'pricing',
            'competitive', 'landscape', 'assessment', 'size', 'growth',
            'trend', 'demand', 'supply', 'geographic', 'regional'
        ]
        
        # Check if any market research keywords are present
        for keyword in market_research_keywords:
            if keyword in business_idea:
                return True
        
        # Check for specific market research phrases
        market_research_phrases = [
            'market research', 'competitive analysis', 'industry analysis',
            'market opportunity', 'target market', 'customer analysis',
            'pricing strategy', 'market size', 'competitive landscape'
        ]
        
        for phrase in market_research_phrases:
            if phrase in business_idea:
                return True
        
        return False
    
    async def _generate_market_research(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive market research analysis.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            Dictionary with market research results
        """
        if not self.ai_engine:
            self.logger.warning("AI engine not available - using fallback market research")
            return self._generate_fallback_market_research(business_info)
        
        try:
            # Create market research prompt
            prompt = self._create_market_research_prompt(business_info)
            
            # Generate market research using AI
            response = await self.ai_engine.generate(prompt)
            
            # Parse AI response
            market_data = self._parse_market_research_response(response.content)
            
            self.logger.info("Market research generation completed successfully")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error in market research generation: {e}")
            return self._generate_fallback_market_research(business_info)
    
    def _create_market_research_prompt(self, business_info: Dict[str, Any]) -> str:
        """
        Create a comprehensive market research prompt for AI analysis.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            Formatted prompt for market research
        """
        business_idea = business_info.get('business_idea', '')
        product_type = business_info.get('product_type', '')
        target_audience = business_info.get('target_audience', '')
        industry = business_info.get('industry', '')
        
        prompt = f"""
You are a market research expert. Analyze the market for this business idea and provide comprehensive research.

Business Idea: {business_idea}
Product Type: {product_type}
Target Audience: {target_audience}
Industry: {industry}

Please provide a detailed market research analysis in the following JSON format:

{{
  "market_size": {{
    "total_market_size": "estimated market size in dollars",
    "addressable_market": "specific market segment size",
    "growth_rate": "annual growth rate percentage",
    "market_maturity": "emerging/growing/mature/declining"
  }},
  "competitive_landscape": {{
    "major_competitors": [
      {{
        "name": "competitor name",
        "market_share": "estimated market share",
        "strengths": ["strength1", "strength2"],
        "weaknesses": ["weakness1", "weakness2"],
        "pricing_strategy": "premium/mid-market/budget"
      }}
    ],
    "competitive_intensity": "high/medium/low",
    "barriers_to_entry": ["barrier1", "barrier2", "barrier3"]
  }},
  "market_segmentation": {{
    "primary_segments": [
      {{
        "segment_name": "segment description",
        "size": "segment size",
        "growth_potential": "high/medium/low",
        "key_characteristics": ["characteristic1", "characteristic2"]
      }}
    ],
    "target_segment": "recommended primary target segment",
    "secondary_segments": ["segment1", "segment2"]
  }},
  "customer_analysis": {{
    "customer_profiles": [
      {{
        "profile_name": "customer type",
        "demographics": "age, income, location",
        "pain_points": ["pain1", "pain2"],
        "buying_behavior": "description",
        "price_sensitivity": "high/medium/low"
      }}
    ],
    "customer_journey": "awareness → consideration → purchase → retention",
    "key_decision_factors": ["factor1", "factor2", "factor3"]
  }},
  "pricing_analysis": {{
    "current_price_range": "low-high price range",
    "pricing_models": ["model1", "model2"],
    "recommended_pricing": "specific pricing recommendation",
    "pricing_factors": ["factor1", "factor2"]
  }},
  "opportunity_assessment": {{
    "market_opportunity": "description of opportunity",
    "competitive_advantage": "potential competitive advantages",
    "risks": ["risk1", "risk2", "risk3"],
    "success_factors": ["factor1", "factor2", "factor3"]
  }},
  "geographic_analysis": {{
    "primary_markets": ["market1", "market2"],
    "regional_differences": "description of regional variations",
    "expansion_opportunities": ["opportunity1", "opportunity2"]
  }},
  "trends_and_forecasts": {{
    "current_trends": ["trend1", "trend2"],
    "future_predictions": "3-5 year forecast",
    "disruption_risks": ["risk1", "risk2"]
  }}
}}

Provide realistic, data-driven analysis based on current market conditions. Focus on actionable insights for business strategy.
"""
        
        return prompt
    
    def _parse_market_research_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse AI market research response into structured data.
        
        Args:
            response_content: Raw AI response content
            
        Returns:
            Dictionary with parsed market research data
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(response_content)
            
            # Validate required fields
            required_sections = [
                'market_size', 'competitive_landscape', 'market_segmentation',
                'customer_analysis', 'pricing_analysis', 'opportunity_assessment'
            ]
            
            for section in required_sections:
                if section not in data:
                    data[section] = {}
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to parse market research response: {e}")
            return self._generate_fallback_market_research({})
    
    def _generate_fallback_market_research(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback market research when AI is unavailable.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            Dictionary with basic market research data
        """
        business_idea = business_info.get('business_idea', 'Unknown business')
        
        return {
            "market_size": {
                "total_market_size": "$10B+ (estimated)",
                "addressable_market": "$2B+ (specific segment)",
                "growth_rate": "5-10% annually",
                "market_maturity": "growing"
            },
            "competitive_landscape": {
                "major_competitors": [
                    {
                        "name": "Major Competitor A",
                        "market_share": "15-20%",
                        "strengths": ["Established brand", "Large distribution network"],
                        "weaknesses": ["Slow to innovate", "High overhead"],
                        "pricing_strategy": "mid-market"
                    }
                ],
                "competitive_intensity": "medium",
                "barriers_to_entry": ["Brand recognition", "Distribution channels", "Capital requirements"]
            },
            "market_segmentation": {
                "primary_segments": [
                    {
                        "segment_name": "Primary target segment",
                        "size": "$500M+",
                        "growth_potential": "high",
                        "key_characteristics": ["Quality conscious", "Value-driven"]
                    }
                ],
                "target_segment": "Primary target segment",
                "secondary_segments": ["Secondary segment 1", "Secondary segment 2"]
            },
            "customer_analysis": {
                "customer_profiles": [
                    {
                        "profile_name": "Primary customer",
                        "demographics": "25-45, middle income, urban/suburban",
                        "pain_points": ["Limited options", "Quality concerns"],
                        "buying_behavior": "Research-driven, value-conscious",
                        "price_sensitivity": "medium"
                    }
                ],
                "customer_journey": "awareness → consideration → purchase → retention",
                "key_decision_factors": ["Quality", "Price", "Convenience"]
            },
            "pricing_analysis": {
                "current_price_range": "$10-$50",
                "pricing_models": ["Premium", "Mid-market", "Budget"],
                "recommended_pricing": "Competitive mid-market pricing",
                "pricing_factors": ["Quality", "Competition", "Target market"]
            },
            "opportunity_assessment": {
                "market_opportunity": f"Significant opportunity in {business_idea} market",
                "competitive_advantage": "Innovation, customer focus, quality",
                "risks": ["Market competition", "Economic factors", "Regulatory changes"],
                "success_factors": ["Quality product", "Strong marketing", "Customer service"]
            },
            "geographic_analysis": {
                "primary_markets": ["North America", "Europe"],
                "regional_differences": "Varies by region and culture",
                "expansion_opportunities": ["Emerging markets", "Online expansion"]
            },
            "trends_and_forecasts": {
                "current_trends": ["Digital transformation", "Sustainability", "Personalization"],
                "future_predictions": "Continued growth with focus on innovation",
                "disruption_risks": ["Technology changes", "New competitors", "Market shifts"]
            }
        }
    
    async def _generate_branding_assets(self, business_info: Dict[str, Any]) -> BrandingResult:
        """
        Generate branding assets using AI.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            BrandingResult with generated assets
        """
        if not self.ai_engine:
            self.logger.warning("AI engine not available - using fallback branding")
            return await self._generate_fallback_branding(business_info)
        
        try:
            # Create prompt for Claude
            prompt = self._create_branding_prompt(business_info)
            
            # Generate branding with AI
            response = await self.ai_engine.generate(prompt)
            
            # Parse AI response
            branding_data = self._parse_ai_response(response.content)
            
            # Interactive approval step for logo prompt
            if self.interactive_approval:
                approved_logo_prompt = await self._request_logo_prompt_approval(
                    branding_data['logo_prompt'], 
                    branding_data, 
                    business_info
                )
                branding_data['logo_prompt'] = approved_logo_prompt
            
            # Generate domain suggestions
            domain_suggestions = self._generate_domain_suggestions(branding_data['brand_name'])
            
            return BrandingResult(
                brand_name=branding_data['brand_name'],
                logo_prompt=branding_data['logo_prompt'],
                color_palette=branding_data['color_palette'],
                domain_suggestions=domain_suggestions
            )
            
        except Exception as e:
            self.logger.error(f"Error generating branding with AI: {e}")
            return await self._generate_fallback_branding(business_info)
    
    def _create_branding_prompt(self, business_info: Dict[str, Any]) -> str:
        """
        Create a detailed prompt for Claude to generate branding assets.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            Formatted prompt string
        """
        business_idea = business_info['business_idea']
        product_type = business_info.get('product_type', '')
        target_audience = business_info.get('target_audience', '')
        industry = business_info.get('industry', '')
        
        # Build context
        context_parts = [f"Business idea: {business_idea}"]
        if product_type:
            context_parts.append(f"Product type: {product_type}")
        if target_audience:
            context_parts.append(f"Target audience: {target_audience}")
        if industry:
            context_parts.append(f"Industry: {industry}")
        
        context = " | ".join(context_parts)
        
        # Add unique identifier to prevent any caching/similarity issues
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        prompt = f"""[Generation ID: {unique_id}] You are a branding strategist and creative director.

Business Context: {context}

Your task is to create compelling and UNIQUE branding assets for this business. Be creative and avoid common/overused names:

1. **Brand Name**: Generate a unique, memorable brand name that:
   - Reflects the business purpose and values
   - Is easy to pronounce and remember
   - Avoids generic or overused terms (especially avoid names starting with 'Nexus', 'Nova', 'Neo')
   - Has potential for trademark registration
   - Is creative and distinctive

2. **Logo Design Prompt**: Create a detailed prompt for a logo designer that:
   - Describes the visual style and mood
   - Specifies key design elements
   - Includes color guidance
   - Is suitable for DALL·E, Midjourney, or human designers
   - CRITICAL: Always end with "IMPORTANT: Spell the brand name exactly as: [BRAND_NAME]" to prevent spelling errors

3. **Color Palette**: Suggest 3-5 colors in hex format that:
   - Complement the brand personality
   - Work well together
   - Are appropriate for the industry
   - Include primary, secondary, and accent colors

Return your response in this exact JSON format:
{{
  "brand_name": "Creative Brand Name",
  "logo_prompt": "Design a [style] logo for [brand_name] that [description]. Use [colors] and incorporate [elements].",
  "color_palette": ["#HEX1", "#HEX2", "#HEX3", "#HEX4"]
}}

Ensure the response is valid JSON and all fields are properly filled. [Request ID: {unique_id}]
"""
        
        return prompt
    
    def _parse_ai_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the AI response and extract branding data.
        
        Args:
            response_content: Raw AI response string
            
        Returns:
            Dictionary with parsed branding data
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
            required_fields = ['brand_name', 'logo_prompt', 'color_palette']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate color palette
            if not isinstance(data['color_palette'], list):
                raise ValueError("color_palette must be a list")
            
            # Validate hex colors
            for color in data['color_palette']:
                if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                    raise ValueError(f"Invalid hex color: {color}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            raise ValueError(f"Failed to parse AI response: {e}")
    
    def _generate_domain_suggestions(self, brand_name: str) -> List[str]:
        """
        Generate domain name suggestions based on brand name.
        
        Args:
            brand_name: The generated brand name
            
        Returns:
            List of domain suggestions
        """
        try:
            # Clean brand name for domain generation
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
            
            # Common TLDs
            tlds = ['.com', '.co', '.ai', '.io', '.net']
            
            suggestions = []
            for tld in tlds:
                domain = f"{clean_name}{tld}"
                suggestions.append(domain)
            
            # Add variations
            if len(clean_name) > 8:
                # Try shorter version
                short_name = clean_name[:8]
                suggestions.append(f"{short_name}.com")
            
            # Limit to max suggestions
            return suggestions[:self.max_domain_suggestions]
            
        except Exception as e:
            self.logger.error(f"Error generating domain suggestions: {e}")
            return []
    
    async def _generate_fallback_branding(self, business_info: Dict[str, Any]) -> BrandingResult:
        """
        Generate realistic mock branding when AI is not available (demo mode).
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            BrandingResult with mock assets
        """
        business_idea = business_info['business_idea'].lower()
        product_type = business_info.get('product_type', 'business')
        
        # Intelligent brand name generation based on business type
        if 'coffee' in business_idea or 'cafe' in business_idea:
            brand_names = ["Brew Haven", "Coffee Craft", "Roast & Co", "The Daily Grind", "Bean Dreams"]
            color_palettes = [
                ["#8B4513", "#D2691E", "#F5DEB3", "#FFFFFF"],
                ["#6F4E37", "#CD853F", "#F4A460", "#FFF8DC"],
                ["#3C2415", "#8B4513", "#D2B48C", "#F5F5DC"]
            ]
        elif 'bakery' in business_idea or 'pastry' in business_idea:
            brand_names = ["Sweet Dreams", "Golden Crust", "Artisan Bake", "The Flour Mill", "Sunrise Bakery"]
            color_palettes = [
                ["#D2691E", "#F4A460", "#FFF8DC", "#8B4513"],
                ["#CD853F", "#F5DEB3", "#FFFFFF", "#A0522D"],
                ["#DAA520", "#F0E68C", "#FFFACD", "#B8860B"]
            ]
        elif 'tech' in business_idea or 'software' in business_idea or 'app' in business_idea:
            brand_names = ["TechFlow", "InnovateLabs", "CodeCraft", "Digital Wave", "NextGen Solutions"]
            color_palettes = [
                ["#0066CC", "#00CCFF", "#FFFFFF", "#E6F3FF"],
                ["#6633FF", "#9966FF", "#CCCCFF", "#F0F0FF"],
                ["#FF6600", "#FF9933", "#FFCC99", "#FFF3E6"]
            ]
        elif 'restaurant' in business_idea or 'food' in business_idea:
            brand_names = ["Savory Spot", "Fresh Plate", "Culinary Corner", "Taste Haven", "Fork & Flavor"]
            color_palettes = [
                ["#228B22", "#32CD32", "#98FB98", "#F0FFF0"],
                ["#DC143C", "#FF6347", "#FFB6C1", "#FFF0F5"],
                ["#FF8C00", "#FFD700", "#FFFFE0", "#FFF8DC"]
            ]
        else:
            # Generic business names
            words = business_idea.split()
            if len(words) >= 2:
                brand_names = [f"{words[0].capitalize()} {words[1].capitalize()}", f"{words[0].capitalize()}Co", f"Pro{words[1].capitalize()}"]
            else:
                brand_names = [f"{words[0].capitalize()} Pro", f"Elite {words[0].capitalize()}", f"{words[0].capitalize()} Solutions"]
            color_palettes = [
                ["#2C3E50", "#3498DB", "#E74C3C", "#F39C12"],
                ["#8E44AD", "#9B59B6", "#BDC3C7", "#ECF0F1"],
                ["#27AE60", "#2ECC71", "#F1C40F", "#E67E22"]
            ]
        
        # Select random options for variety
        import random
        brand_name = random.choice(brand_names)
        color_palette = random.choice(color_palettes)
        
        # Generate contextual logo prompt
        if 'coffee' in business_idea:
            logo_prompt = f"Modern coffee cup with steam rising, incorporating the text '{brand_name}' in elegant typography"
        elif 'bakery' in business_idea:
            logo_prompt = f"Artisanal bread or wheat symbol with warm colors, featuring '{brand_name}' in handcrafted font style"
        elif 'tech' in business_idea:
            logo_prompt = f"Clean, geometric design with tech elements like circuits or pixels, '{brand_name}' in modern sans-serif font"
        elif 'restaurant' in business_idea:
            logo_prompt = f"Elegant fork and knife or chef's hat symbol, '{brand_name}' in sophisticated serif typography"
        else:
            logo_prompt = f"Professional, minimalist logo design for '{brand_name}' representing {product_type} business"
        
        # Create branding data for interactive approval
        branding_data = {
            'brand_name': brand_name,
            'logo_prompt': logo_prompt,
            'color_palette': color_palette
        }
        
        # Interactive approval step for logo prompt (even in fallback mode)
        if self.interactive_approval:
            approved_logo_prompt = await self._request_logo_prompt_approval(
                logo_prompt, 
                branding_data, 
                business_info
            )
            logo_prompt = approved_logo_prompt
        
        # Fallback domain suggestions
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
        domain_suggestions = [f"{clean_name}.com", f"{clean_name}.co"]
        
        return BrandingResult(
            brand_name=brand_name,
            logo_prompt=logo_prompt,
            color_palette=color_palette,
            domain_suggestions=domain_suggestions
        )
    
    async def _request_logo_prompt_approval(
        self, 
        logo_prompt: str, 
        branding_data: Dict[str, Any], 
        business_info: Dict[str, Any]
    ) -> str:
        """
        Request user approval for the generated logo prompt.
        
        Args:
            logo_prompt: Generated logo prompt to review
            branding_data: Full branding data for context
            business_info: Original business information
            
        Returns:
            Approved logo prompt (original or regenerated)
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        
        console = Console()
        current_attempt = 1
        current_prompt = logo_prompt
        
        while True:  # Infinite loop - user controls when to stop
            # Display the logo prompt for review
            console.print("\n" + "="*60)
            console.print("🎨 [bold blue]Logo Prompt Review[/bold blue]")
            console.print("="*60)
            
            # Show business context
            console.print(f"\n📋 [bold]Business:[/bold] {business_info.get('business_idea', 'N/A')}")
            console.print(f"🏢 [bold]Brand Name:[/bold] {branding_data.get('brand_name', 'N/A')}")
            console.print(f"🎨 [bold]Colors:[/bold] {', '.join(branding_data.get('color_palette', []))}")
            
            # Show the generated logo prompt in a panel
            prompt_panel = Panel(
                current_prompt,
                title="Generated Logo Prompt",
                title_align="left",
                border_style="blue"
            )
            console.print("\n", prompt_panel)
            
            # Request user decision
            console.print("\n💡 [bold yellow]What would you like to do?[/bold yellow]")
            console.print("  • Type [green]'yes'[/green] to proceed with this prompt")
            console.print("  • Type [red]'no' or 'skip'[/red] to skip logo generation entirely")
            console.print("  • Type [blue]'try again' or 'redo'[/blue] to generate a new prompt")
            console.print("\n🚪 [dim]Exit Commands:[/dim]")
            console.print("  • [dim]'exit prompt'[/dim] → Use original prompt and continue")
            console.print("  • [dim]'exit agent'[/dim] → Quit branding agent completely") 
            console.print("  • [dim]'quit'[/dim] → Quit entire system")
            
            # Get user input
            user_response = Prompt.ask("\n[bold]Your decision", default="yes").strip()
            
            # Check for exit commands first
            user_lower = user_response.lower().strip()
            
            if user_lower in ['exit prompt', 'exit']:
                console.print("🚪 [dim]Exiting prompt approval - using original prompt[/dim]\n")
                return logo_prompt
                
            elif user_lower in ['exit agent', 'quit agent']:
                console.print("🚪 [yellow]Exiting branding agent completely[/yellow]\n")
                raise AgentExitException("User requested to exit branding agent")
                
            elif user_lower in ['quit', 'quit system', 'exit system']:
                console.print("🚪 [red]Quitting entire HeyJarvis system[/red]\n")
                raise SystemExitException("User requested to quit entire system")
            
            # Parse the response
            decision = self.response_parser.parse_approval_response(user_response)
            
            console.print(f"\n🤖 Interpreted as: [bold]{decision.intent.value}[/bold] (confidence: {decision.confidence:.2f})")
            
            # Handle the decision
            if decision.intent == ApprovalIntent.APPROVE and decision.confidence > 0.6:
                console.print("✅ [green]Proceeding with logo generation![/green]\n")
                return current_prompt
                
            elif decision.intent == ApprovalIntent.REJECT and decision.confidence > 0.6:
                console.print("❌ [red]Skipping logo generation[/red]\n")
                return ""  # Empty prompt means skip logo generation
                
            elif decision.intent == ApprovalIntent.REGENERATE and decision.confidence > 0.6:
                console.print("🔄 [blue]Generating new logo prompt...[/blue]\n")
                
                # Generate a new prompt with variation
                new_prompt = await self._regenerate_logo_prompt(business_info, branding_data, current_attempt)
                current_prompt = new_prompt
                # CRITICAL FIX: Update branding_data so next regeneration compares against current prompt
                branding_data['logo_prompt'] = new_prompt
                current_attempt += 1
                continue
                
            else:
                # Unclear or low confidence response
                suggestion = self.response_parser.suggest_clarification(decision)
                if suggestion:
                    console.print(f"❓ [yellow]{suggestion}[/yellow]\n")
                # Continue the loop - no timeout, user keeps trying
    
    async def _regenerate_logo_prompt(
        self, 
        business_info: Dict[str, Any], 
        branding_data: Dict[str, Any], 
        attempt: int
    ) -> str:
        """
        Generate a new variation of the logo prompt.
        
        Args:
            business_info: Original business information
            branding_data: Current branding data
            attempt: Current attempt number for variation
            
        Returns:
            New logo prompt variation
        """
        if not self.ai_engine:
            # No AI engine - inform user transparently
            from rich.console import Console
            console = Console()
            console.print("❌ [red]AI engine not available - cannot generate new variations[/red]")
            console.print("💡 [yellow]Please check AI configuration and try again[/yellow]")
            return branding_data.get('logo_prompt', 'Design a professional logo')
        
        # Add unique context to prevent any caching/similarity issues
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        variation_prompt = f"""[Generation ID: {unique_id}] Generate a completely different and creative logo design prompt for {branding_data.get('brand_name')} (a {business_info.get('business_idea')}). 

Previous approach: {branding_data.get('logo_prompt')[:100]}...

Create a new detailed logo prompt with a totally different creative style and approach. Use these colors: {', '.join(branding_data.get('color_palette', []))}.

Be specific and creative - make it unique from the previous one.

CRITICAL: Always end your logo prompt with "IMPORTANT: Spell the brand name exactly as: {branding_data.get('brand_name')}" to prevent spelling errors in generated logos.

[Attempt: {attempt}]"""
        
        try:
            self.logger.info(f"Starting AI regeneration call (attempt #{attempt}) with unique ID: {unique_id}")
            
            # NO TIMEOUT - user requested infinite regeneration capability
            # Let the AI take as long as it needs for quality results
            response = await self.ai_engine.generate(variation_prompt)
            
            self.logger.info(f"AI regeneration call completed successfully")
            new_prompt = response.content.strip()
            
            # Trust the LLM - minimal validation
            if len(new_prompt) > 20:
                return new_prompt
            else:
                self.logger.warning("AI returned very short response")
                return branding_data.get('logo_prompt', 'Design a professional logo')
            
        except Exception as e:
            self.logger.error(f"AI regeneration failed: {e}")
            from rich.console import Console
            console = Console()
            console.print(f"❌ [red]Failed to generate new prompt: {str(e)[:50]}...[/red]")
            console.print("💡 [yellow]Continuing with original prompt[/yellow]")
            return branding_data.get('logo_prompt', 'Design a professional logo')


# Agent metadata for registration
AGENT_METADATA = {
    "name": "BrandingAgent",
    "description": "AI-powered brand creation with interactive logo prompt approval",
    "capabilities": ["brand_generation", "logo_prompts", "market_research", "interactive_approval"],
    "inputs": ["business_idea", "user_request"],
    "outputs": ["brand_name", "logo_prompt", "color_palette", "domain_suggestions"],
    "interactive": True,
    "exit_commands": {
        "skip": "Skip logo generation entirely", 
        "exit_prompt": "Use original prompt and continue",
        "exit_agent": "Quit branding agent completely",
        "quit": "Quit entire HeyJarvis system"
    },
    "exceptions": ["AgentExitException", "SystemExitException"],
    "dependencies": ["anthropic", "rich", "utils.user_response_parser"],
    "coordination": ["works_with_logo_generation_agent", "works_with_market_research_agent"]
} 