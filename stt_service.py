"""
Speech-to-Text Service
Handles audio transcription using OpenAI Whisper API
"""
import asyncio
import io
import logging
from typing import Optional, Dict, Any
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionResult(BaseModel):
    """Result from STT transcription"""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None


class STTService:
    """
    Speech-to-Text service using OpenAI Whisper
    Supports multiple languages and streaming transcription
    """
    
    def __init__(self):
        """Initialize STT service with OpenAI client"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL
        logger.info(f"STT Service initialized with model: {self.model}")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio file bytes (wav, mp3, etc.)
            language: ISO-639-1 language code (en, hi, ta, etc.)
            prompt: Optional context prompt to guide transcription
            
        Returns:
            TranscriptionResult with text and metadata
        """
        try:
            logger.info(f"Transcribing audio ({len(audio_data)} bytes)")
            
            # Create audio file object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Prepare transcription parameters
            params: Dict[str, Any] = {
                "model": self.model,
                "file": audio_file,
                "response_format": "verbose_json",
            }
            
            # Add optional parameters
            if language and language != "auto":
                params["language"] = language
            
            if prompt:
                params["prompt"] = prompt
            
            # Call Whisper API
            response = await asyncio.wait_for(
                self.client.audio.transcriptions.create(**params),
                timeout=settings.STT_TIMEOUT
            )
            
            # Extract result
            result = TranscriptionResult(
                text=response.text.strip(),
                language=response.language if hasattr(response, 'language') else language,
                duration=response.duration if hasattr(response, 'duration') else None,
            )
            
            logger.info(f"Transcription successful: '{result.text[:50]}...'")
            return result
            
        except asyncio.TimeoutError:
            logger.error("STT timeout exceeded")
            raise Exception("Transcription timeout - audio too long or service unavailable")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in transcription: {e}")
            raise Exception(f"Transcription error: {str(e)}")
    
    async def transcribe_with_language_detection(
        self,
        audio_data: bytes,
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio with automatic language detection
        
        Args:
            audio_data: Audio file bytes
            prompt: Optional context prompt
            
        Returns:
            TranscriptionResult with detected language
        """
        return await self.transcribe(
            audio_data=audio_data,
            language=None,  # Let Whisper auto-detect
            prompt=prompt
        )
    
    async def transcribe_streaming(
        self,
        audio_stream: asyncio.Queue,
        language: Optional[str] = None
    ) -> asyncio.Queue:
        """
        Transcribe audio stream in real-time
        
        Args:
            audio_stream: Queue of audio chunks
            language: Target language
            
        Returns:
            Queue of transcription results
        """
        result_queue = asyncio.Queue()
        
        async def process_stream():
            buffer = bytearray()
            min_chunk_size = 16000 * 2  # 1 second at 16kHz, 16-bit
            
            try:
                while True:
                    # Get audio chunk
                    chunk = await audio_stream.get()
                    
                    if chunk is None:  # End of stream
                        # Process remaining buffer
                        if len(buffer) >= min_chunk_size:
                            result = await self.transcribe(bytes(buffer), language)
                            await result_queue.put(result)
                        break
                    
                    # Add to buffer
                    buffer.extend(chunk)
                    
                    # Process when buffer is large enough
                    if len(buffer) >= min_chunk_size * 3:  # 3 seconds
                        result = await self.transcribe(bytes(buffer), language)
                        await result_queue.put(result)
                        buffer.clear()
                
                # Signal end of results
                await result_queue.put(None)
                
            except Exception as e:
                logger.error(f"Streaming transcription error: {e}")
                await result_queue.put(None)
        
        # Start processing in background
        asyncio.create_task(process_stream())
        
        return result_queue
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on script
        (For production, use langdetect or similar)
        
        Args:
            text: Input text
            
        Returns:
            ISO-639-1 language code
        """
        # Check for Devanagari script (Hindi/Marathi)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return 'hi'
        
        # Check for Tamil script
        if any('\u0B80' <= char <= '\u0BFF' for char in text):
            return 'ta'
        
        # Check for Telugu script
        if any('\u0C00' <= char <= '\u0C7F' for char in text):
            return 'te'
        
        # Check for Bengali script
        if any('\u0980' <= char <= '\u09FF' for char in text):
            return 'bn'
        
        # Default to English
        return 'en'
    
    async def transcribe_with_context(
        self,
        audio_data: bytes,
        conversation_history: list[str],
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe with conversation context for better accuracy
        
        Args:
            audio_data: Audio file bytes
            conversation_history: Previous messages for context
            language: Target language
            
        Returns:
            TranscriptionResult
        """
        # Build context prompt from history
        prompt = " ".join(conversation_history[-3:]) if conversation_history else None
        
        return await self.transcribe(
            audio_data=audio_data,
            language=language,
            prompt=prompt
        )


# Singleton instance
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Get or create STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
