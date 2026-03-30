"""Entry point do servidor FastAPI para WhatsApp.

Uso: python run_api.py
"""

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "src.api.socketio_server:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
