import asyncio
import json
import os
import sys

import uvicorn  # Uvicorn ASGI server
from api import delete_expired_tokens
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from routes import routes, cargar_configuracion_api

from starlette.middleware.wsgi import WSGIMiddleware

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from db.uDB import *
from config.uGlobalConfig import *

from glib.uGlobalLib import *

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "2016")


# Cargar configuración del API
config = cargar_configuracion_api()
app.config["UPLOAD_FOLDER"] = config.get("csv_rute")

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Register blueprints (routes)
app.register_blueprint(routes)


def create_tables():

    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()
    # mOSTRAR LA CONFIGURCION DE LA BASE DE DATOS
    mostrarConfiguracion(GConfig, cn1)

    """Crea las tablas necesarias en la base de datos si no existen."""
    try:

        # Crear tabla de usuarios
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='usuariosj' AND xtype='U')
        BEGIN
            CREATE TABLE usuariosj (
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT GETDATE()
            )
        END
        """
        cn1.execute_query(query)

        # Crear tabla de tokens
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tokenjwt' AND xtype='U')
        BEGIN
            CREATE TABLE tokenjwt (
                username VARCHAR(50) NOT NULL,
                token VARCHAR(255) NOT NULL,
                active BIT NOT NULL DEFAULT 1,
                [1hour] BIT DEFAULT 0,
                [30min] BIT DEFAULT 0,
                [5min] BIT DEFAULT 0,
                creation_time DATETIME DEFAULT GETDATE()
            )
        END
        """

        cn1.execute_query(query)

        # Crear tabla de claves API
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='api_keys' AND xtype='U')
        BEGIN
            CREATE TABLE api_keys (
                username VARCHAR(50) NOT NULL,
                hashed_key VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL
            )
        END
        """

        cn1.execute_query(query)

        print("Tablas creadas exitosamente o ya existen.")
    except Exception as e:
        print(f"Error al crear tablas: {e}")


# Ejecutar la función de creación de tablas al iniciar la aplicación
create_tables()

# Configuración del programador de tareas
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=delete_expired_tokens, trigger="interval", minutes=1)
# scheduler.start()

# Convert Flask app to ASGI with WSGIMiddleware
asgi_app = WSGIMiddleware(app)


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
            asgi_app,  # Usa el objeto directamente
            host="0.0.0.0",  # Bind to all interfaces
            port=port,
            ssl_certfile=cert_path,  # SSL certificate file
            ssl_keyfile=key_path,  # SSL key file
            log_level="info",  # Reduce verbosity of logging
            log_config=None,  # Disable Uvicorn's logging configuration
            workers=(
                1 if os.name == "nt" else max(1, (os.cpu_count() or 2) // 2)
            ),  # Windows: single worker
            timeout_keep_alive=5,
            limit_max_requests=1000,
            proxy_headers=True,
        )
    except Exception as e:
        print(f"Error al iniciar Uvicorn: {e}")
        import traceback

        traceback.print_exc()  # This will print the full traceback of the error


if __name__ == "__main__":
    start_server()
