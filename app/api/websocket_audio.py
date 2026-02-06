import json
import asyncio
import time
from fastapi import WebSocket, WebSocketDisconnect
from app.services.vad_service import voice_detector
from app.services.interrupt_manager import interrupt_manager

async def audio_stream(websocket: WebSocket):
    """
    Stage W2/W3: Responsive Audio Stream with JSON Control Channel
    """
    await websocket.accept()
    print("🎙️ Sensory Layer: ACTIVE (Sync Mode)")
    
    last_interrupt_time = 0
    last_commit_time = 0  # 🔥 Prevent rapid-fire commit loops
    INTERRUPT_COOLDOWN = 0.6
    COMMIT_COOLDOWN = 1.2  # Balanced for natural turn-taking
    
    try:
        while True:
            # Handle both Binary (Audio) and Text (Control) frames
            message = await websocket.receive()
            
            if "bytes" in message:
                data = message["bytes"]
                # 🧪 DEBUG: Confirm data arrival
                # print(f"📥 Received Bytes: {len(data)}", flush=True)

                # 1. Process VAD
                is_voiced = voice_detector.is_speech(data)
                
                if is_voiced:
                    now = time.time()
                    if now - last_interrupt_time > INTERRUPT_COOLDOWN:
                        if interrupt_manager.on_user_speech():
                            last_interrupt_time = now
                            print(f"⚡ NEURAL INTERRUPT DETECTED")
                            await websocket.send_json({"type": "stop_audio"})
                
                # 2. Fast Commit (with cooldown to prevent loops)
                if voice_detector.check_commit():
                    now = time.time()
                    if now - last_commit_time > COMMIT_COOLDOWN:
                        last_commit_time = now
                        print("🏁 SPEECH END (Commit)")
                        await websocket.send_json({"type": "commit"})
                        interrupt_manager.on_silence()

            elif "text" in message:
                # 3. Control Messages from Frontend
                try:
                    ctrl = json.loads(message["text"])
                    if ctrl.get("type") == "ai_state":
                        if ctrl["status"] == "speaking":
                            print("🛡️ AI SPEAKING (Hardware Immunity SKIPPED -> Strict VAD)")
                            voice_detector.set_strict_mode(True) 
                        elif ctrl["status"] == "listening":
                            print("👂 AI LISTENING")
                            voice_detector.set_strict_mode(False)
                            # 🔥 Clear accumulated "echo" frames to prevent instant trigger on mode switch
                            voice_detector.reset()
                    elif ctrl.get("type") == "lang_update":
                        lang = ctrl.get("lang", "en")
                        voice_detector.set_language_mode(lang)
                except:
                    pass
                        
    except WebSocketDisconnect:
        print("📡 Client Disconnected")
    except Exception as e:
        print(f"📡 Sensory Error: {e}")
    finally:
        interrupt_manager.on_silence()
        voice_detector.reset()
