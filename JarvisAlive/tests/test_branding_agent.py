#!/usr/bin/env python3
"""
Test suite for BrandingAgent

Tests the branding generation functionality including:
- Business intent parsing
- Brand name generation
- Logo prompt creation
- Color palette generation
- Domain suggestions
"""

import sys
import os
import asyncio
import json
import pytest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from departments.branding.branding_agent import BrandingAgent, BrandingResult


class TestBrandingAgent:
    """Test cases for BrandingAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = BrandingAgent()
    
    def test_agent_initialization(self):
        """Test that BrandingAgent initializes correctly"""
        agent = BrandingAgent()
        assert agent is not None
        assert hasattr(agent, 'run')
        assert hasattr(agent, '_extract_business_info')
        assert hasattr(agent, '_generate_branding_assets')
    
    def test_extract_business_info_basic(self):
        """Test basic business info extraction"""
        state = {
            "business_idea": "I want to start a premium pen brand",
            "product_type": "pens"
        }
        
        business_info = self.agent._extract_business_info(state)
        
        assert business_info is not None
        assert business_info['business_idea'] == "I want to start a premium pen brand"
        assert business_info['product_type'] == "pens"
    
    def test_extract_business_info_alternative_fields(self):
        """Test extraction using alternative field names"""
        state = {
            "description": "Creating eco-friendly water bottles",
            "idea": "Sustainable hydration solutions",
            "niche": "environmental"
        }
        
        business_info = self.agent._extract_business_info(state)
        
        assert business_info is not None
        assert business_info['business_idea'] == "Creating eco-friendly water bottles"
        assert business_info['industry'] == "environmental"
    
    def test_extract_business_info_missing_data(self):
        """Test handling of missing business data"""
        state = {
            "unrelated_field": "some value"
        }
        
        business_info = self.agent._extract_business_info(state)
        
        assert business_info is None
    
    def test_extract_business_info_complete(self):
        """Test extraction with complete business information"""
        state = {
            "business_idea": "Launching a luxury coffee subscription service",
            "product_type": "coffee",
            "business_name": "BrewMaster",
            "target_audience": "coffee enthusiasts",
            "industry": "food and beverage"
        }
        
        business_info = self.agent._extract_business_info(state)
        
        assert business_info is not None
        assert business_info['business_idea'] == "Launching a luxury coffee subscription service"
        assert business_info['product_type'] == "coffee"
        assert business_info['business_name'] == "BrewMaster"
        assert business_info['target_audience'] == "coffee enthusiasts"
        assert business_info['industry'] == "food and beverage"
    
    def test_generate_domain_suggestions(self):
        """Test domain suggestion generation"""
        brand_name = "Inkspire"
        suggestions = self.agent._generate_domain_suggestions(brand_name)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Check that all suggestions contain valid TLDs
        valid_tlds = ['.com', '.co', '.ai', '.io', '.net']
        assert all(any(tld in suggestion for tld in valid_tlds) for suggestion in suggestions)
        assert 'inkspire.com' in suggestions
    
    def test_generate_domain_suggestions_special_characters(self):
        """Test domain generation with special characters"""
        brand_name = "Tech&Co"
        suggestions = self.agent._generate_domain_suggestions(brand_name)
        
        # Should clean special characters
        assert all('&' not in suggestion for suggestion in suggestions)
        assert 'techco.com' in suggestions
    
    def test_create_branding_prompt(self):
        """Test branding prompt creation"""
        business_info = {
            "business_idea": "Premium pen brand",
            "product_type": "pens",
            "target_audience": "professionals"
        }
        
        prompt = self.agent._create_branding_prompt(business_info)
        
        assert isinstance(prompt, str)
        assert "Premium pen brand" in prompt
        assert "pens" in prompt
        assert "professionals" in prompt
        assert "brand_name" in prompt
        assert "logo_prompt" in prompt
        assert "color_palette" in prompt
    
    def test_parse_ai_response_valid(self):
        """Test parsing of valid AI response"""
        valid_response = '''
        {
          "brand_name": "Inkspire",
          "logo_prompt": "Design a sleek, modern logo for a premium pen company called Inkspire.",
          "color_palette": ["#1B263B", "#415A77", "#E0E1DD"]
        }
        '''
        
        result = self.agent._parse_ai_response(valid_response)
        
        assert result['brand_name'] == "Inkspire"
        assert result['logo_prompt'] == "Design a sleek, modern logo for a premium pen company called Inkspire."
        assert result['color_palette'] == ["#1B263B", "#415A77", "#E0E1DD"]
    
    def test_parse_ai_response_invalid_json(self):
        """Test handling of invalid JSON response"""
        invalid_response = "This is not JSON"
        
        with pytest.raises(ValueError):
            self.agent._parse_ai_response(invalid_response)
    
    def test_parse_ai_response_missing_fields(self):
        """Test handling of response with missing required fields"""
        incomplete_response = '''
        {
          "brand_name": "Inkspire"
        }
        '''
        
        with pytest.raises(ValueError):
            self.agent._parse_ai_response(incomplete_response)
    
    def test_parse_ai_response_invalid_colors(self):
        """Test handling of invalid color format"""
        invalid_colors_response = '''
        {
          "brand_name": "Inkspire",
          "logo_prompt": "Design a logo",
          "color_palette": ["invalid", "#123456", "not-hex"]
        }
        '''
        
        with pytest.raises(ValueError):
            self.agent._parse_ai_response(invalid_colors_response)
    
    def test_generate_fallback_branding(self):
        """Test fallback branding generation"""
        business_info = {
            "business_idea": "Premium pen brand",
            "product_type": "pens"
        }
        
        result = self.agent._generate_fallback_branding(business_info)
        
        assert isinstance(result, BrandingResult)
        assert result.brand_name is not None
        assert result.logo_prompt is not None
        assert isinstance(result.color_palette, list)
        assert len(result.color_palette) > 0
        assert all(color.startswith('#') for color in result.color_palette)
    
    @patch('departments.branding.branding_agent.AnthropicEngine')
    def test_run_with_ai_engine(self, mock_engine_class):
        """Test running the agent with AI engine"""
        # Mock AI engine response
        mock_response = Mock()
        mock_response.content = '''
        {
          "brand_name": "Inkspire",
          "logo_prompt": "Design a sleek logo for Inkspire",
          "color_palette": ["#1B263B", "#415A77", "#E0E1DD"]
        }
        '''
        
        mock_engine = Mock()
        mock_engine.generate.return_value = mock_response
        mock_engine_class.return_value = mock_engine
        
        # Create agent with mock config
        agent = BrandingAgent(config={'anthropic_api_key': 'test_key'})
        
        # Test state
        state = {
            "business_idea": "Premium pen brand",
            "product_type": "pens"
        }
        
        result = agent.run(state)
        
        # Verify AI engine was called
        mock_engine.generate.assert_called_once()
        
        # Verify result structure
        assert "brand_name" in result
        assert "logo_prompt" in result
        assert "color_palette" in result
        assert "domain_suggestions" in result
        assert "branding_generated_at" in result
    
    def test_run_without_ai_engine(self):
        """Test running the agent without AI engine (fallback mode)"""
        # Create agent without API key
        agent = BrandingAgent(config={})
        
        state = {
            "business_idea": "Premium pen brand",
            "product_type": "pens"
        }
        
        result = agent.run(state)
        
        # Should still return valid structure
        assert "brand_name" in result
        assert "logo_prompt" in result
        assert "color_palette" in result
        assert "domain_suggestions" in result
        assert "branding_generated_at" in result
    
    def test_run_with_invalid_state(self):
        """Test running with invalid/empty state"""
        state = {}
        
        result = self.agent.run(state)
        
        # Should return original state unchanged
        assert result == state
    
    def test_run_error_handling(self):
        """Test error handling during run"""
        # Create a state that will cause issues
        state = {
            "business_idea": "Test business",
            "product_type": "test"
        }
        
        # Mock the AI engine to raise an exception
        with patch.object(self.agent, '_generate_branding_assets', side_effect=Exception("Test error")):
            result = self.agent.run(state)
            
            # Should return original state on error
            assert result == state
    
    def test_branding_result_class(self):
        """Test BrandingResult class"""
        result = BrandingResult(
            brand_name="TestBrand",
            logo_prompt="Design a logo for TestBrand",
            color_palette=["#123456", "#789ABC"],
            domain_suggestions=["testbrand.com", "testbrand.co"]
        )
        
        assert result.brand_name == "TestBrand"
        assert result.logo_prompt == "Design a logo for TestBrand"
        assert result.color_palette == ["#123456", "#789ABC"]
        assert result.domain_suggestions == ["testbrand.com", "testbrand.co"]
    
    def test_branding_result_default_domains(self):
        """Test BrandingResult with default domain suggestions"""
        result = BrandingResult(
            brand_name="TestBrand",
            logo_prompt="Design a logo for TestBrand",
            color_palette=["#123456", "#789ABC"]
        )
        
        assert result.domain_suggestions == []


def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running BrandingAgent Basic Tests")
    print("=" * 50)
    
    # Initialize agent
    agent = BrandingAgent()
    print("✅ Agent initialized successfully")
    
    # Test 1: Basic business info extraction
    print("\n📊 Test 1: Business info extraction")
    state = {
        "business_idea": "Premium pen brand",
        "product_type": "pens"
    }
    business_info = agent._extract_business_info(state)
    print(f"✅ Extracted business info: {business_info}")
    
    # Test 2: Fallback branding generation
    print("\n🎨 Test 2: Fallback branding generation")
    result = agent._generate_fallback_branding(business_info)
    print(f"✅ Generated brand: {result.brand_name}")
    print(f"✅ Logo prompt: {result.logo_prompt}")
    print(f"✅ Colors: {result.color_palette}")
    
    # Test 3: Domain suggestions
    print("\n🌐 Test 3: Domain suggestions")
    domains = agent._generate_domain_suggestions("TestBrand")
    print(f"✅ Domain suggestions: {domains}")
    
    # Test 4: Full run test
    print("\n🚀 Test 4: Full run test")
    final_state = agent.run(state)
    print(f"✅ Final state keys: {list(final_state.keys())}")
    print(f"✅ Brand name: {final_state.get('brand_name')}")
    
    print("\n🎉 All basic tests passed!")


if __name__ == "__main__":
    run_basic_tests() 