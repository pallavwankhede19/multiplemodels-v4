from app.services.tts_pool import TTSWorkerPool
from app.core.config import settings
from app.core.logging_config import logger

tts_pools = {}

async def init_tts_pools():
    for lang, model_path in settings.PIPER_MODELS.items():
        # Deriving config path from model path (english.onnx -> english.onnx.json)
        config_path = f"{model_path}.json"
        
        # 🔥 Marathi model is slower, use more workers for better parallelization
        num_workers = 3 if lang == 'mr' else 2
        
        pool = TTSWorkerPool(
            model_path=model_path,
            config_path=config_path,
            workers=num_workers
        )
        await pool.start()
        tts_pools[lang] = pool
        logger.info(f"✅ TTS Pool Ready: {lang}")

def get_pool(lang: str):
    return tts_pools.get(lang)
