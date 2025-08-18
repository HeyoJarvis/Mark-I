#!/usr/bin/env python3
"""
Simple Frontend Demo for Concurrent Agent System

A minimal working frontend that demonstrates:
- Agent listing and selection
- Direct agent communication
- Real AI responses with Anthropic API
- Clean web interface
"""

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Simple agent system integration
import os
import sys
sys.path.append('/home/sdalal/test/ProjectMarmalade/JarvisAlive')

from departments.branding.branding_agent import BrandingAgent
from departments.market_research.market_research_agent import MarketResearchAgent

# Initialize FastAPI
app = FastAPI(title="Simple Agent Demo", version="1.0.0")

# Global agents
branding_agent = None
market_agent = None

class MessageRequest(BaseModel):
    agent_id: str
    message: str

@app.on_event("startup")
async def startup():
    """Initialize agents with API key."""
    global branding_agent, market_agent
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    config = {'anthropic_api_key': api_key} if api_key else {}
    
    branding_agent = BrandingAgent(config)
    market_agent = MarketResearchAgent(config)
    
    print("🚀 Simple agent demo started!")
    print("📱 Access at: http://localhost:8000")

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the simple frontend interface."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Concurrent Agent System Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
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
        
        .send-btn:hover {
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
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2 style="margin-bottom: 20px; text-align: center; color: #374151;">🤖 Agents</h2>
            
            <div class="agent-card" onclick="selectAgent('branding_agent', '🎨', 'Brand Designer')">
                <div class="agent-icon">🎨</div>
                <div class="agent-name">
                    Brand Designer
                    <span class="status-indicator"></span>
                </div>
                <div class="agent-description">Creates brand identities, logos, and visual designs using AI</div>
            </div>
            
            <div class="agent-card" onclick="selectAgent('market_research_agent', '📊', 'Market Analyst')">
                <div class="agent-icon">📊</div>
                <div class="agent-name">
                    Market Analyst
                    <span class="status-indicator"></span>
                </div>
                <div class="agent-description">Analyzes markets, competition, and business opportunities</div>
            </div>
        </div>
        
        <div class="main-chat">
            <div class="header">
                <h1>🚀 Concurrent Agent System</h1>
                <p>Direct AI-powered agent communication</p>
            </div>
            
            <div class="current-agent" id="current-agent">
                Select an agent to start chatting
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Welcome! Select an agent from the sidebar to start chatting. Each agent is powered by AI and can provide real insights for your business.
                        <div class="message-time">Just now</div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                AI is thinking...
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
        let currentAgent = null;
        let currentAgentName = '';
        let currentAgentIcon = '';

        function selectAgent(agentId, icon, name) {
            currentAgent = agentId;
            currentAgentName = name;
            currentAgentIcon = icon;
            
            // Update active agent card
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Update current agent display
            document.getElementById('current-agent').textContent = 
                `💬 Chatting with ${name} ${icon}`;
            
            // Enable input
            document.getElementById('message-input').disabled = false;
            document.getElementById('send-btn').disabled = false;
            document.getElementById('message-input').focus();
            
            // Add selection message
            addSystemMessage(`Connected to ${name}. How can I help you today?`);
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || !currentAgent) return;
            
            input.value = '';
            
            // Add user message to UI
            addUserMessage(message);
            
            // Show loading
            document.getElementById('loading').classList.add('show');
            document.getElementById('send-btn').disabled = true;
            
            try {
                const response = await fetch('/api/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_id: currentAgent,
                        message: message
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    addAgentMessage(result.response, currentAgentIcon, currentAgentName);
                } else {
                    addSystemMessage(`❌ Error: ${result.error}`);
                }
            } catch (error) {
                console.error('Failed to send message:', error);
                addSystemMessage('❌ Failed to send message. Please try again.');
            } finally {
                // Hide loading
                document.getElementById('loading').classList.remove('show');
                document.getElementById('send-btn').disabled = false;
                document.getElementById('message-input').focus();
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
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function scrollToBottom() {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    </script>
</body>
</html>
    """)

@app.post("/api/message")
async def send_message(request: MessageRequest):
    """Send message to an agent and get AI response."""
    try:
        agent_id = request.agent_id
        message = request.message
        
        print(f"📨 Message to {agent_id}: {message}")
        
        # Route to appropriate agent
        if agent_id == 'branding_agent':
            # Create state for branding agent
            state = {
                'business_idea': message,
                'user_request': message,
                'session_id': 'demo_session'
            }
            
            # Run branding agent
            result = await branding_agent.run(state)
            
            # Format response
            if 'brand_name' in result:
                response = f"🎨 **Brand Design Complete!**\n\n"
                response += f"**Brand Name:** {result.get('brand_name', 'N/A')}\n\n"
                response += f"**Logo Concept:** {result.get('logo_prompt', 'N/A')}\n\n"
                response += f"**Color Palette:** {', '.join(result.get('color_palette', []))}\n\n"
                if result.get('domain_suggestions'):
                    response += f"**Domain Suggestions:** {', '.join(result['domain_suggestions'][:3])}\n\n"
                response += "Your brand identity is ready! Would you like me to refine any aspect?"
            else:
                response = f"I've analyzed your branding request: {message}\n\nLet me create a comprehensive brand identity for you. What specific industry or style preferences do you have?"
                
        elif agent_id == 'market_research_agent':
            # Create state for market research agent  
            state = {
                'business_idea': message,
                'user_request': message,
                'session_id': 'demo_session'
            }
            
            # Run market research agent
            result = await market_agent.run(state)
            
            # Format response
            if 'market_opportunity_score' in result:
                score = result.get('market_opportunity_score', 0)
                findings = result.get('key_findings', [])
                
                response = f"📊 **Market Research Complete!**\n\n"
                response += f"**Opportunity Score:** {score}/100\n\n"
                response += f"**Key Findings:**\n"
                for finding in findings[:3]:
                    response += f"• {finding}\n"
                response += f"\n**Recommended Strategy:** {result.get('recommended_strategy', 'N/A')}\n\n"
                response += "Would you like me to dive deeper into any specific aspect of the market analysis?"
            else:
                response = f"I've started analyzing the market for: {message}\n\nI'll research market opportunities, competition, and strategic recommendations. What specific market aspects interest you most?"
        
        else:
            response = f"I'm the {agent_id} agent. I received your message: {message}\n\nHow can I help you with this request?"
        
        print(f"✅ Response from {agent_id}: {response[:100]}...")
        
        return {
            "success": True,
            "response": response,
            "agent_id": agent_id
        }
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "response": "Sorry, I encountered an error processing your request. Please try again."
        }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Simple Agent Demo Server...")
    print("📱 Access the UI at: http://localhost:8000")
    print("🤖 Available Agents: Brand Designer, Market Analyst")
    print("🔑 AI Mode:", "Enabled" if os.getenv('ANTHROPIC_API_KEY') else "Mock Mode")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 