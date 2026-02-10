import collections
import hashlib
import json
import logging
import os
import secrets
import sys
from datetime import datetime, timedelta

import jwt
import pyodbc
from database import get_db_connection
from flask import Response, abort, current_app, jsonify, request
from passlib.hash import pbkdf2_sha256

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


base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(base_path, "data", "api.log")

# Rotar el archivo de log antes de configurar el logger
rotate_log_file(log_file)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT u.Id, u.EmpresaId, u.username, u.password, u.correo, u.nombre_completo, 
                   u.telefono, u.cedula, u.direccion, u.puesto_trabajo, u.created_at,
                   e.RNC, u.tipo_usuario
            FROM usuariosj u
            LEFT JOIN EmpresaFE e ON u.EmpresaId = e.Id
            WHERE u.username = ?
        """,
            (username,),
        )
        user_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user_data


def get_data_from_database2(rnc):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM EmpresaFE WHERE RNC = ?", (rnc,))
        user_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user_data


def get_data_from_database2_by_id(empresa_id):
    """
    Obtiene datos de una empresa por su ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT Id, RNC, NombreComercial, RazonSocial, Valido, created_at FROM EmpresaFE WHERE Id = ?",
            (empresa_id,),
        )
        empresa_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return empresa_data


from datetime import datetime

import pyodbc
from flask import abort, jsonify, request


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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (cedula,))

        results = cursor.fetchall()
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


import logging
from datetime import datetime

import pyodbc
from flask import abort, jsonify, request

logger = logging.getLogger(__name__)


def process_database_requests3(request_type: str):
    conn = None
    cursor = None
    try:
        fecha_inicio = request.args.get("fecha_inicio", "")
        fecha_fin = request.args.get("fecha_fin", "")
        caja = request.args.get("caja", "TODAS")
        estado_fiscal = request.args.get("estado_fiscal", "TODOS")
        rncemisor = request.args.get("rncemisor", "TODOS")
        tipo_ecf = request.args.get("tipo_ecf", "TODOS")
        order_field = request.args.get("order_field", "FechaEmision")
        order_dir = request.args.get("order_dir", "DESC")

        if not fecha_inicio or not fecha_fin:
            raise ValueError(
                "Los parámetros 'fecha_inicio' y 'fecha_fin' son obligatorios"
            )

        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Las fechas deben tener el formato 'YYYY-MM-DD'")

        if request_type not in ["", "EstadosFiscales"]:
            raise ValueError("Tipo de solicitud inválido")

        query = """
            SELECT TipoVenta, Factura, TipoECF, encf, EstadoFiscal, DescripcionEstadoFiscal, URLC, ResultadoEstadoFiscal, MontoFacturado, ITBISFacturado, MontoDGII, MontoITBISDGII, FechaEmision
            FROM vMonitorSentences
            WHERE CONVERT(date, FechaEmision) BETWEEN ? AND ?
        """
        params = [fecha_inicio_dt, fecha_fin_dt]

        if caja != "TODAS":
            query += " AND caja = ?"
            params.append(caja)

        if estado_fiscal and estado_fiscal != "TODOS":
            query += " AND EstadoFiscal = ?"
            params.append(estado_fiscal)

        if rncemisor and rncemisor != "TODOS":
            query += " AND rncemisor = ?"
            params.append(rncemisor)

        if tipo_ecf and tipo_ecf != "TODOS":
            query += " AND TipoECF = ?"
            params.append(tipo_ecf)

        if order_field not in ("FechaEmision", "Factura"):
            order_field = "FechaEmision"
        if order_dir not in ("ASC", "DESC"):
            order_dir = "DESC"

        query += f" ORDER BY {order_field} {order_dir}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        if not results:
            raise ValueError(
                "No se encontraron resultados para los filtros especificados"
            )

        datos = []
        for row in results:
            # Formatear fecha de emisión
            fecha_emision = row[12]
            if isinstance(fecha_emision, datetime):
                fecha_emision_str = fecha_emision.strftime("%Y-%m-%d")
            else:
                fecha_emision_str = str(fecha_emision) if fecha_emision else ""

            datos.append(
                {
                    "tipo_venta": str(row[0]).strip(),
                    "factura": str(row[1]).strip(),
                    "tipo_ecf": str(row[2]).strip(),
                    "encf": str(row[3]).strip(),
                    "estado_fiscal": row[4],
                    "descripcion_estado_fiscal": str(row[5]).strip(),
                    "urlc": str(row[6]).strip(),
                    "resultado_estado_fiscal": str(row[7] or "").strip(),
                    "monto_facturado": format_number(row[8] or 0.00),
                    "itbis_facturado": format_number(row[9] or 0.00),
                    "monto_dgii": format_number(row[10] or 0.0000),
                    "monto_itbis_dgii": format_number(row[11] or 0.0000),
                    "fecha_emision": fecha_emision_str,
                }
            )

        # Use json.dumps directly instead of jsonify
        import json

        from flask import Response

        response = Response(
            json.dumps({"resultados": datos}, ensure_ascii=False),
            mimetype="application/json",
        )

        return response
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


def update_estado_fiscal():
    conn = None
    cursor = None
    try:
        rnc = request.args.get("rnc", "").strip()
        ncf = request.args.get("ncf", "").strip()

        if not rnc or not ncf:
            raise ValueError("Los parámetros rnc y ncf son obligatorios")

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE FEEncabezado
            SET estadofiscal = 4
            WHERE RNCEmisor = ? AND eNCF = ?
        """
        cursor.execute(query, (rnc, ncf))
        conn.commit()

        if cursor.rowcount == 0:
            raise ValueError("No se actualizó ningún registro. Verifique el RNC y NCF.")

        response = Response(
            json.dumps({"mensaje": "Actualización exitosa"}, ensure_ascii=False),
            mimetype="application/json",
        )
        return response

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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT token FROM tokenjwt WHERE username = ? AND active = 1", (username,)
        )
        token_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return token_data


def deactivate_old_tokens(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tokenjwt SET active = 0 WHERE username = ?", (username,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def save_token(username, token, hour1, min30, min5):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tokenjwt (username, token, active, [1hour], [30min], [5min], creation_time) VALUES (?, ?, 1, ?, ?, ?, GETDATE())",
            (username, token, hour1, min30, min5),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def hash_password(password):
    return pbkdf2_sha256.hash(password)


def verify_password(stored_password, provided_password):
    return pbkdf2_sha256.verify(provided_password, stored_password)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def save_api_key(username: str, hashed_key: str, expiry_hours: int = 24):
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO api_keys (username, hashed_key, expires_at) VALUES (?, ?, ?)",
            (username, hashed_key, expires_at),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    logger.info(f"API key creada por el usuario: {username}")


def get_hashed_api_key(hashed_key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, expires_at FROM api_keys WHERE hashed_key = ?",
            (hashed_key,),
        )
        api_key_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not api_key_data:
        return None

    username, expires_at = api_key_data
    if datetime.utcnow() > expires_at:
        return None

    return username


def deactivate_old_api_keys(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM api_keys WHERE username = ? AND expires_at < ?",
            (username, datetime.utcnow()),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def delete_expired_tokens():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consolidación de eliminación de tokens
        cursor.execute(
            """
        DELETE FROM tokenjwt
        WHERE (creation_time <= DATEADD(hour, -1, GETDATE()) AND [1hour] = 1)
           OR (creation_time <= DATEADD(minute, -30, GETDATE()) AND [30min] = 1)
           OR (creation_time <= DATEADD(minute, -5, GETDATE()) AND [5min] = 1)
        """
        )
        conn.commit()

        logger.info(f"Tokens eliminados: {cursor.rowcount}")
    except Exception as e:
        logger.error(f"Error eliminando tokens expirados: {str(e)}")
    finally:
        cursor.close()
        conn.close()
