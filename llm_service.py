"""
LLM Service
Handles conversation logic using OpenAI GPT-4
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.core.config import settings, SYSTEM_PROMPTS, LANGUAGE_CONFIGS

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Conversation message"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: datetime = datetime.utcnow()
    metadata: Optional[Dict[str, Any]] = None


class ConversationContext(BaseModel):
    """Conversation context and history"""
    session_id: str
    user_id: Optional[str] = None
    language: str = "en"
    messages: List[Message] = []
    detected_intent: Optional[str] = None
    sentiment_score: Optional[float] = None
    metadata: Dict[str, Any] = {}


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None
    intent: Optional[str] = None


class LLMService:
    """
    LLM service for intelligent conversation
    Uses OpenAI GPT-4 for natural language understanding and generation
    """
    
    def __init__(self):
        """Initialize LLM service"""
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        logger.info(f"LLM Service initialized with model: {self.model}")
    
    async def generate_response(
        self,
        context: ConversationContext,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate AI response based on conversation context
        
        Args:
            context: Conversation context with history
            user_message: Latest user message
            system_prompt: Optional custom system prompt
            
        Returns:
            LLMResponse with generated content
        """
        try:
            # Build messages list
            messages = self._build_messages(
                context=context,
                user_message=user_message,
                system_prompt=system_prompt
            )
            
            logger.info(f"Generating response for: '{user_message[:50]}...'")
            
            # Call GPT-4 API
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=settings.LLM_TOP_P,
                ),
                timeout=settings.LLM_TIMEOUT
            )
            
            # Extract response
            choice = response.choices[0]
            content = choice.message.content.strip()
            
            # Detect intent from response
            intent = self._detect_intent(user_message)
            
            result = LLMResponse(
                content=content,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                intent=intent
            )
            
            logger.info(f"Response generated: '{content[:50]}...'")
            return result
            
        except asyncio.TimeoutError:
            logger.error("LLM timeout exceeded")
            raise Exception("Response generation timeout")
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _build_messages(
        self,
        context: ConversationContext,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build messages list for LLM API call
        
        Args:
            context: Conversation context
            user_message: Latest user message
            system_prompt: Custom system prompt
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt
        if system_prompt:
            prompt = system_prompt
        else:
            # Use default or context-specific prompt
            prompt = SYSTEM_PROMPTS.get("default", "You are a helpful assistant.")
            
            # Add language-specific instructions
            if context.language != "en":
                lang_name = LANGUAGE_CONFIGS.get(context.language, {}).get("name", context.language)
                prompt += f"\n\nThe user prefers to communicate in {lang_name}. Respond in {lang_name} when appropriate."
        
        messages.append({"role": "system", "content": prompt})
        
        # Add conversation history (last N messages)
        history_limit = settings.CONVERSATION_MEMORY_LENGTH
        recent_messages = context.messages[-history_limit:] if context.messages else []
        
        for msg in recent_messages:
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _detect_intent(self, text: str) -> Optional[str]:
        """
        Simple intent detection based on keywords
        (For production, use a proper intent classifier)
        
        Args:
            text: User message
            
        Returns:
            Detected intent or None
        """
        text_lower = text.lower()
        
        # Check each intent's keywords
        from app.core.config import INTENT_CONFIGS
        
        for intent, config in INTENT_CONFIGS.items():
            keywords = config.get("keywords", [])
            if any(keyword in text_lower for keyword in keywords):
                return intent
        
        return None
    
    async def generate_contextual_greeting(
        self,
        language: str = "en",
        user_name: Optional[str] = None,
        time_of_day: Optional[str] = None
    ) -> str:
        """
        Generate a contextual greeting
        
        Args:
            language: User's language
            user_name: User's name if known
            time_of_day: morning, afternoon, evening
            
        Returns:
            Greeting message
        """
        # Get default greeting for language
        greeting = LANGUAGE_CONFIGS.get(language, {}).get(
            "greeting",
            "Hello! How can I help you today?"
        )
        
        # Personalize if name is available
        if user_name:
            greeting = greeting.replace("!", f", {user_name}!")
        
        return greeting
    
    async def summarize_conversation(
        self,
        context: ConversationContext
    ) -> str:
        """
        Generate a summary of the conversation
        
        Args:
            context: Conversation context
            
        Returns:
            Summary text
        """
        if not context.messages:
            return "No conversation to summarize."
        
        # Build conversation text
        conversation = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in context.messages
        ])
        
        # Ask LLM to summarize
        messages = [
            {
                "role": "system",
                "content": "Summarize the following conversation in 2-3 sentences."
            },
            {
                "role": "user",
                "content": conversation
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for factual summary
                max_tokens=150,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Unable to generate summary."
    
    async def should_escalate(
        self,
        context: ConversationContext,
        user_message: str
    ) -> bool:
        """
        Determine if conversation should be escalated to human
        
        Args:
            context: Conversation context
            user_message: Latest message
            
        Returns:
            True if should escalate
        """
        # Check for escalation keywords
        escalation_keywords = [
            "speak to human", "human agent", "supervisor",
            "manager", "escalate", "representative",
            "not satisfied", "frustrated", "angry"
        ]
        
        text_lower = user_message.lower()
        if any(keyword in text_lower for keyword in escalation_keywords):
            return True
        
        # Check sentiment if available
        if context.sentiment_score is not None and context.sentiment_score < 0.3:
            # Negative sentiment over multiple turns
            recent_sentiments = [
                msg.metadata.get("sentiment", 0.5)
                for msg in context.messages[-3:]
                if msg.metadata and "sentiment" in msg.metadata
            ]
            if len(recent_sentiments) >= 2 and all(s < 0.4 for s in recent_sentiments):
                return True
        
        # Check for repeated similar messages (user not getting help)
        if len(context.messages) >= 4:
            recent_user_msgs = [
                msg.content.lower()
                for msg in context.messages[-4:]
                if msg.role == "user"
            ]
            if len(recent_user_msgs) >= 2:
                # Simple similarity check
                if recent_user_msgs[-1] == recent_user_msgs[-2]:
                    return True
        
        return False
    
    async def generate_follow_up_questions(
        self,
        context: ConversationContext,
        count: int = 3
    ) -> List[str]:
        """
        Generate suggested follow-up questions
        
        Args:
            context: Conversation context
            count: Number of questions to generate
            
        Returns:
            List of suggested questions
        """
        if not context.messages:
            return [
                "How can I assist you today?",
                "What information are you looking for?",
                "Is there anything specific you'd like help with?"
            ]
        
        # Get last assistant message
        last_response = next(
            (msg.content for msg in reversed(context.messages) if msg.role == "assistant"),
            None
        )
        
        if not last_response:
            return []
        
        # Ask LLM to generate follow-ups
        prompt = f"""Based on this response, suggest {count} natural follow-up questions a user might ask:
        
"{last_response}"

Return only the questions, one per line."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate helpful follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150,
            )
            
            questions = response.choices[0].message.content.strip().split("\n")
            # Clean up questions
            questions = [q.strip("- ").strip() for q in questions if q.strip()]
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Error generating follow-ups: {e}")
            return []


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
