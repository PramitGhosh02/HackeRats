#  VoiceAI Backend - Complete MAP

##  What We'll Built

A **fully functional AI voice chatbot backend** with:

**Speech-to-Text** (OpenAI Whisper)  
**Intelligent Conversation** (GPT-4)  
**Text-to-Speech** (ElevenLabs)  
**Sentiment Analysis** (Real-time emotion detection)  
**Context Management** (Redis-based session storage)  
**WebSocket Support** (Real-time streaming)  
**RESTful API** (Easy integration)  

---

##  Files Created

### Core Services (5 files)
1. **`app/core/config.py`** - Configuration management
2. **`app/services/stt_service.py`** - Speech-to-Text
3. **`app/services/llm_service.py`** - AI Conversation Engine
4. **`app/services/tts_service.py`** - Text-to-Speech
5. **`app/services/sentiment.py`** - Sentiment Analysis
6. **`app/services/context_manager.py`** - Context Storage

### Main Application
7. **`main.py`** - FastAPI app with all endpoints

---

##  Quick Start

### Step 1: Install Dependencies

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file in `backend/` directory:

```env
# REQUIRED - Get these API keys
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Optional (for local testing without Docker)
DATABASE_URL=postgresql://voiceai_user:password123@localhost:5432/voiceai_db
REDIS_URL=redis://localhost:6379/0

# Or use in-memory (will work without Redis)
REDIS_URL=redis://localhost:6379/0
```

### Step 3: Run the Server

```bash
# From backend directory
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --port 8000
```

Server will start at: **http://localhost:8000**

---

##  Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-26T10:30:00",
  "services": {
    "stt": "operational",
    "llm": "operational",
    "tts": "operational"
  }
}
```

### 2. Test Text Chat (No Audio Needed)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my order",
    "language": "en"
  }'
```

**Expected Response:**
```json
{
  "session_id": "uuid-here",
  "response": "Hello! I'd be happy to help you with your order. Could you please provide your order number?",
  "sentiment": {
    "score": 0.2,
    "label": "neutral",
    "emotion": "calm"
  },
  "intent": "query_status",
  "follow_up_suggestions": [
    "What is my order status?",
    "When will my order arrive?",
    "How do I track my order?"
  ]
}
```

### 3. Test Voice Interaction (with Audio File)

```bash
# Record a short audio: "Hello, how are you?"
# Save as test_audio.wav

curl -X POST http://localhost:8000/api/voice \
  -F "audio=@test_audio.wav" \
  -F "language=en"
```

**Expected Response:**
```json
{
  "session_id": "uuid-here",
  "transcript": "Hello, how are you?",
  "response_text": "Hello! I'm doing well, thank you for asking. How can I assist you today?",
  "audio_base64": "base64-encoded-audio-here",
  "sentiment": {
    "score": 0.8,
    "label": "positive",
    "emotion": "happy"
  },
  "intent": "greeting",
  "should_escalate": false
}
```

### 4. Test API Documentation

Open in browser: **http://localhost:8000/docs**

This opens **Swagger UI** where you can:
- See all available endpoints
- Test APIs interactively
- View request/response schemas

---

##  API Endpoints

### Chat Endpoints

#### POST `/api/chat`
Text-based conversation (no audio)

**Request:**
```json
{
  "message": "Hello",
  "language": "en",
  "session_id": "optional-uuid"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "response": "Hello! How can I help?",
  "sentiment": {...},
  "intent": "greeting",
  "follow_up_suggestions": [...]
}
```

---

#### POST `/api/voice`
Complete voice interaction (STT → LLM → TTS)

**Request:** (multipart/form-data)
- `audio`: Audio file (wav, mp3, etc.)
- `language`: Language code (en, hi, ta, etc.)
- `session_id`: Optional session ID

**Response:**
```json
{
  "session_id": "uuid",
  "transcript": "What you said",
  "response_text": "AI response",
  "audio_base64": "response-audio",
  "sentiment": {...},
  "intent": "...",
  "should_escalate": false
}
```

---

#### WebSocket `/ws/voice`
Real-time bidirectional voice streaming

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'connected') {
    console.log('Session:', data.session_id);
  }
  
  if (data.type === 'response') {
    console.log('AI:', data.text);
  }
  
  if (data.type === 'audio') {
    // Play audio from data.audio (base64)
  }
};

// Send audio
ws.send(JSON.stringify({
  type: 'audio',
  audio: audioBase64,
  language: 'en'
}));
```

---

#### GET `/api/conversation/{session_id}`
Retrieve conversation history

**Response:**
```json
{
  "session_id": "uuid",
  "language": "en",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-02-26T10:30:00",
      "metadata": {"sentiment": 0.5}
    },
    {
      "role": "assistant",
      "content": "Hi there!",
      "timestamp": "2024-02-26T10:30:02",
      "metadata": {}
    }
  ]
}
```

---

#### GET `/api/languages`
Get supported languages

**Response:**
```json
{
  "supported_languages": {
    "en": {"name": "English", ...},
    "hi": {"name": "Hindi", ...},
    ...
  },
  "default_language": "en"
}
```

---

## 🌐 Testing with Python Script

Create `test_voice_api.py`:

```python
import requests
import base64
import json

# Test chat endpoint
def test_chat():
    response = requests.post(
        "http://localhost:8000/api/chat",
        json={
            "message": "I need help with my order",
            "language": "en"
        }
    )
    print("Chat Response:", response.json())

# Test voice endpoint
def test_voice():
    with open("test_audio.wav", "rb") as f:
        files = {"audio": f}
        data = {"language": "en"}
        
        response = requests.post(
            "http://localhost:8000/api/voice",
            files=files,
            data=data
        )
        
        result = response.json()
        print("Transcript:", result["transcript"])
        print("Response:", result["response_text"])
        
        # Save response audio
        audio_data = base64.b64decode(result["audio_base64"])
        with open("response.mp3", "wb") as out:
            out.write(audio_data)
        print("Audio saved to response.mp3")

if __name__ == "__main__":
    test_chat()
    test_voice()
```

Run:
```bash
python test_voice_api.py
```

---

##  Testing with Postman

### 1. Import Collection
Create a new Postman collection with these requests:

**Chat Request:**
- Method: POST
- URL: `http://localhost:8000/api/chat`
- Body (JSON):
```json
{
  "message": "Hello, I need help",
  "language": "en"
}
```

**Voice Request:**
- Method: POST
- URL: `http://localhost:8000/api/voice`
- Body (form-data):
  - Key: `audio`, Type: File, Value: [select audio file]
  - Key: `language`, Type: Text, Value: `en`

---

##  Troubleshooting

### Issue: "OpenAI API key not found"
**Solution:** Make sure `.env` file has `OPENAI_API_KEY=sk-...`

### Issue: "Redis connection failed"
**Solution:** 
- Start Redis: `redis-server`
- Or app will work without Redis (uses in-memory storage)

### Issue: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

##  Features Demonstration

### 1. Multi-Turn Conversation
```bash
# First message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to order a pizza",
    "language": "en"
  }'

# Save the session_id from response

# Second message (use same session_id)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<session_id_from_first_response>",
    "message": "Make it large with extra cheese",
    "language": "en"
  }'
```

### 2. Sentiment Detection
```bash
# Positive message
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "This is amazing! I love it!"}'

# Negative message
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "This is terrible, I hate this!"}'
```

### 3. Language Support
```bash
# Hindi
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Namaste, mujhe madad chahiye", "language": "hi"}'


```

---
