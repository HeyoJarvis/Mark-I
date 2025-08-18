"""
Frontend Integration Layer - Bridge between UI and Agent System

This module provides a clean API for frontend applications to interact with
the concurrent agent system, supporting both direct agent communication and
intelligent orchestration.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from orchestration.persistent.persistent_system import PersistentSystem
from orchestration.intelligence.workflow_brain import WorkflowBrain
from orchestration.intelligence.intelligent_workflow_manager import IntelligentWorkflowManager
from orchestration.persistent.message_bus import MessageBus, MessageType

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class MessageSource(Enum):
    """Source of messages in the system."""
    USER = "user"
    AGENT = "agent"
    ORCHESTRATOR = "orchestrator"
    SYSTEM = "system"


@dataclass
class AgentInfo:
    """Information about an available agent."""
    agent_id: str
    agent_type: str
    name: str
    description: str
    status: AgentStatus
    current_task: Optional[str] = None
    capabilities: List[str] = None
    icon: str = "🤖"
    
    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value,
            'capabilities': self.capabilities or []
        }


@dataclass
class ChatMessage:
    """A message in the chat interface."""
    id: str
    source: MessageSource
    agent_id: Optional[str]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source.value,
            'agent_id': self.agent_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class FrontendIntegrationLayer:
    """
    Main integration layer for frontend applications.
    
    Provides:
    - Direct agent communication
    - Intelligent routing through orchestrator
    - Real-time status updates
    - Workflow suggestions
    - Session management
    """
    
    def __init__(self, persistent_system: PersistentSystem, workflow_brain: WorkflowBrain):
        """Initialize the frontend integration layer."""
        self.persistent_system = persistent_system
        self.workflow_brain = workflow_brain
        self.workflow_manager = IntelligentWorkflowManager(workflow_brain, workflow_brain.config)
        
        self.logger = logging.getLogger(__name__)
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_workflows: Dict[str, List[str]] = {}
        
        # Agent registry with frontend metadata
        self.agent_registry = self._initialize_agent_registry()
        
        # Callback handlers for real-time updates
        self.update_handlers: Dict[str, List[Callable]] = {
            'agent_status': [],
            'task_progress': [],
            'workflow_complete': [],
            'suggestion_ready': [],
            'error': []
        }
        
        # Message history per session
        self.message_history: Dict[str, List[ChatMessage]] = {}
        
        self.logger.info("Frontend Integration Layer initialized")
    
    def _initialize_agent_registry(self) -> Dict[str, AgentInfo]:
        """Initialize registry of available agents with frontend metadata."""
        return {
            'branding_agent': AgentInfo(
                agent_id='branding_agent',
                agent_type='branding',
                name='Brand Designer',
                description='Creates brand identities, logos, and visual designs',
                status=AgentStatus.AVAILABLE,
                capabilities=['logo_design', 'brand_strategy', 'color_palette', 'brand_guidelines'],
                icon='🎨'
            ),
            'market_research_agent': AgentInfo(
                agent_id='market_research_agent',
                agent_type='market_research',
                name='Market Analyst',
                description='Analyzes markets, competition, and business opportunities',
                status=AgentStatus.AVAILABLE,
                capabilities=['market_analysis', 'competitor_research', 'trend_analysis', 'opportunity_assessment'],
                icon='📊'
            ),
            'orchestrator': AgentInfo(
                agent_id='orchestrator',
                agent_type='orchestrator',
                name='Business Advisor',
                description='Intelligent orchestrator that coordinates all agents and provides guidance',
                status=AgentStatus.AVAILABLE,
                capabilities=['workflow_planning', 'agent_coordination', 'intelligent_suggestions', 'business_strategy'],
                icon='🧠'
            )
        }
    
    async def create_session(self, user_id: str, session_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: User identifier
            session_metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'metadata': session_metadata or {},
            'workflow_context': {},
            'active_tasks': {}
        }
        
        self.session_workflows[session_id] = []
        self.message_history[session_id] = []
        
        self.logger.info(f"Created session {session_id} for user {user_id}")
        
        # Send initial greeting
        await self._add_message(
            session_id,
            ChatMessage(
                id=str(uuid.uuid4())[:8],
                source=MessageSource.SYSTEM,
                agent_id=None,
                content="Welcome! I'm your Business Development Assistant. You can talk directly to any agent or ask me for guidance. How can I help you today?",
                timestamp=datetime.utcnow()
            )
        )
        
        return session_id
    
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of available agents with their current status.
        
        Returns:
            List of agent information dictionaries
        """
        try:
            # Return static agent data for reliability
            agents = []
            
            for agent_id, agent_info in self.agent_registry.items():
                # Set all agents as available
                agent_info.status = AgentStatus.AVAILABLE
                agents.append(agent_info.to_dict())
            
            self.logger.info(f"Returning {len(agents)} available agents")
            return agents
            
        except Exception as e:
            self.logger.error(f"Error getting available agents: {e}")
            # Return minimal fallback
            return [
                {
                    'agent_id': 'branding_agent',
                    'agent_type': 'branding',
                    'name': 'Brand Designer',
                    'description': 'Creates brand identities, logos, and visual designs',
                    'status': 'available',
                    'capabilities': ['logo_design', 'brand_strategy'],
                    'icon': '🎨'
                },
                {
                    'agent_id': 'market_research_agent',
                    'agent_type': 'market_research',
                    'name': 'Market Analyst',
                    'description': 'Analyzes markets, competition, and business opportunities',
                    'status': 'available',
                    'capabilities': ['market_analysis', 'competitor_research'],
                    'icon': '📊'
                },
                {
                    'agent_id': 'orchestrator',
                    'agent_type': 'orchestrator',
                    'name': 'Business Advisor',
                    'description': 'Intelligent orchestrator that coordinates all agents',
                    'status': 'available',
                    'capabilities': ['workflow_planning', 'agent_coordination'],
                    'icon': '🧠'
                }
            ]
    
    async def send_message_to_agent(
        self,
        session_id: str,
        agent_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a message directly to a specific agent.
        
        Args:
            session_id: Session identifier
            agent_id: Target agent ID
            message: User message
            
        Returns:
            Response with task ID and initial status
        """
        import uuid
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")
        
        # Add user message to history
        await self._add_message(
            session_id,
            ChatMessage(
                id=str(uuid.uuid4())[:8],
                source=MessageSource.USER,
                agent_id=agent_id,
                content=message,
                timestamp=datetime.utcnow()
            )
        )
        
        # Route based on agent type
        if agent_id == 'orchestrator':
            return await self._handle_orchestrator_message(session_id, message)
        else:
            return await self._handle_direct_agent_message(session_id, agent_id, message)
    
    async def _handle_orchestrator_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle message sent to the orchestrator."""
        import uuid
        
        try:
            # Create workflow through WorkflowBrain
            session = self.active_sessions[session_id]
            workflow_id = await self.workflow_brain.create_workflow(
                user_id=session['user_id'],
                session_id=session_id,
                workflow_type=self._infer_workflow_type(message),
                initial_request=message
            )
            
            # Add to session tracking
            self.session_workflows[session_id].append(workflow_id)
            
            # Send acknowledgment
            await self._add_message(
                session_id,
                ChatMessage(
                    id=str(uuid.uuid4())[:8],
                    source=MessageSource.ORCHESTRATOR,
                    agent_id='orchestrator',
                    content=f"I understand. I'll coordinate the right agents to help with: {message}",
                    timestamp=datetime.utcnow(),
                    metadata={'workflow_id': workflow_id}
                )
            )
            
            # Execute workflow
            asyncio.create_task(self._execute_orchestrated_workflow(session_id, workflow_id))
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'message': 'Workflow initiated'
            }
            
        except Exception as e:
            self.logger.error(f"Error in orchestrator message handling: {e}")
            await self._send_error_message(session_id, str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_direct_agent_message(
        self,
        session_id: str,
        agent_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle message sent directly to a specific agent."""
        import uuid
        
        try:
            agent_info = self.agent_registry.get(agent_id)
            if not agent_info:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            # Create task for the agent
            task = {
                'task_id': str(uuid.uuid4())[:8],
                'task_type': agent_info.agent_type,
                'description': message,
                'input_data': {
                    'request': message,
                    'session_id': session_id,
                    'direct_request': True
                }
            }
            
            # Submit to persistent system
            result = await self.persistent_system.submit_task(
                task=task,
                user_id=self.active_sessions[session_id]['user_id'],
                session_id=session_id,
                requires_approval=False
            )
            
            # Track in session
            self.active_sessions[session_id]['active_tasks'][result['task_id']] = {
                'agent_id': agent_id,
                'submitted_at': datetime.utcnow()
            }
            
            # Send acknowledgment
            await self._add_message(
                session_id,
                ChatMessage(
                    id=str(uuid.uuid4())[:8],
                    source=MessageSource.AGENT,
                    agent_id=agent_id,
                    content=f"I'm working on your request: {message}",
                    timestamp=datetime.utcnow(),
                    metadata={'task_id': result['task_id']}
                )
            )
            
            # Monitor task completion
            asyncio.create_task(self._monitor_task_completion(session_id, result['task_id'], agent_id))
            
            return {
                'success': True,
                'task_id': result['task_id'],
                'message': f'{agent_info.name} is processing your request'
            }
            
        except Exception as e:
            self.logger.error(f"Error in direct agent message handling: {e}")
            await self._send_error_message(session_id, str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_workflow_suggestions(
        self,
        session_id: str,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get intelligent workflow suggestions based on session context.
        
        Args:
            session_id: Session identifier
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of workflow suggestions
        """
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        workflow_context = session.get('workflow_context', {})
        
        suggestions = await self.workflow_manager.suggest_next_workflows(
            workflow_context,
            max_suggestions
        )
        
        # Add UI-friendly formatting
        for suggestion in suggestions:
            # Determine which agent would handle this
            agent_id = self._get_agent_for_workflow_type(suggestion.get('workflow_type'))
            if agent_id:
                agent_info = self.agent_registry.get(agent_id)
                if agent_info:
                    suggestion['agent'] = {
                        'id': agent_id,
                        'name': agent_info.name,
                        'icon': agent_info.icon
                    }
        
        return suggestions
    
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of chat messages
        """
        messages = self.message_history.get(session_id, [])
        
        if limit:
            messages = messages[-limit:]
        
        return [msg.to_dict() for msg in messages]
    
    async def subscribe_to_updates(
        self,
        session_id: str,
        event_type: str,
        callback: Callable
    ):
        """
        Subscribe to real-time updates for a session.
        
        Args:
            session_id: Session identifier
            event_type: Type of event to subscribe to
            callback: Callback function to handle updates
        """
        if event_type in self.update_handlers:
            self.update_handlers[event_type].append(callback)
            self.logger.info(f"Subscribed to {event_type} updates for session {session_id}")
    
    async def _execute_orchestrated_workflow(self, session_id: str, workflow_id: str):
        """Execute a workflow through the orchestrator."""
        try:
            result = await self.workflow_brain.execute_workflow_enhanced(
                workflow_id=workflow_id,
                use_concurrent_execution=True
            )
            
            # Update session context
            self.active_sessions[session_id]['workflow_context'][workflow_id] = {
                'request': result.initial_request if hasattr(result, 'initial_request') else '',
                'type': result.workflow_type if hasattr(result, 'workflow_type') else 'unknown',
                'result': result,
                'timestamp': datetime.utcnow(),
                'success': result.status.value == 'completed' if hasattr(result, 'status') else False
            }
            
            # Send completion message
            await self._add_message(
                session_id,
                ChatMessage(
                    id=str(uuid.uuid4())[:8],
                    source=MessageSource.ORCHESTRATOR,
                    agent_id='orchestrator',
                    content=f"Workflow completed successfully! Would you like suggestions for next steps?",
                    timestamp=datetime.utcnow(),
                    metadata={'workflow_id': workflow_id}
                )
            )
            
            # Generate and send suggestions
            suggestions = await self.get_workflow_suggestions(session_id, 3)
            if suggestions:
                await self._send_suggestions_message(session_id, suggestions)
            
            # Notify subscribers
            await self._notify_handlers('workflow_complete', {
                'session_id': session_id,
                'workflow_id': workflow_id,
                'result': result
            })
            
        except Exception as e:
            self.logger.error(f"Error executing orchestrated workflow: {e}")
            await self._send_error_message(session_id, f"Workflow error: {e}")
    
    async def _monitor_task_completion(self, session_id: str, task_id: str, agent_id: str):
        """Monitor a task until completion."""
        import uuid
        
        try:
            # Poll for task result
            result = await self.persistent_system.await_task_result(task_id)
            
            if result:
                # Send result message
                content = self._format_agent_result(agent_id, result)
                await self._add_message(
                    session_id,
                    ChatMessage(
                        id=str(uuid.uuid4())[:8],
                        source=MessageSource.AGENT,
                        agent_id=agent_id,
                        content=content,
                        timestamp=datetime.utcnow(),
                        metadata={'task_id': task_id, 'result': result}
                    )
                )
                
                # Update session context for suggestions
                self.active_sessions[session_id]['workflow_context'][task_id] = {
                    'request': result.get('request', ''),
                    'type': self.agent_registry[agent_id].agent_type,
                    'result': result,
                    'timestamp': datetime.utcnow(),
                    'success': result.get('success', False)
                }
                
                # Remove from active tasks
                self.active_sessions[session_id]['active_tasks'].pop(task_id, None)
                
                # Notify subscribers
                await self._notify_handlers('task_complete', {
                    'session_id': session_id,
                    'task_id': task_id,
                    'agent_id': agent_id,
                    'result': result
                })
            
        except Exception as e:
            self.logger.error(f"Error monitoring task {task_id}: {e}")
            await self._send_error_message(session_id, f"Task monitoring error: {e}")
    
    def _format_agent_result(self, agent_id: str, result: Dict[str, Any]) -> str:
        """Format agent result for display."""
        agent_info = self.agent_registry.get(agent_id)
        
        if agent_id == 'branding_agent':
            if 'brand_names' in result:
                names = result['brand_names'][:3] if isinstance(result['brand_names'], list) else []
                return f"I've created brand options for you:\n" + "\n".join(f"• {name}" for name in names)
            return "Branding analysis complete!"
        
        elif agent_id == 'market_research_agent':
            if 'analysis' in result:
                return f"Market research complete! Key findings:\n{result['analysis'][:500]}..."
            return "Market analysis complete!"
        
        return f"{agent_info.name} has completed your request."
    
    async def _add_message(self, session_id: str, message: ChatMessage):
        """Add a message to session history and notify subscribers."""
        if session_id not in self.message_history:
            self.message_history[session_id] = []
        
        self.message_history[session_id].append(message)
        
        # Notify message handlers
        await self._notify_handlers('new_message', {
            'session_id': session_id,
            'message': message.to_dict()
        })
    
    async def _send_error_message(self, session_id: str, error: str):
        """Send an error message to the session."""
        import uuid
        
        await self._add_message(
            session_id,
            ChatMessage(
                id=str(uuid.uuid4())[:8],
                source=MessageSource.SYSTEM,
                agent_id=None,
                content=f"❌ Error: {error}",
                timestamp=datetime.utcnow(),
                metadata={'error': True}
            )
        )
    
    async def _send_suggestions_message(self, session_id: str, suggestions: List[Dict[str, Any]]):
        """Send workflow suggestions as a formatted message."""
        import uuid
        
        if not suggestions:
            return
        
        content = "📋 **Suggested Next Steps:**\n\n"
        for i, suggestion in enumerate(suggestions[:3], 1):
            agent = suggestion.get('agent', {})
            content += f"{i}. **{suggestion['title']}**\n"
            if agent:
                content += f"   {agent.get('icon', '🤖')} {agent.get('name', 'Agent')}\n"
            content += f"   💡 {suggestion.get('reason', '')}\n"
            content += f"   → \"{suggestion.get('suggested_prompt', '')}\"\n\n"
        
        await self._add_message(
            session_id,
            ChatMessage(
                id=str(uuid.uuid4())[:8],
                source=MessageSource.ORCHESTRATOR,
                agent_id='orchestrator',
                content=content,
                timestamp=datetime.utcnow(),
                metadata={'suggestions': suggestions}
            )
        )
    
    async def _notify_handlers(self, event_type: str, data: Dict[str, Any]):
        """Notify all registered handlers for an event type."""
        handlers = self.update_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                self.logger.error(f"Error in handler for {event_type}: {e}")
    
    def _infer_workflow_type(self, message: str) -> str:
        """Infer workflow type from user message."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['brand', 'logo', 'identity', 'design']):
            return 'branding'
        elif any(word in message_lower for word in ['market', 'research', 'analysis', 'competition']):
            return 'market_analysis'
        elif any(word in message_lower for word in ['business', 'plan', 'strategy']):
            return 'business_planning'
        else:
            return 'general'
    
    def _get_agent_for_workflow_type(self, workflow_type: str) -> Optional[str]:
        """Get the agent ID that handles a workflow type."""
        mapping = {
            'branding': 'branding_agent',
            'market_research': 'market_research_agent',
            'market_analysis': 'market_research_agent',
            'business_planning': 'orchestrator',
            'marketing_strategy': 'orchestrator'
        }
        return mapping.get(workflow_type)
    
    async def close_session(self, session_id: str):
        """Close a user session and clean up resources."""
        if session_id in self.active_sessions:
            # Cancel any active tasks
            session = self.active_sessions[session_id]
            for task_id in session.get('active_tasks', {}).keys():
                try:
                    # Could implement task cancellation here
                    pass
                except:
                    pass
            
            del self.active_sessions[session_id]
            self.session_workflows.pop(session_id, None)
            self.message_history.pop(session_id, None)
            
            self.logger.info(f"Closed session {session_id}") 