import hashlib
import logging
import os
import secrets
import sys
from datetime import datetime, timedelta

import jwt
import pyodbc
from flask import abort, current_app, jsonify, request
from passlib.hash import pbkdf2_sha256

from config.uGlobalConfig import GConfig
from db.uDB import ConectarDB

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Configurar logging


def rotate_log_file(log_file):
    """Renombra el archivo de log si existe, agregando una marca de tiempo antes de la extensión."""
    if os.path.exists(log_file):
        # Separar el nombre del archivo y la extensión
        base_name, extension = os.path.splitext(log_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_log_file = f"{base_name}{timestamp}.{extension}"
        try:
            os.rename(log_file, new_log_file)
            print(f"Archivo de log renombrado a: {new_log_file}")
        except Exception as e:
            print(f"Error al renombrar el archivo de log: {e}")


def _get_runtime_base_dir() -> str:
    """Base del runtime para archivos editables (config/logs).

    - En .exe (PyInstaller): carpeta del ejecutable
    - En desarrollo: raíz del proyecto (carpeta padre de APIFE/)
    """

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


base_path = _get_runtime_base_dir()
log_dir = os.path.join(base_path, "config")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "api.log")

# Desactivar rotación manual para evitar contención con múltiples procesos

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8", delay=True),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)


# Función para validar el archivo CSV (opcional)
def is_csv(filename):
    return filename.lower().endswith(".csv")


def format_number(number):
    return "{:,.2f}".format(number)


def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        abort(400, description="Formato de fecha inválido. Use 'YYYYMMDD'.")


def get_data_from_database(username):
    conn = ConectarDB()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM usuariosj WHERE username = ?", (username,))
        user_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user_data


def process_database_requests2(request_type):
    conn = None
    cursor = None
    try:
        cedula = request.args.get("cedula", "")
        if not cedula:
            raise ValueError("El parámetro cedula es obligatorio")

        if request_type == "CuentasBalance":
            query = """
            SELECT cliente, nombre, banco, cuenta, Tele, balance, FechaUltimoMovimiento, FechaApertura, Moneda, Cedula
            FROM ListaProductosCliente
            WHERE Cedula = ?
            """
        else:
            raise ValueError("Tipo de solicitud inválido")

        GConfig.cargar(1)
        conn = ConectarDB()
        results = conn.fetch_query(query, (cedula,))
        if not results:
            raise ValueError("No se encontraron resultados")

        # Extract client details from the first row
        cliente_data = {
            "numero_socio": results[0][0],  # Cliente
            "nombre": results[0][1],  # Nombre
            "telefono": results[0][4],  # Telefono (4th index based on the query)
            "cedula": results[0][9],  # Cedula (last column in the query)
        }

        # Function to format dates if they are datetime objects
        def format_date(date_value):
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            return None

        # Group product details
        productos_data = [
            {
                "banco": row[2],  # Banco
                "cuenta": row[3],  # Cuenta
                "balance": row[5],  # Balance
                "fecha_ultimo_movimiento": format_date(row[6]),  # Format if datetime
                "fecha_apertura": format_date(row[7]),  # Format if datetime
                "moneda": row[8],  # Moneda
            }
            for row in results
        ]

        # Final data structure
        data = {"cliente": cliente_data, "productos": productos_data}

        return jsonify(data)

    except pyodbc.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        abort(500, description=f"Error de base de datos: {str(e)}")
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        abort(400, description=str(e))
    except Exception as e:
        logger.error(f"Error del servidor: {str(e)}")
        abort(500, description=f"Error del servidor: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_active_token(username):
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "SELECT token FROM tokenjwt WHERE username = ? AND active = 1"
    token_data = cn1.fetch_query(query, (username,))
    return token_data[0] if token_data else None


def deactivate_old_tokens(username):
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "UPDATE tokenjwt SET active = 0 WHERE username = ?"
    cn1.execute_query(query, (username,))


def save_token(username, token, hour1, min30, min5):
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "INSERT INTO tokenjwt (username, token, active, [1hour], [30min], [5min], creation_time) VALUES (?, ?, 1, ?, ?, ?, GETDATE())"
    cn1.execute_query(query, (username, token, hour1, min30, min5))


def hash_password(password):
    return pbkdf2_sha256.hash(password)


def verify_password(stored_password, provided_password):
    return pbkdf2_sha256.verify(provided_password, stored_password)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def save_api_key(username: str, hashed_key: str, expiry_hours: int = 24):
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "INSERT INTO api_keys (username, hashed_key, expires_at) VALUES (?, ?, ?)"
    cn1.execute_query(query, (username, hashed_key, expires_at))
    logger.info(f"API key creada por el usuario: {username}")


def get_hashed_api_key(hashed_key: str):
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "SELECT username, expires_at FROM api_keys WHERE hashed_key = ?"
    api_key_data = cn1.fetch_query(query, (hashed_key,))

    if not api_key_data:
        return None

    username, expires_at = api_key_data[0]
    if datetime.utcnow() > expires_at:
        return None

    return username


def deactivate_old_api_keys(username: str):
    GConfig.cargar(1)
    cn1 = ConectarDB()
    query = "DELETE FROM api_keys WHERE username = ? AND expires_at < ?"
    cn1.execute_query(query, (username, datetime.utcnow()))


def delete_expired_tokens():
    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()

        # Consolidación de eliminación de tokens
        query = """
        DELETE FROM tokenjwt
        WHERE (creation_time <= DATEADD(hour, -1, GETDATE()) AND [1hour] = 1)
           OR (creation_time <= DATEADD(minute, -30, GETDATE()) AND [30min] = 1)
           OR (creation_time <= DATEADD(minute, -5, GETDATE()) AND [5min] = 1)
        """
        cn1.execute_query(query)

        logger.info("Tokens expirados eliminados")
    except Exception as e:
        logger.error(f"Error eliminando tokens expirados: {str(e)}")
