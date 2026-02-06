import asyncio
import numpy as np
from piper import PiperVoice
from app.services.interrupt_manager import interrupt_manager
from app.core.logging_config import logger

class TTSWorkerPool:
    def __init__(self, model_path, config_path, workers=2):
        self.model_path = model_path
        self.config_path = config_path
        self.workers = workers

        self.queue = asyncio.Queue()
        self.voice = None
        self.worker_tasks = []

    async def start(self):
        logger.info(f"🔊 Loading Piper model: {self.model_path}")
        self.voice = PiperVoice.load(self.model_path, self.config_path)

        for i in range(self.workers):
            task = asyncio.create_task(self.worker_loop(i))
            self.worker_tasks.append(task)

    async def worker_loop(self, wid):
        while True:
            job = await self.queue.get()
            if job is None:
                break

            text, future = job
            try:
                # Run blocking synthesis in a thread
                audio_bytes = await asyncio.to_thread(self.synthesize_raw_sync, text)
                future.set_result(audio_bytes)
            except Exception as e:
                logger.error(f"❌ TTS Worker {wid} error: {e}")
                future.set_result(None)

    def synthesize_raw_sync(self, text: str):
        """
        Stage P7: Piper ONNX Synthesis Loop
        Synchronous wrapper to get all raw bytes.
        """
        if not self.voice:
            return b""
        
        all_bytes = b""
        try:
            for chunk in self.voice.synthesize(text):
                # Constraints Stage P7: IF interrupt_signal == TRUE: break
                if interrupt_manager.cancel_current_tts:
                    break
                    
                if hasattr(chunk, 'audio_int16_bytes') and chunk.audio_int16_bytes:
                    all_bytes += chunk.audio_int16_bytes
                elif hasattr(chunk, 'audio'):
                    if chunk.audio.dtype != np.int16:
                        audio_int16 = (chunk.audio * 32767).astype(np.int16)
                        all_bytes += audio_int16.tobytes()
                    else:
                        all_bytes += chunk.audio.tobytes()
        except Exception as e:
            logger.error(f"❌ Synthesis logic error: {e}")
        return all_bytes

    def get_raw_generator(self, text: str):
        """
        Returns a generator yielding raw PCM chunks.
        Used for the /api/v1/generate endpoint.
        """
        if not self.voice:
            return
            
        try:
            for chunk in self.voice.synthesize(text):
                if interrupt_manager.cancel_current_tts:
                    break
                if hasattr(chunk, 'audio_int16_bytes') and chunk.audio_int16_bytes:
                    yield chunk.audio_int16_bytes
                elif hasattr(chunk, 'audio'):
                    if chunk.audio.dtype != np.int16:
                        audio_int16 = (chunk.audio * 32767).astype(np.int16)
                        yield audio_int16.tobytes()
                    else:
                        yield chunk.audio.tobytes()
        except Exception as e:
            print(f"❌ Raw Synthesis error: {e}")

    async def submit(self, text: str):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((text, future))
        return await future

    async def shutdown(self):
        for _ in range(self.workers):
            await self.queue.put(None)
