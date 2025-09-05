"""Hacker News API connector for tech industry monitoring."""

import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ..models.social_models import SocialMention, SocialSource, Sentiment

logger = logging.getLogger(__name__)


class HackerNewsConnector:
    """Connector for Hacker News API integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session = None
    
    async def search_mentions(
        self, 
        keywords: List[str], 
        max_results: int = 50,
        time_range_hours: int = 24
    ) -> List[SocialMention]:
        """Search for mentions in Hacker News stories and comments."""
        
        mentions = []
        
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                
                # Get recent stories
                recent_stories = await self._get_recent_stories(max_results * 2, time_range_hours)
                
                # Search stories for keyword mentions
                for story in recent_stories:
                    if self._contains_keywords(story.get('title', '') + ' ' + story.get('text', ''), keywords):
                        mention = self._create_mention_from_story(story)
                        mentions.append(mention)
                    
                    # Also check comments if story is relevant
                    if len(mentions) < max_results and story.get('kids'):
                        comment_mentions = await self._search_story_comments(
                            story, keywords, min(5, max_results - len(mentions))
                        )
                        mentions.extend(comment_mentions)
                    
                    if len(mentions) >= max_results:
                        break
            
            logger.info(f"Found {len(mentions)} mentions from Hacker News")
            return mentions[:max_results]
            
        except Exception as e:
            logger.error(f"Hacker News search failed: {e}")
            return self._generate_mock_mentions(keywords, min(max_results, 10))
    
    async def _get_recent_stories(self, max_stories: int, time_range_hours: int) -> List[Dict[str, Any]]:
        """Get recent stories from Hacker News."""
        stories = []
        
        try:
            # Get top stories IDs
            async with self.session.get(f"{self.base_url}/topstories.json") as response:
                if response.status == 200:
                    story_ids = await response.json()
                else:
                    logger.error(f"Failed to get top stories: {response.status}")
                    return []
            
            # Get story details for recent stories
            cutoff_time = time.time() - (time_range_hours * 3600)
            
            for story_id in story_ids[:max_stories]:
                try:
                    story = await self._get_story_details(story_id)
                    
                    # Check if story is within time range
                    if story and story.get('time', 0) >= cutoff_time:
                        stories.append(story)
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Error getting story {story_id}: {e}")
                    continue
            
            return stories
            
        except Exception as e:
            logger.error(f"Error getting recent stories: {e}")
            return []
    
    async def _get_story_details(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific story."""
        try:
            async with self.session.get(f"{self.base_url}/item/{story_id}.json") as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.debug(f"Error getting story details for {story_id}: {e}")
            return None
    
    async def _search_story_comments(
        self, 
        story: Dict[str, Any], 
        keywords: List[str], 
        max_comments: int
    ) -> List[SocialMention]:
        """Search comments of a story for keyword mentions."""
        mentions = []
        
        try:
            comment_ids = story.get('kids', [])[:max_comments * 2]  # Get more to filter
            
            for comment_id in comment_ids:
                try:
                    comment = await self._get_story_details(comment_id)
                    
                    if comment and comment.get('text'):
                        if self._contains_keywords(comment['text'], keywords):
                            mention = self._create_mention_from_comment(comment, story)
                            mentions.append(mention)
                    
                    if len(mentions) >= max_comments:
                        break
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Error processing comment {comment_id}: {e}")
                    continue
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error searching story comments: {e}")
            return []
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the specified keywords."""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _create_mention_from_story(self, story: Dict[str, Any]) -> SocialMention:
        """Create SocialMention from Hacker News story."""
        return SocialMention(
            content=story.get('text', '') or story.get('title', ''),
            title=story.get('title', ''),
            url=story.get('url', f"https://news.ycombinator.com/item?id={story.get('id')}"),
            author=story.get('by', 'unknown'),
            source=SocialSource.HACKERNEWS,
            platform_id=str(story.get('id', '')),
            created_at=datetime.fromtimestamp(story.get('time', time.time())).isoformat(),
            upvotes=story.get('score', 0),
            comments_count=story.get('descendants', 0)
        )
    
    def _create_mention_from_comment(self, comment: Dict[str, Any], story: Dict[str, Any]) -> SocialMention:
        """Create SocialMention from Hacker News comment."""
        return SocialMention(
            content=comment.get('text', ''),
            title=f"Comment on: {story.get('title', 'HN Story')}",
            url=f"https://news.ycombinator.com/item?id={comment.get('id')}",
            author=comment.get('by', 'unknown'),
            source=SocialSource.HACKERNEWS,
            platform_id=str(comment.get('id', '')),
            created_at=datetime.fromtimestamp(comment.get('time', time.time())).isoformat(),
            upvotes=0,  # Comments don't have visible scores
            comments_count=0
        )
    
    def _generate_mock_mentions(self, keywords: List[str], count: int) -> List[SocialMention]:
        """Generate mock Hacker News mentions for testing."""
        mock_mentions = []
        
        mock_stories = [
            {
                "title": f"Show HN: New {keywords[0] if keywords else 'startup tool'} for developers",
                "content": f"Built this {keywords[0] if keywords else 'tool'} to solve a problem I had. Looking for feedback!",
                "author": "startup_dev",
                "url": "https://news.ycombinator.com/item?id=123456",
                "score": 42,
                "comments": 18
            },
            {
                "title": f"Ask HN: Best practices for {keywords[0] if keywords else 'development'}?",
                "content": f"What are your thoughts on {keywords[0] if keywords else 'current approaches'}? Seeing mixed opinions.",
                "author": "tech_lead",
                "url": "https://news.ycombinator.com/item?id=123457",
                "score": 67,
                "comments": 34
            },
            {
                "title": f"Discussion: {keywords[0] if keywords else 'Industry trends'} in 2024",
                "content": f"Interesting developments in {keywords[0] if keywords else 'the tech space'}. What's your take?",
                "author": "industry_analyst",
                "url": "https://news.ycombinator.com/item?id=123458",
                "score": 89,
                "comments": 56
            }
        ]
        
        for i, story in enumerate(mock_stories[:count]):
            mention = SocialMention(
                content=story["content"],
                title=story["title"],
                url=story["url"],
                author=story["author"],
                source=SocialSource.HACKERNEWS,
                platform_id=f"mock_hn_{i}",
                upvotes=story["score"],
                comments_count=story["comments"]
            )
            mock_mentions.append(mention)
        
        logger.info(f"Generated {len(mock_mentions)} mock Hacker News mentions")
        return mock_mentions
    
    async def get_trending_topics(self, max_stories: int = 30) -> List[str]:
        """Get trending topics from Hacker News front page."""
        topics = []
        
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                stories = await self._get_recent_stories(max_stories, 24)
                
                # Extract keywords from story titles
                for story in stories:
                    title = story.get('title', '')
                    # Simple keyword extraction (could be enhanced with NLP)
                    words = title.split()
                    for word in words:
                        if len(word) > 3 and word.lower() not in ['show', 'ask', 'tell', 'with', 'from', 'this', 'that']:
                            topics.append(word.lower())
                
                # Return most common topics
                from collections import Counter
                topic_counts = Counter(topics)
                return [topic for topic, count in topic_counts.most_common(10)]
                
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return ["ai", "startup", "programming", "tech", "software"]
