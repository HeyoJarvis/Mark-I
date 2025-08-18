"""
Intent Parser for HeyJarvis Orchestration Layer

Provides intelligent routing of user requests to appropriate agents based on
semantic understanding rather than keyword matching.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Literal
from datetime import datetime
from dataclasses import dataclass

from pydantic import BaseModel, Field
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


from typing import Literal

IntentCategory = Literal[
    "branding", "sales", "marketing", "engineering", 
    "customer_support", "legal", "logistics", "finance", 
    "operations", "market_research", "general"
]

IntentConfidence = Literal["high", "medium", "low"]


class ParsedIntent(BaseModel):
    """Result of intent parsing."""
    primary_intent: IntentCategory = Field(..., description="Primary intent category")
    confidence: IntentConfidence = Field(..., description="Confidence level")
    confidence_score: float = Field(..., ge=0, le=1, description="Numeric confidence score")
    suggested_agents: List[str] = Field(default_factory=list, description="Suggested agent IDs")
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters")
    alternate_intents: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative intents")
    requires_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions for clarification")
    reasoning: str = Field(..., description="Explanation of intent classification")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Parsing timestamp")


class IntentPattern(BaseModel):
    """Pattern for intent matching."""
    category: IntentCategory
    patterns: List[str]
    priority: int = Field(default=1, description="Pattern priority (higher = more specific)")
    parameters: List[str] = Field(default_factory=list, description="Parameters to extract")
    confidence_boost: float = Field(default=0.0, description="Confidence boost for this pattern")


class IntentParser:
    """
    Intelligent intent parser that routes user requests to appropriate agents.
    
    Uses a combination of:
    1. Rule-based pattern matching for common intents
    2. AI-powered semantic understanding for complex requests
    3. Confidence scoring and fallback mechanisms
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the intent parser.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine for semantic understanding
        self._initialize_ai_engine()
        
        # Load intent patterns
        self._load_intent_patterns()
        
        # Agent mapping
        self.agent_mapping = {
            "branding": ["branding_agent", "website_generator_agent"],
            "sales": ["lead_scanner_agent", "outreach_composer_agent"],
            "marketing": ["content_creator_agent", "campaign_manager_agent"],
            "engineering": ["code_reviewer_agent", "architect_agent"],
            "customer_support": ["support_agent", "escalation_agent"],
            "legal": ["legal_reviewer_agent"],
            "logistics": ["inventory_agent", "shipping_agent"],
            "finance": ["accounting_agent", "budget_agent"],
            "operations": ["process_optimizer_agent"],
            "market_research": ["market_research_agent"],
            "general": ["general_assistant_agent"]
        }
        
        self.logger.info("IntentParser initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for semantic understanding."""
        try:
            # Get API key from environment or config
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using rule-based parsing only")
                self.ai_engine = None
                return
            
            # Configure AI engine
            engine_config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent classification
                enable_cache=True
            )
            
            self.ai_engine = AnthropicEngine(engine_config)
            self.logger.info("AI engine initialized for intent parsing")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    def _load_intent_patterns(self):
        """Load intent patterns for rule-based matching."""
        self.intent_patterns = [
            # Branding patterns
            IntentPattern(
                category="branding",
                patterns=[
                    r"brand(?:ing)?|logo|name|identity|visual|design",
                    r"come up with.*name|create.*brand|design.*logo",
                    r"business.*name|company.*name|product.*name",
                    r"color.*palette|brand.*colors|visual.*identity",
                    r"domain.*name|website.*name|online.*presence",
                    r"website|web\s*site|landing\s*page|homepage|site\s*map|sitemap|web\s*copy"
                ],
                priority=3,
                parameters=["business_type", "industry", "target_audience"],
                confidence_boost=0.2
            ),
            
            # Sales patterns
            IntentPattern(
                category="sales",
                patterns=[
                    r"lead|prospect|customer|sales|revenue|deal",
                    r"find.*leads|generate.*leads|qualify.*prospects",
                    r"outreach|email|campaign|follow.*up",
                    r"sales.*pipeline|conversion|close.*deal"
                ],
                priority=3,
                parameters=["target_market", "product", "budget"],
                confidence_boost=0.2
            ),
            
            # Market Research patterns
            IntentPattern(
                category="market_research",
                patterns=[
                    r"market.*research|market.*analysis|market.*intelligence",
                    r"competitor.*analysis|competitive.*landscape|competition",
                    r"market.*size|market.*opportunity|industry.*analysis",
                    r"customer.*insights|target.*market|customer.*research",
                    r"pricing.*analysis|market.*trends|industry.*trends",
                    r"feasibility.*study|market.*validation|business.*intelligence"
                ],
                priority=3,
                parameters=["industry", "geographic_market", "business_idea", "target_audience"],
                confidence_boost=0.25
            ),
            
            # Marketing patterns
            IntentPattern(
                category="marketing",
                patterns=[
                    r"marketing|campaign|advertisement|promotion",
                    r"content|social.*media|email.*marketing",
                    r"seo|search.*engine|google.*ads",
                    r"brand.*awareness|market.*research"
                ],
                priority=2,
                parameters=["campaign_type", "budget", "target_audience"],
                confidence_boost=0.15
            ),
            
            # Engineering patterns
            IntentPattern(
                category="engineering",
                patterns=[
                    r"code|programming|development|software|app",
                    r"bug|fix|debug|test|deploy",
                    r"architecture|system|database|api",
                    r"technical|implementation|coding"
                ],
                priority=2,
                parameters=["technology", "language", "framework"],
                confidence_boost=0.15
            ),
            
            # Customer Support patterns
            IntentPattern(
                category="customer_support",
                patterns=[
                    r"support|help|customer.*service|issue|problem",
                    r"complaint|ticket|escalation|resolution",
                    r"faq|documentation|troubleshoot"
                ],
                priority=2,
                parameters=["issue_type", "urgency", "customer_id"],
                confidence_boost=0.15
            ),
            
            # Legal patterns
            IntentPattern(
                category="legal",
                patterns=[
                    r"legal|contract|agreement|terms|privacy",
                    r"compliance|regulation|law|liability",
                    r"trademark|patent|copyright|intellectual.*property"
                ],
                priority=3,
                parameters=["document_type", "jurisdiction", "urgency"],
                confidence_boost=0.2
            ),
            
            # Logistics patterns
            IntentPattern(
                category="logistics",
                patterns=[
                    r"shipping|delivery|inventory|warehouse|supply.*chain",
                    r"logistics|fulfillment|order.*management",
                    r"tracking|freight|transportation"
                ],
                priority=2,
                parameters=["shipping_method", "destination", "weight"],
                confidence_boost=0.15
            ),
            
            # Finance patterns
            IntentPattern(
                category="finance",
                patterns=[
                    r"finance|accounting|budget|expense|revenue",
                    r"invoice|payment|billing|tax|audit",
                    r"financial.*report|profit.*loss|cash.*flow"
                ],
                priority=2,
                parameters=["report_type", "period", "amount"],
                confidence_boost=0.15
            ),
            
            # Operations patterns
            IntentPattern(
                category="operations",
                patterns=[
                    r"process|workflow|efficiency|optimization",
                    r"operations|procedure|standard.*operating",
                    r"automation|streamline|improve.*process"
                ],
                priority=2,
                parameters=["process_type", "department", "goal"],
                confidence_boost=0.15
            )
        ]
    
    async def parse_intent(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """
        Parse user intent from request.
        
        Args:
            user_request: The user's request text
            context: Optional context information
            
        Returns:
            ParsedIntent with classification results
        """
        self.logger.info(f"Parsing intent for request: {user_request[:100]}...")
        
        try:
            # Step 1: Rule-based pattern matching
            rule_based_result = self._rule_based_parsing(user_request)
            
            # Step 2: AI-powered semantic understanding (if available)
            if self.ai_engine:
                ai_result = await self._ai_semantic_parsing(user_request, context)
                
                # Combine results
                final_result = self._combine_parsing_results(rule_based_result, ai_result)
            else:
                final_result = rule_based_result
            
            # Step 3: Post-processing
            final_result = self._post_process_intent(final_result, user_request, context)
            
            self.logger.info(f"Intent parsed: {final_result.primary_intent} (confidence: {final_result.confidence})")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error parsing intent: {e}")
            return self._create_fallback_intent(user_request)
    
    def _rule_based_parsing(self, user_request: str) -> ParsedIntent:
        """Perform rule-based pattern matching."""
        request_lower = user_request.lower()
        best_match = None
        best_score = 0.0
        extracted_params = {}
        
        for pattern in self.intent_patterns:
            score = 0.0
            matched_patterns = []
            
            for pattern_text in pattern.patterns:
                if re.search(pattern_text, request_lower):
                    score += 1.0
                    matched_patterns.append(pattern_text)
            
            if score > 0:
                # Apply priority and confidence boost
                score = score * pattern.priority + pattern.confidence_boost
                
                if score > best_score:
                    best_score = score
                    best_match = pattern
                    
                    # Extract parameters if specified
                    for param in pattern.parameters:
                        param_value = self._extract_parameter(request_lower, param)
                        if param_value:
                            extracted_params[param] = param_value
        
        if best_match:
            confidence_score = min(best_score / 5.0, 0.9)  # Normalize to 0-0.9 range
            confidence = self._score_to_confidence(confidence_score)
            
            return ParsedIntent(
                primary_intent=best_match.category,
                confidence=confidence,
                confidence_score=confidence_score,
                suggested_agents=self.agent_mapping.get(best_match.category, []),
                extracted_parameters=extracted_params,
                reasoning=f"Matched patterns: {', '.join(matched_patterns)}"
            )
        else:
            return ParsedIntent(
                primary_intent="general",
                confidence="low",
                confidence_score=0.1,
                suggested_agents=self.agent_mapping.get("general", []),
                reasoning="No specific patterns matched"
            )
    
    async def _ai_semantic_parsing(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Use AI for semantic understanding of complex requests."""
        try:
            # Create prompt for AI classification
            prompt = self._create_classification_prompt(user_request, context)
            
            # Get AI response
            response = await self.ai_engine.generate(prompt)
            
            # Parse AI response
            ai_result = self._parse_ai_classification(response.content)
            
            return ai_result
            
        except Exception as e:
            self.logger.error(f"AI parsing failed: {e}")
            return ParsedIntent(
                primary_intent="general",
                confidence="low",
                confidence_score=0.1,
                reasoning=f"AI parsing failed: {e}"
            )
    
    def _create_classification_prompt(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create prompt for AI intent classification."""
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        prompt = f"""
You are an intent classification system for a business AI platform. Analyze the user request and classify it into the appropriate category.

User Request: "{user_request}"{context_str}

Available Categories:
- branding: Brand names, logos, visual identity, domain names
- sales: Lead generation, prospecting, sales pipeline, outreach
- marketing: Campaigns, content, advertising, social media
- engineering: Code, development, technical implementation, debugging
- customer_support: Customer service, help, issue resolution
- legal: Contracts, compliance, legal documents, intellectual property
- logistics: Shipping, inventory, supply chain, delivery
- finance: Accounting, budgeting, financial reporting, invoicing
- operations: Process optimization, workflow, efficiency
- general: General assistance, unclear requests

Return your response in this exact JSON format:
{{
  "primary_intent": "category_name",
  "confidence_score": 0.85,
  "extracted_parameters": {{
    "business_type": "extracted_value",
    "industry": "extracted_value"
  }},
  "reasoning": "Explanation of classification",
  "alternate_intents": [
    {{
      "category": "alternative_category",
      "confidence": 0.3,
      "reasoning": "Why this alternative"
    }}
  ],
  "requires_clarification": false,
  "clarification_questions": []
}}

Ensure the response is valid JSON and all fields are properly filled.
"""
        return prompt
    
    def _parse_ai_classification(self, ai_response: str) -> ParsedIntent:
        """Parse AI classification response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(ai_response)
            
            # Validate and convert
            primary_intent = data.get('primary_intent', 'general')
            confidence_score = float(data.get('confidence_score', 0.5))
            confidence = self._score_to_confidence(confidence_score)
            
            return ParsedIntent(
                primary_intent=primary_intent,
                confidence=confidence,
                confidence_score=confidence_score,
                suggested_agents=self.agent_mapping.get(primary_intent, []),
                extracted_parameters=data.get('extracted_parameters', {}),
                alternate_intents=data.get('alternate_intents', []),
                requires_clarification=data.get('requires_clarification', False),
                clarification_questions=data.get('clarification_questions', []),
                reasoning=data.get('reasoning', 'AI classification')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI classification: {e}")
            raise
    
    def _combine_parsing_results(self, rule_result: ParsedIntent, ai_result: ParsedIntent) -> ParsedIntent:
        """Combine rule-based and AI parsing results."""
        # If AI has higher confidence, use AI result
        if ai_result.confidence_score > rule_result.confidence_score:
            return ai_result
        else:
            return rule_result
    
    def _post_process_intent(self, intent: ParsedIntent, user_request: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Post-process intent results."""
        # Add context-based parameters
        if context:
            intent.extracted_parameters.update(context)
        
        # Check for clarification needs
        if intent.confidence_score < 0.3:
            intent.requires_clarification = True
            intent.clarification_questions.append("Could you provide more details about what you're looking for?")
        
        return intent
    
    def _extract_parameter(self, text: str, param_name: str) -> Optional[str]:
        """Extract parameter value from text."""
        # Simple parameter extraction - could be enhanced with NLP
        param_patterns = {
            "business_type": r"(?:business|company|startup|venture|enterprise)",
            "industry": r"(?:tech|software|ecommerce|healthcare|finance|education|retail)",
            "target_audience": r"(?:customers|users|clients|consumers|professionals)",
            "budget": r"(?:budget|cost|price|investment|funding)",
            "urgency": r"(?:urgent|asap|immediately|soon|quickly)"
        }
        
        if param_name in param_patterns:
            match = re.search(param_patterns[param_name], text)
            if match:
                return match.group(0)
        
        return None
    
    def _score_to_confidence(self, score: float) -> IntentConfidence:
        """Convert numeric score to confidence level."""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _create_fallback_intent(self, user_request: str) -> ParsedIntent:
        """Create fallback intent when parsing fails."""
        return ParsedIntent(
            primary_intent="general",
            confidence="low",
            confidence_score=0.1,
            suggested_agents=self.agent_mapping.get("general", []),
            reasoning="Fallback intent due to parsing error",
            requires_clarification=True,
            clarification_questions=["I'm not sure I understand. Could you rephrase your request?"]
        ) 