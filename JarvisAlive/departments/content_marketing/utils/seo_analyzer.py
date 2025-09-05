"""SEO analysis and optimization utilities."""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine
from ..models.content_models import Content, SEOAnalysis

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """AI-powered SEO analysis and optimization tool."""
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        if not self.ai_engine:
            self.logger.warning("No AI engine provided - using basic SEO analysis")
    
    async def analyze_content_seo(self, content: Content) -> SEOAnalysis:
        """Perform comprehensive SEO analysis of content."""
        
        if not self.ai_engine:
            return self._basic_seo_analysis(content)
        
        try:
            # Use AI for sophisticated SEO analysis
            analysis = await self._ai_seo_analysis(content)
            return analysis
            
        except Exception as e:
            self.logger.error(f"AI SEO analysis failed: {e}")
            return self._basic_seo_analysis(content)
    
    async def _ai_seo_analysis(self, content: Content) -> SEOAnalysis:
        """Use AI to perform comprehensive SEO analysis."""
        
        prompt = f"""
Perform a comprehensive SEO analysis of this content:

Title: {content.title}
Meta Description: {content.meta_description}
Focus Keyword: {content.focus_keyword}
Target Keywords: {content.target_keywords}
Content Length: {len(content.content_body)} characters
Content Preview: {content.content_body[:500]}...

Analyze and provide SEO recommendations in JSON format:
{{
    "keyword_density": 2.5,
    "keyword_placement_score": 0.8,
    "title_tag_optimized": true,
    "meta_description_optimized": false,
    "header_structure_score": 0.7,
    "readability_score": 0.85,
    "content_uniqueness": 0.9,
    "ranking_potential": 0.75,
    "traffic_potential": 1500,
    "overall_seo_score": 0.78,
    "seo_recommendations": [
        "Optimize meta description length (currently too long)",
        "Add more H2 subheadings for better structure",
        "Include focus keyword in first paragraph"
    ],
    "content_improvements": [
        "Add more internal links to related content",
        "Include relevant statistics or data",
        "Add call-to-action at the end"
    ]
}}

Provide detailed, actionable SEO recommendations.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            analysis_data = json.loads(response_text)
            
            return SEOAnalysis(
                content_id=content.content_id,
                primary_keyword=content.focus_keyword,
                keyword_density=analysis_data.get('keyword_density', 0.0),
                keyword_placement_score=analysis_data.get('keyword_placement_score', 0.0),
                related_keywords_found=self._extract_related_keywords(content),
                title_tag_optimized=analysis_data.get('title_tag_optimized', False),
                meta_description_optimized=analysis_data.get('meta_description_optimized', False),
                header_structure_score=analysis_data.get('header_structure_score', 0.0),
                internal_links_count=self._count_internal_links(content.content_body),
                external_links_count=self._count_external_links(content.content_body),
                readability_score=analysis_data.get('readability_score', 0.0),
                content_length=len(content.content_body),
                content_uniqueness=analysis_data.get('content_uniqueness', 0.0),
                ranking_potential=analysis_data.get('ranking_potential', 0.0),
                traffic_potential=analysis_data.get('traffic_potential', 0),
                seo_recommendations=analysis_data.get('seo_recommendations', []),
                content_improvements=analysis_data.get('content_improvements', []),
                overall_seo_score=analysis_data.get('overall_seo_score', 0.0)
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI SEO response: {e}")
            return self._basic_seo_analysis(content)
        except Exception as e:
            self.logger.error(f"AI SEO analysis error: {e}")
            return self._basic_seo_analysis(content)
    
    def _basic_seo_analysis(self, content: Content) -> SEOAnalysis:
        """Basic SEO analysis without AI."""
        
        # Calculate keyword density
        keyword_density = self._calculate_keyword_density(content.content_body, content.focus_keyword)
        
        # Check title optimization
        title_optimized = (
            content.focus_keyword.lower() in content.title.lower() and
            len(content.title) >= 30 and len(content.title) <= 60
        )
        
        # Check meta description optimization
        meta_optimized = (
            content.meta_description and
            len(content.meta_description) >= 120 and len(content.meta_description) <= 160 and
            content.focus_keyword.lower() in content.meta_description.lower()
        )
        
        # Basic readability (simple metric)
        readability = self._calculate_basic_readability(content.content_body)
        
        # Count links
        internal_links = self._count_internal_links(content.content_body)
        external_links = self._count_external_links(content.content_body)
        
        # Calculate overall score
        scores = [
            keyword_density / 5.0,  # Target 2-3% keyword density
            1.0 if title_optimized else 0.0,
            1.0 if meta_optimized else 0.0,
            readability,
            min(1.0, internal_links / 3.0),  # Target 3+ internal links
            min(1.0, external_links / 2.0)   # Target 2+ external links
        ]
        overall_score = sum(scores) / len(scores)
        
        return SEOAnalysis(
            content_id=content.content_id,
            primary_keyword=content.focus_keyword,
            keyword_density=keyword_density,
            keyword_placement_score=0.8 if content.focus_keyword.lower() in content.content_body[:200].lower() else 0.3,
            related_keywords_found=self._extract_related_keywords(content),
            title_tag_optimized=title_optimized,
            meta_description_optimized=meta_optimized,
            header_structure_score=self._analyze_header_structure(content.content_body),
            internal_links_count=internal_links,
            external_links_count=external_links,
            readability_score=readability,
            content_length=len(content.content_body),
            content_uniqueness=0.8,  # Assume unique for basic analysis
            ranking_potential=overall_score,
            traffic_potential=int(overall_score * 1000),  # Estimate based on score
            seo_recommendations=self._generate_basic_seo_recommendations(content),
            content_improvements=self._generate_content_improvements(content),
            overall_seo_score=overall_score
        )
    
    def _calculate_keyword_density(self, content: str, keyword: str) -> float:
        """Calculate keyword density percentage."""
        if not content or not keyword:
            return 0.0
        
        content_words = content.lower().split()
        keyword_words = keyword.lower().split()
        
        if len(keyword_words) == 1:
            # Single word keyword
            keyword_count = content_words.count(keyword.lower())
        else:
            # Multi-word keyword
            keyword_count = content.lower().count(keyword.lower())
        
        total_words = len(content_words)
        
        return (keyword_count / total_words * 100) if total_words > 0 else 0.0
    
    def _calculate_basic_readability(self, content: str) -> float:
        """Basic readability score (simplified Flesch Reading Ease)."""
        if not content:
            return 0.0
        
        # Count sentences (approximate)
        sentences = len([s for s in content.split('.') if s.strip()])
        
        # Count words
        words = len(content.split())
        
        # Count syllables (approximate)
        syllables = sum(self._count_syllables(word) for word in content.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch Reading Ease formula
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Convert to 0-1 scale
        return max(0.0, min(1.0, flesch_score / 100))
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count for a word."""
        word = word.lower().strip('.,!?;:"')
        if not word:
            return 0
        
        # Simple vowel counting method
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        # Every word has at least 1 syllable
        return max(1, syllable_count)
    
    def _count_internal_links(self, content: str) -> int:
        """Count internal links in content."""
        # Look for markdown links or HTML links that might be internal
        internal_patterns = [
            r'\[.*?\]\(/.*?\)',  # Markdown internal links
            r'<a.*?href=["\']\/.*?["\'].*?>',  # HTML internal links
            r'href=["\']\/.*?["\']'  # Direct href attributes
        ]
        
        count = 0
        for pattern in internal_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count
    
    def _count_external_links(self, content: str) -> int:
        """Count external links in content."""
        # Look for links starting with http/https
        external_patterns = [
            r'\[.*?\]\(https?://.*?\)',  # Markdown external links
            r'<a.*?href=["\']https?://.*?["\'].*?>',  # HTML external links
            r'href=["\']https?://.*?["\']'  # Direct href attributes
        ]
        
        count = 0
        for pattern in external_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count
    
    def _analyze_header_structure(self, content: str) -> float:
        """Analyze header structure quality."""
        
        # Count headers (markdown and HTML)
        h1_count = len(re.findall(r'^#\s+.*$|<h1.*?>.*?</h1>', content, re.MULTILINE | re.IGNORECASE))
        h2_count = len(re.findall(r'^##\s+.*$|<h2.*?>.*?</h2>', content, re.MULTILINE | re.IGNORECASE))
        h3_count = len(re.findall(r'^###\s+.*$|<h3.*?>.*?</h3>', content, re.MULTILINE | re.IGNORECASE))
        
        # Good structure: 1 H1, multiple H2s, some H3s
        score = 0.0
        
        if h1_count == 1:
            score += 0.4  # Perfect H1 usage
        elif h1_count == 0:
            score += 0.1  # Missing H1
        else:
            score += 0.2  # Multiple H1s (not ideal)
        
        if h2_count >= 2:
            score += 0.4  # Good H2 usage
        elif h2_count == 1:
            score += 0.2
        
        if h3_count > 0:
            score += 0.2  # Some H3 usage
        
        return min(1.0, score)
    
    def _extract_related_keywords(self, content: Content) -> List[str]:
        """Extract related keywords from content."""
        
        # Simple approach: extract important words from content
        content_words = content.content_body.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        
        # Count word frequency
        word_counts = {}
        for word in content_words:
            word = re.sub(r'[^\w]', '', word)  # Remove punctuation
            if len(word) > 3 and word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return most frequent words as related keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count > 1]
    
    def _generate_basic_seo_recommendations(self, content: Content) -> List[str]:
        """Generate basic SEO recommendations."""
        
        recommendations = []
        
        # Title optimization
        if not content.focus_keyword.lower() in content.title.lower():
            recommendations.append(f"Include focus keyword '{content.focus_keyword}' in title")
        
        if len(content.title) < 30:
            recommendations.append("Title is too short - aim for 30-60 characters")
        elif len(content.title) > 60:
            recommendations.append("Title is too long - aim for 30-60 characters")
        
        # Meta description optimization
        if not content.meta_description:
            recommendations.append("Add meta description for better search snippets")
        elif len(content.meta_description) < 120:
            recommendations.append("Meta description is too short - aim for 120-160 characters")
        elif len(content.meta_description) > 160:
            recommendations.append("Meta description is too long - aim for 120-160 characters")
        
        # Content length
        if len(content.content_body) < 300:
            recommendations.append("Content is too short - aim for at least 300 words for better rankings")
        
        # Keyword density
        keyword_density = self._calculate_keyword_density(content.content_body, content.focus_keyword)
        if keyword_density < 1.0:
            recommendations.append(f"Increase keyword density for '{content.focus_keyword}' (currently {keyword_density:.1f}%)")
        elif keyword_density > 5.0:
            recommendations.append(f"Reduce keyword density for '{content.focus_keyword}' (currently {keyword_density:.1f}% - too high)")
        
        # Links
        internal_links = self._count_internal_links(content.content_body)
        external_links = self._count_external_links(content.content_body)
        
        if internal_links < 2:
            recommendations.append("Add more internal links to related content")
        
        if external_links < 1:
            recommendations.append("Add authoritative external links to support claims")
        
        return recommendations
    
    def _generate_content_improvements(self, content: Content) -> List[str]:
        """Generate content quality improvements."""
        
        improvements = []
        
        # Content structure
        if not self._has_introduction(content.content_body):
            improvements.append("Add clear introduction paragraph")
        
        if not self._has_conclusion(content.content_body):
            improvements.append("Add conclusion or summary section")
        
        # Engagement elements
        if 'call-to-action' not in content.content_body.lower() and 'cta' not in content.content_body.lower():
            improvements.append("Add call-to-action to drive conversions")
        
        # Visual elements
        if 'image' not in content.content_body.lower() and 'img' not in content.content_body.lower():
            improvements.append("Consider adding relevant images or visuals")
        
        # Content depth
        if len(content.content_body.split()) < 500:
            improvements.append("Expand content depth for better authority and rankings")
        
        return improvements
    
    def _has_introduction(self, content: str) -> bool:
        """Check if content has a clear introduction."""
        first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content[:200]
        intro_indicators = ['introduction', 'overview', 'in this', 'this article', 'this post', 'we will']
        return any(indicator in first_paragraph.lower() for indicator in intro_indicators)
    
    def _has_conclusion(self, content: str) -> bool:
        """Check if content has a conclusion."""
        last_paragraph = content.split('\n\n')[-1] if '\n\n' in content else content[-200:]
        conclusion_indicators = ['conclusion', 'summary', 'in summary', 'to conclude', 'final thoughts']
        return any(indicator in last_paragraph.lower() for indicator in conclusion_indicators)
    
    async def optimize_content_for_seo(self, content: Content) -> Content:
        """Optimize content based on SEO analysis."""
        
        # Perform SEO analysis
        seo_analysis = await self.analyze_content_seo(content)
        
        # Apply optimizations (basic version)
        optimized_content = content
        
        # Update SEO score
        optimized_content.seo_score = seo_analysis.overall_seo_score
        optimized_content.keyword_density = seo_analysis.keyword_density
        optimized_content.readability_score = seo_analysis.readability_score
        
        self.logger.info(f"Content SEO optimized - score: {seo_analysis.overall_seo_score:.2f}")
        
        return optimized_content
    
    async def analyze_competitor_content(self, keywords: List[str], max_competitors: int = 5) -> List[Dict[str, Any]]:
        """Analyze competitor content for the given keywords."""
        
        # This would integrate with SEMrush/Ahrefs APIs in a full implementation
        # For now, return mock competitor analysis
        
        competitors = []
        
        for i, keyword in enumerate(keywords[:max_competitors]):
            competitor = {
                "keyword": keyword,
                "top_ranking_url": f"https://competitor{i+1}.com/blog/{keyword.lower().replace(' ', '-')}",
                "estimated_traffic": (i + 1) * 1000,
                "content_length": (i + 1) * 800 + 1200,
                "backlinks": (i + 1) * 50 + 100,
                "content_gap_opportunity": f"Create comprehensive guide on {keyword} with practical examples"
            }
            competitors.append(competitor)
        
        self.logger.info(f"Analyzed {len(competitors)} competitor content pieces")
        return competitors
    
    def generate_seo_content_ideas(self, target_keywords: List[str], content_type: str = "blog_post") -> List[Dict[str, Any]]:
        """Generate SEO-optimized content ideas."""
        
        content_ideas = []
        
        for keyword in target_keywords:
            idea = {
                "title": f"The Complete Guide to {keyword.title()}",
                "focus_keyword": keyword,
                "content_type": content_type,
                "target_audience": "business professionals",
                "content_angle": f"Comprehensive guide covering all aspects of {keyword}",
                "estimated_word_count": 1500,
                "seo_potential": 0.7,
                "competition_level": "medium"
            }
            content_ideas.append(idea)
        
        return content_ideas
