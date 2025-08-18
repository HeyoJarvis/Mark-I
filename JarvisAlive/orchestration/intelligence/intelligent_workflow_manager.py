"""
IntelligentWorkflowManager - AI-powered workflow suggestion and management system.

This component uses LLM intelligence to analyze workflow context and suggest
logical next steps, creating a truly intelligent workflow orchestration experience.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class IntelligentWorkflowManager:
    """
    AI-powered workflow manager that suggests next workflows based on context.
    
    Features:
    - LLM-powered workflow suggestions
    - Context-aware recommendations
    - Learning from workflow patterns
    - Intelligent business flow analysis
    - Multi-workflow coordination
    """
    
    def __init__(self, workflow_brain, config: Dict[str, Any]):
        """Initialize the Intelligent Workflow Manager."""
        self.workflow_brain = workflow_brain
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine for suggestions
        self._initialize_ai_engine()
        
        # Workflow pattern learning
        self.workflow_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.business_context: Dict[str, Any] = {}
        self.suggestion_history: List[Dict[str, Any]] = []
        
        # Common workflow sequences
        self.common_sequences = {
            'business_creation': [
                'market_research',
                'branding',
                'business_plan',
                'marketing_strategy',
                'sales_planning'
            ],
            'product_launch': [
                'market_research',
                'competitive_analysis', 
                'branding',
                'marketing_strategy',
                'launch_planning'
            ],
            'brand_development': [
                'market_research',
                'brand_strategy',
                'visual_identity',
                'brand_guidelines',
                'brand_implementation'
            ]
        }
        
        self.logger.info("IntelligentWorkflowManager initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for intelligent suggestions."""
        try:
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using rule-based suggestions")
                self.ai_engine = None
                return
            
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.4,  # Balanced creativity for suggestions
                enable_cache=False,
                timeout_seconds=60
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("Workflow suggestion AI engine initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize suggestion AI engine: {e}")
            self.ai_engine = None
    
    async def suggest_next_workflows(
        self,
        workflow_context: Dict[str, Any],
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent next workflow suggestions based on context.
        
        Args:
            workflow_context: Dictionary of completed workflows and their results
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of workflow suggestions with confidence scores and reasoning
        """
        try:
            if not workflow_context:
                return await self._get_startup_suggestions()
            
            # Use AI engine if available, otherwise fallback to rule-based
            if self.ai_engine:
                suggestions = await self._generate_ai_suggestions(workflow_context, max_suggestions)
            else:
                suggestions = await self._generate_rule_based_suggestions(workflow_context, max_suggestions)
            
            # Record suggestion history for learning
            self.suggestion_history.append({
                'timestamp': datetime.utcnow(),
                'context': self._summarize_context(workflow_context),
                'suggestions': suggestions
            })
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating workflow suggestions: {e}")
            return await self._get_fallback_suggestions()
    
    async def _generate_ai_suggestions(
        self,
        workflow_context: Dict[str, Any],
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered workflow suggestions."""
        
        # Prepare context for AI
        context_summary = self._prepare_ai_context(workflow_context)
        
        prompt = f"""You are an intelligent business workflow orchestrator. Based on the completed workflows and their results, suggest the next logical business workflows that would be most beneficial.

COMPLETED WORKFLOWS CONTEXT:
{context_summary}

AVAILABLE WORKFLOW TYPES:
- market_research: Analyze market opportunities, competition, and trends
- branding: Create brand identity, logos, visual design, and brand strategy  
- business_planning: Develop business plans, financial projections, and strategy
- marketing_strategy: Create marketing campaigns, customer acquisition plans
- sales_planning: Develop sales processes, lead generation, and sales strategy
- competitive_analysis: Analyze competitors and market positioning
- product_development: Plan and design products or services
- financial_planning: Create budgets, funding strategies, and financial models
- operational_planning: Design business operations, processes, and workflows
- digital_presence: Build websites, social media strategy, online presence

INSTRUCTIONS:
1. Analyze the completed workflows and identify logical next steps
2. Consider business development flow and dependencies between workflows
3. Suggest workflows that build upon completed work
4. Provide specific, actionable workflow suggestions
5. Include confidence scores (0.0-1.0) based on logical flow
6. Explain reasoning for each suggestion

Return a JSON array of suggestions in this format:
[
  {{
    "title": "Workflow Title",
    "workflow_type": "workflow_type_from_list",
    "suggested_prompt": "Specific prompt to execute this workflow",
    "confidence": 0.85,
    "reason": "Why this workflow makes sense next",
    "dependencies": ["list", "of", "dependent", "workflow", "types"],
    "business_value": "How this adds business value"
  }}
]

Focus on practical, high-value next steps that build a complete business foundation."""

        try:
            response = await self.ai_engine.generate_response(prompt)
            
            # Parse AI response
            suggestions = self._parse_ai_suggestions(response, max_suggestions)
            return suggestions
            
        except Exception as e:
            self.logger.error(f"AI suggestion generation failed: {e}")
            return await self._generate_rule_based_suggestions(workflow_context, max_suggestions)
    
    def _prepare_ai_context(self, workflow_context: Dict[str, Any]) -> str:
        """Prepare workflow context for AI analysis."""
        context_lines = []
        
        for workflow_id, info in workflow_context.items():
            request = info.get('request', 'Unknown request')
            workflow_type = info.get('type', 'unknown')
            success = info.get('success', False)
            timestamp = info.get('timestamp', datetime.utcnow())
            
            status = "✅ Completed successfully" if success else "❌ Failed"
            
            context_lines.append(f"""
WORKFLOW: {workflow_id}
- Type: {workflow_type}
- Request: "{request}"
- Status: {status}
- Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
""")
        
        return '\n'.join(context_lines)
    
    def _parse_ai_suggestions(self, response: str, max_suggestions: int) -> List[Dict[str, Any]]:
        """Parse and validate AI-generated suggestions."""
        try:
            # Extract JSON from response
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_text = response[json_start:json_end].strip()
            elif '[' in response and ']' in response:
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                json_text = response[json_start:json_end]
            else:
                raise ValueError("No JSON found in AI response")
            
            suggestions = json.loads(json_text)
            
            # Validate and clean suggestions
            validated_suggestions = []
            for suggestion in suggestions[:max_suggestions]:
                if self._validate_suggestion(suggestion):
                    validated_suggestions.append(suggestion)
            
            return validated_suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI suggestions: {e}")
            self.logger.debug(f"AI Response: {response}")
            return []
    
    def _validate_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Validate a suggestion has required fields."""
        required_fields = ['title', 'workflow_type', 'suggested_prompt', 'confidence', 'reason']
        
        for field in required_fields:
            if field not in suggestion:
                return False
        
        # Validate confidence is a number between 0 and 1
        try:
            confidence = float(suggestion['confidence'])
            if not 0.0 <= confidence <= 1.0:
                suggestion['confidence'] = max(0.0, min(1.0, confidence))
        except:
            suggestion['confidence'] = 0.5
        
        return True
    
    async def _generate_rule_based_suggestions(
        self,
        workflow_context: Dict[str, Any],
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Generate rule-based workflow suggestions."""
        suggestions = []
        
        # Analyze completed workflow types
        completed_types = set()
        latest_type = None
        business_domains = set()
        
        for workflow_id, info in workflow_context.items():
            workflow_type = info.get('type', 'unknown')
            completed_types.add(workflow_type)
            latest_type = workflow_type
            
            # Infer business domain from request
            request = info.get('request', '').lower()
            if any(word in request for word in ['coffee', 'restaurant', 'food', 'bakery']):
                business_domains.add('food_service')
            elif any(word in request for word in ['tech', 'software', 'app', 'digital']):
                business_domains.add('technology')
            elif any(word in request for word in ['retail', 'store', 'shop', 'sales']):
                business_domains.add('retail')
        
        # Rule-based suggestion logic
        if 'market_research' in completed_types and 'branding' not in completed_types:
            suggestions.append({
                'title': 'Brand Identity Development',
                'workflow_type': 'branding',
                'suggested_prompt': 'Create a complete brand identity including logo, colors, and brand guidelines',
                'confidence': 0.9,
                'reason': 'Natural next step after market research to establish brand presence',
                'dependencies': ['market_research'],
                'business_value': 'Establishes professional brand identity and market positioning'
            })
        
        if 'branding' in completed_types and 'marketing_strategy' not in completed_types:
            suggestions.append({
                'title': 'Marketing Strategy Development',
                'workflow_type': 'marketing_strategy',
                'suggested_prompt': 'Develop a comprehensive marketing strategy and customer acquisition plan',
                'confidence': 0.85,
                'reason': 'Marketing strategy builds upon completed branding work',
                'dependencies': ['branding'],
                'business_value': 'Creates systematic approach to customer acquisition and growth'
            })
        
        if latest_type == 'branding' and 'business_planning' not in completed_types:
            suggestions.append({
                'title': 'Business Plan Creation',
                'workflow_type': 'business_planning',
                'suggested_prompt': 'Create a comprehensive business plan with financial projections and strategy',
                'confidence': 0.8,
                'reason': 'Business planning formalizes the foundation created by branding and market research',
                'dependencies': ['branding', 'market_research'],
                'business_value': 'Provides roadmap for business growth and attracts investors'
            })
        
        # Domain-specific suggestions
        if 'food_service' in business_domains:
            if 'operational_planning' not in completed_types:
                suggestions.append({
                    'title': 'Restaurant Operations Planning',
                    'workflow_type': 'operational_planning',
                    'suggested_prompt': 'Design restaurant operations, kitchen workflow, and service processes',
                    'confidence': 0.75,
                    'reason': 'Food service businesses require detailed operational planning',
                    'business_value': 'Ensures smooth operations and quality customer experience'
                })
        
        # Add competitive analysis if not done
        if len(completed_types) > 0 and 'competitive_analysis' not in completed_types:
            suggestions.append({
                'title': 'Competitive Analysis',
                'workflow_type': 'competitive_analysis',
                'suggested_prompt': 'Analyze competitors, market positioning, and competitive advantages',
                'confidence': 0.7,
                'reason': 'Understanding competition is crucial for strategic positioning',
                'business_value': 'Identifies opportunities and threats in the market'
            })
        
        return suggestions[:max_suggestions]
    
    async def _get_startup_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for users just starting out."""
        return [
            {
                'title': 'Market Research Analysis',
                'workflow_type': 'market_research',
                'suggested_prompt': 'Conduct market research for my business idea',
                'confidence': 0.95,
                'reason': 'Market research is the foundation of any successful business',
                'business_value': 'Validates business opportunity and identifies target market'
            },
            {
                'title': 'Brand Identity Creation',
                'workflow_type': 'branding',
                'suggested_prompt': 'Create a brand identity and logo for my business',
                'confidence': 0.9,
                'reason': 'Strong branding differentiates your business in the market',
                'business_value': 'Creates professional appearance and brand recognition'
            },
            {
                'title': 'Business Plan Development',
                'workflow_type': 'business_planning',
                'suggested_prompt': 'Develop a comprehensive business plan with financial projections',
                'confidence': 0.85,
                'reason': 'Business planning provides roadmap and attracts funding',
                'business_value': 'Guides strategic decisions and secures investment'
            }
        ]
    
    async def _get_fallback_suggestions(self) -> List[Dict[str, Any]]:
        """Get fallback suggestions when other methods fail."""
        return [
            {
                'title': 'Business Assessment',
                'workflow_type': 'business_planning',
                'suggested_prompt': 'Assess my current business situation and identify opportunities',
                'confidence': 0.6,
                'reason': 'General business assessment is always valuable',
                'business_value': 'Identifies strengths, weaknesses, and opportunities'
            }
        ]
    
    def _summarize_context(self, workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of workflow context for learning."""
        summary = {
            'total_workflows': len(workflow_context),
            'workflow_types': list(set(info.get('type') for info in workflow_context.values())),
            'success_rate': sum(1 for info in workflow_context.values() if info.get('success', False)) / len(workflow_context) if workflow_context else 0,
            'latest_timestamp': max((info.get('timestamp', datetime.min) for info in workflow_context.values()), default=datetime.min)
        }
        return summary
    
    def update_business_context(self, context_update: Dict[str, Any]):
        """Update business context with new information."""
        self.business_context.update(context_update)
        self.logger.info(f"Updated business context: {context_update}")
    
    def get_workflow_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get learned workflow patterns."""
        return self.workflow_patterns.copy()
    
    def add_workflow_pattern(self, pattern_name: str, workflow_sequence: List[str]):
        """Add a new workflow pattern."""
        if pattern_name not in self.workflow_patterns:
            self.workflow_patterns[pattern_name] = []
        
        self.workflow_patterns[pattern_name].append({
            'sequence': workflow_sequence,
            'timestamp': datetime.utcnow(),
            'usage_count': 1
        })
        
        self.logger.info(f"Added workflow pattern '{pattern_name}': {workflow_sequence}") 