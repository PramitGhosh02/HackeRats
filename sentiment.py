"""
Sentiment Analysis Service
Detects emotions and sentiment in user messages
"""
import logging
from typing import Optional, Dict
from pydantic import BaseModel
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    score: float  # -1.0 (negative) to 1.0 (positive)
    magnitude: float  # 0.0 to 1.0 (intensity)
    label: str  # positive, negative, neutral
    emotion: Optional[str] = None  # happy, sad, angry, frustrated, calm
    confidence: float = 0.0


class SentimentService:
    """
    Sentiment analysis service
    Analyzes emotional tone of user messages
    """
    
    def __init__(self):
        """Initialize sentiment service"""
        self.threshold_positive = 0.2
        self.threshold_negative = -0.2
        logger.info("Sentiment Service initialized")
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text
        
        Args:
            text: Input text
            
        Returns:
            SentimentResult with score and label
        """
        try:
            # Use TextBlob for basic sentiment
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Determine label
            if polarity > self.threshold_positive:
                label = "positive"
            elif polarity < self.threshold_negative:
                label = "negative"
            else:
                label = "neutral"
            
            # Detect emotion based on keywords and polarity
            emotion = self._detect_emotion(text, polarity)
            
            # Calculate confidence (higher subjectivity = more confident)
            confidence = min(abs(polarity) + (subjectivity * 0.3), 1.0)
            
            result = SentimentResult(
                score=round(polarity, 3),
                magnitude=round(subjectivity, 3),
                label=label,
                emotion=emotion,
                confidence=round(confidence, 3)
            )
            
            logger.debug(f"Sentiment: {label} ({polarity:.2f}) for: '{text[:50]}...'")
            return result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            # Return neutral sentiment on error
            return SentimentResult(
                score=0.0,
                magnitude=0.0,
                label="neutral",
                confidence=0.0
            )
    
    def _detect_emotion(self, text: str, polarity: float) -> str:
        """
        Detect specific emotion from text
        
        Args:
            text: Input text
            polarity: Sentiment polarity score
            
        Returns:
            Emotion label
        """
        text_lower = text.lower()
        
        # Emotion keywords
        emotions = {
            "happy": ["happy", "great", "excellent", "wonderful", "amazing", "love", "thank"],
            "excited": ["excited", "can't wait", "awesome", "fantastic", "thrilled"],
            "frustrated": ["frustrated", "annoying", "ridiculous", "waste of time"],
            "angry": ["angry", "furious", "terrible", "horrible", "worst", "hate", "disgusted"],
            "sad": ["sad", "disappointed", "upset", "unhappy", "depressed"],
            "worried": ["worried", "concerned", "anxious", "nervous", "scared"],
            "confused": ["confused", "don't understand", "unclear", "lost"],
        }
        
        # Check for emotion keywords
        for emotion, keywords in emotions.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        # Fall back to polarity-based emotion
        if polarity > 0.5:
            return "happy"
        elif polarity > 0.2:
            return "satisfied"
        elif polarity < -0.5:
            return "angry"
        elif polarity < -0.2:
            return "frustrated"
        else:
            return "calm"
    
    def analyze_conversation_trend(
        self,
        messages: list[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Analyze sentiment trend across conversation
        
        Args:
            messages: List of message dictionaries with 'content' key
            
        Returns:
            Dictionary with trend analysis
        """
        if not messages:
            return {
                "average_sentiment": 0.0,
                "trend": "neutral",
                "volatility": 0.0
            }
        
        # Analyze each message
        sentiments = []
        for msg in messages:
            if "content" in msg:
                result = self.analyze(msg["content"])
                sentiments.append(result.score)
        
        if not sentiments:
            return {
                "average_sentiment": 0.0,
                "trend": "neutral",
                "volatility": 0.0
            }
        
        # Calculate metrics
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Determine trend (comparing first half to second half)
        mid = len(sentiments) // 2
        if mid > 0:
            first_half = sum(sentiments[:mid]) / mid
            second_half = sum(sentiments[mid:]) / (len(sentiments) - mid)
            
            if second_half > first_half + 0.2:
                trend = "improving"
            elif second_half < first_half - 0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Calculate volatility (standard deviation)
        if len(sentiments) > 1:
            mean = sum(sentiments) / len(sentiments)
            variance = sum((x - mean) ** 2 for x in sentiments) / len(sentiments)
            volatility = variance ** 0.5
        else:
            volatility = 0.0
        
        return {
            "average_sentiment": round(avg_sentiment, 3),
            "trend": trend,
            "volatility": round(volatility, 3),
            "sentiment_scores": sentiments
        }
    
    def should_escalate_based_on_sentiment(
        self,
        recent_sentiments: list[float],
        threshold: float = -0.4,
        consecutive_negative: int = 2
    ) -> bool:
        """
        Determine if conversation should escalate based on sentiment
        
        Args:
            recent_sentiments: List of recent sentiment scores
            threshold: Negative sentiment threshold
            consecutive_negative: Number of consecutive negative messages
            
        Returns:
            True if should escalate
        """
        if len(recent_sentiments) < consecutive_negative:
            return False
        
        # Check last N messages
        last_n = recent_sentiments[-consecutive_negative:]
        return all(score < threshold for score in last_n)
    
    def get_response_tone(self, sentiment_score: float) -> str:
        """
        Get recommended response tone based on user sentiment
        
        Args:
            sentiment_score: User's sentiment score
            
        Returns:
            Recommended tone for response
        """
        if sentiment_score < -0.5:
            return "empathetic_apologetic"
        elif sentiment_score < -0.2:
            return "understanding_helpful"
        elif sentiment_score > 0.5:
            return "enthusiastic_positive"
        elif sentiment_score > 0.2:
            return "friendly_warm"
        else:
            return "professional_neutral"


# Singleton instance
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Get or create sentiment service instance"""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service
