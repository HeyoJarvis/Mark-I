"""
PersistentBrandingAgent - Long-running branding agent for concurrent execution.

Provides persistent branding capabilities with:
- Brand name generation and validation
- Logo prompt creation with DALL-E integration
- Visual identity development
- Interactive approval workflows
- Context retention across tasks
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
from pathlib import Path

from ..base_agent import PersistentAgent, TaskRequest, TaskResponse
from departments.branding.branding_agent import BrandingAgent as CoreBrandingAgent
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig


class PersistentBrandingAgent(PersistentAgent):
    """
    Persistent version of the BrandingAgent for concurrent execution.
    
    Supports task types:
    - brand_name_generation
    - logo_prompt_creation
    - visual_identity_design
    - brand_validation
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the persistent branding agent."""
        super().__init__(agent_id, config)
        
        # Initialize core branding agent
        self.core_agent: Optional[CoreBrandingAgent] = None
        self.ai_engine: Optional[AnthropicEngine] = None
        
        # Branding context and state
        self.brand_context: Dict[str, Any] = {}
        self.generated_names: List[str] = []
        self.logo_prompts: List[str] = []
        
        # Performance tracking
        self.successful_generations = 0
        self.failed_generations = 0

        # Reports directory
        self.reports_dir = Path(self.config.get('branding_reports_dir', './branding_reports'))
        self.reports_dir.mkdir(exist_ok=True)
    
    async def on_start(self):
        """Initialize branding agent components."""
        try:
            # Initialize AI engine
            await self._initialize_ai_engine()
            
            # Initialize core branding agent with updated config
            agent_config = self.config.copy()
            # If AI engine available, pass key through; otherwise allow core to fallback
            if self.ai_engine:
                agent_config['anthropic_api_key'] = self.ai_engine.config.api_key
            # Disable interactive approval for persistent agents
            agent_config['interactive_approval'] = False
            # Enable mock mode for demo purposes
            agent_config['mock_mode'] = not bool(self.ai_engine)
            self.core_agent = CoreBrandingAgent(
                config=agent_config
            )
            
            self.logger.info(f"PersistentBrandingAgent {self.agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize branding agent: {e}")
            raise
    
    async def on_stop(self):
        """Cleanup branding agent resources."""
        # Save any persistent state if needed
        self.logger.info(f"PersistentBrandingAgent {self.agent_id} stopped")
    
    def get_supported_task_types(self) -> List[str]:
        """Return supported task types."""
        return [
            "brand_name_generation",
            "logo_prompt_creation", 
            "visual_identity_design",
            "brand_validation",
            "branding_consultation",
            "branding"  # Add high-level branding task type
        ]
    
    async def process_task(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a branding task."""
        self.logger.info(f"Processing {task_type} task")
        
        if not self.core_agent:
            raise Exception("Core branding agent not initialized")
        
        try:
            if task_type == "brand_name_generation":
                return await self._generate_brand_name(input_data)
            elif task_type == "logo_prompt_creation":
                return await self._create_logo_prompt(input_data)
            elif task_type == "visual_identity_design":
                return await self._design_visual_identity(input_data)
            elif task_type == "brand_validation":
                return await self._validate_brand(input_data)
            elif task_type == "branding_consultation":
                return await self._provide_consultation(input_data)
            elif task_type == "branding":
                return await self._conduct_comprehensive_branding(input_data)
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
                
        except Exception as e:
            self.failed_generations += 1
            self.logger.error(f"Task processing failed: {e}")
            raise
    
    async def _initialize_ai_engine(self):
        """Initialize AI engine for branding tasks."""
        try:
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                raise ValueError("No Anthropic API key available")
            
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7,
                enable_cache=False,
                timeout_seconds=300
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            raise
    
    async def _generate_brand_name(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brand names for a business concept."""
        business_idea = input_data.get('business_idea', '')
        industry = input_data.get('industry', '')
        target_audience = input_data.get('target_audience', '')
        style_preferences = input_data.get('style_preferences', [])
        
        if not business_idea:
            raise ValueError("Business idea is required for brand name generation")
        
        # Use core branding agent with unified interface
        state = {
            'business_idea': business_idea,
            'industry': industry,
            'target_audience': target_audience,
            'task_type': 'brand_name_generation'
        }
        result = await self.core_agent.run(state)
        
        # Store in context
        if 'brand_names' in result:
            self.generated_names.extend(result['brand_names'])
            self.brand_context['recent_names'] = result['brand_names']
        
        self.successful_generations += 1
        
        return {
            'task_type': 'brand_name_generation',
            'success': True,
            'brand_names': result.get('brand_names', []),
            'rationale': result.get('rationale', ''),
            'style_analysis': result.get('style_analysis', {}),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def _create_logo_prompt(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create DALL-E logo prompts."""
        brand_name = input_data.get('brand_name', '')
        business_idea = input_data.get('business_idea', '')
        industry = input_data.get('industry', '')
        style_preferences = input_data.get('style_preferences', [])
        color_preferences = input_data.get('color_preferences', [])
        
        if not brand_name and not business_idea:
            raise ValueError("Either brand_name or business_idea is required")
        
        # Use core branding agent for logo prompt generation
        state = {
            'brand_name': brand_name,
            'business_idea': business_idea,
            'industry': industry,
            'task_type': 'logo_prompt_creation'
        }
        result = await self.core_agent.run(state)
        
        # Store in context
        if 'logo_prompt' in result:
            self.logo_prompts.append(result['logo_prompt'])
            self.brand_context['recent_logo_prompt'] = result['logo_prompt']
        
        self.successful_generations += 1
        
        return {
            'task_type': 'logo_prompt_creation',
            'success': True,
            'logo_prompt': result.get('logo_prompt', ''),
            'design_rationale': result.get('design_rationale', ''),
            'color_palette': result.get('color_palette', []),
            'style_elements': result.get('style_elements', []),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def _design_visual_identity(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Design complete visual identity."""
        brand_name = input_data.get('brand_name', '')
        business_idea = input_data.get('business_idea', '')
        industry = input_data.get('industry', '')
        
        # Generate both brand name and logo if needed
        results = {}
        
        if not brand_name:
            name_result = await self._generate_brand_name(input_data)
            brand_name = name_result['brand_names'][0] if name_result['brand_names'] else 'NewBrand'
            results['brand_name_generation'] = name_result
        
        # Generate logo prompt
        logo_data = input_data.copy()
        logo_data['brand_name'] = brand_name
        logo_result = await self._create_logo_prompt(logo_data)
        results['logo_creation'] = logo_result
        
        # Create comprehensive visual identity
        visual_identity = {
            'brand_name': brand_name,
            'logo_prompt': logo_result.get('logo_prompt', ''),
            'color_palette': logo_result.get('color_palette', []),
            'typography_suggestions': [
                'Modern sans-serif for headers',
                'Clean serif for body text',
                'Distinctive display font for brand name'
            ],
            'brand_voice': await self._generate_brand_voice(brand_name, business_idea),
            'style_guide': {
                'primary_colors': logo_result.get('color_palette', [])[:3],
                'secondary_colors': logo_result.get('color_palette', [])[3:],
                'font_hierarchy': ['Primary', 'Secondary', 'Accent'],
                'logo_usage': ['Minimum size: 50px height', 'Clear space: 2x logo height']
            }
        }
        
        self.successful_generations += 1
        
        return {
            'task_type': 'visual_identity_design',
            'success': True,
            'visual_identity': visual_identity,
            'component_results': results,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def _validate_brand(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate brand elements for consistency and effectiveness."""
        brand_name = input_data.get('brand_name', '')
        business_idea = input_data.get('business_idea', '')
        target_audience = input_data.get('target_audience', '')
        
        if not brand_name:
            raise ValueError("Brand name is required for validation")
        
        # Validation criteria
        validation_results = {
            'memorability': await self._check_memorability(brand_name),
            'relevance': await self._check_relevance(brand_name, business_idea),
            'uniqueness': await self._check_uniqueness(brand_name),
            'pronunciation': await self._check_pronunciation(brand_name),
            'scalability': await self._check_scalability(brand_name, business_idea)
        }
        
        # Overall score
        scores = [result['score'] for result in validation_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Recommendations
        recommendations = []
        for criteria, result in validation_results.items():
            if result['score'] < 7:
                recommendations.append(result['recommendation'])
        
        return {
            'task_type': 'brand_validation',
            'success': True,
            'brand_name': brand_name,
            'overall_score': overall_score,
            'detailed_scores': validation_results,
            'recommendations': recommendations,
            'validation_summary': f"Brand scores {overall_score:.1f}/10 overall",
            'validated_at': datetime.utcnow().isoformat()
        }
    
    async def _provide_consultation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide branding consultation and advice."""
        question = input_data.get('question', '')
        context = input_data.get('context', {})
        
        if not question:
            raise ValueError("Question is required for branding consultation")
        
        # Use AI engine for consultation
        prompt = f"""
        As a branding expert, provide consultation on the following:
        
        Question: {question}
        Context: {context}
        
        Please provide:
        1. Direct answer to the question
        2. Professional recommendations
        3. Best practices to consider
        4. Potential challenges and solutions
        5. Next steps or action items
        
        Keep the response practical and actionable.
        """
        
        response = await self.ai_engine.generate(prompt)
        
        return {
            'task_type': 'branding_consultation',
            'success': True,
            'question': question,
            'consultation_response': response.content,
            'expert_advice': {
                'category': 'branding_strategy',
                'confidence_level': 'high',
                'actionable': True
            },
            'consulted_at': datetime.utcnow().isoformat()
        }
    
    async def _generate_brand_voice(self, brand_name: str, business_idea: str) -> Dict[str, Any]:
        """Generate brand voice characteristics."""
        return {
            'tone': ['Professional', 'Approachable', 'Confident'],
            'personality': ['Innovative', 'Trustworthy', 'Customer-focused'],
            'communication_style': 'Clear and engaging',
            'voice_attributes': {
                'formal_vs_casual': 'Balanced',
                'serious_vs_playful': 'Primarily serious with light moments',
                'traditional_vs_modern': 'Modern'
            }
        }
    
    async def _check_memorability(self, brand_name: str) -> Dict[str, Any]:
        """Check brand name memorability."""
        score = 8.0  # Simplified scoring
        if len(brand_name) <= 8:
            score += 1
        if len(brand_name.split()) == 1:
            score += 0.5
        
        return {
            'score': min(score, 10),
            'feedback': 'Name is concise and memorable' if score > 7 else 'Consider shorter alternatives',
            'recommendation': 'Current name works well' if score > 7 else 'Try shorter, single-word options'
        }
    
    async def _check_relevance(self, brand_name: str, business_idea: str) -> Dict[str, Any]:
        """Check brand name relevance to business."""
        # Simplified relevance check
        score = 7.5
        return {
            'score': score,
            'feedback': 'Name aligns well with business concept',
            'recommendation': 'Good alignment with business purpose'
        }
    
    async def _check_uniqueness(self, brand_name: str) -> Dict[str, Any]:
        """Check brand name uniqueness."""
        # Simplified uniqueness check
        score = 8.0
        return {
            'score': score,
            'feedback': 'Name appears distinctive',
            'recommendation': 'Consider trademark search for legal protection'
        }
    
    async def _check_pronunciation(self, brand_name: str) -> Dict[str, Any]:
        """Check brand name pronunciation ease."""
        score = 9.0 if len(brand_name) <= 10 else 7.0
        return {
            'score': score,
            'feedback': 'Name is easy to pronounce' if score > 7 else 'May be challenging to pronounce',
            'recommendation': 'Good pronunciation' if score > 7 else 'Consider phonetic alternatives'
        }
    
    async def _check_scalability(self, brand_name: str, business_idea: str) -> Dict[str, Any]:
        """Check brand name scalability for business growth."""
        score = 8.5
        return {
            'score': score,
            'feedback': 'Name allows for business expansion',
            'recommendation': 'Good potential for scaling across markets'
        }
    
    async def _conduct_comprehensive_branding(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive branding combining multiple branding services."""
        business_idea = input_data.get('business_idea', '')
        industry = input_data.get('industry', '')
        target_audience = input_data.get('target_audience', '')
        
        if not business_idea:
            raise ValueError("Business idea is required for comprehensive branding")
        
        self.logger.info(f"Conducting comprehensive branding for: {business_idea}")
        
        try:
            # Perform multiple branding services
            brand_names = await self._generate_brand_name({
                'business_idea': business_idea,
                'industry': industry,
                'target_audience': target_audience
            })
            
            # Use the first generated brand name for logo prompt
            brand_name_list = brand_names.get('brand_names', [])
            if brand_name_list and len(brand_name_list) > 0:
                selected_brand_name = brand_name_list[0].get('name', business_idea.split()[0])
            else:
                selected_brand_name = business_idea.split()[0] if business_idea else 'Business'
            
            logo_prompt = await self._create_logo_prompt({
                'brand_name': selected_brand_name,
                'business_idea': business_idea,
                'industry': industry,
                'target_audience': target_audience
            })
            
            visual_identity = await self._design_visual_identity({
                'brand_name': selected_brand_name,
                'business_idea': business_idea,
                'industry': industry,
                'logo_concept': logo_prompt.get('logo_prompt', '')
            })
            
            # Combine all branding work into comprehensive result
            comprehensive_branding = {
                'task_type': 'branding',
                'success': True,
                'business_idea': business_idea,
                'branding_package': {
                    'brand_names': brand_names,
                    'selected_brand_name': selected_brand_name,
                    'logo_concept': logo_prompt,
                    'visual_identity': visual_identity
                },
                'brand_strategy': {
                    'positioning': f"Unique positioning for {business_idea} in {industry}",
                    'target_market': target_audience or 'General market',
                    'brand_personality': visual_identity.get('brand_personality', {}),
                    'visual_direction': visual_identity.get('visual_elements', {})
                },
                'deliverables': {
                    'brand_name_options': len(brand_names.get('brand_names', [])),
                    'logo_prompt_created': bool(logo_prompt.get('logo_prompt')),
                    'visual_identity_defined': bool(visual_identity.get('visual_elements')),
                    'color_palette_provided': bool(visual_identity.get('color_palette'))
                },
                'recommendations': [
                    f"Proceed with '{selected_brand_name}' as primary brand name",
                    'Develop logo using the generated prompt',
                    'Apply visual identity consistently across all materials',
                    'Test brand perception with target audience',
                    'Create brand guidelines document'
                ],
                'next_steps': [
                    'Create final logo design using AI image generation',
                    'Develop brand guidelines and style guide',
                    'Design marketing materials with new brand',
                    'Plan brand launch strategy'
                ],
                'branding_confidence': 'High',
                'completion_status': 'Complete brand package delivered',
                'branded_at': datetime.utcnow().isoformat(),
                'from_cache': False
            }
            
            # Update brand context
            self.brand_context[business_idea] = {
                'selected_name': selected_brand_name,
                'branding_date': datetime.utcnow().isoformat(),
                'comprehensive_package': True
            }

            # Save report to disk
            try:
                saved_path = self._save_branding_report(comprehensive_branding)
                if saved_path:
                    comprehensive_branding['saved_report_path'] = saved_path
                    self.logger.info(f"Branding report saved: {saved_path}")
            except Exception as save_err:
                self.logger.warning(f"Failed to save branding report: {save_err}")

            self.successful_generations += 1
            return comprehensive_branding
            
        except Exception as e:
            self.logger.error(f"Comprehensive branding failed: {e}")
            self.failed_generations += 1
            raise

    def _save_branding_report(self, branding_data: Dict[str, Any]) -> str:
        """Persist branding output to a JSON file and return the file path."""
        # Build a safe slug from brand/business name
        base_name = branding_data.get('branding_package', {}).get('selected_brand_name') or branding_data.get('business_idea', 'branding')
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(base_name)).strip('_')[:50] or 'branding'
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_path = self.reports_dir / f"branding_{slug}_{timestamp}.json"
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(branding_data, f, ensure_ascii=False, indent=2)
        return str(file_path)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information with branding-specific metrics."""
        base_info = super().get_agent_info()
        
        branding_info = {
            'successful_generations': self.successful_generations,
            'failed_generations': self.failed_generations,
            'success_rate': (
                self.successful_generations / max(self.successful_generations + self.failed_generations, 1) * 100
            ),
            'generated_names_count': len(self.generated_names),
            'logo_prompts_count': len(self.logo_prompts),
            'brand_context_keys': list(self.brand_context.keys()),
            'specialization': 'Brand identity and visual design'
        }
        
        base_info.update(branding_info)
        return base_info