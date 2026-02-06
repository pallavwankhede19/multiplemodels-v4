/**
 * Samagra Motor Layer (Stage P9 & P10) — FIXED REALTIME VERSION
 * Stable Input + Proper Interrupt + Backend Commit Control
 */

document.addEventListener('DOMContentLoaded', () => {

    // ⭐ Inspection mode (for Antigravity / automation tools)
    const INSPECT_MODE = new URLSearchParams(window.location.search).has("inspect");

    if (INSPECT_MODE) {
        console.log("🧪 Inspection Mode Active — realtime systems paused");
        return; // ⛔ stops mic + websocket + loops from starting
    }
    // ---------- UI ----------
    const chatMessages = document.getElementById('chatMessages');
    const statusLabel = document.getElementById('statusLabel');
    const canvas = document.getElementById('threeCanvas');
    const langOpts = document.querySelectorAll('.lang-opt');
    const textInput = document.getElementById('textInput');
    const sendButton = document.getElementById('sendButton');

    // ---------- STATE ----------
    let currentLang = 'en';
    let globalAudioCtx = null;
    let ttsNextStartTime = 0;
    let ttsQueue = [];
    let isProcessingTTS = false;
    let isInterrupted = false;
    let currentAbortController = null;
    let ttsAbortController = null; // 🔥 Dedicated controller for TTS fetches
    let activeSources = [];

    // ---------- Sensory ----------
    let socket = null;
    let audioWorkletNode = null;

    // ---------- STT VISUAL ONLY ----------
    let recognition = null;
    let isRecognitionActive = false;
    let currentInterimResult = "";

    let lastSubmissionTime = 0;
    let lastManualSubmitTime = 0;
    let lastSubmittedText = "";
    let lastAIEndListenTime = 0; // Cooldown to ignore post-AI echo

    // ---------- Mute Control ----------
    let isMuted = false;

    async function getAudioContext() {
        if (!globalAudioCtx) {
            try {
                // 🔥 CRITICAL: Force 16kHz to match Silero VAD and Piper TTS
                globalAudioCtx = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 16000,
                    latencyHint: 'interactive'
                });
                console.log("🔊 Audio Engine Initialized (Strict 16k):", globalAudioCtx.sampleRate);
            } catch (e) {
                console.warn("Failed to set 16k rate, using default:", e);
                globalAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
        }
        if (globalAudioCtx.state === 'suspended') await globalAudioCtx.resume();
        return globalAudioCtx;
    }

    function stopPlayback() {
        isInterrupted = true;

        if (currentAbortController) {
            console.log("🛑 Aborting active request (Chat Signal)");
            currentAbortController.abort();
            currentAbortController = null;
        }

        if (ttsAbortController) {
            console.log("🔊 Aborting pending TTS chunks");
            ttsAbortController.abort();
            ttsAbortController = null;
        }

        ttsQueue = [];
        ttsCache.clear();
        ttsNextStartTime = 0;

        activeSources.forEach(s => { try { s.stop(0); } catch (e) { } });
        activeSources = [];

        document.body.classList.remove('speaking');
        document.body.classList.add('listening');

        // 🔥 allow next audio after tiny delay
        setTimeout(() => { isInterrupted = false; }, 200);
    }

    // ---------- CHAT FUNCTIONS ----------
    function addChatMessage(text, sender = 'ai') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;

        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);

        // Auto-scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return bubble;
    }

    let currentAIBubble = null;

    // ---------- ORB ----------
    let scene, camera, renderer, particles, innerGlobe;
    const orbColorIdle = 0x0088ff, orbColorListen = 0xff3344, orbColorSpeak = 0x00ff88;

    function initOrb() {
        if (!canvas) return;
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 400;

        renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);

        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(3000 * 3);

        for (let i = 0; i < 3000; i++) {
            const r = 120, t = Math.random() * Math.PI * 2, p = Math.acos((Math.random() * 2) - 1);
            pos[i * 3] = r * Math.sin(p) * Math.cos(t);
            pos[i * 3 + 1] = r * Math.sin(p) * Math.sin(t);
            pos[i * 3 + 2] = r * Math.cos(p);
        }

        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));

        particles = new THREE.Points(
            geo,
            new THREE.PointsMaterial({
                color: orbColorIdle, size: 2.2, transparent: true, opacity: 0.8,
                blending: THREE.AdditiveBlending
            })
        );

        scene.add(particles);

        innerGlobe = new THREE.Mesh(
            new THREE.IcosahedronGeometry(100, 4),
            new THREE.MeshBasicMaterial({ color: orbColorIdle, wireframe: true, transparent: true, opacity: 0.15 })
        );

        scene.add(innerGlobe);
        animateOrb();
    }

    function animateOrb() {
        requestAnimationFrame(animateOrb);
        if (!particles) return;

        particles.rotation.y += 0.003;

        let scaleTarget = 1.0;

        if (document.body.classList.contains('speaking')) {
            scaleTarget = 1.0 + Math.sin(Date.now() * 0.01) * 0.2;
            particles.material.color.setHex(orbColorSpeak);
        }
        else if (document.body.classList.contains('listening')) {
            scaleTarget = 1.3;
            particles.material.color.setHex(orbColorListen);
        }
        else {
            particles.material.color.setHex(orbColorIdle);
        }

        particles.scale.lerp(new THREE.Vector3(scaleTarget, scaleTarget, scaleTarget), 0.1);
        innerGlobe.scale.copy(particles.scale);
        renderer.render(scene, camera);
    }

    let commitTimeout = null;
    let isSubmitting = false;

    // ---------- SENSORY LAYER ----------
    async function initSensoryLayer() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1,
                    sampleRate: 16000
                }
            });

            const ctx = await getAudioContext();
            const source = ctx.createMediaStreamSource(stream);

            await ctx.audioWorklet.addModule('/static/js/worklet.js');
            audioWorkletNode = new AudioWorkletNode(ctx, 'recorder');

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(`${protocol}//${window.location.host}/ws/audio`);

            socket.onmessage = (e) => {
                const data = json_safe_parse(e.data);
                if (!data) return;

                // Update status if this is the first packet confirming connection
                if (statusLabel.innerText === "Connecting...") {
                    statusLabel.innerText = "Always Listening";
                }

                // 🔥 Instant Stop Signal (Stage: Abort)
                if (data.type === 'interrupt' || data.type === 'stop_audio') {
                    console.log("⚡ INTERRUPT/STOP SIGNAL RECEIVED");
                    stopPlayback();
                }

                // 🔥 Backend decides when to submit turn
                if (data.type === 'commit') {
                    if (commitTimeout) clearTimeout(commitTimeout);

                    const trimmed = currentInterimResult.trim();
                    // ChatGPT-Style Filter (Optimized):
                    // 1. Must be at least 3 characters
                    const isMeaningful = trimmed.length >= 3;

                    if (isMeaningful && !isSubmitting) {
                        // Smart Delay: Removed (0ms) - Backend VAD is authoritative now
                        const snapshot = trimmed;
                        const delay = 0; // Instant commit

                        console.log(`🏁 COMMIT | Snapshot: "${snapshot}"`);

                        commitTimeout = setTimeout(() => {
                            if (currentInterimResult.trim().length >= 3 && !isSubmitting) {
                                const final_text = currentInterimResult;
                                console.log("✅ COMMIT EXECUTING:", final_text);
                                currentInterimResult = "";
                                submitTurn(final_text);
                            }
                            commitTimeout = null;
                        }, delay);
                    } else if (trimmed.length > 0) {
                        console.log("🗑️ DISCARDING NOISE/SHORT:", trimmed);
                        currentInterimResult = "";
                    }
                }
            };

            socket.onclose = () => {
                console.warn("📡 Socket Closed. Reconnecting in 2s...");
                setTimeout(() => { if (isRecognitionActive) initSensoryLayer(); }, 2000);
            };

            let captureTimeout = null;
            audioWorkletNode.port.onmessage = (e) => {
                // 🔇 Mute check: Don't send audio when muted
                if (isMuted) return;

                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(e.data);

                    // 🧪 Visual Debug: Confirm capture
                    if (!document.body.classList.contains('speaking') && !isSubmitting) {
                        statusLabel.innerText = "Capturing Audio...";
                        if (captureTimeout) clearTimeout(captureTimeout);
                        captureTimeout = setTimeout(() => {
                            if (!isSubmitting) statusLabel.innerText = "Always Listening";
                        }, 500);
                    }
                }
            };

            source.connect(audioWorkletNode);

            initSTT();   // visual only
            initOrb();
            console.log("✅ Sensory Layer Initialized (Microphone + WebSocket Ready)");

        } catch (err) { console.error("Sensory Fail:", err); }
    }

    function json_safe_parse(str) { try { return JSON.parse(str); } catch (e) { return null; } }

    // ---------- STT VISUAL ONLY ----------
    function initSTT() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' }[currentLang];

        recognition.onstart = () => {
            isRecognitionActive = true;
            document.body.classList.add('listening');
            statusLabel.innerText = "Always Listening";
        };

        recognition.onresult = (e) => {
            if (document.body.classList.contains('speaking')) return;

            // 🔥 STT Absorption Window: Ignore late results for 2s after submission
            if (Date.now() - lastSubmissionTime < 2000) {
                console.log("⏳ ABSORBING LATE STT...");
                return;
            }

            let fullTranscript = '';
            for (let i = 0; i < e.results.length; i++) {
                fullTranscript += e.results[i][0].transcript;
            }

            if (fullTranscript.trim()) {
                currentInterimResult = fullTranscript;
                // 📝 STT DEBUG: See exactly what the browser is hearing
                console.log("📝 STT Result:", currentInterimResult);
            }
        };

        recognition.onend = () => {
            isRecognitionActive = false;
            setTimeout(() => { try { recognition.start(); } catch (err) { } }, 300);
        };

        try { recognition.start(); } catch (err) { }
    }

    // ---------- SUBMIT TURN ----------
    async function submitTurn(text) {
        if (isSubmitting) return;
        const now = Date.now();

        // 🔥 Hard Lock: No submissions within 1.2s of each other (Reduced for snappy feel)
        if (now - lastSubmissionTime < 1201) return;

        const normalizedText = text.trim().toLowerCase();

        // 🔥 Near-Duplicate Similarity Guard (Reduced to 4s window)
        if (lastSubmittedText) {
            const isSub = normalizedText.includes(lastSubmittedText) || lastSubmittedText.includes(normalizedText);
            const isNear = normalizedText.length > 5 && Math.abs(normalizedText.length - lastSubmittedText.length) < 5;
            if ((isSub || isNear) && (now - lastSubmissionTime < 4001)) {
                console.log("🛑 BLOCKING NEAR-DUPLICATE:", normalizedText);
                return;
            }
        }

        isSubmitting = true;
        if (commitTimeout) clearTimeout(commitTimeout);
        currentInterimResult = ""; // ABSOLUTELY FLUSH

        // 🔥 Post-AI Echo Guard
        if (now - lastAIEndListenTime < 1200) {
            console.log("🤐 IGNORING POST-AI ECHO:", normalizedText);
            isSubmitting = false;
            return;
        }

        // 🔥 Force STT Reset
        if (recognition && isRecognitionActive) {
            try { recognition.stop(); } catch (e) { }
        }

        lastSubmissionTime = now;
        lastSubmittedText = normalizedText;
        lastManualSubmitTime = now;

        stopPlayback();
        isInterrupted = false;

        console.log("🚀 SUBMIT:", text);

        // Add user message to chat
        addChatMessage(text, 'user');

        statusLabel.innerText = "Thinking...";
        currentAbortController = new AbortController();

        // Create new AI bubble for response
        currentAIBubble = addChatMessage('', 'ai');

        try {
            const resp = await fetch('/api/stream_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, language: currentLang }),
                signal: currentAbortController.signal
            });

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let partial = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done || isInterrupted) break;

                const lines = (partial + decoder.decode(value)).split('\n');
                partial = lines.pop();

                for (const line of lines) {
                    if (!line.trim() || isInterrupted) continue;
                    const data = json_safe_parse(line);
                    if (!data) continue;

                    if (data.type === 'text') {
                        if (currentAIBubble) {
                            currentAIBubble.textContent += data.content;
                            chatMessages.scrollTop = chatMessages.scrollHeight;

                            // If chat is collapsed, show activity
                            if (chatWrapper && chatWrapper.classList.contains('collapsed')) {
                                chatToggleBtn.classList.add('has-new');
                            }
                        }
                    }
                    else if (data.type === 'audio_text') {
                        ttsQueue.push({ text: data.content, lang: data.lang });
                        if (!isProcessingTTS) processTTS();
                    }
                }
            }
        } catch (e) {
            if (e.name !== 'AbortError') console.error(e);
        }
        finally {
            isSubmitting = false;
            if (!isInterrupted) statusLabel.innerText = "Always Listening";
        }
    }

    // ---------- TTS ----------
    // ---------- TTS PRE-FETCH OPTIMIZATION ----------
    async function processTTS() {
        if (isProcessingTTS) return;
        isProcessingTTS = true;

        try {
            while (ttsQueue.length > 0 && !isInterrupted) {
                const item = ttsQueue.shift();
                await performAudioPlayback(item.text, item.lang);
            }
        } finally {
            isProcessingTTS = false;
            // Clean up AbortController if finished naturally
            if (ttsQueue.length === 0) ttsAbortController = null;
        }
    }

    // Map to cache pre-fetched readers/responses
    const ttsCache = new Map();

    async function performAudioPlayback(text, lang) {
        try {
            const ctx = await getAudioContext();
            document.body.classList.remove('listening');
            document.body.classList.add('speaking');

            // 🔥 SYNC: Tell Backend AI is talking
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'ai_state', status: 'speaking' }));
            }

            // 🔥 FETCH Audio with Pre-fetch Support
            if (!ttsAbortController) ttsAbortController = new AbortController();

            let resp;
            if (ttsCache.has(text)) {
                console.log("⚡ USING PRE-FETCHED CACHE:", text.substring(0, 20));
                resp = ttsCache.get(text);
                ttsCache.delete(text);
            } else {
                resp = await fetch("/api/v1/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text, lang }),
                    signal: ttsAbortController.signal
                });
            }

            const reader = resp.body.getReader();
            let leftover = new Uint8Array(0);

            // Pre-fetch next item in queue if available
            if (ttsQueue.length > 0) {
                const next = ttsQueue[0];
                console.log("🚚 Pre-fetching next chunk:", next.text.substring(0, 20));
                // We don't await this, just trigger it
                fetch("/api/v1/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: next.text, lang: next.lang }),
                    signal: ttsAbortController.signal
                }).then(r => ttsCache.set(next.text, r));
            }

            while (true) {
                if (isInterrupted) { reader.cancel(); return; }

                // 🔥 Re-Sync: Tell backend we are still speaking on every chunk 
                // to keep VAD strictness refreshed
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: 'ai_state', status: 'speaking' }));
                }

                const { done, value } = await reader.read();
                if (done) break;

                const combined = new Uint8Array(leftover.length + value.length);
                combined.set(leftover);
                combined.set(value, leftover.length);

                const usable = combined.length - (combined.length % 2);
                const usableData = combined.subarray(0, usable);
                leftover = combined.subarray(usable);

                if (usable === 0) continue;

                const f32 = new Float32Array(usable / 2);
                const view = new DataView(usableData.buffer, usableData.byteOffset, usableData.byteLength);

                for (let i = 0; i < f32.length; i++) {
                    f32[i] = view.getInt16(i * 2, true) / 32768.0;
                }

                const buffer = ctx.createBuffer(1, f32.length, 22050);
                buffer.getChannelData(0).set(f32);

                const source = ctx.createBufferSource();
                source.buffer = buffer;
                source.connect(ctx.destination);

                const now = ctx.currentTime;
                // Tighten the gap for Jarvis-feel (0.02 instead of 0.05)
                if (ttsNextStartTime < now) ttsNextStartTime = now + 0.02;
                source.start(ttsNextStartTime);

                activeSources.push(source);
                ttsNextStartTime += buffer.duration;

                source.onended = () => {
                    activeSources = activeSources.filter(s => s !== source);

                    // 🔥 Fixed: Only switch back to listening if ALL sentences are done
                    if (activeSources.length === 0 && !isInterrupted && !isProcessingTTS && ttsQueue.length === 0) {
                        document.body.classList.remove('speaking');
                        lastAIEndListenTime = Date.now();

                        if (recognition) {
                            try { recognition.stop(); } catch (e) { }
                        }

                        if (socket && socket.readyState === WebSocket.OPEN) {
                            socket.send(JSON.stringify({ type: 'ai_state', status: 'listening' }));
                        }
                    }
                };
            }
        } catch (err) { }
    }

    // ---------- UI ----------
    // Reset Button: Stop AI + Full Refresh
    const resetBtn = document.getElementById('terminateButton');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            // 1. Stop all audio immediately
            stopPlayback();

            // 2. Call backend reset
            try {
                await fetch('/api/reset', { method: 'POST' });
            } catch (e) { }

            // 3. Force full page reload for clean state
            window.location.reload();
        });
    }

    // Mute Button: Toggle Listening On/Off
    const muteBtn = document.getElementById('muteButton');
    if (muteBtn) {
        muteBtn.addEventListener('click', () => {
            isMuted = !isMuted;

            if (isMuted) {
                muteBtn.textContent = '🔇 Unmute';
                muteBtn.classList.add('danger');
                statusLabel.innerText = 'Muted';
                console.log('🔇 MICROPHONE MUTED');
            } else {
                muteBtn.textContent = '🎤 Mute';
                muteBtn.classList.remove('danger');
                statusLabel.innerText = 'Always Listening';
                console.log('🎤 MICROPHONE ACTIVE');
            }
        });
    }

    langOpts.forEach(opt => {
        opt.addEventListener('click', () => {
            langOpts.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            currentLang = opt.dataset.lang;
            if (recognition) {
                recognition.lang = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' }[currentLang];
                recognition.abort();
            }
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'lang_update', lang: currentLang }));
            }
        });
    });

    sendButton.addEventListener('click', () => {
        const val = textInput.value.trim();
        if (val) { submitTurn(val); textInput.value = ''; }
    });

    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') { sendButton.click(); }
    });

    document.addEventListener('click', () => {
        if (!socket) {
            statusLabel.innerText = "Connecting...";
            initSensoryLayer();
        }
    }, { once: true });

    // ---------- CHAT UI TOGGLE ----------
    const chatWrapper = document.getElementById('chatWrapper');
    const chatToggleBtn = document.getElementById('chatToggleBtn');
    const chatCloseBtn = document.getElementById('chatCloseBtn');

    if (chatWrapper && chatToggleBtn && chatCloseBtn) {
        chatToggleBtn.addEventListener('click', () => {
            chatWrapper.classList.toggle('collapsed');
            if (!chatWrapper.classList.contains('collapsed')) {
                chatToggleBtn.classList.remove('has-new');
            }
        });

        chatCloseBtn.addEventListener('click', () => {
            chatWrapper.classList.add('collapsed');
        });

        // Initialize as collapsed on mobile
        if (window.innerWidth < 768) {
            chatWrapper.classList.add('collapsed');
        }
    }

});
