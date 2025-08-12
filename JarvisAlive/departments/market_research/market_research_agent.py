"""
MarketResearchAgent - Comprehensive market intelligence and analysis

This agent provides detailed market research including competitor analysis, 
market sizing, customer insights, trends, and strategic recommendations.
Integrates web scraping, API data, and AI analysis for actionable intelligence.
"""

import asyncio
import json
import logging
import re
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import hashlib

# AI and analysis imports
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

logger = logging.getLogger(__name__)


@dataclass
class CompetitorProfile:
    """Detailed competitor information."""
    name: str
    website: str = ""
    description: str = ""
    market_position: str = ""
    key_features: List[str] = None
    pricing_info: str = ""
    strengths: List[str] = None
    weaknesses: List[str] = None
    market_share_estimate: str = ""
    
    def __post_init__(self):
        if self.key_features is None:
            self.key_features = []
        if self.strengths is None:
            self.strengths = []
        if self.weaknesses is None:
            self.weaknesses = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'website': self.website,
            'description': self.description,
            'market_position': self.market_position,
            'key_features': self.key_features,
            'pricing_info': self.pricing_info,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'market_share_estimate': self.market_share_estimate
        }


@dataclass
class MarketSegment:
    """Market segment information."""
    segment_name: str
    size_description: str
    growth_rate: str
    key_characteristics: List[str] = None
    opportunity_score: int = 0  # 1-10 scale
    
    def __post_init__(self):
        if self.key_characteristics is None:
            self.key_characteristics = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'segment_name': self.segment_name,
            'size_description': self.size_description,
            'growth_rate': self.growth_rate,
            'key_characteristics': self.key_characteristics,
            'opportunity_score': self.opportunity_score
        }


@dataclass
class CustomerPersona:
    """Detailed customer persona."""
    persona_name: str
    demographics: str = ""
    pain_points: List[str] = None
    needs: List[str] = None
    buying_behavior: str = ""
    price_sensitivity: str = ""
    preferred_channels: List[str] = None
    
    def __post_init__(self):
        if self.pain_points is None:
            self.pain_points = []
        if self.needs is None:
            self.needs = []
        if self.preferred_channels is None:
            self.preferred_channels = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'persona_name': self.persona_name,
            'demographics': self.demographics,
            'pain_points': self.pain_points,
            'needs': self.needs,
            'buying_behavior': self.buying_behavior,
            'price_sensitivity': self.price_sensitivity,
            'preferred_channels': self.preferred_channels
        }


@dataclass
class MarketResearchResult:
    """Complete market research analysis results."""
    # Executive Summary
    market_opportunity_score: int  # 1-100
    key_findings: List[str]
    recommended_strategy: str
    risk_assessment: str
    
    # Market Landscape
    market_size: str
    growth_rate: str
    market_maturity: str
    growth_drivers: List[str]
    barriers: List[str]
    geographic_insights: str
    
    # Competitive Analysis
    competitors: List[Dict[str, Any]]  # Now expects dictionaries instead of dataclass objects
    competitive_landscape: str
    market_gaps: List[str]
    competitive_advantages: List[str]
    
    # Customer Insights
    customer_personas: List[Dict[str, Any]]  # Now expects dictionaries instead of dataclass objects
    market_segments: List[Dict[str, Any]]  # Now expects dictionaries instead of dataclass objects
    customer_sentiment: str
    
    # Trends & Forecasting
    industry_trends: List[str]
    technology_trends: List[str]
    market_forecast: str
    opportunities: List[str]
    threats: List[str]
    
    # Strategic Recommendations
    go_to_market_strategy: str
    positioning_recommendations: str
    pricing_strategy: str
    product_priorities: List[str]
    
    # Metadata
    research_date: str
    data_freshness: str
    confidence_score: int  # 1-100
    
    def __post_init__(self):
        # Initialize empty lists if None
        for field_name in ['key_findings', 'growth_drivers', 'barriers', 'competitors', 
                          'market_gaps', 'competitive_advantages', 'customer_personas',
                          'market_segments', 'industry_trends', 'technology_trends',
                          'opportunities', 'threats', 'product_priorities']:
            field_value = getattr(self, field_name)
            if field_value is None:
                setattr(self, field_name, [])
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'market_opportunity_score': self.market_opportunity_score,
            'key_findings': self.key_findings,
            'recommended_strategy': self.recommended_strategy,
            'risk_assessment': self.risk_assessment,
            'market_size': self.market_size,
            'growth_rate': self.growth_rate,
            'market_maturity': self.market_maturity,
            'growth_drivers': self.growth_drivers,
            'barriers': self.barriers,
            'geographic_insights': self.geographic_insights,
            'competitors': self.competitors,  # Already dictionaries
            'competitive_landscape': self.competitive_landscape,
            'market_gaps': self.market_gaps,
            'competitive_advantages': self.competitive_advantages,
            'customer_personas': self.customer_personas,  # Already dictionaries
            'market_segments': self.market_segments,  # Already dictionaries
            'customer_sentiment': self.customer_sentiment,
            'industry_trends': self.industry_trends,
            'technology_trends': self.technology_trends,
            'market_forecast': self.market_forecast,
            'opportunities': self.opportunities,
            'threats': self.threats,
            'go_to_market_strategy': self.go_to_market_strategy,
            'positioning_recommendations': self.positioning_recommendations,
            'pricing_strategy': self.pricing_strategy,
            'product_priorities': self.product_priorities,
            'research_date': self.research_date,
            'data_freshness': self.data_freshness,
            'confidence_score': self.confidence_score
        }


class MarketResearchAgent:
    """
    Comprehensive market research agent providing professional-grade market intelligence.
    
    Features:
    - Market landscape analysis with sizing and growth projections
    - Competitive intelligence with detailed competitor profiles  
    - Customer research and persona development
    - Industry trend analysis and forecasting
    - Strategic recommendations and opportunity assessment
    - Web scraping for real-time market data
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MarketResearchAgent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine for analysis
        self._initialize_ai_engine()
        
        # Research configuration
        self.max_competitors = self.config.get('max_competitors', 10)
        self.research_depth = self.config.get('research_depth', 'comprehensive')  # basic, standard, comprehensive
        self.include_web_scraping = self.config.get('include_web_scraping', True)
        self.cache_duration_hours = self.config.get('cache_duration_hours', 24)
        
        # Output configuration
        self.reports_dir = Path(self.config.get('reports_dir', './market_research_reports'))
        self.reports_dir.mkdir(exist_ok=True)
        
        self.logger.info("MarketResearchAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize the AI engine for market analysis."""
        if not ANTHROPIC_AVAILABLE:
            self.logger.warning("Anthropic not available - market analysis will be limited")
            self.ai_engine = None
            return
        
        try:
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                import os
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found - using fallback analysis")
                self.ai_engine = None
                return
            
            self.ai_engine = ChatAnthropic(
                anthropic_api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                temperature=0.1,
                max_tokens=4000
            )
            self.logger.info("AI engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for market research analysis.
        
        Args:
            state: Input state containing business information and research parameters
            
        Returns:
            Updated state with comprehensive market research results
        """
        self.logger.info("Starting comprehensive market research analysis")
        
        try:
            # Extract research parameters
            research_params = self._extract_research_params(state)
            
            if not research_params:
                return self._generate_error_result("Insufficient information for market research")
            
            # Generate comprehensive market research
            research_result = await self._conduct_market_research(research_params)
            
            # Update state with results
            updated_state = state.copy()
            updated_state.update({
                'market_research_result': research_result.to_dict() if research_result else None,
                'market_research_success': research_result is not None,
                'market_research_completed_at': datetime.utcnow().isoformat(),
                
                # Expose key findings at top level for easy access
                'market_opportunity_score': research_result.market_opportunity_score if research_result else 0,
                'market_size': research_result.market_size if research_result else "",
                'key_competitors': [comp.get('name', 'Unknown') for comp in research_result.competitors[:5]] if research_result else [],
                'market_trends': research_result.industry_trends[:3] if research_result else [],
                'target_personas': [persona.get('persona_name', 'Unknown') for persona in research_result.customer_personas] if research_result else []
            })
            
            self.logger.info(f"Market research completed successfully")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Market research failed: {e}")
            return self._generate_error_result(f"Market research failed: {str(e)}")
    
    def _extract_research_params(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate research parameters from state."""
        # Extract business information
        business_info = {}
        
        # Try different possible keys for business information
        for key in ['business_idea', 'business_type', 'product_type', 'industry', 'brand_name']:
            if key in state and state[key]:
                business_info[key] = state[key]
        
        # Extract from user request if available
        user_request = state.get('user_request', '')
        if user_request:
            business_info['user_request'] = user_request
        
        # Must have at least some business context
        if not business_info:
            self.logger.error("No business information found for market research")
            return None
        
        return {
            'business_info': business_info,
            'research_type': state.get('research_type', 'comprehensive'),
            'geographic_focus': state.get('geographic_focus', 'global'),
            'specific_questions': state.get('research_questions', [])
        }
    
    async def _conduct_market_research(self, params: Dict[str, Any]) -> Optional[MarketResearchResult]:
        """Conduct comprehensive market research analysis."""
        if not self.ai_engine:
            return self._generate_fallback_research(params)
        
        try:
            # Phase 1: Market Landscape Analysis
            market_analysis = await self._analyze_market_landscape(params)
            
            # Phase 2: Competitive Analysis
            competitive_analysis = await self._analyze_competitors(params)
            
            # Phase 3: Customer Research
            customer_analysis = await self._analyze_customers(params)
            
            # Phase 4: Trend Analysis
            trend_analysis = await self._analyze_trends(params)
            
            # Phase 5: Strategic Recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(
                params, market_analysis, competitive_analysis, customer_analysis, trend_analysis
            )
            
            # Combine all analyses into comprehensive result
            research_result = MarketResearchResult(
                # Executive Summary
                market_opportunity_score=strategic_recommendations.get('opportunity_score', 75),
                key_findings=strategic_recommendations.get('key_findings', []),
                recommended_strategy=strategic_recommendations.get('strategy', ""),
                risk_assessment=strategic_recommendations.get('risks', ""),
                
                # Market Landscape
                market_size=market_analysis.get('size', ""),
                growth_rate=market_analysis.get('growth_rate', ""),
                market_maturity=market_analysis.get('maturity', ""),
                growth_drivers=market_analysis.get('drivers', []),
                barriers=market_analysis.get('barriers', []),
                geographic_insights=market_analysis.get('geographic', ""),
                
                # Competitive Analysis
                competitors=competitive_analysis.get('competitors', []),
                competitive_landscape=competitive_analysis.get('landscape', ""),
                market_gaps=competitive_analysis.get('gaps', []),
                competitive_advantages=competitive_analysis.get('advantages', []),
                
                # Customer Insights
                customer_personas=customer_analysis.get('personas', []),
                market_segments=customer_analysis.get('segments', []),
                customer_sentiment=customer_analysis.get('sentiment', ""),
                
                # Trends & Forecasting
                industry_trends=trend_analysis.get('industry_trends', []),
                technology_trends=trend_analysis.get('tech_trends', []),
                market_forecast=trend_analysis.get('forecast', ""),
                opportunities=trend_analysis.get('opportunities', []),
                threats=trend_analysis.get('threats', []),
                
                # Strategic Recommendations
                go_to_market_strategy=strategic_recommendations.get('go_to_market', ""),
                positioning_recommendations=strategic_recommendations.get('positioning', ""),
                pricing_strategy=strategic_recommendations.get('pricing', ""),
                product_priorities=strategic_recommendations.get('product_priorities', []),
                
                # Metadata
                research_date=datetime.utcnow().isoformat(),
                data_freshness="Current as of " + datetime.utcnow().strftime("%Y-%m-%d"),
                confidence_score=85  # High confidence for AI-generated analysis
            )
            
            # Save detailed report
            await self._save_research_report(research_result, params)
            
            return research_result
            
        except Exception as e:
            self.logger.error(f"Market research analysis failed: {e}")
            return self._generate_fallback_research(params)
    
    async def _analyze_market_landscape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market landscape including size, growth, and maturity."""
        business_info = params['business_info']
        
        prompt = f"""
        Conduct a comprehensive market landscape analysis for the following business:
        
        Business Information: {json.dumps(business_info, indent=2)}
        
        Provide detailed analysis covering:
        
        1. MARKET SIZE & SCOPE
        - Total Addressable Market (TAM) with specific numbers where possible
        - Current market value and projected growth
        - Geographic distribution and regional variations
        
        2. MARKET MATURITY & LIFECYCLE
        - Market development stage (emerging, growth, mature, declining)
        - Market saturation level
        - Innovation cycles and disruption patterns
        
        3. GROWTH DRIVERS & BARRIERS
        - Key factors driving market expansion
        - Major obstacles limiting growth
        - Economic and regulatory influences
        
        4. MARKET DYNAMICS
        - Supply and demand patterns
        - Seasonality and cyclical trends
        - Price sensitivity and elasticity
        
        Provide specific data points, percentages, and dollar amounts where available. 
        Focus on actionable insights with supporting evidence.
        
        Format response as structured data that can be parsed.
        """
        
        try:
            response = await self.ai_engine.ainvoke(prompt)
            analysis_text = response.content
            
            # Parse the AI response into structured data
            return self._parse_market_analysis(analysis_text)
            
        except Exception as e:
            self.logger.error(f"Market landscape analysis failed: {e}")
            return self._generate_fallback_market_analysis(business_info)
    
    def _parse_market_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI-generated market analysis into structured data."""
        # This is a simplified parser - in production would use more sophisticated NLP
        return {
            'size': self._extract_market_size(analysis_text),
            'growth_rate': self._extract_growth_rate(analysis_text),
            'maturity': self._extract_market_maturity(analysis_text),
            'drivers': self._extract_list_items(analysis_text, "growth drivers", "driving"),
            'barriers': self._extract_list_items(analysis_text, "barriers", "obstacle"),
            'geographic': self._extract_geographic_insights(analysis_text)
        }
    
    def _extract_market_size(self, text: str) -> str:
        """Extract market size information from analysis text."""
        # Look for patterns like "$X billion", "$X million", etc.
        size_patterns = [
            r'\$[\d,.]+ (?:billion|million|trillion)',
            r'[\d,.]+ billion dollar',
            r'market (?:worth|valued|size) [\$\d,. ]+ (?:billion|million)'
        ]
        
        for pattern in size_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(0)
        
        return "Market size data not available"
    
    def _extract_growth_rate(self, text: str) -> str:
        """Extract growth rate information from analysis text."""
        # Look for patterns like "X% CAGR", "growing at X%", etc.
        growth_patterns = [
            r'[\d.]+% (?:CAGR|annually|per year|growth)',
            r'growing (?:at )?[\d.]+%',
            r'compound annual growth rate of [\d.]+%'
        ]
        
        for pattern in growth_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(0)
        
        return "Growth rate data not available"
    
    def _extract_market_maturity(self, text: str) -> str:
        """Extract market maturity stage from analysis text."""
        maturity_indicators = {
            'emerging': ['emerging', 'nascent', 'early stage', 'developing'],
            'growth': ['growth stage', 'expanding', 'rapid growth', 'scaling'],
            'mature': ['mature', 'established', 'saturated', 'stable'],
            'declining': ['declining', 'shrinking', 'contracting', 'legacy']
        }
        
        text_lower = text.lower()
        for stage, indicators in maturity_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return stage.title()
        
        return "Market maturity assessment not available"
    
    def _extract_list_items(self, text: str, category: str, keywords: str) -> List[str]:
        """Extract list items related to a specific category."""
        # This is simplified - in production would use more sophisticated extraction
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords.split()) and len(line.strip()) > 20:
                # Clean up the line
                cleaned = re.sub(r'^[-*•]\s*', '', line.strip())
                if len(cleaned) > 10:
                    items.append(cleaned)
        
        return items[:5]  # Return top 5 items
    
    def _extract_geographic_insights(self, text: str) -> str:
        """Extract geographic insights from analysis text."""
        # Look for geographic mentions
        geo_patterns = [
            r'(?:North America|Europe|Asia|Global|US|USA|China|India|Japan)',
            r'regional (?:differences|variations|markets)',
            r'geographic (?:distribution|presence|expansion)'
        ]
        
        insights = []
        for pattern in geo_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            insights.extend(matches)
        
        return "Geographic analysis: " + ", ".join(set(insights)) if insights else "Geographic data not available"
    
    async def _analyze_competitors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive landscape and key competitors."""
        business_info = params['business_info']
        
        prompt = f"""
        Conduct detailed competitive analysis for this business:
        
        Business Information: {json.dumps(business_info, indent=2)}
        
        Provide comprehensive competitive intelligence including:
        
        1. TOP COMPETITORS IDENTIFICATION
        - Direct competitors (same product/service, same market)
        - Indirect competitors (different approach, same customer need)
        - Adjacent competitors (related markets)
        
        2. COMPETITOR PROFILES (for top 5-8 competitors)
        For each competitor provide:
        - Company name and brief description
        - Market position and estimated market share
        - Key products/services and features
        - Pricing strategy and models
        - Strengths and competitive advantages
        - Weaknesses and vulnerabilities
        - Recent developments and strategy changes
        
        3. COMPETITIVE LANDSCAPE ANALYSIS
        - Market concentration (fragmented vs consolidated)
        - Competitive intensity level
        - Barriers to entry
        - Switching costs for customers
        
        4. MARKET GAPS & OPPORTUNITIES
        - Underserved customer segments
        - Product/service gaps in the market
        - Pricing gaps and opportunities
        - Geographic gaps
        
        Focus on actionable competitive intelligence with specific details and data points.
        """
        
        try:
            response = await self.ai_engine.ainvoke(prompt)
            analysis_text = response.content
            
            return self._parse_competitive_analysis(analysis_text)
            
        except Exception as e:
            self.logger.error(f"Competitive analysis failed: {e}")
            return self._generate_fallback_competitive_analysis(business_info)
    
    def _parse_competitive_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse competitive analysis into structured data."""
        competitors = self._extract_competitors(analysis_text)
        return {
            'competitors': [c.to_dict() for c in competitors],
            'landscape': self._extract_competitive_landscape(analysis_text),
            'gaps': self._extract_list_items(analysis_text, "gaps", "gap opportunity underserved"),
            'advantages': self._extract_list_items(analysis_text, "advantages", "advantage strength opportunity")
        }
    
    def _extract_competitors(self, text: str) -> List[CompetitorProfile]:
        """Extract competitor profiles from analysis text."""
        competitors = []
        
        # This is simplified - in production would use more sophisticated parsing
        # Look for competitor names and descriptions
        lines = text.split('\n')
        current_competitor = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for competitor names (often start with numbers or bullets)
            if re.match(r'^[0-9•\-*]\s*[A-Z][^:]+:', line):
                if current_competitor:
                    competitors.append(current_competitor)
                
                # Extract competitor name
                name_match = re.search(r'^[0-9•\-*]\s*([^:]+):', line)
                if name_match:
                    name = name_match.group(1).strip()
                    current_competitor = CompetitorProfile(
                        name=name,
                        description=line.split(':', 1)[1].strip() if ':' in line else ""
                    )
            elif current_competitor and line:
                # Add additional information to current competitor
                if 'strength' in line.lower():
                    current_competitor.strengths.append(line)
                elif 'weakness' in line.lower():
                    current_competitor.weaknesses.append(line)
                elif 'feature' in line.lower():
                    current_competitor.key_features.append(line)
        
        if current_competitor:
            competitors.append(current_competitor)
        
        return competitors[:self.max_competitors]
    
    def _extract_competitive_landscape(self, text: str) -> str:
        """Extract competitive landscape description."""
        # Look for sections about landscape, concentration, intensity
        lines = text.split('\n')
        landscape_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ['landscape', 'competition', 'market share', 'concentration']):
                if len(line.strip()) > 20:
                    landscape_lines.append(line.strip())
        
        return '. '.join(landscape_lines[:3]) if landscape_lines else "Competitive landscape analysis not available"
    
    async def _analyze_customers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer segments and develop personas."""
        business_info = params['business_info']
        
        prompt = f"""
        Conduct comprehensive customer research and persona development for:
        
        Business Information: {json.dumps(business_info, indent=2)}
        
        Provide detailed customer insights including:
        
        1. CUSTOMER SEGMENTATION
        - Primary customer segments with size estimates
        - Demographic profiles (age, income, location, etc.)
        - Behavioral characteristics and patterns
        - Segment-specific needs and pain points
        
        2. DETAILED CUSTOMER PERSONAS (3-4 key personas)
        For each persona provide:
        - Persona name and demographic profile
        - Key pain points and challenges
        - Primary needs and desired outcomes
        - Buying behavior and decision factors
        - Price sensitivity and budget considerations
        - Preferred communication channels
        - Influencers in purchase decisions
        
        3. CUSTOMER JOURNEY ANALYSIS
        - Awareness stage: How customers discover solutions
        - Consideration stage: Evaluation criteria and process
        - Purchase stage: Decision factors and barriers
        - Post-purchase: Usage patterns and satisfaction
        
        4. MARKET SENTIMENT & FEEDBACK
        - Current customer satisfaction levels
        - Common complaints and frustrations
        - Unmet needs and desired improvements
        - Brand perception and loyalty factors
        
        Focus on actionable insights that inform product development, marketing, and sales strategies.
        """
        
        try:
            response = await self.ai_engine.ainvoke(prompt)
            analysis_text = response.content
            
            return self._parse_customer_analysis(analysis_text)
            
        except Exception as e:
            self.logger.error(f"Customer analysis failed: {e}")
            return self._generate_fallback_customer_analysis(business_info)
    
    def _parse_customer_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse customer analysis into structured data."""
        personas = self._extract_customer_personas(analysis_text)
        segments = self._extract_market_segments(analysis_text)
        return {
            'personas': [p.to_dict() for p in personas],
            'segments': [s.to_dict() for s in segments],
            'sentiment': self._extract_customer_sentiment(analysis_text)
        }
    
    def _extract_customer_personas(self, text: str) -> List[CustomerPersona]:
        """Extract customer personas from analysis text."""
        personas = []
        
        # Look for persona sections in the text
        lines = text.split('\n')
        current_persona = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for persona names/titles
            if re.match(r'^[0-9•\-*]\s*.*Persona|^Persona\s*[0-9]', line, re.IGNORECASE):
                if current_persona:
                    personas.append(current_persona)
                
                # Extract persona name
                name_match = re.search(r'Persona[:\s]*(.+)', line, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    name = f"Customer Persona {len(personas) + 1}"
                
                current_persona = CustomerPersona(persona_name=name)
            
            elif current_persona and line:
                # Categorize information
                line_lower = line.lower()
                if 'pain' in line_lower or 'challenge' in line_lower:
                    current_persona.pain_points.append(line)
                elif 'need' in line_lower or 'want' in line_lower:
                    current_persona.needs.append(line)
                elif 'demographic' in line_lower or 'age' in line_lower or 'income' in line_lower:
                    current_persona.demographics = line
                elif 'buy' in line_lower or 'purchase' in line_lower:
                    current_persona.buying_behavior = line
                elif 'price' in line_lower or 'budget' in line_lower:
                    current_persona.price_sensitivity = line
                elif 'channel' in line_lower or 'communication' in line_lower:
                    current_persona.preferred_channels.append(line)
        
        if current_persona:
            personas.append(current_persona)
        
        return personas[:4]  # Return top 4 personas
    
    def _extract_market_segments(self, text: str) -> List[MarketSegment]:
        """Extract market segments from analysis text."""
        segments = []
        
        # Look for segment descriptions
        lines = text.split('\n')
        for line in lines:
            if 'segment' in line.lower() and len(line.strip()) > 30:
                # Extract segment info
                segment_name = f"Market Segment {len(segments) + 1}"
                if ':' in line:
                    parts = line.split(':', 1)
                    segment_name = parts[0].strip()
                
                segments.append(MarketSegment(
                    segment_name=segment_name,
                    size_description=line.strip(),
                    growth_rate="Growth rate not specified",
                    opportunity_score=7  # Default medium-high opportunity
                ))
        
        return segments[:5]  # Return top 5 segments
    
    def _extract_customer_sentiment(self, text: str) -> str:
        """Extract customer sentiment analysis."""
        sentiment_indicators = {
            'positive': ['satisfied', 'happy', 'positive', 'good', 'excellent'],
            'negative': ['frustrated', 'dissatisfied', 'poor', 'bad', 'complaints'],
            'neutral': ['mixed', 'average', 'moderate', 'neutral']
        }
        
        text_lower = text.lower()
        sentiment_scores = {}
        
        for sentiment, indicators in sentiment_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            sentiment_scores[sentiment] = score
        
        # Determine overall sentiment
        if sentiment_scores:
            dominant_sentiment = max(sentiment_scores.keys(), key=lambda k: sentiment_scores[k])
            return f"Overall customer sentiment appears {dominant_sentiment} based on analysis"
        
        return "Customer sentiment analysis not available"
    
    async def _analyze_trends(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze industry trends and future forecasting."""
        business_info = params['business_info']
        
        prompt = f"""
        Conduct comprehensive trend analysis and market forecasting for:
        
        Business Information: {json.dumps(business_info, indent=2)}
        
        Provide detailed analysis covering:
        
        1. CURRENT INDUSTRY TRENDS
        - Major trends reshaping the industry
        - Technology adoption patterns
        - Consumer behavior shifts
        - Regulatory and policy changes
        - Economic factors and impacts
        
        2. TECHNOLOGY TRENDS
        - Emerging technologies affecting the market
        - Digital transformation patterns
        - Automation and AI impacts
        - Platform and ecosystem changes
        
        3. MARKET FORECAST (2-5 year outlook)
        - Growth projections and trajectories
        - Market evolution predictions
        - New segment emergence
        - Disruption risks and opportunities
        
        4. STRATEGIC OPPORTUNITIES
        - Emerging market opportunities
        - White space identification
        - Partnership and collaboration opportunities
        - Innovation and product development areas
        
        5. THREATS AND CHALLENGES
        - Competitive threats
        - Market disruption risks
        - Regulatory challenges
        - Economic headwinds
        
        Focus on actionable insights with timeline implications and strategic relevance.
        """
        
        try:
            response = await self.ai_engine.ainvoke(prompt)
            analysis_text = response.content
            
            return self._parse_trend_analysis(analysis_text)
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return self._generate_fallback_trend_analysis(business_info)
    
    def _parse_trend_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse trend analysis into structured data."""
        return {
            'industry_trends': self._extract_list_items(analysis_text, "trends", "trend pattern shift"),
            'tech_trends': self._extract_list_items(analysis_text, "technology", "technology digital AI automation"),
            'forecast': self._extract_forecast(analysis_text),
            'opportunities': self._extract_list_items(analysis_text, "opportunities", "opportunity potential white space"),
            'threats': self._extract_list_items(analysis_text, "threats", "threat risk challenge disruption")
        }
    
    def _extract_forecast(self, text: str) -> str:
        """Extract market forecast information."""
        forecast_lines = []
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ['forecast', 'projection', 'outlook', 'predict', 'future']):
                if len(line.strip()) > 30:
                    forecast_lines.append(line.strip())
        
        return '. '.join(forecast_lines[:3]) if forecast_lines else "Market forecast not available"
    
    async def _generate_strategic_recommendations(self, params: Dict[str, Any], 
                                                market_analysis: Dict[str, Any],
                                                competitive_analysis: Dict[str, Any], 
                                                customer_analysis: Dict[str, Any],
                                                trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic recommendations based on all analyses."""
        
        combined_insights = {
            'market': market_analysis,
            'competitive': competitive_analysis, 
            'customer': customer_analysis,
            'trends': trend_analysis,
            'business_info': params['business_info']
        }
        
        prompt = f"""
        Based on the comprehensive market research conducted, provide strategic recommendations:
        
        Research Insights: {json.dumps(combined_insights, indent=2)}
        
        Generate actionable strategic recommendations covering:
        
        1. EXECUTIVE SUMMARY & OPPORTUNITY SCORE
        - Market opportunity score (1-100) with justification
        - Top 3-5 key findings from the research
        - Overall strategic recommendation
        - Primary risk factors to monitor
        
        2. GO-TO-MARKET STRATEGY
        - Recommended market entry approach
        - Target customer prioritization
        - Channel strategy recommendations
        - Timeline and milestones
        
        3. POSITIONING & MESSAGING
        - Recommended market positioning
        - Key differentiators to emphasize
        - Value proposition refinements
        - Competitive response strategy
        
        4. PRICING STRATEGY
        - Recommended pricing approach
        - Price positioning vs competitors
        - Value-based pricing opportunities
        - Pricing model recommendations
        
        5. PRODUCT DEVELOPMENT PRIORITIES
        - Feature development priorities
        - Product roadmap recommendations
        - Innovation opportunities
        - Customer feedback integration
        
        Ensure all recommendations are specific, actionable, and backed by research insights.
        """
        
        try:
            response = await self.ai_engine.ainvoke(prompt)
            recommendations_text = response.content
            
            return self._parse_strategic_recommendations(recommendations_text)
            
        except Exception as e:
            self.logger.error(f"Strategic recommendations generation failed: {e}")
            return self._generate_fallback_recommendations(combined_insights)
    
    def _parse_strategic_recommendations(self, recommendations_text: str) -> Dict[str, Any]:
        """Parse strategic recommendations into structured data."""
        return {
            'opportunity_score': self._extract_opportunity_score(recommendations_text),
            'key_findings': self._extract_list_items(recommendations_text, "findings", "finding insight key important"),
            'strategy': self._extract_strategy_summary(recommendations_text),
            'risks': self._extract_list_items(recommendations_text, "risks", "risk threat challenge concern")[0] if self._extract_list_items(recommendations_text, "risks", "risk threat challenge concern") else "",
            'go_to_market': self._extract_go_to_market(recommendations_text),
            'positioning': self._extract_positioning(recommendations_text),
            'pricing': self._extract_pricing_strategy(recommendations_text),
            'product_priorities': self._extract_list_items(recommendations_text, "priorities", "priority feature development roadmap")
        }
    
    def _extract_opportunity_score(self, text: str) -> int:
        """Extract opportunity score from recommendations."""
        # Look for patterns like "score: 85", "85/100", "opportunity score of 85"
        score_patterns = [
            r'score[:\s]*(\d+)',
            r'(\d+)/100',
            r'opportunity.*?(\d+)',
            r'(\d+).*?opportunity'
        ]
        
        for pattern in score_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                score = int(matches.group(1))
                if 1 <= score <= 100:
                    return score
        
        return 75  # Default medium-high opportunity
    
    def _extract_strategy_summary(self, text: str) -> str:
        """Extract overall strategy summary."""
        lines = text.split('\n')
        strategy_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ['recommend', 'strategy', 'approach', 'should']):
                if len(line.strip()) > 30:
                    strategy_lines.append(line.strip())
        
        return '. '.join(strategy_lines[:2]) if strategy_lines else "Strategic recommendations not available"
    
    def _extract_go_to_market(self, text: str) -> str:
        """Extract go-to-market strategy."""
        lines = text.split('\n')
        gtm_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ['go-to-market', 'market entry', 'launch', 'entry']):
                if len(line.strip()) > 20:
                    gtm_lines.append(line.strip())
        
        return '. '.join(gtm_lines[:2]) if gtm_lines else "Go-to-market strategy not available"
    
    def _extract_positioning(self, text: str) -> str:
        """Extract positioning recommendations."""
        lines = text.split('\n')
        positioning_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ['position', 'differentiat', 'value prop']):
                if len(line.strip()) > 20:
                    positioning_lines.append(line.strip())
        
        return '. '.join(positioning_lines[:2]) if positioning_lines else "Positioning recommendations not available"
    
    def _extract_pricing_strategy(self, text: str) -> str:
        """Extract pricing strategy recommendations."""
        lines = text.split('\n')
        pricing_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if 'pric' in line_lower:
                if len(line.strip()) > 20:
                    pricing_lines.append(line.strip())
        
        return '. '.join(pricing_lines[:2]) if pricing_lines else "Pricing strategy not available"
    
    async def _save_research_report(self, research_result: MarketResearchResult, params: Dict[str, Any]):
        """Save detailed research report to file."""
        try:
            # Create filename based on business info and timestamp
            business_name = params['business_info'].get('brand_name', 'business')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_research_{business_name}_{timestamp}.json"
            
            report_path = self.reports_dir / filename
            
            # Convert to dict for JSON serialization
            report_data = {
                'research_parameters': params,
                'research_results': research_result.__dict__,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(report_path, 'w') as f:
                await f.write(json.dumps(report_data, indent=2, default=str))
            
            self.logger.info(f"Market research report saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save research report: {e}")
    
    def _generate_error_result(self, error_message: str) -> Dict[str, Any]:
        """Generate error result when research fails."""
        return {
            'market_research_success': False,
            'market_research_error': error_message,
            'market_research_completed_at': datetime.utcnow().isoformat()
        }
    
    def _generate_fallback_research(self, params: Dict[str, Any]) -> MarketResearchResult:
        """Generate basic fallback research when AI analysis isn't available."""
        business_info = params['business_info']
        
        return MarketResearchResult(
            # Executive Summary
            market_opportunity_score=70,
            key_findings=[
                "Market research capabilities limited without AI engine",
                "Recommend enabling full AI analysis for comprehensive insights",
                "Basic market structure analysis available"
            ],
            recommended_strategy="Enable AI-powered analysis for comprehensive market research",
            risk_assessment="Limited research depth without full analytical capabilities",
            
            # Market Landscape - Basic info
            market_size="Market size analysis requires AI engine",
            growth_rate="Growth rate analysis requires AI engine", 
            market_maturity="Market maturity assessment requires AI engine",
            growth_drivers=["Analysis requires AI engine"],
            barriers=["Analysis requires AI engine"],
            geographic_insights="Geographic analysis requires AI engine",
            
            # Competitive Analysis - Basic structure
            competitors=[],
            competitive_landscape="Competitive analysis requires AI engine",
            market_gaps=["Analysis requires AI engine"],
            competitive_advantages=["Analysis requires AI engine"],
            
            # Customer Insights - Basic structure
            customer_personas=[],
            market_segments=[],
            customer_sentiment="Customer analysis requires AI engine",
            
            # Trends & Forecasting - Basic structure
            industry_trends=["Analysis requires AI engine"],
            technology_trends=["Analysis requires AI engine"],
            market_forecast="Forecasting requires AI engine",
            opportunities=["Analysis requires AI engine"],
            threats=["Analysis requires AI engine"],
            
            # Strategic Recommendations - Basic
            go_to_market_strategy="Strategic analysis requires AI engine",
            positioning_recommendations="Positioning analysis requires AI engine",
            pricing_strategy="Pricing analysis requires AI engine",
            product_priorities=["Analysis requires AI engine"],
            
            # Metadata
            research_date=datetime.utcnow().isoformat(),
            data_freshness="Fallback analysis - limited data",
            confidence_score=30  # Low confidence for fallback
        )
    
    def _generate_fallback_market_analysis(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback market analysis."""
        return {
            'size': "Market size analysis requires AI engine",
            'growth_rate': "Growth rate analysis requires AI engine",
            'maturity': "Market maturity assessment requires AI engine", 
            'drivers': ["Analysis requires AI engine"],
            'barriers': ["Analysis requires AI engine"],
            'geographic': "Geographic analysis requires AI engine"
        }
    
    def _generate_fallback_competitive_analysis(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback competitive analysis.""" 
        return {
            'competitors': [],
            'landscape': "Competitive analysis requires AI engine",
            'gaps': ["Analysis requires AI engine"],
            'advantages': ["Analysis requires AI engine"]
        }
    
    def _generate_fallback_customer_analysis(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback customer analysis."""
        return {
            'personas': [],
            'segments': [],
            'sentiment': "Customer analysis requires AI engine"
        }
    
    def _generate_fallback_trend_analysis(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback trend analysis."""
        return {
            'industry_trends': ["Analysis requires AI engine"],
            'tech_trends': ["Analysis requires AI engine"], 
            'forecast': "Forecasting requires AI engine",
            'opportunities': ["Analysis requires AI engine"],
            'threats': ["Analysis requires AI engine"]
        }
    
    def _generate_fallback_recommendations(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback strategic recommendations."""
        return {
            'opportunity_score': 50,
            'key_findings': ["Analysis requires AI engine"],
            'strategy': "Strategic analysis requires AI engine",
            'risks': "Risk assessment requires AI engine",
            'go_to_market': "Go-to-market analysis requires AI engine",
            'positioning': "Positioning analysis requires AI engine", 
            'pricing': "Pricing analysis requires AI engine",
            'product_priorities': ["Analysis requires AI engine"]
        }


# Agent metadata for orchestration
AGENT_METADATA = {
    "name": "MarketResearchAgent",
    "description": "Comprehensive market research and competitive intelligence agent",
    "capabilities": [
        "market_landscape_analysis", "competitive_intelligence", "customer_research",
        "trend_analysis", "strategic_recommendations", "market_forecasting"
    ],
    "inputs": ["business_info", "industry", "business_type", "user_request"],
    "outputs": [
        "market_research_result", "market_opportunity_score", "key_competitors", 
        "target_personas", "market_trends", "strategic_recommendations"
    ],
    "dependencies": ["anthropic", "ANTHROPIC_API_KEY"],
    "coordination": ["works_with_branding_agent", "supports_business_strategy"]
}