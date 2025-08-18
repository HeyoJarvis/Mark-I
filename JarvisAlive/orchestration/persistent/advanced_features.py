"""
Advanced Features for Persistent Agent System.

This module provides:
- Advanced inter-agent communication patterns
- Workflow performance analytics and optimization
- Comprehensive error recovery and failover
- Workflow templates and pattern recognition
- Advanced monitoring and alerting
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .message_bus import MessageBus, MessageType, Message
from .persistent_system import PersistentSystem


class CommunicationPattern(str, Enum):
    """Inter-agent communication patterns."""
    BROADCAST = "broadcast"
    DIRECT_MESSAGE = "direct_message"
    PUBLISH_SUBSCRIBE = "publish_subscribe"
    REQUEST_RESPONSE = "request_response"
    WORKFLOW_CHAIN = "workflow_chain"
    DATA_PIPELINE = "data_pipeline"


@dataclass
class WorkflowTemplate:
    """Template for common workflow patterns."""
    template_id: str
    name: str
    description: str
    workflow_type: str
    task_sequence: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    estimated_duration: int
    complexity_score: float
    usage_count: int = 0
    success_rate: float = 0.0
    average_duration: float = 0.0


@dataclass
class PerformanceAlert:
    """Performance monitoring alert."""
    alert_id: str
    severity: str  # low, medium, high, critical
    category: str  # performance, error, resource, workflow
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class InterAgentCommunicationManager:
    """Manages advanced inter-agent communication patterns."""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.logger = logging.getLogger(__name__)
        
        # Communication tracking
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        self.communication_patterns: Dict[str, int] = {}
        self.data_flows: Dict[str, List[Dict[str, Any]]] = {}
        
        # Optimization features
        self.message_priorities = {
            'urgent': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        
        # Communication analytics
        self.message_metrics = {
            'total_messages': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'average_response_time': 0.0
        }
    
    async def initiate_agent_collaboration(
        self,
        initiator_agent: str,
        target_agents: List[str],
        collaboration_type: CommunicationPattern,
        task_context: Dict[str, Any]
    ) -> str:
        """Initiate collaboration between agents."""
        
        collaboration_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"Initiating {collaboration_type.value} collaboration {collaboration_id}")
        
        collaboration_config = {
            'collaboration_id': collaboration_id,
            'initiator': initiator_agent,
            'participants': target_agents,
            'pattern': collaboration_type.value,
            'context': task_context,
            'started_at': datetime.utcnow(),
            'status': 'active'
        }
        
        self.active_conversations[collaboration_id] = collaboration_config
        
        if collaboration_type == CommunicationPattern.BROADCAST:
            await self._setup_broadcast_communication(collaboration_config)
        elif collaboration_type == CommunicationPattern.WORKFLOW_CHAIN:
            await self._setup_workflow_chain(collaboration_config)
        elif collaboration_type == CommunicationPattern.DATA_PIPELINE:
            await self._setup_data_pipeline(collaboration_config)
        elif collaboration_type == CommunicationPattern.REQUEST_RESPONSE:
            await self._setup_request_response(collaboration_config)
        
        return collaboration_id
    
    async def _setup_broadcast_communication(self, config: Dict[str, Any]):
        """Setup broadcast communication pattern."""
        collaboration_id = config['collaboration_id']
        topic = f"collaboration:{collaboration_id}:broadcast"
        
        # Publish initiation message
        await self.message_bus.publish(
            topic=topic,
            message_type=MessageType.SYSTEM_EVENT,
            source=config['initiator'],
            payload={
                'event': 'collaboration_start',
                'collaboration_id': collaboration_id,
                'pattern': 'broadcast',
                'context': config['context']
            }
        )
        
        self.logger.debug(f"Setup broadcast communication for {collaboration_id}")
    
    async def _setup_workflow_chain(self, config: Dict[str, Any]):
        """Setup workflow chain communication pattern."""
        collaboration_id = config['collaboration_id']
        participants = config['participants']
        
        # Create chain sequence
        for i, agent in enumerate(participants):
            next_agent = participants[i + 1] if i + 1 < len(participants) else None
            
            topic = f"workflow_chain:{collaboration_id}:{agent}"
            
            await self.message_bus.publish(
                topic=topic,
                message_type=MessageType.WORKFLOW_UPDATE,
                source=config['initiator'],
                payload={
                    'event': 'chain_setup',
                    'collaboration_id': collaboration_id,
                    'current_agent': agent,
                    'next_agent': next_agent,
                    'chain_position': i,
                    'context': config['context']
                }
            )
        
        self.logger.debug(f"Setup workflow chain for {collaboration_id}")
    
    async def _setup_data_pipeline(self, config: Dict[str, Any]):
        """Setup data pipeline communication pattern."""
        collaboration_id = config['collaboration_id']
        
        # Create pipeline configuration
        pipeline_config = {
            'pipeline_id': collaboration_id,
            'stages': config['participants'],
            'data_flow': 'sequential',
            'error_handling': 'continue_on_error',
            'validation': True
        }
        
        topic = f"data_pipeline:{collaboration_id}:config"
        
        await self.message_bus.publish(
            topic=topic,
            message_type=MessageType.SYSTEM_EVENT,
            source=config['initiator'],
            payload={
                'event': 'pipeline_setup',
                'pipeline_config': pipeline_config,
                'context': config['context']
            }
        )
        
        self.logger.debug(f"Setup data pipeline for {collaboration_id}")
    
    async def _setup_request_response(self, config: Dict[str, Any]):
        """Setup request-response communication pattern."""
        collaboration_id = config['collaboration_id']
        
        # Setup response tracking
        for target_agent in config['participants']:
            topic = f"request_response:{collaboration_id}:{target_agent}"
            
            await self.message_bus.publish(
                topic=topic,
                message_type=MessageType.SYSTEM_EVENT,
                source=config['initiator'],
                payload={
                    'event': 'request_setup',
                    'collaboration_id': collaboration_id,
                    'requester': config['initiator'],
                    'responder': target_agent,
                    'timeout': 300,
                    'context': config['context']
                }
            )
        
        self.logger.debug(f"Setup request-response for {collaboration_id}")
    
    async def send_priority_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Dict[str, Any],
        priority: str = 'medium'
    ) -> str:
        """Send a priority message between agents."""
        
        message_id = str(uuid.uuid4())[:8]
        
        topic = f"agent:{recipient}:priority_messages"
        
        await self.message_bus.publish(
            topic=topic,
            message_type=MessageType.DATA_SHARED,
            source=sender,
            payload={
                'message_id': message_id,
                'sender': sender,
                'recipient': recipient,
                'priority': priority,
                'priority_score': self.message_priorities.get(priority, 3),
                'message_type': message_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        self.message_metrics['total_messages'] += 1
        
        return message_id
    
    async def share_data_between_agents(
        self,
        sender: str,
        data_type: str,
        data: Dict[str, Any],
        target_agents: Optional[List[str]] = None,
        workflow_id: Optional[str] = None
    ):
        """Share data between agents with validation and transformation."""
        
        # Validate data
        validated_data = await self._validate_shared_data(data_type, data)
        
        # Transform data if needed
        transformed_data = await self._transform_data_for_sharing(data_type, validated_data)
        
        # Determine sharing scope
        if target_agents:
            # Direct sharing
            for agent in target_agents:
                topic = f"agent:{agent}:shared_data"
                await self._publish_data_share(topic, sender, data_type, transformed_data, workflow_id)
        else:
            # Broadcast sharing
            topic = f"shared_data:{data_type}"
            if workflow_id:
                topic = f"workflow:{workflow_id}:shared_data:{data_type}"
            
            await self._publish_data_share(topic, sender, data_type, transformed_data, workflow_id)
        
        # Track data flow
        self._record_data_flow(sender, data_type, target_agents, workflow_id)
    
    async def _validate_shared_data(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate shared data before distribution."""
        
        # Basic validation rules
        validation_rules = {
            'market_research': ['market_size', 'target_audience'],
            'branding': ['brand_name', 'logo_prompt'],
            'analysis_results': ['results', 'confidence_score']
        }
        
        required_fields = validation_rules.get(data_type, [])
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' for data type '{data_type}'")
        
        return data
    
    async def _transform_data_for_sharing(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data for sharing between agents."""
        
        # Add metadata
        transformed_data = {
            **data,
            'shared_at': datetime.utcnow().isoformat(),
            'data_type': data_type,
            'version': '1.0'
        }
        
        # Type-specific transformations
        if data_type == 'market_research':
            # Standardize market research format
            if 'market_size' in transformed_data:
                market_size = transformed_data['market_size']
                if isinstance(market_size, str):
                    transformed_data['market_size'] = {'description': market_size}
        
        return transformed_data
    
    async def _publish_data_share(
        self,
        topic: str,
        sender: str,
        data_type: str,
        data: Dict[str, Any],
        workflow_id: Optional[str]
    ):
        """Publish data share message."""
        
        await self.message_bus.publish(
            topic=topic,
            message_type=MessageType.DATA_SHARED,
            source=sender,
            payload={
                'data_type': data_type,
                'data': data,
                'workflow_id': workflow_id,
                'shared_by': sender
            }
        )
    
    def _record_data_flow(
        self,
        sender: str,
        data_type: str,
        target_agents: Optional[List[str]],
        workflow_id: Optional[str]
    ):
        """Record data flow for analytics."""
        
        flow_record = {
            'sender': sender,
            'data_type': data_type,
            'targets': target_agents or ['broadcast'],
            'workflow_id': workflow_id,
            'timestamp': datetime.utcnow(),
            'flow_id': str(uuid.uuid4())[:8]
        }
        
        if sender not in self.data_flows:
            self.data_flows[sender] = []
        
        self.data_flows[sender].append(flow_record)
        
        # Keep only recent flows
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.data_flows[sender] = [
            flow for flow in self.data_flows[sender]
            if flow['timestamp'] > cutoff_time
        ]
    
    def get_communication_analytics(self) -> Dict[str, Any]:
        """Get communication analytics and metrics."""
        
        return {
            'message_metrics': self.message_metrics,
            'active_collaborations': len(self.active_conversations),
            'communication_patterns': self.communication_patterns,
            'data_flow_summary': {
                'total_agents_sharing': len(self.data_flows),
                'total_flows_today': sum(
                    len([flow for flow in flows if flow['timestamp'] > datetime.utcnow() - timedelta(days=1)])
                    for flows in self.data_flows.values()
                )
            }
        }


class WorkflowTemplateManager:
    """Manages workflow templates and pattern recognition."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.pattern_history: List[Dict[str, Any]] = []
        
        # Initialize standard templates
        self._initialize_standard_templates()
    
    def _initialize_standard_templates(self):
        """Initialize standard workflow templates."""
        
        # Business Creation Template
        business_creation_template = WorkflowTemplate(
            template_id="business_creation_standard",
            name="Standard Business Creation",
            description="Complete business creation workflow with market research and branding",
            workflow_type="business_creation",
            task_sequence=[
                {
                    'step': 1,
                    'task_type': 'market_opportunity_analysis',
                    'description': 'Analyze market opportunity and size',
                    'parallel_group': 'research',
                    'estimated_duration': 300
                },
                {
                    'step': 2,
                    'task_type': 'competitive_analysis',
                    'description': 'Analyze competitive landscape',
                    'parallel_group': 'research',
                    'estimated_duration': 240
                },
                {
                    'step': 3,
                    'task_type': 'brand_name_generation',
                    'description': 'Generate brand name options',
                    'parallel_group': 'branding',
                    'estimated_duration': 180
                },
                {
                    'step': 4,
                    'task_type': 'logo_prompt_creation',
                    'description': 'Create logo design prompt',
                    'dependencies': ['brand_name_generation'],
                    'estimated_duration': 120
                },
                {
                    'step': 5,
                    'task_type': 'business_plan_synthesis',
                    'description': 'Synthesize research into business plan',
                    'dependencies': ['market_opportunity_analysis', 'competitive_analysis', 'brand_name_generation'],
                    'estimated_duration': 600
                }
            ],
            success_criteria={
                'min_completed_steps': 4,
                'required_outputs': ['market_analysis', 'brand_identity', 'business_plan'],
                'quality_threshold': 0.8
            },
            estimated_duration=1440,  # 24 minutes
            complexity_score=7.5
        )
        
        self.templates[business_creation_template.template_id] = business_creation_template
        
        # Quick Analysis Template
        quick_analysis_template = WorkflowTemplate(
            template_id="quick_analysis",
            name="Quick Market Analysis",
            description="Fast market analysis for existing business ideas",
            workflow_type="market_analysis",
            task_sequence=[
                {
                    'step': 1,
                    'task_type': 'market_opportunity_analysis',
                    'description': 'Quick market opportunity assessment',
                    'estimated_duration': 180
                },
                {
                    'step': 2,
                    'task_type': 'competitive_analysis',
                    'description': 'Basic competitive analysis',
                    'estimated_duration': 120
                }
            ],
            success_criteria={
                'min_completed_steps': 2,
                'required_outputs': ['market_size', 'competition_overview'],
                'quality_threshold': 0.7
            },
            estimated_duration=300,  # 5 minutes
            complexity_score=3.0
        )
        
        self.templates[quick_analysis_template.template_id] = quick_analysis_template
    
    async def recommend_template(
        self,
        workflow_type: str,
        user_requirements: Dict[str, Any],
        complexity_preference: str = 'medium'
    ) -> Optional[WorkflowTemplate]:
        """Recommend the best template based on requirements."""
        
        matching_templates = [
            template for template in self.templates.values()
            if template.workflow_type == workflow_type
        ]
        
        if not matching_templates:
            return None
        
        # Score templates based on requirements
        template_scores = {}
        
        for template in matching_templates:
            score = 0
            
            # Complexity preference
            complexity_map = {'low': 3, 'medium': 6, 'high': 9}
            preferred_complexity = complexity_map.get(complexity_preference, 6)
            complexity_diff = abs(template.complexity_score - preferred_complexity)
            score += max(0, 10 - complexity_diff)
            
            # Success rate
            score += template.success_rate * 10
            
            # Usage frequency (popular templates get bonus)
            if template.usage_count > 10:
                score += 2
            
            # Duration preference
            max_duration = user_requirements.get('max_duration', 3600)  # 1 hour default
            if template.estimated_duration <= max_duration:
                score += 5
            
            template_scores[template.template_id] = score
        
        # Return highest scoring template
        best_template_id = max(template_scores, key=template_scores.get)
        recommended_template = self.templates[best_template_id]
        
        self.logger.info(f"Recommended template: {recommended_template.name} (score: {template_scores[best_template_id]})")
        
        return recommended_template
    
    def create_custom_template(
        self,
        name: str,
        workflow_type: str,
        task_sequence: List[Dict[str, Any]],
        user_id: str
    ) -> str:
        """Create a custom workflow template."""
        
        template_id = f"custom_{user_id}_{str(uuid.uuid4())[:8]}"
        
        # Calculate estimated duration
        total_duration = sum(task.get('estimated_duration', 300) for task in task_sequence)
        
        # Calculate complexity score
        complexity_factors = {
            'num_tasks': len(task_sequence),
            'has_dependencies': any('dependencies' in task for task in task_sequence),
            'parallel_tasks': len(set(task.get('parallel_group') for task in task_sequence if task.get('parallel_group')))
        }
        
        complexity_score = (
            complexity_factors['num_tasks'] * 0.5 +
            (5 if complexity_factors['has_dependencies'] else 0) +
            complexity_factors['parallel_tasks'] * 0.3
        )
        
        custom_template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=f"Custom template created by user {user_id}",
            workflow_type=workflow_type,
            task_sequence=task_sequence,
            success_criteria={
                'min_completed_steps': max(1, len(task_sequence) - 1),
                'quality_threshold': 0.7
            },
            estimated_duration=total_duration,
            complexity_score=complexity_score
        )
        
        self.templates[template_id] = custom_template
        
        self.logger.info(f"Created custom template: {name} ({template_id})")
        
        return template_id
    
    def update_template_metrics(
        self,
        template_id: str,
        success: bool,
        actual_duration: float
    ):
        """Update template metrics based on usage."""
        
        if template_id not in self.templates:
            return
        
        template = self.templates[template_id]
        template.usage_count += 1
        
        # Update success rate
        total_successes = template.success_rate * (template.usage_count - 1)
        if success:
            total_successes += 1
        template.success_rate = total_successes / template.usage_count
        
        # Update average duration
        total_duration = template.average_duration * (template.usage_count - 1)
        total_duration += actual_duration
        template.average_duration = total_duration / template.usage_count
        
        self.logger.debug(f"Updated metrics for template {template_id}: success_rate={template.success_rate:.2f}, avg_duration={template.average_duration:.1f}")
    
    def get_template_analytics(self) -> Dict[str, Any]:
        """Get analytics about template usage and performance."""
        
        if not self.templates:
            return {}
        
        templates_list = list(self.templates.values())
        
        return {
            'total_templates': len(templates_list),
            'most_popular_template': max(templates_list, key=lambda t: t.usage_count).name,
            'highest_success_rate': max(templates_list, key=lambda t: t.success_rate).success_rate,
            'average_complexity': statistics.mean([t.complexity_score for t in templates_list]),
            'template_distribution': {
                template.workflow_type: len([t for t in templates_list if t.workflow_type == template.workflow_type])
                for template in templates_list
            }
        }


class PerformanceAnalyticsEngine:
    """Advanced performance analytics and monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alerts: List[PerformanceAlert] = []
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Initialize alert rules
        self._initialize_alert_rules()
    
    def _initialize_alert_rules(self):
        """Initialize performance alert rules."""
        
        self.alert_rules = {
            'high_error_rate': {
                'condition': lambda metrics: metrics.get('error_rate', 0) > 0.15,
                'severity': 'high',
                'category': 'error',
                'message': 'Error rate exceeds 15%'
            },
            'low_success_rate': {
                'condition': lambda metrics: metrics.get('success_rate', 1.0) < 0.80,
                'severity': 'medium',
                'category': 'performance',
                'message': 'Success rate below 80%'
            },
            'high_response_time': {
                'condition': lambda metrics: metrics.get('average_response_time', 0) > 300,
                'severity': 'medium',
                'category': 'performance',
                'message': 'Average response time exceeds 5 minutes'
            },
            'resource_exhaustion': {
                'condition': lambda metrics: metrics.get('resource_utilization', 0) > 0.90,
                'severity': 'critical',
                'category': 'resource',
                'message': 'Resource utilization exceeds 90%'
            },
            'workflow_backlog': {
                'condition': lambda metrics: metrics.get('pending_workflows', 0) > 10,
                'severity': 'high',
                'category': 'workflow',
                'message': 'Workflow backlog exceeds 10 pending items'
            }
        }
    
    async def analyze_system_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system performance and generate insights."""
        
        # Record metrics
        timestamp = datetime.utcnow()
        metric_record = {
            **metrics,
            'timestamp': timestamp
        }
        
        for metric_name, value in metrics.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
            
            self.metrics_history[metric_name].append({
                'value': value,
                'timestamp': timestamp
            })
            
            # Keep only recent history
            cutoff_time = timestamp - timedelta(hours=24)
            self.metrics_history[metric_name] = [
                record for record in self.metrics_history[metric_name]
                if record['timestamp'] > cutoff_time
            ]
        
        # Check for alerts
        new_alerts = []
        for rule_name, rule in self.alert_rules.items():
            if rule['condition'](metrics):
                alert = PerformanceAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    severity=rule['severity'],
                    category=rule['category'],
                    message=rule['message'],
                    details={'metrics': metrics, 'rule': rule_name},
                    timestamp=timestamp
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
        
        # Generate analysis
        analysis = {
            'timestamp': timestamp.isoformat(),
            'metrics_analyzed': len(metrics),
            'alerts_triggered': len(new_alerts),
            'performance_score': self._calculate_performance_score(metrics),
            'trends': self._analyze_trends(),
            'recommendations': self._generate_recommendations(metrics),
            'new_alerts': [
                {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity,
                    'message': alert.message
                }
                for alert in new_alerts
            ]
        }
        
        return analysis
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        
        base_score = 100.0
        
        # Deduct for high error rate
        error_rate = metrics.get('error_rate', 0)
        base_score -= error_rate * 50
        
        # Deduct for low success rate
        success_rate = metrics.get('success_rate', 1.0)
        base_score -= (1.0 - success_rate) * 30
        
        # Deduct for high response time
        response_time = metrics.get('average_response_time', 0)
        if response_time > 120:  # 2 minutes
            base_score -= min(20, (response_time - 120) / 60 * 5)
        
        # Deduct for high resource utilization
        resource_util = metrics.get('resource_utilization', 0)
        if resource_util > 0.8:
            base_score -= (resource_util - 0.8) * 50
        
        return max(0.0, base_score)
    
    def _analyze_trends(self) -> Dict[str, str]:
        """Analyze performance trends."""
        
        trends = {}
        
        for metric_name, history in self.metrics_history.items():
            if len(history) < 2:
                trends[metric_name] = 'insufficient_data'
                continue
            
            # Calculate trend
            recent_values = [record['value'] for record in history[-5:]]  # Last 5 values
            older_values = [record['value'] for record in history[-10:-5]]  # Previous 5 values
            
            if not older_values:
                trends[metric_name] = 'insufficient_data'
                continue
            
            recent_avg = statistics.mean(recent_values)
            older_avg = statistics.mean(older_values)
            
            change_pct = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
            
            if abs(change_pct) < 5:
                trends[metric_name] = 'stable'
            elif change_pct > 5:
                trends[metric_name] = 'increasing'
            else:
                trends[metric_name] = 'decreasing'
        
        return trends
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        
        recommendations = []
        
        # Error rate recommendations
        if metrics.get('error_rate', 0) > 0.10:
            recommendations.append("High error rate detected - review error logs and implement additional error handling")
        
        # Success rate recommendations
        if metrics.get('success_rate', 1.0) < 0.85:
            recommendations.append("Low success rate - consider improving task validation and retry mechanisms")
        
        # Response time recommendations
        response_time = metrics.get('average_response_time', 0)
        if response_time > 240:  # 4 minutes
            recommendations.append("High response time - consider optimizing agent processing or adding more agent instances")
        elif response_time > 120:  # 2 minutes
            recommendations.append("Moderate response time - monitor for further increases")
        
        # Resource utilization recommendations
        resource_util = metrics.get('resource_utilization', 0)
        if resource_util > 0.85:
            recommendations.append("High resource utilization - consider scaling up agent capacity")
        
        # Workflow-specific recommendations
        pending_workflows = metrics.get('pending_workflows', 0)
        if pending_workflows > 5:
            recommendations.append("Workflow backlog building - consider increasing concurrent execution capacity")
        
        return recommendations
    
    def get_alert_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
        
        if not recent_alerts:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_category': {},
                'resolution_rate': 0.0
            }
        
        severity_counts = {}
        category_counts = {}
        resolved_count = 0
        
        for alert in recent_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
            category_counts[alert.category] = category_counts.get(alert.category, 0) + 1
            if alert.resolved:
                resolved_count += 1
        
        resolution_rate = resolved_count / len(recent_alerts) * 100 if recent_alerts else 0
        
        return {
            'total_alerts': len(recent_alerts),
            'by_severity': severity_counts,
            'by_category': category_counts,
            'resolution_rate': resolution_rate,
            'most_recent_alert': recent_alerts[-1].message if recent_alerts else None
        }
    
    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """Mark an alert as resolved."""
        
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                self.logger.info(f"Resolved alert {alert_id}: {resolution_note}")
                break