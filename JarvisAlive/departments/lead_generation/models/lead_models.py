"""Data models for lead generation."""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LeadSource(str, Enum):
    APOLLO = "apollo"
    SALES_NAVIGATOR = "sales_navigator"
    ZOOMINFO = "zoominfo"
    CLAY = "clay"


class LeadStatus(str, Enum):
    RAW = "raw"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


@dataclass
class ICPCriteria:
    """Ideal Customer Profile criteria for lead mining."""
    company_size_min: int = 50
    company_size_max: int = 500
    industries: List[str] = None
    locations: List[str] = None
    technologies: List[str] = None
    job_titles: List[str] = None
    company_keywords: List[str] = None
    exclude_domains: List[str] = None
    exclude_companies: List[str] = None
    revenue_min: Optional[int] = None
    revenue_max: Optional[int] = None
    
    def __post_init__(self):
        if self.industries is None:
            self.industries = []
        if self.locations is None:
            self.locations = ["United States"]
        if self.job_titles is None:
            self.job_titles = ["VP Sales", "Director Marketing", "Head of Growth"]
        if self.company_keywords is None:
            self.company_keywords = []
        if self.exclude_domains is None:
            self.exclude_domains = []
        if self.exclude_companies is None:
            self.exclude_companies = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ICPCriteria to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Lead:
    """Individual lead record with validation."""
    # Contact info
    email: str
    first_name: str
    last_name: str
    job_title: str
    
    # Company info
    company_name: str
    company_domain: str
    company_size: str
    company_industry: str
    company_location: str
    
    # Optional enrichment data
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    company_revenue: Optional[str] = None
    company_technologies: List[str] = None
    
    # Metadata
    source: LeadSource = LeadSource.APOLLO
    confidence_score: float = 0.0
    status: LeadStatus = LeadStatus.RAW
    discovered_at: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if self.company_technologies is None:
            self.company_technologies = []
        if not self.discovered_at:
            self.discovered_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Lead to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['source'] = self.source.value
        data['status'] = self.status.value
        return data
    
    @property
    def full_name(self) -> str:
        """Get full name of the lead."""
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class LeadMiningResult:
    """Result of lead mining operation."""
    success: bool
    leads_found: int
    qualified_leads: List[Lead]
    search_criteria: ICPCriteria
    sources_used: List[LeadSource]
    mining_duration_seconds: float
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LeadMiningResult to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert complex objects to serializable formats
        data['qualified_leads'] = [lead.to_dict() for lead in self.qualified_leads]
        data['search_criteria'] = self.search_criteria.to_dict()
        data['sources_used'] = [source.value for source in self.sources_used]
        return data
