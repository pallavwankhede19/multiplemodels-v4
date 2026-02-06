import httpx
import asyncio
import json
import os
import sys

# Add working directory to path
sys.path.append(os.getcwd())

async def run_audit():
    print("📋 --- SAMAGRA FINAL VALIDATION REPORT ---")
    print("-" * 40)
    
    base_url = "http://localhost:8082"
    
    tests = [
        ("English", "Hello, who are you?", "en"),
        ("Hindi", "नमस्ते, आपका नाम क्या है?", "hi"),
        ("Marathi", "तुझे नाव काय आहे?", "mr"),
        ("Hinglish Detect", "kaise ho bhai?", "en") # Should auto-switch to Hindi
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        for name, text, lang in tests:
            print(f"\n🔍 Testing {name}...")
            full_text = ""
            found_audio = False
            
            try:
                async with client.stream("POST", f"{base_url}/api/stream_chat", json={"text": text, "language": lang}) as resp:
                    async for line in resp.aiter_lines():
                        if not line: continue
                        data = json.loads(line)
                        if data["type"] == "text":
                            full_text += data["content"]
                        if data["type"] == "audio_text":
                            found_audio = True
                
                print(f"   Input: '{text}'")
                print(f"   Output: '{full_text.strip()}'")
                print(f"   Audio Generated: {'✅' if found_audio else '❌'}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")

    print("\n🏁 --- VALIDATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_audit())
