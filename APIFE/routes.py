import functools
import hashlib
import json
import os
import secrets
import sys
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta

import jwt
import pyodbc
from api import (
    deactivate_old_api_keys,
    deactivate_old_tokens,
    get_active_token,
    get_data_from_database,
    get_hashed_api_key,
    hash_password,
    logger,
    process_database_requests2,
    save_api_key,
    save_token,
    verify_password,
)
from flask import Blueprint  # pyright: ignore[reportUndefinedVariable]
from flask import Response, current_app, jsonify, request
from flask_cors import cross_origin  # pyright: ignore[reportUndefinedVariable]

from config.uGlobalConfig import *  # noqa: F403,E402
from config.uGlobalConfig import GConfig  # pyright: ignore[reportUndefinedVariable]
from db.database import *  # noqa: F403,E402
from db.uDB import ConectarDB  # noqa: E402
from fm.FImport import CSVImportMapper  # noqa: E402
from glib.log_g import log_event  # noqa: E402
from glib.ufe import ConsultaECF, EnvioDGII, GenerarYFirmar  # noqa: E402
from glib.uGlobalLib import validar_encf  # noqa: E402
from glib.uGlobalLib import rellenaceros, validar_formato_rnc

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# from glib2.uXMLGlobalLib import *


routes = Blueprint("routes", __name__)


def cargar_configuracion_api():
    # Ruta del ejecutable o script
    if hasattr(sys, "_MEIPASS"):
        # Cuando es .exe, buscar primero junto al ejecutable
        exe_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_dir, "config", "api.json")

        # Si no existe junto al .exe, buscar en la carpeta temporal empaquetada
        if not os.path.exists(config_path):
            config_path = os.path.join(sys._MEIPASS, "config", "api.json")
    else:
        # En desarrollo, buscar en la carpeta padre donde está config/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "config", "api.json")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


config = cargar_configuracion_api()


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


# Helpers de rendimiento
@functools.lru_cache(maxsize=1)
def _get_api_level_route() -> int:
    # Ruta base del ejecutable o del script
    """base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    base_path = os.path.dirname(base_path)

    # Ruta del archivo cn.ini
    config_path = os.path.join(base_path, "config", "api.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return int(config.get("level_route_csv1", 1))"""
    try:
        return int(config.get("level_route_csv1", 1))
    except Exception as e:
        log_event(
            logger, "error", f"No se pudo cargar api.json: {str(e)}"
        )  # pyright: ignore[reportUndefinedVariable]
        return 1


def token_or_api_key_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        api_key = request.headers.get("x-api-key")

        if not token and not api_key:
            return (
                jsonify({"message": "Authorization token or API key is required"}),
                401,
            )

        if token:
            try:
                token = token.split(" ")[1]
                payload = jwt.decode(
                    token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
                )
                username = payload["username"]
                active_token = get_active_token(username)
                if not active_token or active_token[0] != token:
                    return jsonify({"message": "Invalid or inactive token"}), 401
                log_event(
                    logger, "info", f"Token utilizado por el usuario: {username}"
                )  # pyright: ignore[reportUndefinedVariable]
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token"}), 401
        elif api_key:
            hashed_key = hash_api_key(api_key)
            username = get_hashed_api_key(hashed_key)
            if not username:
                return jsonify({"message": "Invalid or expired API key"}), 401
            log_event(
                logger, "info", f"API Key utilizada por el usuario: {username}"
            )  # pyright: ignore[reportUndefinedVariable]

        return f(*args, **kwargs)

    return decorated_function


@cross_origin
@routes.route("/CB", methods=["GET"])
# @token_or_api_key_required
def CuentasBalance():
    log_event(
        logger, "info", "Acceso a CuentasBalance con autorización válida"
    )  # pyright: ignore[reportUndefinedVariable]
    return process_database_requests2("CuentasBalance")


@routes.route("/")
def home():
    return "404 no found!"


@routes.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    existing_user = get_data_from_database(username)
    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    hashed_password = hash_password(password)

    try:
        conn = ConectarDB()  # pyright: ignore[reportUndefinedVariable]
        cursor = conn.cursor()

        # Insert the new user into the database
        cursor.execute(
            "INSERT INTO usuariosj (username, password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()

    except pyodbc.IntegrityError:
        return jsonify({"message": "A user with this username already exists."}), 400
    except Exception as e:  # noqa: F841
        return (
            jsonify({"message": "An error occurred while registering the user."}),
            500,
        )
    finally:
        cursor.close()
        conn.close()

    log_event(
        logger, "info", f"Nuevo usuario registrado: {username}"
    )  # pyright: ignore[reportUndefinedVariable]
    return jsonify({"message": "User registered successfully"}), 201


@routes.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user_data = get_data_from_database(username)
    if user_data is None:
        return jsonify({"message": "Invalid username or password"}), 401

    if not verify_password(user_data[1], password):
        return jsonify({"message": "Invalid username or password"}), 401

    deactivate_old_tokens(username)

    hour1 = data.get("1hour", 0)
    min30 = data.get("30min", 0)
    min5 = data.get("5min", 0)

    expiration_time = None
    if hour1:
        expiration_time = datetime.utcnow() + timedelta(hours=1)
    elif min30:
        expiration_time = datetime.utcnow() + timedelta(minutes=30)
    elif min5:
        expiration_time = datetime.utcnow() + timedelta(minutes=5)

    token_data = {"username": username}
    if expiration_time:
        token_data["exp"] = int(expiration_time.timestamp())

    token = jwt.encode(token_data, current_app.config["SECRET_KEY"], algorithm="HS256")
    save_token(username, token, hour1, min30, min5)

    log_event(
        logger, "info", f"Usuario {username} inició sesión y se generó un token."
    )  # pyright: ignore[reportUndefinedVariable]
    return jsonify({"token": token})


@routes.route("/generate-api-key", methods=["POST"])
@token_or_api_key_required
def generate_api_key():
    token = request.headers.get("Authorization").split(" ")[1]
    payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    username = payload["username"]

    deactivate_old_api_keys(username)

    raw_key = secrets.token_urlsafe(64)

    hashed_key = hash_api_key(raw_key)

    save_api_key(username, hashed_key, expiry_hours=730)

    log_event(
        logger, "info", f"API Key generada para el usuario: {username}"
    )  # pyright: ignore[reportUndefinedVariable]
    return jsonify({"api_key": raw_key})


@routes.route("/data", methods=["GET"])
@token_or_api_key_required
def protected_data():
    api_key = request.headers.get("x-api-key")

    if api_key:
        hashed_key = hash_api_key(api_key)
        username = get_hashed_api_key(hashed_key)

        if not username:
            return jsonify({"message": "Invalid or expired API key"}), 401

        log_event(  # pyright: ignore[reportUndefinedVariable]
            logger,
            "info",
            f"Acceso a datos protegido utilizando API Key por el usuario: {username}",
        )

    user_data = get_data_from_database(username)

    return jsonify({"username": user_data[0], "additional_data": user_data[1]})


@routes.route("/upload-csv", methods=["POST"])
@cross_origin()
# @token_or_api_key_required
def upload_csv():
    # Cargar configuración desde api.json
    try:
        """config_path = os.path.join(os.path.dirname(__file__), "config", "api.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            level_route_csv1 = config.get(
                "level_route_csv1", 1
            )  # Usa 1 como valor predeterminado"""
        level_route_csv1 = config.get(
            "level_route_csv1", 1
        )  # Usa 1 como valor predeterminado"""
    except Exception as e:
        logger.error(f"Error al cargar api.json: {str(e)}")
        level_route_csv1 = 1  # Valor predeterminado si hay error

    level_route_csv = level_route_csv1
    # Verifica si el RNC está en la solicitud
    rnc = request.form.get(
        "rnc"
    )  # Asegúrate de que el RNC sea enviado como parte del formulario
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    # Get ENCF from request
    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    valido, mensaje = validar_encf(encf)  # pyright: ignore[reportUndefinedVariable]
    if not valido:
        return (jsonify({"codigo": "42", "message": mensaje}), 400)

    # Valida el RNC (opcional, puedes agregar validaciones más estrictas)
    if not rnc.isdigit() or not validar_formato_rnc(
        rnc
    ):  # pyright: ignore[reportUndefinedVariable]
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales.",
                }
            ),
            400,
        )

    if "file" not in request.files:
        return jsonify({"codigo": "44", "message": "No ha enviado archivo CSV."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"codigo": "44", "message": "No ha enviado archivo."}), 400

    # Verifica que el archivo sea un CSV
    if not file.filename.endswith(".csv"):
        return (
            jsonify(
                {
                    "codigo": "45",
                    "message": "Solo son permitidos archivos con formato CSV.",
                }
            ),
            400,
        )

    rncs = rnc.strip()
    encfs = encf.strip()

    try:
        # Verificar si el ENCF ya existe en la base de datos
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        query = f"Select * from vFEEncabezado with (nolock) where rncemisor = '{rncs.strip()}' and encf = '{encfs.strip()}'"
        vFEEncabezado = cn1.fetch_query(query)

        # Verificar si se encontraron resultados
        if vFEEncabezado and len(vFEEncabezado) > 0:
            if vFEEncabezado[0].EstadoFiscal in [1, 2, 3, 4, 5, 6, 99]:
                m = f"El ENCF {encf.strip()} Ya existe y tiene guardado el siguiente mensaje {vFEEncabezado[0].ResultadoEstadoFiscal}"
                log_event(logger, "info", m)  # pyright: ignore[reportUndefinedVariable]
                response_data = OrderedDict(
                    [
                        ("codigo", "46"),
                        ("message", m),
                    ]
                )

                # CORREGIDO: Return solo con Response y status code apropiado
                return Response(
                    json.dumps(response_data),
                    status=409,  # Conflict - más apropiado que 500
                    mimetype="application/json",
                )
            else:
                # Solo ejecutar respaldo si el estado fiscal NO está en [1,2,3,4,5,6,99]
                log_event(  # pyright: ignore[reportUndefinedVariable]
                    logger,
                    "info",
                    f"Estado fiscal {vFEEncabezado[0].EstadoFiscal} permite respaldo para RNC {rncs}, ENCF {encfs}",
                )

                # Respaldar datos importantes en tablas RV antes de borrar
                respaldo_encabezado = f"""
                    INSERT INTO FEEncabezadoRV (
                        TipoECF, eNCF, EstadoFiscal, ResultadoEstadoFiscal, NCFModificado,
                        FechaNCFModificado, CodigoModificacion, RNCEmisor, RazonSocialEmisor,
                        FechaEmision, RNCComprador, RazonSocialComprador, MontoGravadoTotal,
                        MontoGravadoI1, MontoExento, TotalITBIS, TotalITBIS1, MontoTotal,
                        CodigoSeguridad, TrackID, URLQR
                    )
                    SELECT
                        TipoECF, eNCF, EstadoFiscal, ResultadoEstadoFiscal, NCFModificado,
                        FechaNCFModificado, CodigoModificacion, RNCEmisor, RazonSocialEmisor,
                        FechaEmision, RNCComprador, RazonSocialComprador, MontoGravadoTotal,
                        MontoGravadoI1, MontoExento, TotalITBIS, TotalITBIS1, MontoTotal,
                        CodigoSeguridad, TrackID, URLQR
                    FROM FEEncabezado
                    WHERE RNCEmisor = '{rncs}' AND ENCF = '{encfs}'
                """

                respaldo_detalle = f"""
                    INSERT INTO FEDetalleRV (RNCEmisor, TipoECF, NombreItem, CantidadItem, MontoItem)
                    SELECT RNCEmisor, TipoECF, NombreItem, CantidadItem, MontoItem
                    FROM FEDetalle
                    WHERE RNCEmisor = '{rncs}' AND ENCF = '{encfs}'
                """

                cn1.execute_query(respaldo_encabezado)
                cn1.execute_query(respaldo_detalle)
                log_event(  # pyright: ignore[reportUndefinedVariable]
                    logger,
                    "info",
                    f"Se respaldaron los datos de FEEncabezado y FEDetalle en las tablas RV para RNC {rncs}, ENCF {encfs}",
                )

                # Eliminar los datos originales
                delete_detalle = f"""
                    DELETE FROM FEDetalle
                    WHERE RNCEmisor = '{rncs}' AND ENCF = '{encfs}'
                """
                delete_encabezado = f"""
                    DELETE FROM FEEncabezado
                    WHERE RNCEmisor = '{rncs}' AND ENCF = '{encfs}'
                """
                cn1.execute_query(delete_detalle)
                cn1.execute_query(delete_encabezado)
                log_event(  # pyright: ignore[reportUndefinedVariable]
                    logger,
                    "info",
                    f"Se eliminaron los datos originales de FEEncabezado y FEDetalle para RNC {rncs}, ENCF {encfs}",
                )
        else:
            # Si no existe el registro, proceder normalmente (crear nuevo)
            log_event(  # pyright: ignore[reportUndefinedVariable]
                logger,
                "info",
                f"No se encontró registro existente para RNC {rncs}, ENCF {encfs}. Procediendo con nuevo registro.",
            )

        # Create directory for RNC if it doesn't exist
        rnc_directory = os.path.join(current_app.config["UPLOAD_FOLDER"], rnc)
        if not os.path.exists(rnc_directory):
            os.makedirs(rnc_directory)

        # Create filename using RNC and ENCF
        filename = f"{rnc}_{encf}.csv"
        filepath = os.path.join(rnc_directory, filename)

        # Save file in the RNC directory
        file.save(filepath)

        ############################################################################################################################
        # Procesar el archivo CSV después de guardarlo
        # Paso 1

        mapper = CSVImportMapper(
            "fm/datadefCarga.json", cn1
        )  # pyright: ignore[reportUndefinedVariable]
        encabezado_count, detalle_count = mapper.process_and_insert(filepath)
        query = f"Update feencabezado set EstadoFiscal = 1 , ResultadoEstadoFiscal= 'Listo para procesar.' where  rncemisor = '{rnc}' and encf = '{encf}'"
        cn1.execute_query(query)

        log_event(  # pyright: ignore[reportUndefinedVariable]
            logger,
            "info",
            f"Archivo CSV subido exitosamente: {filename} por RNC: {rnc}, ENCF: {encf}",
        )
        log_event(  # pyright: ignore[reportUndefinedVariable]
            logger,
            "info",
            f"Procesados {encabezado_count} registros de encabezado y {detalle_count} registros de detalle",
        )

        if level_route_csv == 1:
            response_data = OrderedDict(
                [
                    ("codigo", "01"),
                    ("message", "Archivo CSV subido exitosamente."),
                    ("encabezado_count", encabezado_count),
                    ("detalle_count", detalle_count),
                ]
            )
            return Response(
                json.dumps(response_data), status=201, mimetype="application/json"
            )

        ############################################################################################################################
        # Generar y firmar XML
        # Paso 2
        query = f"Select *  from vFEEncabezado with (nolock) where  rncemisor = '{rncs.strip()}' and encf = '{encfs.strip()}'"
        vFEEncabezado = cn1.fetch_query(query)
        EstadoFiscal, Mensaje = GenerarYFirmar(
            cn1, vFEEncabezado[0]
        )  # pyright: ignore[reportUndefinedVariable]

        query = f"Select *  from vFEEncabezado with (nolock) where  rncemisor = '{rncs.strip()}' and encf = '{encfs.strip()}'"
        vFEEncabezado = cn1.fetch_query(query)

        if EstadoFiscal != "03":
            log_event(
                logger, "info", f"{EstadoFiscal}'-'{Mensaje}"
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": str(EstadoFiscal), "message": Mensaje}), 500

        if level_route_csv == 2:
            response_data = OrderedDict(
                [
                    (
                        "codigo",
                        rellenaceros(EstadoFiscal if EstadoFiscal != 3 else 5),
                    ),  # pyright: ignore[reportUndefinedVariable]
                    ("message", Mensaje if EstadoFiscal != 3 else "Aceptado"),
                    ("CodigoSeguridad", vFEEncabezado[0].CodigoSeguridad),
                    ("FechayHoradeFirma", vFEEncabezado[0].FechaFirma),
                    ("URLQR", vFEEncabezado[0].URLQR),
                ]
            )
            return Response(
                json.dumps(response_data), status=201, mimetype="application/json"
            )

        ############################################################################################################################
        # Envio a la DGII
        # Estas rutas se cailculan porque el archivo que se envia es solo el resumen el el caso de las 32 con menos de 250,000
        # Paso 3

        # Respuesta si todo fue procesado satisfactoriamente
        query = f"Select *  from vFEEncabezado with (nolock) where  rncemisor = '{rncs.strip()}' and encf = '{encfs.strip()}'"
        vFEEncabezado = cn1.fetch_query(query)

        EstadoFiscal, Mensaje = EnvioDGII(
            cn1, vFEEncabezado[0]
        )  # pyright: ignore[reportUndefinedVariable]
        if rellenaceros(EstadoFiscal) not in [
            "05",
            "06",
        ]:  # pyright: ignore[reportUndefinedVariable]
            log_event(
                logger, "info", f"{rellenaceros(EstadoFiscal)}'-'{Mensaje}"
            )  # pyright: ignore[reportUndefinedVariable]  # pyright: ignore[reportUndefinedVariable]
            return (
                jsonify(
                    {"codigo": rellenaceros(EstadoFiscal), "message": Mensaje}
                ),  # pyright: ignore[reportUndefinedVariable]
                500,
            )

        if level_route_csv == 3:
            response_data = OrderedDict(
                [
                    (
                        "codigo",
                        rellenaceros(EstadoFiscal),
                    ),  # pyright: ignore[reportUndefinedVariable]
                    ("message", Mensaje),
                    ("CodigoSeguridad", vFEEncabezado[0].CodigoSeguridad),
                    ("FechayHoradeFirma", vFEEncabezado[0].FechaFirma),
                    ("URLQR", vFEEncabezado[0].URLQR),
                ]
            )

            return Response(
                json.dumps(response_data), status=201, mimetype="application/json"
            )

        # Fin de Envio a la DGII

    except Exception as e:
        logger.error(f"Error al procesar el archivo: {str(e)}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar el archivo: {str(e)}",
                }
            ),
            500,
        )


@routes.route("/FGE", methods=["POST"])
@cross_origin()
# @token_or_api_key_required
def process_FGE():
    # Config: usar caché para evitar I/O por petición
    try:
        level_route_csv = _get_api_level_route()
    except Exception:
        level_route_csv = 1

    # Modo 1: Inactivo - No procesar
    if level_route_csv == 1:
        return (
            jsonify(
                {"codigo": "-1", "message": "Modo inactivo puesto por el desarrollador"}
            ),
            200,
        )

    # Verifica si el RNC está en la solicitud
    rnc = request.form.get(
        "rnc"
    )  # Asegúrate de que el RNC sea enviado como parte del formulario
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    # Get ENCF from request
    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    # Valida el RNC (opcional, puedes agregar validaciones más estrictas)
    if not rnc.isdigit():
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales..",
                }
            ),
            400,
        )

    try:
        # Preparación de DB
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        rncs = rnc.strip()
        encfs = encf.strip()

        # Obtener encabezado una sola vez
        vFEEncabezado = cn1._get_encabezado(rncs, encfs)
        if not vFEEncabezado:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} no se encuentra la base de datos."
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "57", "message": mensaje}), 409

        encabezado = vFEEncabezado[0]

        # Salida temprana si ya fue procesado
        if getattr(encabezado, "EstadoFiscal", 0) >= 3:
            mensaje = f"El ENCF {encfs} ya ha sido procesado para el RNC {rncs}"
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "58", "message": mensaje}), 409

        # Validar que el estado fiscal sea mayor que 0
        estado_fiscal = getattr(encabezado, "EstadoFiscal", 0)
        if estado_fiscal <= 0:
            mensaje = f"El estado fiscal debe ser mayor que 0 para proceder con el proceso. Estado actual: {estado_fiscal}"
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "59", "message": mensaje}), 400

        # Paso 2: Generar y Firmar
        EstadoFiscal, Mensaje = GenerarYFirmar(
            cn1, encabezado
        )  # pyright: ignore[reportUndefinedVariable]
        if str(EstadoFiscal) != "03":
            log_event(
                logger, "info", f"{EstadoFiscal}'-'{Mensaje}"
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": str(EstadoFiscal), "message": Mensaje}), 500

        # Refrescar datos solo si se van a retornar en nivel 2 o 3
        if level_route_csv in (2, 3):
            vFEEncabezado = cn1._get_encabezado(rncs, encfs)
            if not vFEEncabezado:
                return (
                    jsonify(
                        {
                            "codigo": "08",
                            "message": "Encabezado no disponible tras firmar.",
                        }
                    ),
                    409,
                )
            vFEEncabezado = cn1._get_encabezado(rncs, encfs)
            encabezado = vFEEncabezado[0]

        if level_route_csv == 2:
            response_data = OrderedDict(
                [
                    (
                        "codigo",
                        rellenaceros(EstadoFiscal if EstadoFiscal != 3 else 5),
                    ),  # pyright: ignore[reportUndefinedVariable]
                    ("message", Mensaje if EstadoFiscal != 3 else "Aceptado"),
                    ("CodigoSeguridad", getattr(encabezado, "CodigoSeguridad", None)),
                    ("FechayHoradeFirma", getattr(encabezado, "FechaFirma", None)),
                    ("URLQR", getattr(encabezado, "URLQR", None)),
                ]
            )
            return Response(
                json.dumps(response_data), status=201, mimetype="application/json"
            )

        # Paso 3: Envío DGII
        vFEEncabezado = cn1._get_encabezado(rncs, encfs)
        encabezado = vFEEncabezado[0]
        EstadoFiscal, Mensaje = EnvioDGII(
            cn1, encabezado
        )  # pyright: ignore[reportUndefinedVariable]
        if rellenaceros(EstadoFiscal) not in [
            "05",
            "06",
        ]:  # pyright: ignore[reportUndefinedVariable]
            log_event(
                logger, "info", f"{rellenaceros(EstadoFiscal)}'-'{Mensaje}"
            )  # pyright: ignore[reportUndefinedVariable]  # pyright: ignore[reportUndefinedVariable]
            return (
                jsonify(
                    {"codigo": rellenaceros(EstadoFiscal), "message": Mensaje}
                ),  # pyright: ignore[reportUndefinedVariable]
                500,
            )

        if level_route_csv == 3:
            response_data = OrderedDict(
                [
                    (
                        "codigo",
                        rellenaceros(EstadoFiscal),
                    ),  # pyright: ignore[reportUndefinedVariable]
                    ("message", Mensaje),
                    ("CodigoSeguridad", getattr(encabezado, "CodigoSeguridad", None)),
                    ("FechayHoradeFirma", getattr(encabezado, "FechaFirma", None)),
                    ("URLQR", getattr(encabezado, "URLQR", None)),
                ]
            )
            return Response(
                json.dumps(response_data), status=201, mimetype="application/json"
            )

        # Fin

    except Exception as e:
        logger.error(f"Error al procesar el archivo: {str(e)}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido: {str(e)}",
                }
            ),
            500,
        )


@routes.route(
    "/GenerarYFirmar", methods=["POST"]
)  # pyright: ignore[reportUndefinedVariable]
@cross_origin()
# @token_or_api_key_required
def process_GenerarYFirmar():  # pyright: ignore[reportUndefinedVariable]
    rnc = request.form.get("rnc")
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    if not rnc.isdigit():
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales.",
                }
            ),
            400,
        )

    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        rncs = rnc.strip()
        encfs = encf.strip()

        query = f"SELECT * FROM vfeencabezado WITH (NOLOCK) WHERE rncemisor = '{rncs}' AND encf = '{encfs}'"
        vFEEncabezado = cn1.fetch_query(query)

        if not vFEEncabezado:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} no se encuentra en la base de datos."
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "57", "message": mensaje}), 409

        # Validar que el estado fiscal permita generar firma
        # Estados permitidos: 0, 1, 2, 40, 41, 42, 43, 47, 48, 50, 53, 70
        ESTADOS_PERMITIDOS_GENERAR_FIRMA = [0, 1, 2, 40, 41, 42, 43, 47, 48, 50, 53, 70]
        estado_actual = vFEEncabezado[0].EstadoFiscal

        if estado_actual not in ESTADOS_PERMITIDOS_GENERAR_FIRMA:
            mensaje = f"El comprobante en estado fiscal {estado_actual} no puede generar firma. Estados permitidos: {ESTADOS_PERMITIDOS_GENERAR_FIRMA}"
            log_event(
                logger, "warning", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "59", "message": mensaje}), 422

        # Revisar si ya fue procesado (validación legacy - mantener para compatibilidad)
        if (
            vFEEncabezado[0].EstadoFiscal >= 3
            and estado_actual not in ESTADOS_PERMITIDOS_GENERAR_FIRMA
        ):
            mensaje = f"El ENCF {encfs} ya ha sido procesado para el RNC {rncs}"
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "58", "message": mensaje}), 409

        ################################################################################################
        # SOLO Generar y firmar XML
        resultado = GenerarYFirmar(
            cn1, vFEEncabezado[0]
        )  # pyright: ignore[reportUndefinedVariable]
        if (
            resultado is None
            or not isinstance(resultado, (list, tuple))
            or len(resultado) != 2
        ):
            mensaje = "Error interno al generar y firmar el comprobante."
            logger.error(mensaje)
            return jsonify({"codigo": "00", "message": mensaje}), 500

        EstadoFiscal, Mensaje = resultado

        query = f"SELECT * FROM vFEEncabezado WITH (NOLOCK) WHERE rncemisor = '{rncs}' AND encf = '{encfs}'"
        vFEEncabezado = cn1.fetch_query(query)
        if not vFEEncabezado or vFEEncabezado[0] is None:
            mensaje = (
                f"No se encontró el ENCF {encfs} para el RNC {rncs} después de firmar."
            )
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "08", "message": mensaje}), 409

        response_data = OrderedDict(
            [
                ("codigo", EstadoFiscal),
                ("message", Mensaje),
                ("CodigoSeguridad", vFEEncabezado[0].CodigoSeguridad),
                ("FechayHoradeFirma", vFEEncabezado[0].FechaFirma),
                ("URLQR", vFEEncabezado[0].URLQR),
            ]
        )

        return Response(
            json.dumps(response_data), status=201, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error al procesar el documento: {str(e)}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar el documento: {str(e)}",
                }
            ),
            500,
        )


@routes.route("/EnviarDGII", methods=["POST"])
@cross_origin()
# @token_or_api_key_required
def process_EnviarDGII():
    rnc = request.form.get("rnc")
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    if not rnc.isdigit():
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales.",
                }
            ),
            400,
        )

    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        rncs = rnc.strip()
        encfs = encf.strip()

        query = f"SELECT * FROM vFEEncabezado WITH (NOLOCK) WHERE rncemisor = '{rncs}' AND encf = '{encfs}'"
        vFEEncabezado = cn1.fetch_query(query)

        if not vFEEncabezado:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} no se encuentra en la base de datos."
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "57", "message": mensaje}), 409

        # Validar que el estado fiscal permita enviar a DGII
        # Estados permitidos: 3, 80
        ESTADOS_PERMITIDOS_ENVIAR_DGII = [3, 80]
        estado_actual = vFEEncabezado[0].EstadoFiscal

        if estado_actual not in ESTADOS_PERMITIDOS_ENVIAR_DGII:
            mensaje = f"El comprobante en estado fiscal {estado_actual} no puede ser enviado a DGII. Estados permitidos: {ESTADOS_PERMITIDOS_ENVIAR_DGII}"
            log_event(
                logger, "warning", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "59", "message": mensaje}), 422

        ################################################################################################
        # SOLO Envío a la DGII
        resultado_envio = EnvioDGII(
            cn1, vFEEncabezado[0]
        )  # pyright: ignore[reportUndefinedVariable]
        if (
            resultado_envio is None
            or not isinstance(resultado_envio, (list, tuple))
            or len(resultado_envio) != 2
        ):
            mensaje = "Error interno al enviar el comprobante a la DGII."
            logger.error(mensaje)
            return jsonify({"codigo": "00", "message": mensaje}), 500

        EstadoFiscal, Mensaje = resultado_envio

        response_data = OrderedDict(
            [
                ("codigo", EstadoFiscal),
                ("message", Mensaje),
                ("CodigoSeguridad", vFEEncabezado[0].CodigoSeguridad),
                ("FechayHoradeFirma", vFEEncabezado[0].FechaFirma),
                ("URLQR", vFEEncabezado[0].URLQR),
            ]
        )

        return Response(
            json.dumps(response_data), status=201, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error al enviar a DGII: {str(e)}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar el envío: {str(e)}",
                }
            ),
            500,
        )


@routes.route("/ConsultaDGII", methods=["POST"])
@cross_origin()
# @token_or_api_key_required
def process_ConsultaDGII():
    rnc = request.form.get("rnc")
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    if not rnc.isdigit():
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales.",
                }
            ),
            400,
        )

    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        rncs = rnc.strip()
        encfs = encf.strip()

        # Consulta consistente con FEConsultaEstadoECF.py
        query = f"""
            SELECT TOP 1 *
            FROM vFEEncabezado WITH (NOLOCK)
            WHERE rncemisor = '{rncs}'
            AND encf = '{encfs}'
            AND TipoECFL = 'E'
            ORDER BY FechaCreacion
        """
        vFEEncabezado = cn1.fetch_query(query)

        if not vFEEncabezado:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} no se encuentra en la base de datos."
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "57", "message": mensaje}), 409

        # Validar que el estado fiscal permita consultar en DGII
        # Estados permitidos: 0, 2, 3, 4, 5, 6, 46, 47, 49, 50, 53, 70, 80, 99
        ESTADOS_PERMITIDOS_CONSULTAR_DGII = [
            0,
            2,
            3,
            4,
            5,
            6,
            46,
            47,
            49,
            50,
            53,
            70,
            80,
            99,
        ]
        estado_actual = vFEEncabezado[0].EstadoFiscal

        if estado_actual not in ESTADOS_PERMITIDOS_CONSULTAR_DGII:
            mensaje = f"El comprobante en estado fiscal {estado_actual} no puede ser consultado en DGII. Estados permitidos: {ESTADOS_PERMITIDOS_CONSULTAR_DGII}"
            log_event(
                logger, "warning", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "59", "message": mensaje}), 422

        ################################################################################################
        # Solo Consulta a la DGII
        resultado_envio = ConsultaECF(
            cn1, vFEEncabezado[0]
        )  # pyright: ignore[reportUndefinedVariable]
        if (
            resultado_envio is None
            or not isinstance(resultado_envio, (list, tuple))
            or len(resultado_envio) != 2
        ):
            mensaje = "Error interno al consultar el comprobante a la DGII."
            logger.error(mensaje)
            return jsonify({"codigo": "00", "message": mensaje}), 500

        EstadoFiscal, Mensaje = resultado_envio

        response_data = OrderedDict(
            [
                ("codigo", EstadoFiscal),
                ("message", Mensaje),
                ("CodigoSeguridad", vFEEncabezado[0].CodigoSeguridad),
                ("FechayHoradeFirma", vFEEncabezado[0].FechaFirma),
                ("URLQR", vFEEncabezado[0].URLQR),
            ]
        )

        return Response(
            json.dumps(response_data), status=201, mimetype="application/json"
        )

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error al enviar a DGII: {str(e)}\n{tb}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar el envío: {str(e)}",
                    "traceback": tb,  # cuidado con exponer esto en producción
                }
            ),
            500,
        )


@routes.route("/SustituirNCFDGII", methods=["POST"])
@cross_origin()
# @token_or_api_key_required
def process_SustituirNCFDGII():
    rnc = request.form.get("rnc")
    if not rnc:
        return (
            jsonify({"codigo": "40", "message": "El RNC del emisor es requerido."}),
            400,
        )

    encf = request.form.get("encf")
    if not encf:
        return (
            jsonify({"codigo": "41", "message": "El eNCF emitido es requerido."}),
            400,
        )

    tabla = request.form.get("tabla")
    campo = request.form.get("campo")

    if not rnc.isdigit():
        return (
            jsonify(
                {
                    "codigo": "43",
                    "message": "El formato del RNC es inválido. Por favor, envíe solo números, sin guiones ni caracteres especiales.",
                }
            ),
            400,
        )

    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()  # pyright: ignore[reportUndefinedVariable]

        rncs = rnc.strip()
        encfs = encf.strip()

        # Primero verificar el estado fiscal del comprobante
        query = f"SELECT * FROM vFEEncabezado WITH (NOLOCK) WHERE rncemisor = '{rncs}' AND encf = '{encfs}'"
        vFEEncabezado = cn1.fetch_query(query)

        if not vFEEncabezado:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} no se encuentra en la base de datos."
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "57", "message": mensaje}), 409

        # Validar que el estado fiscal permita sustituir NCF
        # Solo estados 99 pueden ser sustituidos
        ESTADOS_PERMITIDOS_SUSTITUIR = [99]
        estado_actual = vFEEncabezado[0].EstadoFiscal

        if estado_actual not in ESTADOS_PERMITIDOS_SUSTITUIR:
            mensaje = f"Solo los comprobantes en estado fiscal 99 pueden ser sustituidos. Estado actual: {estado_actual}"
            log_event(
                logger, "warning", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "59", "message": mensaje}), 422

        tablas = tabla.strip() if tabla else ""  # noqa: F841
        campos = campo.strip() if campo else ""  # noqa: F841

        ################################################################################################
        # Sustitucion de NCF rechazados

        if not cn1.ejecutar_sustitucion_ncf(tabla, campo, rnc, encf):
            mensaje = (
                f"El ENCF {encfs} especificado para RNC {rncs} no pudo ser sustituido."
            )
            log_event(
                logger, "info", mensaje
            )  # pyright: ignore[reportUndefinedVariable]
            return jsonify({"codigo": "00", "message": mensaje}), 409
        else:
            mensaje = f"El ENCF {encfs} especificado para RNC {rncs} fue sustituido con éxito."
            response_data = OrderedDict([("resultado", "01"), ("message", mensaje)])

        return Response(
            json.dumps(response_data), status=201, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error al sustituir NCF: {str(e)}")
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar la sustitución: {str(e)}",
                }
            ),
            500,
        )
        return (
            jsonify(
                {
                    "codigo": "00",
                    "message": f"Un error ha ocurrido al procesar el envío: {str(e)}",
                }
            ),
            500,
        )
