"""
Unified Frontend Server - Connect to Individual Agents and Intelligence Layer

This server provides a clean interface for users to interact with:
1. Individual agents directly (branding, market research, etc.)
2. The intelligence orchestration layer (LangGraph workflow coordination)
3. Real-time updates and progress tracking
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import system components
from orchestration.persistent.persistent_system import create_development_persistent_system
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.langgraph.parallel_intelligent_graph import ParallelIntelligentGraphBuilder
from departments.branding.branding_agent import BrandingAgent
from departments.market_research.market_research_agent import MarketResearchAgent
from departments.lead_generation.lead_mining_agent import LeadMiningAgent
from departments.social_intelligence.social_listening_agent import SocialListeningAgent
from departments.content_marketing.content_marketing_agent import ContentMarketingAgent

logger = logging.getLogger(__name__)

# Pydantic models
class AgentMessageRequest(BaseModel):
    session_id: str
    agent_id: str
    message: str
    use_orchestrator: bool = False

class OrchestratorRequest(BaseModel):
    session_id: str
    user_request: str
    workflow_type: str = "business_development"

class SessionRequest(BaseModel):
    user_id: str
    metadata: Dict[str, Any] = {}

# Global system components
app = FastAPI(title="Unified Agent System", version="1.0.0")
persistent_system = None
workflow_brain = None
langgraph_builder = None
individual_agents = {}
active_connections: Dict[str, WebSocket] = {}
session_data: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize all system components."""
    global persistent_system, workflow_brain, langgraph_builder, individual_agents
    
    try:
        logger.info("🚀 Starting Unified Agent System...")
        
        # Initialize persistent system
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        logger.info("✅ Persistent system initialized")
        
        # Initialize workflow brain
        config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'redis_url': 'redis://localhost:6379',
            'max_retries': 3,
            'enable_optimization': True
        }
        
        workflow_brain = WorkflowBrain(config)
        await workflow_brain.initialize_orchestration()
        logger.info("✅ Intelligence layer initialized")
        
        # Initialize LangGraph builder
        langgraph_builder = ParallelIntelligentGraphBuilder(
            redis_url='redis://localhost:6379',
            skip_approvals=True  # For demo purposes
        )
        logger.info("✅ LangGraph system initialized")
        
        # Initialize individual agents
        agent_config = {'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')}
        individual_agents = {
            'branding': BrandingAgent(agent_config),
            'market_research': MarketResearchAgent(agent_config),
            'lead_mining': LeadMiningAgent(agent_config),
            'social_intelligence': SocialListeningAgent(agent_config),
            'content_marketing': ContentMarketingAgent(agent_config)
        }
        logger.info("✅ Individual agents initialized")
        
        logger.info("🎉 Unified Agent System ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if persistent_system:
        await persistent_system.stop()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Send initial system status
        await websocket.send_text(json.dumps({
            'type': 'system_ready',
            'data': {
                'session_id': session_id,
                'available_agents': await get_available_agents_list(),
                'intelligence_layer_status': 'ready'
            }
        }))
        
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
            elif message['type'] == 'agent_message':
                await handle_agent_message_ws(session_id, message['data'])
            elif message['type'] == 'orchestrator_request':
                await handle_orchestrator_request_ws(session_id, message['data'])
            
    except WebSocketDisconnect:
        active_connections.pop(session_id, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.pop(session_id, None)

async def broadcast_to_session(session_id: str, message: Dict[str, Any]):
    """Broadcast a message to a specific session's WebSocket."""
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_text(json.dumps(message))
        except:
            active_connections.pop(session_id, None)

# REST API endpoints
@app.post("/api/sessions")
async def create_session(request: SessionRequest):
    """Create a new user session."""
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    session_data[session_id] = {
        'user_id': request.user_id,
        'created_at': datetime.utcnow(),
        'metadata': request.metadata,
        'message_history': [],
        'active_workflows': {}
    }
    
    return {"session_id": session_id}

@app.get("/api/agents")
async def get_agents():
    """Get list of available agents and intelligence layer."""
    return {"agents": await get_available_agents_list()}

async def get_available_agents_list() -> List[Dict[str, Any]]:
    """Get formatted list of available agents."""
    return [
        {
            "agent_id": "intelligence_orchestrator",
            "name": "🧠 Intelligence Orchestrator",
            "description": "Uses LangGraph to coordinate multiple agents intelligently with human-in-the-loop decision making",
            "type": "orchestrator",
            "capabilities": ["workflow_planning", "parallel_coordination", "human_approval", "intelligent_routing"],
            "status": "available",
            "icon": "🧠"
        },
        {
            "agent_id": "branding",
            "name": "🎨 Brand Designer",
            "description": "Creates brand identities, logos, and visual designs using AI",
            "type": "specialist",
            "capabilities": ["logo_design", "brand_strategy", "color_palette", "brand_guidelines"],
            "status": "available",
            "icon": "🎨"
        },
        {
            "agent_id": "market_research",
            "name": "📊 Market Analyst",
            "description": "Analyzes markets, competition, and business opportunities",
            "type": "specialist",
            "capabilities": ["market_analysis", "competitor_research", "trend_analysis", "opportunity_assessment"],
            "status": "available",
            "icon": "📊"
        },
        {
            "agent_id": "lead_mining",
            "name": "🎯 Lead Mining Agent",
            "description": "Finds and qualifies potential customers using Apollo API and AI analysis",
            "type": "specialist",
            "capabilities": ["lead_generation", "apollo_integration", "icp_analysis", "lead_qualification"],
            "status": "available",
            "icon": "🎯"
        },
        {
            "agent_id": "social_intelligence",
            "name": "📱 Social Intelligence",
            "description": "Monitors social media for brand mentions, competitor discussions, and engagement opportunities",
            "type": "specialist",
            "capabilities": ["social_monitoring", "sentiment_analysis", "reddit_monitoring", "hackernews_monitoring"],
            "status": "available",
            "icon": "📱"
        },
        {
            "agent_id": "content_marketing",
            "name": "📝 Content Marketing",
            "description": "Creates SEO-optimized content strategy and manages content distribution",
            "type": "specialist",
            "capabilities": ["content_creation", "seo_optimization", "wordpress_integration", "content_calendar"],
            "status": "available",
            "icon": "📝"
        }
    ]

@app.post("/api/agent/message")
async def send_agent_message(request: AgentMessageRequest):
    """Send message to individual agent."""
    try:
        if request.agent_id not in individual_agents:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        # Run the agent directly
        agent = individual_agents[request.agent_id]
        
        # Prepare state based on agent type
        if request.agent_id == 'lead_mining':
            state = {
                'business_idea': request.message,
                'user_request': request.message,
                'session_id': request.session_id,
                'target_industry': 'Technology',  # Default for testing
                'company_size': '50-500 employees'
            }
        elif request.agent_id in ['social_intelligence', 'content_marketing']:
            state = {
                'business_idea': request.message,
                'user_request': request.message,
                'session_id': request.session_id,
                'brand_name': 'Your Business',  # Default brand context
                'target_audience': 'Business professionals'
            }
        else:
            # Default state for branding and market research
            state = {
                'business_idea': request.message,
                'user_request': request.message,
                'session_id': request.session_id
            }
        
        result = await agent.run(state)
        
        # Format response
        response = format_agent_response(request.agent_id, result)
        
        # Store in session history
        if request.session_id in session_data:
            session_data[request.session_id]['message_history'].append({
                'type': 'agent_response',
                'agent_id': request.agent_id,
                'user_message': request.message,
                'agent_response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Broadcast to WebSocket
        await broadcast_to_session(request.session_id, {
            'type': 'agent_response',
            'data': {
                'agent_id': request.agent_id,
                'response': response,
                'success': True
            }
        })
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Error in agent message: {e}")
        error_msg = f"Error processing request: {str(e)}"
        
        await broadcast_to_session(request.session_id, {
            'type': 'agent_error',
            'data': {
                'agent_id': request.agent_id,
                'error': error_msg
            }
        })
        
        return {
            "success": False,
            "error": error_msg
        }

@app.post("/api/orchestrator/workflow")
async def start_orchestrator_workflow(request: OrchestratorRequest):
    """Start a workflow through the intelligence orchestrator."""
    try:
        # Build and run LangGraph workflow
        graph_app, system, brain = await langgraph_builder.build()
        
        # Create initial state
        initial_state = {
            'workflow_id': f"workflow_{request.session_id}_{int(datetime.utcnow().timestamp())}",
            'session_id': request.session_id,
            'user_request': request.user_request,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Store workflow in session
        if request.session_id in session_data:
            session_data[request.session_id]['active_workflows'][initial_state['workflow_id']] = {
                'status': 'running',
                'started_at': datetime.utcnow(),
                'user_request': request.user_request
            }
        
        # Broadcast workflow started
        await broadcast_to_session(request.session_id, {
            'type': 'workflow_started',
            'data': {
                'workflow_id': initial_state['workflow_id'],
                'status': 'analyzing'
            }
        })
        
        # Run the workflow asynchronously
        asyncio.create_task(execute_langgraph_workflow(
            graph_app, initial_state, request.session_id
        ))
        
        return {
            "success": True,
            "workflow_id": initial_state['workflow_id'],
            "status": "started",
            "message": "Intelligence orchestrator is analyzing your request and planning the workflow..."
        }
        
    except Exception as e:
        logger.error(f"Error starting orchestrator workflow: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def execute_langgraph_workflow(graph_app, initial_state: Dict[str, Any], session_id: str):
    """Execute LangGraph workflow and stream updates."""
    try:
        # Configure the workflow execution
        config = {"configurable": {"thread_id": initial_state['workflow_id']}}
        
        # Stream workflow execution
        async for state_update in graph_app.astream(initial_state, config):
            # Broadcast state updates
            await broadcast_to_session(session_id, {
                'type': 'workflow_progress',
                'data': {
                    'workflow_id': initial_state['workflow_id'],
                    'state_update': state_update,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        
        # Get final state
        final_state = await graph_app.aget_state(config)
        
        # Broadcast completion
        await broadcast_to_session(session_id, {
            'type': 'workflow_complete',
            'data': {
                'workflow_id': initial_state['workflow_id'],
                'final_state': final_state.values if final_state else {},
                'status': 'completed'
            }
        })
        
        # Update session data
        if session_id in session_data:
            workflow_id = initial_state['workflow_id']
            if workflow_id in session_data[session_id]['active_workflows']:
                session_data[session_id]['active_workflows'][workflow_id]['status'] = 'completed'
                session_data[session_id]['active_workflows'][workflow_id]['completed_at'] = datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Error executing LangGraph workflow: {e}")
        await broadcast_to_session(session_id, {
            'type': 'workflow_error',
            'data': {
                'workflow_id': initial_state['workflow_id'],
                'error': str(e),
                'status': 'failed'
            }
        })

async def handle_agent_message_ws(session_id: str, data: Dict[str, Any]):
    """Handle agent message via WebSocket."""
    agent_id = data.get('agent_id')
    message = data.get('message')
    
    if not agent_id or not message:
        return
    
    # Create request object and process
    request = AgentMessageRequest(
        session_id=session_id,
        agent_id=agent_id,
        message=message
    )
    
    await send_agent_message(request)

async def handle_orchestrator_request_ws(session_id: str, data: Dict[str, Any]):
    """Handle orchestrator request via WebSocket."""
    user_request = data.get('user_request')
    workflow_type = data.get('workflow_type', 'business_development')
    
    if not user_request:
        return
    
    request = OrchestratorRequest(
        session_id=session_id,
        user_request=user_request,
        workflow_type=workflow_type
    )
    
    await start_orchestrator_workflow(request)

def format_agent_response(agent_id: str, result: Dict[str, Any]) -> str:
    """Format agent response for display."""
    if agent_id == 'branding':
        if 'brand_name' in result:
            response = f"🎨 **Brand Design Complete!**\n\n"
            response += f"**Brand Name:** {result.get('brand_name', 'N/A')}\n"
            response += f"**Logo Concept:** {result.get('logo_prompt', 'N/A')}\n"
            response += f"**Color Palette:** {', '.join(result.get('color_palette', []))}\n"
            if result.get('domain_suggestions'):
                response += f"**Domain Suggestions:** {', '.join(result['domain_suggestions'][:3])}\n"
            return response
        else:
            return "I'm analyzing your branding request. What specific industry or style do you prefer?"
    
    elif agent_id == 'market_research':
        if 'market_opportunity_score' in result:
            score = result.get('market_opportunity_score', 0)
            findings = result.get('key_findings', [])
            
            response = f"📊 **Market Research Complete!**\n\n"
            response += f"**Opportunity Score:** {score}/100\n"
            response += f"**Key Findings:**\n"
            for finding in findings[:3]:
                response += f"• {finding}\n"
            response += f"**Strategy:** {result.get('recommended_strategy', 'N/A')}\n"
            return response
        else:
            return "I'm analyzing your market research request. What specific aspects interest you?"
    
    elif agent_id == 'lead_mining':
        if result.get('mining_success', False):
            leads_found = result.get('leads_found', 0)
            qualified_leads = result.get('qualified_leads', [])
            
            response = f"🎯 **Lead Mining Complete!**\n\n"
            response += f"**Leads Found:** {leads_found}\n"
            response += f"**Apollo API Status:** Connected ✅\n"
            
            if qualified_leads:
                response += f"\n**Top Qualified Leads:**\n"
                for i, lead in enumerate(qualified_leads[:3], 1):
                    response += f"{i}. **{lead.first_name} {lead.last_name}** - {lead.job_title}\n"
                    response += f"   Company: {lead.company_name} ({lead.company_size} employees)\n"
                    response += f"   Confidence: {lead.confidence_score:.1f}/1.0\n\n"
            else:
                response += f"**Note:** No leads met qualification criteria. Try broader search terms.\n"
            
            return response
        else:
            return "I'm searching for qualified leads using Apollo API. Please specify your target industry and company size."
    
    elif agent_id == 'social_intelligence':
        if result.get('monitoring_success', False):
            mentions = result.get('social_mentions', [])
            sentiment_summary = result.get('sentiment_summary', {})
            
            response = f"📱 **Social Intelligence Complete!**\n\n"
            response += f"**Mentions Found:** {len(mentions)}\n"
            response += f"**Sentiment:** {sentiment_summary.get('overall_sentiment', 'N/A')}\n"
            
            if mentions:
                response += f"\n**Recent Mentions:**\n"
                for mention in mentions[:3]:
                    response += f"• {mention.title} ({mention.source})\n"
            
            return response
        else:
            return "I'm monitoring social media for brand mentions and engagement opportunities."
    
    elif agent_id == 'content_marketing':
        if result.get('content_success', False):
            content_gaps = result.get('content_gaps', [])
            content_calendar = result.get('content_calendar', {})
            
            response = f"📝 **Content Marketing Strategy Complete!**\n\n"
            response += f"**Content Gaps Identified:** {len(content_gaps)}\n"
            
            if content_gaps:
                response += f"\n**Priority Content Opportunities:**\n"
                for gap in content_gaps[:3]:
                    response += f"• {gap.title} (Priority: {gap.priority})\n"
            
            return response
        else:
            return "I'm analyzing your content marketing needs and creating a strategic plan."
    
    return f"Response from {agent_id}: {str(result)}"

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get session history."""
    if session_id not in session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": session_data[session_id]['message_history'],
        "active_workflows": session_data[session_id]['active_workflows']
    }

@app.get("/api/sessions/{session_id}/leads")
async def get_session_leads(session_id: str):
    """Get all leads found for a session."""
    try:
        # Check if workflow brain has workflow result store
        if hasattr(workflow_brain, 'workflow_result_store'):
            workflow_store = workflow_brain.workflow_result_store
        else:
            return {"leads": [], "message": "No workflow store available"}
        
        # Get all workflow results for this session
        session_workflows = workflow_store.session_workflows.get(session_id, [])
        all_leads = []
        
        for workflow_id in session_workflows:
            workflow_result = workflow_store.results_cache.get(workflow_id)
            if workflow_result and workflow_result.agent_type == "lead_mining_agent":
                # Extract leads from results
                results = workflow_result.results
                qualified_leads = results.get('qualified_leads', [])
                
                # Convert leads to dict format if they're objects
                for lead in qualified_leads:
                    if hasattr(lead, 'to_dict'):
                        all_leads.append(lead.to_dict())
                    else:
                        all_leads.append(lead)
        
        return {
            "session_id": session_id,
            "leads": all_leads,
            "total_leads": len(all_leads),
            "workflows_checked": len(session_workflows)
        }
        
    except Exception as e:
        logger.error(f"Error getting leads for session {session_id}: {e}")
        return {"error": str(e), "leads": []}

# Serve the frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the unified frontend interface."""
    return HTMLResponse(content=get_frontend_html())

def get_frontend_html() -> str:
    """Generate the frontend HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Agent System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
            min-height: 100vh;
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .main-chat {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }
        
        .mode-selector {
            margin-bottom: 20px;
        }
        
        .mode-btn {
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: left;
        }
        
        .mode-btn.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .mode-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
        }
        
        .mode-title {
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        .mode-description {
            font-size: 12px;
            opacity: 0.8;
            line-height: 1.3;
        }
        
        .agent-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
        }
        
        .agent-card.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .agent-icon {
            font-size: 24px;
            margin-bottom: 8px;
            display: block;
        }
        
        .agent-name {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .agent-description {
            font-size: 12px;
            opacity: 0.7;
            line-height: 1.3;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            display: inline-block;
            margin-left: 8px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
            border-radius: 10px;
            margin-bottom: 20px;
            max-height: 500px;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-content {
            background: white;
            padding: 12px 16px;
            border-radius: 15px;
            max-width: 70%;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            white-space: pre-wrap;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .message.orchestrator .message-content {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        
        .message.workflow .message-content {
            background: #fef3c7;
            border: 1px solid #f59e0b;
        }
        
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }
        
        .message-time {
            font-size: 10px;
            opacity: 0.5;
            margin-top: 5px;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .input-area input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 25px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-area input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: scale(1.05);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .header {
            text-align: center;
            margin-bottom: 20px;
            color: white;
        }
        
        .current-mode {
            text-align: center;
            padding: 10px;
            background: #f0f9ff;
            border-radius: 8px;
            margin-bottom: 15px;
            font-weight: 600;
            color: #0369a1;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #667eea;
            font-style: italic;
        }
        
        .loading.show {
            display: block;
        }
        
        .workflow-progress {
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            margin-top: 5px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 3px;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2 style="margin-bottom: 20px; text-align: center; color: #374151;">🤖 System Interface</h2>
            
            <div class="mode-selector">
                <div class="mode-btn active" id="orchestratorMode">
                    <div class="mode-title">🧠 Intelligence Orchestrator</div>
                    <div class="mode-description">Uses LangGraph to coordinate multiple agents with intelligent planning and human approval</div>
                </div>
                
                <div class="mode-btn" id="directMode">
                    <div class="mode-title">🎯 Direct Agent Access</div>
                    <div class="mode-description">Talk directly to individual specialist agents</div>
                </div>
            </div>
            
            <div id="agents-list" style="display: none;">
                <!-- Individual agents will be loaded here -->
            </div>
        </div>
        
        <div class="main-chat">
            <div class="header">
                <h1>🚀 Unified Agent System</h1>
                <p>Choose between intelligent orchestration or direct agent communication</p>
            </div>
            
            <div class="current-mode" id="current-mode">
                🧠 Intelligence Orchestrator Mode - AI coordinates multiple agents intelligently
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Welcome to the Unified Agent System! 
                        
                        <strong>🧠 Intelligence Orchestrator Mode (Active):</strong> I'll analyze your request, plan the best workflow, coordinate multiple agents in parallel, and ask for your approval when needed.
                        
                        <strong>🎯 Direct Agent Mode:</strong> Switch to talk directly with individual specialist agents.
                        
                        How can I help you today?
                        <div class="message-time">Just now</div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                Processing your request...
            </div>
            
            <div class="input-area">
                <input 
                    type="text" 
                    id="message-input" 
                    placeholder="Describe what you'd like to accomplish..."
                    onkeypress="handleKeyPress(event)"
                />
                <button class="send-btn" onclick="sendMessage()" id="send-btn">Send</button>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        let websocket = null;
        let currentMode = 'orchestrator'; // 'orchestrator' or 'direct'
        let selectedAgent = null;
        let agents = {};
        let isProcessing = false;

        // Initialize the application
        async function init() {
            try {
                // Create session
                const sessionResponse = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'demo_user', metadata: {} })
                });
                const sessionData = await sessionResponse.json();
                sessionId = sessionData.session_id;
                
                // Load agents
                await loadAgents();
                
                // Connect WebSocket
                connectWebSocket();
                
                // Setup mode switching
                setupModeButtons();
                
                console.log('Unified Agent System initialized successfully');
            } catch (error) {
                console.error('Failed to initialize:', error);
                addSystemMessage('❌ Failed to connect to the system. Please refresh the page.');
            }
        }

        async function loadAgents() {
            try {
                const response = await fetch('/api/agents');
                const data = await response.json();
                
                const agentsList = document.getElementById('agents-list');
                agentsList.innerHTML = '';
                
                data.agents.forEach(agent => {
                    if (agent.type === 'specialist') { // Only show specialist agents for direct mode
                        agents[agent.agent_id] = agent;
                        
                        const agentCard = document.createElement('div');
                        agentCard.className = 'agent-card';
                        agentCard.onclick = () => selectAgent(agent.agent_id);
                        
                        agentCard.innerHTML = `
                            <div class="agent-icon">${agent.icon}</div>
                            <div class="agent-name">
                                ${agent.name}
                                <span class="status-indicator"></span>
                            </div>
                            <div class="agent-description">${agent.description}</div>
                        `;
                        
                        agentsList.appendChild(agentCard);
                    }
                });
            } catch (error) {
                console.error('Failed to load agents:', error);
            }
        }

        function setupModeButtons() {
            document.getElementById('orchestratorMode').onclick = () => setMode('orchestrator');
            document.getElementById('directMode').onclick = () => setMode('direct');
        }

        function setMode(mode) {
            currentMode = mode;
            
            // Update button states
            document.getElementById('orchestratorMode').classList.toggle('active', mode === 'orchestrator');
            document.getElementById('directMode').classList.toggle('active', mode === 'direct');
            
            // Show/hide agent list
            document.getElementById('agents-list').style.display = mode === 'direct' ? 'block' : 'none';
            
            // Update current mode display and placeholder
            const currentModeEl = document.getElementById('current-mode');
            const messageInput = document.getElementById('message-input');
            
            if (mode === 'orchestrator') {
                currentModeEl.textContent = '🧠 Intelligence Orchestrator Mode - AI coordinates multiple agents intelligently';
                messageInput.placeholder = 'Describe what you\'d like to accomplish...';
                selectedAgent = null;
                // Remove active state from agent cards
                document.querySelectorAll('.agent-card').forEach(card => card.classList.remove('active'));
            } else {
                currentModeEl.textContent = '🎯 Direct Agent Mode - Select an agent to chat with directly';
                messageInput.placeholder = 'Select an agent first...';
                messageInput.disabled = true;
                document.getElementById('send-btn').disabled = true;
            }
            
            addSystemMessage(`Switched to ${mode === 'orchestrator' ? 'Intelligence Orchestrator' : 'Direct Agent'} mode`);
        }

        function selectAgent(agentId) {
            if (currentMode !== 'direct') return;
            
            selectedAgent = agentId;
            
            // Update active agent card
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Update current mode display
            const agent = agents[agentId];
            document.getElementById('current-mode').textContent = 
                `💬 Chatting directly with ${agent.name}`;
            
            // Enable input
            const messageInput = document.getElementById('message-input');
            messageInput.disabled = false;
            messageInput.placeholder = `Message ${agent.name}...`;
            document.getElementById('send-btn').disabled = false;
            messageInput.focus();
            
            addSystemMessage(`Connected to ${agent.name}. Ask me anything about ${agent.capabilities.join(', ')}.`);
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || isProcessing) return;
            
            if (currentMode === 'direct' && !selectedAgent) {
                addSystemMessage('Please select an agent first.');
                return;
            }
            
            input.value = '';
            isProcessing = true;
            
            // Add user message to UI
            addUserMessage(message);
            
            // Show loading
            document.getElementById('loading').classList.add('show');
            document.getElementById('send-btn').disabled = true;
            
            try {
                if (currentMode === 'orchestrator') {
                    // Send to orchestrator via WebSocket
                    if (websocket && websocket.readyState === WebSocket.OPEN) {
                        websocket.send(JSON.stringify({
                            type: 'orchestrator_request',
                            data: {
                                user_request: message,
                                workflow_type: 'business_development'
                            }
                        }));
                    }
                } else {
                    // Send to individual agent
                    const response = await fetch('/api/agent/message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: sessionId,
                            agent_id: selectedAgent,
                            message: message
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        const agent = agents[selectedAgent];
                        addAgentMessage(result.response, agent.icon, agent.name);
                    } else {
                        addSystemMessage(`❌ Error: ${result.error}`);
                    }
                }
            } catch (error) {
                console.error('Failed to send message:', error);
                addSystemMessage('❌ Failed to send message. Please try again.');
            } finally {
                // Hide loading and re-enable
                document.getElementById('loading').classList.remove('show');
                document.getElementById('send-btn').disabled = false;
                isProcessing = false;
            }
        }

        function connectWebSocket() {
            websocket = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
            
            websocket.onopen = () => {
                console.log('Connected to unified system backend');
                addSystemMessage('🟢 Connected to unified system');
            };

            websocket.onmessage = (event) => {
                console.log('WebSocket message:', event.data);
                handleWebSocketMessage(event.data);
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                addSystemMessage('🔴 Connection error. Please check if the backend is running.');
            };

            websocket.onclose = () => {
                console.log('WebSocket connection closed');
                addSystemMessage('🔴 Connection lost. Attempting to reconnect...');
                setTimeout(connectWebSocket, 3000);
            };
        }

        function handleWebSocketMessage(rawData) {
            try {
                const data = JSON.parse(rawData);
                console.log('Parsed message:', data);
                
                switch (data.type) {
                    case 'system_ready':
                        console.log('System ready:', data.data);
                        break;
                    case 'workflow_started':
                        addOrchestratorMessage('🚀 Intelligence orchestrator started analyzing your request...');
                        break;
                    case 'workflow_progress':
                        handleWorkflowProgress(data.data);
                        break;
                    case 'workflow_complete':
                        handleWorkflowComplete(data.data);
                        break;
                    case 'workflow_error':
                        addSystemMessage(`❌ Workflow error: ${data.data.error}`);
                        break;
                    case 'agent_response':
                        if (data.data.success) {
                            const agent = agents[data.data.agent_id];
                            addAgentMessage(data.data.response, agent.icon, agent.name);
                        }
                        break;
                    case 'agent_error':
                        addSystemMessage(`❌ Agent error: ${data.data.error}`);
                        break;
                    default:
                        console.log('Unhandled message type:', data.type);
                }
                
                // Hide loading when any response comes in
                document.getElementById('loading').classList.remove('show');
                document.getElementById('send-btn').disabled = false;
                isProcessing = false;
                
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        }

        function handleWorkflowProgress(data) {
            addWorkflowMessage(`🔄 Workflow Progress: ${JSON.stringify(data.state_update, null, 2)}`);
        }

        function handleWorkflowComplete(data) {
            addOrchestratorMessage('✅ Intelligence orchestrator workflow completed successfully!');
            
            // Show final results if available
            if (data.final_state) {
                const results = formatWorkflowResults(data.final_state);
                if (results) {
                    addWorkflowMessage(results);
                }
            }
        }

        function formatWorkflowResults(finalState) {
            // Format the final workflow results for display
            let results = '📊 **Workflow Results:**\n\n';
            
            if (finalState.final_results) {
                const fr = finalState.final_results;
                if (fr.summary) results += `**Summary:** ${fr.summary}\n\n`;
                if (fr.artifacts) {
                    results += '**Generated Artifacts:**\n';
                    Object.keys(fr.artifacts).forEach(key => {
                        results += `• ${key}: ${fr.artifacts[key]}\n`;
                    });
                    results += '\n';
                }
                if (fr.recommendations && fr.recommendations.length > 0) {
                    results += '**Recommendations:**\n';
                    fr.recommendations.forEach(rec => {
                        results += `• ${rec}\n`;
                    });
                }
            }
            
            return results;
        }

        function addUserMessage(content) {
            addMessageToUI(content, 'user', '👤', 'You');
        }

        function addAgentMessage(content, icon, name) {
            addMessageToUI(content, 'agent', icon, name);
        }

        function addOrchestratorMessage(content) {
            addMessageToUI(content, 'orchestrator', '🧠', 'Intelligence Orchestrator');
        }

        function addWorkflowMessage(content) {
            addMessageToUI(content, 'workflow', '⚙️', 'Workflow');
        }

        function addSystemMessage(content) {
            addMessageToUI(content, 'system', '🤖', 'System');
        }

        function addMessageToUI(content, source, icon, name) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${source}`;
            
            const time = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${icon}</div>
                <div class="message-content">
                    ${content}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function scrollToBottom() {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Initialize when page loads
        window.onload = init;
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Unified Agent System...")
    print("📱 Access the UI at: http://localhost:8000")
    print("🧠 Intelligence Orchestrator: Uses LangGraph for intelligent coordination")
    print("🎯 Direct Agents: Talk to individual specialists directly")
    print("🔑 AI Mode:", "Enabled" if os.getenv('ANTHROPIC_API_KEY') else "Mock Mode")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    ) 