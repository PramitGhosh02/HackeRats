"""
╔══════════════════════════════════════════════════════════════╗
║  Voice AI Production — Example Test Client                   ║
║  Demonstrates the full pipeline end-to-end                   ║
║                                                              ║
║  Usage: python test_client.py                                ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio, json, uuid, base64, httpx
from datetime import datetime

BASE_URLS = {
    "stt":        "http://localhost:8002",
    "emotion":    "http://localhost:8003",
    "fraud":      "http://localhost:8004",
    "context":    "http://localhost:8005",
    "llm":        "http://localhost:8006",
    "urgency":    "http://localhost:8007",
    "tts":        "http://localhost:8008",
}

async def test_health_all():
    """Test all services are healthy."""
    print("\n═══ HEALTH CHECKS ═══")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for svc, url in BASE_URLS.items():
            try:
                r = await client.get(f"{url}/api/health")
                status = r.json().get("status", "unknown")
                print(f"  ✓ {svc:25s} → {status}")
            except Exception as e:
                print(f"  ✗ {svc:25s} → ERROR: {e}")

async def test_emotion_text(text: str):
    """Test emotion detection from text."""
    print(f"\n═══ EMOTION DETECTION ═══")
    print(f"  Input: '{text}'")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE_URLS['emotion']}/api/analyze/text",
                               json={"text": text, "session_id": "test"})
        result = r.json()
        print(f"  Emotion:    {result.get('dominant_emotion')} ({result.get('confidence', 0):.2f})")
        print(f"  Valence:    {result.get('valence', 0):.2f}")
        print(f"  Arousal:    {result.get('arousal', 0):.2f}")
        print(f"  Distress:   {result.get('is_distress', False)}")
    return result

async def test_fraud_scoring(session_id: str, transcript: str):
    """Test fraud scoring."""
    print(f"\n═══ FRAUD SCORING ═══")
    print(f"  Session: {session_id}")
    print(f"  Text:    '{transcript[:80]}...' ")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE_URLS['fraud']}/api/score",
                               json={"session_id": session_id, "transcript": transcript})
        result = r.json()
        print(f"  Score:      {result.get('fraud_score', 0):.4f}")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Action:     {result.get('action')}")
        top_feat = {k: v for k, v in result.get("features", {}).items() if v > 0.1}
        if top_feat:
            print(f"  Top Features: {top_feat}")
    return result

async def test_urgency_evaluation(session_id: str, text: str, emotion: str = "angry"):
    """Test urgency evaluation."""
    print(f"\n═══ URGENCY EVALUATION ═══")
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{BASE_URLS['urgency']}/api/evaluate",
                               json={
                                   "session_id": session_id,
                                   "text": text,
                                   "emotion": emotion,
                                   "emotion_confidence": 0.8,
                                   "fraud_level": "LOW",
                                   "turn_count": 3,
                               })
        result = r.json()
        print(f"  Score:     {result.get('urgency_score', 0):.4f}")
        print(f"  Escalate:  {result.get('should_escalate', False)}")
        print(f"  Action:    {result.get('recommended_action')}")
        print(f"  Reasons:   {result.get('reasons', [])}")
    return result

async def test_context_memory(session_id: str):
    """Test context store and retrieval."""
    print(f"\n═══ CONTEXT MEMORY ═══")
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Init session
        await client.post(f"{BASE_URLS['context']}/api/session/{session_id}",
                           json={"user_id": "test_user", "language": "en"})
        print(f"  Session initialized: {session_id}")

        # Add some turns
        for role, text in [("user", "I need help with my account"),
                             ("assistant", "I'd be happy to help. What seems to be the issue?"),
                             ("user", "I can't access my account since yesterday")]:
            await client.post(f"{BASE_URLS['context']}/api/context/{session_id}/turn",
                               json={"role": role, "text": text})

        # Retrieve context
        r = await client.get(f"{BASE_URLS['context']}/api/context/{session_id}")
        ctx = r.json()
        print(f"  Turns stored: {ctx.get('turn_count', 0)}")
        print(f"  Last turn:    {ctx['turns'][-1]['text'][:60] if ctx.get('turns') else 'none'}")

    return ctx

async def test_llm_respond(session_id: str, text: str, language: str = "en"):
    """Test LLM orchestration (non-streaming)."""
    print(f"\n═══ LLM RESPONSE ═══")
    print(f"  Input: '{text}'")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{BASE_URLS['llm']}/api/respond",
                               json={"session_id": session_id, "text": text, "language": language})
        if r.status_code == 200:
            result = r.json()
            print(f"  Response: '{result.get('response', '')[:120]}...'")
        else:
            print(f"  Note: LLM requires API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
            print(f"  Status: {r.status_code}")
    return r.status_code

async def test_tts(text: str, emotion: str = "neutral"):
    """Test TTS generation."""
    print(f"\n═══ TEXT-TO-SPEECH ═══")
    print(f"  Text:    '{text[:60]}'")
    print(f"  Emotion: {emotion}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{BASE_URLS['tts']}/api/speak",
                               json={"text": text, "emotion": emotion, "language": "en"})
        result = r.json()
        print(f"  Engine:     {result.get('engine')}")
        print(f"  Size:       {result.get('size_bytes', 0):,} bytes")
        has_audio = bool(result.get("audio_base64"))
        print(f"  Audio:      {'✓ received' if has_audio else '✗ not available'}")
        if has_audio:
            with open("/tmp/test_output.mp3", "wb") as f:
                f.write(base64.b64decode(result["audio_base64"]))
            print(f"  Saved to:   /tmp/test_output.mp3")
    return result

async def run_full_pipeline_test():
    """Run a complete end-to-end pipeline simulation."""
    session_id = uuid.uuid4().hex[:12]
    print(f"\n{'═'*60}")
    print(f" FULL PIPELINE TEST — Session: {session_id}")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*60}")

    # 1. Health check
    await test_health_all()

    # 2. Simulate an angry user with fraud indicators
    user_text = "I need you to transfer my funds immediately to a new account. It's urgent!"

    # 3. Emotion analysis
    await test_emotion_text(user_text)

    # 4. Fraud scoring
    await test_fraud_scoring(session_id, user_text)

    # 5. Urgency check
    await test_urgency_evaluation(session_id, user_text, emotion="angry")

    # 6. Context memory
    await test_context_memory(session_id)

    # 7. LLM response (needs API keys)
    await test_llm_respond(session_id, user_text)

    # 8. TTS (uses fallback gTTS if ElevenLabs not configured)
    await test_tts("Thank you for contacting us. How can I help you today?", emotion="neutral")

    print(f"\n{'═'*60}")
    print(" Pipeline test complete!")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    asyncio.run(run_full_pipeline_test())
