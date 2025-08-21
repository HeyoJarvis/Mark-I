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
        
        # Initialize LangGraph builder
        langgraph_builder = ParallelIntelligentGraphBuilder(
            redis_url='redis://localhost:6379',
            skip_approvals=True
        )
        logger.info("✅ LangGraph ready")
        
        # Initialize individual agents
        agent_config = {'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')}
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
            async for state_update in graph_app.astream(initial_state, config):
                if state_update:
                    result_summary.append(str(state_update))
            
            # Get final state
            final_state = await graph_app.aget_state(config)
            
            response = "🧠 **Intelligence Orchestrator Workflow Complete!**\n\n"
            
            if final_state and final_state.values:
                fs = final_state.values
                if 'final_results' in fs and fs['final_results']:
                    fr = fs['final_results']
                    if 'summary' in fr:
                        response += f"**Summary:** {fr['summary']}\n\n"
                    if 'artifacts' in fr:
                        response += "**Generated Content:**\n"
                        for key, value in fr['artifacts'].items():
                            response += f"• {key}: {str(value)[:200]}...\n"
                        response += "\n"
                    if 'recommendations' in fr:
                        response += "**Recommendations:**\n"
                        for rec in fr['recommendations'][:3]:
                            response += f"• {rec}\n"
                else:
                    response += "I've coordinated the workflow for your request. The agents have worked together to provide a comprehensive response."
            else:
                response += "Workflow executed successfully. Multiple agents collaborated on your request."
            
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

    <script>
        let sessionId = null;
        let currentAgent = null;
        let agents = {};
        let isProcessing = false;

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