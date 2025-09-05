"""
Context-Aware Response Generator - Creates responses that reference specific previous work
"""

import json
import logging
from typing import Dict, Any, List
from ai_engines.anthropic_engine import AnthropicEngine

logger = logging.getLogger(__name__)


class ContextAwareResponseGenerator:
    """Generates responses that intelligently reference previous work."""
    
    def __init__(self, ai_engine: AnthropicEngine):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
    
    async def generate_contextual_response(
        self, 
        user_message: str,
        context_data: Dict[str, Any],
        cross_agent_synthesis: bool = False
    ) -> str:
        """Generate response using retrieved context."""
        
        if cross_agent_synthesis:
            return await self._generate_cross_agent_response(user_message, context_data)
        else:
            # Single agent context response
            primary_context_type = list(context_data.keys())[0]
            return await self._generate_single_agent_response(
                user_message, 
                context_data[primary_context_type], 
                primary_context_type
            )
    
    async def _generate_single_agent_response(self, message: str, context: Dict[str, Any], context_type: str) -> str:
        """Generate response using single agent context."""
        
        if context_type == "lead_mining":
            return await self._respond_to_lead_analysis_request(message, context)
        elif context_type == "branding":
            return await self._respond_to_branding_reference(message, context)
        elif context_type == "market_research":
            return await self._respond_to_research_reference(message, context)
        elif context_type == "website":
            return await self._respond_to_website_reference(message, context)
        elif context_type == "content_marketing":
            return await self._respond_to_content_reference(message, context)
        elif context_type == "social_intelligence":
            return await self._respond_to_social_reference(message, context)
        
        return f"I found your previous {context_type.replace('_', ' ')} work, but I'm not sure how to help with that specific request."
    
    async def _respond_to_lead_analysis_request(self, message: str, lead_context: Dict[str, Any]) -> str:
        """Respond to requests about previously found leads."""
        
        qualified_leads = lead_context.get("qualified_leads", [])
        
        if not qualified_leads:
            lead_count = lead_context.get("lead_count", 0)
            if lead_count == 0:
                return "I don't see any qualified leads from your recent search. Would you like me to run a new lead search?"
            else:
                return f"I found {lead_count} leads in your recent search, but they didn't meet the qualification criteria. Would you like me to show you the raw results or adjust the search parameters?"
        
        # Use AI to analyze the specific leads
        prompt = f"""
        The user asked: "{message}"
        
        I previously found these leads for them:
        Lead Summary: {lead_context.get('lead_count', 0)} qualified leads
        Top Companies: {lead_context.get('top_companies', [])}
        Top Titles: {lead_context.get('top_titles', [])}
        
        Detailed leads (first 5):
        {json.dumps(qualified_leads[:5], indent=2)}
        
        Provide a helpful analysis that:
        1. References specific leads by name and company
        2. Explains why each lead is promising or not for outreach
        3. Prioritizes them based on title, company, and industry fit
        4. Suggests specific next steps or outreach strategies
        5. Be conversational and reference the actual lead data
        
        Focus on actionable insights for sales outreach.
        """
        
        try:
            response = await self.ai_engine.generate(prompt)
            return response.content
        except Exception as e:
            # Fallback to structured summary
            lead_names = [f"{lead.get('first_name', '')} {lead.get('last_name', '')}" for lead in qualified_leads[:3]]
            companies = [lead.get('company_name', '') for lead in qualified_leads[:3]]
            
            return f"Based on the {len(qualified_leads)} leads I found earlier:\n\n" + \
                   f"**Top Prospects:** {', '.join(lead_names[:3])}\n" + \
                   f"**Companies:** {', '.join(companies[:3])}\n\n" + \
                   f"These leads have confidence scores ranging from 0.6-0.8. " + \
                   f"I can provide more detailed analysis - what specific aspect would you like me to focus on?"
    
    async def _respond_to_branding_reference(self, message: str, branding_context: Dict[str, Any]) -> str:
        """Respond to requests about previous branding work."""
        
        brand_name = branding_context.get("brand_name")
        colors = branding_context.get("color_palette", [])
        
        if not brand_name and not colors:
            return "I don't see complete branding work from your recent session. What specific branding element are you referring to?"
        
        prompt = f"""
        The user asked: "{message}"
        
        Previous branding work:
        - Brand Name: {brand_name}
        - Color Palette: {colors}
        - Logo Prompt: {branding_context.get('logo_prompt', 'N/A')}
        - Domain Suggestions: {branding_context.get('domain_suggestions', [])}
        
        Provide a helpful response that references this specific branding work and addresses their request.
        """
        
        try:
            response = await self.ai_engine.generate(prompt)
            return response.content
        except Exception as e:
            return f"From your recent branding work: Brand '{brand_name}' with colors {colors}. How can I help you with this?"
    
    async def _respond_to_research_reference(self, message: str, research_context: Dict[str, Any]) -> str:
        """Respond to requests about previous market research."""
        
        opportunity_score = research_context.get("opportunity_score")
        key_findings = research_context.get("key_findings", [])
        
        if not opportunity_score and not key_findings:
            return "I don't see complete market research from your recent session. What specific research data are you referring to?"
        
        prompt = f"""
        The user asked: "{message}"
        
        Previous market research:
        - Market Opportunity Score: {opportunity_score}
        - Key Findings: {key_findings[:5]}
        - Market Analysis: {research_context.get('market_analysis', 'N/A')[:300]}
        
        Provide a helpful response that references this specific research and addresses their request.
        """
        
        try:
            response = await self.ai_engine.generate(prompt)
            return response.content
        except Exception as e:
            return f"From your recent market research: Opportunity score {opportunity_score}/100. Key findings: {', '.join(key_findings[:3])}. How can I help you with this data?"
    
    async def _respond_to_website_reference(self, message: str, website_context: Dict[str, Any]) -> str:
        """Respond to requests about previous website work."""
        
        sitemap = website_context.get("sitemap", [])
        homepage = website_context.get("homepage", {})
        
        return f"From your recent website work: {len(sitemap)} pages created including homepage. How can I help you with the website?"
    
    async def _respond_to_content_reference(self, message: str, content_context: Dict[str, Any]) -> str:
        """Respond to requests about previous content marketing work."""
        
        content_calendar = content_context.get("content_calendar", {})
        content_gaps = content_context.get("content_gaps", [])
        
        return f"From your recent content strategy: {len(content_gaps)} content opportunities identified. How can I help you with the content plan?"
    
    async def _respond_to_social_reference(self, message: str, social_context: Dict[str, Any]) -> str:
        """Respond to requests about previous social intelligence work."""
        
        mentions = social_context.get("mentions", [])
        sentiment = social_context.get("sentiment", {})
        
        return f"From your recent social monitoring: {len(mentions)} mentions found. How can I help you with the social data?"
    
    async def _generate_cross_agent_response(self, message: str, context_data: Dict[str, Any]) -> str:
        """Generate response that synthesizes across multiple agent outputs."""
        
        context_summary = self._build_context_summary(context_data)
        
        prompt = f"""
        User request: "{message}"
        
        Previous work context:
        {context_summary}
        
        Generate a helpful response that:
        1. References specific previous work by name/details
        2. Connects insights across different agent outputs  
        3. Provides actionable recommendations
        4. Maintains conversational tone
        5. Shows understanding of the full context
        
        Example good response:
        "Based on the 25 leads I found earlier (Jacob Abrian from Arab Fashion Council, 
        Kumar Rajagopalan from RAI, etc.), and considering the market research showing 
        growth in sustainable fashion, I recommend prioritizing Jacob because his luxury 
        fashion focus aligns with the premium brand positioning from your branding work."
        """
        
        try:
            response = await self.ai_engine.generate(prompt)
            return response.content
        except Exception as e:
            return f"I found relevant previous work across {len(context_data)} areas, but had trouble analyzing it. Could you be more specific about what you'd like me to focus on?"
    
    def _build_context_summary(self, context_data: Dict[str, Any]) -> str:
        """Build formatted summary of all available context."""
        
        summary_parts = []
        
        if "lead_mining" in context_data:
            lead_ctx = context_data["lead_mining"]
            leads = lead_ctx.get("qualified_leads", [])
            summary_parts.append(f"RECENT LEADS ({len(leads)} found):")
            for lead in leads[:5]:
                name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                company = lead.get('company_name', '')
                title = lead.get('job_title', '')
                if name and company:
                    summary_parts.append(f"  - {name}: {title} at {company}")
        
        if "market_research" in context_data:
            research = context_data["market_research"]
            summary_parts.append(f"MARKET RESEARCH:")
            summary_parts.append(f"  - Opportunity Score: {research.get('opportunity_score', 'N/A')}")
            if research.get('key_findings'):
                summary_parts.append(f"  - Key Findings: {research['key_findings'][:3]}")
        
        if "branding" in context_data:
            branding = context_data["branding"]
            summary_parts.append(f"BRAND IDENTITY:")
            if branding.get('brand_name'):
                summary_parts.append(f"  - Brand Name: {branding['brand_name']}")
            if branding.get('color_palette'):
                summary_parts.append(f"  - Colors: {branding['color_palette']}")
        
        if "website" in context_data:
            website = context_data["website"]
            summary_parts.append(f"WEBSITE:")
            if website.get('sitemap'):
                summary_parts.append(f"  - Pages: {len(website['sitemap'])} pages")
            if website.get('homepage'):
                summary_parts.append(f"  - Homepage: Created")
        
        if "content_marketing" in context_data:
            content = context_data["content_marketing"]
            summary_parts.append(f"CONTENT STRATEGY:")
            if content.get('content_gaps'):
                summary_parts.append(f"  - Content Opportunities: {len(content['content_gaps'])}")
        
        if "social_intelligence" in context_data:
            social = context_data["social_intelligence"]
            summary_parts.append(f"SOCIAL MONITORING:")
            if social.get('mentions'):
                summary_parts.append(f"  - Mentions: {len(social['mentions'])}")
            if social.get('sentiment'):
                summary_parts.append(f"  - Sentiment: {social['sentiment']}")
        
        return "\n".join(summary_parts)
