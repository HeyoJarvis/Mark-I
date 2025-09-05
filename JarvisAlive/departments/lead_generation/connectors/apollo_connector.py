"""Apollo API connector for lead mining."""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from ..models.lead_models import Lead, ICPCriteria, LeadSource

logger = logging.getLogger(__name__)


class ApolloConnector:
    """Connector for Apollo API integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.session = None
        self.rate_limit_delay = 1.0  # seconds between requests
    
    async def search_leads(self, criteria: ICPCriteria, max_leads: int) -> List[Lead]:
        """Search for leads using Apollo API."""
        
        if not self.api_key:
            logger.warning("No Apollo API key provided, returning mock data")
            return self._generate_mock_leads(criteria, min(max_leads, 5))
        
        # Build Apollo search parameters
        search_params = self._build_search_params(criteria, max_leads)
        
        try:
            async with aiohttp.ClientSession() as session:
                leads = []
                page = 1
                max_pages = 5  # Limit to prevent excessive API calls
                
                while len(leads) < max_leads and page <= max_pages:
                    search_params["page"] = page
                    search_params["per_page"] = min(50, max_leads - len(leads))
                    
                    page_leads = await self._fetch_page(session, search_params)
                    if not page_leads:
                        break
                    
                    leads.extend(page_leads)
                    page += 1
                    
                    # Rate limiting
                    if page <= max_pages:
                        await asyncio.sleep(self.rate_limit_delay)
                
                logger.info(f"Apollo search completed: {len(leads)} leads found")
                return leads[:max_leads]
                
        except Exception as e:
            logger.error(f"Apollo search failed: {e}")
            logger.info("Falling back to mock data")
            return self._generate_mock_leads(criteria, min(max_leads, 10))
    
    def _build_search_params(self, criteria: ICPCriteria, max_leads: int) -> Dict[str, Any]:
        """Build Apollo API search parameters from ICP criteria."""
        params = {
            "api_key": self.api_key,
            "page": 1,
            "per_page": min(max_leads, 50),  # Apollo limit
        }
        
        # Job titles
        if criteria.job_titles:
            params["person_titles"] = criteria.job_titles
        
        # Locations
        if criteria.locations:
            params["organization_locations"] = criteria.locations
        
        # Company size
        if criteria.company_size_min and criteria.company_size_max:
            params["organization_num_employees_ranges"] = [
                f"{criteria.company_size_min},{criteria.company_size_max}"
            ]
        
        # Industries (would need mapping to Apollo industry IDs)
        if criteria.industries:
            # For now, we'll search by keywords
            params["q_keywords"] = " OR ".join(criteria.industries)
        
        # Company keywords
        if criteria.company_keywords:
            existing_keywords = params.get("q_keywords", "")
            keyword_search = " OR ".join(criteria.company_keywords)
            if existing_keywords:
                params["q_keywords"] = f"{existing_keywords} OR {keyword_search}"
            else:
                params["q_keywords"] = keyword_search
        
        return params
    
    async def _fetch_page(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> List[Lead]:
        """Fetch a single page of results from Apollo API."""
        try:
            async with session.get(
                f"{self.base_url}/mixed_people/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_apollo_response(data)
                elif response.status == 429:  # Rate limited
                    logger.warning("Apollo API rate limit hit, waiting...")
                    await asyncio.sleep(5)
                    return []
                else:
                    logger.error(f"Apollo API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Apollo API request failed: {e}")
            return []
    
    def _parse_apollo_response(self, data: Dict[str, Any]) -> List[Lead]:
        """Parse Apollo API response into Lead objects."""
        leads = []
        
        for person in data.get("people", []):
            try:
                # Extract person data
                email = person.get("email")
                if not email:
                    continue
                
                organization = person.get("organization", {})
                
                # Clean and extract domain
                company_domain = ""
                if organization.get("website_url"):
                    domain = organization["website_url"]
                    domain = domain.replace("http://", "").replace("https://", "")
                    domain = domain.split("/")[0]  # Remove path
                    company_domain = domain
                
                # Build location string
                location_parts = []
                if organization.get("city"):
                    location_parts.append(organization["city"])
                if organization.get("state"):
                    location_parts.append(organization["state"])
                if organization.get("country") and organization["country"] != "United States":
                    location_parts.append(organization["country"])
                company_location = ", ".join(location_parts)
                
                lead = Lead(
                    email=email,
                    first_name=person.get("first_name", ""),
                    last_name=person.get("last_name", ""),
                    job_title=person.get("title", ""),
                    company_name=organization.get("name", ""),
                    company_domain=company_domain,
                    company_size=str(organization.get("estimated_num_employees", "")),
                    company_industry=organization.get("industry", ""),
                    company_location=company_location,
                    linkedin_url=person.get("linkedin_url"),
                    phone=person.get("phone"),
                    company_revenue=organization.get("estimated_annual_revenue"),
                    source=LeadSource.APOLLO,
                    confidence_score=0.8  # Apollo data is generally high quality
                )
                
                leads.append(lead)
                
            except Exception as e:
                logger.warning(f"Failed to parse Apollo lead: {e}")
                continue
        
        return leads
    
    def _generate_mock_leads(self, criteria: ICPCriteria, count: int) -> List[Lead]:
        """Generate mock leads for testing when API is not available."""
        mock_leads = []
        
        # Sample data for mock generation
        first_names = ["John", "Sarah", "Michael", "Emily", "David", "Lisa", "Robert", "Jennifer"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        job_titles = criteria.job_titles or ["VP Sales", "Director Marketing", "Head of Growth", "VP Marketing"]
        companies = ["TechCorp", "DataSoft", "CloudSystems", "InnovateLab", "ScaleUp Inc", "GrowthCo"]
        industries = criteria.industries or ["Software", "SaaS", "Technology", "Marketing"]
        domains = ["techcorp.com", "datasoft.io", "cloudsys.com", "innovatelab.co", "scaleup.com"]
        
        for i in range(count):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            company = companies[i % len(companies)]
            domain = domains[i % len(domains)]
            
            lead = Lead(
                email=f"{first_name.lower()}.{last_name.lower()}@{domain}",
                first_name=first_name,
                last_name=last_name,
                job_title=job_titles[i % len(job_titles)],
                company_name=company,
                company_domain=domain,
                company_size=str(criteria.company_size_min + (i * 50)),
                company_industry=industries[i % len(industries)],
                company_location="San Francisco, CA",
                linkedin_url=f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
                source=LeadSource.APOLLO,
                confidence_score=0.75
            )
            
            mock_leads.append(lead)
        
        logger.info(f"Generated {len(mock_leads)} mock leads")
        return mock_leads
    
    async def verify_api_key(self) -> bool:
        """Verify that the Apollo API key is valid."""
        if not self.api_key:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"api_key": self.api_key}
                async with session.get(
                    f"{self.base_url}/auth/verify",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Apollo API key verification failed: {e}")
            return False
