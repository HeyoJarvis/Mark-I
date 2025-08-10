# Branding Department

The Branding Department provides AI-powered brand creation and visual identity generation for new business ventures.

## Overview

The `BrandingAgent` understands user intent about business ideas and generates:
- **Brand names** - Unique, memorable brand names
- **Logo design prompts** - Detailed prompts for logo designers
- **Color palettes** - Professional color schemes in hex format
- **Domain suggestions** - Available domain name options

## Quick Start

### Basic Usage

```python
from departments.branding.branding_agent import BrandingAgent

# Initialize the agent
agent = BrandingAgent()

# Define your business idea
state = {
    "business_idea": "I want to start a premium pen brand",
    "product_type": "pens",
    "target_audience": "professionals"
}

# Generate branding assets
result = agent.run(state)

# Access the results
print(f"Brand Name: {result['brand_name']}")
print(f"Logo Prompt: {result['logo_prompt']}")
print(f"Color Palette: {result['color_palette']}")
print(f"Domain Suggestions: {result['domain_suggestions']}")
```

### Example Output

```json
{
  "brand_name": "Inkspire",
  "logo_prompt": "Design a sleek, modern logo for a premium pen company called Inkspire.",
  "color_palette": ["#1B263B", "#415A77", "#E0E1DD"],
  "domain_suggestions": ["inkspire.com", "inkspire.co", "inkspire.ai"],
  "branding_generated_at": "2025-08-05T21:14:12.764317"
}
```

## Configuration

### AI Engine Setup

To use Claude for branding generation, set your Anthropic API key:

```python
# Option 1: Environment variable
export ANTHROPIC_API_KEY='your-api-key-here'

# Option 2: Config parameter
agent = BrandingAgent(config={'anthropic_api_key': 'your-api-key-here'})
```

### Configuration Options

```python
config = {
    'anthropic_api_key': 'your-api-key',  # Claude API key
    'max_domain_suggestions': 5,          # Max domain suggestions
    'color_palette_size': 4               # Number of colors in palette
}

agent = BrandingAgent(config=config)
```

## Input State Format

The agent accepts various field names for business information:

### Required Fields
- `business_idea` - Description of the business concept
- `description` - Alternative to business_idea
- `idea` - Alternative to business_idea

### Optional Fields
- `product_type` - Type of product/service
- `business_name` - Existing business name (if any)
- `target_audience` - Target customer segment
- `industry` - Business industry/niche
- `niche` - Alternative to industry

### Example Input States

```python
# Minimal state
state = {"business_idea": "Premium coffee subscription"}

# Complete state
state = {
    "business_idea": "Launching a luxury coffee subscription service",
    "product_type": "coffee subscription",
    "target_audience": "coffee enthusiasts",
    "industry": "food and beverage",
    "business_name": "BrewMaster"  # Optional existing name
}
```

## Features

### 1. Intelligent Brand Name Generation
- Creates unique, memorable brand names
- Avoids generic or overused terms
- Considers business context and target audience
- Ensures trademark potential

### 2. Professional Logo Prompts
- Generates detailed design prompts
- Suitable for DALL·E, Midjourney, or human designers
- Includes style, mood, and color guidance
- Specifies key design elements

### 3. Color Palette Generation
- Creates harmonious color schemes
- Industry-appropriate colors
- Professional hex format
- Primary, secondary, and accent colors

### 4. Domain Suggestions
- Generates available domain options
- Multiple TLD suggestions (.com, .co, .ai, .io, .net)
- Cleans special characters
- Provides variations and alternatives

### 5. Fallback Mode
- Works without AI engine
- Generates basic branding assets
- Ensures reliability and availability
- No external dependencies required

## Error Handling

The agent gracefully handles various error conditions:

- **Missing business information** - Returns original state unchanged
- **AI engine unavailable** - Falls back to basic branding generation
- **Invalid API responses** - Uses fallback mode
- **Network issues** - Continues with local processing

## Testing

Run the test suite:

```bash
# Run all branding tests
python -m pytest tests/test_branding_agent.py -v

# Run basic functionality test
python tests/test_branding_agent.py

# Run demo
python demo_branding_agent.py
```

## Integration with HeyJarvis

The BrandingAgent follows the standard HeyJarvis agent contract:

```python
def run(self, state: dict) -> dict:
    """
    Main entry point - follows HeyJarvis agent contract
    
    Args:
        state: Input state with business information
        
    Returns:
        Updated state with branding assets
    """
```

### LangGraph Integration

The agent can be integrated into LangGraph workflows:

```python
from langgraph.graph import StateGraph
from departments.branding.branding_agent import BrandingAgent

# Create workflow
workflow = StateGraph()

# Add branding node
branding_agent = BrandingAgent()
workflow.add_node("branding", branding_agent.run)

# Connect to other nodes
workflow.add_edge("branding", "next_step")
```

## Examples

### Premium Pen Brand
```python
state = {
    "business_idea": "I want to start a premium pen brand that focuses on luxury writing instruments for professionals and collectors.",
    "product_type": "pens",
    "target_audience": "professionals and collectors",
    "industry": "luxury goods"
}
```

### Eco-Friendly Water Bottles
```python
state = {
    "business_idea": "Creating sustainable, reusable water bottles made from recycled materials to reduce plastic waste.",
    "product_type": "water bottles",
    "target_audience": "environmentally conscious consumers",
    "industry": "sustainability"
}
```

### AI-Powered Fitness App
```python
state = {
    "business_idea": "Developing a mobile app that uses AI to create personalized workout plans and track fitness progress.",
    "product_type": "mobile app",
    "target_audience": "fitness enthusiasts",
    "industry": "health and technology"
}
```

## Architecture

### File Structure
```
departments/branding/
├── __init__.py              # Module exports
├── branding_agent.py        # Main agent implementation
└── README.md               # This documentation

utils/
├── __init__.py             # Utility exports
└── domain_utils.py         # Domain checking utilities

tests/
└── test_branding_agent.py  # Comprehensive test suite
```

### Dependencies
- `ai_engines.anthropic_engine` - Claude AI integration
- `ai_engines.base_engine` - AI engine infrastructure
- Standard Python libraries (json, logging, re, datetime)

## Contributing

To extend the BrandingAgent:

1. **Add new branding features** - Extend the `_generate_branding_assets` method
2. **Improve AI prompts** - Modify `_create_branding_prompt`
3. **Add domain checking** - Integrate with `utils/domain_utils.py`
4. **Enhance fallback mode** - Improve `_generate_fallback_branding`

## License

Part of the HeyJarvis AI Agent System - see main project license. 