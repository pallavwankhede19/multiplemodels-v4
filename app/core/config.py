import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    APP_NAME = "Multi-Lang API"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Path settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
    
    # App settings
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.70"))
    
    # Model Paths - Normalized to lowercase for professionalism
    PIPER_MODELS = {
        "en": os.path.join(MODELS_DIR, "english.onnx"),
        "hi": os.path.join(MODELS_DIR, "hindi.onnx"),
        "mr": os.path.join(MODELS_DIR, "marathi.onnx")
    }

settings = Settings()
