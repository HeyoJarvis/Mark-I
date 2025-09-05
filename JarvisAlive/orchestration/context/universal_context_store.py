"""
Universal Context Store - Cross-agent context management
"""

import json
import logging
import redis.asyncio as redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..workflow_result_store import WorkflowJSONEncoder

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    BRANDING = "branding"
    MARKET_RESEARCH = "market_research" 
    LEAD_MINING = "lead_mining"
    WEBSITE = "website"
    CONTENT_MARKETING = "content_marketing"
    SOCIAL_INTELLIGENCE = "social_intelligence"


@dataclass
class ContextItem:
    """Individual context item with metadata."""
    context_type: ContextType
    data: Dict[str, Any]
    session_id: str
    workflow_id: str
    timestamp: str
    business_goal: str
    agent_id: str


class UniversalContextStore:
    """Stores and retrieves context across ALL agent types."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Define what data to extract from each agent type
        self.context_extractors = {
            ContextType.BRANDING: self._extract_branding_context,
            ContextType.MARKET_RESEARCH: self._extract_market_research_context,
            ContextType.LEAD_MINING: self._extract_lead_mining_context,
            ContextType.WEBSITE: self._extract_website_context,
            ContextType.CONTENT_MARKETING: self._extract_content_marketing_context,
            ContextType.SOCIAL_INTELLIGENCE: self._extract_social_intelligence_context,
        }
    
    async def store_agent_context(
        self, 
        session_id: str, 
        agent_id: str, 
        results: Dict[str, Any]
    ) -> bool:
        """Store agent results as queryable context."""
        
        try:
            # Determine context type from agent_id
            context_type = self._map_agent_to_context_type(agent_id)
            if not context_type:
                self.logger.debug(f"No context mapping for agent {agent_id}")
                return False
            
            # Extract relevant context using specific extractor
            extractor = self.context_extractors.get(context_type)
            if not extractor:
                self.logger.debug(f"No extractor for context type {context_type}")
                return False
            
            extracted_data = extractor(results)
            if not extracted_data:
                self.logger.debug(f"No extractable data for {context_type}")
                return False
            
            # Create context item
            context_item = ContextItem(
                context_type=context_type,
                data=extracted_data,
                session_id=session_id,
                workflow_id=results.get("workflow_id", "unknown"),
                timestamp=datetime.utcnow().isoformat(),
                business_goal=results.get("business_goal", ""),
                agent_id=agent_id
            )
            
            # Store in Redis with multiple access patterns
            await self._store_context_item(context_item)
            
            self.logger.info(f"✅ Stored {context_type.value} context for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store context: {e}")
            return False
    
    def _map_agent_to_context_type(self, agent_id: str) -> Optional[ContextType]:
        """Map agent ID to context type."""
        mapping = {
            "branding_agent": ContextType.BRANDING,
            "market_research_agent": ContextType.MARKET_RESEARCH,
            "lead_mining_agent": ContextType.LEAD_MINING,
            "website_generator_agent": ContextType.WEBSITE,
            "content_marketing_agent": ContextType.CONTENT_MARKETING,
            "social_listening_agent": ContextType.SOCIAL_INTELLIGENCE,
        }
        return mapping.get(agent_id)
    
    def _extract_branding_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract branding-specific context."""
        extracted = {}
        
        # Extract from different possible result structures
        if "brand_name" in results:
            extracted["brand_name"] = results["brand_name"]
        if "color_palette" in results:
            extracted["color_palette"] = results["color_palette"]
        if "logo_prompt" in results:
            extracted["logo_prompt"] = results["logo_prompt"]
        if "domain_suggestions" in results:
            extracted["domain_suggestions"] = results["domain_suggestions"]
        
        return extracted if extracted else None
    
    def _extract_market_research_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract market research context."""
        extracted = {}
        
        if "market_opportunity_score" in results:
            extracted["opportunity_score"] = results["market_opportunity_score"]
        if "key_findings" in results:
            extracted["key_findings"] = results["key_findings"]
        if "market_analysis" in results:
            extracted["market_analysis"] = results["market_analysis"]
        if "competitors" in results:
            extracted["competitors"] = results["competitors"]
        if "target_personas" in results:
            extracted["target_personas"] = results["target_personas"]
        
        return extracted if extracted else None
    
    def _extract_lead_mining_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lead mining context."""
        qualified_leads = results.get("qualified_leads", [])
        
        # Convert lead objects to dicts for storage
        leads_data = []
        for lead in qualified_leads[:10]:  # Store top 10 leads
            if hasattr(lead, 'to_dict'):
                leads_data.append(lead.to_dict())
            elif isinstance(lead, dict):
                leads_data.append(lead)
            elif hasattr(lead, '__dict__'):
                leads_data.append(lead.__dict__)
        
        if not leads_data and not results.get("leads_found"):
            return None
        
        return {
            "qualified_leads": leads_data,
            "leads_found": results.get("leads_found", 0),
            "icp_criteria_used": results.get("icp_criteria_used", {}),
            "apollo_status": "connected" if results.get("mining_success") else "failed",
            "lead_count": len(leads_data),
            "top_companies": [lead.get("company_name", "") for lead in leads_data[:5] if lead.get("company_name")],
            "top_titles": list(set(lead.get("job_title", "") for lead in leads_data[:5] if lead.get("job_title"))),
            "csv_file": results.get("leads_csv_file"),
        }
    
    def _extract_website_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract website generation context."""
        extracted = {}
        
        if "sitemap" in results:
            extracted["sitemap"] = results["sitemap"]
        if "homepage" in results:
            extracted["homepage"] = results["homepage"]
        if "style_guide" in results:
            extracted["style_guide"] = results["style_guide"]
        if "seo_recommendations" in results:
            extracted["seo_recommendations"] = results["seo_recommendations"]
        
        return extracted if extracted else None
    
    def _extract_content_marketing_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content marketing context."""
        extracted = {}
        
        if "content_calendar" in results:
            extracted["content_calendar"] = results["content_calendar"]
        if "content_gaps" in results:
            extracted["content_gaps"] = results["content_gaps"]
        if "seo_keywords" in results:
            extracted["seo_keywords"] = results["seo_keywords"]
        
        return extracted if extracted else None
    
    def _extract_social_intelligence_context(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract social intelligence context."""
        extracted = {}
        
        if "social_mentions" in results:
            extracted["mentions"] = results["social_mentions"]
        if "sentiment_summary" in results:
            extracted["sentiment"] = results["sentiment_summary"]
        if "engagement_opportunities" in results:
            extracted["engagement_opportunities"] = results["engagement_opportunities"]
        
        return extracted if extracted else None
    
    async def _store_context_item(self, context_item: ContextItem) -> bool:
        """Store context item with multiple access patterns."""
        
        try:
            timestamp_key = int(datetime.utcnow().timestamp())
            
            # Primary storage key
            primary_key = f"agent_context:{context_item.session_id}:{context_item.context_type.value}:{timestamp_key}"
            
            # Store the context data
            await self.redis_client.setex(
                primary_key,
                7 * 24 * 60 * 60,  # 7 days TTL
                json.dumps({
                    "data": context_item.data,
                    "timestamp": context_item.timestamp,
                    "workflow_id": context_item.workflow_id,
                    "business_goal": context_item.business_goal,
                    "agent_id": context_item.agent_id
                }, cls=WorkflowJSONEncoder)
            )
            
            # Session index (for "show me everything from this session")
            session_index_key = f"session_context_index:{context_item.session_id}"
            await self.redis_client.lpush(session_index_key, primary_key)
            await self.redis_client.expire(session_index_key, 7 * 24 * 60 * 60)
            
            # Type index (for "show me all my lead generation work")
            type_index_key = f"context_type_index:{context_item.context_type.value}"
            await self.redis_client.lpush(type_index_key, primary_key)
            await self.redis_client.expire(type_index_key, 30 * 24 * 60 * 60)  # 30 days
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store context item: {e}")
            return False
    
    async def get_recent_context(self, session_id: str, context_type: str, hours_back: int = 2) -> Optional[Dict[str, Any]]:
        """Get most recent context of specific type for session."""
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            pattern = f"agent_context:{session_id}:{context_type}:*"
            
            keys = await self.redis_client.keys(pattern)
            
            # Find most recent within time bounds
            for key in sorted(keys, reverse=True):
                context_json = await self.redis_client.get(key)
                if context_json:
                    context_item = json.loads(context_json)
                    context_time = datetime.fromisoformat(context_item["timestamp"])
                    
                    if context_time >= cutoff_time:
                        return context_item["data"]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get recent context: {e}")
            return None
