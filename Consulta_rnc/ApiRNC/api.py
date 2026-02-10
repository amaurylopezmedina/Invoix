import asyncio
import hashlib
import logging
import os
import secrets
import sys
from datetime import datetime, timedelta

import jwt
import pyodbc
from database import get_db_connection
from flask import abort, current_app, jsonify, request
from passlib.hash import pbkdf2_sha256

# Configurar logging

base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(base_path, "data", "api.log")

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


from datetime import datetime

import pyodbc
from flask import abort, jsonify, request


async def process_database_requests2(request_type):
    rnc = request.args.get("rnc", "").strip()
    if not rnc:
        abort(400, description="El parámetro RNC es obligatorio")

    if request_type != "RNCInfo":
        abort(400, description="Tipo de solicitud inválido")

    query = """
    SELECT rnc, nombre, ncomercial, actividad, representante, numero, dire, tele, fecharegistro, estado, regimenpago
    FROM DGII_RNC WITH (NOLOCK)
    WHERE rnc = ?
    """

    def run_query():
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, (rnc,))
            return cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    try:
        row = await asyncio.to_thread(run_query)
    except pyodbc.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        abort(500, description="Error de base de datos")
    except Exception as e:
        logger.error(f"Error del servidor: {str(e)}")
        abort(500, description="Error del servidor")

    if not row:
        abort(404, description="No se encontraron resultados para el RNC proporcionado")

    empresa_data = {
        "rnc": row[0].strip() if isinstance(row[0], str) else row[0],
        "nombre": row[1].strip() if isinstance(row[1], str) else row[1],
        "nombre_comercial": row[2].strip() if isinstance(row[2], str) else row[2],
        "actividad": row[3].strip() if isinstance(row[3], str) else row[3],
        "representante": row[4].strip() if isinstance(row[4], str) else row[4],
        "numero": row[5].strip() if isinstance(row[5], str) else row[5],
        "direccion": row[6].strip() if isinstance(row[6], str) else row[6],
        "telefono": row[7].strip() if isinstance(row[7], str) else row[7],
        "fecha_registro": row[8].strip() if isinstance(row[8], str) else row[8],
        "estado": row[9].strip() if isinstance(row[9], str) else row[9],
        "regimen_pago": row[10].strip() if isinstance(row[10], str) else row[10],
    }

    return jsonify({"empresa": empresa_data})
