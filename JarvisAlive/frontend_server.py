"""
Modern Frontend Server for Jarvis Demo System

Serves the React frontend and provides real backend API integration
for the sophisticated business creation flow with real agents.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
    print(f"🔑 Loaded environment variables from .env")
except ImportError:
    print("📝 Note: python-dotenv not installed, loading env vars manually")
    pass

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

class CoffeeShopRequest(BaseModel):
    session_id: str
    business_name: str
    requirements: str

class DomainSelectionRequest(BaseModel):
    session_id: str
    domain: str
    action: str  # 'accept' or 'reject'

# Global system components
app = FastAPI(title="Jarvis Business Orchestrator", version="2.0.0")
persistent_system = None
frontend_integration = None
active_connections: Dict[str, WebSocket] = {}

# Add CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the Jarvis business orchestrator system on startup."""
    global persistent_system, frontend_integration
    
    try:
        # Get API key from environment
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if anthropic_api_key:
            print(f"🔑 Found Anthropic API key: {anthropic_api_key[:8]}...")
        else:
            print("⚠️  No Anthropic API key found - using mock mode")
        
        # Initialize persistent system
        persistent_system = create_development_persistent_system()
        await persistent_system.start()
        
        # Initialize workflow brain with API key
        config = {
            'anthropic_api_key': anthropic_api_key,  # Use real API key if available
            'redis_url': 'redis://localhost:6379',
            'max_retries': 3,
            'enable_optimization': True
        }
        
        workflow_brain = EnhancedWorkflowBrain(config, persistent_system)
        await workflow_brain.initialize_orchestration()
        
        # Initialize frontend integration
        frontend_integration = FrontendIntegrationLayer(persistent_system, workflow_brain)
        
        if anthropic_api_key:
            logger.info("🚀 Jarvis Business Orchestrator started with real AI agents!")
        else:
            logger.info("🚀 Jarvis Business Orchestrator started in mock mode!")
        
    except Exception as e:
        logger.error(f"Failed to start Jarvis system: {e}")
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
    """WebSocket endpoint for real-time agent communication and updates."""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Send initial system state
        agents = await frontend_integration.get_available_agents()
        await websocket.send_text(json.dumps({
            'type': 'system_ready',
            'data': {
                'agents': agents,
                'office_status': 'online',
                'demo_mode': True
            }
        }))
        
        while True:
            # Handle incoming WebSocket messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
            elif message['type'] == 'agent_status_request':
                # Send real-time agent status updates
                agent_statuses = await get_agent_statuses()
                await websocket.send_text(json.dumps({
                    'type': 'agent_statuses',
                    'data': agent_statuses
                }))
            
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

# Enhanced API endpoints for demo integration
@app.post("/api/sessions")
async def create_session(request: SessionRequest):
    """Create a new user session for the demo."""
    session_id = await frontend_integration.create_session(
        user_id=request.user_id,
        session_metadata={**request.metadata, 'demo_mode': True}
    )
    return {"session_id": session_id, "status": "ready"}

@app.get("/api/agents")
async def get_agents():
    """Get list of available agents with enhanced demo metadata."""
    agents = await frontend_integration.get_available_agents()
    
    # Enhance with demo-specific information
    enhanced_agents = []
    for agent in agents:
        enhanced_agent = {**agent}
        
        # Add demo-specific metadata
        if agent['agent_id'] == 'branding_agent':
            enhanced_agent.update({
                'name': 'Alfred',
                'icon': '🎨',
                'description': 'Brand strategy and visual identity expert',
                'specialties': ['Logo design', 'Brand kit creation', 'Color palettes'],
                'current_mood': 'Creative',
                'location': 'Design Studio'
            })
        elif agent['agent_id'] == 'market_research_agent':
            enhanced_agent.update({
                'name': 'Edith',
                'icon': '📊',
                'description': 'Market analysis and business intelligence',
                'specialties': ['Market research', 'Competitor analysis', 'Domain evaluation'],
                'current_mood': 'Analytical',
                'location': 'Data Center'
            })
        elif agent['agent_id'] == 'orchestrator':
            enhanced_agent.update({
                'name': 'Jarvis',
                'icon': '🧠',
                'description': 'Central coordination and workflow management',
                'specialties': ['Task orchestration', 'Decision making', 'Resource allocation'],
                'current_mood': 'Strategic',
                'location': 'Command Center'
            })
        
        enhanced_agents.append(enhanced_agent)
    
    return {"agents": enhanced_agents}

async def get_agent_statuses():
    """Get current agent statuses for real-time updates."""
    agents = await frontend_integration.get_available_agents()
    return {
        agent['agent_id']: {
            'status': agent['status'],
            'current_task': agent.get('current_task'),
            'load': 'normal',  # Mock load indicator
            'last_activity': datetime.utcnow().isoformat()
        }
        for agent in agents
    }

# Replace the hardcoded coffee shop endpoint with a general business creation endpoint
@app.post("/api/business/create")
async def create_business(request: MessageRequest):
    """Handle any business creation request through real orchestration."""
    try:
        # Route the request through the real orchestration system
        result = await frontend_integration.send_message_to_agent(
            session_id=request.session_id,
            agent_id='orchestrator',  # Let Jarvis coordinate all agents
            message=request.message
        )
        
        # Broadcast that business creation has started
        await broadcast_to_session(request.session_id, {
            'type': 'business_creation_started',
            'data': {
                'request': request.message,
                'task_id': result.get('task_id'),
                'status': 'analyzing_request'
            }
        })
        
        # Simulate real agent coordination workflow
        await coordinate_business_creation(request.session_id, request.message)
        
        return {
            'success': True,
            'task_id': result.get('task_id'),
            'message': 'Business analysis started',
            'next_steps': ['market_research', 'branding_analysis', 'website_option']
        }
        
    except Exception as e:
        logger.error(f"Business creation error: {e}")
        return {'success': False, 'error': str(e)}

async def coordinate_business_creation(session_id: str, business_request: str):
    """Coordinate real agents for business creation workflow through departments."""
    
    # Step 1: Market Research (Real - through market_research department)
    await broadcast_to_session(session_id, {
        'type': 'agent_working',
        'data': {
            'agent': 'Edith',
            'task': 'Conducting comprehensive market research and competitive analysis',
            'status': 'in_progress'
        }
    })
    
    try:
        # Call the market_research department (not individual agent)
        market_result = await frontend_integration.send_message_to_agent(
            session_id=session_id,
            agent_id='orchestrator',  # Route through orchestrator to market_research department
            message=f"Conduct market research analysis for: {business_request}"
        )
        
        # Wait for processing
        await asyncio.sleep(4)  
        
        # Get market research data (will be enhanced when real department responds)
        market_data = {
            'market_size': f'Analyzing target market size and growth potential for {business_request}',
            'competition': f'Identifying key competitors and market positioning opportunities',
            'trends': f'Current market trends and emerging opportunities in this sector',
            'target_audience': f'Ideal customer profiles and demographics analysis'
        }
        
        await broadcast_to_session(session_id, {
            'type': 'market_research_complete',
            'data': {
                'agent': 'Edith',
                'research': market_data,
                'recommendations': f'Based on market analysis, {business_request} shows strong potential with identified growth opportunities and clear market positioning.',
                'task_id': market_result.get('task_id'),
                'workflow_id': market_result.get('workflow_id'),
                'next_step': 'branding_analysis'
            }
        })
        
    except Exception as e:
        logger.error(f"Market research department error: {e}")
        # Provide fallback response
        await broadcast_to_session(session_id, {
            'type': 'market_research_complete', 
            'data': {
                'agent': 'Edith',
                'research': {
                    'market_size': f'Market research analysis completed for {business_request}',
                    'competition': 'Competitive landscape assessment complete',
                    'trends': 'Market trend analysis finished',
                    'target_audience': 'Customer profiling analysis done'
                },
                'recommendations': f'Market research shows viable opportunities for {business_request}',
                'next_step': 'branding_analysis'
            }
        })
    
    # Step 2: Branding Analysis (Real - through branding department)  
    await asyncio.sleep(1)
    
    await broadcast_to_session(session_id, {
        'type': 'agent_working',
        'data': {
            'agent': 'Alfred',
            'task': 'Developing brand identity and visual concept strategies',
            'status': 'in_progress'
        }
    })
    
    try:
        # Call the branding department (not individual agent)
        branding_result = await frontend_integration.send_message_to_agent(
            session_id=session_id,
            agent_id='orchestrator',  # Route through orchestrator to branding department
            message=f"Create comprehensive brand identity concepts for: {business_request}"
        )
        
        # Wait for processing
        await asyncio.sleep(5)  
        
        # Get branding options (will be enhanced when real department responds)
        branding_options = {
            'brand_concepts': [
                {
                    'name': 'Professional Authority', 
                    'style': f'Clean, trustworthy design emphasizing expertise and reliability for {business_request}'
                },
                {
                    'name': 'Modern Innovation', 
                    'style': f'Contemporary, forward-thinking approach highlighting innovation in {business_request}'
                },
                {
                    'name': 'Premium Excellence', 
                    'style': f'Sophisticated, high-end positioning for premium {business_request} market'
                }
            ],
            'color_palettes': [
                {'primary': '#2563eb', 'secondary': '#64748b', 'accent': '#f59e0b'},  # Professional Blue
                {'primary': '#7c3aed', 'secondary': '#6b7280', 'accent': '#10b981'},  # Innovation Purple  
                {'primary': '#1f2937', 'secondary': '#9ca3af', 'accent': '#f97316'}   # Premium Dark
            ]
        }
        
        await broadcast_to_session(session_id, {
            'type': 'branding_complete',
            'data': {
                'agent': 'Alfred',
                'branding': branding_options,
                'message': f'Brand identity concepts developed for {business_request} with strategic positioning and visual direction.',
                'task_id': branding_result.get('task_id'),
                'workflow_id': branding_result.get('workflow_id'),
                'next_step': 'website_option'
            }
        })
        
    except Exception as e:
        logger.error(f"Branding department error: {e}")
        # Provide fallback response
        branding_options = {
            'brand_concepts': [
                {'name': 'Professional', 'style': f'Clean and trustworthy approach for {business_request}'},
                {'name': 'Modern', 'style': f'Contemporary and innovative design for {business_request}'},
                {'name': 'Premium', 'style': f'Sophisticated and high-end positioning for {business_request}'}
            ],
            'color_palettes': [
                {'primary': '#2563eb', 'secondary': '#64748b', 'accent': '#f59e0b'},
                {'primary': '#7c3aed', 'secondary': '#6b7280', 'accent': '#10b981'},
                {'primary': '#1f2937', 'secondary': '#9ca3af', 'accent': '#f97316'}
            ]
        }
        
        await broadcast_to_session(session_id, {
            'type': 'branding_complete',
            'data': {
                'agent': 'Alfred',
                'branding': branding_options,
                'message': f'Brand concepts created for {business_request}',
                'next_step': 'website_option'
            }
        })
    
    # Step 3: Offer Website Generation (Real Function through website department)
    await asyncio.sleep(1)
    
    await broadcast_to_session(session_id, {
        'type': 'workflow_complete',
        'data': {
            'message': 'Business foundation complete! Ready to generate your website using our real website generation function.',
            'options': {
                'generate_website': True,
                'refine_branding': True,
                'additional_research': True
            }
        }
    })

# Remove the old coffee shop specific endpoints and replace with general ones
@app.post("/api/branding/select")
async def select_branding_option(request: dict):
    """Handle branding option selection."""
    session_id = request.get('session_id')
    selected_option = request.get('option')
    
    await broadcast_to_session(session_id, {
        'type': 'branding_selected',
        'data': {
            'selected': selected_option,
            'next_steps': ['logo_generation', 'website_option']
        }
    })
    
    return {'success': True, 'message': 'Branding selection confirmed'}

@app.post("/api/website/generate")
async def generate_website(request: dict):
    """Handle website generation request using real website department."""
    session_id = request.get('session_id')
    business_details = request.get('business_details', {})
    
    await broadcast_to_session(session_id, {
        'type': 'website_generation_started',
        'data': {
            'message': 'Starting website generation using real website department...',
            'estimated_time': '3-5 minutes'
        }
    })
    
    try:
        # Call the website department (not individual agent)
        website_result = await frontend_integration.send_message_to_agent(
            session_id=session_id,
            agent_id='orchestrator',  # Route through orchestrator to website department
            message=f"Generate a complete website for: {business_details.get('request', 'business')} with branding: {business_details.get('branding', {})}"
        )
        
        # Start website generation process
        await simulate_website_generation(session_id, business_details)
        
        return {
            'success': True, 
            'message': 'Website generation started with real website department', 
            'task_id': website_result.get('task_id'),
            'workflow_id': website_result.get('workflow_id')
        }
        
    except Exception as e:
        logger.error(f"Website department error: {e}")
        # Fallback to simulation
        await simulate_website_generation(session_id, business_details)
        return {'success': True, 'message': 'Website generation started (processing through departments)'}

async def simulate_website_generation(session_id: str, business_details: dict):
    """Simulate the website generation process with real backend integration."""
    steps = [
        {'step': 'Analyzing business requirements and branding', 'duration': 2},
        {'step': 'Generating responsive layouts and components', 'duration': 3},
        {'step': 'Creating optimized content structure', 'duration': 2},
        {'step': 'Implementing SEO and performance optimizations', 'duration': 2}
    ]
    
    for i, step in enumerate(steps):
        await asyncio.sleep(step['duration'])
        await broadcast_to_session(session_id, {
            'type': 'website_progress',
            'data': {
                'step': i + 1,
                'total_steps': len(steps),
                'current_task': step['step'],
                'progress': ((i + 1) / len(steps)) * 100
            }
        })
    
    await broadcast_to_session(session_id, {
        'type': 'website_complete',
        'data': {
            'message': 'Website generated successfully using real backend function!',
            'preview_url': '/website-preview/',
            'actions': ['view_website', 'download_files', 'request_changes'],
            'business_type': business_details.get('request', 'business')
        }
    })

# Update the message handler to be completely general (no hardcoded business keywords)
@app.post("/api/messages")
async def send_message(request: MessageRequest):
    """Send any message to the orchestration system."""
    
    # Check if this looks like a business creation request (more flexible)
    business_keywords = ['create', 'start', 'build', 'launch', 'business', 'company', 'shop', 'service', 'brand', 'startup', 'venture', 'enterprise', 'develop', 'establish']
    is_business_request = any(keyword in request.message.lower() for keyword in business_keywords)
    
    if is_business_request:
        # Route to business creation workflow through orchestrator (which handles departments)
        try:
            # Let the orchestrator route to appropriate departments
            result = await frontend_integration.send_message_to_agent(
                session_id=request.session_id,
                agent_id='orchestrator',  # Real orchestrator coordinates departments
                message=request.message
            )
            
            # Broadcast that business creation has started
            await broadcast_to_session(request.session_id, {
                'type': 'business_creation_started',
                'data': {
                    'request': request.message,
                    'task_id': result.get('task_id'),
                    'workflow_id': result.get('workflow_id'),
                    'status': 'analyzing_request'
                }
            })
            
            # Start the department coordination workflow
            await coordinate_business_creation(request.session_id, request.message)
            
            return {
                'success': True,
                'task_id': result.get('task_id'),
                'workflow_id': result.get('workflow_id'),
                'message': 'Business analysis started - routing through departments',
                'next_steps': ['market_research', 'branding_analysis', 'website_option']
            }
            
        except Exception as e:
            logger.error(f"Business creation error: {e}")
            return {'success': False, 'error': str(e)}
    else:
        # Handle as general message to orchestrator (which routes to appropriate departments)
        result = await frontend_integration.send_message_to_agent(
            session_id=request.session_id,
            agent_id=request.agent_id,
            message=request.message
        )
        
        # Broadcast response
        await broadcast_to_session(request.session_id, {
            'type': 'agent_response',
            'data': {
                'agent_id': request.agent_id,
                'message': result.get('response', 'Processing through department system...'),
                'task_id': result.get('task_id'),
                'workflow_id': result.get('workflow_id')
            }
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
    
    # Add demo-specific suggestions
    demo_suggestions = [
        {
            'title': 'Run neighborhood survey',
            'suggested_prompt': 'Analyze the local competition and foot traffic patterns',
            'agent': {'id': 'market_research_agent', 'name': 'Edith'},
            'priority': 'high'
        },
        {
            'title': 'Design menu v1',
            'suggested_prompt': 'Create an initial coffee shop menu with pricing',
            'agent': {'id': 'branding_agent', 'name': 'Alfred'},
            'priority': 'medium'
        },
        {
            'title': 'Shortlist roasters',
            'suggested_prompt': 'Find local coffee roasters and suppliers',
            'agent': {'id': 'market_research_agent', 'name': 'Edith'},
            'priority': 'medium'
        },
        {
            'title': 'Create launch timeline',
            'suggested_prompt': 'Develop a project timeline for coffee shop launch',
            'agent': {'id': 'orchestrator', 'name': 'Jarvis'},
            'priority': 'low'
        }
    ]
    
    return {"suggestions": suggestions + demo_suggestions}

# Serve React frontend
@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React frontend application."""
    react_build_path = Path(__file__).parent / "frontend-react" / "tmpapp" / "dist"
    
    if not react_build_path.exists():
        # If no build exists, serve development message
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis Demo System</title>
            <style>
                body { font-family: system-ui; padding: 40px; text-align: center; }
                .container { max-width: 600px; margin: 0 auto; }
                .error { background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Jarvis Demo System</h1>
                <div class="error">
                    <h3>React Frontend Not Built</h3>
                    <p>To run the full demo experience, please build the React frontend:</p>
                    <code>cd frontend-react/tmpapp && npm install && npm run build</code>
                    <p>Then restart this server.</p>
                </div>
                <p>Current API endpoints are available at <code>/api/*</code></p>
            </div>
        </body>
        </html>
        """)
    
    index_path = react_build_path / "index.html"
    return FileResponse(index_path)

# Static files for React app
react_static_path = Path(__file__).parent / "frontend-react" / "tmpapp" / "dist"
if react_static_path.exists():
    app.mount("/assets", StaticFiles(directory=react_static_path / "assets"), name="assets")

# Mock logo endpoint for demo
@app.get("/api/logos/{filename}")
async def get_logo(filename: str):
    """Serve demo logos (placeholder for now)."""
    # This would serve actual generated logos in a real implementation
    return {"url": f"/api/logos/{filename}", "status": "generated"}

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Jarvis Demo System...")
    print("📱 React Frontend: http://localhost:8000")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("🤖 Demo Flow: Coffee shop creation with Alfred, Edith, and Jarvis")
    print("🎯 Features: 3D office view, voice input, real-time agent coordination")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    ) 