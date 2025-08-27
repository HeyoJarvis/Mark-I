"""Bridge API server for React frontend to connect to JarvisAlive orchestrator."""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, List, Tuple
from contextlib import asynccontextmanager
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path to import orchestration modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the real department agents
from departments.branding.branding_agent import BrandingAgent
from departments.branding.logo_generation_agent import LogoGenerationAgent
from departments.market_research.market_research_agent import MarketResearchAgent
from departments.website.website_generator_agent import WebsiteGeneratorAgent

# Import orchestration
from orchestration.orchestrator import HeyJarvisOrchestrator, OrchestratorConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
orchestrator = None
real_agents = {}

# In-memory storage for demo purposes
sessions_store = {}

# Define our agents mapping to department agents
JARVIS_AGENTS = [
    {
        "agent_id": "jarvis",
        "name": "Jarvis",
        "description": "Main AI assistant and orchestrator",
        "type": "orchestrator",
        "icon": "🤖"
    },
    {
        "agent_id": "branding",
        "name": "Alfred",
        "description": "Brand identity and creative design specialist",
        "type": "branding",
        "icon": "🎨"
    },
    {
        "agent_id": "market_research",
        "name": "EDITH",
        "description": "Market research and competitive analysis",
        "type": "analyst",
        "icon": "📊"
    },
    {
        "agent_id": "website",
        "name": "Friday",
        "description": "Website generation and development",
        "type": "developer",
        "icon": "🌐"
    }
]

class SessionRequest(BaseModel):
    """Request model for session creation."""
    user_id: str

class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str

class AgentMessageRequest(BaseModel):
    """Request model for agent messages."""
    session_id: str
    agent_id: str
    message: str

class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""
    success: bool
    response: str
    agent_id: str
    error: str = None
    data: Dict[str, Any] = None  # Add structured data field

class AgentsResponse(BaseModel):
    """Response model for agents list."""
    agents: List[Dict[str, Any]]

class LogoGenerationRequest(BaseModel):
    """Request model for logo generation."""
    session_id: str
    brand_name: str
    logo_prompt: str
    colors: List[str]

class LogoGenerationResponse(BaseModel):
    """Response model for logo generation."""
    success: bool
    logo_url: str = None
    error: str = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle."""
    global orchestrator, real_agents
    
    # Startup
    try:
        # Initialize orchestrator
        config = OrchestratorConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        )
        orchestrator = HeyJarvisOrchestrator(config)
        await orchestrator.initialize()
        logger.info("HeyJarvis orchestrator initialized")
        
        # Initialize real department agents
        agent_config = {
            'anthropic_api_key': os.getenv("ANTHROPIC_API_KEY"),
            'openai_api_key': os.getenv("OPENAI_API_KEY")
        }
        
        # Initialize each department agent
        try:
            branding_config = agent_config.copy()
            branding_config['interactive_approval'] = False  # Disable interactive prompts
            real_agents['branding'] = BrandingAgent(branding_config)
            logger.info("✅ Branding Agent initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Branding Agent: {e}")
            
        try:
            real_agents['logo'] = LogoGenerationAgent(agent_config)
            logger.info("✅ Logo Generation Agent initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Logo Generation Agent: {e}")
            
        try:
            real_agents['market_research'] = MarketResearchAgent(agent_config)
            logger.info("✅ Market Research Agent initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Market Research Agent: {e}")
            
        try:
            real_agents['website'] = WebsiteGeneratorAgent(agent_config)
            logger.info("✅ Website Generator Agent initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Website Generator Agent: {e}")
            
        logger.info(f"Initialized {len(real_agents)} department agents")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        # Continue without orchestrator for demo purposes
    
    yield
    
    # Shutdown
    if orchestrator:
        try:
            await orchestrator.close()
        except:
            pass
    logger.info("API server shut down")

# Create FastAPI app
app = FastAPI(
    title="Jarvis React Bridge API",
    description="Bridge API for React frontend to connect to JarvisAlive department agents",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="generated_logos"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Jarvis React Bridge API is running",
        "agents_initialized": list(real_agents.keys()),
        "orchestrator_ready": orchestrator is not None
    }

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """Create a new session."""
    session_id = str(uuid.uuid4())
    sessions_store[session_id] = {
        "user_id": request.user_id,
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    logger.info(f"Created session: {session_id} for user: {request.user_id}")
    return SessionResponse(session_id=session_id)

@app.get("/api/agents", response_model=AgentsResponse)
async def get_agents():
    """Get available agents."""
    return AgentsResponse(agents=JARVIS_AGENTS)

async def run_branding_agent(message: str) -> Tuple[str, Dict[str, Any]]:
    """Run the branding agent and return formatted text and structured data."""
    if 'branding' not in real_agents:
        return ("Branding agent is not available. Please ensure API keys are configured.", {})
    
    try:
        agent = real_agents['branding']
        state = {
            'business_idea': message,
            'user_request': message,
            'session_id': str(uuid.uuid4())[:8],
            'skip_logo_generation': True  # Skip logo generation in initial run
        }
        
        result = await agent.run(state)
        
        # Extract structured data
        branding_data = {
            'brand_name': result.get('brand_name', 'Your Brand'),
            'tagline': result.get('tagline', 'Your tagline here'),
            'color_palette': result.get('color_palette', ['#000000']),
            'domain_suggestions': result.get('domain_suggestions', []),
            'logo_prompt': result.get('logo_prompt', ''),
            'brand_values': result.get('brand_values', []),
            'target_audience': result.get('target_audience', '')
        }
        
        # Format response
        response = f"""🎨 **Brand Identity Created!**

**Brand Name:** {branding_data['brand_name']}
**Tagline:** {branding_data['tagline']}
**Colors:** {', '.join(branding_data['color_palette'])}
**Available Domains:** {', '.join(branding_data['domain_suggestions'][:3]) if branding_data['domain_suggestions'] else 'Check availability'}

Your brand identity has been designed to resonate with your target audience."""
        
        return (response, branding_data)
        
    except Exception as e:
        logger.error(f"Branding agent error: {e}")
        return (f"I encountered an error while creating your brand identity. Please try again.", {})

async def run_market_research_agent(message: str) -> Tuple[str, Dict[str, Any]]:
    """Run the market research agent and return formatted text and structured data."""
    if 'market_research' not in real_agents:
        return ("Market research agent is not available. Please ensure API keys are configured.", {})
    
    try:
        agent = real_agents['market_research']
        state = {
            'business_idea': message,
            'user_request': message,
            'session_id': str(uuid.uuid4())[:8]
        }
        
        result = await agent.run(state)
        
        # Extract structured data from the nested market_research_result
        research_result = result.get('market_research_result', {})
        
        market_data = {
            'market_opportunity_score': research_result.get('market_opportunity_score', result.get('market_opportunity_score', 75)),
            'key_findings': research_result.get('key_findings', ['Market analysis in progress']),
            'recommended_strategy': research_result.get('recommended_strategy', 'Focus on differentiation'),
            'market_size': research_result.get('market_size', result.get('market_size')),
            'growth_rate': research_result.get('market_growth_rate', research_result.get('growth_rate')),
            'target_audience': research_result.get('target_audience'),
            'competitors': research_result.get('competitors', []),
            'threats': research_result.get('threats', []),
            'opportunities': research_result.get('opportunities', []),
            'industry_trends': research_result.get('industry_trends', []),
            'customer_personas': research_result.get('customer_personas', []),
            'positioning_recommendations': research_result.get('positioning_recommendations'),
            'pricing_strategy': research_result.get('pricing_strategy'),
            'go_to_market_strategy': research_result.get('go_to_market_strategy')
        }
        
        # Format response text
        response = f"""📊 **Market Research Complete!**

**Opportunity Score:** {market_data['market_opportunity_score']}/100
**Key Findings:**
"""
        for finding in market_data['key_findings'][:3]:
            response += f"• {finding}\n"
        
        response += f"\n**Recommended Strategy:** {market_data['recommended_strategy']}"
        
        return (response, market_data)
        
    except Exception as e:
        logger.error(f"Market research agent error: {e}")
        return (f"I encountered an error during market research. Please try again.", {})

async def run_website_agent(message: str) -> str:
    """Run the website generator agent."""
    if 'website' not in real_agents:
        return "Website generator agent is not available. Please ensure API keys are configured."
    
    try:
        agent = real_agents['website']
        state = {
            'business_idea': message,
            'user_request': message,
            'session_id': str(uuid.uuid4())[:8],
            'brand_name': 'Your Business',
            'business_type': 'general'
        }
        
        result = await agent.run(state)
        
        # Format response
        pages = result.get('sitemap', ['Home', 'About', 'Contact'])
        features = result.get('features', ['Responsive design'])
        
        response = f"""🌐 **Website Generated!**

**Pages Created:** {', '.join(pages[:5])}
**Features:** {', '.join(features[:3])}
**Technology:** Modern HTML5, CSS3, JavaScript

Your website has been generated and is ready for deployment."""
        
        return response
        
    except Exception as e:
        logger.error(f"Website generator error: {e}")
        return f"I encountered an error while generating your website. Please try again."

@app.post("/api/agent/message", response_model=AgentMessageResponse)
async def send_agent_message(request: AgentMessageRequest):
    """Send a message to an agent."""
    try:
        # Store the message
        if request.session_id in sessions_store:
            sessions_store[request.session_id]["messages"].append({
                "agent_id": request.agent_id,
                "message": request.message,
                "timestamp": datetime.now().isoformat()
            })
        
        # Get agent info
        agent = next((a for a in JARVIS_AGENTS if a["agent_id"] == request.agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        # Route to appropriate agent
        if request.agent_id == "jarvis":
            # Check if this is a business request (not agent creation)
            is_business_request = any(keyword in request.message.lower() for keyword in [
                'store', 'shop', 'business', 'company', 'startup', 'brand', 
                'market', 'website', 'coffee', 'restaurant', 'service', 
                'product', 'sell', 'launch', 'build my', 'create my',
                'i want to create a', 'i want to start', 'i want to build',
                'help me create', 'help me build', 'help me start'
            ])
            
            # Skip orchestrator for business requests - go straight to department agents
            if is_business_request:
                response_text = "I'll help you with your business! Let me coordinate the appropriate department agents.\n\n"
                combined_data = {}
                
                # For any business request, we want to run both market research and branding
                # These are the foundation for any new business
                try:
                    # Run market research first
                    market_response, market_data = await run_market_research_agent(request.message)
                    response_text += "📊 **Market Analysis**\n" + market_response + "\n\n"
                    combined_data['market_research'] = market_data
                    
                    # Then run branding
                    branding_response, branding_data = await run_branding_agent(request.message)
                    response_text += "🎨 **Brand Identity**\n" + branding_response
                    combined_data['branding'] = branding_data
                    
                    # Optionally suggest website creation
                    if any(keyword in request.message.lower() for keyword in ['online', 'website', 'web', 'digital']):
                        response_text += "\n\n💡 **Next Step:** Would you like me to create a website for your business?"
                    
                    # Return with combined data
                    return AgentMessageResponse(
                        success=True,
                        response=response_text,
                        agent_id=request.agent_id,
                        data=combined_data
                    )
                    
                except Exception as e:
                    logger.error(f"Department agent error: {e}")
                    response_text = "I understand you want to create a business. Let me help you with market research and branding."
                    return AgentMessageResponse(
                        success=True,
                        response=response_text,
                        agent_id=request.agent_id
                    )
            # Only use orchestrator for actual agent/automation creation requests
            elif orchestrator and 'agent' in request.message.lower():
                try:
                    result = await orchestrator.process_request(
                        request.message, 
                        request.session_id
                    )
                    response_text = f"I've processed your agent creation request.\n\n"
                    response_text += f"Status: {result.get('deployment_status', 'Processing')}"
                        
                except Exception as e:
                    logger.error(f"Orchestrator error: {e}")
                    response_text = f"I understand your request. How can I help you with your business today?"
            else:
                # Default response for Jarvis
                response_text = "Hello! I'm Jarvis, your AI orchestrator. I can help you create businesses, conduct market research, design brand identities, and generate websites. What would you like to build today?"
                
        elif request.agent_id == "branding":
            response_text, branding_data = await run_branding_agent(request.message)
            return AgentMessageResponse(
                success=True,
                response=response_text,
                agent_id=request.agent_id,
                data=branding_data
            )
            
        elif request.agent_id == "market_research":
            response_text, market_data = await run_market_research_agent(request.message) # Only get the text response
            return AgentMessageResponse(
                success=True,
                response=response_text,
                agent_id=request.agent_id,
                data=market_data
            )
            
        elif request.agent_id == "website":
            response_text = await run_website_agent(request.message)
            return AgentMessageResponse(
                success=True,
                response=response_text,
                agent_id=request.agent_id
            )
            
        else:
            response_text = f"Agent {request.agent_id} received: {request.message}"
        
        return AgentMessageResponse(
            success=True,
            response=response_text,
            agent_id=request.agent_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return AgentMessageResponse(
            success=False,
            response="",
            agent_id=request.agent_id,
            error=str(e)
        )

@app.post("/api/generate-logo", response_model=LogoGenerationResponse)
async def generate_logo(request: LogoGenerationRequest):
    """Generate a logo for the brand."""
    try:
        if 'logo' not in real_agents:
            return LogoGenerationResponse(
                success=False,
                error="Logo generation agent is not available"
            )
        
        agent = real_agents['logo']
        
        # Prepare the state for logo generation
        state = {
            'brand_name': request.brand_name,
            'logo_prompt': request.logo_prompt,
            'color_palette': request.colors,
            'session_id': request.session_id,
            'skip_interactive': True  # Skip the interactive prompt
        }
        
        logger.info(f"Generating logo for brand: {request.brand_name}")
        result = await agent.run(state)
        
        # Extract the logo URL from the result
        logo_url = result.get('logo_url', '')
        if not logo_url and result.get('logo_path'):
            # Convert local path to a URL that the frontend can access
            logo_path = result.get('logo_path')
            # Extract the relative path from generated_logos/
            if 'generated_logos/' in logo_path:
                relative_path = logo_path.split('generated_logos/')[-1]
                logo_url = f"/static/{relative_path}"
            else:
                logo_url = f"/static/{os.path.basename(logo_path)}"
        
        return LogoGenerationResponse(
            success=bool(logo_url),
            logo_url=logo_url,
            error=None if logo_url else "Failed to generate logo"
        )
        
    except Exception as e:
        logger.error(f"Logo generation error: {e}")
        return LogoGenerationResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get session message history."""
    if session_id not in sessions_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": sessions_store[session_id]["messages"]
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            agent_id = data.get("agent_id")
            message = data.get("message")
            
            if not agent_id or not message:
                await websocket.send_json({
                    "error": "agent_id and message are required"
                })
                continue
            
            # Process the message
            request = AgentMessageRequest(
                session_id=session_id,
                agent_id=agent_id,
                message=message
            )
            
            response = await send_agent_message(request)
            
            await websocket.send_json({
                "success": response.success,
                "response": response.response,
                "agent_id": response.agent_id,
                "error": response.error,
                "data": response.data # Include data in websocket response
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    # Run on a different port to avoid conflict with main API server
    uvicorn.run(app, host="0.0.0.0", port=8001) 