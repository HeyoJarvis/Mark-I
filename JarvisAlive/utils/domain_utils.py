"""
Domain utility functions for HeyJarvis AI Agent System.

Provides domain availability checking and suggestion generation.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def check_domain_availability(domain: str) -> Dict[str, bool]:
    """
    Check domain availability using WHOIS or DNS lookup.
    
    Args:
        domain: Domain name to check (e.g., "example.com")
        
    Returns:
        Dictionary with availability status for different TLDs
    """
    try:
        # Common TLDs to check
        tlds = ['.com', '.co', '.ai', '.io', '.net']
        results = {}
        
        for tld in tlds:
            full_domain = f"{domain}{tld}"
            is_available = await _check_single_domain(full_domain)
            results[full_domain] = is_available
            
        return results
        
    except Exception as e:
        logger.error(f"Error checking domain availability: {e}")
        return {}


async def _check_single_domain(domain: str) -> bool:
    """
    Check availability of a single domain.
    
    Args:
        domain: Full domain name to check
        
    Returns:
        True if domain appears to be available, False otherwise
    """
    try:
        # Simple DNS lookup approach
        # In a real implementation, you might use WHOIS APIs
        # or services like Domainr, GoDaddy API, etc.
        
        # For now, we'll simulate availability based on domain length
        # This is just a placeholder - real implementation would use actual APIs
        
        # Simulate some domains as taken
        taken_domains = [
            "google.com", "facebook.com", "amazon.com", "netflix.com",
            "apple.com", "microsoft.com", "tesla.com", "spacex.com"
        ]
        
        if domain.lower() in taken_domains:
            return False
        
        # Simulate availability for shorter domains
        domain_name = domain.split('.')[0]
        if len(domain_name) < 3:
            return False  # Too short
        elif len(domain_name) > 20:
            return False  # Too long
        else:
            return True  # Assume available
            
    except Exception as e:
        logger.error(f"Error checking domain {domain}: {e}")
        return False


def generate_domain_suggestions(brand_name: str, max_suggestions: int = 5) -> List[str]:
    """
    Generate domain name suggestions based on brand name.
    
    Args:
        brand_name: The brand name to generate domains for
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        List of domain suggestions
    """
    import re
    
    # Clean the brand name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
    
    suggestions = []
    
    # Common TLDs
    tlds = ['.com', '.co', '.ai', '.io', '.net']
    
    # Generate basic suggestions
    for tld in tlds:
        domain = f"{clean_name}{tld}"
        suggestions.append(domain)
    
    # Generate variations
    if len(clean_name) > 6:
        # Try shorter version
        short_name = clean_name[:6]
        suggestions.append(f"{short_name}.com")
    
    # Add some creative variations
    if len(clean_name) > 4:
        # Add "get" prefix
        suggestions.append(f"get{clean_name}.com")
        # Add "my" prefix
        suggestions.append(f"my{clean_name}.com")
    
    # Limit to max suggestions
    return suggestions[:max_suggestions]


def validate_domain_name(domain: str) -> bool:
    """
    Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if domain format is valid, False otherwise
    """
    import re
    
    # Basic domain validation regex
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    return bool(re.match(domain_pattern, domain))


async def get_domain_info(domain: str) -> Optional[Dict[str, any]]:
    """
    Get information about a domain (placeholder for real implementation).
    
    Args:
        domain: Domain name to get info for
        
    Returns:
        Dictionary with domain information or None if not found
    """
    try:
        # This would typically use WHOIS APIs or domain registrar APIs
        # For now, return a placeholder structure
        
        return {
            "domain": domain,
            "available": await _check_single_domain(domain),
            "registrar": "Unknown",
            "creation_date": None,
            "expiration_date": None,
            "status": "unknown"
        }
        
    except Exception as e:
        logger.error(f"Error getting domain info for {domain}: {e}")
        return None 