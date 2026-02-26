"""
Context Manager Service
Manages conversation state and context using Redis
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from app.services.llm_service import Message, ConversationContext

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context with Redis storage
    Handles session persistence and context retrieval
    """
    
    def __init__(self):
        """Initialize context manager with Redis connection"""
        self.redis_url = settings.REDIS_URL
        self.ttl = settings.REDIS_TTL
        self.pool = None
        self.redis_client = None
        logger.info("Context Manager initialized")
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=10
            )
            self.redis_client = redis.Redis(connection_pool=self.pool)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fall back to in-memory storage
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            await self.pool.disconnect()
            logger.info("Disconnected from Redis")
    
    def _get_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"conversation:{session_id}"
    
    async def save_context(
        self,
        session_id: str,
        context: ConversationContext
    ) -> bool:
        """
        Save conversation context to Redis
        
        Args:
            session_id: Session identifier
            context: Conversation context to save
            
        Returns:
            True if saved successfully
        """
        try:
            if not self.redis_client:
                logger.warning("Redis not available, context not persisted")
                return False
            
            # Serialize context
            context_dict = context.model_dump()
            # Convert datetime objects to ISO format strings
            for msg in context_dict.get("messages", []):
                if "timestamp" in msg and isinstance(msg["timestamp"], datetime):
                    msg["timestamp"] = msg["timestamp"].isoformat()
            
            context_json = json.dumps(context_dict)
            
            # Save to Redis with TTL
            key = self._get_key(session_id)
            await self.redis_client.setex(
                key,
                self.ttl,
                context_json
            )
            
            logger.debug(f"Context saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            return False
    
    async def get_context(
        self,
        session_id: str
    ) -> Optional[ConversationContext]:
        """
        Retrieve conversation context from Redis
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext or None if not found
        """
        try:
            if not self.redis_client:
                return None
            
            key = self._get_key(session_id)
            context_json = await self.redis_client.get(key)
            
            if not context_json:
                logger.debug(f"No context found for session: {session_id}")
                return None
            
            # Deserialize context
            context_dict = json.loads(context_json)
            
            # Convert ISO format strings back to datetime
            for msg in context_dict.get("messages", []):
                if "timestamp" in msg and isinstance(msg["timestamp"], str):
                    msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
            
            context = ConversationContext(**context_dict)
            
            logger.debug(f"Context retrieved for session: {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to conversation context
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            metadata: Optional metadata
            
        Returns:
            True if added successfully
        """
        try:
            # Get existing context or create new
            context = await self.get_context(session_id)
            if not context:
                context = ConversationContext(
                    session_id=session_id,
                    language=settings.DEFAULT_LANGUAGE
                )
            
            # Add message
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            context.messages.append(message)
            
            # Keep only last N messages
            max_messages = settings.CONVERSATION_MEMORY_LENGTH * 2  # user + assistant
            if len(context.messages) > max_messages:
                context.messages = context.messages[-max_messages:]
            
            # Save updated context
            return await self.save_context(session_id, context)
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    async def update_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update conversation metadata
        
        Args:
            session_id: Session identifier
            metadata: Metadata to update
            
        Returns:
            True if updated successfully
        """
        try:
            context = await self.get_context(session_id)
            if not context:
                return False
            
            context.metadata.update(metadata)
            return await self.save_context(session_id, context)
            
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            return False
    
    async def delete_context(self, session_id: str) -> bool:
        """
        Delete conversation context
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            if not self.redis_client:
                return False
            
            key = self._get_key(session_id)
            await self.redis_client.delete(key)
            
            logger.debug(f"Context deleted for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return False
    
    async def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs
        
        Returns:
            List of session IDs
        """
        try:
            if not self.redis_client:
                return []
            
            # Scan for all conversation keys
            pattern = "conversation:*"
            sessions = []
            
            async for key in self.redis_client.scan_iter(match=pattern):
                session_id = key.replace("conversation:", "")
                sessions.append(session_id)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    async def extend_ttl(self, session_id: str, seconds: int = None) -> bool:
        """
        Extend TTL for a session
        
        Args:
            session_id: Session identifier
            seconds: TTL in seconds (default: settings.REDIS_TTL)
            
        Returns:
            True if extended successfully
        """
        try:
            if not self.redis_client:
                return False
            
            key = self._get_key(session_id)
            ttl = seconds or self.ttl
            
            await self.redis_client.expire(key, ttl)
            return True
            
        except Exception as e:
            logger.error(f"Error extending TTL: {e}")
            return False


# Singleton instance
_context_manager: Optional[ContextManager] = None


async def get_context_manager() -> ContextManager:
    """Get or create context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
        await _context_manager.connect()
    return _context_manager
