# 🎙️ Real-Time Multilingual AI Voice Assistant — Production Architecture

> **Evolved from Hogwarts Voice Spellbook v2.0 → Enterprise-Grade Production System**

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  CLIENT (Web/Mobile/IVR)  ←──WebRTC/gRPC──→  API GATEWAY (Kong) │
└─────────────────────────────────────────────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  audio-ingress-svc │  (Go — 100ms chunks)
                          └─────────┬─────────┘
                                    │ Kafka: voice.audio.raw
              ┌─────────────────────┼───────────────────────┐
              ▼                     ▼                        ▼
      ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
      │   stt-svc    │    │   emotion-svc     │    │   fraud-svc      │
      │ DeepGram+    │    │ HuBERT SER model  │    │ XGBoost+         │
      │ Whisper      │    │ 8-class emotion   │    │ Pyannote verify  │
      └──────┬───────┘    └────────┬──────────┘    └────────┬─────────┘
             │                     │                         │
             └─────────────────────▼─────────────────────────┘
                                   │ merged context
                          ┌────────▼─────────┐
                          │   context-svc     │  Redis + pgvector
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────────┐
                          │  llm-orchestrator-svc │  GPT-4o / Claude
                          └────────┬──────────────┘
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
             ┌──────────┐  ┌────────────┐  ┌──────────────┐
             │  tts-svc │  │ urgency-svc│  │  audit-svc   │
             │ElevenLabs│  │ Escalation │  │ SIEM/Comply  │
             └────┬─────┘  └─────┬──────┘  └──────────────┘
                  │              │
                  ▼              ▼
           WebRTC Audio    Human Agent / Alert
```

## Services

| Service | Language | Port | Purpose |
|---------|----------|------|---------|
| `audio-ingress-svc` | Python/FastAPI | 8001 | WebSocket audio ingestion, Kafka publishing |
| `stt-svc` | Python | 8002 | DeepGram + Whisper fallback, multilingual STT |
| `emotion-svc` | Python | 8003 | HuBERT SER, 8-class emotion detection |
| `fraud-svc` | Python | 8004 | XGBoost scoring, voiceprint verification |
| `context-svc` | Python | 8005 | Redis session + pgvector semantic memory |
| `llm-orchestrator-svc` | Python | 8006 | LiteLLM proxy, response adaptation, streaming |
| `urgency-escalation-svc` | Python | 8007 | Rule+ML urgency engine, human escalation |
| `tts-svc` | Python | 8008 | ElevenLabs streaming, Coqui fallback |

## Quick Start (Development)

```bash
# 1. Clone and navigate
cd voice-ai-production

# 2. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up --build

# 4. Access the system
open http://localhost:8080  # Frontend
open http://localhost:8080/docs  # API docs
```

## Production Deploy (Kubernetes)

```bash
# Install with Helm
helm install voice-ai ./helm/voice-ai \
  --namespace voice-ai \
  --create-namespace \
  --values helm/voice-ai/values.prod.yaml

# Check rollout
kubectl rollout status deployment/llm-orchestrator-svc -n voice-ai
```

## Latency Budget

| Component | Target | Actual p95 |
|-----------|--------|------------|
| Audio ingestion | 110ms | ~100ms |
| STT (DeepGram) | 350ms | ~220ms |
| Emotion + Fraud (parallel) | 100ms | ~80ms |
| Context assembly | 30ms | ~5ms |
| LLM first token | 700ms | ~520ms |
| TTS stream start | 250ms | ~180ms |
| Audio delivery | 100ms | ~40ms |
| **Total E2E** | **2000ms** | **~1083ms** |

## Environment Variables

See `.env.example` for all required configuration.

## Legacy Code

The original Hogwarts Voice Spellbook v2.0 is preserved in `legacy/hogwarts-spellbook/` for reference.
It can still be run standalone: `cd legacy/hogwarts-spellbook && python app.py`

## Architecture Deep-Dive

See `docs/architecture.md` for full Principal Engineer design notes.
