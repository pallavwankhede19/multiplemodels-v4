import os, json, asyncio, certifi
from collections import deque
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from google import genai
from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.services.transliteration_detector import detect_transliteration
from app.services.script_normalizer import ScriptNormalizer
from app.services.tts_manager import init_tts_pools, get_pool
from app.services.interrupt_manager import interrupt_manager
from app.api.websocket_audio import audio_stream
from app.services.vad_service import voice_detector

# ---------------- ENV ----------------
os.environ["SSL_CERT_FILE"] = certifi.where()

# ---------------- APP ----------------
app = FastAPI(title="Ai Assistance Powered By The Baap Company lead real-time conversation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SERVICES ----------------
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
chat_history = deque(maxlen=10)

@app.on_event("startup")
async def startup_event():
    setup_logging()
    logger.info("🚀 Starting Ai Assistance Powered By The Baap Company Orchestrator...")
    await init_tts_pools()
    logger.info("✅ TTS Pools & Gemini Ready")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0"}

# ---------------- ENDPOINTS ----------------

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await audio_stream(websocket)

@app.post("/api/reset")
async def reset_session():
    chat_history.clear()
    interrupt_manager.reset_interrupt()
    voice_detector.reset()
    return {"status": "ok"}

# ---------------- MODELS ----------------
class TextRequest(BaseModel):
    text: str
    language: str = None

LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}

@app.post("/api/stream_chat")
async def stream_chat(req: TextRequest):
    user_text_raw = req.text.strip()
    if not user_text_raw:
        raise HTTPException(400, "Empty input")

    logger.info(f"🎯 INPUT: {user_text_raw}")
    interrupt_manager.reset_interrupt()

    # Shared immunity: AI is about to start thinking/speaking
    voice_detector.start_immunity(400)

    # Language Identification & Normalization
    # Priority: UI Selection > Auto-Detection
    det_lang = detect_transliteration(user_text_raw)
    
    # If user explicitly selected a language in UI, ALWAYS use that
    if req.language and req.language in ["en", "hi", "mr"]:
        LOCKED_LANGUAGE = req.language
        print(f" IMMUNITY ACTIVE (600ms)")
        print(f"DEBUG Detect: AUTO={det_lang.upper()}, UI_OVERRIDE={req.language.upper()}")
    elif det_lang in ["hi", "mr"]:
        LOCKED_LANGUAGE = det_lang
    else:
        LOCKED_LANGUAGE = "en"

    logger.info(f"🔒 MODE: {LOCKED_LANGUAGE.upper()}")
    normalized_user_text = ScriptNormalizer.normalize_input(user_text_raw, LOCKED_LANGUAGE)

    async def pipeline():
        response_q = asyncio.Queue()
        tts_q = asyncio.Queue()
        stop_event = asyncio.Event()

        # ---------------- GEMINI TASK ----------------
        async def gemini_task():
            try:
                import datetime
                current_time = datetime.datetime.now().strftime("%I:%M %p")
                history_text = "\n".join([f"{item['role']}: {item['text']}" for item in list(chat_history)])
                
                # Prepare History with Language Tags
                formatted_history = []
                for item in list(chat_history):
                    role = item.get('role', 'User')
                    text = item.get('text', '')
                    lang = item.get('lang', '??')
                    formatted_history.append(f"({lang.upper()}) {role}: {text}")
                history_text = "\n".join(formatted_history)
                
                # STRICT Language Instruction
                if LOCKED_LANGUAGE == "en":
                    lang_rule = "YOU MUST RESPOND IN ENGLISH ONLY. Use only English words. Never use Hindi or Marathi."
                elif LOCKED_LANGUAGE == "hi":
                    lang_rule = "आपको केवल हिंदी में ही बात करनी है। पूरी तरह से देवनागरी लिपि का उपयोग करें। अंग्रेजी या मराठी शब्दों का प्रयोग न करें। (Respond 100% in Hindi Devanagari)."
                elif LOCKED_LANGUAGE == "mr":
                    lang_rule = "तुम्हाला फक्त मराठीतच बोलायचे आहे। पूर्णपणे देवनागरी लिपी वापरा। इंग्रजी किंवा हिंदी शब्द वापरू नका। (Respond 100% in Marathi Devanagari)."

                sys_prompt = f"""You are Ai Assistance Powered By The Baap Company, a human-like AI friend. Current Time: {current_time}.
Never use emojis. Keep it punchy, witty & very warm (10-15 words max).

CONTEXT HISTORY:
{history_text}

CRITICAL INSTRUCTION:
The history above may contain different languages. IGNORE THEM.
{lang_rule}
TARGET_LANGUAGE: {LOCKED_LANGUAGE.upper()}
RESPOND_NOW_IN_{LOCKED_LANGUAGE.upper()}:
USER: "{normalized_user_text}"
AGENT:"""

                stream = gemini_client.models.generate_content_stream(
                    model="gemini-2.0-flash",
                    contents=sys_prompt,
                    config={"temperature": 0.3}  # Reduced for strict consistency
                )

                buffer = ""
                boundaries = {".", "!", "?", "।", ",", "\n"}
                first = True
                full_text = ""

                for chunk in stream:
                    if interrupt_manager.cancel_current_tts or stop_event.is_set():
                        print(" Gemini Interrupted")
                        break
                    if not chunk.text: continue

                    await response_q.put(json.dumps({"type": "text", "content": chunk.text}) + "\n")
                    buffer += chunk.text
                    full_text += chunk.text

                    # Chunking for TTS: Stage P6 Optimizations
                    if any(b in buffer for b in boundaries):
                        potential_pos = [buffer.find(b) for b in boundaries if buffer.find(b) != -1]
                        pos = min(potential_pos) if potential_pos else -1
                        # Stage: Phoneme-level Streaming (Fast start with 6 tokens)
                        m_len = 6 if first else 40

                        if pos != -1 and (pos >= m_len or buffer[pos] in ".!?।\n"):
                            phrase = buffer[:pos + 1].strip()
                            buffer = buffer[pos + 1:]
                            if phrase:
                                valid = ScriptNormalizer.validate_output(phrase, LOCKED_LANGUAGE)
                                if valid:
                                    await tts_q.put(valid)
                                    first = False
                                    
                if buffer.strip() and not interrupt_manager.cancel_current_tts:
                    valid = ScriptNormalizer.validate_output(buffer, LOCKED_LANGUAGE)
                    if valid: await tts_q.put(valid)
                
                #  ALWAYS Save History (Full or Partial)
                if normalized_user_text and full_text.strip():
                    # Check if we already added it
                    if not chat_history or chat_history[-1]["text"] != full_text.strip():
                        # Only add User if not last
                        if not chat_history or chat_history[-1]["role"] != "User": 
                             chat_history.append({"role": "User", "text": normalized_user_text, "lang": LOCKED_LANGUAGE})
                        chat_history.append({"role": "Ai Assistance Powered By The Baap Company", "text": full_text.strip(), "lang": LOCKED_LANGUAGE})
                        print(f" MEMORY SAVED [{LOCKED_LANGUAGE.upper()}]: {full_text.strip()[:40]}...")

            except Exception as e:
                print(f" Gemini Error: {e}")
            finally:
                await tts_q.put(None)

        # ---------------- TTS WORKER ----------------
        async def tts_worker():
            results = {}
            total_items = 0
            next_idx = 0
            done = False
            new_item_event = asyncio.Event()
            
            async def producer():
                nonlocal done, total_items
                while True:
                    item = await tts_q.get()
                    if item is None:
                        done = True
                        new_item_event.set()
                        break
                    results[total_items] = {"type": "audio_text", "content": item, "lang": LOCKED_LANGUAGE}
                    total_items += 1
                    new_item_event.set()

            p_task = asyncio.create_task(producer())

            try:
                while True:
                    if interrupt_manager.cancel_current_tts: break
                    
                    if next_idx in results:
                        res = results.pop(next_idx)
                        if next_idx == 0:
                            voice_detector.start_immunity(800)
                        await response_q.put(json.dumps(res) + "\n")
                        next_idx += 1
                    elif done and next_idx >= total_items:
                        break
                    else:
                        # Wait for new items instead of sleeping fixed time
                        new_item_event.clear()
                        try:
                            await asyncio.wait_for(new_item_event.wait(), timeout=1.0)
                        except asyncio.TimeoutError:
                            if done: break
            finally:
                p_task.cancel()
                await response_q.put(None)

        # ---------------- RUN PIPELINE ----------------
        g_task = asyncio.create_task(gemini_task())
        t_task = asyncio.create_task(tts_worker())
        
        try:
            while True:
                if interrupt_manager.cancel_current_tts:
                    stop_event.set()
                    yield json.dumps({"type": "interrupt"}) + "\n"
                    # 🔥 Save Partial Context on Interrupt
                    if normalized_user_text:
                        chat_history.append({"role": "User", "text": normalized_user_text})
                         # Retrieve whatever text we generated so far from the task scope? 
                         # Actually we can't easily get it here without Refactoring. 
                         # Let's rely on the gemini_task to do a "Final Save" before it dies.
                    break
                
                try:
                    pkt = await asyncio.wait_for(response_q.get(), timeout=0.1)

                    if pkt is None: break
                    yield pkt
                except asyncio.TimeoutError:
                    if g_task.done() and t_task.done() and response_q.empty():
                        break
        finally:
            stop_event.set()
            g_task.cancel()
            t_task.cancel()
            print("🚀 Interaction Pipeline Cleaned.")

    return StreamingResponse(pipeline(), media_type="application/x-ndjson")

# ---------------- LOCAL TTS ----------------
class TTSRequest(BaseModel):
    text: str
    lang: str = None

@app.post("/api/v1/generate")
async def generate_local_tts(req: TTSRequest):
    lang = req.lang or "en"
    pool = get_pool(lang)
    if not pool: raise HTTPException(404, "TTS Pool not found")

    # Fixed Stage P7: Stream directly without async wrapper to avoid blocking event loop
    return StreamingResponse(pool.get_raw_generator(req.text), media_type="audio/pcm")

# ---------------- STATIC ----------------
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(settings.FRONTEND_DIR, "favicon.ico"))

@app.get("/")
async def root():
    return FileResponse(os.path.join(settings.FRONTEND_DIR, "index.html"))

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_probe():
    return {}

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
