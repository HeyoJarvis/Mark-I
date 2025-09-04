"""
Simple Frontend Server for Concurrent Agent System

Provides a web interface to demonstrate the concurrent agent orchestration
with direct agent communication, intelligent suggestions, and real-time updates.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import our system components
from orchestration.persistent.persistent_system import create_development_persistent_system
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.persistent.enhanced_workflow_brain import EnhancedWorkflowBrain
from orchestration.frontend_integration import FrontendIntegrationLayer

logger = logging.getLogger(__name__)

# Pydantic models for API
class MessageRequest(BaseModel):
    session_id: str
    agent_id: str
    message: str

class SessionRequest(BaseModel):
    user_id: str
    metadata: Dict[str, Any] = {}

class SuggestionRequest(BaseModel):
    session_id: str
    max_suggestions: int = 5

# Global system components
app = FastAPI(title="Concurrent Agent System", version="1.0.0")
persistent_system = None
frontend_integration = None
active_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the concurrent agent system on startup."""
    global persistent_system, frontend_integration
    
    try:
        # Initialize persistent system
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        
        # Initialize workflow brain
        config = {
            'anthropic_api_key': None,  # Will use mock mode
            'redis_url': 'redis://localhost:6379',
            'max_retries': 3,
            'enable_optimization': True
        }
        
        workflow_brain = EnhancedWorkflowBrain(config, persistent_system)
        await workflow_brain.initialize_orchestration()
        
        # Initialize frontend integration
        frontend_integration = FrontendIntegrationLayer(persistent_system, workflow_brain)
        
        logger.info("Frontend server started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start frontend server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global persistent_system
    if persistent_system:
        await persistent_system.stop()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Send initial agent list
        agents = await frontend_integration.get_available_agents()
        await websocket.send_text(json.dumps({
            'type': 'agents_update',
            'data': agents
        }))
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
            
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
    session_id = await frontend_integration.create_session(
        user_id=request.user_id,
        session_metadata=request.metadata
    )
    return {"session_id": session_id}

@app.get("/api/agents")
async def get_agents():
    """Get list of available agents."""
    agents = await frontend_integration.get_available_agents()
    return {"agents": agents}

@app.post("/api/messages")
async def send_message(request: MessageRequest):
    """Send a message to an agent."""
    result = await frontend_integration.send_message_to_agent(
        session_id=request.session_id,
        agent_id=request.agent_id,
        message=request.message
    )
    
    # Broadcast message update to WebSocket
    await broadcast_to_session(request.session_id, {
        'type': 'message_sent',
        'data': result
    })
    
    return result

@app.get("/api/sessions/{session_id}/history")
async def get_history(session_id: str, limit: int = 50):
    """Get chat history for a session."""
    history = await frontend_integration.get_session_history(session_id, limit)
    return {"history": history}

@app.post("/api/suggestions")
async def get_suggestions(request: SuggestionRequest):
    """Get intelligent workflow suggestions."""
    suggestions = await frontend_integration.get_workflow_suggestions(
        session_id=request.session_id,
        max_suggestions=request.max_suggestions
    )
    return {"suggestions": suggestions}

# Serve the frontend HTML
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend interface."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Concurrent Agent System</title>
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
            grid-template-columns: 300px 1fr;
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
            display: inline-block;
            margin-left: 8px;
        }
        
        .status-available { background: #10b981; }
        .status-busy { background: #f59e0b; }
        .status-offline { background: #ef4444; }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
            border-radius: 10px;
            margin-bottom: 20px;
            max-height: 400px;
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
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 70%;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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
            font-size: 14px;
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
        
        .send-btn:hover {
            transform: scale(1.05);
        }
        
        .suggestions {
            background: #fef3c7;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            display: none;
        }
        
        .suggestions.show {
            display: block;
        }
        
        .suggestion-item {
            background: white;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .suggestion-item:hover {
            background: #f3f4f6;
        }
        
        .suggestion-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .suggestion-prompt {
            font-size: 12px;
            color: #6b7280;
            font-style: italic;
        }
        
        .header {
            text-align: center;
            margin-bottom: 20px;
            color: white;
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
        
        .suggest-btn {
            width: 100%;
            padding: 10px;
            background: #059669;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 15px;
        }
        
        .suggest-btn:hover {
            background: #047857;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2 style="margin-bottom: 20px; text-align: center; color: #374151;">🤖 Agents</h2>
            <div id="agents-list">
                <!-- Agents will be loaded here -->
            </div>
            <button class="suggest-btn" onclick="getSuggestions()">💡 Get Suggestions</button>
        </div>
        
        <div class="main-chat">
            <div class="header">
                <h1>🚀 Concurrent Agent System</h1>
                <p>Chat with agents individually or let the orchestrator coordinate them</p>
            </div>
            
            <div class="current-agent" id="current-agent">
                Select an agent to start chatting
            </div>
            
            <div class="suggestions" id="suggestions">
                <!-- Suggestions will appear here -->
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Welcome! Select an agent from the sidebar to start chatting. You can talk directly to individual agents or use the orchestrator for intelligent coordination.
                        <div class="message-time">Just now</div>
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <input 
                    type="text" 
                    id="message-input" 
                    placeholder="Type your message..." 
                    onkeypress="handleKeyPress(event)"
                    disabled
                />
                <button class="send-btn" onclick="sendMessage()" id="send-btn" disabled>Send</button>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        let currentAgent = null;
        let websocket = null;
        let agents = {};

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
                
                console.log('Application initialized successfully');
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
                    agents[agent.agent_id] = agent;
                    
                    const agentCard = document.createElement('div');
                    agentCard.className = 'agent-card';
                    agentCard.onclick = () => selectAgent(agent.agent_id);
                    
                    const statusClass = `status-${agent.status}`;
                    
                    agentCard.innerHTML = `
                        <div class="agent-icon">${agent.icon}</div>
                        <div class="agent-name">
                            ${agent.name}
                            <span class="status-indicator ${statusClass}"></span>
                        </div>
                        <div class="agent-description">${agent.description}</div>
                    `;
                    
                    agentsList.appendChild(agentCard);
                });
            } catch (error) {
                console.error('Failed to load agents:', error);
            }
        }

        function selectAgent(agentId) {
            currentAgent = agentId;
            
            // Update active agent card
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Update current agent display
            const agent = agents[agentId];
            document.getElementById('current-agent').textContent = 
                `💬 Chatting with ${agent.name} ${agent.icon}`;
            
            // Enable input
            document.getElementById('message-input').disabled = false;
            document.getElementById('send-btn').disabled = false;
            document.getElementById('message-input').focus();
            
            // Load chat history
            loadChatHistory();
        }

        async function loadChatHistory() {
            try {
                const response = await fetch(`/api/sessions/${sessionId}/history`);
                const data = await response.json();
                
                const messagesContainer = document.getElementById('chat-messages');
                messagesContainer.innerHTML = '';
                
                data.history.forEach(message => {
                    addMessageToUI(message);
                });
                
                scrollToBottom();
            } catch (error) {
                console.error('Failed to load chat history:', error);
            }
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || !currentAgent) return;
            
            input.value = '';
            
            // Add user message to UI immediately
            addUserMessage(message);
            
            try {
                const response = await fetch('/api/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        agent_id: currentAgent,
                        message: message
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    const agent = agents[currentAgent];
                    addAgentMessage(`I'm working on your request: ${message}`, agent);
                } else {
                    addSystemMessage(`❌ Error: ${result.error}`);
                }
            } catch (error) {
                console.error('Failed to send message:', error);
                addSystemMessage('❌ Failed to send message. Please try again.');
            }
        }

        function addUserMessage(content) {
            addMessageToUI({
                content: content,
                source: 'user',
                timestamp: new Date().toISOString()
            });
        }

        function addAgentMessage(content, agent) {
            addMessageToUI({
                content: content,
                source: 'agent',
                agent_id: agent.agent_id,
                timestamp: new Date().toISOString()
            });
        }

        function addSystemMessage(content) {
            addMessageToUI({
                content: content,
                source: 'system',
                timestamp: new Date().toISOString()
            });
        }

        function addMessageToUI(message) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.source}`;
            
            let avatar = '🤖';
            let name = 'System';
            
            if (message.source === 'user') {
                avatar = '👤';
                name = 'You';
            } else if (message.agent_id && agents[message.agent_id]) {
                avatar = agents[message.agent_id].icon;
                name = agents[message.agent_id].name;
            }
            
            const time = new Date(message.timestamp).toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    ${message.content}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        async function getSuggestions() {
            try {
                const response = await fetch('/api/suggestions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        max_suggestions: 5
                    })
                });
                
                const data = await response.json();
                showSuggestions(data.suggestions);
            } catch (error) {
                console.error('Failed to get suggestions:', error);
                addSystemMessage('❌ Failed to get suggestions. Please try again.');
            }
        }

        function showSuggestions(suggestions) {
            const suggestionsDiv = document.getElementById('suggestions');
            
            if (!suggestions || suggestions.length === 0) {
                suggestionsDiv.innerHTML = '<p>💡 No suggestions available yet. Try completing some tasks first!</p>';
                suggestionsDiv.classList.add('show');
                return;
            }
            
            suggestionsDiv.innerHTML = '<h3>💡 Suggested Next Steps:</h3>';
            
            suggestions.forEach(suggestion => {
                const suggestionDiv = document.createElement('div');
                suggestionDiv.className = 'suggestion-item';
                suggestionDiv.onclick = () => useSuggestion(suggestion);
                
                suggestionDiv.innerHTML = `
                    <div class="suggestion-title">${suggestion.title}</div>
                    <div class="suggestion-prompt">"${suggestion.suggested_prompt}"</div>
                `;
                
                suggestionsDiv.appendChild(suggestionDiv);
            });
            
            suggestionsDiv.classList.add('show');
        }

        function useSuggestion(suggestion) {
            document.getElementById('message-input').value = suggestion.suggested_prompt;
            document.getElementById('suggestions').classList.remove('show');
            
            // Auto-select appropriate agent if available
            if (suggestion.agent && agents[suggestion.agent.id]) {
                selectAgent(suggestion.agent.id);
            }
        }

        function connectWebSocket() {
            websocket = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'agents_update') {
                    console.log('Agents updated:', data.data);
                } else if (data.type === 'message_sent') {
                    console.log('Message sent:', data.data);
                }
            };
            
            websocket.onclose = function() {
                console.log('WebSocket closed, attempting to reconnect...');
                setTimeout(connectWebSocket, 3000);
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
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
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Concurrent Agent System Frontend Server...")
    print("📱 Access the UI at: http://localhost:8000")
    print("🤖 Agents: Branding Agent, Market Research Agent, Business Advisor")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    ) 