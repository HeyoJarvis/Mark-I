"""
Message Bus system for real-time communication between agents and components.

Features:
- Redis pub/sub for message distribution
- Topic-based messaging
- Message filtering and routing
- Real-time event streaming
- Cross-agent data sharing
"""

import asyncio
import json
import logging
import redis.asyncio as redis
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(str, Enum):
    """Message types for the message bus."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STATUS = "agent_status"
    WORKFLOW_UPDATE = "workflow_update"
    DATA_SHARED = "data_shared"
    SYSTEM_EVENT = "system_event"
    USER_EVENT = "user_event"


@dataclass
class Message:
    """Message structure for the message bus."""
    id: str
    type: MessageType
    topic: str
    source: str  # Agent ID or system component
    destination: Optional[str] = None  # Specific recipient, None for broadcast
    payload: Dict[str, Any] = None
    timestamp: datetime = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.payload is None:
            self.payload = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'topic': self.topic,
            'source': self.source,
            'destination': self.destination,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            id=data['id'],
            type=MessageType(data['type']),
            topic=data['topic'],
            source=data['source'],
            destination=data.get('destination'),
            payload=data.get('payload', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id')
        )


class MessageBus:
    """
    Redis-based message bus for real-time communication.
    
    Provides:
    - Topic-based pub/sub messaging
    - Message filtering and routing
    - Subscription management
    - Event streaming
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the message bus."""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
        
        # Subscription management
        self.subscriptions: Dict[str, Set[Callable]] = {}  # topic -> set of callbacks
        self.subscription_tasks: Dict[str, asyncio.Task] = {}
        
        # Message filtering
        self.message_filters: List[Callable[[Message], bool]] = []
        
        # Statistics
        self.messages_published = 0
        self.messages_received = 0
        self.active_subscriptions = 0
        
        self._shutdown_event = asyncio.Event()
        self.logger.info("MessageBus initialized")
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis message bus")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis and cleanup."""
        self._shutdown_event.set()
        
        # Cancel all subscription tasks
        for task in self.subscription_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.subscription_tasks:
            await asyncio.gather(*self.subscription_tasks.values(), return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("Disconnected from message bus")
    
    async def publish(
        self,
        topic: str,
        message_type: MessageType,
        source: str,
        payload: Dict[str, Any],
        destination: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            message_type: Type of message
            source: Source agent/component ID
            payload: Message payload data
            destination: Optional specific destination
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Message ID
        """
        if not self.redis_client:
            raise RuntimeError("Message bus not connected")
        
        # Create message
        import uuid
        message = Message(
            id=str(uuid.uuid4())[:8],
            type=message_type,
            topic=topic,
            source=source,
            destination=destination,
            payload=payload,
            correlation_id=correlation_id
        )
        
        # Serialize and publish
        def _default_serializer(obj):
            try:
                from datetime import datetime
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if hasattr(obj, "to_dict") and callable(obj.to_dict):
                    return obj.to_dict()
                if hasattr(obj, "__dict__"):
                    # Convert simple objects to dict safely
                    return {
                        k: v for k, v in obj.__dict__.items()
                        if not k.startswith("_") and not callable(v)
                    }
            except Exception:
                pass
            return str(obj)
        message_data = json.dumps(message.to_dict(), default=_default_serializer)
        await self.redis_client.publish(topic, message_data)
        
        self.messages_published += 1
        self.logger.debug(f"Published message {message.id} to topic {topic}")
        
        return message.id
    
    async def subscribe(
        self,
        topic: str,
        callback: Callable[[Message], Any],
        message_filter: Optional[Callable[[Message], bool]] = None
    ):
        """
        Subscribe to a topic with a callback.
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to handle messages
            message_filter: Optional filter function for messages
        """
        if not self.redis_client:
            raise RuntimeError("Message bus not connected")
        
        # Add callback to subscriptions
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
            # Start subscription task for this topic
            self.subscription_tasks[topic] = asyncio.create_task(
                self._subscription_worker(topic)
            )
        
        # Store callback with optional filter
        callback_info = (callback, message_filter)
        self.subscriptions[topic].add(callback_info)
        self.active_subscriptions += 1
        
        self.logger.debug(f"Subscribed to topic {topic}")
    
    async def unsubscribe(self, topic: str, callback: Callable[[Message], Any]):
        """Unsubscribe from a topic."""
        if topic not in self.subscriptions:
            return
        
        # Find and remove callback
        to_remove = None
        for callback_info in self.subscriptions[topic]:
            if callback_info[0] == callback:
                to_remove = callback_info
                break
        
        if to_remove:
            self.subscriptions[topic].remove(to_remove)
            self.active_subscriptions -= 1
            
            # If no more subscribers, cancel the subscription task
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
                if topic in self.subscription_tasks:
                    self.subscription_tasks[topic].cancel()
                    del self.subscription_tasks[topic]
        
        self.logger.debug(f"Unsubscribed from topic {topic}")
    
    async def subscribe_pattern(
        self,
        pattern: str,
        callback: Callable[[Message], Any],
        message_filter: Optional[Callable[[Message], bool]] = None
    ):
        """
        Subscribe to topics matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "workflow:*", "agent:status:*")
            callback: Callback function to handle messages
            message_filter: Optional filter function for messages
        """
        if not self.redis_client:
            raise RuntimeError("Message bus not connected")
        
        # Create pattern subscription task
        task_key = f"pattern:{pattern}"
        if task_key not in self.subscription_tasks:
            self.subscription_tasks[task_key] = asyncio.create_task(
                self._pattern_subscription_worker(pattern, callback, message_filter)
            )
            self.active_subscriptions += 1
        
        self.logger.debug(f"Subscribed to pattern {pattern}")
    
    def add_global_filter(self, filter_func: Callable[[Message], bool]):
        """Add a global message filter."""
        self.message_filters.append(filter_func)
    
    def remove_global_filter(self, filter_func: Callable[[Message], bool]):
        """Remove a global message filter."""
        if filter_func in self.message_filters:
            self.message_filters.remove(filter_func)
    
    async def _subscription_worker(self, topic: str):
        """Worker task for handling topic subscriptions."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(topic)
            
            while not self._shutdown_event.is_set():
                try:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        await self._process_message(topic, message['data'])
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in subscription worker for {topic}: {e}")
                    await asyncio.sleep(1.0)
            
            await pubsub.unsubscribe(topic)
            await pubsub.close()
            
        except Exception as e:
            self.logger.error(f"Subscription worker for {topic} failed: {e}")
    
    async def _pattern_subscription_worker(
        self,
        pattern: str,
        callback: Callable[[Message], Any],
        message_filter: Optional[Callable[[Message], bool]]
    ):
        """Worker task for handling pattern subscriptions."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.psubscribe(pattern)
            
            while not self._shutdown_event.is_set():
                try:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'pmessage':
                        # Parse message
                        try:
                            message_data = json.loads(message['data'])
                            parsed_message = Message.from_dict(message_data)
                            
                            # Apply global filters
                            if not self._apply_filters(parsed_message):
                                continue
                            
                            # Apply callback-specific filter
                            if message_filter and not message_filter(parsed_message):
                                continue
                            
                            # Call callback
                            if asyncio.iscoroutinefunction(callback):
                                await callback(parsed_message)
                            else:
                                callback(parsed_message)
                                
                            self.messages_received += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error processing pattern message: {e}")
                            
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in pattern subscription worker for {pattern}: {e}")
                    await asyncio.sleep(1.0)
            
            await pubsub.punsubscribe(pattern)
            await pubsub.close()
            
        except Exception as e:
            self.logger.error(f"Pattern subscription worker for {pattern} failed: {e}")
    
    async def _process_message(self, topic: str, message_data: str):
        """Process incoming message for a topic."""
        try:
            # Parse message
            message_dict = json.loads(message_data)
            message = Message.from_dict(message_dict)
            
            # Apply global filters
            if not self._apply_filters(message):
                return
            
            # Call all callbacks for this topic
            if topic in self.subscriptions:
                for callback_info in self.subscriptions[topic]:
                    callback, message_filter = callback_info
                    
                    # Apply callback-specific filter
                    if message_filter and not message_filter(message):
                        continue
                    
                    try:
                        # Call callback
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        self.logger.error(f"Error in message callback: {e}")
            
            self.messages_received += 1
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _apply_filters(self, message: Message) -> bool:
        """Apply global message filters."""
        for filter_func in self.message_filters:
            try:
                if not filter_func(message):
                    return False
            except Exception as e:
                self.logger.error(f"Error in message filter: {e}")
                return False
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            'messages_published': self.messages_published,
            'messages_received': self.messages_received,
            'active_subscriptions': self.active_subscriptions,
            'subscribed_topics': list(self.subscriptions.keys()),
            'active_tasks': len(self.subscription_tasks)
        }


class AgentMessageBusInterface:
    """
    Simplified interface for agents to interact with the message bus.
    """
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        """Initialize agent message bus interface."""
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.logger = logging.getLogger(f"agent.{agent_id}.messagebus")
    
    async def publish_task_started(self, task_id: str, task_type: str, workflow_id: Optional[str] = None):
        """Publish task started event."""
        topic = f"agent:{self.agent_id}:tasks"
        payload = {
            'task_id': task_id,
            'task_type': task_type,
            'workflow_id': workflow_id
        }
        await self.message_bus.publish(
            topic, MessageType.TASK_STARTED, self.agent_id, payload
        )
    
    async def publish_task_completed(self, task_id: str, result_data: Dict[str, Any], workflow_id: Optional[str] = None):
        """Publish task completed event."""
        topic = f"agent:{self.agent_id}:tasks"
        payload = {
            'task_id': task_id,
            'result_data': result_data,
            'workflow_id': workflow_id
        }
        await self.message_bus.publish(
            topic, MessageType.TASK_COMPLETED, self.agent_id, payload
        )
    
    async def publish_data_shared(self, data_type: str, data: Dict[str, Any], workflow_id: Optional[str] = None):
        """Publish shared data for other agents."""
        topic = f"data:{data_type}"
        if workflow_id:
            topic = f"workflow:{workflow_id}:data:{data_type}"
        
        payload = {
            'data_type': data_type,
            'data': data,
            'workflow_id': workflow_id
        }
        await self.message_bus.publish(
            topic, MessageType.DATA_SHARED, self.agent_id, payload
        )
    
    async def subscribe_to_data(self, data_type: str, callback: Callable[[Dict[str, Any]], Any], workflow_id: Optional[str] = None):
        """Subscribe to shared data of a specific type."""
        topic = f"data:{data_type}"
        if workflow_id:
            topic = f"workflow:{workflow_id}:data:{data_type}"
        
        async def message_handler(message: Message):
            if message.type == MessageType.DATA_SHARED:
                await callback(message.payload.get('data', {}))
        
        await self.message_bus.subscribe(topic, message_handler)
    
    async def subscribe_to_workflow_events(self, workflow_id: str, callback: Callable[[Message], Any]):
        """Subscribe to all events for a specific workflow."""
        pattern = f"workflow:{workflow_id}:*"
        await self.message_bus.subscribe_pattern(pattern, callback)
    
    async def publish_status_update(self, status: str, details: Dict[str, Any] = None):
        """Publish agent status update."""
        topic = f"agent:{self.agent_id}:status"
        payload = {
            'status': status,
            'details': details or {}
        }
        await self.message_bus.publish(
            topic, MessageType.AGENT_STATUS, self.agent_id, payload
        )


# Utility functions for common message patterns
def create_workflow_filter(workflow_id: str) -> Callable[[Message], bool]:
    """Create a filter for messages related to a specific workflow."""
    def filter_func(message: Message) -> bool:
        return (
            message.topic.startswith(f"workflow:{workflow_id}:") or
            message.payload.get('workflow_id') == workflow_id
        )
    return filter_func


def create_agent_filter(agent_id: str) -> Callable[[Message], bool]:
    """Create a filter for messages from a specific agent."""
    def filter_func(message: Message) -> bool:
        return message.source == agent_id
    return filter_func


def create_message_type_filter(message_type: MessageType) -> Callable[[Message], bool]:
    """Create a filter for specific message types."""
    def filter_func(message: Message) -> bool:
        return message.type == message_type
    return filter_func