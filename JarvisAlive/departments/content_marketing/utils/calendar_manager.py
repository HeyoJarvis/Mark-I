"""Content calendar management utilities."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.calendar_models import ContentCalendar, ContentPlan

logger = logging.getLogger(__name__)


class CalendarManager:
    """Manages content calendar creation and scheduling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def create_calendar(
        self, 
        content_plans: List[ContentPlan],
        calendar_name: str,
        weeks: int = 12
    ) -> ContentCalendar:
        """Create a content calendar from content plans."""
        
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=weeks)
        
        calendar = ContentCalendar(
            calendar_name=calendar_name,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            content_plans=content_plans
        )
        
        self.logger.info(f"Created content calendar with {len(content_plans)} pieces")
        return calendar
