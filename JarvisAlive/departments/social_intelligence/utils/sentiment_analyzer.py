"""AI-powered sentiment analysis for social mentions."""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig
from ..models.social_models import SocialMention, Sentiment, SentimentSummary

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """AI-powered sentiment analyzer using Anthropic Claude."""
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        
        if not self.ai_engine:
            self.logger.warning("No AI engine provided - using basic sentiment analysis")
    
    async def analyze_mention_sentiment(self, mention: SocialMention) -> SocialMention:
        """Analyze sentiment for a single social mention."""
        
        if not self.ai_engine:
            # Fallback to basic keyword-based sentiment
            mention.sentiment, mention.sentiment_score = self._basic_sentiment_analysis(mention.content)
            return mention
        
        try:
            # Use AI for sophisticated sentiment analysis
            sentiment, score = await self._ai_sentiment_analysis(mention.content, mention.title)
            
            mention.sentiment = sentiment
            mention.sentiment_score = score
            
            return mention
            
        except Exception as e:
            self.logger.error(f"AI sentiment analysis failed: {e}")
            # Fallback to basic analysis
            mention.sentiment, mention.sentiment_score = self._basic_sentiment_analysis(mention.content)
            return mention
    
    async def analyze_batch_sentiment(self, mentions: List[SocialMention]) -> List[SocialMention]:
        """Analyze sentiment for multiple mentions efficiently."""
        
        if not mentions:
            return mentions
        
        if not self.ai_engine:
            # Use basic analysis for all mentions
            for mention in mentions:
                mention.sentiment, mention.sentiment_score = self._basic_sentiment_analysis(mention.content)
            return mentions
        
        try:
            # Batch process for efficiency
            batch_size = 10  # Process in batches to avoid token limits
            
            for i in range(0, len(mentions), batch_size):
                batch = mentions[i:i + batch_size]
                await self._process_sentiment_batch(batch)
            
            return mentions
            
        except Exception as e:
            self.logger.error(f"Batch sentiment analysis failed: {e}")
            # Fallback to basic analysis
            for mention in mentions:
                mention.sentiment, mention.sentiment_score = self._basic_sentiment_analysis(mention.content)
            return mentions
    
    async def _ai_sentiment_analysis(self, content: str, title: str = "") -> Tuple[Sentiment, float]:
        """Perform AI-powered sentiment analysis."""
        
        prompt = f"""
Analyze the sentiment of this social media content. Consider both the title and content.

Title: {title}
Content: {content}

Provide sentiment analysis in the following JSON format:
{{
    "sentiment": "positive|negative|neutral|mixed",
    "confidence": 0.85,
    "sentiment_score": 0.3,
    "reasoning": "Brief explanation of the sentiment classification"
}}

Guidelines:
- sentiment_score: -1.0 (very negative) to +1.0 (very positive), 0.0 is neutral
- confidence: 0.0 to 1.0 indicating how confident you are in the analysis
- Consider context, tone, and implied meaning
- Look for pain points, complaints, praise, or neutral information sharing
- Mixed sentiment should be used when content has both positive and negative elements

Return only the JSON response.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Parse JSON response
            analysis = json.loads(response_text)
            
            sentiment_str = analysis.get('sentiment', 'neutral').lower()
            sentiment_score = float(analysis.get('sentiment_score', 0.0))
            
            # Convert string to Sentiment enum
            sentiment_map = {
                'positive': Sentiment.POSITIVE,
                'negative': Sentiment.NEGATIVE,
                'neutral': Sentiment.NEUTRAL,
                'mixed': Sentiment.MIXED
            }
            
            sentiment = sentiment_map.get(sentiment_str, Sentiment.NEUTRAL)
            
            return sentiment, sentiment_score
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI sentiment response: {e}")
            return self._basic_sentiment_analysis(content)
        except Exception as e:
            self.logger.error(f"AI sentiment analysis error: {e}")
            return self._basic_sentiment_analysis(content)
    
    async def _process_sentiment_batch(self, batch: List[SocialMention]):
        """Process a batch of mentions for sentiment analysis."""
        
        # Prepare batch content for analysis
        batch_content = []
        for i, mention in enumerate(batch):
            batch_content.append({
                "index": i,
                "title": mention.title,
                "content": mention.content[:500]  # Limit content length
            })
        
        prompt = f"""
Analyze the sentiment for each of these social media posts. Return a JSON array with sentiment analysis for each post.

Posts to analyze:
{json.dumps(batch_content, indent=2)}

For each post, provide:
{{
    "index": 0,
    "sentiment": "positive|negative|neutral|mixed",
    "sentiment_score": 0.3,
    "reasoning": "Brief explanation"
}}

Guidelines:
- sentiment_score: -1.0 (very negative) to +1.0 (very positive)
- Look for pain points, complaints, praise, or neutral information
- Consider context and tone

Return a JSON array with analysis for each post by index.
"""
        
        try:
            response = await self.ai_engine.generate(prompt)
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            analyses = json.loads(response_text)
            
            # Apply results to mentions
            for analysis in analyses:
                index = analysis.get('index', 0)
                if 0 <= index < len(batch):
                    mention = batch[index]
                    
                    sentiment_str = analysis.get('sentiment', 'neutral').lower()
                    sentiment_score = float(analysis.get('sentiment_score', 0.0))
                    
                    sentiment_map = {
                        'positive': Sentiment.POSITIVE,
                        'negative': Sentiment.NEGATIVE,
                        'neutral': Sentiment.NEUTRAL,
                        'mixed': Sentiment.MIXED
                    }
                    
                    mention.sentiment = sentiment_map.get(sentiment_str, Sentiment.NEUTRAL)
                    mention.sentiment_score = sentiment_score
            
        except Exception as e:
            self.logger.error(f"Batch sentiment processing failed: {e}")
            # Fallback to basic analysis for this batch
            for mention in batch:
                mention.sentiment, mention.sentiment_score = self._basic_sentiment_analysis(mention.content)
    
    def _basic_sentiment_analysis(self, content: str) -> Tuple[Sentiment, float]:
        """Basic keyword-based sentiment analysis as fallback."""
        
        if not content:
            return Sentiment.NEUTRAL, 0.0
        
        content_lower = content.lower()
        
        # Positive indicators
        positive_keywords = [
            'love', 'great', 'awesome', 'excellent', 'amazing', 'fantastic', 'perfect',
            'wonderful', 'outstanding', 'brilliant', 'impressed', 'recommend', 'best',
            'good', 'nice', 'helpful', 'useful', 'easy', 'simple', 'efficient'
        ]
        
        # Negative indicators
        negative_keywords = [
            'hate', 'terrible', 'awful', 'horrible', 'worst', 'bad', 'poor', 'sucks',
            'broken', 'useless', 'frustrated', 'annoying', 'difficult', 'complicated',
            'expensive', 'slow', 'problem', 'issue', 'bug', 'error', 'fail', 'disappointed'
        ]
        
        # Pain point indicators (usually negative)
        pain_point_keywords = [
            'struggling with', 'having trouble', 'can\'t figure out', 'need help',
            'looking for alternative', 'alternatives to', 'better than', 'instead of'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
        pain_point_count = sum(1 for keyword in pain_point_keywords if keyword in content_lower)
        
        # Adjust negative count for pain points
        negative_count += pain_point_count
        
        # Calculate sentiment
        if positive_count > negative_count:
            sentiment = Sentiment.POSITIVE
            score = min(0.8, 0.3 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = Sentiment.NEGATIVE
            score = max(-0.8, -0.3 - (negative_count - positive_count) * 0.1)
        else:
            sentiment = Sentiment.NEUTRAL
            score = 0.0
        
        return sentiment, score
    
    def create_sentiment_summary(self, mentions: List[SocialMention]) -> SentimentSummary:
        """Create aggregated sentiment summary from mentions."""
        
        if not mentions:
            return SentimentSummary(
                total_mentions=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                mixed_count=0,
                average_sentiment_score=0.0
            )
        
        sentiment_counts = {
            Sentiment.POSITIVE: 0,
            Sentiment.NEGATIVE: 0,
            Sentiment.NEUTRAL: 0,
            Sentiment.MIXED: 0
        }
        
        total_score = 0.0
        
        for mention in mentions:
            sentiment_counts[mention.sentiment] += 1
            total_score += mention.sentiment_score
        
        average_score = total_score / len(mentions) if mentions else 0.0
        
        return SentimentSummary(
            total_mentions=len(mentions),
            positive_count=sentiment_counts[Sentiment.POSITIVE],
            negative_count=sentiment_counts[Sentiment.NEGATIVE],
            neutral_count=sentiment_counts[Sentiment.NEUTRAL],
            mixed_count=sentiment_counts[Sentiment.MIXED],
            average_sentiment_score=round(average_score, 3)
        )
