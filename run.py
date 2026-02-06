import uvicorn
import os
import sys

if __name__ == "__main__":
    print("Starting Multi-Lang AI Assistant...")
    
    # Force UTF-8 for Windows Console
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Run Uvicorn from the root directory
    from app.core.config import settings
    
    port = int(os.getenv("APP_PORT", 8082))
    host = os.getenv("APP_HOST", "localhost")
    
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
