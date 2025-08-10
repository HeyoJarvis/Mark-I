#!/usr/bin/env python3
"""
Test script for Enhanced Branding Agent with Market Research

This script demonstrates the enhanced branding agent that now supports
both branding creation and comprehensive market research analysis.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from departments.branding.branding_agent import BrandingAgent


def test_enhanced_branding_agent():
    """Test the enhanced branding agent with different types of requests."""
    print("🧪 Testing Enhanced Branding Agent with Market Research")
    print("=" * 60)
    
    # Initialize the agent
    agent = BrandingAgent()
    
    # Test cases
    test_cases = [
        {
            "name": "Basic Branding Request",
            "input": {
                "business_idea": "I want to start a coffee shop for professionals",
                "product_type": "coffee",
                "target_audience": "professionals"
            },
            "expected_type": "branding_only"
        },
        {
            "name": "Market Research Request",
            "input": {
                "business_idea": "Research the pen market and identify opportunities",
                "product_type": "writing instruments",
                "target_audience": "offices, schools, retailers"
            },
            "expected_type": "branding_and_market_research"
        },
        {
            "name": "Competitive Analysis Request",
            "input": {
                "business_idea": "Analyze the competitive landscape for eco-friendly products",
                "product_type": "sustainable products",
                "target_audience": "environmentally conscious consumers"
            },
            "expected_type": "branding_and_market_research"
        },
        {
            "name": "Industry Analysis Request",
            "input": {
                "business_idea": "Research the tech startup market and pricing strategies",
                "product_type": "software",
                "target_audience": "small businesses"
            },
            "expected_type": "branding_and_market_research"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Run the agent
            result = agent.run(test_case['input'])
            
            # Display results
            print(f"✅ Status: Success")
            print(f"📊 Analysis Type: {result.get('analysis_type', 'unknown')}")
            
            # Show branding results
            brand_name = result.get('brand_name', 'N/A')
            print(f"🎨 Brand Name: {brand_name}")
            
            # Show market research if available
            market_research = result.get('market_research', {})
            if market_research:
                print(f"📊 Market Research: Available")
                
                # Show key market insights
                market_size = market_research.get('market_size', {})
                if market_size:
                    print(f"  📈 Market Size: {market_size.get('total_market_size', 'N/A')}")
                
                competitive = market_research.get('competitive_landscape', {})
                if competitive:
                    competitors = competitive.get('major_competitors', [])
                    print(f"  🏢 Competitors: {len(competitors)} identified")
                
                opportunity = market_research.get('opportunity_assessment', {})
                if opportunity:
                    print(f"  💡 Opportunity: {opportunity.get('market_opportunity', 'N/A')[:50]}...")
            else:
                print(f"📊 Market Research: Not requested")
            
            # Validate expected type
            actual_type = result.get('analysis_type', 'unknown')
            expected_type = test_case['expected_type']
            
            if actual_type == expected_type:
                print(f"✅ Type Match: Expected {expected_type}, got {actual_type}")
            else:
                print(f"⚠️ Type Mismatch: Expected {expected_type}, got {actual_type}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🎉 Enhanced Branding Agent Test Completed!")
    print("\n💡 Key Features Demonstrated:")
    print("• Automatic detection of market research requests")
    print("• Comprehensive market analysis when requested")
    print("• Branding assets generation for all requests")
    print("• Structured output with both branding and market data")


if __name__ == "__main__":
    test_enhanced_branding_agent() 