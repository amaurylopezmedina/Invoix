import os
import sys

from flask import Flask
from flask_cors import CORS
from routes import routes

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "monitor2025"

# Enable CORS con configuración específica
CORS(
    app,
    resources={
        r"/api/monitor/*": {
            "origins": ["http://localhost:3002", "http://localhost:3000", "http://127.0.0.1:3002", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Accept", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": False,
            "max_age": 3600
        }
    }
)

# Register blueprints with prefix /api/monitor
app.register_blueprint(routes, url_prefix="/api/monitor")


def start_server():
    """Inicia el servidor Flask para el Monitor"""
    try:
        print("=" * 60)
        print("Monitor de Facturación Electrónica - API REST")
        print("=" * 60)
        print(f"Servidor iniciado en: http://0.0.0.0:8002")
        print(f"")
        print(f"Acceso local:  http://127.0.0.1:8002")
        print(f"Acceso red:    http://192.168.x.x:8002")
        print(f"")
        print(f"Endpoints disponibles:")
        print(f"  - GET   /api/monitor/estados-fiscales (Listado de facturas)")
        print(f"  - GET   /api/monitor/empresa-rnc (RNC empresa)")
        print(f"  - PUT   /api/monitor/actualizar-estado-fiscal")
        print(f"  - POST  /api/monitor/generar-pdf (Representación impresa)")
        print(f"  - GET   /api/monitor/health (Estado del servicio)")
        print(f"")
        print(f"IMPORTANTE: Usar HTTP (no HTTPS)")
        print("=" * 60)
        
        app.run(
            host="0.0.0.0",
            port=8002,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    start_server()
