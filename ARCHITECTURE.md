# VoiceAI Assistant - System Architecture

## Overview

VoiceAI Assistant is a real-time, multilingual voice chatbot system designed to replace traditional IVR systems with intelligent, human-like voice interactions.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │
│  │  Web Browser   │  │  Mobile App    │  │  WhatsApp      │      │
│  │  (React)       │  │  (React Native)│  │  Integration   │      │
│  └────────┬───────┘  └───────┬────────┘  └──────┬─────────┘      │
└───────────┼──────────────────┼──────────────────┼────────────────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
            ┌──────────────────▼──────────────────┐
            │     Load Balancer (Nginx)           │
            └──────────────────┬──────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                        API Gateway                              │
│              FastAPI + WebSocket Server                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Authentication & Authorization Middleware                 │ │
│  │  Rate Limiting │ CORS │ Request Validation                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
┌───────────▼────────┐ ┌───────▼────────┐ ┌───────▼──────┐
│  Voice Processing  │ │  Conversation  │ │  Analytics   │
│     Pipeline       │ │    Manager     │ │   Service    │
└───────────┬────────┘ └───────┬────────┘ └──────┬───────┘
            │                  │                 │
┌───────────▼──────────────────▼─────────────────▼──────────────┐
│                     Core AI Engine                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   STT    │→ │   NLU    │→ │Response  │→ │   TTS    │       │
│  │ Service  │  │ Service  │  │Generator │  │ Service  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │           Intelligence Layer                         │     │
│  │  • Sentiment Analysis    • Fraud Detection           │     │
│  │  • Language Detection    • Intent Recognition        │     │
│  │  • Context Management    • Urgency Detection         │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────┬─────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
┌───────────▼────┐ ┌──────▼──────┐ ┌────▼────────┐
│   PostgreSQL   │ │    Redis    │ │   Celery    │
│   (Primary DB) │ │   (Cache)   │ │   Queue     │
└───────────┬────┘ └──────┬──────┘ └────┬────────┘
            │             │             │
┌───────────▼─────────────▼─────────────▼────────────────────────┐
│                  External Integrations                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CRM    │  │ WhatsApp │  │   ERP    │  │ Payment  │        │
│  │(Salesforce)││ (Twilio) │  │  Systems │  │ Gateway  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Voice Processing Pipeline

#### Speech-to-Text (STT)
- **Primary**: OpenAI Whisper API
- **Fallback**: Deepgram API
- **Features**:
  - Real-time streaming transcription
  - Multi-language support (8+ Indian languages)
  - Noise cancellation
  - Accent adaptation
  - Code-mixing support (Hinglish, Tanglish)

**Flow**:
```
Audio Input → VAD (Voice Activity Detection) → Chunking → 
STT API → Transcription → Language Detection → Output
```

#### Text-to-Speech (TTS)
- **Primary**: ElevenLabs API
- **Fallback**: Azure Cognitive Services
- **Features**:
  - Human-like voice synthesis
  - Emotional tone modulation
  - Multi-language support
  - Low latency streaming
  - Voice cloning capability

**Flow**:
```
Text Input → Language Detection → Voice Selection → 
TTS API → Audio Stream → Client
```

### 2. Natural Language Understanding (NLU)

#### Core LLM
- **Primary**: GPT-4 Turbo
- **Context**: Up to 10 conversation turns
- **Temperature**: 0.7 (balanced creativity)

#### Intent Recognition
```python
intents = [
    "query_status",     
    "complaint",       
    "information",       
    "transaction",       
    "support",         
    "feedback",       
    "escalation"       
]
```

#### Entity Extraction
- Customer ID
- Order/Ticket numbers
- Dates and times
- Product names
- Locations
- Phone numbers
- Email addresses

### 3. Context Management System

```python
class ConversationContext:
    user_id: str
    session_id: str
    conversation_history: List[Message]
    user_profile: Dict
    sentiment_history: List[float]
    detected_intents: List[str]
    metadata: Dict
    ttl: int = 3600
```

### 4. Sentiment Analysis

**Model**: DistilBERT fine-tuned on SST-2
**Outputs**:
- Sentiment: Positive, Negative, Neutral
- Confidence score: 0.0 to 1.0
- Emotional state: Happy, Frustrated, Angry, Calm

**Real-time monitoring**:
```python
if sentiment.score < 0.3:  
    if sentiment.intensity > 0.8:  
        trigger_escalation(conversation_id)
```

### 5. Fraud Detection System

**Detection Methods**:
1. **Keyword Analysis**: Suspicious terms (scam, fake, hack)
2. **Voice Stress Analysis**: Unusual vocal patterns
3. **Behavioral Patterns**: Rapid requests, repeated failures
4. **Historical Data**: Compare with known fraud cases

**Alert Levels**:
- Low (0-30%): Log for review
- Medium (30-70%): Require additional verification
- High (70-100%): Immediate escalation + block

### 6. Integration Layer

#### CRM Integration (Salesforce)
```python
endpoints = {
    "get_customer": "/services/data/v58.0/sobjects/Contact/{id}",
    "create_case": "/services/data/v58.0/sobjects/Case",
    "update_case": "/services/data/v58.0/sobjects/Case/{id}",
    "search": "/services/data/v58.0/search/"
}
```

#### WhatsApp Integration (Twilio)
```python
# Webhook flow
Incoming Message → Parse → Process → Generate Response → 
Send via Twilio → Store in DB
```

#### ERP Integration
- Order status queries
- Inventory checks
- Shipment tracking
- Invoice retrieval

## Data Flow

### Voice Call Flow

```
1. User initiates call
   ↓
2. WebSocket connection established
   ↓
3. Audio stream starts → STT → Text
   ↓
4. Text → NLU (Intent + Entity extraction)
   ↓
5. Context retrieval from Redis
   ↓
6. Query external systems (CRM/ERP) if needed
   ↓
7. LLM generates contextual response
   ↓
8. Sentiment analysis on response
   ↓
9. Response → TTS → Audio stream
   ↓
10. Audio streamed back to user
    ↓
11. Update context in Redis
    ↓
12. Log interaction in PostgreSQL
```

### Analytics Pipeline

```
Voice Interaction → 
Extract Metrics (latency, sentiment, success) → 
Process with Celery → 
Store in PostgreSQL → 
Display in Dashboard (React + Recharts)
```

## Database Schema

### Core Tables

#### conversations
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id VARCHAR(50),
    session_id UUID,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INT,
    language VARCHAR(10),
    sentiment_avg FLOAT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(10),  -- 'user' or 'assistant'
    content TEXT,
    audio_url VARCHAR(255),
    sentiment FLOAT,
    intent VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### analytics
```sql
CREATE TABLE analytics (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT NOW()
);
```

## Security

### Authentication
- JWT tokens (1-hour expiry)
- Refresh tokens (7-day expiry)
- API key authentication for service-to-service

### Encryption
- TLS 1.3 for all communications
- AES-256 for sensitive data at rest
- Audio recordings encrypted in S3

### Rate Limiting
```python
limits = {
    "public_api": "100/hour",
    "authenticated": "1000/hour",
    "premium": "10000/hour"
}
```


## Scalability

### Horizontal Scaling
- **API Servers**: Auto-scale based on CPU (target: 70%)
- **Celery Workers**: Scale based on queue length
- **Database**: Read replicas for analytics queries

### Caching Strategy
- **Redis**: User sessions, conversation context
- **CDN**: Static assets, audio files
- **Application**: LRU cache for frequent queries

## Monitoring & Observability

### Metrics (Prometheus)
- Request rate, error rate, duration
- Active WebSocket connections
- Queue length (Celery)
- Database connection pool utilization

### Logging (Structured JSON)
```python
{
    "timestamp": "2024-02-26T10:30:45Z",
    "level": "INFO",
    "service": "voice_processing",
    "conversation_id": "uuid",
    "message": "STT completed",
    "latency_ms": 450,
    "language": "hi"
}
```

### Error Tracking (Sentry)
- Automatic error reporting
- Context capture (user, conversation)
- Performance monitoring

## Disaster Recovery

### Backups
- **Database**: Daily full backup, hourly incremental
- **Audio recordings**: S3 versioning enabled
- **Redis**: RDB snapshots every 5 minutes

### Failover
- Database: Automatic failover to replica (< 30s)
- Services: Health checks + auto-restart
- Multi-region deployment (future)

## Future Enhancements

1. **Voice Biometrics**: Speaker identification
2. **Emotion AI**: Advanced emotional intelligence
3. **Predictive Analytics**: Anticipate customer needs
4. **Video Support**: Face-to-face video calls
5. **IoT Integration**: Smart device control
6. **Blockchain**: Immutable conversation logs


**Last Updated**: February 2026
**Version**: 1.0
**Authors**: Team HackeRats
