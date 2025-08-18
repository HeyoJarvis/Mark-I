# Website Generation Department

This department provides AI-powered website structure, content, and design generation for businesses based on their branding and business requirements.

## Features

- **Website Architecture**: Generates comprehensive sitemaps and page structures
- **Content Generation**: Creates conversion-focused copy and content sections
- **SEO Optimization**: Provides SEO recommendations and meta content
- **Style Guide Creation**: Develops design guidelines based on brand context
- **Industry Customization**: Tailors content and structure to specific business types
- **Conversion Optimization**: Focuses on user experience and conversion goals

## Agent: WebsiteGeneratorAgent

### Inputs
- `brand_name` (optional): Business/brand name
- `business_idea` (required): Description of the business
- `color_palette` (optional): Array of brand colors in hex format
- `target_audience` (optional): Description of target customers
- `industry` (optional): Business industry/sector
- `pages` (optional): Array of specific page names requested
- `website_type` (optional): Type of website (business, ecommerce, etc.)

### Outputs
- `sitemap`: Array of page names for the website
- `website_structure`: Detailed page structures with sections and content
- `homepage`: Complete homepage content with SEO and copy
- `style_guide`: Branding and design guidelines
- `seo_recommendations`: SEO strategy and technical recommendations

## Usage Examples

### Through Universal Orchestrator
```python
# Website requests are automatically routed through the branding orchestrator
query = "Create a landing page for my eco-friendly water bottle brand"
response = await universal_orchestrator.process_query(query)
```

### Direct Agent Invocation
```python
from departments.website.website_generator_agent import WebsiteGeneratorAgent

agent = WebsiteGeneratorAgent()
result = await agent.run({
    "brand_name": "EcoBottle",
    "business_idea": "Sustainable water bottles made from recycled materials",
    "color_palette": ["#2D5A27", "#4A7C59", "#8FBC8F"],
    "target_audience": "environmentally conscious consumers",
    "industry": "sustainability"
})
```

## Integration

The Website Generator Agent is:
- Registered in the agent integration system
- Mapped to the "branding" intent category
- Routed through the branding orchestrator
- Compatible with branding agent outputs for enhanced context

## Output Structure

### Sitemap
```json
["Home", "About", "Products", "Pricing", "Contact"]
```

### Website Structure
```json
[
  {
    "page": "Home",
    "purpose": "Convert visitors into leads/customers",
    "sections": [
      {
        "id": "hero",
        "type": "hero_section",
        "headline": "Main value proposition",
        "subheadline": "Supporting description",
        "primary_cta": "Get Started",
        "secondary_cta": "Learn More"
      }
    ]
  }
]
```

### Homepage Details
```json
{
  "seo_title": "Brand Name - Professional Services",
  "meta_description": "SEO-optimized description",
  "hero": {
    "headline": "Primary value proposition",
    "subheadline": "Supporting explanation",
    "primary_cta": "Get Started",
    "secondary_cta": "Learn More"
  },
  "value_propositions": ["Benefit 1", "Benefit 2", "Benefit 3"],
  "features": [
    {
      "title": "Feature Name",
      "description": "Feature description",
      "benefit": "Customer benefit"
    }
  ]
}
```

### Style Guide
```json
{
  "brand_name": "Brand Name",
  "colors": ["#1F2937", "#3B82F6"],
  "typography": {
    "primary_font": "Inter",
    "secondary_font": "Inter"
  },
  "tone_of_voice": {
    "personality": "professional",
    "writing_style": "Clear and trustworthy"
  }
}
```

## Coordination

This agent works seamlessly with:
- **BrandingAgent**: Uses brand context for consistent website design
- **MarketResearchAgent**: Can incorporate market insights into content strategy
- **Intelligence Layer**: Supports multi-step workflow orchestration 