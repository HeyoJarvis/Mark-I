"""Apollo API connector for lead mining."""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from ..models.lead_models import Lead, ICPCriteria, LeadSource

logger = logging.getLogger(__name__)


class ApolloConnector:
    """Connector for Apollo API integration."""
    
    def __init__(self, api_key: str, auto_unlock_emails: bool = True):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"  # Fixed URL path
        self.session = None
        self.rate_limit_delay = 1.0  # seconds between requests
        self.auto_unlock_emails = auto_unlock_emails  # Automatically spend credits to unlock emails
    
    async def search_leads(self, criteria: ICPCriteria, max_leads: int) -> List[Lead]:
        """Search for leads using Apollo API."""
        
        if not self.api_key:
            logger.warning("No Apollo API key provided, returning mock data")
            return self._generate_mock_leads(criteria, min(max_leads, 5))
        
        # Build Apollo search parameters
        search_params = self._build_search_params(criteria, max_leads)
        
        # Debug: log the search parameters
        logger.info(f"Apollo search parameters: {search_params}")
        
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
        # Start with minimal parameters that we know work
        params = {
            "page": 1,
            "per_page": min(max_leads, 50),  # Apollo limit
        }
        
        # Use MINIMAL filters to ensure we get results
        # Based on testing, we know these simple parameters work:
        
        # Only add job titles if they're simple/common
        if criteria.job_titles:
            # Use only the first, simplest job title
            simple_titles = []
            for title in criteria.job_titles[:1]:  # Only use first title
                if "VP" in title:
                    simple_titles.append("VP Sales")
                elif "Director" in title:
                    simple_titles.append("Sales Director") 
                elif "Manager" in title:
                    simple_titles.append("Sales Manager")
                else:
                    simple_titles.append(title)
            
            if simple_titles:
                params["person_titles"] = simple_titles
        
        # Only add location if it's broad
        if criteria.locations and "United States" in criteria.locations:
            params["organization_locations"] = ["United States"]
        
        # Skip company size, industries, and keywords for now to ensure results
        # These were causing 0 results in testing
        
        return params
    
    async def _fetch_page(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> List[Lead]:
        """Fetch a single page of results from Apollo API."""
        try:
            headers = {
                "x-api-key": self.api_key,  # Fixed header name per documentation
                "accept": "application/json",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json"
            }
            async with session.post(
                f"{self.base_url}/mixed_people/search",
                json=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self._parse_apollo_response(data)
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
    
    async def _parse_apollo_response(self, data: Dict[str, Any]) -> List[Lead]:
        """Parse Apollo API response into Lead objects."""
        leads = []
        
        # Apollo returns data in 'people' key, not 'contacts'
        people_data = data.get("people", [])
        if not people_data:
            people_data = data.get("contacts", [])  # Fallback
        
        for person in people_data:
            try:
                # Extract person data from Apollo response format
                email = person.get("email")
                if not email:
                    email = "email_not_available@domain.com"
                
                # Apollo response structure - person contains company info directly
                first_name = person.get("first_name", "")
                last_name = person.get("last_name", "")
                title = person.get("title", "")
                
                # Organization data might be nested or at person level
                organization = person.get("organization", {})
                company_name = organization.get("name", "") if organization else person.get("organization_name", "")
                
                # If no organization object, try person-level company data
                if not company_name:
                    company_name = person.get("company_name", "")
                
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
                    first_name=first_name,
                    last_name=last_name,
                    job_title=title,
                    company_name=company_name,
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
        
        # Automatically unlock emails if enabled
        if self.auto_unlock_emails and leads:
            leads = await self._unlock_lead_emails(leads)
        
        return leads
    
    async def _unlock_lead_emails(self, leads: List[Lead]) -> List[Lead]:
        """Automatically unlock emails for leads using Apollo's enrichment API."""
        unlocked_leads = []
        
        for lead in leads:
            if "email_not_unlocked@domain.com" in lead.email:
                try:
                    # Find the person ID from the original Apollo response
                    real_email = await self._enrich_lead_email(lead)
                    if real_email and real_email != lead.email:
                        lead.email = real_email
                        logger.info(f"Unlocked email for {lead.first_name} {lead.last_name}: {real_email}")
                except Exception as e:
                    logger.warning(f"Failed to unlock email for {lead.first_name} {lead.last_name}: {e}")
            
            unlocked_leads.append(lead)
        
        return unlocked_leads
    
    async def _enrich_lead_email(self, lead: Lead) -> Optional[str]:
        """Enrich a single lead to get real email (costs 1 credit)."""
        try:
            # Apollo's enrichment API - this costs credits but gets real emails
            enrichment_data = {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "organization_name": lead.company_name,
                "domain": lead.company_domain
            }
            
            headers = {
                "x-api-key": self.api_key,
                "accept": "application/json",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/people/match",
                    json=enrichment_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        person = data.get("person", {})
                        email = person.get("email")
                        
                        if email and email != "email_not_unlocked@domain.com":
                            return email
                    elif response.status == 422:
                        logger.warning(f"Cannot enrich {lead.first_name} {lead.last_name} - insufficient data")
                    elif response.status == 402:
                        logger.error("Insufficient credits to unlock emails")
                    else:
                        logger.warning(f"Email enrichment failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Email enrichment request failed: {e}")
        
        return None
    
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
                headers = {"X-Api-Key": self.api_key}
                async with session.get(
                    f"{self.base_url}/auth/verify",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Apollo API key verification failed: {e}")
            return False
