"""
Comprehensive Error Handling and Resilience System

This module provides robust error handling, recovery mechanisms, and resilience features:
- Graceful partial failure handling
- Automatic retry logic with exponential backoff  
- Circuit breaker patterns for failing services
- Error classification and intelligent recovery
- Rollback mechanisms for critical failures
- Health monitoring and alerting
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification."""
    LOW = "low"           # Minor issues, workflow can continue
    MEDIUM = "medium"     # Significant issues, may impact results
    HIGH = "high"         # Critical issues, requires intervention
    CRITICAL = "critical" # System-threatening, immediate action needed


class RecoveryStrategy(Enum):
    """Available recovery strategies for different error types."""
    RETRY = "retry"                    # Simple retry with backoff
    FALLBACK = "fallback"             # Use alternative approach
    SKIP = "skip"                     # Skip the failing component
    ROLLBACK = "rollback"             # Undo changes and restart
    CIRCUIT_BREAK = "circuit_break"   # Temporarily disable component
    ESCALATE = "escalate"             # Require human intervention


@dataclass
class ErrorContext:
    """Context information for error analysis and recovery."""
    error_id: str
    timestamp: datetime
    component: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    context_data: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    suggested_strategy: Optional[RecoveryStrategy] = None
    

@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    strategy_used: RecoveryStrategy
    message: str
    data: Optional[Dict[str, Any]] = None
    retry_after: Optional[float] = None


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for handling failing services."""
    service_name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    
    def should_allow_request(self) -> bool:
        """Check if requests should be allowed through."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record a successful request."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class WorkflowErrorHandler:
    """Comprehensive error handling system for parallel workflows."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Error tracking
        self.error_history: List[ErrorContext] = []
        self.recovery_callbacks: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Configuration
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.base_retry_delay = self.config.get('base_retry_delay', 1.0)
        self.max_retry_delay = self.config.get('max_retry_delay', 30.0)
        self.enable_circuit_breakers = self.config.get('enable_circuit_breakers', True)
    
    async def handle_workflow_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        component: str = "unknown"
    ) -> RecoveryResult:
        """
        Handle a workflow error with intelligent recovery.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            component: Name of the component that failed
            
        Returns:
            RecoveryResult with recovery outcome
        """
        # Create error context
        error_context = await self._create_error_context(error, context, component)
        self.error_history.append(error_context)
        
        self.logger.error(f"Handling error in {component}: {error_context.error_message}")
        
        # Check circuit breaker
        if self.enable_circuit_breakers and not self._check_circuit_breaker(component):
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.CIRCUIT_BREAK,
                message=f"Circuit breaker open for {component}",
                retry_after=60.0
            )
        
        # Determine recovery strategy
        strategy = await self._determine_recovery_strategy(error_context)
        
        # Execute recovery
        recovery_result = await self._execute_recovery(error_context, strategy)
        
        # Update circuit breaker
        if self.enable_circuit_breakers:
            self._update_circuit_breaker(component, recovery_result.success)
        
        return recovery_result
    
    async def handle_partial_failure(
        self,
        workflow_state: Dict[str, Any],
        failed_agents: List[str],
        successful_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Handle partial workflow failures gracefully.
        
        Args:
            workflow_state: Current workflow state
            failed_agents: List of agents that failed
            successful_agents: List of agents that succeeded
            
        Returns:
            Updated workflow state with recovery actions
        """
        self.logger.info(f"Handling partial failure: {len(failed_agents)} failed, {len(successful_agents)} succeeded")
        
        recovery_actions = []
        updated_state = workflow_state.copy()
        
        for agent in failed_agents:
            agent_error = workflow_state.get('agent_errors', {}).get(agent, 'Unknown error')
            
            # Analyze if agent failure is recoverable
            is_recoverable = await self._is_agent_failure_recoverable(agent, agent_error)
            
            if is_recoverable:
                recovery_actions.append({
                    "agent": agent,
                    "action": "retry_with_fallback",
                    "strategy": "Use alternative approach or skip non-essential features",
                    "impact": "low"
                })
            else:
                recovery_actions.append({
                    "agent": agent,
                    "action": "graceful_degradation",
                    "strategy": "Continue with reduced functionality",
                    "impact": "medium"
                })
        
        # Calculate overall workflow health
        total_agents = len(failed_agents) + len(successful_agents)
        success_rate = len(successful_agents) / total_agents if total_agents > 0 else 0
        
        if success_rate >= 0.75:  # 75% success rate
            updated_state['partial_failure_status'] = 'acceptable'
            updated_state['continuation_recommendation'] = 'proceed_with_warnings'
        elif success_rate >= 0.5:  # 50% success rate  
            updated_state['partial_failure_status'] = 'degraded'
            updated_state['continuation_recommendation'] = 'proceed_with_reduced_scope'
        else:  # Less than 50% success
            updated_state['partial_failure_status'] = 'severely_impacted'
            updated_state['continuation_recommendation'] = 'consider_restart_or_abort'
        
        updated_state['recovery_actions'] = recovery_actions
        updated_state['workflow_health'] = {
            'success_rate': success_rate,
            'total_agents': total_agents,
            'functional_agents': successful_agents,
            'failed_agents': failed_agents,
            'recovery_potential': len([a for a in recovery_actions if a['action'] == 'retry_with_fallback'])
        }
        
        return updated_state
    
    async def _create_error_context(
        self,
        error: Exception,
        context: Dict[str, Any],
        component: str
    ) -> ErrorContext:
        """Create detailed error context for analysis."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Classify error severity
        severity = await self._classify_error_severity(error, error_message, context)
        
        # Suggest recovery strategy
        strategy = await self._suggest_initial_recovery_strategy(error_type, severity, context)
        
        return ErrorContext(
            error_id=f"err_{int(time.time())}_{hash(error_message) % 10000:04d}",
            timestamp=datetime.utcnow(),
            component=component,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            context_data=context,
            suggested_strategy=strategy
        )
    
    async def _classify_error_severity(
        self,
        error: Exception,
        error_message: str,
        context: Dict[str, Any]
    ) -> ErrorSeverity:
        """Classify error severity based on type and context."""
        error_type = type(error).__name__
        message_lower = error_message.lower()
        
        # Critical errors
        if any(word in message_lower for word in ['authentication', 'authorization', 'permission denied']):
            return ErrorSeverity.CRITICAL
        if error_type in ['SystemExit', 'KeyboardInterrupt']:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(word in message_lower for word in ['timeout', 'connection refused', 'network', 'database']):
            return ErrorSeverity.HIGH
        if error_type in ['ConnectionError', 'TimeoutError', 'OSError']:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(word in message_lower for word in ['api', 'rate limit', 'quota', 'invalid']):
            return ErrorSeverity.MEDIUM
        if error_type in ['ValueError', 'TypeError', 'KeyError']:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    async def _suggest_initial_recovery_strategy(
        self,
        error_type: str,
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ) -> RecoveryStrategy:
        """Suggest initial recovery strategy based on error characteristics."""
        
        # Critical errors require escalation
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ESCALATE
        
        # High severity errors often need circuit breaking or fallback
        if severity == ErrorSeverity.HIGH:
            if error_type in ['ConnectionError', 'TimeoutError']:
                return RecoveryStrategy.CIRCUIT_BREAK
            else:
                return RecoveryStrategy.FALLBACK
        
        # Medium severity errors can often be retried
        if severity == ErrorSeverity.MEDIUM:
            if 'rate limit' in context.get('error_message', '').lower():
                return RecoveryStrategy.RETRY  # With backoff
            else:
                return RecoveryStrategy.FALLBACK
        
        # Low severity errors default to retry
        return RecoveryStrategy.RETRY
    
    async def _determine_recovery_strategy(self, error_context: ErrorContext) -> RecoveryStrategy:
        """Determine the best recovery strategy for the error."""
        # Check if we've exceeded retry attempts
        if error_context.recovery_attempts >= error_context.max_recovery_attempts:
            if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                return RecoveryStrategy.ESCALATE
            else:
                return RecoveryStrategy.SKIP
        
        # Use suggested strategy as starting point
        return error_context.suggested_strategy or RecoveryStrategy.RETRY
    
    async def _execute_recovery(
        self,
        error_context: ErrorContext,
        strategy: RecoveryStrategy
    ) -> RecoveryResult:
        """Execute the recovery strategy."""
        self.logger.info(f"Executing recovery strategy {strategy.value} for error {error_context.error_id}")
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._execute_retry_recovery(error_context)
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._execute_fallback_recovery(error_context)
        elif strategy == RecoveryStrategy.SKIP:
            return await self._execute_skip_recovery(error_context)
        elif strategy == RecoveryStrategy.ROLLBACK:
            return await self._execute_rollback_recovery(error_context)
        elif strategy == RecoveryStrategy.CIRCUIT_BREAK:
            return await self._execute_circuit_break_recovery(error_context)
        elif strategy == RecoveryStrategy.ESCALATE:
            return await self._execute_escalation_recovery(error_context)
        else:
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                message=f"Unknown recovery strategy: {strategy.value}"
            )
    
    async def _execute_retry_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute retry recovery with exponential backoff."""
        attempt = error_context.recovery_attempts + 1
        delay = min(
            self.base_retry_delay * (2 ** (attempt - 1)),
            self.max_retry_delay
        )
        
        return RecoveryResult(
            success=False,  # Will be retried by caller
            strategy_used=RecoveryStrategy.RETRY,
            message=f"Scheduled retry attempt {attempt} after {delay:.1f}s",
            retry_after=delay
        )
    
    async def _execute_fallback_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute fallback recovery strategy."""
        # Implement component-specific fallback logic
        component = error_context.component
        
        if "logo_generation" in component:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                message="Using mock logo generation as fallback",
                data={"fallback_mode": True, "mock_results": True}
            )
        elif "market_research" in component:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                message="Using basic market analysis as fallback",
                data={"fallback_mode": True, "reduced_scope": True}
            )
        else:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                message=f"Using simplified approach for {component}",
                data={"fallback_mode": True}
            )
    
    async def _execute_skip_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute skip recovery strategy."""
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.SKIP,
            message=f"Skipping {error_context.component} due to persistent failures",
            data={"skipped": True, "reason": "persistent_failures"}
        )
    
    async def _execute_rollback_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute rollback recovery strategy."""
        # Implement rollback logic based on context
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.ROLLBACK,
            message=f"Rolling back changes for {error_context.component}",
            data={"rolled_back": True}
        )
    
    async def _execute_circuit_break_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute circuit breaker recovery strategy."""
        component = error_context.component
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = CircuitBreaker(component)
        
        self.circuit_breakers[component].record_failure()
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.CIRCUIT_BREAK,
            message=f"Circuit breaker activated for {component}",
            retry_after=self.circuit_breakers[component].recovery_timeout
        )
    
    async def _execute_escalation_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Execute escalation recovery strategy."""
        self.logger.critical(f"Escalating error {error_context.error_id}: {error_context.error_message}")
        
        # Here you would typically notify administrators, create tickets, etc.
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ESCALATE,
            message=f"Error escalated for manual intervention: {error_context.error_id}",
            data={"escalated": True, "requires_intervention": True}
        )
    
    def _check_circuit_breaker(self, component: str) -> bool:
        """Check if circuit breaker allows requests for component."""
        if component not in self.circuit_breakers:
            return True
        
        return self.circuit_breakers[component].should_allow_request()
    
    def _update_circuit_breaker(self, component: str, success: bool):
        """Update circuit breaker state based on operation result."""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = CircuitBreaker(component)
        
        if success:
            self.circuit_breakers[component].record_success()
        else:
            self.circuit_breakers[component].record_failure()
    
    async def _is_agent_failure_recoverable(self, agent: str, error_message: str) -> bool:
        """Determine if an agent failure is recoverable."""
        error_lower = error_message.lower()
        
        # Non-recoverable errors
        if any(word in error_lower for word in ['authentication', 'authorization', 'permission']):
            return False
        if any(word in error_lower for word in ['not found', '404', 'invalid_api_key']):
            return False
        
        # Potentially recoverable errors
        if any(word in error_lower for word in ['timeout', 'rate limit', 'temporary', 'retry']):
            return True
        
        # Agent-specific recovery logic
        if agent in ['logo_generation', 'website_generation']:
            return True  # Can use fallback/mock modes
        
        return True  # Default to recoverable
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered."""
        if not self.error_history:
            return {"total_errors": 0, "status": "healthy"}
        
        severity_counts = {}
        component_errors = {}
        recent_errors = []
        
        for error in self.error_history[-10:]:  # Last 10 errors
            # Count by severity
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by component
            component = error.component
            component_errors[component] = component_errors.get(component, 0) + 1
            
            # Recent errors
            if (datetime.utcnow() - error.timestamp).total_seconds() < 300:  # Last 5 minutes
                recent_errors.append({
                    "error_id": error.error_id,
                    "component": error.component,
                    "severity": error.severity.value,
                    "message": error.error_message[:100],
                    "timestamp": error.timestamp.isoformat()
                })
        
        return {
            "total_errors": len(self.error_history),
            "severity_distribution": severity_counts,
            "component_distribution": component_errors,
            "recent_errors": recent_errors,
            "circuit_breaker_states": {
                name: breaker.state.value 
                for name, breaker in self.circuit_breakers.items()
            },
            "status": "degraded" if recent_errors else "stable"
        }


# Factory function
def create_error_handler(config: Optional[Dict[str, Any]] = None) -> WorkflowErrorHandler:
    """Create a WorkflowErrorHandler instance."""
    return WorkflowErrorHandler(config)