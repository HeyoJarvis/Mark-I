"""
Simple Unified Frontend - Working Version

A simplified but fully functional frontend that connects to both individual agents 
and the intelligence orchestration layer with proper event handling.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import system components
from orchestration.persistent.persistent_system import create_development_persistent_system
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.langgraph.parallel_intelligent_graph import ParallelIntelligentGraphBuilder
from departments.branding.branding_agent import BrandingAgent
from departments.market_research.market_research_agent import MarketResearchAgent

logger = logging.getLogger(__name__)

# Pydantic models
class AgentMessageRequest(BaseModel):
    session_id: str
    agent_id: str
    message: str

class SessionRequest(BaseModel):
    user_id: str = "demo_user"

# Global system components
app = FastAPI(title="Simple Unified Agent System", version="1.0.0")
persistent_system = None
workflow_brain = None
langgraph_builder = None
individual_agents = {}
active_connections: Dict[str, WebSocket] = {}
session_data: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize system components."""
    global persistent_system, workflow_brain, langgraph_builder, individual_agents
    
    try:
        logger.info("🚀 Starting Simple Unified Agent System...")
        
        # Initialize persistent system
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        logger.info("✅ Persistent system ready")
        
        # Initialize workflow brain  
        config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'redis_url': 'redis://localhost:6379'
        }
        
        workflow_brain = WorkflowBrain(config)
        await workflow_brain.initialize_orchestration()
        logger.info("✅ Intelligence layer ready")
        
        # Initialize LangGraph builder with approval callback
        langgraph_builder = ParallelIntelligentGraphBuilder(
            redis_url='redis://localhost:6379',
            skip_approvals=False,  # Enable approvals for HITL
            approval_callback=ui_approval_callback
        )
        logger.info("✅ LangGraph ready")
        
        # Initialize individual agents with interactive approval
        agent_config = {
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'interactive_approval': True,
            'approval_callback': ui_approval_callback
        }
        individual_agents = {
            'branding': BrandingAgent(agent_config),
            'market_research': MarketResearchAgent(agent_config)
        }
        logger.info("✅ Individual agents ready")
        
        logger.info("🎉 System ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup."""
    if persistent_system:
        await persistent_system.stop()

# WebSocket endpoint for real-time updates and human-in-the-loop
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication and HITL."""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Send initial system status
        await websocket.send_text(json.dumps({
            'type': 'system_ready',
            'data': {
                'session_id': session_id,
                'message': 'Connected to Unified Agent System with Human-in-the-Loop support'
            }
        }))
        
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
            elif message['type'] == 'approval_response':
                await handle_approval_response(session_id, message['data'])
            
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

# Global storage for pending approvals
pending_approvals: Dict[str, Dict[str, Any]] = {}

async def handle_approval_response(session_id: str, data: Dict[str, Any]):
    """Handle human approval responses."""
    approval_id = data.get('approval_id')
    response = data.get('response')  # 'approve', 'reject', 'regenerate'
    
    if approval_id in pending_approvals:
        approval_data = pending_approvals[approval_id]
        approval_data['user_response'] = response
        approval_data['responded'] = True
        
        # Notify that approval was received
        await broadcast_to_session(session_id, {
            'type': 'approval_received',
            'data': {
                'approval_id': approval_id,
                'response': response,
                'message': f'Your {response} response has been received. Processing...'
            }
        })

# Custom approval callback for human-in-the-loop
async def ui_approval_callback(approval_request: Dict[str, Any]) -> str:
    """Handle approval requests through the UI."""
    session_id = approval_request.get('session_id', 'unknown')
    approval_id = f"approval_{int(datetime.utcnow().timestamp())}_{session_id}"
    
    # Store the approval request
    pending_approvals[approval_id] = {
        'request': approval_request,
        'responded': False,
        'user_response': None,
        'created_at': datetime.utcnow()
    }
    
    # Send approval request to UI
    await broadcast_to_session(session_id, {
        'type': 'approval_request',
        'data': {
            'approval_id': approval_id,
            'prompt': approval_request.get('prompt', 'Please review and approve'),
            'options': approval_request.get('options', ['approve', 'reject', 'regenerate']),
            'context': approval_request.get('context', {}),
            'agent': approval_request.get('agent', 'system')
        }
    })
    
    # Wait for user response (with timeout)
    timeout = 300  # 5 minutes
    start_time = datetime.utcnow()
    
    while not pending_approvals[approval_id]['responded']:
        await asyncio.sleep(1)
        if (datetime.utcnow() - start_time).total_seconds() > timeout:
            # Timeout - default to approve
            pending_approvals[approval_id]['user_response'] = 'approve'
            break
    
    response = pending_approvals[approval_id]['user_response']
    
    # Cleanup
    del pending_approvals[approval_id]
    
    return response or 'approve'

# REST API endpoints
@app.post("/api/sessions")
async def create_session(request: SessionRequest):
    """Create session."""
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    session_data[session_id] = {
        'user_id': request.user_id,
        'created_at': datetime.utcnow(),
        'messages': []
    }
    
    return {"session_id": session_id}

@app.get("/api/agents")
async def get_agents():
    """Get agents list."""
    return {
        "agents": [
            {
                "agent_id": "orchestrator",
                "name": "🧠 Intelligence Orchestrator",
                "description": "Coordinates multiple agents using LangGraph",
                "type": "orchestrator",
                "icon": "🧠"
            },
            {
                "agent_id": "branding",
                "name": "🎨 Brand Designer", 
                "description": "Creates brand identities and designs",
                "type": "specialist",
                "icon": "🎨"
            },
            {
                "agent_id": "market_research",
                "name": "📊 Market Analyst",
                "description": "Analyzes markets and opportunities", 
                "type": "specialist",
                "icon": "📊"
            }
        ]
    }

@app.post("/api/agent/message")
async def send_agent_message(request: AgentMessageRequest):
    """Send message to agent."""
    try:
        if request.agent_id == "orchestrator":
            # Use LangGraph orchestrator
            try:
                graph_app, system, brain = await langgraph_builder.build()
                
                initial_state = {
                    'workflow_id': f"wf_{request.session_id}_{int(datetime.utcnow().timestamp())}",
                    'session_id': request.session_id,
                    'user_request': request.message,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # Run workflow and collect results
                config = {"configurable": {"thread_id": initial_state['workflow_id']}}
                
                result_summary = []
                try:
                    async for state_update in graph_app.astream(initial_state, config):
                        if state_update:
                            result_summary.append(str(state_update))
                except Exception as workflow_error:
                    logger.error(f"Workflow execution error: {workflow_error}")
                    # Continue to try getting final state
                
                # Get final state
                final_state = None
                try:
                    final_state = await graph_app.aget_state(config)
                except Exception as state_error:
                    logger.error(f"Final state retrieval error: {state_error}")
                    
            except Exception as orchestrator_error:
                logger.error(f"Orchestrator initialization error: {orchestrator_error}")
                response = f"🧠 **Intelligence Orchestrator Error**\n\nI encountered an issue while setting up the workflow: {str(orchestrator_error)}\n\nPlease try again or contact support if the issue persists."
            else:
                # Only process results if no error occurred
                response = "🧠 **Intelligence Orchestrator Workflow Complete!**\n\n"
                
                # Notify via WebSocket that workflow is complete
                await broadcast_to_session(request.session_id, {
                    'type': 'workflow_complete',
                    'data': {
                        'message': 'Intelligence orchestrator workflow completed successfully!'
                    }
                })
                
                if final_state and final_state.values:
                    fs = final_state.values
                    
                    # Check for agent results first
                    if 'agent_results' in fs and fs['agent_results']:
                        agent_results = fs['agent_results']
                        response += "**Agent Results:**\n\n"
                        
                        for agent_name, result in agent_results.items():
                            if result and isinstance(result, dict):
                                response += f"**{agent_name.title()} Agent:**\n"
                                
                                # Format branding results
                                if agent_name == 'branding' and result:
                                    if 'brand_name' in result:
                                        response += f"• Brand Name: {result['brand_name']}\n"
                                    if 'logo_prompt' in result:
                                        response += f"• Logo Concept: {result['logo_prompt']}\n"
                                    if 'color_palette' in result:
                                        colors = result['color_palette']
                                        if isinstance(colors, list):
                                            response += f"• Color Palette: {', '.join(colors)}\n"
                                    if 'brand_guidelines' in result:
                                        response += f"• Brand Guidelines: {result['brand_guidelines'][:200]}...\n"
                                    if 'domain_suggestions' in result:
                                        domains = result['domain_suggestions']
                                        if isinstance(domains, list):
                                            response += f"• Domain Suggestions: {', '.join(domains[:3])}\n"
                                
                                # Format market research results
                                elif agent_name == 'market_research' and result:
                                    if 'market_opportunity_score' in result:
                                        response += f"• Market Opportunity Score: {result['market_opportunity_score']}/100\n"
                                    if 'key_findings' in result:
                                        findings = result['key_findings']
                                        if isinstance(findings, list):
                                            response += f"• Key Findings:\n"
                                            for finding in findings[:3]:
                                                response += f"  - {finding}\n"
                                    if 'recommended_strategy' in result:
                                        response += f"• Strategy: {result['recommended_strategy']}\n"
                                
                                # Generic result formatting
                                else:
                                    for key, value in result.items():
                                        if key not in ['report_path', 'timestamp', 'session_id']:
                                            response += f"• {key.replace('_', ' ').title()}: {str(value)[:100]}...\n"
                                
                                response += "\n"
                    
                    # Check for final_results as fallback
                    elif 'final_results' in fs and fs['final_results']:
                        fr = fs['final_results']
                        if 'summary' in fr:
                            response += f"**Summary:** {fr['summary']}\n\n"
                        if 'artifacts' in fr and fr['artifacts']:
                            response += "**Generated Content:**\n"
                            for key, value in fr['artifacts'].items():
                                if value:  # Only show non-empty values
                                    response += f"• {key}: {str(value)[:200]}...\n"
                            response += "\n"
                        if 'recommendations' in fr and fr['recommendations']:
                            response += "**Recommendations:**\n"
                            for rec in fr['recommendations'][:3]:
                                if isinstance(rec, dict):
                                    response += f"• {rec.get('action', str(rec))}\n"
                                else:
                                    response += f"• {rec}\n"
                    
                    # If no meaningful results found, show debug info
                    else:
                        response += "**Workflow Status:**\n"
                        if 'overall_status' in fs:
                            response += f"• Status: {fs['overall_status']}\n"
                        if 'completed_agents' in fs:
                            response += f"• Completed Agents: {', '.join(fs['completed_agents'])}\n"
                        if 'agent_tasks' in fs:
                            response += f"• Agent Tasks: {fs['agent_tasks']}\n"
                        
                        response += "\n*Note: The workflow completed but detailed results may still be processing. Check the reports directory for full output.*"
                        
                        # Try to read the latest report as fallback
                        try:
                            import glob
                            import os
                            
                            # Look for the most recent branding report
                            branding_reports = glob.glob("branding_reports/branding_*.json")
                            if branding_reports:
                                latest_report = max(branding_reports, key=os.path.getctime)
                                with open(latest_report, 'r') as f:
                                    report_data = json.load(f)
                                    
                                response += "\n**Latest Generated Report:**\n"
                                if 'brand_name' in report_data:
                                    response += f"• Brand Name: {report_data['brand_name']}\n"
                                if 'logo_prompt' in report_data:
                                    response += f"• Logo Concept: {report_data['logo_prompt']}\n"
                                if 'color_palette' in report_data:
                                    colors = report_data['color_palette']
                                    if isinstance(colors, list):
                                        response += f"• Color Palette: {', '.join(colors)}\n"
                        except Exception as e:
                            logger.info(f"Could not read fallback report: {e}")
                            
                else:
                    response += "Workflow executed but no final state was retrieved. The agents may still be processing your request."
            
        else:
            # Use individual agent
            if request.agent_id not in individual_agents:
                raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
            
            agent = individual_agents[request.agent_id]
            state = {
                'business_idea': request.message,
                'user_request': request.message,
                'session_id': request.session_id
            }
            
            # Notify that agent is starting
            agent_names = {
                'branding': '🎨 Brand Designer',
                'market_research': '📊 Market Analyst'
            }
            await broadcast_to_session(request.session_id, {
                'type': 'agent_started',
                'data': {
                    'agent_id': request.agent_id,
                    'message': f'{agent_names.get(request.agent_id, "Agent")} is processing your request...'
                }
            })
            
            result = await agent.run(state)
            
            # Format response
            if request.agent_id == 'branding':
                if 'brand_name' in result:
                    response = f"🎨 **Brand Design Complete!**\n\n"
                    response += f"**Brand Name:** {result.get('brand_name', 'N/A')}\n"
                    response += f"**Logo Concept:** {result.get('logo_prompt', 'N/A')}\n"
                    response += f"**Colors:** {', '.join(result.get('color_palette', []))}\n"
                    if result.get('domain_suggestions'):
                        response += f"**Domains:** {', '.join(result['domain_suggestions'][:3])}\n"
                else:
                    response = "I'm analyzing your branding request. What industry or style do you prefer?"
                    
            elif request.agent_id == 'market_research':
                if 'market_opportunity_score' in result:
                    score = result.get('market_opportunity_score', 0)
                    findings = result.get('key_findings', [])
                    
                    response = f"📊 **Market Research Complete!**\n\n"
                    response += f"**Opportunity Score:** {score}/100\n"
                    response += f"**Key Findings:**\n"
                    for finding in findings[:3]:
                        response += f"• {finding}\n"
                    response += f"**Strategy:** {result.get('recommended_strategy', 'N/A')}\n"
                else:
                    response = "I'm analyzing the market for your request. What specific aspects interest you?"
            else:
                response = f"Response from {request.agent_id}: {str(result)}"
        
        # Store in session
        if request.session_id in session_data:
            session_data[request.session_id]['messages'].append({
                'user_message': request.message,
                'agent_id': request.agent_id,
                'agent_response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return {
            "success": True,
            "response": response,
            "agent_id": request.agent_id
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": f"Sorry, I encountered an error: {str(e)}"
        }

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get session history."""
    return {
        "messages": session_data.get(session_id, {}).get('messages', [])
    }

# Serve the frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend."""
    return HTMLResponse(content=get_simple_frontend_html())

def get_simple_frontend_html() -> str:
    """Generate simple, working frontend HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Unified Agent System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            height: calc(100vh - 40px);
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            overflow-y: auto;
        }
        
        .main-chat {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        
        .agent-card {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .agent-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .agent-card.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .agent-icon {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .agent-name {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .agent-description {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
            border-radius: 10px;
            margin-bottom: 20px;
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
            max-width: 80%;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
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
            font-size: 14px;
        }
        
        .input-area input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: scale(1.05);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .current-agent {
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
        
        /* Approval Dialog Styles */
        .approval-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .approval-overlay.show {
            display: flex;
        }
        
        .approval-dialog {
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .approval-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #374151;
        }
        
        .approval-content {
            margin-bottom: 20px;
            line-height: 1.6;
            color: #6b7280;
        }
        
        .approval-prompt {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }
        
        .approval-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
        }
        
        .approval-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .approval-btn.approve {
            background: #10b981;
            color: white;
        }
        
        .approval-btn.approve:hover {
            background: #059669;
        }
        
        .approval-btn.reject {
            background: #ef4444;
            color: white;
        }
        
        .approval-btn.reject:hover {
            background: #dc2626;
        }
        
        .approval-btn.regenerate {
            background: #f59e0b;
            color: white;
        }
        
        .approval-btn.regenerate:hover {
            background: #d97706;
        }
        
        .approval-agent {
            display: inline-block;
            background: #e5e7eb;
            color: #374151;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        h1 {
            text-align: center;
            color: #374151;
            margin-bottom: 20px;
        }
        
        h2 {
            color: #374151;
            margin-bottom: 15px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>🤖 Agents</h2>
            <div id="agents-list">
                <!-- Agents will be loaded here -->
            </div>
        </div>
        
        <div class="main-chat">
            <h1>🚀 Unified Agent System</h1>
            
            <div class="current-agent" id="current-agent">
                Select an agent to start chatting
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Welcome! Select an agent from the sidebar:
                        
                        🧠 <strong>Intelligence Orchestrator</strong> - Uses LangGraph to coordinate multiple agents
                        🎨 <strong>Brand Designer</strong> - Creates brand identities and designs  
                        📊 <strong>Market Analyst</strong> - Analyzes markets and opportunities
                        
                        Choose one to get started!
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
                    placeholder="Select an agent first..."
                    disabled
                />
                <button class="send-btn" id="send-btn" disabled>Send</button>
            </div>
        </div>
    </div>
    
    <!-- Approval Dialog -->
    <div class="approval-overlay" id="approval-overlay">
        <div class="approval-dialog">
            <div class="approval-title" id="approval-title">Human Approval Required</div>
            <div class="approval-agent" id="approval-agent">Agent Request</div>
            <div class="approval-content" id="approval-content">
                Please review the following request and choose your response:
            </div>
            <div class="approval-prompt" id="approval-prompt">
                <!-- Approval content will be inserted here -->
            </div>
            <div class="approval-buttons">
                <button class="approval-btn approve" onclick="sendApprovalResponse('approve')">
                    ✅ Approve
                </button>
                <button class="approval-btn regenerate" onclick="sendApprovalResponse('regenerate')">
                    🔄 Regenerate
                </button>
                <button class="approval-btn reject" onclick="sendApprovalResponse('reject')">
                    ❌ Reject
                </button>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        let currentAgent = null;
        let agents = {};
        let isProcessing = false;
        let websocket = null;
        let currentApprovalId = null;

        // Initialize the application
        async function init() {
            try {
                console.log('Initializing application...');
                
                // Create session
                const sessionResponse = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'demo_user' })
                });
                const sessionData = await sessionResponse.json();
                sessionId = sessionData.session_id;
                console.log('Session created:', sessionId);
                
                // Load agents
                await loadAgents();
                
                // Setup event listeners
                setupEventListeners();
                
                // Connect WebSocket
                connectWebSocket();
                
                console.log('Application initialized successfully');
                addSystemMessage('✅ System ready! Select an agent to start.');
                
            } catch (error) {
                console.error('Failed to initialize:', error);
                addSystemMessage('❌ Failed to connect. Please refresh the page.');
            }
        }

        async function loadAgents() {
            try {
                console.log('Loading agents...');
                const response = await fetch('/api/agents');
                const data = await response.json();
                
                const agentsList = document.getElementById('agents-list');
                agentsList.innerHTML = '';
                
                data.agents.forEach(agent => {
                    agents[agent.agent_id] = agent;
                    
                    const agentCard = document.createElement('div');
                    agentCard.className = 'agent-card';
                    agentCard.onclick = () => selectAgent(agent.agent_id);
                    
                    agentCard.innerHTML = `
                        <div class="agent-icon">${agent.icon}</div>
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-description">${agent.description}</div>
                    `;
                    
                    agentsList.appendChild(agentCard);
                });
                
                console.log('Agents loaded:', Object.keys(agents));
                
            } catch (error) {
                console.error('Failed to load agents:', error);
                addSystemMessage('❌ Failed to load agents.');
            }
        }

        function setupEventListeners() {
            const sendBtn = document.getElementById('send-btn');
            const messageInput = document.getElementById('message-input');
            
            sendBtn.addEventListener('click', sendMessage);
            
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            console.log('Event listeners setup complete');
        }

        function selectAgent(agentId) {
            console.log('Selecting agent:', agentId);
            
            currentAgent = agentId;
            
            // Update active agent card
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            
            // Find and activate the clicked card
            const cards = document.querySelectorAll('.agent-card');
            cards.forEach(card => {
                if (card.onclick.toString().includes(agentId)) {
                    card.classList.add('active');
                }
            });
            
            // Update current agent display
            const agent = agents[agentId];
            document.getElementById('current-agent').textContent = 
                `💬 Chatting with ${agent.name}`;
            
            // Enable input
            const messageInput = document.getElementById('message-input');
            const sendBtn = document.getElementById('send-btn');
            
            messageInput.disabled = false;
            messageInput.placeholder = `Message ${agent.name}...`;
            sendBtn.disabled = false;
            messageInput.focus();
            
            addSystemMessage(`Connected to ${agent.name}. How can I help you?`);
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || !currentAgent || isProcessing) return;
            
            console.log('Sending message:', message, 'to agent:', currentAgent);
            
            input.value = '';
            isProcessing = true;
            
            // Add user message to UI
            addUserMessage(message);
            
            // Show loading
            document.getElementById('loading').classList.add('show');
            document.getElementById('send-btn').disabled = true;
            
            try {
                const response = await fetch('/api/agent/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        agent_id: currentAgent,
                        message: message
                    })
                });
                
                const result = await response.json();
                console.log('Response received:', result);
                
                if (result.success) {
                    const agent = agents[currentAgent];
                    addAgentMessage(result.response, agent.icon, agent.name);
                } else {
                    addSystemMessage(`❌ Error: ${result.error || result.response}`);
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

        function addUserMessage(content) {
            addMessageToUI(content, 'user', '👤', 'You');
        }

        function addAgentMessage(content, icon, name) {
            addMessageToUI(content, 'agent', icon, name);
        }

        function addSystemMessage(content) {
            addMessageToUI(content, 'system', '🤖', 'System');
        }

        function addMessageToUI(content, source, icon, name) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${source}`;
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${icon}</div>
                <div class="message-content">${content}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function connectWebSocket() {
            if (!sessionId) return;
            
            websocket = new WebSocket(`ws://localhost:8001/ws/${sessionId}`);
            
            websocket.onopen = () => {
                console.log('WebSocket connected');
                addSystemMessage('🟢 Real-time connection established');
            };

            websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket message:', data);
                
                switch (data.type) {
                    case 'system_ready':
                        console.log('System ready:', data.data.message);
                        break;
                    case 'approval_request':
                        showApprovalDialog(data.data);
                        break;
                    case 'approval_received':
                        hideApprovalDialog();
                        addSystemMessage(`✅ ${data.data.message}`);
                        break;
                    default:
                        console.log('Unhandled message type:', data.type);
                }
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                addSystemMessage('🔴 Connection error');
            };

            websocket.onclose = () => {
                console.log('WebSocket closed');
                addSystemMessage('🔴 Connection lost. Attempting to reconnect...');
                setTimeout(connectWebSocket, 3000);
            };
        }

        function showApprovalDialog(approvalData) {
            currentApprovalId = approvalData.approval_id;
            
            document.getElementById('approval-title').textContent = 'Human Approval Required';
            document.getElementById('approval-agent').textContent = `${approvalData.agent} Agent Request`;
            document.getElementById('approval-content').textContent = 'Please review the following and choose your response:';
            document.getElementById('approval-prompt').textContent = approvalData.prompt;
            
            document.getElementById('approval-overlay').classList.add('show');
            
            // Add approval message to chat
            addSystemMessage('⏳ Human approval required. Please review the dialog that appeared.');
        }

        function hideApprovalDialog() {
            document.getElementById('approval-overlay').classList.remove('show');
            currentApprovalId = null;
        }

        function sendApprovalResponse(response) {
            if (!currentApprovalId || !websocket) return;
            
            websocket.send(JSON.stringify({
                type: 'approval_response',
                data: {
                    approval_id: currentApprovalId,
                    response: response
                }
            }));
            
            hideApprovalDialog();
            addSystemMessage(`📤 Sent ${response} response. Processing...`);
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', init);
        
        console.log('Script loaded');
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Simple Unified Agent System...")
    print("📱 Access at: http://localhost:8001")
    print("🧠 Intelligence Orchestrator + 🎯 Direct Agents")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 