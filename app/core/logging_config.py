import logging
import os
from app.core.config import settings

def setup_logging():
    # Ensure logs directory exists
    if not os.path.exists(settings.LOGS_DIR):
        os.makedirs(settings.LOGS_DIR)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(settings.LOGS_DIR, "app.log"), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

logger = logging.getLogger("samagra")
