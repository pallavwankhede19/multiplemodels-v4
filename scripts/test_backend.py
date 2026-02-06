import httpx
import asyncio
import json
import os
import sys

# Add working directory to path so we can import app
sys.path.append(os.getcwd())

async def test_backend():
    print("🧪 --- BACKEND DIAGNOSTIC TEST ---")
    
    # 1. Test Reset API
    print("\n1. Testing /api/reset...")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post("http://localhost:8082/api/reset", timeout=5)
            print(f"   Status: {r.status_code}, Body: {r.json()}")
        except Exception as e:
            print(f"   ❌ FAILED to connect to backend: {e}")
            return

    # 2. Test Gemini Stream Chat API
    print("\n2. Testing /api/stream_chat (English)...")
    payload = {"text": "hello", "language": "en"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", "http://localhost:8082/api/stream_chat", json=payload) as resp:
                print(f"   Status: {resp.status_code}")
                found_text = False
                found_audio = False
                async for line in resp.aiter_lines():
                    if not line: continue
                    data = json.loads(line)
                    if data["type"] == "text":
                        print(f"   AI Text: {data['content']}")
                        found_text = True
                    elif data["type"] == "audio_text":
                        print(f"   AI Audio Chunk: {data['content']}")
                        found_audio = True
                
                if found_text and found_audio:
                    print("   ✅ English Pipeline SUCCESS")
                else:
                    print(f"   ❌ Pipeline Incomplete: text={found_text}, audio={found_audio}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # 3. Test Marathi Detection & Response
    print("\n3. Testing Marathi Auto-Detection...")
    payload = {"text": "mala tujha naav maahit aahe ka?", "language": "en"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", "http://localhost:8082/api/stream_chat", json=payload) as resp:
                print(f"   Status: {resp.status_code}")
                full_text = ""
                async for line in resp.aiter_lines():
                    if not line: continue
                    data = json.loads(line)
                    if data["type"] == "text":
                        full_text += data["content"]
                
                print(f"   AI Response: {full_text}")
                # Check for Devanagari characters
                if any('\u0900' <= c <= '\u097F' for c in full_text):
                    print("   ✅ Marathi Detection SUCCESS")
                else:
                    print("   ❌ Failed to switch to Marathi")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # 4. Test Local TTS Endpoint (Hindi)
    print("\n4. Testing Local TTS /api/v1/generate...")
    payload = {"text": "नमस्ते", "lang": "hi"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("http://localhost:8082/api/v1/generate", json=payload)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200 and len(resp.content) > 1000:
                print(f"   ✅ TTS Generated {len(resp.content)} bytes of PCM")
            else:
                print(f"   ❌ TTS Generation failed or empty")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    print("\n🏁 --- DIAGNOSTIC FINISHED ---")

if __name__ == "__main__":
    asyncio.run(test_backend())
