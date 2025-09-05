"""
LeadMiningAgent - Multi-source Lead Discovery and Qualification

Integrates with Apollo, Sales Navigator, ZoomInfo, and Clay for comprehensive
lead discovery based on ICP criteria.
"""

import asyncio
import logging
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig
from .models.lead_models import Lead, ICPCriteria, LeadMiningResult, LeadSource, LeadStatus
from .connectors.apollo_connector import ApolloConnector
from .utils.data_validator import LeadValidator
from .utils.deduplication import LeadDeduplicator

logger = logging.getLogger(__name__)


class LeadMiningAgent:
    """
    AI agent for mining qualified leads from multiple sources.
    
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Lead Mining Agent."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine for ICP analysis
        self._initialize_ai_engine()
        
        # Initialize connectors
        self._initialize_connectors()
        
        # Configuration
        self.max_leads_per_source = self.config.get('max_leads_per_source', 50)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.enable_deduplication = self.config.get('enable_deduplication', True)
        
        # Initialize utilities
        self.validator = LeadValidator()
        self.deduplicator = LeadDeduplicator()
        
        self.logger.info("LeadMiningAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize AI engine for ICP analysis and lead qualification."""
        try:
            api_key = self.config.get('anthropic_api_key') or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                config = AIEngineConfig(
                    api_key=api_key,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.3,  # Low temperature for consistent analysis
                    max_tokens=2000
                )
                self.ai_engine = AnthropicEngine(config)
                self.logger.info("AI engine initialized for ICP analysis")
            else:
                self.ai_engine = None
                self.logger.warning("No AI engine - using basic lead mining")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    def _initialize_connectors(self):
        """Initialize data source connectors."""
        self.connectors = {}
        
        # Apollo connector
        apollo_key = self.config.get('apollo_api_key') or os.getenv('APOLLO_API_KEY')
        if apollo_key:
            self.connectors['apollo'] = ApolloConnector(apollo_key)
            self.logger.info("Apollo connector initialized")
        else:
            # Create connector with empty key for mock data
            self.connectors['apollo'] = ApolloConnector("")
            self.logger.info("Apollo connector initialized in mock mode")
        
        # Add other connectors as needed
        self.logger.info(f"Initialized {len(self.connectors)} data connectors")
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for lead mining.
        
        Expected state format:
        {
            "business_goal": "Find 50 qualified leads for SaaS companies",
            "icp_criteria": {
                "company_size": "50-500",
                "industries": ["Software", "SaaS"],
                "job_titles": ["VP Sales", "Director Marketing"],
                "locations": ["United States"],
                "technologies": ["Salesforce", "HubSpot"]
            },
            "max_leads": 100,
            "sources": ["apollo", "sales_navigator"],
            "exclude_domains": ["competitor1.com"]
        }
        
        Returns state with:
        {
            "leads_found": 45,
            "qualified_leads": [list of Lead objects],
            "mining_result": LeadMiningResult object,
            "next_recommended_action": "enrichment"
        }
        """
        start_time = datetime.now()
        self.logger.info("Starting lead mining process")
        
        try:
            # Step 1: Extract and validate ICP criteria
            icp_criteria = await self._extract_icp_criteria(state)
            if not icp_criteria:
                return self._create_error_response(state, "Invalid or missing ICP criteria")
            
            # Step 2: Mine leads from available sources
            raw_leads = await self._mine_from_sources(icp_criteria, state)
            
            # Step 3: Validate and score leads
            validated_leads = await self._validate_leads(raw_leads)
            
            # Step 4: Deduplicate leads
            if self.enable_deduplication:
                unique_leads = self.deduplicator.deduplicate(validated_leads)
            else:
                unique_leads = validated_leads
            
            # Step 5: Qualify leads using AI
            qualified_leads = await self._qualify_leads(unique_leads, icp_criteria)
            
            # Step 6: Create mining result
            mining_duration = (datetime.now() - start_time).total_seconds()
            mining_result = LeadMiningResult(
                success=True,
                leads_found=len(qualified_leads),
                qualified_leads=qualified_leads,
                search_criteria=icp_criteria,
                sources_used=[LeadSource.APOLLO],  # Update based on actual sources used
                mining_duration_seconds=mining_duration
            )
            
            # Step 7: Update state with results
            result_state = state.copy()
            result_state.update({
                "leads_found": len(qualified_leads),
                "qualified_leads": [lead.__dict__ for lead in qualified_leads],
                "mining_result": mining_result.__dict__,
                "icp_criteria_used": icp_criteria.__dict__,
                "mining_success": True,
                "mining_completed_at": datetime.now().isoformat(),
                "next_recommended_action": "enrichment",
                "data_sources_used": list(self.connectors.keys())
            })
            
            self.logger.info(f"Lead mining completed successfully: {len(qualified_leads)} qualified leads")
            return result_state
            
        except Exception as e:
            self.logger.error(f"Lead mining failed: {e}")
            return self._create_error_response(state, str(e))
    
    async def _extract_icp_criteria(self, state: Dict[str, Any]) -> Optional[ICPCriteria]:
        """Extract ICP criteria from state, using AI if needed."""
        
        # Check if explicit criteria provided
        icp_data = state.get("icp_criteria")
        if icp_data:
            return ICPCriteria(**icp_data)
        
        # Extract from business goal using AI
        business_goal = state.get("business_goal", "")
        if business_goal and self.ai_engine:
            return await self._extract_icp_from_business_goal(business_goal)
        
        # Use defaults
        return ICPCriteria()
    
    async def _extract_icp_from_business_goal(self, business_goal: str) -> ICPCriteria:
        """Use AI to extract ICP criteria from business goal."""
        
        prompt = f"""
Extract Ideal Customer Profile (ICP) criteria from this business goal:

"{business_goal}"

Analyze the request and extract:
- Company size range (employees)
- Industries/verticals
- Geographic locations  
- Job titles to target
- Technologies they might use
- Company keywords/descriptors

Return JSON format:
{{
    "company_size_min": 50,
    "company_size_max": 500,
    "industries": ["Software", "SaaS"],
    "locations": ["United States"],
    "job_titles": ["VP Sales", "Director Marketing"],
    "technologies": ["Salesforce", "HubSpot"],
    "company_keywords": ["B2B", "Enterprise"]
}}

Be specific and realistic based on the business goal.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            data = json.loads(response.content)
            return ICPCriteria(**data)
        except Exception as e:
            self.logger.error(f"AI ICP extraction failed: {e}")
            return ICPCriteria()  # Return defaults
    
    async def _mine_from_sources(self, criteria: ICPCriteria, state: Dict[str, Any]) -> List[Lead]:
        """Mine leads from all available sources."""
        all_leads = []
        max_leads = state.get("max_leads", 100)
        sources = state.get("sources", ["apollo"])
        
        # Distribute lead quota across sources
        leads_per_source = max_leads // len(sources)
        
        # Mine from each source
        mining_tasks = []
        for source in sources:
            if source in self.connectors:
                task = self._mine_from_single_source(
                    self.connectors[source], 
                    criteria, 
                    leads_per_source
                )
                mining_tasks.append(task)
        
        # Execute mining in parallel
        if mining_tasks:
            source_results = await asyncio.gather(*mining_tasks, return_exceptions=True)
            
            for result in source_results:
                if isinstance(result, list):
                    all_leads.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Source mining failed: {result}")
        
        return all_leads
    
    async def _mine_from_single_source(
        self, 
        connector, 
        criteria: ICPCriteria, 
        max_leads: int
    ) -> List[Lead]:
        """Mine leads from a single data source."""
        try:
            return await connector.search_leads(criteria, max_leads)
        except Exception as e:
            self.logger.error(f"Mining from {connector.__class__.__name__} failed: {e}")
            return []
    
    async def _validate_leads(self, leads: List[Lead]) -> List[Lead]:
        """Validate lead data quality."""
        validated_leads = []
        
        for lead in leads:
            # Clean the lead data first
            lead = self.validator.clean_lead_data(lead)
            
            # Validate email format
            if self.validator.is_valid_email(lead.email):
                # Validate domain
                if self.validator.is_valid_domain(lead.company_domain):
                    # Calculate confidence score
                    lead.confidence_score = self.validator.calculate_confidence(lead)
                    
                    # Only keep high-confidence leads
                    if lead.confidence_score >= self.confidence_threshold:
                        lead.status = LeadStatus.VALIDATED
                        validated_leads.append(lead)
        
        self.logger.info(f"Validated {len(validated_leads)}/{len(leads)} leads")
        return validated_leads
    
    async def _qualify_leads(self, leads: List[Lead], criteria: ICPCriteria) -> List[Lead]:
        """Use AI to qualify leads against ICP criteria."""
        if not self.ai_engine:
            # Basic qualification without AI
            qualified = [lead for lead in leads if lead.confidence_score >= self.confidence_threshold]
            for lead in qualified:
                lead.status = LeadStatus.QUALIFIED
            return qualified
        
        qualified_leads = []
        
        # Batch process leads for efficiency
        batch_size = 10
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            qualified_batch = await self._qualify_lead_batch(batch, criteria)
            qualified_leads.extend(qualified_batch)
        
        return qualified_leads
    
    async def _qualify_lead_batch(self, leads: List[Lead], criteria: ICPCriteria) -> List[Lead]:
        """Qualify a batch of leads using AI."""
        
        leads_data = [
            {
                "name": f"{lead.first_name} {lead.last_name}",
                "title": lead.job_title,
                "company": lead.company_name,
                "industry": lead.company_industry,
                "size": lead.company_size,
                "location": lead.company_location
            }
            for lead in leads
        ]
        
        prompt = f"""
Qualify these leads against the ICP criteria:

ICP Criteria:
{criteria.__dict__}

Leads to qualify:
{leads_data}

For each lead, determine:
1. ICP fit score (0.0-1.0)
2. Qualification status (qualified/disqualified)
3. Reason for decision

Return JSON array:
[
    {{
        "lead_index": 0,
        "icp_fit_score": 0.85,
        "qualified": true,
        "reason": "Strong fit: VP Sales at SaaS company in target size range"
    }}
]
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            qualifications = json.loads(response.content)
            
            qualified_leads = []
            for i, qualification in enumerate(qualifications):
                if i < len(leads) and qualification.get("qualified", False):
                    lead = leads[i]
                    lead.confidence_score = qualification.get("icp_fit_score", lead.confidence_score)
                    lead.status = LeadStatus.QUALIFIED
                    qualified_leads.append(lead)
            
            return qualified_leads
            
        except Exception as e:
            self.logger.error(f"AI qualification failed: {e}")
            # Fallback to confidence threshold
            qualified = [lead for lead in leads if lead.confidence_score >= self.confidence_threshold]
            for lead in qualified:
                lead.status = LeadStatus.QUALIFIED
            return qualified
    
    def _create_error_response(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create standardized error response."""
        error_state = state.copy()
        error_state.update({
            "mining_success": False,
            "mining_error": error,
            "leads_found": 0,
            "qualified_leads": [],
            "mining_completed_at": datetime.now().isoformat()
        })
        return error_state
