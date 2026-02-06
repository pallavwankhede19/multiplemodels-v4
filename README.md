# Ai Assistance Powered By The Baap Company: Real-Time Multilingual AI Voice Assistant

**Ai Assistance Powered By The Baap Company** is a premium, ultra-low-latency AI Voice Assistant designed to be a warm, human-like companion. It speaks **English**, **Hindi**, and **Marathi** with deep emotional intelligence and real-time situational awareness.

---

## ✨ Features: The Premium Experience

**Ai Assistance Powered By The Baap Company** is designed for a natural, face-to-face conversational feel, moving beyond standard command-response bots.

*   **🎙️ Smart Barge-In**: Interrupt the AI naturally at any time. Using a sophisticated dual-threshold VAD (Neural Ear), the AI instantly stops speaking the moment it hears your voice and begins listening to your next thought.
*   **🧠 Adaptive VAD (Neural Ear)**: 
    *   **English**: Fast-commit mode (~600ms silence) for snappy, rapid-fire dialogue.
    *   **Hindi/Marathi**: Relaxed-commit mode (~1.1s silence) to accommodate the natural cadence and longer pauses of Indic languages.
*   **🔒 Strict Language Lock**: An advanced multi-layer enforcement system. If you select Hindi, the AI is cryptographically locked to **Devanagari script only**, rejecting any English words to maintain 100% immersion.
*   **🔮 Three.js Living Orb**: A high-performance 3D visual heart that pulses with life. It changes color and scale dynamically based on its state: **Blue (Idle)**, **Red (Listening)**, and **Green (Speaking)**.
*   **💬 Floating Smart Chat**: A non-intrusive, collapsible side-corner chatbox with persistence-aware notifications (red dot pulse) if the AI responds while hidden.
*   **🧠 Situational Intelligence**: Powered by **Gemini 2.0 Flash**, Ai Assistance Powered By The Baap Company handles complex multi-turn conversations while maintaining a consistent persona.
*   **🌐 Real-Time Grounding**: Integrated Google Search for the latest news, incidents, and facts, ensuring it never hallucinates current events.
*   **🎭 Emotional Resonance**: Automatically adapts its tone and script based on your sentiment—sharing joy, comfort, or enthusiasm.

---

## 🏗️ Technical Architecture (The 10-Stage Pipeline)

The system operates on an high-performance orchestration pipeline:

1.  **Neural Ear (VAD)**: A 16kHz PCM stream analyzed by `webrtcvad` + Silero VAD with RMS volume gating to ignore background noise.
2.  **Immediate Interruption (Barge-In)**: A hardware-level cutoff system that kills active audio buffers in the browser and cancels backend generation tasks the microsecond user speech is validated.
3.  **Language Lock**: Advanced multi-layer detection (character markers, verb patterns "aahe/hai", transliteration weights) locking response to `hi`, `mr`, or `en`.
4.  **Hinglish/Manglish Normalization**: Automatically converts transliterated text into native Devanagari script for maximum LLM reasoning accuracy.
5.  **Gemini 2.0 Flash Engine**: Streams tokens with weighted temperature for a balance of creativity and factual speed.
6.  **Dynamic Phrase Buffering**: Intelligently splits streams for sub-second audio generation (First chunk < 15 chars).
7.  **In-Memory TTS Pool**: Parallel **Piper ONNX** worker threads pre-loaded in RAM for near-zero synthesis latency.
8.  **Active Audio Sync**: Tracking and scheduling individual PCM segments in the browser for seamless, gapless playback.
9.  **NDJSON Mixed Protocol**: Concurrent delivery of text tokens and audio triggers over a single streaming response.
10. **Living UI Rendering**: Smooth starfield and particle animations at 60+ FPS using WebGL integration.

---

## 🚀 Technical Specs

- **Model**: `gemini-2.0-flash`
- **TTS**: Piper (ONNX) with In-Memory Worker Pools
- **VAD**: Silero VAD + RMS Volume Gating (Adaptive Thresholds)
- **Latency**: Sub-1s Voice-to-Voice response
- **Interruption Support**: True hardware-level stop (mid-syllable)
- **Languages**: English, Hindi, Marathi (Advanced linguistic differentiation)

---

## 🏗️ Project Structure

```text
├── app/
│   ├── api/             # API Endpoints (WebSockets & REST)
│   ├── core/            # Config, Security, and Logging setup
│   ├── services/        # Orchestrators (VAD, Language Detection, TTS Pool)
│   └── main.py          # FastAPI Root Application
├── docs/                # Project Documentation & Architecture Guides
├── frontend/            # HTML/JS Interaction Layer
│   └── static/          # Assets (CSS/JS/Images)
├── models/              # Piper ONNX Models (english.onnx, hindi.onnx, etc.)
├── logs/                # Application & Connection Logs
├── scripts/             # Utility & Deployment Scripts
├── tests/               # Unit & Integration Tests
├── .env                 # Environment Configuration (Local/Prod)
├── .gitignore           # File Exclusions (Models, Venv, Logs)
├── run.py               # Main Entry Point
├── requirements.txt     # Python Dependencies
```

---

## 📦 Getting Started

### Installation
1.  **Clone & Install**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configuration**:
    Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.
    ```bash
    cp .env.example .env
    ```
3.  **Models**:
    Ensure the `.onnx` and `.json` files for English, Hindi, and Marathi are in the `models/` directory with lowercase names (e.g., `english.onnx`).

### Running the System
```bash
python run.py
```
1. Access `http://localhost:8082` in Chrome/Edge.
2. **First Interaction**: Click anywhere to wake up the Audio Engine.
3. **Usage**: Talk naturally. Use the text box if you are in a loud environment.

---

## ❓ Troubleshooting

*   **Microphone Not Working**: Ensure your browser has permission (Chrome > Settings > Privacy > Microphone). Check if `AudioWorklet` logs appear in console.
*   **Static/Noise**: The VAD auto-calibrates. If usage is noisy, try reloading to recalibrate the background noise floor.
*   **Wrong Language**: Click the language toggle (EN/HI/MR) to force the mode if auto-detection is struggling with short phrases.
*   **Port In Use**: If `8082` is busy, check `run.py` or kill existing python processes.

---
**Built with ❤️ by Antigravity AI for The Baap Company**
