"""
Semantic Request Parser - Single AI call for understanding business context and direct agent mapping

This replaces the multi-step IntentParser with a semantic understanding approach that:
1. Makes ONE AI call to fully understand the request
2. Maps directly to agent capabilities (not departments)  
3. Preserves context throughout execution
4. Eliminates unnecessary routing layers
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """Strategy for executing the request."""
    SINGLE_AGENT = "single_agent"        # One agent can handle this alone
    PARALLEL_MULTI = "parallel_multi"    # Multiple agents in parallel
    SEQUENTIAL_MULTI = "sequential_multi"  # Multiple agents with dependencies
    HYBRID = "hybrid"                    # Mix of parallel and sequential


class CapabilityCategory(str, Enum):
    """Core capability categories agents can provide."""
    BRAND_CREATION = "brand_creation"
    LOGO_GENERATION = "logo_generation" 
    MARKET_ANALYSIS = "market_analysis"
    WEBSITE_BUILDING = "website_building"
    SALES_OUTREACH = "sales_outreach"
    CONTENT_CREATION = "content_creation"
    LEAD_GENERATION = "lead_generation"
    DATA_ANALYSIS = "data_analysis"
    DESIGN_SERVICES = "design_services"
    TECHNICAL_IMPLEMENTATION = "technical_implementation"


@dataclass
class AgentCapability:
    """Represents what an agent can do."""
    agent_id: str
    capability_category: CapabilityCategory
    specific_skills: List[str]
    execution_requirements: Dict[str, Any]
    estimated_duration: Optional[int] = None  # seconds
    dependencies: List[str] = None  # other capabilities needed first
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class SemanticUnderstanding:
    """Complete semantic understanding of a user request."""
    # Business Context (required fields first)
    business_goal: str
    user_intent_summary: str
    primary_capabilities: List[CapabilityCategory]
    secondary_capabilities: List[CapabilityCategory]
    recommended_agents: List[str]
    execution_strategy: ExecutionStrategy
    execution_plan: Dict[str, Any]
    extracted_parameters: Dict[str, Any]
    business_context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    confidence_score: float
    reasoning: str
    
    # Optional fields with defaults
    business_domain: Optional[str] = None
    urgency_level: str = "medium"  # low, medium, high
    potential_challenges: List[str] = None
    
    def __post_init__(self):
        if self.potential_challenges is None:
            self.potential_challenges = []


class CapabilityAgentRegistry:
    """Registry that maps capabilities to agents without department intermediaries."""
    
    def __init__(self):
        self.capability_map: Dict[CapabilityCategory, List[AgentCapability]] = {}
        self.agent_specs: Dict[str, Dict[str, Any]] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the capability registry with known agents."""
        # Branding capabilities
        self.register_capability(AgentCapability(
            agent_id="branding_agent",
            capability_category=CapabilityCategory.BRAND_CREATION,
            specific_skills=["brand_strategy", "brand_messaging", "brand_identity"],
            execution_requirements={"api_access": "claude", "output_format": "structured"}
        ))
        
        self.register_capability(AgentCapability(
            agent_id="logo_generation_agent", 
            capability_category=CapabilityCategory.LOGO_GENERATION,
            specific_skills=["logo_design", "visual_identity", "brand_assets"],
            execution_requirements={"api_access": "openai", "image_generation": True},
            estimated_duration=120
        ))
        
        # Market Research capabilities  
        self.register_capability(AgentCapability(
            agent_id="market_research_agent",
            capability_category=CapabilityCategory.MARKET_ANALYSIS,
            specific_skills=["market_sizing", "competitor_analysis", "trend_analysis"],
            execution_requirements={"web_access": True, "data_sources": ["web", "apis"]}
        ))
        
        # Website capabilities
        self.register_capability(AgentCapability(
            agent_id="website_generator_agent",
            capability_category=CapabilityCategory.WEBSITE_BUILDING,
            specific_skills=["html_generation", "responsive_design", "seo_optimization"],
            execution_requirements={"template_access": True, "asset_management": True},
            dependencies=[]  # Can work independently - will use fallback branding if needed
        ))
        
        # Lead Mining capabilities (NEW Apollo-powered agent - PRIORITY)
        self.register_capability(AgentCapability(
            agent_id="lead_mining_agent",
            capability_category=CapabilityCategory.LEAD_GENERATION,
            specific_skills=["apollo_integration", "prospect_search", "icp_analysis", "lead_qualification"],
            execution_requirements={"apollo_api": True, "data_validation": True, "ai_analysis": True}
        ))
        
        # Sales capabilities (legacy lead scanner - fallback)
        self.register_capability(AgentCapability(
            agent_id="lead_scanner_agent",
            capability_category=CapabilityCategory.LEAD_GENERATION,
            specific_skills=["prospect_identification", "contact_discovery", "lead_qualification"],
            execution_requirements={"web_access": True, "data_extraction": True}
        ))
        
        # Content creation capabilities
        self.register_capability(AgentCapability(
            agent_id="content_creator_agent",
            capability_category=CapabilityCategory.CONTENT_CREATION,
            specific_skills=["copywriting", "blog_posts", "social_media_content", "marketing_materials"],
            execution_requirements={"api_access": "claude", "output_format": "text"}
        ))
        
        # Design services capabilities
        self.register_capability(AgentCapability(
            agent_id="design_services_agent",
            capability_category=CapabilityCategory.DESIGN_SERVICES,
            specific_skills=["visual_design", "ui_design", "graphic_design", "layout_design"],
            execution_requirements={"design_tools": True, "asset_management": True}
        ))
        
        # Technical implementation capabilities
        self.register_capability(AgentCapability(
            agent_id="technical_implementation_agent",
            capability_category=CapabilityCategory.TECHNICAL_IMPLEMENTATION,
            specific_skills=["system_integration", "api_development", "technical_setup"],
            execution_requirements={"development_tools": True, "api_access": "multiple"}
        ))
        
        # Data analysis capabilities
        self.register_capability(AgentCapability(
            agent_id="data_analysis_agent",
            capability_category=CapabilityCategory.DATA_ANALYSIS,
            specific_skills=["data_processing", "statistical_analysis", "reporting"],
            execution_requirements={"data_tools": True, "api_access": "claude"}
        ))
        
        # General agent for fallback
        self.register_capability(AgentCapability(
            agent_id="general_agent",
            capability_category=CapabilityCategory.CONTENT_CREATION,  # Default to content creation
            specific_skills=["general_assistance", "information_processing", "basic_analysis"],
            execution_requirements={"api_access": "claude"}
        ))
    
    def register_capability(self, capability: AgentCapability):
        """Register a new agent capability."""
        if capability.capability_category not in self.capability_map:
            self.capability_map[capability.capability_category] = []
        self.capability_map[capability.capability_category].append(capability)
        logger.info(f"Registered {capability.agent_id} for {capability.capability_category}")
    
    def get_agents_for_capability(self, capability: CapabilityCategory) -> List[AgentCapability]:
        """Get all agents that can handle a specific capability."""
        return self.capability_map.get(capability, [])
    
    def get_best_agent_for_capability(self, capability: CapabilityCategory, context: Dict[str, Any] = None) -> Optional[AgentCapability]:
        """Get the best agent for a capability given context."""
        agents = self.get_agents_for_capability(capability)
        if not agents:
            return None
        
        # For now, return first agent, but could add scoring logic
        return agents[0]
    
    def resolve_dependencies(self, capabilities: List[CapabilityCategory]) -> List[CapabilityCategory]:
        """Resolve capability dependencies to determine execution order."""
        resolved = []
        remaining = capabilities.copy()
        max_iterations = len(capabilities) * 2  # Prevent infinite loops
        iteration = 0
        
        while remaining and iteration < max_iterations:
            iteration += 1
            progress_made = False
            
            for capability in remaining.copy():
                agents = self.get_agents_for_capability(capability)
                if not agents:
                    remaining.remove(capability)
                    progress_made = True
                    continue
                
                # Check if dependencies are resolved
                agent = agents[0]  # Use first agent for dependency check
                if not hasattr(agent, 'dependencies') or not agent.dependencies:
                    # No dependencies, can execute immediately
                    resolved.append(capability)
                    remaining.remove(capability)
                    progress_made = True
                else:
                    deps_satisfied = all(dep in [c.value for c in resolved] for dep in agent.dependencies)
                    if deps_satisfied:
                        resolved.append(capability)
                        remaining.remove(capability)
                        progress_made = True
            
            # If no progress made, break to avoid infinite loop
            if not progress_made:
                # Add remaining capabilities without dependencies resolved
                resolved.extend(remaining)
                break
        
        return resolved


class SemanticRequestParser:
    """
    Semantic parser that replaces IntentParser with single AI call approach.
    
    Makes ONE comprehensive AI call to understand business context, map to capabilities,
    and create execution plan - eliminating multiple classification steps.
    """
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.ai_engine = ai_engine or AnthropicEngine(AIEngineConfig())
        self.registry = CapabilityAgentRegistry()
    
    async def parse_request(self, user_request: str, conversation_context: Optional[Dict[str, Any]] = None) -> SemanticUnderstanding:
        """
        Parse user request with single AI call for complete semantic understanding.
        
        Args:
            user_request: The user's natural language request
            conversation_context: Previous conversation context if available
        
        Returns:
            SemanticUnderstanding: Complete understanding and execution plan
        """
        try:
            # Build comprehensive prompt for single AI analysis
            analysis_prompt = self._build_semantic_analysis_prompt(user_request, conversation_context)
            
            # Single AI call for complete understanding
            response = await self.ai_engine.generate(analysis_prompt)
            
            # Extract text content if response is an AIResponse object
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Parse the structured response
            understanding = self._parse_ai_response(response_text, user_request)
            
            # Enhance with capability mapping
            understanding = await self._enhance_with_capability_mapping(understanding)
            
            return understanding
            
        except Exception as e:
            logger.error(f"Failed to parse request semantically: {e}")
            # Return intelligent fallback understanding
            return await self._create_intelligent_fallback(user_request, str(e))
    
    def _build_semantic_analysis_prompt(self, user_request: str, context: Optional[Dict[str, Any]]) -> str:
        """Build comprehensive prompt for semantic analysis."""
        
        available_capabilities = list(CapabilityCategory)
        capability_descriptions = {
            CapabilityCategory.BRAND_CREATION: "Creating brand strategy, messaging, and identity",
            CapabilityCategory.LOGO_GENERATION: "Designing logos and visual brand assets",
            CapabilityCategory.MARKET_ANALYSIS: "Market research, competitor analysis, trend identification", 
            CapabilityCategory.WEBSITE_BUILDING: "Building responsive websites with modern design",
            CapabilityCategory.SALES_OUTREACH: "Creating sales materials and outreach campaigns",
            CapabilityCategory.LEAD_GENERATION: "Finding and qualifying potential customers",
            CapabilityCategory.CONTENT_CREATION: "Writing marketing copy, blog posts, social content",
            CapabilityCategory.DATA_ANALYSIS: "Analyzing data and creating insights",
            CapabilityCategory.DESIGN_SERVICES: "Visual design and creative services",
            CapabilityCategory.TECHNICAL_IMPLEMENTATION: "Technical development and implementation"
        }
        
        context_str = ""
        if context:
            context_str = f"\nConversation Context: {json.dumps(context, indent=2)}"
        
        return f"""
You are a semantic business request analyzer. Analyze this user request and provide a comprehensive understanding in JSON format.

USER REQUEST: "{user_request}"{context_str}

Available Capabilities:
{json.dumps({cap.value: desc for cap, desc in capability_descriptions.items()}, indent=2)}

Available Agents:
{json.dumps(self._get_agent_descriptions(), indent=2)}

Analyze the request and respond with ONLY a JSON object containing:

{{
    "business_goal": "Clear statement of what the user wants to achieve",
    "user_intent_summary": "Concise summary of the user's intent", 
    "business_domain": "Industry/domain if identifiable",
    "urgency_level": "low|medium|high",
    
    "primary_capabilities": ["List of main capabilities needed"],
    "secondary_capabilities": ["List of supporting capabilities that might be helpful"],
    
    "recommended_agents": ["List of specific agent IDs that should handle this"],
    "execution_strategy": "single_agent|parallel_multi|sequential_multi|hybrid",
    "execution_plan": {{
        "description": "How to execute this request",
        "sequence": "If sequential/hybrid, describe the order",
        "parallel_groups": "If parallel, group agents that can run together"
    }},
    
    "extracted_parameters": {{
        "Any specific parameters extracted from the request"
    }},
    "business_context": {{
        "relevant_business_context": "extracted from request"
    }},
    "user_preferences": {{
        "Any preferences mentioned by user"
    }},
    
    "confidence_score": 0.95,
    "reasoning": "Detailed explanation of your analysis and recommendations",
    "potential_challenges": ["List any potential issues or challenges"]
}}

Focus on understanding the BUSINESS INTENT and mapping directly to agents that can deliver results.
Avoid unnecessary complexity - prefer simpler execution strategies when possible.
IMPORTANT: Only recommend ONE agent unless the user explicitly asks for multiple services.
For website requests, use ONLY website_generator_agent unless user specifically mentions branding/logos.

IMPORTANT: If the request doesn't clearly map to available capabilities, set confidence_score below 0.5 
and provide helpful suggestions for what the user might want instead. Include "off_key_request": true 
in the execution_plan and suggest the closest available capabilities.
"""

    def _get_agent_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available agents."""
        descriptions = {}
        for capabilities in self.registry.capability_map.values():
            for agent_cap in capabilities:
                descriptions[agent_cap.agent_id] = {
                    "capability": agent_cap.capability_category.value,
                    "skills": agent_cap.specific_skills
                }
        return descriptions

    def _parse_execution_strategy(self, strategy_value: str) -> ExecutionStrategy:
        """Parse execution strategy with fallback for invalid values."""
        if not strategy_value or strategy_value.lower() in ['none', 'null', '']:
            return ExecutionStrategy.SINGLE_AGENT
        
        # Try to match valid strategies
        strategy_mapping = {
            'single_agent': ExecutionStrategy.SINGLE_AGENT,
            'single': ExecutionStrategy.SINGLE_AGENT,
            'parallel_multi': ExecutionStrategy.PARALLEL_MULTI,
            'parallel': ExecutionStrategy.PARALLEL_MULTI,
            'sequential_multi': ExecutionStrategy.SEQUENTIAL_MULTI,
            'sequential': ExecutionStrategy.SEQUENTIAL_MULTI,
            'hybrid': ExecutionStrategy.HYBRID
        }
        
        strategy_lower = strategy_value.lower().strip()
        if strategy_lower in strategy_mapping:
            return strategy_mapping[strategy_lower]
        
        # Default fallback
        logger.warning(f"Unknown execution strategy '{strategy_value}', defaulting to single_agent")
        return ExecutionStrategy.SINGLE_AGENT

    def _parse_capabilities(self, capabilities_list: List[str]) -> List[CapabilityCategory]:
        """Parse capabilities list with fallback for invalid values."""
        parsed_capabilities = []
        
        if not capabilities_list:
            return parsed_capabilities
        
        for cap in capabilities_list:
            if not cap or cap in ['none', 'null', '']:
                continue
                
            try:
                # Try to parse as CapabilityCategory
                parsed_cap = CapabilityCategory(cap.lower().strip())
                parsed_capabilities.append(parsed_cap)
            except ValueError:
                # Try to map common variations
                capability_mapping = {
                    'branding': CapabilityCategory.BRAND_CREATION,
                    'brand': CapabilityCategory.BRAND_CREATION,
                    'logo': CapabilityCategory.LOGO_GENERATION,
                    'logos': CapabilityCategory.LOGO_GENERATION,
                    'market': CapabilityCategory.MARKET_ANALYSIS,
                    'research': CapabilityCategory.MARKET_ANALYSIS,
                    'website': CapabilityCategory.WEBSITE_BUILDING,
                    'web': CapabilityCategory.WEBSITE_BUILDING,
                    'sales': CapabilityCategory.SALES_OUTREACH,
                    'content': CapabilityCategory.CONTENT_CREATION,
                    'writing': CapabilityCategory.CONTENT_CREATION,
                    'design': CapabilityCategory.DESIGN_SERVICES,
                    'visual': CapabilityCategory.DESIGN_SERVICES,
                    'leads': CapabilityCategory.LEAD_GENERATION,
                    'prospects': CapabilityCategory.LEAD_GENERATION,
                    'prospecting': CapabilityCategory.LEAD_GENERATION,
                    'lead generation': CapabilityCategory.LEAD_GENERATION,
                    'lead mining': CapabilityCategory.LEAD_GENERATION,
                    'find leads': CapabilityCategory.LEAD_GENERATION,
                    'data': CapabilityCategory.DATA_ANALYSIS,
                    'analysis': CapabilityCategory.DATA_ANALYSIS
                }
                
                cap_lower = cap.lower().strip()
                if cap_lower in capability_mapping:
                    parsed_capabilities.append(capability_mapping[cap_lower])
                else:
                    logger.warning(f"Unknown capability '{cap}', skipping")
        
        # If no valid capabilities found, default to content creation
        if not parsed_capabilities:
            parsed_capabilities.append(CapabilityCategory.CONTENT_CREATION)
        
        return parsed_capabilities

    def _parse_ai_response(self, response: str, original_request: str) -> SemanticUnderstanding:
        """Parse AI response into SemanticUnderstanding object."""
        try:
            # Extract JSON from response if wrapped in markdown
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3].strip()
            elif response.startswith('```'):
                response = response[3:-3].strip()
            
            data = json.loads(response)
            
            return SemanticUnderstanding(
                business_goal=data.get("business_goal", "Unclear goal"),
                user_intent_summary=data.get("user_intent_summary", original_request[:100]),
                business_domain=data.get("business_domain"),
                urgency_level=data.get("urgency_level", "medium"),
                
                primary_capabilities=self._parse_capabilities(data.get("primary_capabilities", [])),
                secondary_capabilities=self._parse_capabilities(data.get("secondary_capabilities", [])),
                
                recommended_agents=data.get("recommended_agents", []),
                execution_strategy=self._parse_execution_strategy(data.get("execution_strategy", "single_agent")),
                execution_plan=data.get("execution_plan", {}),
                
                extracted_parameters=data.get("extracted_parameters", {}),
                business_context=data.get("business_context", {}),  
                user_preferences=data.get("user_preferences", {}),
                
                confidence_score=float(data.get("confidence_score", 0.5)),
                reasoning=data.get("reasoning", ""),
                potential_challenges=data.get("potential_challenges", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response: {response}")
            
            # Return minimal fallback
            return SemanticUnderstanding(
                business_goal="Failed to parse goal",
                user_intent_summary=original_request[:100],
                primary_capabilities=[CapabilityCategory.CONTENT_CREATION],
                secondary_capabilities=[],
                recommended_agents=["general_agent"],
                execution_strategy=ExecutionStrategy.SINGLE_AGENT,
                execution_plan={"error": "Failed to parse AI response"},
                extracted_parameters={},
                business_context={},
                user_preferences={},
                confidence_score=0.1,
                reasoning=f"Parse error: {str(e)}"
            )

    async def _enhance_with_capability_mapping(self, understanding: SemanticUnderstanding) -> SemanticUnderstanding:
        """Enhance understanding with precise capability-to-agent mapping."""
        # Resolve dependencies between capabilities
        all_capabilities = understanding.primary_capabilities + understanding.secondary_capabilities
        resolved_capabilities = self.registry.resolve_dependencies(all_capabilities)
        
        # Map capabilities to best available agents
        enhanced_agents = []
        execution_plan_updates = {}
        
        for capability in resolved_capabilities:
            best_agent = self.registry.get_best_agent_for_capability(
                capability, understanding.business_context
            )
            if best_agent and best_agent.agent_id not in enhanced_agents:
                enhanced_agents.append(best_agent.agent_id)
                execution_plan_updates[best_agent.agent_id] = {
                    "capability": capability.value,
                    "estimated_duration": best_agent.estimated_duration,
                    "requirements": best_agent.execution_requirements
                }
        
        # Update the understanding with enhanced mappings if we have better ones
        if enhanced_agents:
            understanding.recommended_agents = enhanced_agents
        understanding.execution_plan.update({
            "agent_mappings": execution_plan_updates,
            "resolved_capability_order": [cap.value for cap in resolved_capabilities]
        })
        
        return understanding

    async def validate_execution_plan(self, understanding: SemanticUnderstanding) -> Tuple[bool, List[str]]:
        """Validate that the execution plan is feasible."""
        issues = []
        
        # Check that recommended agents exist
        for agent_id in understanding.recommended_agents:
            if not self._agent_exists(agent_id):
                issues.append(f"Agent {agent_id} is not available")
        
        # Check capability coverage
        for capability in understanding.primary_capabilities:
            if not self.registry.get_agents_for_capability(capability):
                issues.append(f"No agents available for {capability.value}")
        
        # Check execution strategy feasibility
        if understanding.execution_strategy == ExecutionStrategy.PARALLEL_MULTI:
            if len(understanding.recommended_agents) < 2:
                issues.append("Parallel execution requires multiple agents")
        
        return len(issues) == 0, issues
    
    def _agent_exists(self, agent_id: str) -> bool:
        """Check if an agent is registered in the capability registry."""
        for capabilities in self.registry.capability_map.values():
            for agent_cap in capabilities:
                if agent_cap.agent_id == agent_id:
                    return True
        return False
    
    async def _create_intelligent_fallback(self, user_request: str, error_msg: str) -> SemanticUnderstanding:
        """Create intelligent fallback when parsing fails or request is off-key."""
        try:
            # Try to use AI to provide helpful suggestions even for off-key requests
            fallback_prompt = f"""
The user made this request: "{user_request}"

Our system couldn't process this request normally. Provide a helpful response that:
1. Acknowledges what they're asking for
2. Explains we don't have that specific capability 
3. Suggests the closest available capabilities from this list:

Available Capabilities:
- logo_generation: Create professional logos and visual branding
- brand_creation: Develop brand strategy, messaging, and identity
- market_analysis: Research markets, competitors, and trends  
- website_building: Create websites and landing pages
- sales_outreach: Generate sales materials and campaigns
- lead_generation: Find and qualify potential customers
- content_creation: Write marketing copy and content

Respond with JSON:
{{
    "business_goal": "What you think they really want to achieve",
    "user_intent_summary": "Helpful summary of their request",
    "primary_capabilities": [],
    "secondary_capabilities": [],  
    "recommended_agents": [],
    "execution_strategy": "single_agent",
    "execution_plan": {{
        "off_key_request": true,
        "suggestion": "Helpful suggestion for what they might want instead",
        "available_alternatives": ["list of relevant capabilities"]
    }},
    "extracted_parameters": {{}},
    "business_context": {{}},
    "user_preferences": {{}},
    "confidence_score": 0.3,
    "reasoning": "This request doesn't map to available capabilities, but here's what might help..."
}}
"""
            
            response = await self.ai_engine.generate(fallback_prompt)
            
            # Extract text content if response is an AIResponse object
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            understanding = self._parse_ai_response(response_text, user_request)
            
            # Ensure it's marked as off-key with low confidence
            understanding.confidence_score = min(understanding.confidence_score, 0.4)
            if "off_key_request" not in understanding.execution_plan:
                understanding.execution_plan["off_key_request"] = True
            
            return understanding
            
        except Exception as e:
            logger.error(f"Intelligent fallback also failed: {e}")
            # Final fallback
            return SemanticUnderstanding(
                business_goal="I don't fully understand this request",
                user_intent_summary=user_request[:100],
                primary_capabilities=[],
                secondary_capabilities=[],
                recommended_agents=[],
                execution_strategy=ExecutionStrategy.SINGLE_AGENT,
                execution_plan={
                    "off_key_request": True,
                    "suggestion": "Could you rephrase your request? I specialize in logos, branding, market research, websites, and sales materials.",
                    "available_alternatives": ["logo_generation", "brand_creation", "market_analysis", "website_building", "sales_outreach"]
                },
                extracted_parameters={},
                business_context={},
                user_preferences={},
                confidence_score=0.1,
                reasoning=f"Request unclear. Available services: logos, branding, market research, websites, sales materials. Error: {error_msg}"
            )


# Example usage and testing
if __name__ == "__main__":
    async def test_semantic_parser():
        parser = SemanticRequestParser()
        
        test_requests = [
            "Create a logo for my coffee shop startup",
            "I need a complete brand identity and website for my tech consulting business", 
            "Generate market research for electric vehicle charging stations",
            "Build me a sales funnel with lead generation and outreach campaigns"
        ]
        
        for request in test_requests:
            print(f"\n=== Testing: {request} ===")
            understanding = await parser.parse_request(request)
            print(f"Goal: {understanding.business_goal}")
            print(f"Strategy: {understanding.execution_strategy}")
            print(f"Agents: {understanding.recommended_agents}")
            print(f"Confidence: {understanding.confidence_score}")
    
    # Run test if called directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_semantic_parser())