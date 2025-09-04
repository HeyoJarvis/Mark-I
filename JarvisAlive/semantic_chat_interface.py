#!/usr/bin/env python3
"""
Semantic Chat Interface - Conversational AI that routes to existing agents

This provides a natural chat interface that users can talk to, which then
intelligently routes their requests to your existing agents using semantic understanding.

Features:
- Natural conversational interface
- Intelligent routing to existing agents
- Context preservation across conversation
- Real-time agent execution and results
- Fallback to legacy orchestration when needed
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.semantic_integration import SemanticJarvis
from orchestration.semantic_universal_orchestrator import (
    SemanticUniversalOrchestrator, 
    OrchestrationMode,
    create_semantic_universal_orchestrator
)
from orchestration.universal_orchestrator import UniversalOrchestratorConfig
from orchestration.response_analyzer import ContextAwareResponseAnalyzer, ResponseType, ResponseDecision
from orchestration.workflow_result_store import WorkflowResultStore
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig


class MockSemanticJarvis:
    """Mock SemanticJarvis for development that doesn't need complex config."""
    
    def __init__(self, ai_engine):
        from orchestration.semantic_request_parser import SemanticRequestParser
        self.semantic_parser = SemanticRequestParser(ai_engine)
    
    async def process_request(self, user_request: str, session_id: str, conversation_context: Optional[Dict[str, Any]] = None):
        """Process request using semantic parser only."""
        try:
            understanding = await self.semantic_parser.parse_request(user_request, conversation_context)
            
            # Convert to standard response format
            return {
                "success": True,
                "workflow_id": f"mock_{session_id}",
                "session_id": session_id,
                "method": "mock_semantic",
                "business_goal": understanding.business_goal,
                "user_intent": understanding.user_intent_summary,
                "confidence": understanding.confidence_score,
                "execution_strategy": understanding.execution_strategy.value,
                "agents_used": understanding.recommended_agents,
                "capabilities": [cap.value for cap in understanding.primary_capabilities],
                "execution_plan": understanding.execution_plan,
                "results": {"status": "Mock execution completed"},
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "mock_semantic",
                "timestamp": datetime.now().isoformat()
            }


class ChatSession:
    """Enhanced chat session with workflow result tracking and context management."""
    
    def __init__(self, session_id: str, user_name: str = "User"):
        self.session_id = session_id
        self.user_name = user_name
        self.created_at = datetime.now()
        self.conversation_history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.active_workflows: List[str] = []
        self.completed_workflows: Dict[str, Dict[str, Any]] = {}  # workflow_id -> workflow_data
        self.workflow_artifacts: Dict[str, List[str]] = {}        # workflow_id -> [file_paths]
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
    
    def add_workflow_result(self, workflow_id: str, agent_type: str, results: Dict[str, Any]):
        """Add completed workflow results to session context."""
        self.completed_workflows[workflow_id] = {
            "agent_type": agent_type,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "business_goal": results.get("business_goal", ""),
            "deliverables": self._extract_deliverables(agent_type, results)
        }
        
        # Track artifacts (files created)
        artifacts = self._extract_artifacts(agent_type, results)
        if artifacts:
            self.workflow_artifacts[workflow_id] = artifacts
    
    def _extract_deliverables(self, agent_type: str, results: Dict[str, Any]) -> List[str]:
        """Extract what was delivered by this workflow."""
        deliverables = []
        
        try:
            if agent_type == "website_generator_agent":
                business_name = results.get("business_name", "business")
                if results.get("website_generated_at"):
                    deliverables.append(f"Website for {business_name}")
                if results.get("saved_paths"):
                    deliverables.append(f"HTML files: {len(results['saved_paths'])} pages")
                    
            elif agent_type == "branding_agent":
                brand_name = results.get("brand_name", "brand")
                if brand_name:
                    deliverables.append(f"Brand identity: {brand_name}")
                if results.get("color_palette"):
                    deliverables.append(f"Color palette: {len(results['color_palette'])} colors")
                    
            elif agent_type == "logo_generation_agent":
                if results.get("logo_url"):
                    deliverables.append("Professional logo design")
                    
            elif agent_type == "market_research_agent":
                industry = results.get("industry", "market")
                deliverables.append(f"Market research report for {industry}")
                
        except Exception as e:
            deliverables.append(f"Completed {agent_type.replace('_', ' ').title()}")
                
        return deliverables
    
    def _extract_artifacts(self, agent_type: str, results: Dict[str, Any]) -> List[str]:
        """Extract file paths or URLs created by this workflow."""
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
        
        except Exception:
            pass
        
        return artifacts
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get context for semantic understanding (legacy compatibility)."""
        return {
            "conversation_history": self.conversation_history[-10:],  # Last 10 messages
            "session_context": self.context,
            "user_name": self.user_name,
            "session_duration": str(datetime.now() - self.created_at)
        }
    
    def get_enhanced_context(self) -> Dict[str, Any]:
        """Get enhanced context including workflow results for intelligent responses."""
        return {
            "conversation_history": self.conversation_history[-10:],
            "session_context": self.context,
            "completed_workflows": list(self.completed_workflows.values()),
            "recent_deliverables": self._get_recent_deliverables(),
            "available_artifacts": self.workflow_artifacts,
            "session_duration": str(datetime.now() - self.created_at),
            "user_name": self.user_name
        }
    
    def _get_recent_deliverables(self) -> List[Dict[str, Any]]:
        """Get recent deliverables for quick context access."""
        recent = []
        for workflow_data in list(self.completed_workflows.values())[-5:]:  # Last 5 workflows
            recent.append({
                "agent_type": workflow_data["agent_type"],
                "business_goal": workflow_data["business_goal"],
                "deliverables": workflow_data["deliverables"],
                "timestamp": workflow_data["timestamp"]
            })
        return recent


class SemanticChatInterface:
    """
    Conversational AI interface that intelligently routes to existing agents.
    
    Provides natural chat experience while leveraging semantic orchestration
    to route requests to appropriate agents seamlessly.
    """
    
    def __init__(self, mode: OrchestrationMode = OrchestrationMode.SEMANTIC_WITH_FALLBACK):
        self.mode = mode
        self.sessions: Dict[str, ChatSession] = {}
        self.jarvis: Optional[SemanticJarvis] = None
        self.orchestrator: Optional[SemanticUniversalOrchestrator] = None
        self.startup_time = datetime.now()
        
        # New context-aware components
        self.workflow_store = None  # Will be initialized in initialize()
        self.response_analyzer = None  # Will be initialized in initialize()
        self.ai_engine = None  # Will be set during initialization
        
    async def initialize(self):
        """Initialize the chat interface with semantic orchestration."""
        print("🚀 Initializing Semantic Chat Interface...")
        
        try:
            # Check for API key
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("❌ No ANTHROPIC_API_KEY found in .env file")
                print("   Using mock mode for development")
                await self._initialize_mock_mode()
                return True
            
            # Initialize AI engine
            config = AIEngineConfig(
                api_key=api_key,
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,  # Slightly higher for conversational responses
                max_tokens=2000
            )
            ai_engine = AnthropicEngine(config)
            self.ai_engine = ai_engine
            
            # Initialize semantic components
            self.jarvis = SemanticJarvis(ai_engine)
            await self.jarvis.initialize()
            
            # Initialize context-aware components
            self.workflow_store = WorkflowResultStore(ai_engine, redis_url="redis://localhost:6379")
            await self.workflow_store.initialize()
            self.response_analyzer = ContextAwareResponseAnalyzer(ai_engine)
            
            print("✅ Semantic orchestration initialized")
            print("✅ Context-aware response system initialized")
            print(f"✅ Mode: {self.mode.value}")
            print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            print("   Falling back to mock mode")
            await self._initialize_mock_mode()
            return False
    
    async def _initialize_mock_mode(self):
        """Initialize with mock AI for development/testing."""
        from orchestration.semantic_request_parser import SemanticRequestParser
        
        class MockAIEngine:
            async def generate(self, prompt):
                # Handle off-key requests intelligently
                if "legal" in prompt.lower() or "contract" in prompt.lower():
                    return '{"business_goal": "Get legal contract assistance", "user_intent_summary": "User needs legal help", "primary_capabilities": [], "secondary_capabilities": [], "recommended_agents": [], "execution_strategy": "single_agent", "execution_plan": {"off_key_request": true, "suggestion": "I don\'t have legal services, but I can help with business content creation.", "available_alternatives": ["content_creation", "brand_creation"]}, "extracted_parameters": {}, "business_context": {}, "user_preferences": {}, "confidence_score": 0.3, "reasoning": "This is a legal request which I cannot handle directly"}'
                elif "hire" in prompt.lower() or "employee" in prompt.lower():
                    return '{"business_goal": "Help with hiring and recruitment", "user_intent_summary": "User needs HR assistance", "primary_capabilities": [], "secondary_capabilities": [], "recommended_agents": [], "execution_strategy": "single_agent", "execution_plan": {"off_key_request": true, "suggestion": "I don\'t handle HR, but I can help create job descriptions and content.", "available_alternatives": ["content_creation", "lead_generation"]}, "extracted_parameters": {}, "business_context": {}, "user_preferences": {}, "confidence_score": 0.3, "reasoning": "This is an HR request which I cannot handle directly"}'
                elif "logo" in prompt.lower():
                    return '{"business_goal": "Create professional logo", "user_intent_summary": "Logo design needed", "primary_capabilities": ["logo_generation"], "secondary_capabilities": ["brand_creation"], "recommended_agents": ["logo_generation_agent"], "execution_strategy": "single_agent", "execution_plan": {"description": "Direct logo generation"}, "extracted_parameters": {"business_type": "startup"}, "business_context": {"industry": "creative"}, "user_preferences": {"style": "professional"}, "confidence_score": 0.9, "reasoning": "Clear logo request"}'
                elif "market" in prompt.lower() or "research" in prompt.lower():
                    return '{"business_goal": "Conduct market research", "user_intent_summary": "Market analysis needed", "primary_capabilities": ["market_analysis"], "secondary_capabilities": [], "recommended_agents": ["market_research_agent"], "execution_strategy": "single_agent", "execution_plan": {"description": "Market research analysis"}, "extracted_parameters": {"industry": "technology"}, "business_context": {"focus": "competitive_analysis"}, "user_preferences": {"depth": "comprehensive"}, "confidence_score": 0.85, "reasoning": "Market research request"}'
                else:
                    return "I understand you'd like help with your business. Could you be more specific about what you need? I can help with logos, market research, branding, websites, and more."
        
        # Create a simple mock jarvis that doesn't need OrchestratorConfig
        mock_ai_engine = MockAIEngine()
        self.jarvis = MockSemanticJarvis(mock_ai_engine)
        self.ai_engine = mock_ai_engine
        
        # Initialize context-aware components with mock engine
        self.workflow_store = WorkflowResultStore(mock_ai_engine, redis_url="redis://localhost:6379")
        await self.workflow_store.initialize()
        self.response_analyzer = ContextAwareResponseAnalyzer(mock_ai_engine)
        
        print("✅ Mock mode initialized for development")
        print("✅ Context-aware response system initialized (mock mode)")
    
    def get_or_create_session(self, session_id: str, user_name: str = "User") -> ChatSession:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id, user_name)
        return self.sessions[session_id]
    
    async def chat(self, message: str, session_id: str = "default", user_name: str = "User") -> str:
        """
        Process a chat message and return response.
        
        Args:
            message: User's message
            session_id: Session identifier
            user_name: User's name for personalization
        
        Returns:
            Response from the system
        """
        session = self.get_or_create_session(session_id, user_name)
        session.add_message("user", message)
        
        try:
            # Check if this is a basic greeting
            if self._is_basic_greeting(message):
                response = await self._handle_conversational_message(message, session)
            else:
                # Use intelligent analysis for all other messages
                response = await self._handle_message_intelligently(message, session)
            
            session.add_message("assistant", response)
            return response
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an issue: {str(e)}. Could you please try rephrasing your request?"
            session.add_message("assistant", error_response, {"error": str(e)})
            return error_response
    
    def _is_basic_greeting(self, message: str) -> bool:
        """Determine if message is a basic greeting that doesn't need intelligent analysis."""
        basic_greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", 
            "thanks", "thank you", "bye", "goodbye", "see you"
        ]
        
        message_lower = message.lower().strip()
        # Only treat as basic greeting if it's short and matches exactly
        return any(message_lower.startswith(greeting) for greeting in basic_greetings) and len(message.split()) <= 3
    
    async def _handle_conversational_message(self, message: str, session: ChatSession) -> str:
        """Handle conversational messages with appropriate responses."""
        message_lower = message.lower().strip()
        
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return f"Hello {session.user_name}! 👋 I'm your AI business assistant. I can help you with:\n\n🎨 Logo design and branding\n📊 Market research and analysis\n🌐 Website creation\n📈 Business strategy\n💼 Sales and marketing\n\nWhat can I help you with today?"
        
        elif "what can you do" in message_lower or "help" in message_lower:
            return "I can assist you with various business needs:\n\n• **Creative Services**: Logo design, branding, visual identity\n• **Research & Analysis**: Market research, competitor analysis, trend insights\n• **Digital Presence**: Website creation, landing pages, online presence\n• **Business Strategy**: Planning, positioning, growth strategies\n• **Sales & Marketing**: Lead generation, outreach campaigns, sales materials\n\nJust tell me what you need in natural language, like:\n- 'Create a logo for my coffee shop'\n- 'I need market research for electric vehicles'\n- 'Build a website for my consulting business'\n\nWhat would you like to work on?"
        
        elif any(thanks in message_lower for thanks in ["thanks", "thank you"]):
            return "You're welcome! 😊 Is there anything else I can help you with?"
        
        elif any(bye in message_lower for bye in ["bye", "goodbye", "see you"]):
            return f"Goodbye {session.user_name}! Feel free to come back anytime you need business assistance. Have a great day! 👋"
        
        else:
            return "I'm here to help with your business needs. Could you tell me more about what you're looking for? I specialize in creative services, market research, websites, and business strategy."
    
    async def _handle_message_intelligently(self, message: str, session: ChatSession) -> str:
        """Intelligent message handling with full context awareness."""
        
        if not self.response_analyzer:
            # Fallback to business request handling if analyzer not available
            return await self._handle_business_request(message, session)
        
        try:
            # Get enhanced conversation context
            conversation_context = session.get_enhanced_context()
            
            # Analyze what type of response is needed
            decision = await self.response_analyzer.analyze_response_needed(
                message, conversation_context
            )
            
            # Route based on decision
            if decision.response_type == ResponseType.DIRECT_ANSWER:
                return await self._provide_contextual_answer(message, session, decision)
            elif decision.response_type == ResponseType.AGENT_EXECUTION:
                return await self._execute_agents_workflow(message, session)
            elif decision.response_type == ResponseType.HYBRID:
                return await self._provide_hybrid_response(message, session, decision)
            else:
                return await self._request_clarification(message, session, decision)
                
        except Exception as e:
            # Fallback to business request handling
            return await self._handle_business_request(message, session)
    
    async def _provide_contextual_answer(
        self, 
        message: str, 
        session: ChatSession, 
        decision: ResponseDecision
    ) -> str:
        """Provide answer using context and knowledge without agent execution."""
        
        try:
            # Extract relevant context based on decision
            relevant_context = await self._extract_relevant_context(
                message, session, decision.context_sources
            )
            
            # Generate intelligent answer
            if relevant_context and relevant_context.get("context_found"):
                return await self._answer_from_context(message, relevant_context, session)
            else:
                return await self._answer_from_knowledge(message, session)
                
        except Exception as e:
            return f"I'd be happy to help with that question, but I encountered an issue accessing the information. Could you please rephrase your question?"
    
    async def _extract_relevant_context(
        self, 
        message: str, 
        session: ChatSession, 
        context_sources: List[str]
    ) -> Dict[str, Any]:
        """Extract relevant context for answering the user's question."""
        
        try:
            if self.workflow_store:
                return await self.workflow_store.query_context(message, session.session_id)
            else:
                # Fallback to session-based context
                return self._extract_session_context(message, session, context_sources)
                
        except Exception as e:
            return {"context_found": False, "confidence": 0.0}
    
    def _extract_session_context(
        self, 
        message: str, 
        session: ChatSession, 
        context_sources: List[str]
    ) -> Dict[str, Any]:
        """Extract relevant context from session data (fallback method)."""
        
        relevant_context = {"context_found": False, "confidence": 0.0}
        
        try:
            # Extract from completed workflows
            if "recent_workflows" in context_sources and session.completed_workflows:
                latest_workflow = list(session.completed_workflows.values())[-1]
                relevant_context = {
                    "context_found": True,
                    "confidence": 0.7,
                    "relevant_info": f"Recent work: {latest_workflow['business_goal']}",
                    "source_workflows": [latest_workflow["agent_type"]],
                    "specific_details": {
                        "business_goal": latest_workflow["business_goal"],
                        "deliverables": latest_workflow["deliverables"]
                    }
                }
            
            # Look for specific information in session context
            last_result = session.context.get("last_result", {})
            if last_result and any(keyword in message.lower() for keyword in ["color", "website", "logo", "brand"]):
                relevant_context["context_found"] = True
                relevant_context["specific_details"]["last_result"] = last_result
        
        except Exception:
            pass
        
        return relevant_context
    
    async def _answer_from_context(
        self, 
        message: str, 
        context_data: Dict[str, Any], 
        session: ChatSession
    ) -> str:
        """Generate answer using specific context from previous workflows."""
        
        try:
            answer_prompt = f"""
User asked: "{message}"

Available context from their previous work:
{json.dumps(context_data, indent=2)}

Provide a helpful, specific answer using this context. Be conversational and reference their previous work naturally.

Examples of good responses:
- "What colors did you use?" → "In the website I created for your shawarma restaurant, I used #C87941 (warm copper), #1B365C (deep navy), and #F4E9D7 (cream) to create an authentic Middle Eastern feel."
- "How's my project going?" → "Your shawarma restaurant website is complete! I generated the full site with menu sections, contact info, and used a warm color palette that reflects the Middle Eastern cuisine."

Answer naturally and helpfully, referencing the specific work I did for them:
"""
            
            response = await self.ai_engine.generate(answer_prompt)
            return response.content
            
        except Exception as e:
            return "I can see we've worked together before, but I'm having trouble accessing the specific details right now. Could you be more specific about what you'd like to know?"
    
    async def _answer_from_knowledge(
        self, 
        message: str, 
        session: ChatSession
    ) -> str:
        """Generate answer using AI general knowledge when no specific context available."""
        
        try:
            knowledge_prompt = f"""
User asked: "{message}"

They don't have relevant previous work context, so answer using your general knowledge. Be helpful and conversational.

If the question relates to business topics I can help with (branding, websites, marketing, etc.), provide a good answer and optionally suggest how I could help create something related.

Answer naturally and helpfully:
"""
            
            response = await self.ai_engine.generate(knowledge_prompt)
            return response.content
            
        except Exception as e:
            return "I'd be happy to help with that question! Could you provide a bit more context about what specifically you're looking for?"
    
    async def _execute_agents_workflow(self, message: str, session: ChatSession) -> str:
        """Execute agents workflow - same as the old _handle_business_request."""
        return await self._handle_business_request(message, session)
    
    async def _provide_hybrid_response(
        self, 
        message: str, 
        session: ChatSession, 
        decision: ResponseDecision
    ) -> str:
        """Provide hybrid response - answer question and suggest actions."""
        
        try:
            # First provide the answer
            answer = await self._provide_contextual_answer(message, session, decision)
            
            # Then suggest related actions
            suggestion = "\n\nWould you like me to create something related to this? I can help with websites, logos, branding, or market research!"
            
            return answer + suggestion
            
        except Exception as e:
            return await self._provide_contextual_answer(message, session, decision)
    
    async def _request_clarification(
        self, 
        message: str, 
        session: ChatSession, 
        decision: ResponseDecision
    ) -> str:
        """Request clarification when the message is ambiguous."""
        
        return f"I'd like to help you with that! Could you provide a bit more detail about what you're looking for? I can assist with creating websites, logos, branding, market research, and more business services."
    
    async def _handle_business_request(self, message: str, session: ChatSession) -> str:
        """Handle business requests by routing to appropriate agents."""
        if not self.jarvis:
            return "I'm currently in setup mode. Please check the system configuration and try again."
        
        try:
            # Get conversation context
            conversation_context = session.get_conversation_context()
            
            # Process with semantic orchestration
            result = await self.jarvis.process_request(
                message, session.session_id, conversation_context
            )
            
            # Update session context
            session.context.update({
                "last_request": message,
                "last_result": result,
                "business_goal": result.get("business_goal"),
                "agents_used": result.get("agents_used", [])
            })
            
            # Store workflow results for context queries
            await self._store_workflow_results(result, session)
            
            # Format response based on result
            return self._format_business_response(result, session)
            
        except Exception as e:
            return f"I encountered an issue processing your request: {str(e)}. Could you please try rephrasing what you need?"
    
    async def _store_workflow_results(self, result: Dict[str, Any], session: ChatSession):
        """Store workflow results for context-aware responses."""
        
        try:
            if not self.workflow_store or not result.get("success"):
                return
            
            workflow_id = result.get("workflow_id")
            agents_used = result.get("agents_used", [])
            business_goal = result.get("business_goal", "")
            results_data = result.get("results", result)  # Use full result if no specific results field
            
            if workflow_id and agents_used:
                # Store results for each agent used
                for agent_type in agents_used:
                    await self.workflow_store.store_workflow_result(
                        workflow_id=f"{workflow_id}_{agent_type}",
                        session_id=session.session_id,
                        agent_type=agent_type,
                        results=results_data,
                        business_goal=business_goal
                    )
                    
                    # Update session with completed workflow
                    session.add_workflow_result(
                        workflow_id=f"{workflow_id}_{agent_type}",
                        agent_type=agent_type,
                        results=results_data
                    )
                    
        except Exception as e:
            # Don't fail the main workflow if storage fails
            pass
    
    def _format_business_response(self, result: Dict[str, Any], session: ChatSession) -> str:
        """Format the business result into a conversational response."""
        if not result.get("success"):
            return f"I had trouble processing that request. {result.get('error', 'Could you please provide more details about what you need?')}"
        
        # Extract key information
        business_goal = result.get("business_goal", "your request")
        agents_used = result.get("agents_used", [])
        confidence = result.get("confidence", 0)
        execution_strategy = result.get("execution_strategy", "")
        
        # Check if this is an off-key request
        execution_plan = result.get("execution_plan", {})
        is_off_key = execution_plan.get("off_key_request", False)
        
        if is_off_key:
            return self._format_off_key_response(result, session)
        
        # Create conversational response for valid requests
        response_parts = []
        
        # Acknowledge understanding
        response_parts.append(f"I understand you want to {business_goal.lower()}.")
        
        # Explain what's happening
        if len(agents_used) == 1:
            agent_name = agents_used[0].replace("_", " ").title()
            response_parts.append(f"I'm routing this to my {agent_name} to handle this for you.")
        elif len(agents_used) > 1:
            if "parallel" in execution_strategy:
                response_parts.append(f"I'm coordinating multiple specialists ({len(agents_used)} agents) to work on this simultaneously.")
            else:
                response_parts.append(f"I'm organizing a sequential workflow with {len(agents_used)} specialists to ensure the best results.")
        
        # Add confidence indicator
        if confidence >= 0.9:
            response_parts.append("I'm very confident about this approach.")
        elif confidence >= 0.7:
            response_parts.append("I have a good understanding of your needs.")
        elif confidence >= 0.5:
            response_parts.append("I believe I understand what you're looking for.")
        else:
            response_parts.append("I'll do my best based on what I understand.")
        
        # Add results if available
        if result.get("results"):
            response_parts.append("\n📋 **Results:**")
            results_summary = self._summarize_results(result["results"])
            response_parts.append(results_summary)
        
        # Add next steps or follow-up
        response_parts.append(f"\nIs there anything specific you'd like me to adjust or any additional help you need with {business_goal.lower()}?")
        
        return " ".join(response_parts)
    
    def _format_off_key_response(self, result: Dict[str, Any], session: ChatSession) -> str:
        """Format response for off-key requests that don't map to existing agents."""
        business_goal = result.get("business_goal", "help you with that")
        execution_plan = result.get("execution_plan", {})
        suggestion = execution_plan.get("suggestion", "")
        available_alternatives = execution_plan.get("available_alternatives", [])
        
        response_parts = []
        
        # Acknowledge the request
        response_parts.append(f"I understand you'd like to {business_goal.lower()}.")
        
        # Explain limitation and provide suggestion
        if suggestion:
            response_parts.append(suggestion)
        else:
            response_parts.append("I don't have a specific agent for that exact request.")
        
        # Offer alternatives
        if available_alternatives:
            response_parts.append("\n🔧 **Here's what I can help with instead:**")
            
            capability_descriptions = {
                "logo_generation": "🎨 **Logo Design** - Create professional logos and visual branding",
                "brand_creation": "🏢 **Brand Strategy** - Develop brand identity, messaging, and positioning", 
                "market_analysis": "📊 **Market Research** - Analyze markets, competitors, and industry trends",
                "website_building": "🌐 **Website Creation** - Build responsive websites and landing pages",
                "sales_outreach": "💼 **Sales Materials** - Create sales campaigns and outreach content",
                "lead_generation": "🎯 **Lead Generation** - Find and qualify potential customers",
                "content_creation": "✍️ **Content Writing** - Write marketing copy, blog posts, and materials"
            }
            
            for alternative in available_alternatives[:4]:  # Limit to top 4
                if alternative in capability_descriptions:
                    response_parts.append(f"\n• {capability_descriptions[alternative]}")
        
        # Helpful closing
        response_parts.append(f"\nWould any of these services help with what you're trying to achieve? Just let me know what interests you!")
        
        return " ".join(response_parts)
    
    def _summarize_results(self, results: Dict[str, Any]) -> str:
        """Summarize agent results in conversational format."""
        if not results:
            return "Working on your request..."
        
        summary_parts = []
        
        # Look for specific result types
        if "logo_url" in str(results):
            summary_parts.append("• Logo design completed")
        if "market_analysis" in str(results):
            summary_parts.append("• Market research analysis ready")
        if "brand_strategy" in str(results):
            summary_parts.append("• Brand strategy developed")
        if "website" in str(results):
            summary_parts.append("• Website created")
        
        if summary_parts:
            return "\n".join(summary_parts)
        else:
            return f"• Processing completed ({len(results)} deliverables ready)"
    
    async def interactive_chat(self):
        """Start interactive chat session."""
        print("\n" + "="*60)
        print("🎯 SEMANTIC CHAT INTERFACE - INTERACTIVE MODE")
        print("="*60)
        print("Chat with your AI business assistant!")
        print("Type 'quit', 'exit', or 'bye' to end the session.")
        print("Type 'help' to see what I can do.")
        print("-"*60)
        
        session_id = f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Welcome message
        welcome = await self.chat("hello", session_id, "Interactive User")
        print(f"\n🤖 Assistant: {welcome}")
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    goodbye = await self.chat("bye", session_id)
                    print(f"\n🤖 Assistant: {goodbye}")
                    break
                
                if not user_input:
                    continue
                
                # Process message
                print(f"\n🤖 Assistant: Processing your request...")
                response = await self.chat(user_input, session_id)
                print(f"\n🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                goodbye = await self.chat("bye", session_id)
                print(f"\n\n🤖 Assistant: {goodbye}")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def demo_conversation(self):
        """Run a demo conversation showing capabilities."""
        print("\n" + "="*60)
        print("🎭 SEMANTIC CHAT INTERFACE - DEMO CONVERSATION")
        print("="*60)
        
        demo_messages = [
            "Hi there!",
            "What can you help me with?",
            "I need a professional logo for my artisan coffee roastery called Bean Craft",
            "That sounds great! Can you also do some market research on the specialty coffee industry?",
            "Perfect! How long will this take?",
            "Thanks for your help!"
        ]
        
        session_id = "demo_session"
        user_name = "Demo User"
        
        for i, message in enumerate(demo_messages, 1):
            print(f"\n💬 {user_name}: {message}")
            
            # Show processing for business requests
            if i > 2:  # Business requests
                print("   🤖 Processing...")
                await asyncio.sleep(1)  # Simulate processing time
            
            response = await self.chat(message, session_id, user_name)
            print(f"🤖 Assistant: {response}")
            
            # Small delay for readability
            await asyncio.sleep(0.5)
        
        print(f"\n{'='*60}")
        print("🎉 Demo completed! This shows how users can chat naturally")
        print("   and get routed to appropriate agents seamlessly.")


async def main():
    """Main function to run the semantic chat interface."""
    print("🚀 Starting Semantic Chat Interface")
    
    # Initialize the chat interface
    chat = SemanticChatInterface(OrchestrationMode.SEMANTIC_WITH_FALLBACK)
    
    success = await chat.initialize()
    if not success:
        print("⚠️  Running in limited mode")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            await chat.demo_conversation()
        elif sys.argv[1] == "--test":
            # Quick test
            test_messages = [
                "Hello!",
                "Create a logo for my startup",
                "I need market research for electric cars",
                "Thanks!"
            ]
            
            for msg in test_messages:
                print(f"\nTest: {msg}")
                response = await chat.chat(msg, "test")
                print(f"Response: {response[:100]}...")
        else:
            print("Usage:")
            print("  python semantic_chat_interface.py           # Interactive mode")
            print("  python semantic_chat_interface.py --demo    # Demo conversation")  
            print("  python semantic_chat_interface.py --test    # Quick test")
    else:
        # Interactive mode
        await chat.interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())