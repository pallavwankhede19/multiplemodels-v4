import torch
import numpy as np
import time

class VoiceDetector:
    def __init__(self, aggressiveness=2, volume_threshold=0.01):
        # ---------------- Neural VAD (Silero) ----------------
        print("🧠 Loading Silero VAD Model...")
        try:
            self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                             model='silero_vad',
                                             force_reload=False,
                                             trust_repo=True)
            (self.get_speech_timestamps, _, self.read_audio, _, _) = utils
            print("✅ Silero VAD Ready")
        except Exception as e:
            print(f"⚠️ Silero Load Fail ({e}), falling back to basic VAD")
            self.model = None

        self.volume_threshold = volume_threshold
        self.rolling_buffer = []  # For Silero (needs 512 samples)
        
        # ---------------- Calibration ----------------
        self.calibration_frames = []
        self.calibrated = False

        # ---------------- Real-time speech state ----------------
        self.speech_frames = 0
        self.silence_frames = 0
        self.speech_session_active = False

        # Trigger logic (ChatGPT-style robust triggering)
        self.speech_trigger_frames = 6   # ~192ms sustained speech (Stage 1 Gate)
        self.silence_commit_frames = 35  # ~1.1s silence to commit (Balanced for Marathi/English)
        self.silence_reset_frames = 80   # ~2.5s to reset

        # Immunity window
        self.immunity_until = 0
        self.strict_mode = False
        
        # Speaker Lock
        self.speaker_lock_until = 0
        self.SPEAKER_LOCK_DURATION = 3.0

    def set_strict_mode(self, enabled: bool):
        self.strict_mode = enabled

    def set_language_mode(self, lang: str):
        if lang == 'en':
            self.silence_commit_frames = 20  # ~0.6s (Fast for English)
            print(f"⚡ VAD Mode: ENGLISH (Fast Commit 0.6s)")
        else:
            self.silence_commit_frames = 35  # ~1.1s (Relaxed for HI/MR)
            print(f"🧘 VAD Mode: {lang.upper()} (Relaxed Commit 1.1s)")

    def get_rms(self, pcm_frame: bytes):
        if not pcm_frame or len(pcm_frame) < 2:
            return 0
        audio_data = np.frombuffer(pcm_frame, dtype=np.int16).astype(np.float32)
        if audio_data.size == 0: return 0
        audio_data *= (1.0 / 32768.0)
        return float(np.sqrt(np.mean(audio_data * audio_data)))

    def calibrate(self, rms_value):
        if self.calibrated: return
        self.calibration_frames.append(rms_value)
        if len(self.calibration_frames) >= 20:
            avg_noise = sum(self.calibration_frames) / len(self.calibration_frames)
            self.volume_threshold = max(0.01, avg_noise * 2.5)
            self.calibrated = True
            print(f"🛠️ VAD CALIBRATED: Ambient={round(avg_noise,4)} Threshold={round(self.volume_threshold,4)}")

    def is_speech(self, pcm_frame: bytes, sample_rate: int = 16000):
        if time.time() < self.immunity_until:
            return False
            
        # 1. Fragment-Resistant Buffer (Stage 1)
        audio_int16 = np.frombuffer(pcm_frame, dtype=np.int16)
        self.rolling_buffer.extend(audio_int16.tolist())
        
        has_speech_in_cycle = False

        # Process ALL available 512-sample (32ms) chunks in the buffer
        while len(self.rolling_buffer) >= 512:
            chunk_data = np.array(self.rolling_buffer[:512], dtype=np.float32) / 32768.0
            self.rolling_buffer = self.rolling_buffer[512:]
            
            rms = np.sqrt(np.mean(chunk_data**2))
            
            # 2. Volume Gate (Stage 2)
            # In Strict Mode (AI Speaking), we ignore echo with 10x floor
            thresh = self.volume_threshold * 10.0 if self.strict_mode else 0.003
            
            if rms < thresh:
                self.speech_frames = max(0, self.speech_frames - 1)
                self.silence_frames += 1
                continue

            # 3. Neural Verification (Stage 3)
            is_voiced = False
            if self.model:
                with torch.no_grad():
                    conf = self.model(torch.from_numpy(chunk_data), sample_rate).item()
                    # High confidence required in strict mode to filter echo
                    conf_req = 0.4 if self.strict_mode else 0.2
                    if conf > conf_req or rms > 0.025:
                        is_voiced = True
            else:
                is_voiced = True

            if is_voiced:
                if not self.speech_session_active:
                    print(f"✅ VAD: HUMAN SPEECH DETECTED (RMS: {round(rms,4)})", flush=True)
                self.speech_frames = min(50, self.speech_frames + 1)
                self.silence_frames = 0
                self.speech_session_active = True
            else:
                self.speech_frames = max(0, self.speech_frames - 1)
                self.silence_frames += 1

            # 4. Fast Trigger: ~160ms (5 frames)
            # Strict Trigger: ~800ms (25 frames) to ensure it's not a loud echo
            trigger_limit = 10 if self.strict_mode else 5
            if self.speech_frames >= trigger_limit:
                if self.speech_frames == trigger_limit:
                    print(f"🎤 TURN ACTIVE {'(Interruption)' if self.strict_mode else ''}", flush=True)
                has_speech_in_cycle = True

        return has_speech_in_cycle

    def check_commit(self):
        # Use configurable threshold (40 frames = ~1.2s) to allow natural pauses in Marathi/Hindi
        if self.speech_session_active and self.silence_frames >= self.silence_commit_frames:
            print("🏁 VAD COMMIT: Sent to Gemini.", flush=True)
            self.speech_session_active = False
            self.speech_frames = 0
            self.silence_frames = 0
            return True
        return False

    def start_immunity(self, duration_ms=600):
        self.immunity_until = time.time() + (duration_ms / 1000)

    def reset(self):
        self.speech_frames = 0
        self.silence_frames = 0
        self.speech_session_active = False
        self.rolling_buffer = []

# REQUIRED GLOBAL SINGLETON
voice_detector = VoiceDetector()
