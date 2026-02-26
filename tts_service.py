"""
Text-to-Speech Service
Handles voice synthesis using ElevenLabs API
"""
import asyncio
import logging
from typing import Optional, Dict
import httpx
from pydantic import BaseModel

from app.core.config import settings, LANGUAGE_CONFIGS

logger = logging.getLogger(__name__)


class TTSResult(BaseModel):
    """Result from TTS synthesis"""
    audio_data: bytes
    duration: Optional[float] = None
    voice_id: str
    language: str


class TTSService:
    """
    Text-to-Speech service using ElevenLabs
    Generates natural-sounding voice audio
    """
    
    def __init__(self):
        """Initialize TTS service"""
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = settings.ELEVENLABS_VOICE_ID
        logger.info("TTS Service initialized with ElevenLabs")
    
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> TTSResult:
        """
        Convert text to speech
        
        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID (uses default if None)
            language: Language code
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity (0-1)
            
        Returns:
            TTSResult with audio data
        """
        try:
            # Get voice ID for language
            if not voice_id:
                voice_id = LANGUAGE_CONFIGS.get(language, {}).get(
                    "voice_id",
                    self.default_voice_id
                )
            
            logger.info(f"Synthesizing text: '{text[:50]}...' with voice {voice_id}")
            
            # Prepare request
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            # Make API call
            async with httpx.AsyncClient(timeout=settings.TTS_TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                audio_data = response.content
            
            result = TTSResult(
                audio_data=audio_data,
                voice_id=voice_id,
                language=language,
                duration=self._estimate_duration(text)
            )
            
            logger.info(f"Synthesis successful: {len(audio_data)} bytes")
            return result
            
        except httpx.TimeoutException:
            logger.error("TTS timeout exceeded")
            raise Exception("Speech synthesis timeout")
        
        except httpx.HTTPError as e:
            logger.error(f"ElevenLabs API error: {e}")
            raise Exception(f"Speech synthesis failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in TTS: {e}")
            raise Exception(f"TTS error: {str(e)}")
    
    async def synthesize_streaming(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
    ) -> asyncio.Queue:
        """
        Stream audio synthesis in chunks for lower latency
        
        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            language: Language code
            
        Returns:
            Queue of audio chunks
        """
        audio_queue = asyncio.Queue()
        
        async def stream_audio():
            try:
                # Get voice ID
                if not voice_id:
                    vid = LANGUAGE_CONFIGS.get(language, {}).get(
                        "voice_id",
                        self.default_voice_id
                    )
                else:
                    vid = voice_id
                
                url = f"{self.base_url}/text-to-speech/{vid}/stream"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key
                }
                
                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                    }
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    async with client.stream("POST", url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        
                        async for chunk in response.aiter_bytes(chunk_size=4096):
                            if chunk:
                                await audio_queue.put(chunk)
                
                # Signal end of stream
                await audio_queue.put(None)
                
            except Exception as e:
                logger.error(f"Streaming TTS error: {e}")
                await audio_queue.put(None)
        
        # Start streaming in background
        asyncio.create_task(stream_audio())
        
        return audio_queue
    
    def _estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length
        Average speaking rate: ~150 words per minute
        
        Args:
            text: Input text
            
        Returns:
            Estimated duration in seconds
        """
        words = len(text.split())
        duration = (words / 150) * 60  # Convert to seconds
        return round(duration, 2)
    
    async def get_available_voices(self) -> Dict:
        """
        Get list of available voices from ElevenLabs
        
        Returns:
            Dictionary of available voices
        """
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return {"voices": []}
    
    async def synthesize_with_emotion(
        self,
        text: str,
        emotion: str,
        language: str = "en",
    ) -> TTSResult:
        """
        Synthesize speech with emotional tone
        
        Args:
            text: Text to synthesize
            emotion: Emotion (happy, sad, neutral, excited, angry)
            language: Language code
            
        Returns:
            TTSResult with audio
        """
        # Adjust voice settings based on emotion
        emotion_settings = {
            "happy": {"stability": 0.3, "similarity_boost": 0.8},
            "sad": {"stability": 0.7, "similarity_boost": 0.6},
            "excited": {"stability": 0.2, "similarity_boost": 0.9},
            "angry": {"stability": 0.4, "similarity_boost": 0.85},
            "neutral": {"stability": 0.5, "similarity_boost": 0.75},
        }
        
        settings_dict = emotion_settings.get(emotion, emotion_settings["neutral"])
        
        return await self.synthesize(
            text=text,
            language=language,
            stability=settings_dict["stability"],
            similarity_boost=settings_dict["similarity_boost"],
        )
    
    async def synthesize_multilingual(
        self,
        text: str,
        language: str,
    ) -> TTSResult:
        """
        Synthesize text in specified language with appropriate voice
        
        Args:
            text: Text to synthesize
            language: Language code (en, hi, ta, etc.)
            
        Returns:
            TTSResult with audio
        """
        # Get language-specific voice
        voice_id = LANGUAGE_CONFIGS.get(language, {}).get(
            "voice_id",
            self.default_voice_id
        )
        
        return await self.synthesize(
            text=text,
            voice_id=voice_id,
            language=language
        )


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get or create TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
