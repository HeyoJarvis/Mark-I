"""
Context Retrieval Service - Gets relevant previous work for current requests
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .universal_context_store import UniversalContextStore, ContextType
from .context_analyzer import ContextReference

logger = logging.getLogger(__name__)


class ContextRetrievalService:
    """Retrieves and formats context for current requests."""
    
    def __init__(self, context_store: UniversalContextStore):
        self.context_store = context_store
        self.logger = logging.getLogger(__name__)
    
    async def retrieve_relevant_context(
        self, 
        session_id: str, 
        context_ref: ContextReference
    ) -> Dict[str, Any]:
        """Retrieve all relevant context based on reference analysis."""
        
        context_data = {}
        
        for context_type in context_ref.context_types:
            try:
                # Map recency to hours
                hours_back = {
                    "current_session": 2,
                    "today": 24,
                    "this_week": 168
                }.get(context_ref.recency_requirement, 2)
                
                # Get context for this type
                agent_context = await self.context_store.get_recent_context(
                    session_id, 
                    context_type, 
                    hours_back
                )
                
                if agent_context:
                    context_data[context_type] = agent_context
                    
            except Exception as e:
                self.logger.error(f"Failed to retrieve {context_type} context: {e}")
        
        return context_data
