"""WordPress API connector for content management."""

import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64

from ..models.content_models import Content, ContentType, ContentStatus

logger = logging.getLogger(__name__)


class WordPressConnector:
    """Connector for WordPress REST API integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = None
        self.auth_header = None
        self._initialize_wordpress()
    
    def _initialize_wordpress(self):
        """Initialize WordPress API connection."""
        import os
        
        # WordPress site configuration
        site_url = (self.config.get('wordpress_site_url') or 
                   os.getenv('WORDPRESS_SITE_URL', ''))
        username = (self.config.get('wordpress_username') or 
                   os.getenv('WORDPRESS_USERNAME', ''))
        app_password = (self.config.get('wordpress_app_password') or 
                       os.getenv('WORDPRESS_APP_PASSWORD', ''))
        
        if not site_url or not username or not app_password:
            logger.warning("WordPress credentials not configured, using mock data")
            logger.info("To use real WordPress, add WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD to .env")
            self.base_url = None
            self.auth_header = None
        else:
            # Set up WordPress REST API connection
            self.base_url = f"{site_url.rstrip('/')}/wp-json/wp/v2"
            
            # Create basic auth header for WordPress
            credentials = f"{username}:{app_password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded_credentials}"
            
            logger.info("WordPress connector initialized successfully")
    
    async def get_existing_posts(self, max_posts: int = 100) -> List[Content]:
        """Get existing WordPress posts."""
        
        if not self.base_url:
            logger.info("WordPress not configured, returning mock posts")
            return self._generate_mock_posts(max_posts)
        
        try:
            headers = {"Authorization": self.auth_header}
            params = {
                "per_page": min(max_posts, 100),  # WordPress limit
                "status": "publish",
                "_fields": "id,title,content,excerpt,date,slug,link,meta"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/posts",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        posts_data = await response.json()
                        return self._parse_wordpress_posts(posts_data)
                    else:
                        logger.error(f"WordPress API error: {response.status}")
                        return self._generate_mock_posts(min(max_posts, 10))
                        
        except Exception as e:
            logger.error(f"WordPress posts retrieval failed: {e}")
            return self._generate_mock_posts(min(max_posts, 10))
    
    async def publish_content(self, content: Content) -> Dict[str, Any]:
        """Publish content to WordPress."""
        
        if not self.base_url:
            logger.info("WordPress not configured, simulating publish")
            return self._simulate_wordpress_publish(content)
        
        try:
            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
            
            post_data = {
                "title": content.title,
                "content": content.content_body,
                "excerpt": content.meta_description,
                "slug": content.slug,
                "status": "publish" if content.status == ContentStatus.PUBLISHED else "draft",
                "meta": {
                    "focus_keyword": content.focus_keyword,
                    "target_keywords": ",".join(content.target_keywords)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/posts",
                    headers=headers,
                    json=post_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"Content published to WordPress: {result.get('id')}")
                        return {
                            "success": True,
                            "wordpress_id": result.get('id'),
                            "url": result.get('link'),
                            "status": result.get('status')
                        }
                    else:
                        logger.error(f"WordPress publish error: {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"WordPress publish failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_content(self, content: Content, wordpress_id: str) -> Dict[str, Any]:
        """Update existing WordPress content."""
        
        if not self.base_url:
            return self._simulate_wordpress_update(content, wordpress_id)
        
        try:
            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
            
            update_data = {
                "title": content.title,
                "content": content.content_body,
                "excerpt": content.meta_description,
                "slug": content.slug,
                "meta": {
                    "focus_keyword": content.focus_keyword,
                    "target_keywords": ",".join(content.target_keywords)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/posts/{wordpress_id}",
                    headers=headers,
                    json=update_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Content updated in WordPress: {wordpress_id}")
                        return {
                            "success": True,
                            "wordpress_id": wordpress_id,
                            "url": result.get('link')
                        }
                    else:
                        logger.error(f"WordPress update error: {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"WordPress update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_wordpress_posts(self, posts_data: List[Dict[str, Any]]) -> List[Content]:
        """Parse WordPress posts into Content objects."""
        
        contents = []
        
        for post in posts_data:
            try:
                # Extract content from WordPress post
                content = Content(
                    title=post.get('title', {}).get('rendered', ''),
                    content_type=ContentType.BLOG_POST,  # Assume blog post for WordPress
                    content_body=post.get('content', {}).get('rendered', ''),
                    meta_description=post.get('excerpt', {}).get('rendered', ''),
                    target_keywords=[],  # Would extract from meta
                    focus_keyword=post.get('meta', {}).get('focus_keyword', ''),
                    slug=post.get('slug', ''),
                    status=ContentStatus.PUBLISHED,
                    publish_date=post.get('date', ''),
                    canonical_url=post.get('link', ''),
                    content_id=str(post.get('id', ''))
                )
                
                contents.append(content)
                
            except Exception as e:
                logger.warning(f"Failed to parse WordPress post: {e}")
                continue
        
        return contents
    
    def _generate_mock_posts(self, count: int) -> List[Content]:
        """Generate mock WordPress posts for testing."""
        
        mock_posts = []
        
        mock_data = [
            {
                "title": "How to Improve Your Business Process Automation",
                "focus_keyword": "business automation",
                "content_type": ContentType.BLOG_POST
            },
            {
                "title": "Top 10 CRM Features Every Small Business Needs",
                "focus_keyword": "CRM features",
                "content_type": ContentType.ARTICLE
            },
            {
                "title": "Case Study: 300% Growth with Marketing Automation",
                "focus_keyword": "marketing automation",
                "content_type": ContentType.CASE_STUDY
            },
            {
                "title": "The Complete Guide to Lead Generation in 2024",
                "focus_keyword": "lead generation",
                "content_type": ContentType.BLOG_POST
            }
        ]
        
        for i, post_data in enumerate(mock_data[:count]):
            content = Content(
                title=post_data["title"],
                content_type=post_data["content_type"],
                content_body=f"This is mock content for {post_data['title']}. In a real implementation, this would contain the full article content with SEO optimization, internal links, and comprehensive coverage of the topic.",
                meta_description=f"Learn about {post_data['focus_keyword']} with our comprehensive guide.",
                target_keywords=[post_data["focus_keyword"], f"{post_data['focus_keyword']} guide"],
                focus_keyword=post_data["focus_keyword"],
                slug=post_data["title"].lower().replace(" ", "-").replace(":", ""),
                status=ContentStatus.PUBLISHED,
                publish_date=(datetime.now()).isoformat(),
                page_views=500 + i * 200,
                organic_traffic=300 + i * 150,
                content_id=f"mock_wp_{i}"
            )
            mock_posts.append(content)
        
        logger.info(f"Generated {len(mock_posts)} mock WordPress posts")
        return mock_posts
    
    def _simulate_wordpress_publish(self, content: Content) -> Dict[str, Any]:
        """Simulate WordPress publishing for testing."""
        
        return {
            "success": True,
            "wordpress_id": f"mock_{content.content_id}",
            "url": f"https://yoursite.com/{content.slug}",
            "status": "published",
            "message": "Content published successfully (simulated)"
        }
    
    def _simulate_wordpress_update(self, content: Content, wordpress_id: str) -> Dict[str, Any]:
        """Simulate WordPress update for testing."""
        
        return {
            "success": True,
            "wordpress_id": wordpress_id,
            "url": f"https://yoursite.com/{content.slug}",
            "message": "Content updated successfully (simulated)"
        }
