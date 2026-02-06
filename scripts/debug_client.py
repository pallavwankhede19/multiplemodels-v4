
import asyncio
import websockets
import json
import random
import time
import ssl

async def test_interaction():
    uri = "wss://jayla-bouilli-chun.ngrok-free.dev/ws/audio"
    print(f"🔌 Connecting to {uri}...")
    
    # Create SSL context for WSS
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        print("✅ Connected to WebSocket")
        
        # --- TEST 1: Short Audio (0.3s) ---
        print("\n🧪 TEST 1: Short Audio (0.3s) - Expected to be IGNORED in Strict Mode")
        # 1. Set AI Listening (Resets VAD to 'listening' mode, but we want to test STRICT mode if possible?)
        # Actually user said check response. 
        # If I send 'ai_state=speaking', it goes to STRICT.
        # If I don't send anything, it's default (which is usually LISTENING/Non-Strict).
        # But wait, the issue usually happens when interrupting (Strict Mode).
        # Let's test BOTH.
        
        # A. Non-Strict Test (Normal input)
        print("   [Mode: Normal/Listening]")
        await websocket.send(json.dumps({"type": "ai_state", "status": "listening"}))
        await asyncio.sleep(0.1)
        
        # Send 0.4s audio (should trigger fast VAD)
        # 16000 * 2 * 0.4 = 12800 bytes
        noise = bytes([random.randint(0, 255) for _ in range(int(16000 * 2 * 0.4))])
        await websocket.send(noise)
        print("   📤 Sent 0.4s Noise")
        
        start = time.time()
        triggered = False
        try:
            while time.time() - start < 1.0:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(response)
                    if data.get("type") in ["stop_audio", "commit"]:
                        print(f"   ⚡ TRIGGERED: {data['type']}")
                        triggered = True
                        break
                except asyncio.TimeoutError:
                    continue
        except Exception: pass
        
        if not triggered: print("   ❌ NOT TRIGGERED (Unexpected for Normal Mode?)")

        # --- TEST 2: Strict Mode (Simulating Interruption) ---
        print("\n🧪 TEST 2: Strict Audio (0.3s) - Simulate Interrupting AI")
        print("   [Mode: Strict/Speaking]")
        await websocket.send(json.dumps({"type": "ai_state", "status": "speaking"}))
        await asyncio.sleep(0.1)
        
        await websocket.send(noise) # Same 0.4s noise
        print("   📤 Sent 0.4s Noise")
        
        start = time.time()
        triggered = False
        try:
            while time.time() - start < 1.0:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(response)
                    if data.get("type") in ["stop_audio", "commit"]:
                         print(f"   ⚡ TRIGGERED: {data['type']}")
                         triggered = True
                         break
                except asyncio.TimeoutError:
                    continue
        except Exception: pass
        
        if not triggered: print("   ❌ NOT TRIGGERED (Expected Failure if Limit=25)")
        else: print("   ✅ TRIGGERED (Limit is low?)")

        # --- TEST 3: Long Audio (1.2s) in Strict Mode ---
        print("\n🧪 TEST 3: Long Audio (1.2s) - Strict Mode")
        # Reset to strict
        await websocket.send(json.dumps({"type": "ai_state", "status": "speaking"}))
        await asyncio.sleep(0.1)
        
        long_noise = bytes([random.randint(0, 255) for _ in range(int(16000 * 2 * 1.2))])
        # Send in chunks to simulate stream
        chunk_size = 4096
        print("   📤 Sending 1.2s Noise Stream...")
        for i in range(0, len(long_noise), chunk_size):
            await websocket.send(long_noise[i:i+chunk_size])
            await asyncio.sleep(0.01)
            
        start = time.time()
        triggered = False
        try:
            while time.time() - start < 2.0:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(response)
                    if data.get("type") in ["stop_audio", "commit"]:
                         print(f"   ⚡ TRIGGERED: {data['type']}")
                         triggered = True
                         break
                except asyncio.TimeoutError:
                    continue
        except Exception: pass
        
        if not triggered: print("   ❌ NOT TRIGGERED (System Unresponsive?)")
        else: print("   ✅ TRIGGERED (System Works for Long Audio)")

if __name__ == "__main__":
    asyncio.run(test_interaction())
