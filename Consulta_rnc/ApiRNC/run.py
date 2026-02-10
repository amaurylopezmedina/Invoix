import asyncio
import json
import os

import uvicorn  # Uvicorn ASGI server
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from starlette.middleware.wsgi import (
    WSGIMiddleware,
)  # Correct middleware for WSGI to ASGI conversion


from routes import routes

# Create Flask app
app = Flask(__name__)


# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Register blueprints (routes)
app.register_blueprint(routes)

asgi_app = WSGIMiddleware(app)


def cargar_configuracion_api():
    """Carga la configuración desde config/api.json"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "api.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def start_server():
    """Inicia el servidor Uvicorn con soporte SSL usando configuración de api.json."""
    config = cargar_configuracion_api()
    port = config.get("port_rute", 8001)
    cert_path = config.get("ssl_certfile_rute")
    key_path = config.get("ssl_keyfile_rute")

    try:
        print(f"Iniciando Uvicorn con SSL en https://0.0.0.0:{port}")

        # Ensure Windows uses the SelectorEventLoop
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        uvicorn.run(
            asgi_app,  # Pass the ASGI-wrapped app
            host="0.0.0.0",  # Bind to all interfaces
            port=port,
            ssl_certfile=cert_path,  # SSL certificate file
            ssl_keyfile=key_path,  # SSL key file
            log_level="info",  # Reduce verbosity of logging
            log_config=None,  # Disable Uvicorn's logging configuration
        )
    except Exception as e:
        print(f"Error al iniciar Uvicorn: {e}")
        import traceback

        traceback.print_exc()  # This will print the full traceback of the error


if __name__ == "__main__":
    start_server()
