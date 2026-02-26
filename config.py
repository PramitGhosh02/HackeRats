"""
VoiceAI Assistant - Core Configuration
Handles all application settings, environment variables, and constants
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "VoiceAI Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = True
    
    # Security
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # Database
    DATABASE_URL: str = "postgresql://voiceai_user:password123@localhost:5432/voiceai_db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_TTL: int = 3600
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_BASE_URL: str = "https://api.groq.com/openai/v1"
    WHISPER_MODEL: str = "whisper-1"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 500
    LLM_TOP_P: float = 0.9
    
    # Anthropic (alternative)
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # ElevenLabs (TTS)
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    # Deepgram (alternative STT)
    DEEPGRAM_API_KEY: Optional[str] = None
    
    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: str = "wav"
    MAX_AUDIO_DURATION_SECONDS: int = 300
    
    # Voice Activity Detection
    VAD_ENABLED: bool = True
    SILENCE_THRESHOLD: float = 0.01
    SILENCE_DURATION: float = 1.5
    
    # Language Support
    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "bn", "mr"]
    DEFAULT_LANGUAGE: str = "en"
    ENABLE_CODE_MIXING: bool = True
    
    # Conversation
    CONVERSATION_MEMORY_LENGTH: int = 10
    
    # Feature Flags
    ENABLE_SENTIMENT_ANALYSIS: bool = True
    ENABLE_FRAUD_DETECTION: bool = True
    ENABLE_LANGUAGE_DETECTION: bool = True
    ENABLE_CALL_RECORDING: bool = True
    ENABLE_ANALYTICS: bool = True
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    SENTIMENT_THRESHOLD: float = 0.7
    
    # Fraud Detection
    FRAUD_KEYWORDS: List[str] = [
        "scam", "fake", "cheat", "unauthorized", 
        "suspicious", "hack", "fraud", "steal"
    ]
    FRAUD_CONFIDENCE_THRESHOLD: float = 0.8
    
    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./storage/recordings"
    
    # Twilio (WhatsApp)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # Performance
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_CONCURRENT_CALLS: int = 50
    REQUEST_TIMEOUT: int = 30
    STT_TIMEOUT: int = 10
    LLM_TIMEOUT: int = 15
    TTS_TIMEOUT: int = 10
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Language configurations
LANGUAGE_CONFIGS = {
    "en": {
        "name": "English",
        "native_name": "English",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "greeting": "Hello! How can I help you today?",
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "greeting": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?",
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "voice_id": "flq6f7yk4E4fJM5XTYuZ",
        "greeting": "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?",
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "voice_id": "zrHiDhphv9ZnVXBqCLjz",
        "greeting": "నమస్కారం! నేను మీకు ఎలా సహాయం చేయగలను?",
    },
    "bn": {
        "name": "Bengali",
        "native_name": "বাংলা",
        "voice_id": "N2lVS1w4EtoT3dr4eOWO",
        "greeting": "নমস্কার! আমি কিভাবে আপনাকে সাহায্য করতে পারি?",
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "voice_id": "pqHfZKP75CvOlQylNhV4",
        "greeting": "नमस्कार! मी तुम्हाला कशी मदत करू शकतो?",
    },
}

# Intent configurations
INTENT_CONFIGS = {
    "greeting": {
        "keywords": ["hello", "hi", "hey", "good morning", "good evening", "namaste"],
        "response_template": "Hello! I'm your AI assistant. How may I help you today?",
    },
    "query_status": {
        "keywords": ["status", "where is", "track", "order", "delivery"],
        "response_template": "I'll help you check the status. Could you provide more details?",
    },
    "complaint": {
        "keywords": ["complaint", "issue", "problem", "not working", "broken"],
        "response_template": "I understand you're facing an issue. Let me help resolve this.",
        "escalate": True,
    },
    "information": {
        "keywords": ["what", "how", "when", "why", "tell me", "explain"],
        "response_template": "I'd be happy to provide that information.",
    },
    "support": {
        "keywords": ["help", "support", "assist", "need help"],
        "response_template": "I'm here to help. What do you need assistance with?",
    },
    "farewell": {
        "keywords": ["bye", "goodbye", "thanks", "thank you", "that's all"],
        "response_template": "Thank you for contacting us. Have a great day!",
    },
}

# System prompts for different conversation contexts
SYSTEM_PROMPTS = {
    "default": """You are a helpful, friendly AI voice assistant for customer service. 
Your goal is to assist customers with their queries in a natural, conversational manner.

Guidelines:
- Be concise and clear in your responses (2-3 sentences max)
- Show empathy and understanding
- Ask clarifying questions when needed
- For complex issues, offer to escalate to a human agent
- Maintain a professional yet friendly tone
- Adapt to the user's language and tone
- Never make promises you can't keep""",
    
    "greeting": """You are greeting a customer who just connected. 
Be warm and welcoming. Ask how you can help them today.""",
    
    "complaint": """You are handling a customer complaint. 
Show empathy, acknowledge their frustration, and work towards a solution.
If the issue is complex, offer to escalate to a supervisor.""",
    
    "technical": """You are helping with a technical issue.
Be patient, ask diagnostic questions, and provide step-by-step guidance.""",
}

# Response templates
RESPONSE_TEMPLATES = {
    "acknowledgment": [
        "I understand.",
        "I see what you mean.",
        "Got it.",
        "I hear you.",
    ],
    "clarification": [
        "Could you please provide more details?",
        "Can you tell me more about that?",
        "I want to make sure I understand correctly. Can you elaborate?",
    ],
    "escalation": [
        "I'd like to connect you with a specialist who can better help you with this.",
        "Let me transfer you to someone who can assist you further.",
        "I think a human agent would be better suited to help with this.",
    ],
    "error": [
        "I apologize, but I'm having trouble processing that. Could you please try again?",
        "I'm sorry, I didn't quite catch that. Could you repeat?",
    ],
}

# Export settings instance
settings = get_settings()
