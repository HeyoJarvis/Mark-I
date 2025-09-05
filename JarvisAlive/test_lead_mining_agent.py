"""Test Lead Mining Agent directly."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from departments.lead_generation.lead_mining_agent import LeadMiningAgent


async def test_lead_mining_direct():
    """Test Lead Mining Agent with direct execution."""
    
    print("🧪 Testing Lead Mining Agent - Direct Execution")
    print("=" * 60)
    
    agent = LeadMiningAgent()
    
    # Test Case 1: Basic lead mining with explicit ICP criteria
    test_state_1 = {
        "business_goal": "Find 20 qualified leads for SaaS companies in the US",
        "icp_criteria": {
            "company_size_min": 50,
            "company_size_max": 500,
            "industries": ["Software", "SaaS"],
            "job_titles": ["VP Sales", "Director Marketing", "Head of Growth"],
            "locations": ["United States"]
        },
        "max_leads": 10,
        "sources": ["apollo"]
    }
    
    print("\n🧪 Test 1: Explicit ICP Criteria")
    print("-" * 40)
    result_1 = await agent.run(test_state_1)
    
    print(f"✅ Success: {result_1.get('mining_success')}")
    print(f"📊 Leads found: {result_1.get('leads_found')}")
    if result_1.get('qualified_leads'):
        first_lead = result_1['qualified_leads'][0]
        print(f"📋 First lead: {first_lead.get('first_name')} {first_lead.get('last_name')} at {first_lead.get('company_name')}")
        print(f"📧 Email: {first_lead.get('email')}")
        print(f"🎯 Confidence: {first_lead.get('confidence_score')}")
    
    # Test Case 2: AI-extracted ICP from business goal
    test_state_2 = {
        "business_goal": "I need prospects for my marketing automation software targeting B2B companies with 100-300 employees",
        "max_leads": 5,
        "sources": ["apollo"]
    }
    
    print("\n🧪 Test 2: AI-Extracted ICP from Business Goal")
    print("-" * 40)
    result_2 = await agent.run(test_state_2)
    
    print(f"✅ Success: {result_2.get('mining_success')}")
    print(f"📊 Leads found: {result_2.get('leads_found')}")
    if result_2.get('icp_criteria_used'):
        criteria = result_2['icp_criteria_used']
        print(f"🎯 Extracted ICP: {criteria.get('industries', [])} companies, {criteria.get('company_size_min')}-{criteria.get('company_size_max')} employees")
    
    # Test Case 3: Error handling
    test_state_3 = {
        "max_leads": 5,
        "sources": ["invalid_source"]
    }
    
    print("\n🧪 Test 3: Error Handling")
    print("-" * 40)
    result_3 = await agent.run(test_state_3)
    
    print(f"✅ Handled gracefully: {not result_3.get('mining_success')}")
    if result_3.get('mining_error'):
        print(f"❌ Error message: {result_3['mining_error']}")
    
    print("\n" + "=" * 60)
    print("🎯 Lead Mining Agent direct testing complete")
    
    return result_1, result_2, result_3


async def test_lead_validation():
    """Test lead validation components."""
    print("\n🧪 Testing Lead Validation Components")
    print("-" * 40)
    
    from departments.lead_generation.utils.data_validator import LeadValidator
    from departments.lead_generation.utils.deduplication import LeadDeduplicator
    from departments.lead_generation.models.lead_models import Lead, LeadSource
    
    validator = LeadValidator()
    deduplicator = LeadDeduplicator()
    
    # Test email validation
    test_emails = [
        "valid@company.com",
        "invalid-email",
        "test@test.com",
        "",
        "user@domain"
    ]
    
    print("📧 Email Validation:")
    for email in test_emails:
        is_valid = validator.is_valid_email(email)
        print(f"  {email}: {'✅' if is_valid else '❌'}")
    
    # Test domain validation
    test_domains = [
        "company.com",
        "test.io",
        "localhost",
        "example.com",
        ""
    ]
    
    print("\n🌐 Domain Validation:")
    for domain in test_domains:
        is_valid = validator.is_valid_domain(domain)
        print(f"  {domain}: {'✅' if is_valid else '❌'}")
    
    # Test deduplication
    duplicate_leads = [
        Lead(
            email="john.doe@company.com",
            first_name="John",
            last_name="Doe",
            job_title="VP Sales",
            company_name="TechCorp",
            company_domain="techcorp.com",
            company_size="200",
            company_industry="Software",
            company_location="San Francisco, CA"
        ),
        Lead(
            email="john.doe@company.com",  # Duplicate email
            first_name="John",
            last_name="Doe",
            job_title="VP Sales",
            company_name="TechCorp",
            company_domain="techcorp.com",
            company_size="200",
            company_industry="Software",
            company_location="San Francisco, CA"
        ),
        Lead(
            email="jane.smith@company.com",
            first_name="Jane",
            last_name="Smith",
            job_title="Director Marketing",
            company_name="TechCorp",
            company_domain="techcorp.com",
            company_size="200",
            company_industry="Software",
            company_location="San Francisco, CA"
        )
    ]
    
    print(f"\n🔄 Deduplication Test:")
    print(f"  Original leads: {len(duplicate_leads)}")
    unique_leads = deduplicator.deduplicate(duplicate_leads)
    print(f"  After deduplication: {len(unique_leads)}")
    print(f"  Duplicates removed: {'✅' if len(unique_leads) == 2 else '❌'}")


if __name__ == "__main__":
    asyncio.run(test_lead_mining_direct())
    asyncio.run(test_lead_validation())
