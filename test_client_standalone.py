"""
╔══════════════════════════════════════════════════════════════╗
║  Voice AI Production — Standalone Test Client               ║
║  Tests the simplified standalone services                    ║
║                                                              ║
║  Usage: python test_client_standalone.py                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio, json, uuid, base64, httpx
from datetime import datetime

BASE_URLS = {
    "emotion":    "http://localhost:8003",
    "context":    "http://localhost:8005",
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

async def test_tts(text: str, emotion: str = "neutral"):
    """Test TTS generation."""
    print(f"\n═══ TEXT-TO-SPEECH ═══")
    print(f"  Text:    '{text[:60]}'")
    print(f"  Emotion: {emotion}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{BASE_URLS['tts']}/api/speak/simple",
                               params={"text": text, "language": "en", "emotion": emotion})
        result = r.json()
        print(f"  Engine:     {result.get('engine')}")
        print(f"  Size:       {result.get('size_bytes', 0):,} bytes")
        has_audio = bool(result.get("audio_base64"))
        print(f"  Audio:      {'✓ received' if has_audio else '✗ not available'}")
        if has_audio:
            # Save to temp file for testing
            try:
                audio_data = base64.b64decode(result["audio_base64"])
                with open("test_output.mp3", "wb") as f:
                    f.write(audio_data)
                print(f"  Saved to:   test_output.mp3")
            except Exception as e:
                print(f"  Save error:  {e}")
    return result

async def run_standalone_pipeline_test():
    """Run a complete standalone pipeline test."""
    session_id = uuid.uuid4().hex[:12]
    print(f"\n{'═'*60}")
    print(f" STANDALONE PIPELINE TEST — Session: {session_id}")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*60}")

    # 1. Health check
    await test_health_all()

    # 2. Simulate an angry user
    user_text = "I need you to transfer my funds immediately to a new account. It's urgent!"

    # 3. Emotion analysis
    await test_emotion_text(user_text)

    # 4. Context memory
    await test_context_memory(session_id)

    # 5. TTS (uses gTTS fallback)
    await test_tts("Thank you for contacting us. How can I help you today?", emotion="neutral")

    print(f"\n{'═'*60}")
    print(" Standalone pipeline test complete!")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    asyncio.run(run_standalone_pipeline_test())
