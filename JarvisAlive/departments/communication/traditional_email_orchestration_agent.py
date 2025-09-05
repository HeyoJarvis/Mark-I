"""
EmailOrchestrationAgent - Traditional agent for email orchestration following standard patterns.

This agent integrates with the semantic layer like other agents and provides:
- AI-powered email sequence creation
- Advanced personalization with Claude AI
- Send time optimization
- Reply detection and management
- Bounce/unsubscribe handling
- Email warming capabilities
- Comprehensive analytics
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Import AI engine infrastructure
from ai_engines.anthropic_engine import AnthropicEngine
from ai_engines.base_engine import AIEngineConfig

# Import our advanced orchestration components
from .semantic_advanced_orchestrator import SemanticAdvancedEmailOrchestrator
from .models.advanced_email_models import EmailOrchestrationConfig, AdvancedEmailSequence
from .models.communication_models import CommunicationContact

logger = logging.getLogger(__name__)


class EmailOrchestrationResult:
    """Result of email orchestration operations"""
    
    def __init__(
        self,
        sequences_created: List[Dict[str, Any]],
        contacts_processed: int,
        capabilities_info: Optional[Dict[str, Any]] = None,
        analytics_data: Optional[Dict[str, Any]] = None,
        warming_status: Optional[Dict[str, Any]] = None
    ):
        self.sequences_created = sequences_created
        self.contacts_processed = contacts_processed
        self.capabilities_info = capabilities_info or {}
        self.analytics_data = analytics_data or {}
        self.warming_status = warming_status or {}
        
        # Generate summary metrics
        self.total_sequences = len(sequences_created)
        self.success_rate = 1.0 if self.total_sequences > 0 else 0.0
        
    def to_dict(self) -> dict:
        """Convert result to dictionary format"""
        return {
            'sequences_created': self.sequences_created,
            'contacts_processed': self.contacts_processed,
            'capabilities_info': self.capabilities_info,
            'analytics_data': self.analytics_data,
            'warming_status': self.warming_status,
            'total_sequences': self.total_sequences,
            'success_rate': self.success_rate,
            'operation_completed_at': datetime.utcnow().isoformat()
        }


class EmailOrchestrationAgent:
    """
    Traditional email orchestration agent following standard agent patterns.
    
    Integrates with semantic layer and business workflows.
    Follows the contract: run(state: dict) -> dict
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the EmailOrchestrationAgent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI engine
        self._initialize_ai_engine()
        
        # Email orchestration configuration
        self.max_sequences = self.config.get('max_sequences', 10)
        self.default_sequence_length = self.config.get('default_sequence_length', 5)
        self.enable_ai_personalization = self.config.get('enable_ai_personalization', True)
        self.enable_send_optimization = self.config.get('enable_send_optimization', True)
        
        # Output configuration
        # Use absolute path to ensure outputs go to the main JarvisAlive directory
        import os
        jarvis_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_outputs_dir = os.path.join(jarvis_root, 'email_orchestration_outputs')
        self.outputs_dir = Path(self.config.get('outputs_dir', default_outputs_dir))
        self.outputs_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize advanced orchestrator
        self.advanced_orchestrator: Optional[SemanticAdvancedEmailOrchestrator] = None
        
        self.logger.info("EmailOrchestrationAgent initialized successfully")
    
    def _initialize_ai_engine(self):
        """Initialize the AI engine for email orchestration"""
        try:
            import os
            
            # Try multiple environment variable names
            api_key = (
                os.getenv('ANTHROPIC_API_KEY') or 
                os.getenv('CLAUDE_API_KEY') or
                os.getenv('ANTHROPIC_KEY')
            )
            
            if api_key:
                config = AIEngineConfig(
                    api_key=api_key,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.7,
                    max_tokens=2000
                )
                self.ai_engine = AnthropicEngine(config)
                self.logger.info("AI engine initialized for email orchestration")
            else:
                self.logger.warning("No AI API key found - some features may be limited")
                self.ai_engine = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize AI engine: {e}")
            self.ai_engine = None
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the EmailOrchestrationAgent.
        
        Args:
            state: Input state containing business information and email requirements
            
        Returns:
            Updated state with email orchestration results
        """
        self.logger.info("Starting email orchestration")
        
        try:
            # Extract email requirements from state
            email_requirements = self._extract_email_requirements(state)
            
            if not email_requirements:
                self.logger.warning("No email requirements found in state")
                return state
            
            # Initialize advanced orchestrator if not done
            if not self.advanced_orchestrator:
                await self._initialize_advanced_orchestrator()
            
            # Determine operation type from requirements
            operation_type = email_requirements.get('operation_type', 'create_sequence')
            
            # Route to appropriate handler
            if operation_type == 'describe_capabilities':
                result = await self._handle_capabilities_request(email_requirements)
            elif operation_type == 'create_sequence':
                result = await self._handle_sequence_creation(email_requirements)
            elif operation_type == 'personalize_advanced':
                result = await self._handle_personalization(email_requirements)
            elif operation_type == 'setup_warming':
                result = await self._handle_warming_setup(email_requirements)
            elif operation_type == 'analytics':
                result = await self._handle_analytics_request(email_requirements)
            else:
                result = await self._handle_general_request(email_requirements)
            
            # Save outputs
            saved_paths = await self._save_orchestration_outputs(result, email_requirements)
            
            # Update state with results
            updated_state = state.copy()
            updated_state.update({
                "email_orchestration_result": result.to_dict() if result else None,
                "email_orchestration_success": result is not None,
                "email_orchestration_completed_at": datetime.utcnow().isoformat(),
                
                # Expose key findings at top level for easy access
                "sequences_created": result.sequences_created if result else [],
                "total_email_sequences": result.total_sequences if result else 0,
                "email_capabilities": result.capabilities_info if result else {},
                "email_analytics": result.analytics_data if result else {},
                "saved_paths": saved_paths,
                "analysis_type": "email_orchestration"
            })
            
            self.logger.info(f"Email orchestration completed successfully")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in email orchestration: {e}")
            # Return original state on error with error info
            error_state = state.copy()
            error_state.update({
                "email_orchestration_error": str(e),
                "email_orchestration_success": False,
                "analysis_type": "email_orchestration_error"
            })
            return error_state
    
    def _extract_email_requirements(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract email orchestration requirements from state"""
        # Look for direct email requirements
        if 'email_requirements' in state:
            return state['email_requirements']
        
        # Extract from business context
        business_goal = state.get('business_goal', state.get('business_idea', ''))
        user_input = state.get('user_input', state.get('user_request', ''))
        target_audience = state.get('target_audience', 'professionals')
        industry = state.get('industry', 'business')
        
        # Determine operation type from input
        operation_type = 'create_sequence'  # default
        if any(word in (user_input + business_goal).lower() for word in ['capabilities', 'what can you do']):
            operation_type = 'describe_capabilities'
        elif 'personalize' in (user_input + business_goal).lower():
            operation_type = 'personalize_advanced'
        elif any(word in (user_input + business_goal).lower() for word in ['warming', 'warm up']):
            operation_type = 'setup_warming'
        elif 'analytics' in (user_input + business_goal).lower():
            operation_type = 'analytics'
        
        # Build requirements
        return {
            'business_goal': business_goal,
            'user_input': user_input,
            'operation_type': operation_type,
            'target_audience': target_audience,
            'industry': industry,
            'sequence_length': self.default_sequence_length,
            'enable_ai_personalization': self.enable_ai_personalization,
            'enable_send_optimization': self.enable_send_optimization,
            'business_context': state.get('business_context', {}),
            'user_preferences': state.get('user_preferences', {}),
            'extracted_parameters': state.get('extracted_parameters', {})
        }
    
    async def _initialize_advanced_orchestrator(self):
        """Initialize the advanced orchestrator"""
        try:
            self.advanced_orchestrator = SemanticAdvancedEmailOrchestrator()
            await self.advanced_orchestrator.initialize()
            self.logger.info("Advanced email orchestrator initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize advanced orchestrator: {e}")
            self.advanced_orchestrator = None
    
    async def _handle_capabilities_request(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle capabilities description requests"""
        if self.advanced_orchestrator:
            task_data = {
                'user_input': requirements.get('user_input', ''),
                'task_type': 'describe_capabilities',
                'business_goal': requirements.get('business_goal', '')
            }
            
            result = await self.advanced_orchestrator.run(task_data)
            
            return EmailOrchestrationResult(
                sequences_created=[],
                contacts_processed=0,
                capabilities_info=result.get('result', {})
            )
        
        # Fallback capabilities info
        capabilities_info = {
            'core_features': [
                'AI-Powered Email Sequences',
                'Advanced Personalization', 
                'Send Time Optimization',
                'Reply Detection & Management',
                'Bounce & Unsubscribe Handling',
                'Email Account Warming',
                'Comprehensive Analytics'
            ],
            'status': 'Available via traditional agent interface'
        }
        
        return EmailOrchestrationResult(
            sequences_created=[],
            contacts_processed=0,
            capabilities_info=capabilities_info
        )
    
    async def _handle_sequence_creation(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle email sequence creation"""
        if self.advanced_orchestrator:
            task_data = {
                'user_input': requirements.get('user_input', ''),
                'task_type': 'create_sequence',
                'business_goal': requirements.get('business_goal', ''),
                'target_audience': requirements.get('target_audience', 'executives'),
                'industry': requirements.get('industry', 'technology')
            }
            
            result = await self.advanced_orchestrator.run(task_data)
            
            if result.get('success'):
                sequence_data = result.get('result', {})
                sequences = [sequence_data] if sequence_data else []
                
                return EmailOrchestrationResult(
                    sequences_created=sequences,
                    contacts_processed=sequence_data.get('estimated_contacts', 0)
                )
        
        # Fallback sequence creation
        sequence = {
            'sequence_name': f"AI Sequence for {requirements.get('target_audience', 'Professionals')}",
            'business_goal': requirements.get('business_goal', ''),
            'target_audience': requirements.get('target_audience', 'professionals'),
            'sequence_length': requirements.get('sequence_length', 5),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'created_via_traditional_agent'
        }
        
        return EmailOrchestrationResult(
            sequences_created=[sequence],
            contacts_processed=1
        )
    
    async def _handle_personalization(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle email personalization requests"""
        if self.advanced_orchestrator:
            task_data = {
                'user_input': requirements.get('user_input', ''),
                'task_type': 'personalize_advanced',
                'business_goal': requirements.get('business_goal', '')
            }
            
            result = await self.advanced_orchestrator.run(task_data)
            
            return EmailOrchestrationResult(
                sequences_created=[],
                contacts_processed=0,
                analytics_data=result.get('result', {})
            )
        
        # Fallback personalization
        return EmailOrchestrationResult(
            sequences_created=[],
            contacts_processed=0,
            analytics_data={'personalization_status': 'available'}
        )
    
    async def _handle_warming_setup(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle email warming setup"""
        warming_status = {
            'warming_available': True,
            'recommended_duration': '2-4 weeks',
            'daily_send_limit': '10-50 emails',
            'status': 'ready_for_setup'
        }
        
        return EmailOrchestrationResult(
            sequences_created=[],
            contacts_processed=0,
            warming_status=warming_status
        )
    
    async def _handle_analytics_request(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle analytics requests"""
        analytics_data = {
            'analytics_available': True,
            'metrics_tracked': ['open_rates', 'click_rates', 'reply_rates', 'bounce_rates'],
            'reporting_formats': ['json', 'csv', 'dashboard'],
            'status': 'analytics_ready'
        }
        
        return EmailOrchestrationResult(
            sequences_created=[],
            contacts_processed=0,
            analytics_data=analytics_data
        )
    
    async def _handle_general_request(self, requirements: Dict[str, Any]) -> EmailOrchestrationResult:
        """Handle general email orchestration requests"""
        return await self._handle_sequence_creation(requirements)
    
    async def _save_orchestration_outputs(self, result: EmailOrchestrationResult, requirements: Dict[str, Any]) -> List[str]:
        """Save orchestration outputs to files"""
        saved_paths = []
        
        try:
            # Create timestamped directory
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_dir = self.outputs_dir / f"orchestration_{timestamp}"
            output_dir.mkdir(exist_ok=True)
            
            # Save main result
            result_file = output_dir / "orchestration_result.json"
            with open(result_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            saved_paths.append(str(result_file))
            
            # Save sequences if any
            if result.sequences_created:
                sequences_file = output_dir / "email_sequences.json"
                with open(sequences_file, 'w') as f:
                    json.dump(result.sequences_created, f, indent=2)
                saved_paths.append(str(sequences_file))
            
            # Save capabilities if requested
            if result.capabilities_info:
                capabilities_file = output_dir / "capabilities.json"
                with open(capabilities_file, 'w') as f:
                    json.dump(result.capabilities_info, f, indent=2)
                saved_paths.append(str(capabilities_file))
            
            self.logger.info(f"Saved orchestration outputs to {len(saved_paths)} files")
            
        except Exception as e:
            self.logger.error(f"Error saving outputs: {e}")
        
        return saved_paths


# Agent metadata for registration
AGENT_METADATA = {
    "name": "EmailOrchestrationAgent",
    "description": "AI-powered email orchestration with sequences, personalization, and analytics",
    "capabilities": ["email_sequences", "ai_personalization", "send_optimization", "reply_detection", "email_warming", "analytics"],
    "inputs": ["business_idea", "user_request", "target_audience", "industry"],
    "outputs": ["email_sequences", "capabilities_info", "analytics_data", "warming_status"],
    "interactive": False,
    "dependencies": ["anthropic", "google-api-python-client", "pydantic"],
    "coordination": ["works_with_branding_agent", "works_with_market_research_agent", "integrates_with_business_workflows"]
} 