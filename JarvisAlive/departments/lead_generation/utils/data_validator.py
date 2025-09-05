"""Lead data validation utilities."""

import re
import logging
from typing import Dict, Any
from ..models.lead_models import Lead

logger = logging.getLogger(__name__)


class LeadValidator:
    """Validates lead data quality and accuracy."""
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_valid_domain(self, domain: str) -> bool:
        """Validate domain exists - simplified version without DNS lookup."""
        if not domain:
            return False
        
        # Basic domain format validation
        domain_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, domain):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'\.local$',
            r'test\.',
            r'example\.',
            r'\.test$'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return False
        
        return True
    
    def calculate_confidence(self, lead: Lead) -> float:
        """Calculate confidence score for lead quality."""
        score = 0.0
        
        # Email validation (40% of score)
        if self.is_valid_email(lead.email):
            score += 0.4
        
        # Domain validation (20% of score)
        if self.is_valid_domain(lead.company_domain):
            score += 0.2
        
        # Data completeness (40% of score)
        fields = [lead.first_name, lead.last_name, lead.job_title, 
                 lead.company_name, lead.company_industry]
        filled_fields = sum(1 for field in fields if field and field.strip())
        score += (filled_fields / len(fields)) * 0.4
        
        return round(score, 2)
    
    def validate_lead_completeness(self, lead: Lead) -> bool:
        """Check if lead has minimum required data."""
        required_fields = [
            lead.email,
            lead.first_name,
            lead.last_name,
            lead.company_name
        ]
        
        return all(field and field.strip() for field in required_fields)
    
    def clean_lead_data(self, lead: Lead) -> Lead:
        """Clean and normalize lead data."""
        # Clean email
        if lead.email:
            lead.email = lead.email.strip().lower()
        
        # Clean names
        if lead.first_name:
            lead.first_name = lead.first_name.strip().title()
        if lead.last_name:
            lead.last_name = lead.last_name.strip().title()
        
        # Clean company data
        if lead.company_name:
            lead.company_name = lead.company_name.strip()
        if lead.company_domain:
            lead.company_domain = lead.company_domain.strip().lower()
            # Remove http/https prefixes
            lead.company_domain = re.sub(r'^https?://', '', lead.company_domain)
            # Remove trailing slash
            lead.company_domain = lead.company_domain.rstrip('/')
        
        # Clean job title
        if lead.job_title:
            lead.job_title = lead.job_title.strip()
        
        return lead
