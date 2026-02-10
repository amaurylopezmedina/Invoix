import asyncio
import os
import ssl
import sys

import uvicorn  # Uvicorn ASGI server
from api import delete_expired_tokens
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_db_connection
from flask import Flask
from flask_cors import CORS
from routes import routes
from starlette.middleware.wsgi import (
    WSGIMiddleware,
)  # Correct middleware for WSGI to ASGI conversion

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from db.uDB import *
from config.uGlobalConfig import GConfig

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "2016")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.abspath(os.sep), "xmlvalidar", "csv")

# Enable Cross-Origin Resource Sharing (CORS) con configuración más permisiva
CORS(
    app,
    origins=["*"],  # Permitir todos los orígenes para desarrollo
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "x-api-key",
        "X-Requested-With",
        "Accept",
        "Content-Disposition",
    ],
    supports_credentials=False,  # Cambiar a False para evitar problemas
    expose_headers=["*", "Content-Disposition", "Content-Length", "Content-Type"],
)

# Register blueprints (routes)
app.register_blueprint(routes)


def create_tables():
    """Crea las tablas necesarias en la base de datos si no existen."""
    try:
        # Conexión a la base de datos usando función local de APIWEB
        connection = get_db_connection()
        cursor = connection.cursor()

        # Crear tabla de usuarios
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='usuariosj' AND xtype='U')
        BEGIN
            CREATE TABLE usuariosj (
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                rnc VARCHAR(12) NOT NULL,
                created_at DATETIME DEFAULT GETDATE()
            )
        END
        """
        cursor.execute(query)
        connection.commit()

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
        cursor.execute(query)
        connection.commit()

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
        cursor.execute(query)
        connection.commit()

        # Agregar columna tipo_usuario si no existe
        query = """
        IF NOT EXISTS (
            SELECT * FROM sys.columns 
            WHERE object_id = OBJECT_ID('usuariosj') 
            AND name = 'tipo_usuario'
        )
        BEGIN
            ALTER TABLE usuariosj 
            ADD tipo_usuario VARCHAR(20) DEFAULT 'FACTURACION'
        END
        """
        cursor.execute(query)
        connection.commit()

        cursor.close()
        connection.close()
        
        print("Tablas creadas exitosamente o ya existen.")

    except Exception as e:
        print(f"Error al crear tablas: {e}")


# Crear tabla de queries SQL (sistema de soporte)
def create_query_tables():
    """Crea la tabla de queries SQL para el sistema de soporte"""
    try:
        from query_models import create_query_table, ensure_query_directory

        # Asegurar que el directorio C:\Query\ existe
        ensure_query_directory()
        print("Directorio C:\\Query\\ verificado/creado")

        # Crear tabla en base de datos
        create_query_table()
        print("Tabla sql_queries verificada/creada")

    except Exception as e:
        print(f"Error al crear tabla de queries: {e}")


# Crear tabla de manuales PDF (sistema de soporte)
def create_manual_tables():
    """Crea la tabla de manuales/instructivos PDF para el sistema de soporte"""
    try:
        from manual_models import create_manual_table, ensure_manual_directory

        # Asegurar que el directorio C:\Manuales\ existe
        ensure_manual_directory()
        print("Directorio C:\\Manuales\\ verificado/creado")

        # Crear tabla en base de datos
        create_manual_table()
        print("Tabla manuales verificada/creada")

    except Exception as e:
        print(f"Error al crear tabla de manuales: {e}")


# Crear tabla de tickets (sistema de incidencias)
def create_ticket_tables():
    """Crea las tablas del sistema de tickets de incidencias"""
    try:
        from ticket_models import TicketDatabase

        # Asegurar que el directorio C:\Tickets\Attachments\ existe
        attachments_path = r"C:\Tickets\Attachments"
        os.makedirs(attachments_path, exist_ok=True)
        print("Directorio C:\\Tickets\\Attachments\\ verificado/creado")

        # Crear tablas en base de datos
        TicketDatabase.create_tables()
        print("Tablas de tickets verificadas/creadas")

    except Exception as e:
        print(f"Error al crear tablas de tickets: {e}")


# Crear tabla de facturas importadas
def create_facturas_table():
    """Crea la tabla de facturas importadas en SQL Server"""
    try:
        from routes import verificar_o_crear_tabla_facturas

        exito, mensaje = verificar_o_crear_tabla_facturas()
        if exito:
            print("Tabla FacturasImportadas verificada/creada")
        else:
            print(f"Error al crear tabla de facturas: {mensaje}")

    except Exception as e:
        print(f"Error al crear tabla de facturas: {e}")


# Ejecutar la función de creación de tablas al iniciar la aplicación
create_tables()
create_query_tables()  # Tabla para queries
create_manual_tables()  # Tabla para manuales PDF
create_ticket_tables()  # Tablas para tickets de incidencias
create_facturas_table()  # Tabla para facturas importadas

# Configuración del programador de tareas
scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_expired_tokens, trigger="interval", minutes=30)
scheduler.start()

# Convert Flask app to ASGI with WSGIMiddleware
asgi_app = WSGIMiddleware(app)


def start_server():
    """Inicia el servidor Uvicorn con soporte SSL mejorado para iOS."""
    cert_path = "C:/cert/certificado.pem"
    key_path = "C:/cert/llave_privada.pem"

    try:
        print(
            f"Iniciando Uvicorn con SSL en https://0.0.0.0:8001"
        )  # ✅ Muestra el puerto real

        # Configurar SSL con cadena completa
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_path, key_path)

        # Configurar cifrados compatibles con iOS
        ssl_context.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
        )

        # Ensure Windows uses the SelectorEventLoop
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        uvicorn.run(
            asgi_app,
            host="0.0.0.0",
            port=8443,
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
            ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS",
            log_level="info",
            log_config=None,
        )
    except Exception as e:
        print(f"Error al iniciar Uvicorn: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    start_server()
