"""Reddit API connector for social listening."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from ..models.social_models import SocialMention, SocialSource, Sentiment

logger = logging.getLogger(__name__)


class RedditConnector:
    """Connector for Reddit API integration using PRAW."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reddit = None
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """Initialize Reddit API connection."""
        try:
            # Try to import praw
            import praw
            
            # Reddit API credentials (can be set via config or env vars)
            client_id = self.config.get('reddit_client_id', 'your_client_id')
            client_secret = self.config.get('reddit_client_secret', 'your_client_secret')
            user_agent = self.config.get('reddit_user_agent', 'SocialListening:v1.0')
            
            # For now, use read-only mode with placeholder credentials
            if client_id == 'your_client_id':
                logger.warning("Reddit API credentials not configured, using mock data")
                self.reddit = None
            else:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit connector initialized successfully")
                
        except ImportError:
            logger.warning("PRAW library not installed, using mock data")
            self.reddit = None
        except Exception as e:
            logger.error(f"Failed to initialize Reddit connector: {e}")
            self.reddit = None
    
    async def search_mentions(
        self, 
        keywords: List[str], 
        subreddits: List[str], 
        max_results: int = 50,
        time_range_hours: int = 24
    ) -> List[SocialMention]:
        """Search for mentions across specified subreddits."""
        
        if not self.reddit:
            logger.info("Reddit API not available, returning mock data")
            return self._generate_mock_mentions(keywords, subreddits, max_results)
        
        mentions = []
        
        try:
            for subreddit_name in subreddits:
                subreddit_mentions = await self._search_subreddit(
                    subreddit_name, keywords, max_results // len(subreddits), time_range_hours
                )
                mentions.extend(subreddit_mentions)
            
            logger.info(f"Found {len(mentions)} mentions from Reddit")
            return mentions[:max_results]
            
        except Exception as e:
            logger.error(f"Reddit search failed: {e}")
            return self._generate_mock_mentions(keywords, subreddits, min(max_results, 10))
    
    async def _search_subreddit(
        self, 
        subreddit_name: str, 
        keywords: List[str], 
        max_results: int,
        time_range_hours: int
    ) -> List[SocialMention]:
        """Search a specific subreddit for keyword mentions."""
        mentions = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search recent posts
            for submission in subreddit.new(limit=max_results * 2):  # Get more to filter by time
                # Check if post is within time range
                post_time = datetime.fromtimestamp(submission.created_utc)
                if datetime.now() - post_time > timedelta(hours=time_range_hours):
                    continue
                
                # Check if any keywords match
                if self._contains_keywords(submission.title + " " + submission.selftext, keywords):
                    mention = self._create_mention_from_submission(submission, subreddit_name)
                    mentions.append(mention)
                
                # Also check comments for keyword mentions
                try:
                    submission.comments.replace_more(limit=5)  # Limit comment expansion
                    for comment in submission.comments.list()[:10]:  # Check top 10 comments
                        if self._contains_keywords(comment.body, keywords):
                            comment_mention = self._create_mention_from_comment(comment, submission, subreddit_name)
                            mentions.append(comment_mention)
                except Exception as e:
                    logger.debug(f"Error processing comments: {e}")
                    continue
                
                if len(mentions) >= max_results:
                    break
            
            return mentions[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching subreddit {subreddit_name}: {e}")
            return []
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the specified keywords."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _create_mention_from_submission(self, submission, subreddit_name: str) -> SocialMention:
        """Create SocialMention from Reddit submission."""
        return SocialMention(
            content=submission.selftext or submission.title,
            title=submission.title,
            url=f"https://reddit.com{submission.permalink}",
            author=str(submission.author) if submission.author else "[deleted]",
            source=SocialSource.REDDIT,
            platform_id=submission.id,
            subreddit=subreddit_name,
            created_at=datetime.fromtimestamp(submission.created_utc).isoformat(),
            upvotes=submission.score,
            comments_count=submission.num_comments
        )
    
    def _create_mention_from_comment(self, comment, submission, subreddit_name: str) -> SocialMention:
        """Create SocialMention from Reddit comment."""
        return SocialMention(
            content=comment.body,
            title=f"Comment on: {submission.title}",
            url=f"https://reddit.com{comment.permalink}",
            author=str(comment.author) if comment.author else "[deleted]",
            source=SocialSource.REDDIT,
            platform_id=comment.id,
            subreddit=subreddit_name,
            created_at=datetime.fromtimestamp(comment.created_utc).isoformat(),
            upvotes=comment.score,
            comments_count=0
        )
    
    def _generate_mock_mentions(
        self, 
        keywords: List[str], 
        subreddits: List[str], 
        count: int
    ) -> List[SocialMention]:
        """Generate mock Reddit mentions for testing."""
        mock_mentions = []
        
        mock_posts = [
            {
                "title": f"Looking for alternatives to {keywords[0] if keywords else 'current solution'}",
                "content": f"Has anyone tried different options for {keywords[0] if keywords else 'this problem'}? Current solution is too expensive.",
                "author": "startup_founder_23",
                "subreddit": subreddits[0] if subreddits else "entrepreneur",
                "upvotes": 15,
                "comments": 8
            },
            {
                "title": f"Pain points with {keywords[0] if keywords else 'existing tools'}",
                "content": f"Struggling with {keywords[0] if keywords else 'our current setup'}. Anyone else facing similar issues?",
                "author": "growth_hacker",
                "subreddit": subreddits[1] if len(subreddits) > 1 else "SaaS",
                "upvotes": 23,
                "comments": 12
            },
            {
                "title": "What tools are you using for business growth?",
                "content": f"Survey: What's working for you? Especially interested in {keywords[0] if keywords else 'automation tools'}.",
                "author": "marketing_manager",
                "subreddit": subreddits[2] if len(subreddits) > 2 else "marketing",
                "upvotes": 31,
                "comments": 19
            }
        ]
        
        for i, post in enumerate(mock_posts[:count]):
            mention = SocialMention(
                content=post["content"],
                title=post["title"],
                url=f"https://reddit.com/r/{post['subreddit']}/comments/mock_{i}",
                author=post["author"],
                source=SocialSource.REDDIT,
                platform_id=f"mock_reddit_{i}",
                subreddit=post["subreddit"],
                upvotes=post["upvotes"],
                comments_count=post["comments"]
            )
            mock_mentions.append(mention)
        
        logger.info(f"Generated {len(mock_mentions)} mock Reddit mentions")
        return mock_mentions
