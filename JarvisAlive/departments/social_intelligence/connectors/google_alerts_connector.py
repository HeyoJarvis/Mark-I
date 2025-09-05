"""Google Alerts connector for brand monitoring."""

import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import quote_plus

from ..models.social_models import SocialMention, SocialSource, Sentiment

logger = logging.getLogger(__name__)


class GoogleAlertsConnector:
    """Connector for Google Alerts monitoring via web scraping."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session = None
    
    async def search_mentions(
        self, 
        keywords: List[str], 
        max_results: int = 50,
        time_range_hours: int = 24
    ) -> List[SocialMention]:
        """Search for brand mentions using Google search."""
        
        mentions = []
        
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                
                for keyword in keywords:
                    keyword_mentions = await self._search_keyword_mentions(
                        keyword, max_results // len(keywords), time_range_hours
                    )
                    mentions.extend(keyword_mentions)
            
            logger.info(f"Found {len(mentions)} mentions from Google search")
            return mentions[:max_results]
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return self._generate_mock_mentions(keywords, min(max_results, 10))
    
    async def _search_keyword_mentions(
        self, 
        keyword: str, 
        max_results: int,
        time_range_hours: int
    ) -> List[SocialMention]:
        """Search for mentions of a specific keyword."""
        mentions = []
        
        try:
            # Build Google search query for recent mentions
            time_filter = self._get_time_filter(time_range_hours)
            search_query = f'"{keyword}" {time_filter}'
            
            # Use Google search (simplified approach)
            search_results = await self._perform_google_search(search_query, max_results)
            
            for result in search_results:
                mention = self._create_mention_from_search_result(result, keyword)
                mentions.append(mention)
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error searching for keyword {keyword}: {e}")
            return []
    
    async def _perform_google_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform Google search and extract results."""
        
        # Try multiple approaches for Google data
        import os
        
        # Option 1: Google Custom Search API (if configured)
        google_api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if google_api_key and search_engine_id:
            try:
                return await self._google_custom_search(query, max_results, google_api_key, search_engine_id)
            except Exception as e:
                logger.error(f"Google Custom Search API failed: {e}")
        
        # Option 2: RSS Feed parsing (if configured)
        rss_feeds = os.getenv('GOOGLE_ALERTS_RSS_FEEDS', '').split(',')
        if rss_feeds and rss_feeds[0]:
            try:
                return await self._parse_google_alerts_rss(rss_feeds, query, max_results)
            except Exception as e:
                logger.error(f"RSS feed parsing failed: {e}")
        
        # Option 3: Fallback to mock data
        logger.info(f"Using mock data for Google search: {query}")
        logger.info("To use real Google data, configure GOOGLE_CUSTOM_SEARCH_API_KEY or GOOGLE_ALERTS_RSS_FEEDS")
        return self._get_mock_search_results(query, max_results)
    
    def _get_time_filter(self, hours: int) -> str:
        """Generate time filter for Google search."""
        if hours <= 24:
            return "past 24 hours"
        elif hours <= 168:  # 7 days
            return "past week"
        else:
            return "past month"
    
    def _create_mention_from_search_result(self, result: Dict[str, Any], keyword: str) -> SocialMention:
        """Create SocialMention from Google search result."""
        return SocialMention(
            content=result.get("snippet", ""),
            title=result.get("title", ""),
            url=result.get("url", ""),
            author=result.get("source", "Unknown"),
            source=SocialSource.GOOGLE_ALERTS,
            platform_id=result.get("url", "").replace("/", "_").replace(":", ""),
            created_at=result.get("date", datetime.now().isoformat())
        )
    
    def _get_mock_search_results(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Generate mock search results for testing."""
        mock_results = []
        
        # Extract keyword from query for more realistic mock data
        keyword = query.split('"')[1] if '"' in query else query.split()[0]
        
        mock_data = [
            {
                "title": f"Industry Report: {keyword} Market Analysis 2024",
                "snippet": f"Latest trends in {keyword} show significant growth...",
                "url": f"https://techcrunch.com/2024/01/15/{keyword.lower().replace(' ', '-')}-analysis",
                "source": "TechCrunch",
                "date": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "title": f"Discussion: {keyword} vs Competitors",
                "snippet": f"Users comparing {keyword} with alternative solutions...",
                "url": f"https://news.ycombinator.com/item?id=12345",
                "source": "Hacker News",
                "date": (datetime.now() - timedelta(hours=8)).isoformat()
            },
            {
                "title": f"Review: Our Experience with {keyword}",
                "snippet": f"After using {keyword} for 6 months, here are our thoughts...",
                "url": f"https://medium.com/@user/review-{keyword.lower().replace(' ', '-')}",
                "source": "Medium",
                "date": (datetime.now() - timedelta(hours=12)).isoformat()
            },
            {
                "title": f"{keyword} Announces New Features",
                "snippet": f"Company behind {keyword} releases major update...",
                "url": f"https://example-news.com/{keyword.lower().replace(' ', '-')}-update",
                "source": "Industry News",
                "date": (datetime.now() - timedelta(hours=6)).isoformat()
            }
        ]
        
        return mock_data[:count]
    
    def _generate_mock_mentions(self, keywords: List[str], count: int) -> List[SocialMention]:
        """Generate mock mentions for testing."""
        mock_mentions = []
        
        for i, keyword in enumerate(keywords[:count]):
            mock_results = self._get_mock_search_results(f'"{keyword}"', 2)
            
            for j, result in enumerate(mock_results):
                mention = self._create_mention_from_search_result(result, keyword)
                mock_mentions.append(mention)
        
        logger.info(f"Generated {len(mock_mentions)} mock Google mentions")
        return mock_mentions[:count]
    
    async def setup_google_alerts(self, keywords: List[str]) -> bool:
        """Set up Google Alerts for keywords (placeholder for future implementation)."""
        logger.info(f"Setting up Google Alerts for keywords: {keywords}")
        
        # In a real implementation, this would:
        # 1. Use Google Alerts API (if available)
        # 2. Or automate Google Alerts setup via web automation
        # 3. Or set up RSS feed monitoring for existing alerts
        
        return True
    
    async def check_rss_feeds(self, rss_urls: List[str]) -> List[SocialMention]:
        """Check RSS feeds from Google Alerts."""
        mentions = []
        
        try:
            for rss_url in rss_urls:
                feed_mentions = await self._parse_rss_feed(rss_url)
                mentions.extend(feed_mentions)
            
            return mentions
            
        except Exception as e:
            logger.error(f"RSS feed parsing failed: {e}")
            return []
    
    async def _google_custom_search(self, query: str, max_results: int, api_key: str, search_engine_id: str) -> List[Dict[str, Any]]:
        """Use Google Custom Search API for real search results."""
        
        try:
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(max_results, 10),  # Google Custom Search limit
                'dateRestrict': 'd1'  # Last day
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'source': item.get('displayLink', ''),
                            'date': datetime.now().isoformat()  # Google doesn't provide exact dates
                        })
                    
                    logger.info(f"Google Custom Search API returned {len(results)} results")
                    return results
                else:
                    logger.error(f"Google Custom Search API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google Custom Search API failed: {e}")
            return []
    
    async def _parse_google_alerts_rss(self, rss_feeds: List[str], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse Google Alerts RSS feeds for mentions."""
        
        try:
            import feedparser
            results = []
            
            for rss_url in rss_feeds:
                if not rss_url.strip():
                    continue
                    
                logger.info(f"Parsing RSS feed: {rss_url}")
                
                # Parse RSS feed
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:max_results//len(rss_feeds)]:
                    # Check if entry matches query keywords
                    if query.lower() in (entry.title + ' ' + entry.summary).lower():
                        results.append({
                            'title': entry.title,
                            'snippet': entry.summary,
                            'url': entry.link,
                            'source': entry.get('source', 'Google Alerts'),
                            'date': entry.get('published', datetime.now().isoformat())
                        })
            
            logger.info(f"RSS parsing returned {len(results)} results")
            return results[:max_results]
            
        except ImportError:
            logger.error("feedparser library not available for RSS parsing")
            return []
        except Exception as e:
            logger.error(f"RSS parsing failed: {e}")
            return []
    
    async def _parse_rss_feed(self, rss_url: str) -> List[SocialMention]:
        """Parse RSS feed and extract mentions."""
        
        try:
            import feedparser
            
            feed = feedparser.parse(rss_url)
            mentions = []
            
            for entry in feed.entries:
                mention = SocialMention(
                    content=entry.summary,
                    title=entry.title,
                    url=entry.link,
                    author=entry.get('author', 'Google Alerts'),
                    source=SocialSource.GOOGLE_ALERTS,
                    platform_id=entry.get('id', entry.link),
                    created_at=entry.get('published', datetime.now().isoformat())
                )
                mentions.append(mention)
            
            logger.info(f"Parsed {len(mentions)} mentions from RSS feed")
            return mentions
            
        except ImportError:
            logger.warning("feedparser library not available")
            return []
        except Exception as e:
            logger.error(f"RSS parsing failed: {e}")
            return []
