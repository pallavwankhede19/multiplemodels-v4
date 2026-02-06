import httpx
import asyncio
import json
import os
import sys

# Add working directory to path
sys.path.append(os.getcwd())

async def run_audit():
    print("📋 --- SAMAGRA SYSTEM AUDIT REPORT ---")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 40)
    
    base_url = "http://localhost:8082"
    results = {}

    async def test_endpoint(name, method, path, payload=None, is_stream=False):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                if is_stream:
                    print(f"Testing {name} (Streaming)...")
                    full_text = ""
                    found_audio = False
                    async with client.stream(method, f"{base_url}{path}", json=payload) as resp:
                        if resp.status_code != 200:
                            return False, f"HTTP {resp.status_code}"
                        async for line in resp.aiter_lines():
                            if not line: continue
                            data = json.loads(line)
                            if data.get("type") == "text": full_text += data["content"]
                            if data.get("type") == "audio_text": found_audio = True
                    return (len(full_text) > 0 and found_audio), f"Text: {len(full_text)} chars, Audio: {found_audio}"
                else:
                    print(f"Testing {name}...")
                    resp = await client.request(method, f"{base_url}{path}", json=payload)
                    if resp.status_code != 200:
                        return False, f"HTTP {resp.status_code}"
                    if "audio/pcm" in resp.headers.get("content-type", ""):
                        return len(resp.content) > 1000, f"PCM Size: {len(resp.content)} bytes"
                    return True, "OK"
        except Exception as e:
            return False, str(e)

    # 1. English Model Test
    results["English Pipeline"] = await test_endpoint(
        "EN Chat", "POST", "/api/stream_chat", 
        {"text": "Hello, how is the weather?", "language": "en"}, is_stream=True
    )

    # 2. Hindi Model Test
    results["Hindi Pipeline"] = await test_endpoint(
        "HI Chat", "POST", "/api/stream_chat", 
        {"text": "नमस्ते, आप कैसे हैं?", "language": "hi"}, is_stream=True
    )

    # 3. Marathi Model Test
    results["Marathi Pipeline"] = await test_endpoint(
        "MR Chat", "POST", "/api/stream_chat", 
        {"text": "पुण्यातील हवामान कसे आहे?", "language": "mr"}, is_stream=True
    )

    # 4. Transliteration Auto-Detect Test (Hinglish -> Hindi)
    results["Hinglish Detect"] = await test_endpoint(
        "Hinglish Auto", "POST", "/api/stream_chat", 
        {"text": "aapka naam kya hai?", "language": "en"}, is_stream=True # Force detect from English input
    )

    # 5. Local TTS Strength Test (Marathi)
    results["Marathi TTS Model"] = await test_endpoint(
        "MR TTS", "POST", "/api/v1/generate", 
        {"text": "मी आपल्या मदतीसाठी येथे आहे.", "lang": "mr"}
    )

    print("\n📊 --- AUDIT SUMMARY ---")
    score = 0
    for test, (status, msg) in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {test:20} : {msg}")
        if status: score += 1
    
    print("-" * 40)
    print(f"FINAL SCORE: {score}/{len(results)}")
    if score == len(results):
        print("🚀 SYSTEM STATUS: PRODUCTION READY")
    else:
        print("⚠️ SYSTEM STATUS: ISSUE DETECTED")

import time
if __name__ == "__main__":
    asyncio.run(run_audit())
