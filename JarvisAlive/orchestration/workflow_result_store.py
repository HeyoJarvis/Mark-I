"""
Workflow Result Store

Stores and manages results from completed workflows to enable context-aware responses.
Provides intelligent querying of previous work for answering user questions.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import redis.asyncio as redis

from ai_engines.anthropic_engine import AnthropicEngine


class WorkflowJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for workflow results that handles complex objects."""
    
    def default(self, obj):
        # Handle dataclass objects
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        # Handle enums
        elif hasattr(obj, 'value'):
            return obj.value
        # Handle datetime objects
        elif isinstance(obj, datetime):
            return obj.isoformat()
        
        return super().default(obj)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Represents a completed workflow result."""
    workflow_id: str
    session_id: str
    agent_type: str
    results: Dict[str, Any]
    timestamp: str
    business_goal: str
    extractable_info: Dict[str, Any]
    deliverables: List[str]
    artifacts: List[str]  # File paths or URLs created


class WorkflowResultStore:
    """Stores and retrieves results from completed workflows for context queries with Redis persistence."""
    
    def __init__(self, ai_engine: Optional[AnthropicEngine] = None, redis_url: str = "redis://localhost:6379"):
        self.ai_engine = ai_engine
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
        # In-memory cache for performance
        self.results_cache: Dict[str, WorkflowResult] = {}
        self.session_workflows: Dict[str, List[str]] = {}  # session_id -> [workflow_ids]
        self.agent_type_index: Dict[str, List[str]] = {}  # agent_type -> [workflow_ids]
        
        # Redis keys
        self.WORKFLOW_KEY_PREFIX = "workflow_result:"
        self.SESSION_KEY_PREFIX = "session_workflows:"
        self.AGENT_INDEX_KEY_PREFIX = "agent_index:"
        
        logger.info("Workflow Result Store initialized with Redis persistence")
    
    async def initialize(self):
        """Initialize Redis connection and load existing data."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
            # Load existing data from Redis
            await self._load_from_redis()
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Operating in memory-only mode.")
            self.redis_client = None
    
    async def _load_from_redis(self):
        """Load existing workflow results from Redis."""
        if not self.redis_client:
            return
        
        try:
            # Load all workflow results
            workflow_keys = await self.redis_client.keys(f"{self.WORKFLOW_KEY_PREFIX}*")
            for key in workflow_keys:
                workflow_data = await self.redis_client.hgetall(key)
                if workflow_data:
                    workflow_result = WorkflowResult(
                        workflow_id=workflow_data["workflow_id"],
                        session_id=workflow_data["session_id"],
                        agent_type=workflow_data["agent_type"],
                        results=json.loads(workflow_data["results"]),
                        timestamp=workflow_data["timestamp"],
                        business_goal=workflow_data["business_goal"],
                        extractable_info=json.loads(workflow_data["extractable_info"]),
                        deliverables=json.loads(workflow_data["deliverables"]),
                        artifacts=json.loads(workflow_data["artifacts"])
                    )
                    self.results_cache[workflow_result.workflow_id] = workflow_result
            
            # Load session indexes
            session_keys = await self.redis_client.keys(f"{self.SESSION_KEY_PREFIX}*")
            for key in session_keys:
                session_id = key.replace(self.SESSION_KEY_PREFIX, "")
                workflow_ids = await self.redis_client.lrange(key, 0, -1)
                self.session_workflows[session_id] = workflow_ids
            
            # Load agent type indexes
            agent_keys = await self.redis_client.keys(f"{self.AGENT_INDEX_KEY_PREFIX}*")
            for key in agent_keys:
                agent_type = key.replace(self.AGENT_INDEX_KEY_PREFIX, "")
                workflow_ids = await self.redis_client.lrange(key, 0, -1)
                self.agent_type_index[agent_type] = workflow_ids
            
            logger.info(f"Loaded {len(self.results_cache)} workflow results from Redis")
            
        except Exception as e:
            logger.error(f"Error loading data from Redis: {e}")
    
    async def _save_to_redis(self, workflow_result: WorkflowResult):
        """Save workflow result to Redis."""
        if not self.redis_client:
            return
        
        try:
            # Store workflow result
            workflow_key = f"{self.WORKFLOW_KEY_PREFIX}{workflow_result.workflow_id}"
            await self.redis_client.hset(workflow_key, mapping={
                "workflow_id": workflow_result.workflow_id,
                "session_id": workflow_result.session_id,
                "agent_type": workflow_result.agent_type,
                "results": json.dumps(workflow_result.results, cls=WorkflowJSONEncoder),
                "timestamp": workflow_result.timestamp,
                "business_goal": workflow_result.business_goal,
                "extractable_info": json.dumps(workflow_result.extractable_info, cls=WorkflowJSONEncoder),
                "deliverables": json.dumps(workflow_result.deliverables, cls=WorkflowJSONEncoder),
                "artifacts": json.dumps(workflow_result.artifacts, cls=WorkflowJSONEncoder)
            })
            
            # Set expiration (30 days)
            await self.redis_client.expire(workflow_key, 30 * 24 * 60 * 60)
            
            # Update session index
            session_key = f"{self.SESSION_KEY_PREFIX}{workflow_result.session_id}"
            await self.redis_client.lpush(session_key, workflow_result.workflow_id)
            await self.redis_client.expire(session_key, 30 * 24 * 60 * 60)
            
            # Update agent type index
            agent_key = f"{self.AGENT_INDEX_KEY_PREFIX}{workflow_result.agent_type}"
            await self.redis_client.lpush(agent_key, workflow_result.workflow_id)
            await self.redis_client.expire(agent_key, 30 * 24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")
    
    async def store_workflow_result(
        self, 
        workflow_id: str, 
        session_id: str,
        agent_type: str,
        results: Dict[str, Any],
        business_goal: str = ""
    ):
        """Store workflow results for future context queries."""
        
        try:
            # Extract queryable information
            extractable_info = await self._extract_queryable_info(agent_type, results)
            
            # Extract deliverables
            deliverables = self._extract_deliverables(agent_type, results)
            
            # Extract artifacts (files/URLs created)
            artifacts = self._extract_artifacts(agent_type, results)
            
            # Create workflow result
            workflow_result = WorkflowResult(
                workflow_id=workflow_id,
                session_id=session_id,
                agent_type=agent_type,
                results=results,
                timestamp=datetime.utcnow().isoformat(),
                business_goal=business_goal or results.get("business_goal", ""),
                extractable_info=extractable_info,
                deliverables=deliverables,
                artifacts=artifacts
            )
            
            # Store result in memory cache
            self.results_cache[workflow_id] = workflow_result
            
            # Update session index
            if session_id not in self.session_workflows:
                self.session_workflows[session_id] = []
            self.session_workflows[session_id].append(workflow_id)
            
            # Update agent type index
            if agent_type not in self.agent_type_index:
                self.agent_type_index[agent_type] = []
            self.agent_type_index[agent_type].append(workflow_id)
            
            # NEW: Store context for universal context awareness
            if hasattr(self, '_context_store') and self._context_store:
                try:
                    await self._context_store.store_agent_context(
                        session_id=session_id,
                        agent_id=agent_type,  # Don't add _agent suffix, it's already in agent_type
                        results=results
                    )
                    logger.info(f"✅ Stored universal context for {agent_type}")
                except Exception as e:
                    logger.error(f"Failed to store universal context: {e}")
            
            # 🚀 NEW: Persist to Redis
            await self._save_to_redis(workflow_result)
            
            logger.info(f"Stored workflow result: {workflow_id} ({agent_type}) for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error storing workflow result: {e}")
    
    async def _extract_queryable_info(self, agent_type: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract commonly queried information from results AND analyze actual output files."""
        
        extractable = {
            "agent_type": agent_type,
            "completion_time": datetime.utcnow().isoformat()
        }
        
        try:
            if agent_type == "website_generator_agent":
                # Basic extraction from results
                extractable["business_name"] = results.get("business_name", "")
                extractable["business_type"] = results.get("business_idea", "")
                extractable["website_type"] = results.get("site_type", "business")
                extractable["pages_created"] = len(results.get("saved_paths", []))
                
                # Extract from style guide
                if "style_guide" in results:
                    style_guide = results["style_guide"]
                    if isinstance(style_guide, dict):
                        extractable["colors"] = style_guide.get("colors", [])
                        extractable["fonts"] = style_guide.get("typography", {})
                        extractable["color_scheme"] = style_guide.get("color_scheme", "")
                
                # 🚀 NEW: Analyze actual HTML files
                html_analysis = await self._analyze_website_files(results)
                extractable.update(html_analysis)
                
            elif agent_type == "market_research_agent":
                # Basic extraction
                extractable["industry"] = results.get("industry", "")
                extractable["target_market"] = results.get("target_market", "")
                
                # 🚀 NEW: Analyze actual market research JSON
                market_analysis = await self._analyze_market_research_file(results)
                extractable.update(market_analysis)
                
            elif agent_type == "branding_agent":
                extractable["brand_name"] = results.get("brand_name", "")
                extractable["brand_colors"] = results.get("color_palette", [])
                extractable["brand_style"] = results.get("style_preferences", [])
                extractable["brand_personality"] = results.get("brand_personality", "")
                extractable["target_audience"] = results.get("target_audience", "")
                
            elif agent_type == "logo_generation_agent":
                extractable["logo_style"] = results.get("logo_style", "")
                extractable["logo_colors"] = results.get("colors", [])
                extractable["logo_type"] = results.get("logo_type", "")
                extractable["logo_url"] = results.get("logo_url", "")
            
            # Common extractable info for all agents
            extractable["business_goal"] = results.get("business_goal", "")
            extractable["status"] = results.get("status", "completed")
            
        except Exception as e:
            logger.error(f"Error extracting queryable info for {agent_type}: {e}")
        
        return extractable
    
    def _extract_deliverables(self, agent_type: str, results: Dict[str, Any]) -> List[str]:
        """Extract what was delivered by this workflow."""
        
        deliverables = []
        
        try:
            if agent_type == "website_generator_agent":
                business_name = results.get("business_name", "business")
                if results.get("website_generated_at"):
                    deliverables.append(f"Complete website for {business_name}")
                
                saved_paths = results.get("saved_paths", [])
                if saved_paths:
                    deliverables.append(f"{len(saved_paths)} HTML pages created")
                    # Add specific pages
                    for path in saved_paths[:3]:  # First 3 pages
                        page_name = path.split("/")[-1].replace(".html", "").replace("_", " ").title()
                        deliverables.append(f"• {page_name} page")
                
                if "style_guide" in results:
                    deliverables.append("Custom style guide and color palette")
                    
            elif agent_type == "branding_agent":
                brand_name = results.get("brand_name", "brand")
                if brand_name:
                    deliverables.append(f"Brand identity for {brand_name}")
                
                if results.get("color_palette"):
                    colors = results["color_palette"]
                    deliverables.append(f"Color palette with {len(colors)} colors")
                
                if results.get("brand_personality"):
                    deliverables.append("Brand personality and positioning")
                    
            elif agent_type == "logo_generation_agent":
                if results.get("logo_url"):
                    deliverables.append("Professional logo design")
                if results.get("logo_variations"):
                    variations = results["logo_variations"]
                    deliverables.append(f"{len(variations)} logo variations")
                    
            elif agent_type == "market_research_agent":
                industry = results.get("industry", "market")
                deliverables.append(f"Market research report for {industry}")
                
                if results.get("competitive_analysis"):
                    deliverables.append("Competitive analysis")
                if results.get("market_analysis"):
                    deliverables.append("Market size and trends analysis")
                if results.get("target_audience_analysis"):
                    deliverables.append("Target audience insights")
        
        except Exception as e:
            logger.error(f"Error extracting deliverables for {agent_type}: {e}")
        
        return deliverables
    
    def _extract_artifacts(self, agent_type: str, results: Dict[str, Any]) -> List[str]:
        """Extract file paths or URLs created by the workflow."""
        
        artifacts = []
        
        try:
            # Look for saved paths
            if "saved_paths" in results:
                artifacts.extend(results["saved_paths"])
            
            # Look for URLs
            if "logo_url" in results:
                artifacts.append(results["logo_url"])
            
            # Look for generated files
            if "generated_files" in results:
                artifacts.extend(results["generated_files"])
            
            # Look for output directory
            if "output_directory" in results:
                artifacts.append(results["output_directory"])
        
        except Exception as e:
            logger.error(f"Error extracting artifacts for {agent_type}: {e}")
        
        return artifacts
    
    async def query_context(
        self, 
        query: str, 
        session_id: str,
        max_results: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Query previous workflow results for relevant information."""
        
        try:
            # Get session workflows
            session_workflows = self.session_workflows.get(session_id, [])
            if not session_workflows:
                logger.info(f"No workflows found for session {session_id}")
                return None
            
            # Get relevant workflow results
            relevant_results = []
            for workflow_id in reversed(session_workflows):  # Most recent first
                if workflow_id in self.results_cache:
                    result = self.results_cache[workflow_id]
                    relevant_results.append(result)
                    if len(relevant_results) >= max_results:
                        break
            
            if not relevant_results:
                return None
            
            # Use AI to extract relevant information if available
            if self.ai_engine:
                return await self._ai_extract_relevant_info(query, relevant_results)
            else:
                # Fallback to simple extraction
                return self._simple_extract_relevant_info(query, relevant_results)
                
        except Exception as e:
            logger.error(f"Error querying context: {e}")
            return None
    
    async def _ai_extract_relevant_info(
        self, 
        query: str, 
        workflow_results: List[WorkflowResult]
    ) -> Dict[str, Any]:
        """Use AI to extract relevant information from workflow results."""
        
        try:
            # Prepare context data with rich content analysis
            context_data = []
            for result in workflow_results:
                context_item = {
                    "agent_type": result.agent_type,
                    "business_goal": result.business_goal,
                    "deliverables": result.deliverables,
                    "extractable_info": result.extractable_info,
                    "timestamp": result.timestamp
                }
                context_data.append(context_item)
            
            # Build extraction prompt
            extraction_prompt = f"""
You are extracting relevant information from previous workflow results to answer a user query.
The workflow results now include ACTUAL CONTENT ANALYSIS from generated files.

USER QUERY: "{query}"

AVAILABLE WORKFLOW RESULTS WITH CONTENT ANALYSIS:
{json.dumps(context_data, indent=2)}

Extract and return the most relevant information that answers the user's query.
Use the rich content analysis data (actual_colors_used, page_titles, key_competitors, etc.) to provide specific, detailed answers.

Examples of what you can now answer:
- "What colors did you use?" → Use actual_colors_used from CSS analysis
- "What pages did you create?" → Use page_titles and navigation_items
- "Who are the main competitors?" → Use key_competitors with descriptions
- "What's the market size?" → Use actual_market_size from research analysis

Return a JSON object with:
{{
    "relevant_info": "Detailed, specific answer using the actual content analysis",
    "source_workflows": ["list of relevant agent types"],
    "specific_details": {{
        "colors": ["actual hex codes if available"],
        "business_name": "extracted from actual content",
        "pages": ["actual page titles created"],
        "competitors": ["actual competitor names and descriptions"],
        "market_data": "actual market insights",
        "other_relevant_fields": "any other specific data that answers their question"
    }},
    "confidence": 0.95,
    "context_found": true
}}

If no relevant information is found, return:
{{
    "relevant_info": null,
    "context_found": false,
    "confidence": 0.0
}}
"""
            
            response = await self.ai_engine.generate(extraction_prompt)
            
            # Parse response
            try:
                if "```json" in response.content:
                    start = response.content.find("```json") + 7
                    end = response.content.find("```", start)
                    json_text = response.content[start:end].strip()
                else:
                    json_text = response.content.strip()
                
                extracted_info = json.loads(json_text)
                return extracted_info
                
            except json.JSONDecodeError:
                logger.error("Failed to parse AI extraction response")
                return self._simple_extract_relevant_info(query, workflow_results)
                
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return self._simple_extract_relevant_info(query, workflow_results)
    
    def _simple_extract_relevant_info(
        self, 
        query: str, 
        workflow_results: List[WorkflowResult]
    ) -> Dict[str, Any]:
        """Simple extraction without AI - fallback method."""
        
        query_lower = query.lower()
        relevant_info = {
            "context_found": True,
            "confidence": 0.6,
            "relevant_info": "",
            "source_workflows": [],
            "specific_details": {}
        }
        
        # Look for relevant information based on keywords
        for result in workflow_results:
            extractable = result.extractable_info
            
            # Check for color queries
            if any(keyword in query_lower for keyword in ["color", "colours", "palette"]):
                if "colors" in extractable and extractable["colors"]:
                    relevant_info["specific_details"]["colors"] = extractable["colors"]
                    relevant_info["source_workflows"].append(result.agent_type)
                    relevant_info["relevant_info"] = f"Colors used: {', '.join(extractable['colors'])}"
            
            # Check for business name queries
            if any(keyword in query_lower for keyword in ["name", "business", "company"]):
                if "business_name" in extractable and extractable["business_name"]:
                    relevant_info["specific_details"]["business_name"] = extractable["business_name"]
                    relevant_info["source_workflows"].append(result.agent_type)
                    relevant_info["relevant_info"] = f"Business name: {extractable['business_name']}"
            
            # Check for deliverable queries
            if any(keyword in query_lower for keyword in ["create", "made", "built", "delivered"]):
                if result.deliverables:
                    relevant_info["specific_details"]["deliverables"] = result.deliverables
                    relevant_info["source_workflows"].append(result.agent_type)
                    relevant_info["relevant_info"] = f"Deliverables: {', '.join(result.deliverables[:3])}"
        
        if not relevant_info["relevant_info"]:
            relevant_info["context_found"] = False
            relevant_info["confidence"] = 0.0
        
        return relevant_info
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of all work completed in a session."""
        
        session_workflows = self.session_workflows.get(session_id, [])
        if not session_workflows:
            return {"workflows": [], "total_deliverables": 0}
        
        summary = {
            "workflows": [],
            "total_deliverables": 0,
            "agent_types_used": set(),
            "time_range": {"start": None, "end": None}
        }
        
        for workflow_id in session_workflows:
            if workflow_id in self.results_cache:
                result = self.results_cache[workflow_id]
                
                summary["workflows"].append({
                    "agent_type": result.agent_type,
                    "business_goal": result.business_goal,
                    "deliverables": result.deliverables,
                    "timestamp": result.timestamp
                })
                
                summary["total_deliverables"] += len(result.deliverables)
                summary["agent_types_used"].add(result.agent_type)
                
                # Track time range
                timestamp = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
                if summary["time_range"]["start"] is None or timestamp < summary["time_range"]["start"]:
                    summary["time_range"]["start"] = timestamp
                if summary["time_range"]["end"] is None or timestamp > summary["time_range"]["end"]:
                    summary["time_range"]["end"] = timestamp
        
        summary["agent_types_used"] = list(summary["agent_types_used"])
        return summary
    
    def cleanup_old_results(self, days_to_keep: int = 30):
        """Clean up old workflow results to manage memory."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        workflows_to_remove = []
        
        for workflow_id, result in self.results_cache.items():
            try:
                result_date = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
                if result_date < cutoff_date:
                    workflows_to_remove.append(workflow_id)
            except Exception as e:
                logger.error(f"Error parsing timestamp for cleanup: {e}")
        
        # Remove old workflows
        for workflow_id in workflows_to_remove:
            result = self.results_cache[workflow_id]
            
            # Remove from session index
            session_workflows = self.session_workflows.get(result.session_id, [])
            if workflow_id in session_workflows:
                session_workflows.remove(workflow_id)
            
            # Remove from agent type index
            agent_workflows = self.agent_type_index.get(result.agent_type, [])
            if workflow_id in agent_workflows:
                agent_workflows.remove(workflow_id)
            
            # Remove from cache
            del self.results_cache[workflow_id]
        
        logger.info(f"Cleaned up {len(workflows_to_remove)} old workflow results")
    
    async def _analyze_website_files(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze actual HTML and CSS files to extract meaningful information."""
        
        analysis = {
            "actual_colors_used": [],
            "page_titles": [],
            "business_description": "",
            "content_themes": [],
            "navigation_items": [],
            "key_sections": []
        }
        
        try:
            saved_paths = results.get("saved_paths", [])
            if not saved_paths:
                return analysis
            
            # Find the website directory
            website_dir = None
            for path in saved_paths:
                if isinstance(path, str):
                    # Look for the website output directory
                    path_obj = Path(path)
                    if not path_obj.is_absolute():
                        # Try common locations
                        for base_dir in [".", "website_outputs"]:
                            potential_dir = Path(base_dir) / path_obj.parent
                            if potential_dir.exists():
                                website_dir = potential_dir
                                break
                        
                        # Try to find by pattern
                        if not website_dir:
                            for output_dir in Path(".").glob("website_outputs/*"):
                                if output_dir.is_dir():
                                    if (output_dir / path_obj.name).exists():
                                        website_dir = output_dir
                                        break
                    else:
                        website_dir = path_obj.parent
                    break
            
            if not website_dir or not website_dir.exists():
                logger.warning("Could not find website directory for analysis")
                return analysis
            
            # Analyze HTML files
            for html_file in website_dir.glob("*.html"):
                try:
                    html_content = html_file.read_text(encoding='utf-8')
                    
                    # Extract page title
                    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                    if title_match:
                        analysis["page_titles"].append(title_match.group(1))
                    
                    # Extract business name from content
                    business_name_matches = re.findall(r'<strong>(.*?)</strong>', html_content)
                    for match in business_name_matches:
                        if len(match) < 50 and not match.lower() in ['services', 'about', 'contact']:
                            analysis["business_description"] = match
                            break
                    
                    # Extract navigation items
                    nav_matches = re.findall(r'<a href="#(\w+)"[^>]*>(.*?)</a>', html_content)
                    for href, text in nav_matches:
                        if text not in analysis["navigation_items"]:
                            analysis["navigation_items"].append(text)
                    
                    # Extract main headings
                    heading_matches = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html_content, re.IGNORECASE)
                    for heading in heading_matches[:5]:  # First 5 headings
                        clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
                        if clean_heading and clean_heading not in analysis["key_sections"]:
                            analysis["key_sections"].append(clean_heading)
                
                except Exception as e:
                    logger.error(f"Error analyzing HTML file {html_file}: {e}")
            
            # Analyze CSS file for colors
            css_file = website_dir / "styles.css"
            if css_file.exists():
                try:
                    css_content = css_file.read_text(encoding='utf-8')
                    
                    # Extract color values
                    color_matches = re.findall(r'--[\w-]+:\s*(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})', css_content)
                    analysis["actual_colors_used"] = list(set(color_matches))  # Remove duplicates
                    
                    # Extract business themes from CSS variable names and values
                    if "copper" in css_content.lower() or "warm" in css_content.lower():
                        analysis["content_themes"].append("warm_tones")
                    if "professional" in css_content.lower() or "corporate" in css_content.lower():
                        analysis["content_themes"].append("professional")
                    if "restaurant" in css_content.lower() or "food" in css_content.lower():
                        analysis["content_themes"].append("restaurant")
                
                except Exception as e:
                    logger.error(f"Error analyzing CSS file: {e}")
        
        except Exception as e:
            logger.error(f"Error in website file analysis: {e}")
        
        return analysis
    
    async def _analyze_market_research_file(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze actual market research JSON file to extract meaningful information."""
        
        analysis = {
            "actual_market_size": "",
            "key_competitors": [],
            "market_insights": [],
            "target_audience_details": "",
            "competitive_advantages": [],
            "market_gaps": [],
            "industry_focus": ""
        }
        
        try:
            # Look for saved market research file
            saved_file = results.get("saved_file", "")
            if not saved_file:
                # Try to find market research files
                for report_file in Path(".").glob("market_research_reports/*.json"):
                    # Use the most recent one
                    saved_file = str(report_file)
                    break
            
            if saved_file and Path(saved_file).exists():
                try:
                    market_data = json.loads(Path(saved_file).read_text(encoding='utf-8'))
                    
                    # Extract research parameters
                    params = market_data.get("research_parameters", {})
                    business_info = params.get("business_info", {})
                    analysis["industry_focus"] = business_info.get("business_idea", "")
                    
                    # Extract research results
                    research_results = market_data.get("research_results", {})
                    
                    # Market size and metrics
                    analysis["actual_market_size"] = research_results.get("market_size", "")
                    
                    # Competitors with descriptions
                    competitors = research_results.get("competitors", [])
                    for comp in competitors[:5]:  # Top 5 competitors
                        if isinstance(comp, dict):
                            name = comp.get("name", "")
                            desc = comp.get("description", "")
                            if name:
                                analysis["key_competitors"].append({
                                    "name": name,
                                    "description": desc
                                })
                    
                    # Market insights
                    key_findings = research_results.get("key_findings", [])
                    if isinstance(key_findings, list):
                        analysis["market_insights"] = key_findings[:5]
                    
                    # Market gaps and opportunities
                    market_gaps = research_results.get("market_gaps", [])
                    if isinstance(market_gaps, list):
                        analysis["market_gaps"] = market_gaps[:5]
                    
                    # Target audience
                    analysis["target_audience_details"] = research_results.get("target_audience", "")
                    
                    # Competitive landscape
                    competitive_landscape = research_results.get("competitive_landscape", "")
                    if competitive_landscape:
                        analysis["market_insights"].append(competitive_landscape)
                
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing market research JSON: {e}")
                except Exception as e:
                    logger.error(f"Error reading market research file: {e}")
        
        except Exception as e:
            logger.error(f"Error in market research analysis: {e}")
        
        return analysis
