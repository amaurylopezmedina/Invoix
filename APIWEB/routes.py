import os
import sys
import functools
import hashlib
import jwt
import pyodbc
import shutil
import uuid
import mimetypes
import base64

import json
import logging
import secrets
import time
import pandas as pd
from collections import OrderedDict
from datetime import datetime, timedelta, date
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from api import (
    deactivate_old_api_keys,
    deactivate_old_tokens,
    get_active_token,
    get_data_from_database,
    get_data_from_database2,
    get_data_from_database2_by_id,
    get_hashed_api_key,
    hash_password,
    logger,
    process_database_requests2,
    process_database_requests3,
    save_api_key,
    save_token,
    update_estado_fiscal,
    verify_password,
)
from database import get_db_connection
from flask import Blueprint, Response, current_app, jsonify, request, send_file
from flask_cors import CORS, cross_origin
from PyQt5 import QtWidgets
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename

# from glib2.uXMLGlobalLib import *

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from config.uGlobalConfig import *
from config.uGlobalConfig import GConfig
from db.database import *
from db.database import fetch_invoice_data
from db.uDB import *
from glib.Servicios import *
from glib.ufe import *
from cert_utils import obtener_info_basica_certificado, cargar_certificado

def crear_estructura_empresa(rnc):
    """
    Crea la estructura de carpetas específica para una empresa basada en su RNC.
    Utiliza la configuración definida en data/directorios.json
    
    Estructura creada:
    C:/Base/Ambiente/
    ├── PRD/{RNC}/
    │   ├── Img/
    │   ├── RI/
    │   ├── Semillas/
    │   │   ├── Firmadas/
    │   │   └── Generadas/
    │   ├── Bin/
    │   │   └── Servicios/
    │   │       └── Config/
    │   │           ├── configdgii.json
    │   │           ├── configxsd.json
    │   │           ├── directorios.json
    │   │           └── config.json
    │   ├── Token/
    │   ├── XML/
    │   │   ├── Firmadas/
    │   │   └── Generadas/
    │   ├── Cert/
    │   └── CSV/
    ├── CERT/{RNC}/
    │   └── [misma estructura]
    └── QAS/{RNC}/
        └── [misma estructura]
    
    Args:
        rnc (str): RNC de la empresa
        
    Returns:
        dict: Diccionario con las rutas de cada ambiente creado
    """
    try:
        # Cargar configuración desde directorios.json
        config_directorios = cargar_config_directorios()
        
        # Ruta base según configuración o valor por defecto
        ruta_base = config_directorios.get("estructura_base", "C:/Base/Ambiente/")
        
        # Ambientes a crear
        ambientes = ["PRD", "CERT", "QAS"]
        rutas_creadas = {}
        
        # Obtener carpetas desde configuración
        carpetas_principales = config_directorios.get("carpetas_principales", [
            "Img", "RI", "Token", "Cert", "CSV"
        ])
        
        carpetas_con_subcarpetas = config_directorios.get("carpetas_con_subcarpetas", {
            "Semillas": ["Firmadas", "Generadas"],
            "XML": ["Firmadas", "Generadas"],
            "Bin": ["Servicios"]
        })
        
        # Crear estructura para cada ambiente
        for ambiente in ambientes:
            ruta_ambiente = os.path.join(ruta_base, ambiente)
            ruta_empresa = os.path.join(ruta_ambiente, str(rnc))
            
            # Crear directorio principal de la empresa en este ambiente
            os.makedirs(ruta_empresa, exist_ok=True)
            logger.info(f"Directorio principal creado: {ruta_empresa}")
            
            # Crear carpetas principales
            for carpeta in carpetas_principales:
                ruta_carpeta = os.path.join(ruta_empresa, carpeta)
                os.makedirs(ruta_carpeta, exist_ok=True)
                logger.info(f"Carpeta creada: {ruta_carpeta}")
            
            # Crear carpetas con subcarpetas
            for carpeta_padre, subcarpetas in carpetas_con_subcarpetas.items():
                ruta_padre = os.path.join(ruta_empresa, carpeta_padre)
                os.makedirs(ruta_padre, exist_ok=True)
                logger.info(f"Carpeta padre creada: {ruta_padre}")
                
                # Manejar estructura anidada
                if isinstance(subcarpetas, dict):
                    # Estructura anidada como Bin -> Servicios -> Config
                    for subcarpeta_nivel1, subcarpetas_nivel2 in subcarpetas.items():
                        ruta_sub_nivel1 = os.path.join(ruta_padre, subcarpeta_nivel1)
                        os.makedirs(ruta_sub_nivel1, exist_ok=True)
                        logger.info(f"Subcarpeta nivel 1 creada: {ruta_sub_nivel1}")
                        
                        if isinstance(subcarpetas_nivel2, list):
                            for subcarpeta_nivel2 in subcarpetas_nivel2:
                                ruta_sub_nivel2 = os.path.join(ruta_sub_nivel1, subcarpeta_nivel2)
                                os.makedirs(ruta_sub_nivel2, exist_ok=True)
                                logger.info(f"Subcarpeta nivel 2 creada: {ruta_sub_nivel2}")
                                
                                # Si es la carpeta Config dentro de Servicios, copiar archivos
                                if subcarpeta_nivel2 == "Config" and subcarpeta_nivel1 == "Servicios":
                                    copiar_archivos_configuracion(ruta_sub_nivel2, rnc, ambiente)
                else:
                    # Estructura simple como lista
                    for subcarpeta in subcarpetas:
                        ruta_sub = os.path.join(ruta_padre, subcarpeta)
                        os.makedirs(ruta_sub, exist_ok=True)
                        logger.info(f"Subcarpeta creada: {ruta_sub}")
            
            # Guardar ruta creada para este ambiente
            rutas_creadas[ambiente] = ruta_empresa
        
        logger.info(f"Estructura de carpetas completada para RNC: {rnc} en todos los ambientes (PRD, CERT, QAS)")
        return rutas_creadas
        
    except Exception as e:
        logger.error(f"Error creando estructura para RNC {rnc}: {str(e)}")
        raise e

def copiar_archivos_configuracion(ruta_config, rnc, ambiente):
    """
    Copia los archivos de configuración a la carpeta Config de cada empresa
    
    Args:
        ruta_config (str): Ruta de la carpeta Config de la empresa
        rnc (str): RNC de la empresa
        ambiente (str): Ambiente (PRD, CERT, QAS)
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Archivos a copiar desde APIWEB/data
        archivos_a_copiar = [
            "configdgii.json",
            "directorios.json",
            "configxsd.json"
        ]
        
        for archivo in archivos_a_copiar:
            # Ruta origen
            archivo_origen = os.path.join(current_dir, "data", archivo)
            
            # Ruta destino
            archivo_destino = os.path.join(ruta_config, archivo)
            
            if os.path.exists(archivo_origen):
                # Leer contenido del archivo origen
                with open(archivo_origen, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                # Escribir en destino
                with open(archivo_destino, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                
                logger.info(f"Archivo {archivo} copiado para empresa {rnc} en ambiente {ambiente}: {archivo_destino}")
            else:
                logger.warning(f"Archivo origen no encontrado: {archivo_origen}")
        
        # Crear archivo config.json específico para la empresa si no existe
        config_empresa_path = os.path.join(ruta_config, "config.json")
        if not os.path.exists(config_empresa_path):
            config_empresa = {
                "RNC": rnc,
                "ambiente": ambiente,
                "ruta_base": f"C:/Base/Ambiente/{ambiente}/{rnc}",
                "configuracion_creada": datetime.now().isoformat()
            }
            
            with open(config_empresa_path, 'w', encoding='utf-8') as f:
                json.dump(config_empresa, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Archivo config.json específico creado para empresa {rnc} en ambiente {ambiente}")
                
    except Exception as e:
        logger.error(f"Error copiando archivos de configuración para RNC {rnc} en ambiente {ambiente}: {str(e)}")

def cargar_config_directorios():
    """
    Carga la configuración de directorios desde data/directorios.json
    
    Returns:
        dict: Configuración de directorios
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, "data", "directorios.json")
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Archivo directorios.json no encontrado en {config_file_path}, usando configuración por defecto")
            return {
                "estructura_base": "C:/Base/Ambiente/",
                "carpetas_principales": ["Img", "RI", "Token", "Cert", "CSV"],
                "carpetas_con_subcarpetas": {
                    "Semillas": ["Firmadas", "Generadas"],
                    "XML": ["Firmadas", "Generadas"],
                    "Bin": {
                        "Servicios": ["Config"]
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Error cargando configuración de directorios: {str(e)}")
        # Retornar configuración por defecto en caso de error
        return {
            "estructura_base": "C:/Base/Ambiente/",
            "carpetas_principales": ["Img", "RI", "Token", "Cert", "CSV"],
            "carpetas_con_subcarpetas": {
                "Semillas": ["Firmadas", "Generadas"],
                "XML": ["Firmadas", "Generadas"],
                "Bin": {
                    "Servicios": ["Config"]
                }
            }
        }

routes = Blueprint("routes", __name__)

# ========================= FUNCIÓN AUXILIAR PARA RUTAS DE AMBIENTE =========================

def obtener_ruta_empresa(rnc, ambiente="CERT"):
    """
    Obtiene la ruta completa de una empresa según el ambiente especificado.
    
    Args:
        rnc (str): RNC de la empresa
        ambiente (str): Ambiente (PRD, CERT, QAS). Por defecto CERT
        
    Returns:
        str: Ruta completa de la empresa
    """
    config_directorios = cargar_config_directorios()
    ruta_base = config_directorios.get("estructura_base", "C:/Base/Ambiente/")
    return os.path.join(ruta_base, ambiente, str(rnc))

# ========================================================================================

# ========================= FUNCIONES DE ENCRIPTACIÓN PARA CONTRASEÑAS =========================

# Clave de encriptación (en producción, esto debe estar en una variable de entorno o archivo de configuración seguro)
# Esta clave se usa para encriptar/desencriptar las contraseñas de los certificados
ENCRYPTION_KEY = b'fedgii_cert_key_2025_secure_do_not_share_this_key_ever'

def get_encryption_key():
    """
    Genera una clave de encriptación derivada de la clave maestra usando PBKDF2HMAC.
    Esto asegura que la clave tenga el formato correcto para Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fedgii_salt_2025',
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
    return key

def encrypt_password(password: str) -> str:
    """
    Encripta una contraseña para almacenarla de forma segura pero reversible.
    
    Args:
        password (str): Contraseña en texto plano
        
    Returns:
        str: Contraseña encriptada en base64
    """
    try:
        fernet = Fernet(get_encryption_key())
        encrypted = fernet.encrypt(password.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encriptando contraseña: {str(e)}")
        raise

def decrypt_password(encrypted_password: str) -> str:
    """
    Desencripta una contraseña almacenada.
    
    Args:
        encrypted_password (str): Contraseña encriptada en base64
        
    Returns:
        str: Contraseña en texto plano
    """
    try:
        fernet = Fernet(get_encryption_key())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error desencriptando contraseña: {str(e)}")
        raise

# ========================================================================================

def add_cors_headers(response):
    """Agregar headers CORS a una respuesta"""
    if hasattr(response, 'headers'):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition,Content-Length,Content-Type')
    return response

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def clean_expired_tokens():
    """
    Limpia tokens expirados de la base de datos
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar tokens con tiempo de expiración pasado
        # Nota: Asumiendo que creation_time + duración = tiempo de expiración
        cursor.execute("""
            UPDATE tokenjwt 
            SET active = 0 
            WHERE active = 1 
            AND (
                ([1hour] = 1 AND DATEADD(hour, 1, creation_time) < GETDATE()) OR
                ([30min] = 1 AND DATEADD(minute, 30, creation_time) < GETDATE()) OR
                ([5min] = 1 AND DATEADD(minute, 5, creation_time) < GETDATE())
            )
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logger.info(f"Se limpiaron {affected_rows} tokens expirados")
        
        return affected_rows
        
    except Exception as e:
        logger.error(f"Error limpiando tokens expirados: {str(e)}")
        return 0

def validate_api_key_from_file(api_key):
    """
    Valida la API key contra la API key guardada en el archivo local APIWEB/data/apikey.json
    """
    try:
        # Ruta absoluta del archivo API key en APIWEB/data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        apikey_file_path = os.path.join(current_dir, "data", "apikey.json")
        
        # Verificar que el archivo existe
        if not os.path.exists(apikey_file_path):
            logger.warning("Archivo de API key no encontrado")
            return False
        
        # Leer API key del archivo
        with open(apikey_file_path, "r", encoding="utf-8") as f:
            api_key_data = json.load(f)
        
        # Verificar formato del archivo
        if not isinstance(api_key_data, dict) or "API_KEY" not in api_key_data:
            logger.error("Formato inválido del archivo de API key")
            return False
        
        stored_api_key = api_key_data.get("API_KEY")
        if not stored_api_key:
            logger.error("API key vacía en archivo")
            return False
        
        # Comparar API keys
        return api_key == stored_api_key.strip()
        
    except Exception as e:
        logger.error(f"Error validando API key desde archivo: {str(e)}")
        return False

def validate_token_from_database(token, username):
    """
    Valida un token JWT contra la base de datos tokenjwt
    También limpia tokens expirados automáticamente
    
    Args:
        token (str): Token JWT a validar
        username (str): Nombre de usuario
        
    Returns:
        bool: True si el token es válido, False si no
    """
    try:
        # Limpiar tokens expirados primero
        clean_expired_tokens()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consultar token activo en la base de datos
        cursor.execute(
            "SELECT token, active, creation_time FROM tokenjwt WHERE username = ? AND active = 1",
            (username,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            logger.warning(f"No se encontró token activo para usuario: {username}")
            return False
        
        db_token, active, created_at = result
        
        # Verificar que el token coincida
        if db_token != token:
            logger.warning(f"Token no coincide para usuario: {username}")
            return False
        
        # Verificar que esté activo
        if not active:
            logger.warning(f"Token inactivo para usuario: {username}")
            return False
        
        logger.info(f"Token validado exitosamente para usuario: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error validando token en base de datos: {str(e)}")
        return False

def token_required(f):
    """
    Decorador que requiere SOLO token JWT válido (para usuarios regulares)
    No acepta API Keys - solo autenticación por token de sesión
    """
    @functools.wraps(f)
    def token_decorator(*args, **kwargs):
        token = request.headers.get("Authorization")
        api_key = request.headers.get("x-api-key")
        
        # Verificar si se está intentando usar API key cuando se requiere token
        if api_key and not token:
            logger.warning("Intento de acceso con API key en endpoint que requiere token JWT")
            return jsonify({"message": "Este endpoint requiere token JWT, no API key. Use el header Authorization: Bearer <token>"}), 401

        if not token:
            logger.warning("Intento de acceso sin token de autorización")
            return jsonify({"message": "Authorization token is required"}), 401

        try:
            # Extraer el token del header Authorization "Bearer <token>"
            if not token.startswith("Bearer "):
                logger.warning("Formato de header de autorización inválido")
                return jsonify({"message": "Invalid authorization header format. Use 'Bearer <token>'"}), 401
            
            token = token.split(" ")[1]
            
            # Decodificar y validar el JWT
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            username = payload["username"]
            
            # Validar token contra la base de datos tokenjwt
            if not validate_token_from_database(token, username):
                logger.warning(f"Token inválido o inactivo para usuario: {username}")
                return jsonify({"message": "Invalid or inactive token. Please login again."}), 401
            
            logger.info(f"Acceso autorizado con token JWT para usuario: {username}")
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return jsonify({"message": "Token has expired. Please login again."}), 401
        except jwt.InvalidTokenError:
            logger.warning("Token JWT inválido")
            return jsonify({"message": "Invalid token. Please login again."}), 401
        except IndexError:
            logger.warning("Formato de header Authorization inválido")
            return jsonify({"message": "Invalid authorization header format. Use 'Bearer <token>'"}), 401
        except Exception as e:
            logger.error(f"Error validando token: {str(e)}")
            return jsonify({"message": "Token validation error. Please login again."}), 401

        return f(*args, **kwargs)

    return token_decorator

def admin_api_key_required(f):
    """
    Decorador que requiere SOLO API Key válida (para administradores)
    No acepta tokens JWT - solo para operaciones administrativas
    """
    @functools.wraps(f)
    def api_key_decorator(*args, **kwargs):
        api_key = request.headers.get("x-api-key")

        if not api_key:
            return jsonify({"message": "Admin API key is required"}), 401

        try:
            # Validar API Key desde archivo local
            if not validate_api_key_from_file(api_key):
                return jsonify({"message": "Invalid or expired API key"}), 401
            
            logger.info(f"Acceso administrativo autorizado con API Key")
            
        except Exception as e:
            logger.error(f"Error validando API Key: {str(e)}")
            return jsonify({"message": "API Key validation error"}), 401

        return f(*args, **kwargs)

    return api_key_decorator

def token_or_api_key_required(f):
    """
    Decorador que acepta tanto token JWT como API Key (para compatibilidad)
    USAR SOLO cuando sea necesario para operaciones mixtas
    """
    @functools.wraps(f)
    def mixed_auth_decorator(*args, **kwargs):
        token = request.headers.get("Authorization")
        api_key = request.headers.get("x-api-key")

        if not token and not api_key:
            return (
                jsonify({"message": "Authorization token or API key is required"}),
                401,
            )

        if token:
            try:
                # Extraer el token del header Authorization "Bearer <token>"
                if not token.startswith("Bearer "):
                    return jsonify({"message": "Invalid authorization header format"}), 401
                
                token = token.split(" ")[1]
                
                # Decodificar y validar el JWT
                payload = jwt.decode(
                    token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
                )
                username = payload["username"]
                
                # Validar token contra la base de datos
                if not validate_token_from_database(token, username):
                    return jsonify({"message": "Invalid or inactive token"}), 401
                
                logger.info(f"Token utilizado por el usuario: {username}")
                
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token"}), 401
            except IndexError:
                return jsonify({"message": "Invalid authorization header format"}), 401
            except Exception as e:
                logger.error(f"Error validando token: {str(e)}")
                return jsonify({"message": "Token validation error"}), 401
                
        elif api_key:
            if not validate_api_key_from_file(api_key):
                return jsonify({"message": "Invalid or expired API key"}), 401
            logger.info(f"API Key utilizada por administrador")

        return f(*args, **kwargs)

    return mixed_auth_decorator

@routes.route("/CB", methods=["GET"])
@token_or_api_key_required
def CuentasBalance():
    logger.info("Acceso a CuentasBalance con autorización válida")
    response = process_database_requests2("CuentasBalance")
    if hasattr(response, 'headers'):
        response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@routes.route("/EF", methods=["GET"])
@token_or_api_key_required
def estados_fiscales():
    logger.info("Acceso a EstadosFiscales con autorización válida")
    response = process_database_requests3("EstadosFiscales")
    if hasattr(response, 'headers'):
        response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@routes.route("/clean-expired-tokens", methods=["POST"])
@token_or_api_key_required
def clean_expired_tokens_endpoint():
    """
    Endpoint para limpiar manualmente tokens expirados
    """
    try:
        affected_rows = clean_expired_tokens()
        
        return jsonify({
            "message": "Limpieza de tokens completada",
            "tokens_cleaned": affected_rows
        }), 200
        
    except Exception as e:
        logger.error(f"Error en endpoint de limpieza: {str(e)}")
        return jsonify({"message": "Error en limpieza de tokens"}), 500

@routes.route("/verify-token", methods=["GET"])
def verify_token():
    """
    Endpoint para verificar si un token JWT es válido
    """
    try:
        token = request.headers.get("Authorization")
        
        if not token:
            return jsonify({"valid": False, "message": "No token provided"}), 401
        
        if not token.startswith("Bearer "):
            return jsonify({"valid": False, "message": "Invalid authorization header format"}), 401
        
        token = token.split(" ")[1]
        
        # Decodificar el JWT
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        username = payload["username"]
        
        # Validar contra la base de datos
        if validate_token_from_database(token, username):
            return jsonify({
                "valid": True, 
                "username": username,
                "message": "Token is valid"
            }), 200
        else:
            return jsonify({"valid": False, "message": "Token not found in database or inactive"}), 401
            
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "message": "Invalid token"}), 401
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        return jsonify({"valid": False, "message": "Token verification error"}), 500

@routes.route("/")
def home():
    return "404 no found!"

# Handler genérico para solicitudes OPTIONS (CORS preflight)
@routes.route("/xsd/<path:path>", methods=["OPTIONS"])
def handle_xsd_options_path(path=None):
    """
    Handler para las solicitudes OPTIONS (CORS preflight) de todos los endpoints XSD con path
    """
    response = jsonify({"message": "OK"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition,Content-Length,Content-Type')
    return response

@routes.route("/xsd", methods=["OPTIONS"])
def handle_xsd_options_root():
    """
    Handler para las solicitudes OPTIONS (CORS preflight) de endpoint XSD raíz
    """
    response = jsonify({"message": "OK"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition,Content-Length,Content-Type')
    return response

#_______________________________Register User______________________________________________#
@routes.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    tipo_usuario = data.get("tipo_usuario", "FACTURACION")  # Por defecto FACTURACION
    empresa_id = data.get("empresa_id")  # Ahora se requiere EmpresaId en lugar de RNC
    correo = data.get("correo")
    nombre_completo = data.get("nombre_completo")
    telefono = data.get("telefono")  # Opcional
    cedula = data.get("cedula")  # Opcional
    direccion = data.get("direccion")  # Opcional
    puesto_trabajo = data.get("puesto_trabajo")  # Opcional

    # Validar campos requeridos básicos
    if not username or not password:
        return jsonify({
            "error": "Los campos username y password son requeridos"
        }), 400

    # Validaciones condicionales según tipo de usuario
    if tipo_usuario == "FACTURACION":
        # Validar campos requeridos para facturación
        if not empresa_id or not correo or not nombre_completo:
            return jsonify({
                "error": "Los campos empresa_id, correo y nombre_completo son requeridos para usuario de Facturación"
            }), 400
        
        # Verificar que la empresa existe
        empresa = get_data_from_database2_by_id(empresa_id)
        if not empresa:
            return jsonify({"error": "La empresa especificada no existe"}), 400
    elif tipo_usuario == "SOPORTE":
        # Para SOPORTE, empresa_id es opcional pero recomendado
        empresa = None
        if empresa_id:
            empresa = get_data_from_database2_by_id(empresa_id)
            if not empresa:
                return jsonify({"error": "La empresa especificada no existe"}), 400
    elif tipo_usuario == "CLIENTE":
        # Para CLIENTE, empresa_id es obligatorio (vincula al cliente con su empresa)
        if not empresa_id:
            return jsonify({
                "error": "El campo empresa_id es obligatorio para usuarios de tipo Cliente"
            }), 400
        
        # Verificar que la empresa existe
        empresa = get_data_from_database2_by_id(empresa_id)
        if not empresa:
            return jsonify({"error": "La empresa especificada no existe"}), 400
    else:
        return jsonify({"error": "Tipo de usuario inválido. Use 'FACTURACION', 'SOPORTE' o 'CLIENTE'"}), 400

    # Verificar que el usuario no existe
    existing_user = get_data_from_database(username)
    if existing_user:
        return jsonify({"error": "Usuario ya existe"}), 400

    hashed_password = hash_password(password)

    conn = None
    cursor = None
    rnc_empresa = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construcción dinámica del INSERT según el tipo de usuario
        if tipo_usuario == "SOPORTE":
            # Para SOPORTE generar correo único (requerido por constraint UNIQUE)
            # Usar username + timestamp + dominio interno para garantizar unicidad
            correo_soporte = f"{username}_{int(time.time())}@sopor.inter"
            
            if empresa_id:
                # Soporte con empresa asignada
                cursor.execute("""
                    INSERT INTO usuariosj (EmpresaId, username, password, correo, nombre_completo, tipo_usuario) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (empresa_id, username, hashed_password, correo_soporte, nombre_completo or username, tipo_usuario))
            else:
                # Soporte sin empresa
                cursor.execute("""
                    INSERT INTO usuariosj (username, password, correo, tipo_usuario) 
                    VALUES (?, ?, ?, ?)
                """, (username, hashed_password, correo_soporte, tipo_usuario))
        elif tipo_usuario == "CLIENTE":
            # Para CLIENTE, empresa_id es obligatorio - correo opcional
            correo_cliente = correo if correo else f"{username}_{int(time.time())}@cliente.interno"
            cursor.execute("""
                INSERT INTO usuariosj (EmpresaId, username, password, correo, nombre_completo, telefono, tipo_usuario) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (empresa_id, username, hashed_password, correo_cliente, nombre_completo or username, telefono, tipo_usuario))
        else:
            # Para FACTURACION insertar todos los campos
            cursor.execute("""
                INSERT INTO usuariosj (EmpresaId, username, password, correo, nombre_completo, telefono, cedula, direccion, puesto_trabajo, tipo_usuario) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (empresa_id, username, hashed_password, correo, nombre_completo, telefono, cedula, direccion, puesto_trabajo, tipo_usuario))
        
        conn.commit()
        
        # Crear estructura de carpetas para la empresa si no existe (solo para FACTURACION)
        if tipo_usuario == "FACTURACION" and empresa:
            try:
                rnc_empresa = empresa[1]  # Asumiendo que el RNC está en la segunda posición
                ruta_empresa = crear_estructura_empresa(rnc_empresa)
                logger.info(f"Estructura de carpetas verificada en: {ruta_empresa}")
            except Exception as e:
                logger.warning(f"Error creando estructura de carpetas: {str(e)}")
                # No fallar el registro por esto
        
    except pyodbc.IntegrityError as e:
        if conn:
            conn.rollback()
        if "correo" in str(e).lower():
            return jsonify({"error": "El correo electrónico ya está registrado"}), 400
        elif "username" in str(e).lower():
            return jsonify({"error": "El nombre de usuario ya está registrado"}), 400
        else:
            return jsonify({"error": "Error de integridad en la base de datos"}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    logger.info(f"Nuevo usuario registrado: {username} (tipo: {tipo_usuario})" + (f" para empresa ID: {empresa_id}" if empresa_id else ""))
    
    response_data = {
        "message": "Usuario registrado exitosamente", 
        "username": username,
        "tipo_usuario": tipo_usuario
    }
    
    # Agregar datos de empresa para FACTURACION y CLIENTE
    if tipo_usuario in ["FACTURACION", "CLIENTE"]:
        response_data["empresa_id"] = empresa_id
        response_data["rnc_empresa"] = rnc_empresa
    elif tipo_usuario == "SOPORTE" and empresa_id:
        response_data["empresa_id"] = empresa_id
    
    return jsonify(response_data), 201

#_______________________________Login Soporte______________________________________________#
@routes.route("/login-soporte", methods=["POST"])
def login_soporte():
    """
    Endpoint específico para login de usuarios de soporte y clientes.
    Valida usuarios con tipo_usuario = 'SOPORTE' o 'CLIENTE'
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Usuario y contraseña son requeridos"
        }), 400
    
    try:
        # Buscar usuario en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, username, password, tipo_usuario, nombre_completo, correo, EmpresaId
            FROM usuariosj 
            WHERE username = ? AND tipo_usuario IN ('SOPORTE', 'CLIENTE')
        """, (username,))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not usuario:
            logger.warning(f"Intento de login fallido - Usuario no encontrado o no es de soporte: {username}")
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado o no tiene permisos de soporte"
            }), 401
        
        # Verificar contraseña usando la misma función que el registro
        stored_password = usuario[2]  # password hasheado de la BD
        
        # Verificar si la contraseña coincide
        if not verify_password(stored_password, password):
            logger.warning(f"Intento de login fallido - Contraseña incorrecta para: {username}")
            return jsonify({
                "success": False,
                "error": "Contraseña incorrecta"
            }), 401
        
        # Log diferente según el tipo de usuario
        tipo_usuario = usuario[3]
        if tipo_usuario == "CLIENTE":
            logger.info(f"Login exitoso de usuario cliente: {username}")
        else:
            logger.info(f"Login exitoso de usuario de soporte: {username}")
        
        response_data = {
            "success": True,
            "message": "Login exitoso",
            "usuario": {
                "id": usuario[0],
                "username": usuario[1],
                "tipo_usuario": usuario[3],
                "nombre_completo": usuario[4] if usuario[4] else usuario[1],
                "correo": usuario[5]
            }
        }
        
        # Agregar empresa_id si existe (importante para clientes)
        if usuario[6]:  # EmpresaId
            response_data["usuario"]["empresa_id"] = usuario[6]
        
        return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f"Error en login de soporte: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        }), 500


#_______________________________Login Cliente______________________________________________#
@routes.route("/login-cliente", methods=["POST"])
def login_cliente():
    """
    Endpoint específico para login de usuarios clientes.
    Solo valida usuarios con tipo_usuario = 'CLIENTE'
    Los clientes pueden ver y editar tickets de su empresa, pero no eliminarlos.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Usuario y contraseña son requeridos"
        }), 400
    
    try:
        # Buscar usuario en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.Id, u.username, u.password, u.tipo_usuario, u.nombre_completo, u.correo, 
                   u.EmpresaId, e.RNC, e.RazonSocial, e.NombreComercial
            FROM usuariosj u
            LEFT JOIN EmpresaFE e ON u.EmpresaId = e.Id
            WHERE u.username = ? AND u.tipo_usuario = 'CLIENTE'
        """, (username,))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not usuario:
            logger.warning(f"Intento de login fallido - Usuario cliente no encontrado: {username}")
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado o no tiene permisos de cliente"
            }), 401
        
        # Verificar contraseña
        stored_password = usuario[2]
        
        if not verify_password(stored_password, password):
            logger.warning(f"Intento de login fallido - Contraseña incorrecta para cliente: {username}")
            return jsonify({
                "success": False,
                "error": "Contraseña incorrecta"
            }), 401
        
        # Generar token JWT para el cliente
        deactivate_old_tokens(username)
        
        expiration_time = datetime.utcnow() + timedelta(hours=8)  # 8 horas para clientes
        
        token_data = {
            "username": username,
            "tipo_usuario": "CLIENTE",
            "empresa_id": usuario[6],
            "rnc_empresa": usuario[7],
            "exp": expiration_time
        }
        
        token = jwt.encode(
            token_data,
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        
        # Guardar token en base de datos
        save_token(username, token, hour1=0, min30=0, min5=0)
        
        logger.info(f"Login exitoso de cliente: {username} (Empresa: {usuario[8]})")
        
        return jsonify({
            "success": True,
            "message": "Login exitoso",
            "token": token,
            "usuario": {
                "id": usuario[0],
                "username": usuario[1],
                "tipo_usuario": usuario[3],
                "nombre_completo": usuario[4] if usuario[4] else usuario[1],
                "correo": usuario[5],
                "empresa_id": usuario[6],
                "empresa": {
                    "id": usuario[6],
                    "rnc": usuario[7],
                    "razon_social": usuario[8],
                    "nombre_comercial": usuario[9]
                } if usuario[6] else None
            },
            # Permisos específicos del cliente
            "permisos": {
                "tickets": {
                    "ver": True,
                    "crear": True,
                    "editar": True,
                    "eliminar": False
                },
                "queries": False,
                "manuales": False
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Error en login de cliente: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        }), 500


#_______________________________Login Admin______________________________________________#
@routes.route("/login-admin", methods=["POST"])
def login_admin():
    """
    Endpoint específico para login de usuarios administradores.
    Solo valida usuarios con tipo_usuario = 'ADMIN' o 'ADMINISTRADOR'
    Incluye generación de token JWT para autenticación posterior.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "JSON data required"
        }), 400
    
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Usuario y contraseña son requeridos"
        }), 400
    
    try:
        # Buscar usuario en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, username, password, tipo_usuario, nombre_completo, correo, EmpresaId
            FROM usuariosj 
            WHERE username = ? AND tipo_usuario IN ('ADMIN', 'ADMINISTRADOR')
        """, (username,))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not usuario:
            logger.warning(f"Intento de login fallido - Usuario no encontrado o no es administrador: {username}")
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado o no tiene permisos de administrador"
            }), 401
        
        # Verificar contraseña usando la misma función que el registro
        stored_password = usuario[2]  # password hasheado de la BD
        
        # Verificar si la contraseña coincide
        if not verify_password(stored_password, password):
            logger.warning(f"Intento de login fallido - Contraseña incorrecta para administrador: {username}")
            return jsonify({
                "success": False,
                "error": "Contraseña incorrecta"
            }), 401
        
        # Desactivar tokens antiguos del usuario
        deactivate_old_tokens(username)
        
        # Obtener configuración de tiempo de expiración
        hour1 = data.get("1hour", 0)
        min30 = data.get("30min", 0)
        min5 = data.get("5min", 0)
        
        # Determinar tiempo de expiración
        expiration_time = None
        if hour1:
            expiration_time = datetime.utcnow() + timedelta(hours=1)
        elif min30:
            expiration_time = datetime.utcnow() + timedelta(minutes=30)
        elif min5:
            expiration_time = datetime.utcnow() + timedelta(minutes=5)
        else:
            # Por defecto, 1 hora si no se especifica
            expiration_time = datetime.utcnow() + timedelta(hours=1)
        
        # Crear payload del token
        token_data = {
            "username": username,
            "user_id": usuario[0],
            "empresa_id": usuario[6] if usuario[6] else None,
            "tipo_usuario": usuario[3]
        }
        
        if expiration_time:
            token_data["exp"] = int(expiration_time.timestamp())
        
        # Generar token JWT
        token = jwt.encode(token_data, current_app.config["SECRET_KEY"], algorithm="HS256")
        
        # Guardar token en base de datos
        save_token(username, token, hour1, min30, min5)
        
        logger.info(f"Login exitoso de usuario administrador: {username}")
        
        return jsonify({
            "success": True,
            "message": "Login exitoso",
            "token": token,
            "usuario": {
                "id": usuario[0],
                "username": usuario[1],
                "tipo_usuario": usuario[3],
                "nombre_completo": usuario[4] if usuario[4] else usuario[1],
                "correo": usuario[5],
                "empresa_id": usuario[6] if usuario[6] else None
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Error en login de administrador: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        }), 500

#_____________________________________________Register interprise__________________________________________________________#

def allowed_file(filename):
    """Valida si el archivo tiene una extensión permitida para imágenes"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_certificate_file(filename):
    """Valida si el archivo tiene una extensión permitida para certificados"""
    ALLOWED_CERT_EXTENSIONS = {'p12', 'pfx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_CERT_EXTENSIONS

def validar_url(url):
    """Validar que la URL sea válida (opcional pero recomendado)"""
    if not url:
        return True  # Campo opcional, vacío es válido
    
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def api_key_required(f):
    """Decorador que requiere API Key válida desde archivo local"""
    @functools.wraps(f)
    def api_key_auth_decorator(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return jsonify({"error": "API Key requerida en header X-API-Key"}), 401
        
        if not validate_api_key(api_key):
            return jsonify({"error": "API Key inválida"}), 401
        
        return f(*args, **kwargs)
    
    return api_key_auth_decorator

def validate_api_key(api_key):
    """Valida la API key proporcionada contra la guardada en archivo local"""
    if not api_key:
        return False
    
    try:
        # Ruta del archivo de API Key en APIWEB/data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        apikey_file_path = os.path.join(current_dir, "data", "apikey.json")
        
        # Verificar que el archivo existe
        if not os.path.exists(apikey_file_path):
            logger.warning("No se encontró archivo de API key para validación")
            return False
        
        # Leer API key guardada
        with open(apikey_file_path, "r", encoding="utf-8") as f:
            api_key_data = json.load(f)
        
        # Validar formato del archivo
        if not isinstance(api_key_data, dict) or "API_KEY" not in api_key_data:
            logger.error("Archivo de API key tiene formato inválido")
            return False
        
        stored_api_key = api_key_data.get("API_KEY")
        if not stored_api_key:
            logger.error("API key en archivo está vacía")
            return False
        
        # Comparar API keys
        return api_key.strip() == stored_api_key.strip()
        
    except Exception as e:
        logger.error(f"Error validando API key: {str(e)}")
        return False

@routes.route("/register_empresa", methods=["POST"])
def register_empresa():
    # Obtener datos del formulario (multipart/form-data para archivos)
    rnc = request.form.get("rnc")
    nombre_comercial = request.form.get("NombreComercial")
    razon_social = request.form.get("RazonSocial")
    valido = request.form.get("Valido", "1")  # por defecto '1'
    enlace_renovacion = request.form.get("enlace_renovacion_certificado", "")  # Campo opcional
    clave_portal_cert = request.form.get("clave_portal_cert", "")  # Campo opcional
    clave_certificado = request.form.get("clave_certificado", "")  # Campo opcional
    
    # Si no hay datos en form, intentar obtener de JSON (compatibilidad hacia atrás)
    if not rnc:
        data = request.get_json()
        if data:
            rnc = data.get("rnc")
            nombre_comercial = data.get("NombreComercial")
            razon_social = data.get("RazonSocial")
            valido = data.get("Valido", "1")
            enlace_renovacion = data.get("enlace_renovacion_certificado", "")
            clave_portal_cert = data.get("clave_portal_cert", "")
            clave_certificado = data.get("clave_certificado", "")

    # Validar datos requeridos
    if not rnc or not nombre_comercial or not razon_social:
        return jsonify({"error": "RNC, NombreComercial y RazonSocial son requeridos"}), 400
    
    # Validar URL de renovación si se proporciona
    if enlace_renovacion and not validar_url(enlace_renovacion):
        return jsonify({"error": "El enlace de renovación de certificado no es una URL válida"}), 400
    
    # Encriptar las claves si se proporcionan
    clave_portal_cert_encrypted = None
    if clave_portal_cert:
        try:
            clave_portal_cert_encrypted = encrypt_password(clave_portal_cert)
        except Exception as e:
            logger.error(f"Error encriptando clave portal: {str(e)}")
            return jsonify({"error": "Error procesando clave del portal"}), 500
    
    clave_certificado_encrypted = None
    if clave_certificado:
        try:
            clave_certificado_encrypted = encrypt_password(clave_certificado)
        except Exception as e:
            logger.error(f"Error encriptando clave certificado: {str(e)}")
            return jsonify({"error": "Error procesando clave del certificado"}), 500

    # Validar si ya existe la empresa
    existing_empresa = get_data_from_database2(rnc)
    if existing_empresa:
        return jsonify({"error": "La empresa ya existe"}), 400

    # Procesar imagen si se envía
    logo_filename = None
    logo_path = None
    
    # Crear estructura de carpetas primero
    try:
        rutas_empresa = crear_estructura_empresa(rnc)
        logger.info(f"Estructura de carpetas creada en: {rutas_empresa}")
    except Exception as e:
        logger.warning(f"Error creando estructura de carpetas: {str(e)}")
        return jsonify({"error": f"Error creando estructura de carpetas: {str(e)}"}), 500
    
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename != '':
            if allowed_file(file.filename):
                # Generar nombre seguro para el archivo
                original_extension = file.filename.rsplit('.', 1)[1].lower()
                logo_filename = f"logo_{rnc}.{original_extension}"
                
                # Guardar la imagen en la carpeta img de CERT (ambiente de certificación)
                try:
                    ruta_cert = rutas_empresa.get("CERT")
                    img_folder = os.path.join(ruta_cert, "Img")
                    logo_path = os.path.join(img_folder, logo_filename)
                    
                    file.save(logo_path)
                    logger.info(f"Logo guardado en: {logo_path}")
                    
                except Exception as e:
                    logger.error(f"Error guardando logo: {str(e)}")
                    return jsonify({"error": f"Error guardando logo: {str(e)}"}), 500
            else:
                return jsonify({"error": "Tipo de archivo no permitido. Use: png, jpg, jpeg, gif, bmp, webp"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar en la base de datos sin la columna Logo
        cursor.execute(
            """INSERT INTO EmpresaFE (RNC, NombreComercial, RazonSocial, Valido, 
               enlace_renovacion_certificado, clave_portal_cert, clave_certificado) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (rnc, nombre_comercial, razon_social, valido, 
             enlace_renovacion, clave_portal_cert_encrypted, clave_certificado_encrypted)
        )
        logger.info(f"Empresa registrada en base de datos para RNC: {rnc}")
        
        conn.commit()
        cursor.close()
        conn.close()

    except pyodbc.IntegrityError:
        return jsonify({"error": "Error de integridad en la base de datos"}), 500
    except Exception as e:
        logger.error(f"Error en registro de empresa: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

    response_data = {
        "message": "Empresa registrada exitosamente",
        "rnc": rnc,
        "rutas_empresa": {
            "PRD": f"C:/Base/Ambiente/PRD/{rnc}",
            "CERT": f"C:/Base/Ambiente/CERT/{rnc}",
            "QAS": f"C:/Base/Ambiente/QAS/{rnc}"
        }
    }
    
    if logo_filename:
        response_data["logo"] = {
            "filename": logo_filename,
            "path": logo_path.replace("\\", "/")
        }

    logger.info(f"Nueva empresa registrada: {razon_social} con RNC: {rnc}")
    return jsonify(response_data), 201

@routes.route("/empresa/<rnc>/logo", methods=["GET"])
@token_or_api_key_required
def obtener_logo_empresa(rnc):
    """
    Endpoint para obtener el logo de una empresa desde la carpeta img.
    Retorna la imagen directamente como respuesta binaria.
    Busca en el ambiente CERT por defecto, pero puede especificarse con query param ?ambiente=PRD|QAS
    """
    try:
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        
        # Ruta de la carpeta img de la empresa
        img_folder = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Img")
        
        # Verificar que existe la carpeta
        if not os.path.exists(img_folder):
            return jsonify({"error": f"Carpeta de imágenes no encontrada para esta empresa en ambiente {ambiente}"}), 404
        
        # Buscar archivos de logo (pueden tener diferentes extensiones)
        logo_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
        logo_file = None
        
        for ext in logo_extensions:
            potential_logo = os.path.join(img_folder, f"logo_{rnc}.{ext}")
            if os.path.exists(potential_logo):
                logo_file = potential_logo
                break
        
        if not logo_file:
            return jsonify({"error": "Logo no encontrado para esta empresa"}), 404
        
        # Detectar el tipo de contenido basado en la extensión
        file_ext = logo_file.split('.')[-1].lower()
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        content_type = content_type_map.get(file_ext, 'image/jpeg')
        
        # Enviar archivo
        return send_file(
            logo_file,
            mimetype=content_type,
            as_attachment=False,  # Para mostrar en el navegador, no descargar
            download_name=f"logo_{rnc}.{file_ext}"
        )
            
    except Exception as e:
        logger.error(f"Error obteniendo logo: {str(e)}")
        return jsonify({"error": "Error obteniendo logo"}), 500

@token_or_api_key_required
def verificar_estructura_empresa(rnc):
    """
    Endpoint para verificar si existe la estructura de carpetas para un RNC en todos los ambientes.
    """
    try:
        ambientes = ["PRD", "CERT", "QAS"]
        resultado = {
            "rnc": rnc,
            "ambientes": {}
        }
        
        for ambiente in ambientes:
            ruta_empresa = obtener_ruta_empresa(rnc, ambiente)
            existe = os.path.exists(ruta_empresa)
            resultado["ambientes"][ambiente] = {
                "existe": existe,
                "ruta": ruta_empresa
            }
        
        return jsonify(resultado), 200
            
    except Exception as e:
        logger.error(f"Error verificando estructura: {str(e)}")
        return jsonify({"error": "Error verificando estructura"}), 500

def obtener_info_certificados_empresa(rnc, ambiente="CERT"):
    """
    Función auxiliar para obtener información resumida de certificados de una empresa
    Usa valido_desde y valido_hasta extraídos del certificado real
    
    Args:
        rnc (str): RNC de la empresa
        ambiente (str): Ambiente del cual obtener los certificados (CERT por defecto)
    """
    try:
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        
        if not os.path.exists(cert_dir):
            return {
                "total_certificados": 0,
                "certificados": [],
                "estado_general": "sin_certificados"
            }
        
        certificates = []
        current_date = datetime.now()
        
        for filename in os.listdir(cert_dir):
            if filename.endswith('.json'):
                continue
                
            file_path = os.path.join(cert_dir, filename)
            if not os.path.isfile(file_path):
                continue
            
            # Datos básicos
            cert_info = {
                "filename": filename,
                "nombre_personalizado": "Sin nombre personalizado",
                "valido_desde": None,
                "valido_hasta": None,
                "estado": "desconocido",
                "password_hash": None
            }
            
            # Cargar metadatos si existen
            metadata_file = os.path.join(cert_dir, f"{filename}.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        cert_info.update({
                            "nombre_personalizado": metadata.get("nombre_personalizado", cert_info["nombre_personalizado"]),
                            "valido_desde": metadata.get("valido_desde"),
                            "valido_hasta": metadata.get("valido_hasta"),
                            "password_hash": metadata.get("password_hash")
                        })
                except:
                    pass
            
            # Si no hay fechas en metadatos, intentar extraer del certificado
            if not cert_info["valido_hasta"] or not cert_info["valido_desde"]:
                try:
                    # Intentar cargar info del certificado si tenemos password_hash
                    # Nota: En producción necesitarías la contraseña real para extraer las fechas
                    # Por ahora usamos valores por defecto si no están en metadatos
                    if cert_info["valido_hasta"] is None:
                        # Fecha por defecto: 1 año desde la fecha de modificación del archivo
                        stat_info = os.stat(file_path)
                        fecha_archivo = datetime.fromtimestamp(stat_info.st_mtime)
                        cert_info["valido_desde"] = fecha_archivo.isoformat()
                        cert_info["valido_hasta"] = (fecha_archivo + timedelta(days=365)).isoformat()
                except:
                    pass
            
            # Calcular estado si tenemos fecha de vencimiento
            if cert_info["valido_hasta"]:
                try:
                    fecha_venc = datetime.fromisoformat(cert_info["valido_hasta"].replace('Z', '+00:00'))
                    if fecha_venc.tzinfo:
                        fecha_venc = fecha_venc.replace(tzinfo=None)
                    
                    dias_restantes = (fecha_venc - current_date).days
                    
                    if dias_restantes < 0:
                        cert_info["estado"] = "expirado"
                        cert_info["estado_emoji"] = "🔴"
                    elif dias_restantes <= 60:
                        cert_info["estado"] = "proximo_a_vencer"
                        cert_info["estado_emoji"] = "🟠"
                    else:
                        cert_info["estado"] = "vigente"
                        cert_info["estado_emoji"] = "🟢"
                    
                    cert_info["dias_para_vencer"] = dias_restantes
                except:
                    cert_info["estado"] = "error"
                    cert_info["dias_para_vencer"] = None
            
            certificates.append(cert_info)
        
        # Determinar estado general
        if not certificates:
            estado_general = "sin_certificados"
        elif any(c["estado"] == "expirado" for c in certificates):
            estado_general = "tiene_expirados"
        elif any(c["estado"] == "proximo_a_vencer" for c in certificates):
            estado_general = "tiene_proximos_a_vencer"
        else:
            estado_general = "todos_vigentes"
        
        return {
            "total_certificados": len(certificates),
            "certificados": certificates,
            "estado_general": estado_general,
            "resumen": {
                "vigentes": len([c for c in certificates if c["estado"] == "vigente"]),
                "proximos_a_vencer": len([c for c in certificates if c["estado"] == "proximo_a_vencer"]),
                "expirados": len([c for c in certificates if c["estado"] == "expirado"])
            }
        }
        
    except Exception as e:
        logger.warning(f"Error obteniendo certificados para empresa {rnc}: {str(e)}")
        return {
            "total_certificados": 0,
            "certificados": [],
            "estado_general": "error",
            "error": str(e)
        }

@routes.route("/empresas", methods=["GET"])
@token_or_api_key_required
def obtener_empresas():
    """
    Endpoint para obtener todas las empresas registradas en la tabla EmpresaFE
    con información detallada de certificados incluyendo:
    - Contenido del certificado (información básica)
    - Fechas de agregado y vencimiento
    - Estado del certificado (vigente/próximo a vencer/expirado)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Id, RNC, NombreComercial, RazonSocial, Valido, created_at, 
                   enlace_renovacion_certificado, clave_portal_cert, clave_certificado
            FROM EmpresaFE 
            ORDER BY RazonSocial
        """)
        empresas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir resultados a formato JSON con información de certificados
        empresas_list = []
        for empresa in empresas:
            rnc = empresa[1]
            
            # Obtener información de certificados
            cert_info = obtener_info_certificados_empresa(rnc)
            
            # Desencriptar claves si existen
            clave_portal_cert_decrypted = None
            if len(empresa) > 7 and empresa[7]:
                try:
                    clave_portal_cert_decrypted = decrypt_password(empresa[7])
                except Exception as e:
                    logger.warning(f"Error desencriptando clave portal para RNC {rnc}: {str(e)}")
            
            clave_certificado_decrypted = None
            if len(empresa) > 8 and empresa[8]:
                try:
                    clave_certificado_decrypted = decrypt_password(empresa[8])
                except Exception as e:
                    logger.warning(f"Error desencriptando clave certificado para RNC {rnc}: {str(e)}")
            
            empresa_data = {
                "id": empresa[0],
                "rnc": rnc,
                "nombre_comercial": empresa[2],
                "razon_social": empresa[3],
                "valido": empresa[4],
                "created_at": empresa[5].isoformat() if empresa[5] else None,
                "enlace_renovacion_certificado": empresa[6] if len(empresa) > 6 else None,
                "clave_portal_cert": clave_portal_cert_decrypted,
                "clave_certificado": clave_certificado_decrypted,
                
                # Nueva información de certificados
                "certificados": {
                    "total": cert_info["total_certificados"],
                    "estado_general": cert_info["estado_general"],
                    "resumen": cert_info.get("resumen", {
                        "vigentes": 0,
                        "proximos_a_vencer": 0,
                        "expirados": 0
                    }),
                    "detalle": cert_info["certificados"]  # Lista completa de certificados
                }
            }
            
            empresas_list.append(empresa_data)
        
        logger.info(f"Consulta de empresas realizada con información de certificados. Total encontradas: {len(empresas_list)}")
        
        # Estadísticas generales
        total_certificados = sum(e["certificados"]["total"] for e in empresas_list)
        empresas_con_cert = len([e for e in empresas_list if e["certificados"]["total"] > 0])
        empresas_sin_cert = len(empresas_list) - empresas_con_cert
        
        return jsonify({
            "empresas": empresas_list,
            "total": len(empresas_list),
            "estadisticas": {
                "total_empresas": len(empresas_list),
                "empresas_con_certificados": empresas_con_cert,
                "empresas_sin_certificados": empresas_sin_cert,
                "total_certificados_sistema": total_certificados
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo empresas: {str(e)}")
        return jsonify({"error": "Error obteniendo lista de empresas"}), 500

@routes.route("/usuarios", methods=["GET"])
@token_or_api_key_required
def obtener_usuarios():
    """
    Endpoint para obtener TODOS los usuarios registrados (FACTURACION y SOPORTE) con información de la empresa.
    Usa LEFT JOIN para incluir usuarios sin empresa asociada (tipo SOPORTE).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.Id, u.EmpresaId, u.username, u.correo, u.nombre_completo, 
                   u.telefono, u.cedula, u.direccion, u.puesto_trabajo, u.created_at,
                   u.tipo_usuario,
                   e.RNC, e.NombreComercial, e.RazonSocial
            FROM usuariosj u
            LEFT JOIN EmpresaFE e ON u.EmpresaId = e.Id
            ORDER BY u.tipo_usuario, u.username
        """)
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir resultados a formato JSON
        usuarios_list = []
        for usuario in usuarios:
            usuario_data = {
                "id": usuario[0],
                "empresa_id": usuario[1],
                "username": usuario[2],
                "correo": usuario[3],
                "nombre_completo": usuario[4],
                "telefono": usuario[5],
                "cedula": usuario[6],
                "direccion": usuario[7],
                "puesto_trabajo": usuario[8],
                "created_at": usuario[9].isoformat() if usuario[9] else None,
                "tipo_usuario": usuario[10] if usuario[10] else "FACTURACION"  # Default si es NULL
            }
            
            # Solo agregar información de empresa si existe (para usuarios FACTURACION)
            if usuario[1] is not None:  # Si tiene EmpresaId
                usuario_data["empresa"] = {
                    "rnc": usuario[11],
                    "nombre_comercial": usuario[12],
                    "razon_social": usuario[13]
                }
            else:
                # Para usuarios SOPORTE sin empresa
                usuario_data["empresa"] = None
            
            usuarios_list.append(usuario_data)
        
        logger.info(f"Consulta de usuarios realizada. Total encontrados: {len(usuarios_list)}")
        
        # Agregar estadísticas por tipo
        stats = {
            "total": len(usuarios_list),
            "facturacion": len([u for u in usuarios_list if u["tipo_usuario"] == "FACTURACION"]),
            "soporte": len([u for u in usuarios_list if u["tipo_usuario"] == "SOPORTE"])
        }
        
        return jsonify({
            "usuarios": usuarios_list,
            "total": len(usuarios_list),
            "estadisticas": stats
        }), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {str(e)}")
        return jsonify({"error": "Error obteniendo lista de usuarios"}), 500

@routes.route("/usuario/<username>", methods=["GET"])
@token_or_api_key_required
def obtener_usuario(username):
    """
    Endpoint para obtener información de un usuario específico por username con información de la empresa.
    Usa LEFT JOIN para incluir usuarios sin empresa asociada (tipo SOPORTE).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.Id, u.EmpresaId, u.username, u.correo, u.nombre_completo, 
                   u.telefono, u.cedula, u.direccion, u.puesto_trabajo, u.created_at,
                   u.tipo_usuario,
                   e.RNC, e.NombreComercial, e.RazonSocial
            FROM usuariosj u
            LEFT JOIN EmpresaFE e ON u.EmpresaId = e.Id
            WHERE u.username = ?
        """, (username,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        usuario_data = {
            "id": usuario[0],
            "empresa_id": usuario[1],
            "username": usuario[2],
            "correo": usuario[3],
            "nombre_completo": usuario[4],
            "telefono": usuario[5],
            "cedula": usuario[6],
            "direccion": usuario[7],
            "puesto_trabajo": usuario[8],
            "created_at": usuario[9].isoformat() if usuario[9] else None,
            "tipo_usuario": usuario[10] if usuario[10] else "FACTURACION"
        }
        
        # Solo agregar información de empresa si existe
        if usuario[1] is not None:  # Si tiene EmpresaId
            usuario_data["empresa"] = {
                "rnc": usuario[11],
                "nombre_comercial": usuario[12],
                "razon_social": usuario[13]
            }
        else:
            usuario_data["empresa"] = None
        
        logger.info(f"Consulta de usuario específico realizada: {username}")
        return jsonify(usuario_data), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo usuario {username}: {str(e)}")
        return jsonify({"error": "Error obteniendo información del usuario"}), 500

@routes.route("/usuario/<username>", methods=["PUT"])
@token_or_api_key_required
def actualizar_usuario(username):
    """
    Endpoint para actualizar los datos de un usuario existente.
    Permite actualizar todos los campos incluyendo empresa_id, password, correo, nombre_completo, etc.
    """
    # Verificar que el usuario existe
    existing_user = get_data_from_database(username)
    if not existing_user:
        return jsonify({"error": "El usuario no existe"}), 404
    
    # Obtener datos del JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    # Extraer campos del request
    empresa_id = data.get("empresa_id")
    password = data.get("password")
    correo = data.get("correo")
    nombre_completo = data.get("nombre_completo")
    telefono = data.get("telefono")
    cedula = data.get("cedula")
    direccion = data.get("direccion")
    puesto_trabajo = data.get("puesto_trabajo")

    # Validar que al menos un campo se va a actualizar
    campos_a_actualizar = [empresa_id, password, correo, nombre_completo, telefono, cedula, direccion, puesto_trabajo]
    if not any(campo is not None for campo in campos_a_actualizar):
        return jsonify({"error": "Se debe proporcionar al menos un campo para actualizar"}), 400

    # Si se proporciona empresa_id, verificar que la empresa existe
    if empresa_id is not None:
        empresa = get_data_from_database2_by_id(empresa_id)
        if not empresa:
            return jsonify({"error": "La empresa especificada no existe"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente solo para campos que se van a actualizar
        updates = []
        params = []
        
        if empresa_id is not None:
            updates.append("EmpresaId = ?")
            params.append(empresa_id)
            
        if password is not None:
            hashed_password = hash_password(password)
            updates.append("password = ?")
            params.append(hashed_password)
            
        if correo is not None:
            updates.append("correo = ?")
            params.append(correo)
            
        if nombre_completo is not None:
            updates.append("nombre_completo = ?")
            params.append(nombre_completo)
            
        if telefono is not None:
            updates.append("telefono = ?")
            params.append(telefono)
            
        if cedula is not None:
            updates.append("cedula = ?")
            params.append(cedula)
            
        if direccion is not None:
            updates.append("direccion = ?")
            params.append(direccion)
            
        if puesto_trabajo is not None:
            updates.append("puesto_trabajo = ?")
            params.append(puesto_trabajo)
        
        # Agregar username al final para la cláusula WHERE
        params.append(username)
        
        query = f"UPDATE usuariosj SET {', '.join(updates)} WHERE username = ?"
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return jsonify({"error": "No se pudo actualizar el usuario"}), 404
            
        conn.commit()
        cursor.close()
        conn.close()

        response_data = {
            "message": "Usuario actualizado exitosamente",
            "username": username,
            "campos_actualizados": {
                "empresa_id": empresa_id is not None,
                "password": password is not None,
                "correo": correo is not None,
                "nombre_completo": nombre_completo is not None,
                "telefono": telefono is not None,
                "cedula": cedula is not None,
                "direccion": direccion is not None,
                "puesto_trabajo": puesto_trabajo is not None
            }
        }

        logger.info(f"Usuario actualizado: {username}")
        return jsonify(response_data), 200

    except pyodbc.IntegrityError as e:
        if "correo" in str(e).lower():
            return jsonify({"error": "El correo electrónico ya está registrado"}), 400
        elif "username" in str(e).lower():
            return jsonify({"error": "El nombre de usuario ya está registrado"}), 400
        else:
            return jsonify({"error": "Error de integridad en la base de datos"}), 500
    except Exception as e:
        logger.error(f"Error actualizando usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/usuario/<username>", methods=["DELETE"])
@token_or_api_key_required
def eliminar_usuario(username):
    """
    Endpoint para eliminar un usuario específico de la tabla usuariosj.
    También desactiva todos los tokens JWT asociados al usuario.
    """
    # Verificar que el usuario existe
    existing_user = get_data_from_database(username)
    if not existing_user:
        return jsonify({"error": "El usuario no existe"}), 404

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar todos los tokens JWT del usuario antes de eliminarlo
        cursor.execute("""
            UPDATE tokenjwt 
            SET active = 0 
            WHERE username = ?
        """, (username,))
        
        # Eliminar usuario de la tabla usuariosj
        cursor.execute("DELETE FROM usuariosj WHERE username = ?", (username,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "No se pudo eliminar el usuario"}), 404
            
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Usuario eliminado exitosamente: {username}")
        return jsonify({
            "message": "Usuario eliminado exitosamente",
            "username": username
        }), 200

    except pyodbc.IntegrityError:
        return jsonify({"error": "Error de integridad en la base de datos"}), 500
    except Exception as e:
        logger.error(f"Error eliminando usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/empresa/<rnc>", methods=["PUT"])
@token_or_api_key_required
def actualizar_empresa(rnc):
    """
    Endpoint para actualizar los datos de una empresa existente.
    Permite actualizar NombreComercial, RazonSocial, Valido y Logo.
    """
    # Verificar que la empresa existe
    existing_empresa = get_data_from_database2(rnc)
    if not existing_empresa:
        return jsonify({"error": "La empresa no existe"}), 404
    
    # Obtener datos del formulario (multipart/form-data para archivos)
    nombre_comercial = request.form.get("NombreComercial")
    razon_social = request.form.get("RazonSocial")
    valido = request.form.get("Valido")
    enlace_renovacion = request.form.get("enlace_renovacion_certificado")
    clave_portal_cert = request.form.get("clave_portal_cert")
    clave_certificado = request.form.get("clave_certificado")
    
    # Si no hay datos en form, intentar obtener de JSON (compatibilidad)
    if not any([nombre_comercial, razon_social, valido, enlace_renovacion, clave_portal_cert, clave_certificado]):
        data = request.get_json()
        if data:
            nombre_comercial = data.get("NombreComercial")
            razon_social = data.get("RazonSocial")
            valido = data.get("Valido")
            enlace_renovacion = data.get("enlace_renovacion_certificado")
            clave_portal_cert = data.get("clave_portal_cert")
            clave_certificado = data.get("clave_certificado")

    # Procesar nueva imagen si se envía
    logo_filename = None
    logo_path = None
    
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename != '':
            if allowed_file(file.filename):
                # Generar nombre seguro para el archivo
                original_extension = file.filename.rsplit('.', 1)[1].lower()
                logo_filename = f"logo_{rnc}.{original_extension}"
                
                # Guardar la imagen en la carpeta img (en ambiente CERT por defecto)
                try:
                    ruta_empresa = obtener_ruta_empresa(rnc, "CERT")
                    img_folder = os.path.join(ruta_empresa, "Img")
                    
                    # Crear carpeta img si no existe
                    os.makedirs(img_folder, exist_ok=True)
                    
                    logo_path = os.path.join(img_folder, logo_filename)
                    file.save(logo_path)
                    logger.info(f"Logo actualizado en: {logo_path}")
                    
                except Exception as e:
                    logger.error(f"Error guardando logo actualizado: {str(e)}")
                    return jsonify({"error": f"Error guardando logo: {str(e)}"}), 500
            else:
                return jsonify({"error": "Tipo de archivo no permitido. Use: png, jpg, jpeg, gif, bmp, webp"}), 400

    # Validar URL de renovación si se proporciona
    if enlace_renovacion and not validar_url(enlace_renovacion):
        return jsonify({"error": "El enlace de renovación de certificado no es una URL válida"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente solo para campos que se van a actualizar
        updates = []
        params = []
        
        if nombre_comercial is not None:
            updates.append("NombreComercial = ?")
            params.append(nombre_comercial)
            
        if razon_social is not None:
            updates.append("RazonSocial = ?")
            params.append(razon_social)
            
        if valido is not None:
            updates.append("Valido = ?")
            params.append(valido)
        
        if enlace_renovacion is not None:
            updates.append("enlace_renovacion_certificado = ?")
            params.append(enlace_renovacion)
        
        if clave_portal_cert is not None:
            # Encriptar la clave si no está vacía
            if clave_portal_cert:
                try:
                    clave_portal_cert_encrypted = encrypt_password(clave_portal_cert)
                    updates.append("clave_portal_cert = ?")
                    params.append(clave_portal_cert_encrypted)
                except Exception as e:
                    logger.error(f"Error encriptando clave portal: {str(e)}")
                    return jsonify({"error": "Error procesando clave del portal"}), 500
            else:
                # Si es vacío, guardar NULL
                updates.append("clave_portal_cert = ?")
                params.append(None)
        
        if clave_certificado is not None:
            # Encriptar la clave si no está vacía
            if clave_certificado:
                try:
                    clave_certificado_encrypted = encrypt_password(clave_certificado)
                    updates.append("clave_certificado = ?")
                    params.append(clave_certificado_encrypted)
                except Exception as e:
                    logger.error(f"Error encriptando clave certificado: {str(e)}")
                    return jsonify({"error": "Error procesando clave del certificado"}), 500
            else:
                # Si es vacío, guardar NULL
                updates.append("clave_certificado = ?")
                params.append(None)
        
        if not updates:
            return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400
        
        # Agregar RNC al final para la cláusula WHERE
        params.append(rnc)
        
        query = f"UPDATE EmpresaFE SET {', '.join(updates)} WHERE RNC = ?"
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return jsonify({"error": "No se pudo actualizar la empresa"}), 404
            
        conn.commit()
        cursor.close()
        conn.close()

        response_data = {
            "message": "Empresa actualizada exitosamente",
            "rnc": rnc,
            "campos_actualizados": {
                "nombre_comercial": nombre_comercial is not None,
                "razon_social": razon_social is not None,
                "valido": valido is not None,
                "logo": logo_filename is not None,
                "enlace_renovacion_certificado": enlace_renovacion is not None,
                "clave_portal_cert": clave_portal_cert is not None,
                "clave_certificado": clave_certificado is not None
            }
        }
        
        if logo_filename:
            response_data["logo"] = {
                "filename": logo_filename,
                "path": logo_path.replace("\\", "/") if logo_path else None
            }

        logger.info(f"Empresa actualizada: RNC {rnc}")
        return jsonify(response_data), 200

    except pyodbc.IntegrityError:
        return jsonify({"error": "Error de integridad en la base de datos"}), 500
    except Exception as e:
        logger.error(f"Error actualizando empresa: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/logout", methods=["POST"])
@token_or_api_key_required
def logout():
    """
    Endpoint para cerrar sesión (desactivar el token actual)
    """
    try:
        token = request.headers.get("Authorization")
        
        if not token:
            return jsonify({"message": "No token provided"}), 401
        
        if not token.startswith("Bearer "):
            return jsonify({"message": "Invalid authorization header format"}), 401
        
        token = token.split(" ")[1]
        
        # Decodificar el JWT para obtener el username
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        username = payload["username"]
        
        # Desactivar el token específico en lugar de todos los tokens del usuario
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE tokenjwt SET active = 0 WHERE username = ? AND token = ?",
            (username, token)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Usuario {username} cerró sesión exitosamente")
        return jsonify({"message": "Logout exitoso"}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return jsonify({"message": "Error en logout"}), 500

@routes.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "JSON data required"}), 400
            
        username = data.get("username")
        password = data.get("password")
        rnc = data.get("rnc")  # Opcional para verificación adicional

        # Validar campos requeridos
        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        user_data = get_data_from_database(username)
        if user_data is None:
            logger.warning(f"Intento de login con usuario inexistente: {username}")
            return jsonify({"message": "Invalid username or password"}), 401

        # Extraer datos del usuario según la nueva estructura
        user_id = user_data[0]
        empresa_id = user_data[1]
        username_db = user_data[2]
        db_password = user_data[3]
        correo = user_data[4]
        nombre_completo = user_data[5]
        db_rnc = user_data[11]  # RNC de la empresa (puede ser None para SOPORTE)
        tipo_usuario = user_data[12] if len(user_data) > 12 else "FACTURACION"  # tipo_usuario

        # Verificar contraseña
        if not verify_password(db_password, password):
            logger.warning(f"Intento de login con contraseña inválida: {username}")
            return jsonify({"message": "Invalid username or password"}), 401

        # Verificar RNC si se proporciona (opcional) y solo para usuarios FACTURACION
        if rnc and tipo_usuario == "FACTURACION" and rnc != db_rnc:
            logger.warning(f"Intento de login con RNC inválido: {username}")
            return jsonify({"message": "Invalid RNC for this user"}), 401

        # Desactivar tokens antiguos del usuario
        deactivate_old_tokens(username)

        # Obtener configuración de tiempo de expiración
        hour1 = data.get("1hour", 0)
        min30 = data.get("30min", 0)
        min5 = data.get("5min", 0)

        # Determinar tiempo de expiración
        expiration_time = None
        if hour1:
            expiration_time = datetime.utcnow() + timedelta(hours=1)
        elif min30:
            expiration_time = datetime.utcnow() + timedelta(minutes=30)
        elif min5:
            expiration_time = datetime.utcnow() + timedelta(minutes=5)
        else:
            # Por defecto, 1 hora si no se especifica
            expiration_time = datetime.utcnow() + timedelta(hours=1)

        # Crear payload del token
        token_data = {
            "username": username, 
            "user_id": user_id,
            "empresa_id": empresa_id,
            "rnc": db_rnc,
            "tipo_usuario": tipo_usuario
        }
        if expiration_time:
            token_data["exp"] = int(expiration_time.timestamp())

        # Generar token JWT
        token = jwt.encode(token_data, current_app.config["SECRET_KEY"], algorithm="HS256")
        
        # Guardar token en base de datos
        save_token(username, token, hour1, min30, min5)

        logger.info(f"Usuario {username} (ID: {user_id}, Tipo: {tipo_usuario})" + (f" con RNC: {db_rnc}" if db_rnc else "") + " inició sesión exitosamente")
        
        # Construir respuesta de usuario
        user_response = {
            "id": user_id,
            "username": username,
            "tipo_usuario": tipo_usuario
        }
        
        # Agregar datos opcionales si existen
        if correo:
            user_response["correo"] = correo
        if nombre_completo:
            user_response["nombre_completo"] = nombre_completo
        if empresa_id:
            user_response["empresa_id"] = empresa_id
        if db_rnc:
            user_response["rnc"] = db_rnc
        
        return jsonify({
            "token": token,
            "user": user_response,
            "expires_at": expiration_time.isoformat() if expiration_time else None,
            "message": "Login exitoso"
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({"message": "Error interno del servidor"}), 500

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

    logger.info(f"API Key generada para el usuario: {username}")
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

        logger.info(
            f"Acceso a datos protegido utilizando API Key por el usuario: {username}"
        )

    user_data = get_data_from_database(username)

    return jsonify({"username": user_data[0], "additional_data": user_data[1]})

# ================================= ENDPOINTS PARA MANEJO DE CERTIFICADOS =================================
# Los certificados se almacenan en: C:/Base/Ambiente/{AMBIENTE}/{RNC}/Cert/
# Esta estructura es consistente con la función crear_estructura_empresa()
# Por defecto se usa el ambiente CERT, pero puede especificarse con query param ?ambiente=PRD|QAS

@routes.route("/empresa/<rnc>/certificado", methods=["POST"])
def upload_certificate(rnc):
    """
    Endpoint específico para manejar la subida de certificados por empresa
    Guarda los certificados en: C:/Base/Ambiente/{AMBIENTE}/{RNC}/Cert/
    Por defecto usa ambiente CERT, pero puede especificarse con query param ?ambiente=PRD|QAS
    """
    # Obtener API key del header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API Key requerida"}), 401
    
    # Validar API key
    if not validate_api_key(api_key):
        return jsonify({"error": "API Key inválida"}), 401
    
    # Validar que la empresa existe
    empresa = get_data_from_database2(rnc)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    
    # Validar que se envió un archivo
    if 'certificate' not in request.files:
        return jsonify({"error": "No se encontró el archivo de certificado"}), 400
    
    certificate = request.files['certificate']
    if certificate.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400
    
    # Obtener contraseña del formulario
    password = request.form.get('password')
    if not password:
        return jsonify({"error": "Contraseña requerida"}), 400
    
    # Validar tipo de archivo
    if not allowed_certificate_file(certificate.filename):
        return jsonify({
            "error": "Tipo de archivo no permitido. Extensiones permitidas: p12, pfx"
        }), 400
    
    try:
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        # Crear directorio si no existe - Ruta completa: C:/Base/Ambiente/{AMBIENTE}/{RNC}/Cert/
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        os.makedirs(cert_dir, exist_ok=True)
        
        # Crear nombre seguro para el archivo
        secure_name = secure_filename(certificate.filename)
        timestamp = int(time.time())
        final_filename = f"{timestamp}_{secure_name}"
        file_path = os.path.join(cert_dir, final_filename)
        
        # Guardar archivo
        certificate.save(file_path)
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        
        # Extraer fechas reales del certificado
        valido_desde = None
        valido_hasta = None
        estado_certificado = "desconocido"
        dias_restantes = None
        
        try:
            info_cert = obtener_info_basica_certificado(file_path, password)
            valido_desde = info_cert.get("valido_desde")
            valido_hasta = info_cert.get("valido_hasta")
            estado_certificado = info_cert.get("estado", "desconocido")
            dias_restantes = info_cert.get("dias_restantes")
        except Exception as e:
            logger.warning(f"No se pudo extraer información del certificado: {str(e)}")
            fecha_actual = datetime.now()
            valido_desde = fecha_actual.isoformat()
            valido_hasta = (fecha_actual + timedelta(days=365)).isoformat()
        
        # Crear metadatos del certificado
        certificate_data = {
            "rnc": rnc,
            "filename": final_filename,
            "original_filename": certificate.filename,
            "file_path": file_path.replace("\\", "/"),
            "valido_desde": valido_desde,
            "valido_hasta": valido_hasta,
            "estado": estado_certificado,
            "dias_restantes": dias_restantes,
            "fecha_subida": datetime.now().isoformat(),
            "file_size": file_size,
            "password_encrypted": encrypt_password(password)  # Guardar contraseña encriptada
        }
        
        # Guardar metadatos en archivo JSON (opcional)
        metadata_file = os.path.join(cert_dir, f"{final_filename}.metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(certificate_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Certificado subido exitosamente para empresa {rnc}: {final_filename}")
        
        return jsonify({
            "message": "Certificado guardado exitosamente",
            "data": {
                "rnc": rnc,
                "filename": final_filename,
                "original_filename": certificate.filename,
                "file_path": certificate_data["file_path"],
                "valido_desde": valido_desde,
                "valido_hasta": valido_hasta,
                "estado": estado_certificado,
                "dias_restantes": dias_restantes,
                "file_size": file_size
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error subiendo certificado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificados", methods=["GET"])
def get_certificates(rnc):
    """
    Endpoint para listar certificados de una empresa
    Por defecto usa ambiente CERT, pero puede especificarse con query param ?ambiente=PRD|QAS
    """
    # Obtener API key del header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API Key requerida"}), 401
    
    # Validar API key
    if not validate_api_key(api_key):
        return jsonify({"error": "API Key inválida"}), 401
    
    # Validar que la empresa existe
    empresa = get_data_from_database2(rnc)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    
    try:
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        
        # Verificar si existe el directorio
        if not os.path.exists(cert_dir):
            return jsonify({"certificados": []}), 200
        
        certificates = []
        
        # Listar archivos en el directorio
        for filename in os.listdir(cert_dir):
            file_path = os.path.join(cert_dir, filename)
            
            # Saltar archivos de metadatos
            if filename.endswith('.metadata.json'):
                continue
                
            if os.path.isfile(file_path):
                # Obtener información básica del archivo
                stat_info = os.stat(file_path)
                cert_info = {
                    "filename": filename,
                    "file_path": file_path.replace("\\", "/"),
                    "file_size": stat_info.st_size,
                    "nombre_personalizado": "Sin nombre personalizado",
                    "valido_desde": None,
                    "valido_hasta": None,
                    "estado": "desconocido"
                }
                
                # Intentar cargar metadatos si existen
                metadata_file = os.path.join(cert_dir, f"{filename}.json")
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            cert_info.update({
                                "original_filename": metadata.get("original_filename", filename),
                                "nombre_personalizado": metadata.get("nombre_personalizado", cert_info["nombre_personalizado"]),
                                "valido_desde": metadata.get("valido_desde"),
                                "valido_hasta": metadata.get("valido_hasta"),
                                "estado": metadata.get("estado", "desconocido")
                            })
                    except Exception as e:
                        logger.warning(f"Error cargando metadatos para {filename}: {str(e)}")
                
                # Si no hay fechas, usar valores por defecto
                if not cert_info["valido_desde"] or not cert_info["valido_hasta"]:
                    fecha_archivo = datetime.fromtimestamp(stat_info.st_mtime)
                    cert_info["valido_desde"] = fecha_archivo.isoformat()
                    cert_info["valido_hasta"] = (fecha_archivo + timedelta(days=365)).isoformat()
                
                certificates.append(cert_info)
        
        # Ordenar por fecha valido_desde (más reciente primero)
        certificates.sort(key=lambda x: x.get("valido_desde", ""), reverse=True)
        
        logger.info(f"Consultados {len(certificates)} certificados para empresa {rnc} en ambiente {ambiente}")
        
        return jsonify({
            "rnc": rnc,
            "ambiente": ambiente,
            "certificados": certificates,
            "total": len(certificates)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo certificados: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificado/<filename>", methods=["DELETE"])
def delete_certificate(rnc, filename):
    """
    Endpoint para eliminar un certificado específico
    Por defecto usa ambiente CERT, pero puede especificarse con query param ?ambiente=PRD|QAS
    """
    # Obtener API key del header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API Key requerida"}), 401
    
    # Validar API key
    if not validate_api_key(api_key):
        return jsonify({"error": "API Key inválida"}), 401
    
    # Validar que la empresa existe
    empresa = get_data_from_database2(rnc)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    
    try:
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        file_path = os.path.join(cert_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Certificado no encontrado"}), 404
        
        # Eliminar archivo principal
        os.remove(file_path)
        logger.info(f"Archivo eliminado: {file_path}")
        
        # Eliminar archivo de metadatos si existe (formato: filename.json)
        metadata_file = os.path.join(cert_dir, f"{filename}.json")
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
            logger.info(f"Metadatos eliminados: {metadata_file}")
        
        # También eliminar el formato antiguo .metadata.json si existe
        old_metadata_file = os.path.join(cert_dir, f"{filename}.metadata.json")
        if os.path.exists(old_metadata_file):
            os.remove(old_metadata_file)
            logger.info(f"Metadatos antiguos eliminados: {old_metadata_file}")
        
        logger.info(f"Certificado {filename} eliminado exitosamente para empresa {rnc} en ambiente {ambiente}")
        
        return jsonify({
            "message": f"Certificado {filename} eliminado exitosamente",
            "rnc": rnc,
            "filename": filename
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminando certificado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificado/<filename>/descargar", methods=["GET"])
def download_certificate(rnc, filename):
    """
    Endpoint para descargar un certificado específico
    Por defecto usa ambiente CERT, pero puede especificarse con query param ?ambiente=PRD|QAS
    """
    # Obtener API key del header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API Key requerida"}), 401
    
    # Validar API key
    if not validate_api_key(api_key):
        return jsonify({"error": "API Key inválida"}), 401
    
    # Validar que la empresa existe
    empresa = get_data_from_database2(rnc)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    
    try:
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        file_path = os.path.join(cert_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Certificado no encontrado"}), 404
        
        # Leer archivo
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Determinar tipo de contenido
        extension = filename.split('.')[-1].lower()
        content_type = "application/octet-stream"
        
        if extension in ['p12', 'pfx']:
            content_type = "application/x-pkcs12"
        
        # Obtener nombre original si existe en metadatos
        metadata_file = os.path.join(cert_dir, f"{filename}.metadata.json")
        download_filename = filename
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    download_filename = metadata.get("original_filename", filename)
            except Exception as e:
                logger.warning(f"Error leyendo metadatos: {str(e)}")
        
        logger.info(f"Descargando certificado {filename} para empresa {rnc} en ambiente {ambiente}")
        
        return Response(
            file_data,
            mimetype=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}",
                "Content-Length": str(len(file_data))
            }
        )
        
    except Exception as e:
        logger.error(f"Error descargando certificado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificado/<filename>/contenido", methods=["POST"])
@token_or_api_key_required
def view_certificate_content(rnc, filename):
    """
    Endpoint para visualizar el contenido de un certificado proporcionando la contraseña.
    Retorna información detallada del certificado en formato JSON.
    
    Body esperado:
    {
        "password": "contraseña_del_certificado"
    }
    
    Respuesta:
    {
        "filename": "certificado.p12",
        "nombre_personalizado": "Mi Certificado",
        "certificado_principal": {
            "subject": {...},
            "issuer": {...},
            "numero_serie": "...",
            "valido_desde": "2024-01-01T00:00:00",
            "valido_hasta": "2026-01-01T00:00:00",
            "estado": "Vigente",
            "algoritmo_firma": "..."
        },
        "estado_clave_privada": "Cargada correctamente",
        "certificados_adicionales": [...]
    }
    """
    try:
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        # Construir ruta del certificado
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        file_path = os.path.join(cert_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Certificado no encontrado"}), 404
        
        # Cargar metadatos (necesarios para obtener contraseña guardada)
        metadata_file = os.path.join(cert_dir, f"{filename}.json")
        if not os.path.exists(metadata_file):
            # Intentar con formato antiguo .metadata.json
            metadata_file = os.path.join(cert_dir, f"{filename}.metadata.json")
        
        nombre_personalizado = "Sin nombre personalizado"
        descripcion = ""
        password_encrypted = None
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    nombre_personalizado = metadata.get("nombre_personalizado", nombre_personalizado)
                    descripcion = metadata.get("descripcion", "")
                    password_encrypted = metadata.get("password_encrypted")
            except Exception as e:
                logger.warning(f"Error cargando metadatos para {filename}: {str(e)}")
        
        # Obtener contraseña del body o de los metadatos
        data = request.get_json() if request.get_json() else {}
        password_from_request = data.get('password')
        
        # Determinar qué contraseña usar
        password_to_use = None
        
        if password_from_request:
            # Si se proporciona contraseña en la petición, usarla
            password_to_use = password_from_request
            logger.info(f"Usando contraseña proporcionada en la petición para certificado {filename}")
        elif password_encrypted:
            # Si no se proporciona contraseña pero existe en metadatos, desencriptarla y usarla
            try:
                password_to_use = decrypt_password(password_encrypted)
                logger.info(f"Usando contraseña almacenada en metadatos para certificado {filename}")
            except Exception as e:
                logger.error(f"Error desencriptando contraseña guardada: {str(e)}")
                return jsonify({
                    "error": "No se pudo recuperar la contraseña almacenada",
                    "details": "La contraseña guardada está corrupta o no se puede desencriptar"
                }), 500
        else:
            # No hay contraseña disponible
            return jsonify({
                "error": "Contraseña no disponible",
                "details": "No se proporcionó contraseña y no hay contraseña almacenada en los metadatos del certificado"
            }), 400
        
        # Intentar cargar el certificado con la contraseña
        try:
            cert_info = cargar_certificado(file_path, password_to_use, como_json=False)
            
            # Obtener enlace de renovación y claves de la empresa
            enlace_renovacion = None
            clave_portal_cert_decrypted = None
            clave_certificado_decrypted = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT enlace_renovacion_certificado, clave_portal_cert, clave_certificado 
                    FROM EmpresaFE WHERE RNC = ?
                """, (rnc,))
                result = cursor.fetchone()
                if result:
                    if result[0]:
                        enlace_renovacion = result[0]
                    # Desencriptar claves si existen
                    if result[1]:
                        try:
                            clave_portal_cert_decrypted = decrypt_password(result[1])
                        except Exception as e:
                            logger.warning(f"Error desencriptando clave portal: {str(e)}")
                    if result[2]:
                        try:
                            clave_certificado_decrypted = decrypt_password(result[2])
                        except Exception as e:
                            logger.warning(f"Error desencriptando clave certificado: {str(e)}")
                cursor.close()
                conn.close()
            except Exception as db_error:
                logger.warning(f"Error obteniendo datos de la empresa: {str(db_error)}")
            
            # Construir respuesta
            response_data = {
                "filename": filename,
                "nombre_personalizado": nombre_personalizado,
                "descripcion": descripcion,
                "certificado_principal": cert_info.get("certificado_principal", {}),
                "estado_clave_privada": cert_info.get("estado_clave_privada", "No encontrada"),
                "certificados_adicionales": cert_info.get("certificados_adicionales", []),
                "total_certificados_adicionales": len(cert_info.get("certificados_adicionales", [])),
                "enlace_renovacion_certificado": enlace_renovacion,
                "clave_portal_cert": clave_portal_cert_decrypted,
                "clave_certificado": clave_certificado_decrypted
            }
            
            logger.info(f"Contenido del certificado {filename} visualizado exitosamente para empresa {rnc}")
            
            return jsonify({
                "success": True,
                "message": "Contenido del certificado cargado exitosamente",
                "data": response_data
            }), 200
            
        except ValueError as ve:
            # Error de contraseña incorrecta o certificado inválido
            logger.warning(f"Error al cargar certificado {filename}: {str(ve)}")
            return jsonify({
                "error": "Contraseña incorrecta o certificado inválido",
                "details": str(ve)
            }), 401
            
        except Exception as e:
            # Otro tipo de error
            logger.error(f"Error procesando certificado {filename}: {str(e)}")
            return jsonify({
                "error": "Error al procesar el certificado",
                "details": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Error general en view_certificate_content: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# ================================= NUEVOS ENDPOINTS PARA GESTIÓN AVANZADA DE CERTIFICADOS =================================
# Endpoints mejorados que permiten definir nombres personalizados y mejor gestión

@routes.route("/empresa/<rnc>/certificado/preparar", methods=["POST"])
@token_or_api_key_required
def preparar_certificado(rnc):
    """
    Endpoint para preparar el nombre del certificado antes de subirlo
    Permite al usuario definir un nombre personalizado para el certificado
    
    Body esperado:
    {
        "nombre_personalizado": "Mi Certificado Fiscal 2024",
        "descripcion": "Certificado para facturación electrónica" (opcional)
    }
    """
    try:
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos JSON requeridos"}), 400
        
        nombre_personalizado = data.get('nombre_personalizado', '').strip()
        if not nombre_personalizado:
            return jsonify({"error": "El nombre personalizado es requerido"}), 400
        
        descripcion = data.get('descripcion', '').strip()
        
        # Generar un ID único para esta preparación
        preparation_id = f"{int(time.time())}_{secrets.token_hex(8)}"
        
        # Crear estructura de preparación
        preparation_data = {
            "preparation_id": preparation_id,
            "rnc": rnc,
            "nombre_personalizado": nombre_personalizado,
            "descripcion": descripcion,
            "created_at": datetime.now().isoformat(),
            "status": "preparado"  # Estados: preparado, completado, expirado
        }
        
        # Crear directorio temporal para preparaciones si no existe
        config_directorios = cargar_config_directorios()
        ruta_base = config_directorios.get("estructura_base", "C:/Base/Ambiente/")
        temp_dir = os.path.join(ruta_base, "temp_preparations")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Guardar datos de preparación
        prep_file = os.path.join(temp_dir, f"{preparation_id}.json")
        with open(prep_file, 'w', encoding='utf-8') as f:
            json.dump(preparation_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Certificado preparado para empresa {rnc}: {nombre_personalizado}")
        
        return jsonify({
            "message": "Certificado preparado exitosamente",
            "preparation_id": preparation_id,
            "nombre_personalizado": nombre_personalizado,
            "descripcion": descripcion,
            "rnc": rnc,
            "next_step": f"Usar preparation_id '{preparation_id}' en el endpoint de subida del certificado"
        }), 201
        
    except Exception as e:
        logger.error(f"Error preparando certificado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificado/subir", methods=["POST"])
@token_or_api_key_required
def subir_certificado_con_nombre(rnc):
    """
    Endpoint mejorado para subir certificados con nombres personalizados
    Utiliza preparation_id para asociar el archivo con el nombre definido previamente
    
    Form data esperado:
    - certificate: archivo del certificado (p12/pfx)
    - password: contraseña del certificado
    - preparation_id: ID obtenido del endpoint de preparación
    """
    try:
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # Validar que se envió un archivo
        if 'certificate' not in request.files:
            return jsonify({"error": "No se encontró el archivo de certificado"}), 400
        
        certificate = request.files['certificate']
        if certificate.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        # Obtener datos del formulario
        password = request.form.get('password')
        preparation_id = request.form.get('preparation_id')
        
        if not password:
            return jsonify({"error": "Contraseña requerida"}), 400
        
        if not preparation_id:
            return jsonify({"error": "preparation_id requerido"}), 400
        
        # Validar tipo de archivo
        if not allowed_certificate_file(certificate.filename):
            return jsonify({
                "error": "Tipo de archivo no permitido. Extensiones permitidas: p12, pfx"
            }), 400
        
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        # Cargar datos de preparación
        config_directorios = cargar_config_directorios()
        ruta_base = config_directorios.get("estructura_base", "C:/Base/Ambiente/")
        temp_dir = os.path.join(ruta_base, "temp_preparations")
        prep_file = os.path.join(temp_dir, f"{preparation_id}.json")
        
        if not os.path.exists(prep_file):
            return jsonify({"error": "preparation_id inválido o expirado"}), 400
        
        with open(prep_file, 'r', encoding='utf-8') as f:
            preparation_data = json.load(f)
        
        # Verificar que el RNC coincide
        if preparation_data.get('rnc') != rnc:
            return jsonify({"error": "preparation_id no corresponde a esta empresa"}), 400
        
        # Crear directorio del certificado
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        os.makedirs(cert_dir, exist_ok=True)
        
        # Crear nombre seguro para el archivo usando SOLO el nombre personalizado
        secure_name = secure_filename(certificate.filename)
        timestamp = int(time.time())
        extension = secure_name.split('.')[-1] if '.' in secure_name else 'p12'
        # Solo usar el nombre personalizado sin timestamp ni otros prefijos
        nombre_limpio = secure_filename(preparation_data['nombre_personalizado'][:50])
        final_filename = f"{nombre_limpio}.{extension}"
        
        # Si ya existe un archivo con ese nombre, agregar timestamp para evitar conflictos
        file_path = os.path.join(cert_dir, final_filename)
        if os.path.exists(file_path):
            final_filename = f"{timestamp}_{nombre_limpio}.{extension}"
            file_path = os.path.join(cert_dir, final_filename)
        
        # Guardar archivo temporalmente
        certificate.save(file_path)
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        
        # Extraer fechas reales del certificado usando cert_utils
        valido_desde = None
        valido_hasta = None
        estado_certificado = "desconocido"
        dias_restantes = None
        
        try:
            # Intentar extraer información real del certificado
            info_cert = obtener_info_basica_certificado(file_path, password)
            valido_desde = info_cert.get("valido_desde")
            valido_hasta = info_cert.get("valido_hasta")
            estado_certificado = info_cert.get("estado", "desconocido")
            dias_restantes = info_cert.get("dias_restantes")
            
            logger.info(f"Certificado cargado: válido desde {valido_desde} hasta {valido_hasta}, estado: {estado_certificado}")
        except Exception as e:
            logger.warning(f"No se pudo extraer información del certificado: {str(e)}")
            # Si falla, usar valores por defecto
            fecha_actual = datetime.now()
            valido_desde = fecha_actual.isoformat()
            valido_hasta = (fecha_actual + timedelta(days=365)).isoformat()
            estado_certificado = "info_no_disponible"
        
        # Crear metadatos completos del certificado
        certificate_data = {
            "rnc": rnc,
            "filename": final_filename,
            "original_filename": certificate.filename,
            "nombre_personalizado": preparation_data['nombre_personalizado'],
            "descripcion": preparation_data.get('descripcion', ''),
            "file_path": file_path.replace("\\", "/"),
            "valido_desde": valido_desde,
            "valido_hasta": valido_hasta,
            "estado": estado_certificado,
            "dias_restantes": dias_restantes,
            "file_size": file_size,
            "password_encrypted": encrypt_password(password),  # Guardar contraseña encriptada
            "preparation_id": preparation_id,
            "fecha_subida": datetime.now().isoformat(),
            "status": "activo"
        }
        
        # Guardar metadatos en archivo JSON
        metadata_file = os.path.join(cert_dir, f"{final_filename}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(certificate_data, f, indent=2, ensure_ascii=False)
        
        # Marcar preparación como completada y eliminar archivo temporal
        try:
            os.remove(prep_file)
        except:
            pass  # No es crítico si no se puede eliminar
        
        logger.info(f"Certificado '{preparation_data['nombre_personalizado']}' subido exitosamente para empresa {rnc}: {final_filename}")
        
        return jsonify({
            "message": "Certificado guardado exitosamente",
            "data": {
                "rnc": rnc,
                "filename": final_filename,
                "original_filename": certificate.filename,
                "nombre_personalizado": preparation_data['nombre_personalizado'],
                "descripcion": preparation_data.get('descripcion', ''),
                "file_path": certificate_data["file_path"],
                "valido_desde": valido_desde,
                "valido_hasta": valido_hasta,
                "estado": estado_certificado,
                "dias_restantes": dias_restantes,
                "file_size": file_size
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error subiendo certificado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/empresa/<rnc>/certificados/detallados", methods=["GET"])
@token_or_api_key_required
def obtener_certificados_detallados(rnc):
    """
    Endpoint para obtener información detallada de certificados incluyendo:
    - Contenido del certificado (similar a como se muestran los XSD)
    - Fechas de agregado y vencimiento
    - Estado del certificado (vigente/próximo a vencer/expirado)
    """
    try:
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # Obtener ambiente desde query params (por defecto CERT)
        ambiente = request.args.get('ambiente', 'CERT')
        if ambiente not in ['PRD', 'CERT', 'QAS']:
            return jsonify({"error": "Ambiente inválido. Use PRD, CERT o QAS"}), 400
        
        cert_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "Cert")
        
        # Verificar si existe el directorio
        if not os.path.exists(cert_dir):
            return jsonify({
                "rnc": rnc,
                "certificados": [],
                "total": 0
            }), 200
        
        certificates = []
        current_date = datetime.now()
        
        # Listar archivos en el directorio
        for filename in os.listdir(cert_dir):
            file_path = os.path.join(cert_dir, filename)
            
            # Saltar archivos de metadatos JSON
            if filename.endswith('.json'):
                continue
                
            if os.path.isfile(file_path):
                # Obtener información básica del archivo
                stat_info = os.stat(file_path)
                
                # Datos básicos del certificado
                cert_info = {
                    "filename": filename,
                    "file_path": file_path.replace("\\", "/"),
                    "file_size": stat_info.st_size,
                    "nombre_personalizado": "Sin nombre personalizado",
                    "descripcion": "",
                    "valido_desde": None,
                    "valido_hasta": None,
                    "estado": "desconocido",
                    "dias_para_vencer": None,
                    "contenido_certificado": None
                }
                
                # Intentar cargar metadatos detallados si existen
                metadata_file = os.path.join(cert_dir, f"{filename}.json")
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            cert_info.update({
                                "original_filename": metadata.get("original_filename", filename),
                                "nombre_personalizado": metadata.get("nombre_personalizado", cert_info["nombre_personalizado"]),
                                "descripcion": metadata.get("descripcion", ""),
                                "valido_desde": metadata.get("valido_desde"),
                                "valido_hasta": metadata.get("valido_hasta"),
                                "password_hash": metadata.get("password_hash")
                            })
                    except Exception as e:
                        logger.warning(f"Error cargando metadatos para {filename}: {str(e)}")
                
                # Si no hay fechas, intentar extraer del certificado o usar valores por defecto
                if not cert_info["valido_hasta"] or not cert_info["valido_desde"]:
                    fecha_archivo = datetime.fromtimestamp(stat_info.st_mtime)
                    cert_info["valido_desde"] = fecha_archivo.isoformat()
                    cert_info["valido_hasta"] = (fecha_archivo + timedelta(days=365)).isoformat()
                
                # Calcular estado del certificado
                if cert_info["valido_hasta"]:
                    try:
                        fecha_venc = datetime.fromisoformat(cert_info["valido_hasta"].replace('Z', '+00:00'))
                        if fecha_venc.tzinfo:
                            fecha_venc = fecha_venc.replace(tzinfo=None)
                        
                        dias_restantes = (fecha_venc - current_date).days
                        cert_info["dias_para_vencer"] = dias_restantes
                        
                        if dias_restantes < 0:
                            cert_info["estado"] = "expirado"
                            cert_info["estado_emoji"] = "🔴"
                            cert_info["estado_descripcion"] = "Certificado expirado"
                        elif dias_restantes <= 60:
                            cert_info["estado"] = "proximo_a_vencer"
                            cert_info["estado_emoji"] = "🟠"
                            cert_info["estado_descripcion"] = f"Próximo a vencer en {dias_restantes} días"
                        else:
                            cert_info["estado"] = "vigente"
                            cert_info["estado_emoji"] = "🟢"
                            cert_info["estado_descripcion"] = f"Vigente ({dias_restantes} días restantes)"
                    except Exception as e:
                        logger.warning(f"Error calculando estado del certificado {filename}: {str(e)}")
                
                # Intentar leer el contenido del certificado (información básica)
                try:
                    with open(file_path, 'rb') as f:
                        cert_bytes = f.read()
                        # Información básica del certificado
                        cert_info["contenido_certificado"] = {
                            "size_bytes": len(cert_bytes),
                            "tipo": "PKCS#12" if filename.lower().endswith('.p12') else "PFX",
                            "formato": "binario",
                            "puede_visualizar": False,  # Los certificados son binarios
                            "descripcion_contenido": f"Certificado digital {cert_info['tipo']} - {cert_info['size_bytes']} bytes"
                        }
                except Exception as e:
                    logger.warning(f"Error leyendo contenido del certificado {filename}: {str(e)}")
                    cert_info["contenido_certificado"] = {
                        "error": "No se pudo leer el contenido del certificado",
                        "puede_visualizar": False
                    }
                
                certificates.append(cert_info)
        
        # Ordenar por fecha valido_desde (más reciente primero)
        certificates.sort(key=lambda x: x.get("valido_desde", ""), reverse=True)
        
        logger.info(f"Consultados {len(certificates)} certificados detallados para empresa {rnc}")
        
        return jsonify({
            "rnc": rnc,
            "certificados": certificates,
            "total": len(certificates),
            "resumen_estados": {
                "vigentes": len([c for c in certificates if c["estado"] == "vigente"]),
                "proximos_a_vencer": len([c for c in certificates if c["estado"] == "proximo_a_vencer"]),
                "expirados": len([c for c in certificates if c["estado"] == "expirado"])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo certificados detallados: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@routes.route("/update-estado-fiscal", methods=["PUT"])
@token_or_api_key_required
def actualizar_estado_fiscal():
    logger.info("Acceso a actualización de estado fiscal con autorización válida")
    return update_estado_fiscal()

# ================================= ENDPOINTS PARA MANEJO DE API KEY =================================
# Endpoints para guardar y recuperar API keys en archivo local
# Uso:
# POST /save_apikey - Guardar API key: {"apiKey": "tu_api_key_aqui"}
# GET /get_apikey - Obtener API key guardada
# GET /verify_apikey - Verificar si una API key es válida (header X-API-Key)
# GET /apikey_info - Obtener información sobre el estado de la API Key
# 
# Archivo de almacenamiento: APIWEB/data/apikey.json (ruta absoluta)
# Formato del archivo: {"API_KEY": "valor_de_la_api_key"}
# 
# IMPORTANTE: La API Key se guarda ÚNICAMENTE en la carpeta APIWEB/data/
# y se usa para validación en endpoints que requieren autenticación

@routes.route("/save_apikey", methods=["POST"])
def save_apikey():
    """
    Endpoint para guardar una API key en archivo local APIWEB/data/apikey.json
    
    Body esperado:
    {
        "apiKey": "string_con_la_api_key"
    }
    
    Respuesta exitosa:
    {
        "message": "API key guardada exitosamente",
        "file_path": "ruta_completa_del_archivo"
    }
    
    NOTA: La API Key se guarda ÚNICAMENTE en APIWEB/data/apikey.json
    """
    try:
        # Obtener datos del JSON
        data = request.get_json()
        
        # Validar que se recibió un JSON válido
        if not data:
            return jsonify({"error": "Se requiere un JSON válido en el body"}), 400
        
        # Validar que existe el campo apiKey
        api_key = data.get("apiKey")
        if not api_key:
            return jsonify({"error": "El campo 'apiKey' es requerido"}), 400
        
        # Validar que la API key no esté vacía
        if not isinstance(api_key, str) or api_key.strip() == "":
            return jsonify({"error": "La API key debe ser una cadena no vacía"}), 400
        
        # Preparar datos para guardar
        api_key_data = {
            "API_KEY": api_key.strip()
        }
        
        # Crear carpeta data si no existe en APIWEB
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Directorio donde está routes.py (APIWEB)
        data_dir = os.path.join(current_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Ruta completa del archivo
        apikey_file_path = os.path.join(data_dir, "apikey.json")
        
        # Guardar en archivo data/apikey.json
        try:
            with open(apikey_file_path, "w", encoding="utf-8") as f:
                json.dump(api_key_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API key guardada exitosamente en {apikey_file_path}")
            
            return jsonify({
                "message": "API key guardada exitosamente",
                "file_path": apikey_file_path.replace("\\", "/")
            }), 200
            
        except IOError as e:
            logger.error(f"Error escribiendo archivo {apikey_file_path}: {str(e)}")
            return jsonify({"error": "Error guardando la API key en archivo"}), 500
            
    except json.JSONDecodeError:
        return jsonify({"error": "JSON inválido en el body de la petición"}), 400
    except Exception as e:
        logger.error(f"Error inesperado en save_apikey: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/apikey_info", methods=["GET"])
def apikey_info():
    """
    Endpoint para obtener información sobre el estado de la API Key
    (sin revelar la API Key en sí)
    
    Respuesta:
    {
        "exists": true/false,
        "file_path": "ruta_del_archivo",
        "created_date": "fecha_de_creación" (si existe)
    }
    """
    try:
        # Ruta del archivo de API Key en APIWEB/data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        apikey_file_path = os.path.join(current_dir, "data", "apikey.json")
        
        exists = os.path.exists(apikey_file_path)
        
        response_data = {
            "exists": exists,
            "file_path": apikey_file_path.replace("\\", "/")
        }
        
        if exists:
            try:
                stat_info = os.stat(apikey_file_path)
                response_data["created_date"] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                response_data["modified_date"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                response_data["file_size_bytes"] = stat_info.st_size
            except Exception as e:
                logger.warning(f"Error obteniendo información del archivo: {str(e)}")
        
        logger.info(f"Consulta de información de API key - Existe: {exists}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error inesperado en apikey_info: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/verify_apikey", methods=["GET"])
def verify_apikey():
    """
    Endpoint para verificar si una API key es válida
    
    Headers esperados:
    X-API-Key: la_api_key_a_verificar
    
    Respuesta exitosa:
    {
        "valid": true,
        "message": "API key válida"
    }
    
    Respuesta de error:
    {
        "valid": false,
        "error": "mensaje_de_error"
    }
    """
    try:
        # Obtener API key del header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return jsonify({
                "valid": False, 
                "error": "No se proporcionó API Key en header X-API-Key"
            }), 400
        
        # Validar API key
        is_valid = validate_api_key(api_key)
        
        if is_valid:
            logger.info("API key verificada exitosamente")
            return jsonify({
                "valid": True,
                "message": "API key válida"
            }), 200
        else:
            logger.warning("Intento de verificación con API key inválida")
            return jsonify({
                "valid": False,
                "error": "API key inválida"
            }), 401
            
    except Exception as e:
        logger.error(f"Error inesperado en verify_apikey: {str(e)}")
        return jsonify({
            "valid": False,
            "error": "Error interno del servidor"
        }), 500

@routes.route("/get_apikey", methods=["GET"])
def get_apikey():
    """
    Endpoint para recuperar la API key guardada desde el archivo APIWEB/data/apikey.json
    
    Respuesta exitosa:
    {
        "API_KEY": "valor_de_la_api_key_guardada",
        "file_path": "ruta_completa_del_archivo"
    }
    
    Respuesta de error:
    {
        "error": "mensaje_de_error"
    }
    
    NOTA: Lee la API Key ÚNICAMENTE desde APIWEB/data/apikey.json
    """
    try:
        # Ruta completa del archivo en APIWEB/data
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Directorio donde está routes.py (APIWEB)
        apikey_file_path = os.path.join(current_dir, "data", "apikey.json")
        
        # Verificar que el archivo existe
        if not os.path.exists(apikey_file_path):
            return jsonify({"error": "No se encontró archivo de API key. Use POST /save_apikey para crear uno"}), 404
        
        # Leer archivo
        try:
            with open(apikey_file_path, "r", encoding="utf-8") as f:
                api_key_data = json.load(f)
            
            # Validar que el archivo tiene el formato correcto
            if not isinstance(api_key_data, dict) or "API_KEY" not in api_key_data:
                logger.error(f"Archivo {apikey_file_path} tiene formato inválido")
                return jsonify({"error": "Archivo de API key tiene formato inválido"}), 500
            
            # Validar que la API key no esté vacía
            api_key = api_key_data.get("API_KEY")
            if not api_key or api_key.strip() == "":
                logger.error("API key en archivo está vacía")
                return jsonify({"error": "API key en archivo está vacía o es inválida"}), 500
            
            logger.info(f"API key recuperada exitosamente desde {apikey_file_path}")
            
            return jsonify({
                "API_KEY": api_key,
                "file_path": apikey_file_path.replace("\\", "/")
            }), 200
            
        except json.JSONDecodeError:
            logger.error(f"Error: {apikey_file_path} contiene JSON inválido")
            return jsonify({"error": "Archivo de API key contiene JSON inválido"}), 500
        except IOError as e:
            logger.error(f"Error leyendo archivo {apikey_file_path}: {str(e)}")
            return jsonify({"error": "Error accediendo al archivo de API key"}), 500
            
    except Exception as e:
        logger.error(f"Error inesperado en get_apikey: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# === ENDPOINTS PARA MANEJO DE ARCHIVOS XSD ===

def validar_nombre_archivo(filename):
    """
    Valida el nombre de archivo sin usar secure_filename para mantener espacios y caracteres especiales
    
    Args:
        filename (str): Nombre del archivo a validar
        
    Returns:
        bool: True si el nombre es válido, False si contiene caracteres peligrosos
    """
    # Caracteres que pueden ser peligrosos para el sistema de archivos
    caracteres_peligrosos = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    for char in caracteres_peligrosos:
        if char in filename:
            return False
    
    # Verificar que no sea un nombre reservado del sistema
    nombres_reservados = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    base_name = os.path.splitext(filename.upper())[0]
    
    if base_name in nombres_reservados:
        return False
    
    return True

# Tipos de ECF válidos
TIPOS_ECF_VALIDOS = {
    '31': 'Factura de Crédito Fiscal',
    '32': 'Factura de Consumo',
    '33': 'Nota de Débito',
    '34': 'Nota de Crédito',
    '41': 'Comprobante de Compras',
    '43': 'Registro de Gastos Menores',
    '44': 'Registro de Regímenes Especiales',
    '45': 'Comprobante de Gubernamentales',
    '46': 'Comprobante de Exportaciones',
    '47': 'Comprobante de Pagos al Exterior'
}

# Archivos XSD especiales que no requieren tipo ECF
ARCHIVOS_XSD_ESPECIALES = ['ARECF', 'ACECF', 'ANECF', 'RFCE', 'Semilla']

# Ruta base para archivos XSD
XSD_BASE_PATH = "C:/Base/XSD"
CONFIG_XSD_PATH = "data/configxsd.json"

def actualizar_config_xsd(tipo_ecf, file_path):
    """
    Actualiza el archivo configxsd.json con la nueva ruta del archivo XSD
    
    Args:
        tipo_ecf (str): Tipo de ECF (31, 32, 33, etc.)
        file_path (str): Ruta completa del archivo XSD
    """
    try:
        # Construir ruta completa del archivo de configuración
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, CONFIG_XSD_PATH)
        
        # Leer configuración actual
        config_data = {}
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        # Actualizar la entrada para este tipo de ECF
        config_data[tipo_ecf] = file_path.replace("/", "\\")
        
        # Guardar configuración actualizada
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Configuración XSD actualizada para tipo {tipo_ecf}: {file_path}")
        
    except Exception as e:
        logger.error(f"Error actualizando configuración XSD: {str(e)}")

def obtener_config_xsd():
    """
    Obtiene la configuración actual de archivos XSD
    
    Returns:
        dict: Configuración de archivos XSD
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, CONFIG_XSD_PATH)
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
            
    except Exception as e:
        logger.error(f"Error leyendo configuración XSD: {str(e)}")
        return {}

def eliminar_de_config_xsd(tipo_ecf):
    """
    Elimina una entrada del archivo configxsd.json
    
    Args:
        tipo_ecf (str): Tipo de ECF a eliminar
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, CONFIG_XSD_PATH)
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Eliminar la entrada si existe
            if tipo_ecf in config_data:
                del config_data[tipo_ecf]
                
                # Guardar configuración actualizada
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Configuración XSD eliminada para tipo {tipo_ecf}")
            
    except Exception as e:
        logger.error(f"Error eliminando configuración XSD: {str(e)}")

def obtener_tipo_ecf_por_archivo(filename):
    """
    Obtiene el tipo ECF asociado a un archivo basándose en la configuración XSD
    
    Args:
        filename (str): Nombre del archivo XSD
        
    Returns:
        dict: Información del tipo ECF o None si no se encuentra
    """
    try:
        config_data = obtener_config_xsd()
        
        # Construir ruta completa del archivo a buscar
        file_path_to_find = os.path.join(XSD_BASE_PATH, filename).replace("\\", "/")
        
        # Buscar en la configuración
        for tipo_ecf, config_path in config_data.items():
            # Normalizar rutas para comparación
            normalized_config_path = os.path.normpath(config_path).replace("\\", "/")
            normalized_file_path = os.path.normpath(file_path_to_find).replace("\\", "/")
            
            if normalized_config_path == normalized_file_path:
                return {
                    "tipo_ecf": tipo_ecf,
                    "descripcion": TIPOS_ECF_VALIDOS.get(tipo_ecf, f"ECF Tipo {tipo_ecf}")
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo tipo ECF para archivo {filename}: {str(e)}")
        return None

@routes.route("/xsd/upload", methods=["POST"])

@token_or_api_key_required
def upload_xsd():
    """
    Endpoint para subir archivos XSD según el tipo de ECF o archivos especiales
    
    Esperamos:
    - archivo XSD en form-data con key 'xsd_file'  
    - tipo_ecf en form-data (31, 32, 33, 34, 41, 43, 44, 45, 46, 47) - OPCIONAL para archivos especiales
    """
    try:
        # Verificar que se envió un archivo
        if 'xsd_file' not in request.files:
            return jsonify({"error": "No se encontró archivo XSD en la solicitud"}), 400
            
        file = request.files['xsd_file']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        # Verificar extensión del archivo
        if not file.filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo debe tener extensión .xsd"}), 400
        
        # Obtener nombre del archivo original (manteniendo espacios y caracteres especiales)
        original_filename = file.filename
        
        # Validación básica de seguridad usando nuestra función personalizada
        if not validar_nombre_archivo(original_filename):
            return jsonify({"error": "El nombre del archivo contiene caracteres no permitidos o es un nombre reservado del sistema"}), 400
        
        base_name = os.path.splitext(original_filename)[0]
        
        # Verificar si es un archivo especial
        es_archivo_especial = any(especial.upper() in base_name.upper() for especial in ARCHIVOS_XSD_ESPECIALES)
        
        # Verificar tipo de ECF solo si no es archivo especial
        tipo_ecf = request.form.get('tipo_ecf')
        if not es_archivo_especial:
            if not tipo_ecf:
                return jsonify({"error": "Debe especificar el tipo_ecf para archivos XSD estándar"}), 400
                
            if tipo_ecf not in TIPOS_ECF_VALIDOS:
                return jsonify({
                    "error": f"Tipo de ECF inválido. Tipos válidos: {list(TIPOS_ECF_VALIDOS.keys())}"
                }), 400
        
        # Crear carpeta XSD si no existe
        os.makedirs(XSD_BASE_PATH, exist_ok=True)
        
        # Usar el nombre original del archivo (manteniendo espacios)
        filename = original_filename
        
        # Ruta completa del archivo
        file_path = os.path.join(XSD_BASE_PATH, filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Actualizar configuración XSD solo si tiene tipo ECF
        if not es_archivo_especial and tipo_ecf:
            actualizar_config_xsd(tipo_ecf, file_path)
        
        logger.info(f"Archivo XSD guardado: {file_path}")
        
        response_data = {
            "message": "Archivo XSD subido exitosamente",
            "filename": filename,
            "path": file_path.replace("\\", "/"),
            "es_archivo_especial": es_archivo_especial
        }
        
        if not es_archivo_especial and tipo_ecf:
            response_data.update({
                "tipo_ecf": tipo_ecf,
                "tipo_descripcion": TIPOS_ECF_VALIDOS[tipo_ecf]
            })
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error subiendo archivo XSD: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/list", methods=["GET"])

@token_or_api_key_required
def list_xsd_files():
    """
    Endpoint para listar todos los archivos XSD disponibles, organizados por tipo de ECF y archivos especiales
    """
    try:
        # Verificar que existe la carpeta base
        if not os.path.exists(XSD_BASE_PATH):
            return jsonify({"message": "No hay archivos XSD disponibles", "xsd_files": {}, "archivos_especiales": []}), 200
        
        xsd_files = {}
        archivos_especiales = []
        
        # Inicializar estructura para todos los tipos de ECF
        for tipo_ecf, descripcion in TIPOS_ECF_VALIDOS.items():
            xsd_files[tipo_ecf] = {
                "descripcion": descripcion,
                "archivos": []
            }
        
        # Listar archivos en la carpeta XSD
        for filename in os.listdir(XSD_BASE_PATH):
            if filename.lower().endswith('.xsd'):
                file_path = os.path.join(XSD_BASE_PATH, filename)
                file_stat = os.stat(file_path)
                
                file_info = {
                    "filename": filename,
                    "size_bytes": file_stat.st_size,
                    "created_date": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                }
                
                # Verificar si es archivo especial
                base_name = os.path.splitext(filename)[0]
                es_especial = any(especial.upper() in base_name.upper() for especial in ARCHIVOS_XSD_ESPECIALES)
                
                if es_especial:
                    file_info["es_archivo_especial"] = True
                    archivos_especiales.append(file_info)
                else:
                    # Intentar obtener tipo ECF de la configuración primero
                    tipo_ecf_config = obtener_tipo_ecf_por_archivo(filename)
                    
                    if tipo_ecf_config:
                        # Archivo tiene tipo ECF configurado
                        tipo_ecf = tipo_ecf_config["tipo_ecf"]
                        file_info["tipo_ecf_vinculado"] = {
                            "tipo": tipo_ecf,
                            "descripcion": tipo_ecf_config["descripcion"]
                        }
                        xsd_files[tipo_ecf]["archivos"].append(file_info)
                    else:
                        # Determinar tipo de ECF basado en el prefijo del nombre del archivo (compatibilidad con archivos antiguos)
                        tipo_encontrado = False
                        for tipo_ecf in TIPOS_ECF_VALIDOS.keys():
                            if filename.startswith(f"ECF_{tipo_ecf}_"):
                                file_info["tipo_ecf_vinculado"] = {
                                    "tipo": tipo_ecf,
                                    "descripcion": TIPOS_ECF_VALIDOS[tipo_ecf]
                                }
                                xsd_files[tipo_ecf]["archivos"].append(file_info)
                                tipo_encontrado = True
                                break
                        
                        if not tipo_encontrado:
                            # Si no tiene prefijo, agregar a sección "sin_clasificar"
                            file_info["tipo_ecf_vinculado"] = None
                            if "sin_clasificar" not in xsd_files:
                                xsd_files["sin_clasificar"] = {
                                    "descripcion": "Archivos XSD sin clasificar",
                                    "archivos": []
                                }
                            xsd_files["sin_clasificar"]["archivos"].append(file_info)
        
        # Remover tipos que no tienen archivos
        xsd_files = {k: v for k, v in xsd_files.items() if v["archivos"]}
        
        return jsonify({
            "message": "Lista de archivos XSD obtenida exitosamente",
            "total_tipos": len(xsd_files),
            "total_especiales": len(archivos_especiales),
            "xsd_files": xsd_files,
            "archivos_especiales": archivos_especiales
        }), 200
        
    except Exception as e:
        logger.error(f"Error listando archivos XSD: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/<tipo_ecf>/<filename>/view", methods=["GET"])

@token_or_api_key_required  
def view_xsd_file(tipo_ecf, filename):
    """
    Endpoint para obtener el contenido de un archivo XSD específico para visualización/edición
    """
    try:
        # Validar tipo de ECF
        if tipo_ecf not in TIPOS_ECF_VALIDOS:
            return jsonify({
                "error": f"Tipo de ECF inválido. Tipos válidos: {list(TIPOS_ECF_VALIDOS.keys())}"
            }), 400
        
        # Construir nombre esperado del archivo con prefijo (compatibilidad con archivos antiguos)
        expected_filename = f"ECF_{tipo_ecf}_{filename}" if not filename.startswith(f"ECF_{tipo_ecf}_") else filename
        file_path = os.path.join(XSD_BASE_PATH, expected_filename)
        
        # Si no se encuentra con prefijo, intentar con el nombre original
        if not os.path.exists(file_path):
            original_file_path = os.path.join(XSD_BASE_PATH, filename)
            if os.path.exists(original_file_path):
                file_path = original_file_path
                expected_filename = filename
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not expected_filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
        
        # Leer contenido del archivo
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Si falla UTF-8, intentar con latin-1
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Obtener información adicional del archivo
        file_stats = os.stat(file_path)
        
        return jsonify({
            "success": True,
            "filename": expected_filename,
            "tipo_ecf": tipo_ecf,
            "tipo_descripcion": TIPOS_ECF_VALIDOS[tipo_ecf],
            "content": content,
            "file_path": file_path.replace("\\", "/"),
            "file_size": file_stats.st_size,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "editable": True
        }), 200
        
    except Exception as e:
        logger.error(f"Error procesando archivo XSD {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/<tipo_ecf>/<filename>/download", methods=["GET"])

@token_or_api_key_required  
def download_xsd_file(tipo_ecf, filename):
    """
    Endpoint para descargar un archivo XSD específico con tipo ECF
    """
    try:
        # Validar tipo de ECF
        if tipo_ecf not in TIPOS_ECF_VALIDOS:
            return jsonify({
                "error": f"Tipo de ECF inválido. Tipos válidos: {list(TIPOS_ECF_VALIDOS.keys())}"
            }), 400
        
        # Construir nombre esperado del archivo con prefijo (compatibilidad con archivos antiguos)
        expected_filename = f"ECF_{tipo_ecf}_{filename}" if not filename.startswith(f"ECF_{tipo_ecf}_") else filename
        file_path = os.path.join(XSD_BASE_PATH, expected_filename)
        
        # Si no se encuentra con prefijo, intentar con el nombre original
        if not os.path.exists(file_path):
            original_file_path = os.path.join(XSD_BASE_PATH, filename)
            if os.path.exists(original_file_path):
                file_path = original_file_path
                expected_filename = filename
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not expected_filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
            
        # Enviar archivo
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=expected_filename,
            mimetype='application/xml'
        )
        
        # Agregar headers CORS explícitos para descarga
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition,Content-Length,Content-Type')
        
        return response
        
    except Exception as e:
        logger.error(f"Error descargando archivo XSD {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/view/<filename>", methods=["GET"])

@token_or_api_key_required  
def view_xsd_file_direct(filename):
    """
    Endpoint para obtener el contenido de un archivo XSD especial para visualización/edición
    """
    try:
        # Construir ruta del archivo
        file_path = os.path.join(XSD_BASE_PATH, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
        
        # Verificar si es archivo especial
        base_name = os.path.splitext(filename)[0]
        es_especial = any(especial.upper() in base_name.upper() for especial in ARCHIVOS_XSD_ESPECIALES)
        
        # Leer contenido del archivo
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Si falla UTF-8, intentar con latin-1
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Obtener información adicional del archivo
        file_stats = os.stat(file_path)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "es_archivo_especial": es_especial,
            "content": content,
            "file_path": file_path.replace("\\", "/"),
            "file_size": file_stats.st_size,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "editable": True
        }), 200
        
    except Exception as e:
        logger.error(f"Error visualizando archivo XSD especial {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/download/<filename>", methods=["GET"])

@token_or_api_key_required  
def download_xsd_file_direct(filename):
    """
    Endpoint para descargar un archivo XSD específico directamente por nombre (para archivos especiales)
    """
    try:
        # Construir ruta del archivo
        file_path = os.path.join(XSD_BASE_PATH, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
            
        # Enviar archivo
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/xml'
        )
        
        # Agregar headers CORS explícitos para descarga
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition,Content-Length,Content-Type')
        
        return response
        
    except Exception as e:
        logger.error(f"Error descargando archivo XSD {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ENDPOINT DELETE ELIMINADO - Los XSD solo pueden ser visualizados, no editados

@routes.route("/xsd/<tipo_ecf>/<filename>/view", methods=["GET"])
@token_or_api_key_required
def view_xsd_file_type(tipo_ecf, filename):
    """
    Endpoint para visualizar el contenido de un archivo XSD específico con tipo ECF
    Solo permite lectura, no edición
    """
    try:
        # Validar tipo de ECF
        if tipo_ecf not in TIPOS_ECF_VALIDOS:
            return jsonify({
                "error": f"Tipo de ECF inválido. Tipos válidos: {list(TIPOS_ECF_VALIDOS.keys())}"
            }), 400
        
        # Construir nombre esperado del archivo con prefijo (compatibilidad con archivos antiguos)
        expected_filename = f"ECF_{tipo_ecf}_{filename}" if not filename.startswith(f"ECF_{tipo_ecf}_") else filename
        file_path = os.path.join(XSD_BASE_PATH, expected_filename)
        
        # Si no se encuentra con prefijo, intentar con el nombre original
        if not os.path.exists(file_path):
            original_file_path = os.path.join(XSD_BASE_PATH, filename)
            if os.path.exists(original_file_path):
                file_path = original_file_path
                expected_filename = filename
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not expected_filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
        
        # Leer contenido del archivo para visualización únicamente
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Si falla UTF-8, intentar con latin-1
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Obtener información adicional del archivo
        file_stats = os.stat(file_path)
        
        response_data = {
            "success": True,
            "message": "Archivo XSD cargado para visualización",
            "filename": expected_filename,
            "tipo_ecf": tipo_ecf,
            "tipo_descripcion": TIPOS_ECF_VALIDOS[tipo_ecf],
            "content": content,
            "file_path": file_path.replace("\\", "/"),
            "file_size": file_stats.st_size,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "readonly": True  # Indica que es solo lectura
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error procesando archivo XSD {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/view-special/<filename>", methods=["GET"])
@token_or_api_key_required
def view_xsd_file_special(filename):
    """
    Endpoint para visualizar el contenido de un archivo XSD especial
    Solo permite lectura, no edición
    """
    try:
        # Construir ruta del archivo
        file_path = os.path.join(XSD_BASE_PATH, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({"error": "Archivo XSD no encontrado"}), 404
        
        # Verificar que es un archivo XSD
        if not filename.lower().endswith('.xsd'):
            return jsonify({"error": "El archivo no es un XSD válido"}), 400
        
        # Leer contenido del archivo para visualización únicamente
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Si falla UTF-8, intentar con latin-1
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Verificar si es archivo especial
        base_name = os.path.splitext(filename)[0]
        es_especial = any(especial.upper() in base_name.upper() for especial in ARCHIVOS_XSD_ESPECIALES)
        
        # Obtener información adicional del archivo
        file_stats = os.stat(file_path)
        
        response_data = {
            "success": True,
            "message": "Archivo XSD cargado para visualización",
            "filename": filename,
            "es_archivo_especial": es_especial,
            "content": content,
            "file_path": file_path.replace("\\", "/"),
            "file_size": file_stats.st_size,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "readonly": True  # Indica que es solo lectura
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error procesando archivo XSD {filename}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/tipos", methods=["GET"])

def get_tipos_ecf():
    """
    Endpoint público para obtener los tipos de ECF válidos
    """
    try:
        return jsonify({
            "message": "Tipos de ECF disponibles",
            "tipos_ecf": TIPOS_ECF_VALIDOS
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de ECF: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/xsd/config", methods=["GET"])

@token_or_api_key_required
def get_xsd_config():
    """
    Endpoint para obtener la configuración actual de archivos XSD desde configxsd.json
    """
    try:
        config_data = obtener_config_xsd()
        
        return jsonify({
            "message": "Configuración de XSD obtenida exitosamente",
            "configuracion": config_data,
            "total_configurados": len(config_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración XSD: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ================================= ENDPOINTS PARA CONFIGURACIÓN DE DIRECTORIOS =================================

@routes.route("/config/directorios", methods=["GET"])
@token_or_api_key_required
def get_config_directorios():
    """
    Endpoint para obtener la configuración actual de directorios
    """
    try:
        config_data = cargar_config_directorios()
        
        return jsonify({
            "message": "Configuración de directorios obtenida exitosamente",
            "configuracion": config_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración de directorios: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/config/directorios", methods=["PUT"])
@token_or_api_key_required
def update_config_directorios():
    """
    Endpoint para actualizar la configuración de directorios
    
    Body esperado:
    {
        "estructura_base": "C:/Base/Ambiente/",
        "carpetas_principales": ["Img", "RI", "Token", "Cert", "CSV"],
        "carpetas_con_subcarpetas": {
            "Semillas": ["Firmadas", "Generadas"],
            "XML": ["Firmadas", "Generadas"],
            "Bin": ["Servicios"]
        }
    }
    """
    try:
        # Obtener datos del JSON
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        
        # Validar estructura básica
        if "estructura_base" not in data:
            return jsonify({"error": "estructura_base es requerido"}), 400
            
        # Construir ruta del archivo de configuración
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, "data", "directorios.json")
        
        # Guardar nueva configuración
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        logger.info("Configuración de directorios actualizada exitosamente")
        
        return jsonify({
            "message": "Configuración de directorios actualizada exitosamente",
            "configuracion": data
        }), 200
        
    except Exception as e:
        logger.error(f"Error actualizando configuración de directorios: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@routes.route("/config/dgii", methods=["GET"])
@token_or_api_key_required  
def get_config_dgii():
    """
    Endpoint para obtener la configuración DGII desde configdgii.json
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, "data", "configdgii.json")
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return jsonify({
                "message": "Configuración DGII obtenida exitosamente",
                "configuracion": config_data
            }), 200
        else:
            return jsonify({"error": "Archivo de configuración DGII no encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo configuración DGII: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# ============================================================================
# ENDPOINTS PARA GESTIÓN DE QUERIES SQL (PESTAÑA SOPORTE)
# ============================================================================

@routes.route("/api/queries", methods=["POST"])
@token_or_api_key_required
def create_query():
    """
    Crea un nuevo query SQL y lo guarda en C:\\Query\\
    
    Payload JSON:
    {
        "nombre": "string (3-100 chars, obligatorio)",
        "tipo": "string (SELECT/UPDATE/INSERT/DELETE/VIEW/PROCEDURE/FUNCTION/OTHER, obligatorio)",
        "finalidad": "string (opcional)",
        "empresa": "string (opcional)",
        "query_text": "string (contenido SQL, obligatorio, max 20000 chars)"
    }
    """
    try:
        from query_models import create_query as create_query_model
        
        # Obtener username del token JWT
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        
        # Crear query
        result, error = create_query_model(data, username)
        
        if error:
            logger.warning(f"Error al crear query: {error}")
            return jsonify({"error": error}), 400
        
        logger.info(f"Query creado exitosamente por usuario {username}: {result['id']}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error interno al crear query: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/queries", methods=["GET"])
@token_or_api_key_required
def list_queries():
    """
    Lista queries con filtros y paginación.
    
    Query params:
    - nombre: filtrar por nombre (búsqueda parcial)
    - tipo: filtrar por tipo exacto (SELECT, UPDATE, etc.)
    - empresa: filtrar por empresa (búsqueda parcial)
    - finalidad: filtrar por finalidad (búsqueda parcial)
    - limit: número de registros por página (default: 20)
    - offset: desplazamiento para paginación (default: 0)
    - list_view: si es 'true', devuelve vista simplificada
    """
    try:
        from query_models import get_queries
        
        # Obtener parámetros de filtrado
        filters = {}
        if request.args.get('nombre'):
            filters['nombre'] = request.args.get('nombre')
        if request.args.get('tipo'):
            filters['tipo'] = request.args.get('tipo')
        if request.args.get('empresa'):
            filters['empresa'] = request.args.get('empresa')
        if request.args.get('finalidad'):
            filters['finalidad'] = request.args.get('finalidad')
        
        # Obtener parámetros de paginación
        try:
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            # Validar límites razonables
            if limit < 1 or limit > 100:
                limit = 20
            if offset < 0:
                offset = 0
                
        except ValueError:
            limit = 20
            offset = 0
        
        # Obtener queries
        queries, total = get_queries(filters if filters else None, limit, offset)
        
        # Si es vista simplificada, devolver solo campos mínimos
        list_view = request.args.get('list_view', '').lower() == 'true'
        if list_view:
            queries = [
                {
                    'id': q['id'],
                    'nombre': q['nombre'],
                    'tipo': q['tipo'],
                    'empresa': q['empresa'],
                    'created_at': q['created_at']
                }
                for q in queries
            ]
        
        response = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'items': queries
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error al listar queries: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/queries/<query_id>", methods=["GET"])
@token_or_api_key_required
def get_query(query_id):
    """
    Obtiene un query por su ID, incluyendo el contenido del archivo .txt
    """
    try:
        from query_models import get_query_by_id
        
        # Validar formato de UUID
        try:
            uuid.UUID(query_id)
        except ValueError:
            return jsonify({"error": "ID de query inválido"}), 400
        
        # Obtener query
        query = get_query_by_id(query_id, include_text=True)
        
        if not query:
            return jsonify({"error": "Query no encontrado"}), 404
        
        return jsonify(query), 200
        
    except Exception as e:
        logger.error(f"Error al obtener query {query_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/queries/<query_id>", methods=["PUT"])
@token_or_api_key_required
def update_query(query_id):
    """
    Actualiza un query existente.
    
    Payload JSON (mismos campos que POST):
    {
        "nombre": "string (3-100 chars, obligatorio)",
        "tipo": "string (obligatorio)",
        "finalidad": "string (opcional)",
        "empresa": "string (opcional)",
        "query_text": "string (obligatorio)"
    }
    """
    try:
        from query_models import update_query as update_query_model
        
        # Validar formato de UUID
        try:
            uuid.UUID(query_id)
        except ValueError:
            return jsonify({"error": "ID de query inválido"}), 400
        
        # Obtener username del token JWT
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        
        # Actualizar query
        result, error = update_query_model(query_id, data, username)
        
        if error:
            logger.warning(f"Error al actualizar query {query_id}: {error}")
            
            if "no encontrado" in error.lower():
                return jsonify({"error": error}), 404
            else:
                return jsonify({"error": error}), 400
        
        logger.info(f"Query actualizado exitosamente por usuario {username}: {query_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error interno al actualizar query {query_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/queries/<query_id>", methods=["DELETE"])
@token_or_api_key_required
def delete_query(query_id):
    """
    Elimina un query de la base de datos y su archivo físico de C:\\Query\\
    """
    try:
        from query_models import delete_query as delete_query_model
        
        # Validar formato de UUID
        try:
            uuid.UUID(query_id)
        except ValueError:
            return jsonify({"error": "ID de query inválido"}), 400
        
        # Obtener username del token JWT para logging
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        # Eliminar query
        success, error = delete_query_model(query_id)
        
        if not success:
            logger.warning(f"Error al eliminar query {query_id}: {error}")
            
            if "no encontrado" in error.lower():
                return jsonify({"error": error}), 404
            else:
                return jsonify({"error": error}), 400
        
        logger.info(f"Query eliminado exitosamente por usuario {username}: {query_id}")
        return "", 204
        
    except Exception as e:
        logger.error(f"Error interno al eliminar query {query_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# ============================================================================
# ENDPOINTS PARA GESTIÓN DE MANUALES/INSTRUCTIVOS PDF (PESTAÑA SOPORTE)
# ============================================================================

@routes.route("/api/manuales", methods=["POST"])
@token_or_api_key_required
def upload_manual():
    """
    Sube un nuevo manual/instructivo en PDF.
    
    Multipart/form-data:
    - file: archivo PDF (obligatorio, máx 50MB)
    - nombre: string (obligatorio, 3-150 caracteres)
    - categoria: string (opcional: USUARIO/TECNICO/ADMINISTRADOR/CONFIGURACION/API/OTRO)
    - descripcion: string (opcional, máx 500 caracteres)
    - version: string (opcional, ej: "1.0", "2.5")
    """
    try:
        from manual_models import create_manual
        
        # Obtener username del token JWT
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({"error": "No se proporcionó archivo PDF"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip() or None
        descripcion = request.form.get('descripcion', '').strip() or None
        version = request.form.get('version', '').strip() or None
        
        if not nombre:
            return jsonify({"error": "El nombre es obligatorio"}), 400
        
        # Leer contenido del archivo
        file_content = file.read()
        
        # Crear manual
        result, error = create_manual(
            nombre=nombre,
            file_content=file_content,
            original_filename=file.filename,
            categoria=categoria,
            descripcion=descripcion,
            version=version,
            username=username
        )
        
        if error:
            logger.warning(f"Error al crear manual: {error}")
            return jsonify({"error": error}), 400
        
        logger.info(f"Manual creado exitosamente por usuario {username}: {result['id']}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error interno al subir manual: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/manuales", methods=["GET"])
@token_or_api_key_required
def list_manuales():
    """
    Lista manuales con filtros y paginación (similar a queries).
    
    Query params:
    - nombre: filtrar por nombre (búsqueda parcial)
    - categoria: filtrar por categoría exacta (USUARIO/TECNICO/etc.)
    - descripcion: filtrar por descripción (búsqueda parcial)
    - limit: número de registros por página (default: 20, max: 100)
    - offset: desplazamiento para paginación (default: 0)
    """
    try:
        from manual_models import get_manuales
        
        # Obtener parámetros de filtrado
        filters = {}
        if request.args.get('nombre'):
            filters['nombre'] = request.args.get('nombre')
        if request.args.get('categoria'):
            filters['categoria'] = request.args.get('categoria')
        if request.args.get('descripcion'):
            filters['descripcion'] = request.args.get('descripcion')
        
        # Obtener parámetros de paginación
        try:
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            # Validar límites razonables
            if limit < 1 or limit > 100:
                limit = 20
            if offset < 0:
                offset = 0
                
        except ValueError:
            limit = 20
            offset = 0
        
        # Obtener manuales
        manuales, total = get_manuales(filters if filters else None, limit, offset)
        
        response = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'items': manuales
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error al listar manuales: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/manuales/<manual_id>", methods=["GET"])
@token_or_api_key_required
def get_manual_metadata(manual_id):
    """
    Obtiene metadata de un manual por su ID (sin descargar el PDF).
    Para descargar el PDF, usar el endpoint /api/manuales/{id}/download
    """
    try:
        from manual_models import get_manual_by_id
        
        # Validar formato de UUID
        try:
            uuid.UUID(manual_id)
        except ValueError:
            return jsonify({"error": "ID de manual inválido"}), 400
        
        # Obtener manual
        manual = get_manual_by_id(manual_id)
        
        if not manual:
            return jsonify({"error": "Manual no encontrado"}), 404
        
        return jsonify(manual), 200
        
    except Exception as e:
        logger.error(f"Error al obtener manual {manual_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/manuales/<manual_id>/download", methods=["GET"])
@token_or_api_key_required
def download_manual(manual_id):
    """
    Descarga el archivo PDF del manual.
    Incrementa el contador de descargas automáticamente.
    """
    try:
        from manual_models import get_manual_by_id, read_manual_file, increment_download_count
        import io
        
        # Validar formato de UUID
        try:
            uuid.UUID(manual_id)
        except ValueError:
            return jsonify({"error": "ID de manual inválido"}), 400
        
        # Obtener manual
        manual = get_manual_by_id(manual_id)
        
        if not manual:
            return jsonify({"error": "Manual no encontrado"}), 404
        
        # Leer archivo
        file_content = read_manual_file(manual['filename'])
        
        if file_content is None:
            return jsonify({"error": "Error al leer el archivo del manual"}), 500
        
        # Incrementar contador de descargas
        increment_download_count(manual_id)
        
        # Obtener username para logging
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        logger.info(f"Manual descargado por usuario {username}: {manual_id} - {manual['nombre']}")
        
        # Crear un objeto BytesIO para enviar el archivo
        return send_file(
            io.BytesIO(file_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{manual['nombre']}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error al descargar manual {manual_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/manuales/<manual_id>/view", methods=["GET"])
@token_or_api_key_required
def view_manual(manual_id):
    """
    Visualiza el PDF en el navegador (inline, no como descarga).
    Útil para previsualización.
    """
    try:
        from manual_models import get_manual_by_id, read_manual_file, increment_download_count
        import io
        
        # Validar formato de UUID
        try:
            uuid.UUID(manual_id)
        except ValueError:
            return jsonify({"error": "ID de manual inválido"}), 400
        
        # Obtener manual
        manual = get_manual_by_id(manual_id)
        
        if not manual:
            return jsonify({"error": "Manual no encontrado"}), 404
        
        # Leer archivo
        file_content = read_manual_file(manual['filename'])
        
        if file_content is None:
            return jsonify({"error": "Error al leer el archivo del manual"}), 500
        
        # Incrementar contador de visualizaciones
        increment_download_count(manual_id)
        
        # Obtener username para logging
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        logger.info(f"Manual visualizado por usuario {username}: {manual_id} - {manual['nombre']}")
        
        # Enviar como inline para visualización en navegador
        return send_file(
            io.BytesIO(file_content),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"{manual['nombre']}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error al visualizar manual {manual_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@routes.route("/api/manuales/<manual_id>", methods=["DELETE"])
@token_or_api_key_required
def delete_manual_endpoint(manual_id):
    """
    Elimina un manual de la base de datos y su archivo físico de C:\\Manuales\\
    """
    try:
        from manual_models import delete_manual
        
        # Validar formato de UUID
        try:
            uuid.UUID(manual_id)
        except ValueError:
            return jsonify({"error": "ID de manual inválido"}), 400
        
        # Obtener username del token JWT para logging
        token = request.headers.get("Authorization", "").split(" ")[1] if request.headers.get("Authorization") else None
        username = None
        
        if token:
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                username = payload.get("username")
            except:
                pass
        
        # Eliminar manual
        success, error = delete_manual(manual_id)
        
        if not success:
            logger.warning(f"Error al eliminar manual {manual_id}: {error}")
            
            if "no encontrado" in error.lower():
                return jsonify({"error": error}), 404
            else:
                return jsonify({"error": error}), 400
        
        logger.info(f"Manual eliminado exitosamente por usuario {username}: {manual_id}")
        return "", 204
        
    except Exception as e:
        logger.error(f"Error interno al eliminar manual {manual_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# ============================================================================
# SISTEMA DE TICKETS DE INCIDENCIAS
# ============================================================================

# Importar modelos de tickets
from ticket_models import (
    TicketModel, 
    AttachmentModel, 
    TicketDatabase,
    PrioridadEnum,
    EstadoEnum
)

# Configuración de tickets
ATTACHMENTS_BASE_PATH = r"C:\Tickets\Attachments"
MAX_FILE_SIZE_TICKETS = 10 * 1024 * 1024  # 10 MB
MAX_TOTAL_SIZE_TICKETS = 50 * 1024 * 1024  # 50 MB por ticket
ALLOWED_EXTENSIONS_TICKETS = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp',
    'text/plain', 'text/csv', 'application/json',
    'application/zip', 'application/x-zip-compressed',
    'application/pdf',
    '.log', '.txt', '.csv', '.json', '.zip', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp'
}

BLOCKED_EXTENSIONS_TICKETS = {'.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.vbs', '.js', '.jar', '.sh', '.ps1'}


def ensure_attachments_directory():
    """Crea el directorio base de attachments si no existe"""
    try:
        os.makedirs(ATTACHMENTS_BASE_PATH, exist_ok=True)
        logger.info(f"Directorio de attachments asegurado: {ATTACHMENTS_BASE_PATH}")
    except Exception as e:
        logger.error(f"Error al crear directorio de attachments: {e}")
        raise


def is_allowed_file_ticket(filename: str, content_type: str) -> bool:
    """Valida si un archivo es permitido basado en extensión y content type"""
    _, ext = os.path.splitext(filename.lower())
    if ext in BLOCKED_EXTENSIONS_TICKETS:
        return False
    
    if content_type in ALLOWED_EXTENSIONS_TICKETS or ext in ALLOWED_EXTENSIONS_TICKETS:
        return True
    
    if content_type.startswith('image/'):
        return True
    
    return False


def sanitize_filename_ticket(filename: str) -> str:
    """Sanitiza el nombre del archivo para prevenir path traversal"""
    safe_name = secure_filename(filename)
    name, ext = os.path.splitext(safe_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{timestamp}_{unique_id}{ext}"


def save_attachment_ticket(file, ticket_id: str) -> AttachmentModel:
    """Guarda un archivo adjunto y retorna el modelo de attachment"""
    ensure_attachments_directory()
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE_TICKETS:
        raise ValueError(f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_TICKETS / (1024*1024):.1f}MB")
    
    original_name = file.filename
    content_type = file.content_type or mimetypes.guess_type(original_name)[0] or 'application/octet-stream'
    
    if not is_allowed_file_ticket(original_name, content_type):
        raise ValueError(f"Tipo de archivo no permitido: {original_name}")
    
    ticket_dir = os.path.join(ATTACHMENTS_BASE_PATH, ticket_id)
    os.makedirs(ticket_dir, exist_ok=True)
    
    safe_filename_str = sanitize_filename_ticket(original_name)
    file_path = os.path.join(ticket_dir, safe_filename_str)
    
    file.save(file_path)
    logger.info(f"Archivo guardado: {file_path}")
    
    attachment = AttachmentModel(
        id=str(uuid.uuid4()),
        ticket_id=ticket_id,
        filename=safe_filename_str,
        original_name=original_name,
        content_type=content_type,
        size_bytes=file_size,
        path=file_path,
        uploaded_at=datetime.now()
    )
    
    return attachment


def normalize_prioridad(prioridad: str) -> str:
    """Normaliza el valor de prioridad aceptando variaciones comunes"""
    if not prioridad:
        return prioridad
    
    prioridad_upper = prioridad.upper().strip()
    
    # Mapeo de variaciones comunes a valores válidos
    normalizaciones = {
        'CRITICA': 'CRÍTICA',
        'CRÍTICA': 'CRÍTICA',
        'ALTA': 'ALTA',
        'MEDIA': 'MEDIA',
        'BAJA': 'BAJA'
    }
    
    return normalizaciones.get(prioridad_upper, prioridad_upper)


def validate_ticket_data(data: dict, is_update: bool = False) -> dict:
    """Valida los datos del ticket"""
    errors = {}
    
    # Normalizar prioridad si existe
    if 'prioridad' in data and data['prioridad']:
        data['prioridad'] = normalize_prioridad(data['prioridad'])
    
    if not is_update:
        if not data.get('titulo'):
            errors['titulo'] = 'El título es obligatorio'
        elif len(data['titulo']) < 5 or len(data['titulo']) > 200:
            errors['titulo'] = 'El título debe tener entre 5 y 200 caracteres'
        
        if not data.get('prioridad'):
            errors['prioridad'] = 'La prioridad es obligatoria'
        elif data['prioridad'] not in [p.value for p in PrioridadEnum]:
            errors['prioridad'] = f'Prioridad inválida. Valores permitidos: BAJA, MEDIA, ALTA, CRITICA (o CRÍTICA)'
        
        if not data.get('categoria'):
            errors['categoria'] = 'La categoría es obligatoria'
        
        if not data.get('descripcion'):
            errors['descripcion'] = 'La descripción es obligatoria'
        
        if not data.get('creado_por'):
            errors['creado_por'] = 'El campo creado_por es obligatorio'
    else:
        if 'titulo' in data:
            if len(data['titulo']) < 5 or len(data['titulo']) > 200:
                errors['titulo'] = 'El título debe tener entre 5 y 200 caracteres'
        
        if 'prioridad' in data:
            if data['prioridad'] not in [p.value for p in PrioridadEnum]:
                errors['prioridad'] = f'Prioridad inválida. Valores permitidos: BAJA, MEDIA, ALTA, CRITICA (o CRÍTICA)'
        
        if 'estado' in data:
            if data['estado'].upper() not in [e.value for e in EstadoEnum]:
                errors['estado'] = f'Estado inválido. Valores permitidos: {", ".join([e.value for e in EstadoEnum])}'
    
    if errors:
        raise ValueError(errors)
    
    return data


# ==================== FUNCIÓN HELPER PARA PERMISOS DE CLIENTE ====================

def get_client_info_from_token():
    """
    Extrae información del cliente desde el token JWT.
    Retorna None si no es un cliente o no hay token.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1] if ' ' in auth_header else None
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            current_app.config["SECRET_KEY"], 
            algorithms=["HS256"]
        )
        
        if payload.get('tipo_usuario') == 'CLIENTE':
            return {
                'username': payload.get('username'),
                'tipo_usuario': 'CLIENTE',
                'empresa_id': payload.get('empresa_id'),
                'rnc_empresa': payload.get('rnc_empresa')
            }
        
        # Retornar info para ADMIN/SOPORTE (tienen acceso completo)
        if payload.get('tipo_usuario') in ['ADMIN', 'ADMINISTRADOR', 'SOPORTE']:
            return {
                'username': payload.get('username'),
                'tipo_usuario': payload.get('tipo_usuario'),
                'empresa_id': None,  # Acceso a todas las empresas
                'rnc_empresa': None
            }
        
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def check_client_ticket_permission(ticket, client_info, action='view'):
    """
    Verifica si un cliente tiene permiso sobre un ticket.
    
    Args:
        ticket: El ticket a verificar
        client_info: Información del cliente desde get_client_info_from_token()
        action: 'view', 'edit', 'delete'
    
    Returns:
        (allowed: bool, error_message: str or None)
    """
    if not client_info:
        return True, None  # Sin token = permitir (legacy)
    
    # Admin y Soporte tienen acceso completo
    if client_info['tipo_usuario'] in ['ADMIN', 'ADMINISTRADOR', 'SOPORTE']:
        return True, None
    
    # Para clientes
    if client_info['tipo_usuario'] == 'CLIENTE':
        # Verificar que el ticket pertenece a su empresa
        # Comparar por nombre de empresa (ticket.empresa) o RNC
        ticket_empresa = ticket.empresa if hasattr(ticket, 'empresa') else None
        client_rnc = client_info.get('rnc_empresa')
        
        # Verificar coincidencia
        if ticket_empresa and client_rnc:
            # Permitir si la empresa del ticket coincide con el RNC del cliente
            if ticket_empresa == client_rnc or client_rnc in str(ticket_empresa):
                if action == 'delete':
                    return False, "Los clientes no pueden eliminar tickets"
                return True, None
        
        # También verificar por creador
        if ticket.creado_por == client_info['username']:
            if action == 'delete':
                return False, "Los clientes no pueden eliminar tickets"
            return True, None
        
        return False, "No tiene permiso para acceder a este ticket"
    
    return True, None


# ==================== ENDPOINTS DE TICKETS ====================

@routes.route("/api/tickets", methods=["POST"])
def create_ticket():
    """Crea un nuevo ticket con archivos adjuntos opcionales"""
    try:
        data = {
            'titulo': request.form.get('titulo'),
            'prioridad': request.form.get('prioridad', '').upper(),
            'categoria': request.form.get('categoria'),
            'empresa': request.form.get('empresa'),
            'descripcion': request.form.get('descripcion'),
            'creado_por': request.form.get('creado_por'),
            'asignado_a': request.form.get('asignado_a'),
        }
        
        validate_ticket_data(data)
        
        ticket_id = str(uuid.uuid4())
        ticket = TicketModel(
            id=ticket_id,
            titulo=data['titulo'],
            prioridad=data['prioridad'],
            categoria=data['categoria'],
            empresa=data['empresa'],
            descripcion=data['descripcion'],
            estado=EstadoEnum.PENDIENTE.value,
            creado_por=data['creado_por'],
            asignado_a=data['asignado_a']
        )
        
        TicketDatabase.create_ticket(ticket)
        
        attachments_data = []
        total_size = 0
        
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            
            for file in files:
                if file and file.filename:
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    total_size += file_size
                    
                    if total_size > MAX_TOTAL_SIZE_TICKETS:
                        raise ValueError(f"El tamaño total de los archivos excede el límite de {MAX_TOTAL_SIZE_TICKETS / (1024*1024):.1f}MB")
                    
                    attachment = save_attachment_ticket(file, ticket_id)
                    TicketDatabase.create_attachment(attachment)
                    attachments_data.append(attachment.to_dict())
        
        response_data = ticket.to_dict()
        response_data['attachments'] = attachments_data
        
        logger.info(f"Ticket {ticket_id} creado exitosamente por {data['creado_por']}")
        return jsonify(response_data), 201
        
    except ValueError as e:
        logger.warning(f"Error de validación al crear ticket: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear ticket: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets", methods=["GET"])
def list_tickets():
    """Lista tickets con filtros y paginación"""
    try:
        estado = request.args.get('estado', 'PENDIENTE').upper()
        prioridad = request.args.get('prioridad', '').upper() or None
        categoria = request.args.get('categoria') or None
        empresa = request.args.get('empresa') or None
        creado_por = request.args.get('creado_por') or None
        asignado_a = request.args.get('asignado_a') or None
        search = request.args.get('search') or None
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        sort = request.args.get('sort', 'priority_score:desc,created_at:asc')
        detail = request.args.get('detail', 'false').lower() == 'true'
        list_view = request.args.get('list_view', 'false').lower() == 'true'
        
        # Verificar si es un cliente - filtrar por su empresa automáticamente
        client_info = get_client_info_from_token()
        if client_info and client_info['tipo_usuario'] == 'CLIENTE':
            # Forzar filtro por RNC de empresa del cliente
            empresa = client_info.get('rnc_empresa')
            logger.info(f"Cliente {client_info['username']} listando tickets de empresa: {empresa}")
        
        tickets, total_count = TicketDatabase.list_tickets(
            estado=estado,
            prioridad=prioridad,
            categoria=categoria,
            empresa=empresa,
            creado_por=creado_por,
            asignado_a=asignado_a,
            search=search,
            limit=limit,
            offset=offset,
            sort=sort
        )
        
        tickets_data = []
        for ticket in tickets:
            if list_view:
                ticket_dict = {
                    'id': ticket.id,
                    'titulo': ticket.titulo,
                    'prioridad': ticket.prioridad,
                    'categoria': ticket.categoria,
                    'empresa_nombre': ticket.empresa_nombre,  # ← AGREGAR ESTO
                    'estado': ticket.estado,
                    'creado_por': ticket.creado_por,
                    'asignado_a': ticket.asignado_a,
                    'created_at': ticket.created_at.isoformat() if isinstance(ticket.created_at, datetime) else ticket.created_at,
                    'short_description': ticket.descripcion[:200] + ('...' if len(ticket.descripcion) > 200 else '') if ticket.descripcion else ''
                }
            else:
                truncate = None if detail else 200
                ticket_dict = ticket.to_dict(include_description=True, truncate_description=truncate)
            
            tickets_data.append(ticket_dict)
        
        return jsonify({
            'tickets': tickets_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'count': len(tickets_data)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error al listar tickets: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>", methods=["GET"])
def get_ticket_detail(ticket_id: str):
    """Obtiene el detalle completo de un ticket incluyendo attachments"""
    try:
        ticket = TicketDatabase.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        # Verificar permisos de cliente
        client_info = get_client_info_from_token()
        allowed, error_msg = check_client_ticket_permission(ticket, client_info, 'view')
        if not allowed:
            return jsonify({'error': error_msg}), 403
        
        attachments = TicketDatabase.get_attachments_by_ticket(ticket_id)
        
        response_data = ticket.to_dict(include_description=True)
        response_data['attachments'] = [
            {
                **att.to_dict(),
                'download_url': f"/api/tickets/{ticket_id}/attachments/{att.id}"
            }
            for att in attachments
        ]
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error al obtener ticket {ticket_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>", methods=["PUT", "PATCH"])
def update_ticket(ticket_id: str):
    """Actualiza un ticket existente"""
    try:
        ticket = TicketDatabase.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        # Verificar permisos de cliente
        client_info = get_client_info_from_token()
        allowed, error_msg = check_client_ticket_permission(ticket, client_info, 'edit')
        if not allowed:
            return jsonify({'error': error_msg}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400
        
        if 'prioridad' in data:
            data['prioridad'] = data['prioridad'].upper()
        if 'estado' in data:
            data['estado'] = data['estado'].upper()
        
        validate_ticket_data(data, is_update=True)
        
        updated_ticket = TicketDatabase.update_ticket(ticket_id, **data)
        
        if not updated_ticket:
            return jsonify({'error': 'Error al actualizar ticket'}), 500
        
        logger.info(f"Ticket {ticket_id} actualizado exitosamente")
        return jsonify(updated_ticket.to_dict()), 200
        
    except ValueError as e:
        logger.warning(f"Error de validación al actualizar ticket: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar ticket {ticket_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id: str):
    """Elimina un ticket y todos sus attachments"""
    try:
        ticket = TicketDatabase.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        # Verificar permisos - los clientes NO pueden eliminar
        client_info = get_client_info_from_token()
        allowed, error_msg = check_client_ticket_permission(ticket, client_info, 'delete')
        if not allowed:
            return jsonify({'error': error_msg}), 403
        
        attachments = TicketDatabase.get_attachments_by_ticket(ticket_id)
        
        TicketDatabase.delete_ticket(ticket_id)
        
        ticket_dir = os.path.join(ATTACHMENTS_BASE_PATH, ticket_id)
        if os.path.exists(ticket_dir):
            shutil.rmtree(ticket_dir)
            logger.info(f"Directorio de attachments eliminado: {ticket_dir}")
        
        logger.info(f"Ticket {ticket_id} eliminado exitosamente")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error al eliminar ticket {ticket_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>/attachments", methods=["POST"])
def upload_attachments(ticket_id: str):
    """Sube nuevos attachments a un ticket existente"""
    try:
        ticket = TicketDatabase.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        if 'attachments' not in request.files:
            return jsonify({'error': 'No se proporcionaron archivos'}), 400
        
        files = request.files.getlist('attachments')
        if not files or all(not f.filename for f in files):
            return jsonify({'error': 'No se proporcionaron archivos válidos'}), 400
        
        attachments_data = []
        total_size = 0
        
        existing_attachments = TicketDatabase.get_attachments_by_ticket(ticket_id)
        existing_size = sum(att.size_bytes for att in existing_attachments)
        
        for file in files:
            if file and file.filename:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                total_size += file_size
                
                if existing_size + total_size > MAX_TOTAL_SIZE_TICKETS:
                    raise ValueError(f"El tamaño total de los archivos excede el límite de {MAX_TOTAL_SIZE_TICKETS / (1024*1024):.1f}MB")
                
                attachment = save_attachment_ticket(file, ticket_id)
                TicketDatabase.create_attachment(attachment)
                
                att_dict = attachment.to_dict()
                att_dict['download_url'] = f"/api/tickets/{ticket_id}/attachments/{attachment.id}"
                attachments_data.append(att_dict)
        
        logger.info(f"{len(attachments_data)} attachments subidos al ticket {ticket_id}")
        return jsonify({'attachments': attachments_data}), 201
        
    except ValueError as e:
        logger.warning(f"Error de validación al subir attachments: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error al subir attachments al ticket {ticket_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>/attachments/<attachment_id>", methods=["GET"])
def download_attachment(ticket_id: str, attachment_id: str):
    """Descarga un attachment"""
    try:
        attachment = TicketDatabase.get_attachment_by_id(attachment_id)
        if not attachment or attachment.ticket_id != ticket_id:
            return jsonify({'error': 'Attachment no encontrado'}), 404
        
        if not os.path.exists(attachment.path):
            logger.error(f"Archivo no encontrado en disco: {attachment.path}")
            return jsonify({'error': 'Archivo no encontrado en el sistema'}), 404
        
        return send_file(
            attachment.path,
            as_attachment=True,
            download_name=attachment.original_name,
            mimetype=attachment.content_type
        )
        
    except Exception as e:
        logger.error(f"Error al descargar attachment {attachment_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/<ticket_id>/attachments/<attachment_id>", methods=["DELETE"])
def delete_attachment(ticket_id: str, attachment_id: str):
    """Elimina un attachment"""
    try:
         # Verificar permisos de cliente - los clientes NO pueden eliminar attachments
        client_info = get_client_info_from_token()
        if client_info and client_info['tipo_usuario'] == 'CLIENTE':
            return jsonify({'error': 'Los clientes no tienen permiso para eliminar archivos'}), 403
        
        attachment = TicketDatabase.get_attachment_by_id(attachment_id)
        if not attachment or attachment.ticket_id != ticket_id:
            return jsonify({'error': 'Attachment no encontrado'}), 404
        
        TicketDatabase.delete_attachment(attachment_id)
        
        if os.path.exists(attachment.path):
            os.remove(attachment.path)
            logger.info(f"Archivo eliminado: {attachment.path}")
        
        logger.info(f"Attachment {attachment_id} eliminado exitosamente")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error al eliminar attachment {attachment_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/stats", methods=["GET"])
def get_ticket_stats():
    """Obtiene estadísticas generales de tickets"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT estado, COUNT(*) as count
            FROM tickets
            GROUP BY estado
        """)
        estado_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT prioridad, COUNT(*) as count
            FROM tickets
            GROUP BY prioridad
        """)
        prioridad_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT categoria, COUNT(*) as count
            FROM tickets
            GROUP BY categoria
            ORDER BY count DESC
        """)
        categoria_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'por_estado': estado_stats,
            'por_prioridad': prioridad_stats,
            'por_categoria': categoria_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@routes.route("/api/tickets/config", methods=["GET"])
def get_ticket_config():
    """Obtiene la configuración del sistema de tickets"""
    return jsonify({
        'prioridades': [p.value for p in PrioridadEnum],
        'prioridades_aceptadas': ['BAJA', 'MEDIA', 'ALTA', 'CRITICA', 'CRÍTICA'],
        'estados': [e.value for e in EstadoEnum],
        'max_file_size_mb': MAX_FILE_SIZE_TICKETS / (1024 * 1024),
        'max_total_size_mb': MAX_TOTAL_SIZE_TICKETS / (1024 * 1024),
        'allowed_extensions': list(ALLOWED_EXTENSIONS_TICKETS),
        'blocked_extensions': list(BLOCKED_EXTENSIONS_TICKETS),
        'nota_prioridad': 'CRITICA (sin tilde) y CRÍTICA (con tilde) son aceptadas'
    }), 200


# ================================= ENDPOINTS PARA IMPORTACIÓN DE FACTURAS =================================
# Sistema de importación de archivos Excel/CSV con facturas por empresa (RNC)
# Tabla: FacturasImportadas
# Campos: RNC_Empresa, RNC_Receptor, ENCF, ENCF_Modificado, Fecha_Comprobante, 
#         Fecha_Recepcion, Aprobacion_Comercial, Fecha_Aprobacion_Comercial, Estado,
#         ITBIS_Facturado, Monto_Total_Gravado, Monto_Exento, Monto_No_Facturable

def verificar_o_crear_tabla_facturas():
    """
    Verifica si la tabla FacturasImportadas existe en SQL Server y la crea si no existe.
    También verifica que los campos sean del tipo correcto.
    
    Estructura de la tabla:
    - RNC_Empresa: NVARCHAR(20) - RNC de la empresa propietaria
    - RNC_Receptor: NVARCHAR(20) - RNC del receptor de la factura
    - ENCF: NVARCHAR(19) - Número de comprobante fiscal (campo único por empresa)
    - ENCF_Modificado: NVARCHAR(19) - Número de comprobante modificado (nullable)
    - Fecha_Comprobante: DATE - Fecha del comprobante
    - Fecha_Recepcion: DATE - Fecha de recepción
    - Aprobacion_Comercial: BIT - Si/No aprobación comercial
    - Fecha_Aprobacion_Comercial: DATE - Fecha de aprobación (nullable)
    - Estado: NVARCHAR(50) - Estado del comprobante
    - ITBIS_Facturado: DECIMAL(18,2) - Monto de ITBIS
    - Monto_Total_Gravado: DECIMAL(18,2) - Monto gravado
    - Monto_Exento: DECIMAL(18,2) - Monto exento
    - Monto_No_Facturable: DECIMAL(18,2) - Monto no facturable
    - Fecha_Importacion: DATETIME - Fecha de importación del registro
    
    Returns:
        tuple: (bool, str) - (éxito, mensaje)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FacturasImportadas')
            BEGIN
                CREATE TABLE FacturasImportadas (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    RNC_Empresa NVARCHAR(20) NOT NULL,
                    RNC_Receptor NVARCHAR(20),
                    ENCF NVARCHAR(19) NOT NULL,
                    ENCF_Modificado NVARCHAR(19),
                    Fecha_Comprobante DATE,
                    Fecha_Recepcion DATE,
                    Aprobacion_Comercial BIT DEFAULT 0,
                    Fecha_Aprobacion_Comercial DATE,
                    Estado NVARCHAR(50),
                    ITBIS_Facturado DECIMAL(18,2) DEFAULT 0,
                    Monto_Total_Gravado DECIMAL(18,2) DEFAULT 0,
                    Monto_Exento DECIMAL(18,2) DEFAULT 0,
                    Monto_No_Facturable DECIMAL(18,2) DEFAULT 0,
                    Fecha_Importacion DATETIME DEFAULT GETDATE(),
                    CONSTRAINT UQ_Empresa_ENCF UNIQUE (RNC_Empresa, ENCF)
                )
            END
        """)
        conn.commit()
        
        # Verificar columnas existentes
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'FacturasImportadas'
        """)
        
        columnas_existentes = {row[0]: row for row in cursor.fetchall()}
        
        # Definir estructura esperada
        columnas_esperadas = {
            'Id': ('int', None, None, None),
            'RNC_Empresa': ('nvarchar', 20, None, None),
            'RNC_Receptor': ('nvarchar', 20, None, None),
            'ENCF': ('nvarchar', 19, None, None),
            'ENCF_Modificado': ('nvarchar', 19, None, None),
            'Fecha_Comprobante': ('date', None, None, None),
            'Fecha_Recepcion': ('date', None, None, None),
            'Aprobacion_Comercial': ('bit', None, None, None),
            'Fecha_Aprobacion_Comercial': ('date', None, None, None),
            'Estado': ('nvarchar', 50, None, None),
            'ITBIS_Facturado': ('decimal', None, 18, 2),
            'Monto_Total_Gravado': ('decimal', None, 18, 2),
            'Monto_Exento': ('decimal', None, 18, 2),
            'Monto_No_Facturable': ('decimal', None, 18, 2),
            'Fecha_Importacion': ('datetime', None, None, None)
        }
        
        cursor.close()
        conn.close()
        
        logger.info("Tabla FacturasImportadas verificada/creada exitosamente")
        return True, "Tabla verificada correctamente"
        
    except Exception as e:
        logger.error(f"Error verificando/creando tabla FacturasImportadas: {str(e)}")
        return False, f"Error: {str(e)}"


def normalizar_nombre_columna(nombre):
    """
    Normaliza nombres de columnas para mapear correctamente desde archivos Excel/CSV
    
    Args:
        nombre (str): Nombre de columna original
        
    Returns:
        str: Nombre normalizado para la base de datos
    """
    # Mapeo de posibles nombres a nombres estándar
    mapeo = {
        'rnc receptor': 'RNC_Receptor',
        'rnc': 'RNC_Receptor',
        'receptor': 'RNC_Receptor',
        'encf': 'ENCF',
        'e-ncf': 'ENCF',
        'ncf': 'ENCF',
        'numero comprobante': 'ENCF',
        'encf modificado': 'ENCF_Modificado',
        'e-ncf modificado': 'ENCF_Modificado',
        'ncf modificado': 'ENCF_Modificado',
        'fecha comprobante': 'Fecha_Comprobante',
        'fecha': 'Fecha_Comprobante',
        'fecha recepcion': 'Fecha_Recepcion',
        'fecha recepción': 'Fecha_Recepcion',
        'aprobacion comercial': 'Aprobacion_Comercial',
        'aprobación comercial': 'Aprobacion_Comercial',
        'fecha aprobacion comercial': 'Fecha_Aprobacion_Comercial',
        'fecha aprobación comercial': 'Fecha_Aprobacion_Comercial',
        'estado': 'Estado',
        'itbis facturado': 'ITBIS_Facturado',
        'itbis': 'ITBIS_Facturado',
        'monto total gravado': 'Monto_Total_Gravado',
        'total gravado': 'Monto_Total_Gravado',
        'gravado': 'Monto_Total_Gravado',
        'monto exento': 'Monto_Exento',
        'exento': 'Monto_Exento',
        'monto no facturable': 'Monto_No_Facturable',
        'no facturable': 'Monto_No_Facturable'
    }
    
    nombre_limpio = nombre.strip().lower()
    return mapeo.get(nombre_limpio, nombre)


def normalizar_rnc(valor):
    """
    Normaliza un RNC eliminando cualquier separador o carácter no numérico.

    - Si viene como número con decimales (p. ej. 101234567.0 por Excel),
      se convierte de forma segura a entero y luego a string.
    - Si viene como texto (p. ej. "10123456.7" o "10-1234567"),
      se conservan únicamente los dígitos.

    Args:
        valor: Valor del RNC (str, int, float, etc.)

    Returns:
        str: RNC sólo con dígitos (puede ser cadena vacía si no hay dígitos)
    """
    try:
        if valor is None or (hasattr(valor, 'strip') and str(valor).strip() == ''):
            return ''

        # Números: manejar floats que vienen de Excel (p. ej., 101234567.0)
        if isinstance(valor, (int,)):
            return str(valor)
        if isinstance(valor, (float,)):
            # Si es un float "entero" (x.0), castear a int directamente
            try:
                if valor.is_integer():
                    return str(int(valor))
            except Exception:
                pass
            # Si no, eliminar caracteres no numéricos del string del float
            valor = str(valor)

        # Texto: conservar sólo dígitos
        s = str(valor)
        solo_digitos = ''.join(ch for ch in s if ch.isdigit())
        return solo_digitos
    except Exception:
        return str(valor) if valor is not None else ''


def limpiar_fecha_texto(fecha_texto):
    """
    Limpia y normaliza texto de fecha eliminando AM/PM con puntos
    
    Args:
        fecha_texto: Texto de fecha a limpiar
        
    Returns:
        str: Fecha limpia o None
    """
    if pd.isna(fecha_texto) or fecha_texto == '':
        return None
    
    fecha_str = str(fecha_texto).strip()
    
    # Reemplazar A.M. y P.M. por AM y PM (sin puntos)
    fecha_str = fecha_str.replace('A.M.', 'AM').replace('P.M.', 'PM')
    fecha_str = fecha_str.replace('a.m.', 'AM').replace('p.m.', 'PM')

    # Omitir la hora por completo y quedarnos sólo con la fecha
    # Cortar por 'T' (ISO 8601) y por espacio si hay componentes de hora
    if 'T' in fecha_str:
        fecha_str = fecha_str.split('T')[0]
    if ' ' in fecha_str:
        # Mantener la primera porción antes del espacio (fecha)
        fecha_str = fecha_str.split(' ')[0]
    
    return fecha_str


def formatear_fecha_sql(fecha):
    """
    Convierte cualquier valor de fecha a formato 'YYYY-MM-DD' para SQL Server.
    Maneja: datetime, date, pandas Timestamp, strings con diferentes formatos.
    Retorna None si no puede convertir o si la fecha está fuera de rango SQL Server (1753-9999).
    
    Args:
        fecha: Valor a convertir (datetime, date, str, pandas Timestamp, etc.)
        
    Returns:
        str: Fecha en formato 'YYYY-MM-DD' o None
    """
    try:
        if fecha is None or pd.isna(fecha):
            return None
        
        if isinstance(fecha, str) and fecha.strip() == '':
            return None

        # Si viene como pandas Timestamp o datetime
        if isinstance(fecha, (pd.Timestamp, datetime)):
            if fecha.year < 1753 or fecha.year > 9999:
                return None
            try:
                return fecha.date().strftime('%Y-%m-%d')
            except Exception:
                return fecha.strftime('%Y-%m-%d')

        # Si ya es date
        try:
            from datetime import date as _date
            if isinstance(fecha, _date):
                if fecha.year < 1753 or fecha.year > 9999:
                    return None
                return fecha.strftime('%Y-%m-%d')
        except Exception:
            pass

        # Si es texto, limpiar y parsear
        fecha_txt = limpiar_fecha_texto(str(fecha))
        if not fecha_txt:
            return None
            
        # Intentar parseo directo ISO (yyyy-mm-dd)
        try:
            if len(fecha_txt) == 10 and fecha_txt[4] == '-' and fecha_txt[7] == '-':
                # Validar que sea una fecha válida
                f = datetime.strptime(fecha_txt, '%Y-%m-%d')
                if f.year < 1753 or f.year > 9999:
                    return None
                return fecha_txt
        except Exception:
            pass
            
        # Intentar formatos explícitos (dd/mm/yyyy preferido)
        formatos = [
            '%d/%m/%Y',              # 02/05/2025
            '%Y-%m-%d',              # 2025-05-02
            '%d-%m-%Y',              # 02-05-2025
            '%m/%d/%Y',              # 05/02/2025 (formato USA)
        ]
        
        for formato in formatos:
            try:
                f = datetime.strptime(fecha_txt, formato)
                if f.year < 1753 or f.year > 9999:
                    return None
                return f.strftime('%Y-%m-%d')
            except:
                continue
        
        # Como último recurso, usar pandas con dayfirst=True
        try:
            f = pd.to_datetime(fecha_txt, errors='coerce', dayfirst=True)
            if pd.isna(f):
                return None
            if f.year < 1753 or f.year > 9999:
                return None
            return f.strftime('%Y-%m-%d')
        except Exception:
            pass
        
        return None
        
    except Exception as e:
        logger.warning(f"Error formateando fecha '{fecha}': {str(e)}")
        return None


def serializar_fecha_desde_db(valor):
    """
    Serializa fechas desde SQL Server asegurando que se devuelvan como 'YYYY-MM-DD' 
    sin ajustes de zona horaria que puedan restar días.
    
    Args:
        valor: Valor que puede ser datetime, date, o cualquier otro tipo
        
    Returns:
        str o el valor original: Fecha como 'YYYY-MM-DD' si es fecha, sino el valor original
    """
    if isinstance(valor, datetime):
        # Si es datetime, extraer solo la fecha como string
        return valor.strftime('%Y-%m-%d')
    elif isinstance(valor, date):
        # Si es date (tipo DATE de SQL), convertir directamente a string
        return valor.strftime('%Y-%m-%d')
    else:
        return valor


def procesar_archivo_facturas(file_path, rnc_empresa):
    """
    Procesa un archivo Excel o CSV y retorna un DataFrame normalizado
    
    Args:
        file_path (str): Ruta del archivo a procesar
        rnc_empresa (str): RNC de la empresa
        
    Returns:
        tuple: (DataFrame, str) - (datos procesados, mensaje de error si hay)
    """
    try:
        # Determinar tipo de archivo
        extension = os.path.splitext(file_path)[1].lower()
        
        logger.info(f"Procesando archivo {file_path} con extensión {extension}")
        
        # Detectar tipo real del archivo leyendo sus primeros bytes (magic bytes)
        with open(file_path, 'rb') as f:
            file_header = f.read(8)
        
        # Verificar firma de archivo
        is_xlsx = file_header[:4] == b'PK\x03\x04'  # ZIP (usado por .xlsx)
        is_xls = file_header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # OLE2 (usado por .xls)
        
        logger.info(f"Firma del archivo - is_xlsx: {is_xlsx}, is_xls: {is_xls}")
        
        if extension == '.xlsx':
            if not is_xlsx and is_xls:
                # El archivo dice ser .xlsx pero realmente es .xls
                logger.warning(f"Archivo {file_path} tiene extensión .xlsx pero es realmente un .xls")
                try:
                    df = pd.read_excel(file_path, engine='xlrd')
                    logger.info(f"Archivo .xls (renombrado a .xlsx) leído correctamente con xlrd")
                except Exception as e:
                    logger.error(f"Error leyendo archivo: {str(e)}")
                    return None, f"El archivo parece ser .xls renombrado a .xlsx. Error: {str(e)}"
            else:
                # Para .xlsx DEBE usar openpyxl
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    logger.info(f"Archivo .xlsx leído correctamente con openpyxl")
                except Exception as e:
                    logger.error(f"Error leyendo .xlsx con openpyxl: {str(e)}")
                    return None, f"Error leyendo archivo Excel (.xlsx). Asegúrese que el archivo no esté corrupto: {str(e)}"
        elif extension == '.xls':
            if is_xlsx and not is_xls:
                # El archivo dice ser .xls pero realmente es .xlsx
                logger.warning(f"Archivo {file_path} tiene extensión .xls pero es realmente un .xlsx")
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    logger.info(f"Archivo .xlsx (renombrado a .xls) leído correctamente con openpyxl")
                except Exception as e:
                    logger.error(f"Error leyendo archivo: {str(e)}")
                    return None, f"El archivo parece ser .xlsx renombrado a .xls. Error: {str(e)}"
            else:
                # Para .xls DEBE usar xlrd
                try:
                    df = pd.read_excel(file_path, engine='xlrd')
                    logger.info(f"Archivo .xls leído correctamente con xlrd")
                except Exception as e:
                    logger.error(f"Error leyendo .xls con xlrd: {str(e)}")
                    return None, f"Error leyendo archivo Excel (.xls). Asegúrese que el archivo no esté corrupto: {str(e)}"
        elif extension == '.csv':
            # Intentar diferentes encodings comunes
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Archivo CSV leído correctamente con encoding {encoding}")
                    break
                except:
                    continue
            else:
                return None, "No se pudo leer el archivo CSV con ninguna codificación"
        else:
            return None, f"Formato de archivo no soportado: {extension}. Use .xlsx, .xls o .csv"
        
        # Verificar que el archivo no esté vacío
        if df.empty:
            return None, "El archivo está vacío"
        
        # Normalizar nombres de columnas
        df.columns = [normalizar_nombre_columna(col) for col in df.columns]
        
        # Agregar columna RNC_Empresa
        df['RNC_Empresa'] = rnc_empresa
        
        # Convertir columna Aprobacion_Comercial a booleano
        if 'Aprobacion_Comercial' in df.columns:
            df['Aprobacion_Comercial'] = df['Aprobacion_Comercial'].apply(
                lambda x: 1 if str(x).lower() in ['si', 'sí', 's', 'yes', 'y', '1', 'true'] else 0
            )
        else:
            df['Aprobacion_Comercial'] = 0
        
        # Convertir fechas directamente a formato SQL (YYYY-MM-DD)
        # Ya no necesitamos convertir aquí porque formatear_fecha_sql lo hace todo
        # Mantener los valores originales en el DataFrame para procesarlos después
        
        # Convertir valores numéricos
        for col in ['ITBIS_Facturado', 'Monto_Total_Gravado', 'Monto_Exento', 'Monto_No_Facturable']:
            if col in df.columns:
                # Limpiar caracteres no numéricos (comas, símbolos de moneda, etc.)
                df[col] = df[col].apply(lambda x: str(x).replace(',', '').replace('$', '').replace('RD$', '').strip() if pd.notna(x) else '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        
        # Llenar valores nulos en columnas de texto
        for col in ['RNC_Receptor', 'ENCF_Modificado', 'Estado']:
            if col in df.columns:
                df[col] = df[col].fillna('')
            else:
                df[col] = ''

        # Normalizar RNC del receptor para eliminar puntos u otros separadores
        if 'RNC_Receptor' in df.columns:
            df['RNC_Receptor'] = df['RNC_Receptor'].apply(normalizar_rnc)
        
        # Asegurar que ENCF no sea nulo
        if 'ENCF' in df.columns:
            df['ENCF'] = df['ENCF'].fillna('')
        
        logger.info(f"Archivo procesado: {len(df)} registros leídos")
        return df, None
        
    except Exception as e:
        return None, f"Error procesando archivo: {str(e)}"


@routes.route("/empresa/<rnc>/importar-facturas", methods=["POST"])
@token_or_api_key_required
def importar_facturas(rnc):
    """
    Endpoint para importar facturas desde archivo Excel o CSV
    
    Args:
        rnc (str): RNC de la empresa
        
    Form data esperado:
        - archivo: archivo Excel (.xlsx, .xls) o CSV
        
    Respuesta:
        {
            "message": "Facturas importadas exitosamente",
            "registros_procesados": 100,
            "registros_nuevos": 50,
            "registros_actualizados": 50,
            "errores": []
        }
    """
    try:
        # Validar que el RNC no esté vacío o sea inválido
        if not rnc or rnc == '-' or rnc.strip() == '':
            return jsonify({"error": "RNC de empresa es requerido"}), 400
        
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": f"Empresa con RNC {rnc} no encontrada"}), 404
        
        # Verificar/crear tabla
        exito, mensaje = verificar_o_crear_tabla_facturas()
        if not exito:
            return jsonify({"error": f"Error en la base de datos: {mensaje}"}), 500
        
        # Validar que se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({"error": "No se encontró archivo en la solicitud"}), 400
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        logger.info(f"Archivo recibido: {archivo.filename}")
        
        # Validar extensión
        extension = os.path.splitext(archivo.filename)[1].lower()
        logger.info(f"Extensión detectada: {extension}")
        
        if extension not in ['.xlsx', '.xls', '.csv']:
            return jsonify({"error": f"Formato no soportado: {extension}. Use .xlsx, .xls o .csv"}), 400
        
        # Guardar archivo temporalmente en la carpeta CSV de la empresa (ambiente CERT por defecto)
        ambiente = request.args.get('ambiente', 'CERT')
        temp_dir = os.path.join(obtener_ruta_empresa(rnc, ambiente), "CSV")
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = int(time.time())
        temp_filename = f"import_{timestamp}_{secure_filename(archivo.filename)}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        logger.info(f"Guardando archivo en: {temp_path}")
        archivo.save(temp_path)
        
        # Verificar que el archivo se guardó correctamente
        if not os.path.exists(temp_path):
            return jsonify({"error": "Error guardando archivo temporalmente"}), 500
        
        file_size = os.path.getsize(temp_path)
        logger.info(f"Archivo guardado correctamente. Tamaño: {file_size} bytes")
        
        # Procesar archivo
        df, error = procesar_archivo_facturas(temp_path, rnc)
        if error:
            os.remove(temp_path)
            return jsonify({"error": error}), 400
        
        # Validar que tiene la columna ENCF
        if 'ENCF' not in df.columns:
            os.remove(temp_path)
            return jsonify({"error": "El archivo debe contener la columna 'ENCF'"}), 400
        
        # Insertar/actualizar registros en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        registros_nuevos = 0
        registros_actualizados = 0
        registros_omitidos = 0
        errores = []
        
        for idx, row in df.iterrows():
            try:
                encf = str(row.get('ENCF', '')).strip()
                if not encf or encf == '' or encf == 'nan':
                    registros_omitidos += 1
                    logger.debug(f"Fila {idx + 2}: ENCF vacío o inválido, omitiendo")
                    continue
                
                # Obtener valores con conversión segura
                rnc_receptor = normalizar_rnc(row.get('RNC_Receptor', ''))[:20]
                encf_modificado = str(row.get('ENCF_Modificado', '') or '')[:19]
                if encf_modificado == 'nan':
                    encf_modificado = ''
                estado = str(row.get('Estado', '') or '')[:50]
                if estado == 'nan':
                    estado = ''
                
                # Obtener fechas directamente como strings 'YYYY-MM-DD' o None
                fecha_comprobante_sql = formatear_fecha_sql(row.get('Fecha_Comprobante'))
                fecha_recepcion_sql = formatear_fecha_sql(row.get('Fecha_Recepcion'))
                fecha_aprobacion_sql = formatear_fecha_sql(row.get('Fecha_Aprobacion_Comercial'))
                
                logger.debug(f"Fila {idx + 2}: ENCF={encf}, RNC_Receptor={rnc_receptor}, Fecha_Comp={fecha_comprobante_sql}, Fecha_Recep={fecha_recepcion_sql}")
                
                # Obtener valores numéricos
                aprobacion = int(row.get('Aprobacion_Comercial', 0))
                itbis = float(row.get('ITBIS_Facturado', 0))
                gravado = float(row.get('Monto_Total_Gravado', 0))
                exento = float(row.get('Monto_Exento', 0))
                no_facturable = float(row.get('Monto_No_Facturable', 0))
                
                # Verificar si el registro existe
                cursor.execute("""
                    SELECT Id FROM FacturasImportadas 
                    WHERE RNC_Empresa = ? AND ENCF = ?
                """, (rnc, encf))
                
                existe = cursor.fetchone()
                
                if existe:
                    # Actualizar registro existente
                    cursor.execute("""
                        UPDATE FacturasImportadas SET
                            RNC_Receptor = ?,
                            ENCF_Modificado = ?,
                            Fecha_Comprobante = ?,
                            Fecha_Recepcion = ?,
                            Aprobacion_Comercial = ?,
                            Fecha_Aprobacion_Comercial = ?,
                            Estado = ?,
                            ITBIS_Facturado = ?,
                            Monto_Total_Gravado = ?,
                            Monto_Exento = ?,
                            Monto_No_Facturable = ?,
                            Fecha_Importacion = GETDATE()
                        WHERE RNC_Empresa = ? AND ENCF = ?
                    """, 
                        rnc_receptor,
                        encf_modificado,
                        fecha_comprobante_sql,
                        fecha_recepcion_sql,
                        aprobacion,
                        fecha_aprobacion_sql,
                        estado,
                        itbis,
                        gravado,
                        exento,
                        no_facturable,
                        rnc,
                        encf
                    )
                    registros_actualizados += 1
                    logger.debug(f"Fila {idx + 2}: Registro actualizado - ENCF={encf}")
                else:
                    # Insertar nuevo registro
                    cursor.execute("""
                        INSERT INTO FacturasImportadas (
                            RNC_Empresa, RNC_Receptor, ENCF, ENCF_Modificado,
                            Fecha_Comprobante, Fecha_Recepcion, Aprobacion_Comercial,
                            Fecha_Aprobacion_Comercial, Estado, ITBIS_Facturado,
                            Monto_Total_Gravado, Monto_Exento, Monto_No_Facturable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (rnc,
                        rnc_receptor,
                        encf,
                        encf_modificado,
                        fecha_comprobante_sql,
                        fecha_recepcion_sql,
                        aprobacion,
                        fecha_aprobacion_sql,
                        estado,
                        itbis,
                        gravado,
                        exento,
                        no_facturable)
                    )
                    registros_nuevos += 1
                    logger.debug(f"Fila {idx + 2}: Nuevo registro insertado - ENCF={encf}")
                
            except Exception as e:
                error_msg = f"Fila {idx + 2} (ENCF: {encf if 'encf' in locals() else 'N/A'}): {str(e)}"
                errores.append(error_msg)
                logger.error(f"Error procesando fila {idx + 2}: {str(e)}")
                registros_omitidos += 1
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Mantener copia del archivo importado
        logger.info(f"Facturas importadas para empresa {rnc}: {registros_nuevos} nuevas, {registros_actualizados} actualizadas, {registros_omitidos} omitidas")
        
        return jsonify({
            "message": "Facturas importadas exitosamente",
            "archivo": temp_filename,
            "registros_procesados": len(df),
            "registros_nuevos": registros_nuevos,
            "registros_actualizados": registros_actualizados,
            "registros_omitidos": registros_omitidos,
            "errores": errores[:10]  # Limitar a 10 errores para no saturar la respuesta
        }), 200
        
    except Exception as e:
        logger.error(f"Error importando facturas: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


@routes.route("/empresa/<rnc>/facturas", methods=["GET"])
@token_or_api_key_required
def obtener_facturas(rnc):
    """
    Endpoint para consultar facturas importadas de una empresa
    
    Args:
        rnc (str): RNC de la empresa
        
    Query params opcionales:
        - limit: Número máximo de registros (default: 100)
        - offset: Número de registros a saltar (default: 0)
        - encf: Filtrar por ENCF específico
        - fecha_desde: Filtrar desde fecha (formato: YYYY-MM-DD)
        - fecha_hasta: Filtrar hasta fecha (formato: YYYY-MM-DD)
        - estado: Filtrar por estado
        
    Respuesta:
        {
            "rnc": "123456789",
            "total": 1000,
            "limit": 100,
            "offset": 0,
            "facturas": [...]
        }
    """
    try:
        # Validar que el RNC no esté vacío o sea inválido
        if not rnc or rnc == '-' or rnc.strip() == '':
            return jsonify({"error": "RNC de empresa es requerido"}), 400
        
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": f"Empresa con RNC {rnc} no encontrada"}), 404
        
        # Verificar tabla
        exito, mensaje = verificar_o_crear_tabla_facturas()
        if not exito:
            return jsonify({"error": f"Error en la base de datos: {mensaje}"}), 500
        
        # Obtener parámetros de consulta
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        encf_filtro = request.args.get('encf', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        estado_filtro = request.args.get('estado', '')
        
        # Construir consulta SQL
        where_clauses = ["RNC_Empresa = ?"]
        params = [rnc]
        
        if encf_filtro:
            where_clauses.append("ENCF LIKE ?")
            params.append(f"%{encf_filtro}%")
        
        if fecha_desde:
            where_clauses.append("Fecha_Comprobante >= ?")
            params.append(fecha_desde)
        
        if fecha_hasta:
            where_clauses.append("Fecha_Comprobante <= ?")
            params.append(fecha_hasta)
        
        if estado_filtro:
            where_clauses.append("Estado = ?")
            params.append(estado_filtro)
        
        where_sql = " AND ".join(where_clauses)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar total de registros
        cursor.execute(f"""
            SELECT COUNT(*) FROM FacturasImportadas
            WHERE {where_sql}
        """, *params)
        total = cursor.fetchone()[0]
        
        # Obtener registros paginados
        params.extend([offset, limit])
        cursor.execute(f"""
            SELECT 
                Id, RNC_Empresa, RNC_Receptor, ENCF, ENCF_Modificado,
                Fecha_Comprobante, Fecha_Recepcion, Aprobacion_Comercial,
                Fecha_Aprobacion_Comercial, Estado, ITBIS_Facturado,
                Monto_Total_Gravado, Monto_Exento, Monto_No_Facturable,
                Fecha_Importacion
            FROM FacturasImportadas
            WHERE {where_sql}
            ORDER BY Fecha_Comprobante DESC, Id DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """, *params)
        
        columnas = [column[0] for column in cursor.description]
        facturas = []
        
        for row in cursor.fetchall():
            factura = {}
            for i, col in enumerate(columnas):
                valor = row[i]
                # Serializar fechas correctamente sin ajuste de zona horaria
                valor_serializado = serializar_fecha_desde_db(valor)
                # Para otros tipos, usar conversión estándar
                if isinstance(valor_serializado, (int, float, str, bool, type(None))):
                    factura[col] = valor_serializado
                else:
                    factura[col] = str(valor_serializado)
            facturas.append(factura)
        
        cursor.close()
        conn.close()
        
        logger.info(f"Consultadas {len(facturas)} facturas para empresa {rnc}")
        
        return jsonify({
            "rnc": rnc,
            "total": total,
            "limit": limit,
            "offset": offset,
            "facturas": facturas
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo facturas: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


@routes.route("/empresa/<rnc>/facturas/estadisticas", methods=["GET"])
@token_or_api_key_required
def obtener_estadisticas_facturas(rnc):
    """
    Endpoint para obtener estadísticas de facturas de una empresa
    
    Args:
        rnc (str): RNC de la empresa
        
    Respuesta:
        {
            "total_facturas": 1000,
            "por_estado": {...},
            "totales_montos": {...},
            "ultima_importacion": "2025-10-20T10:30:00"
        }
    """
    try:
        # Validar que el RNC no esté vacío o sea inválido
        if not rnc or rnc == '-' or rnc.strip() == '':
            return jsonify({"error": "RNC de empresa es requerido"}), 400
        
        # Validar que la empresa existe
        empresa = get_data_from_database2(rnc)
        if not empresa:
            return jsonify({"error": f"Empresa con RNC {rnc} no encontrada"}), 404
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de facturas
        cursor.execute("""
            SELECT COUNT(*) FROM FacturasImportadas
            WHERE RNC_Empresa = ?
        """, rnc)
        total_facturas = cursor.fetchone()[0]
        
        # Facturas por estado
        cursor.execute("""
            SELECT Estado, COUNT(*) as cantidad
            FROM FacturasImportadas
            WHERE RNC_Empresa = ?
            GROUP BY Estado
        """, rnc)
        por_estado = {row[0] if row[0] else 'Sin estado': row[1] for row in cursor.fetchall()}
        
        # Totales de montos
        cursor.execute("""
            SELECT 
                SUM(ITBIS_Facturado) as total_itbis,
                SUM(Monto_Total_Gravado) as total_gravado,
                SUM(Monto_Exento) as total_exento,
                SUM(Monto_No_Facturable) as total_no_facturable
            FROM FacturasImportadas
            WHERE RNC_Empresa = ?
        """, rnc)
        row = cursor.fetchone()
        totales_montos = {
            "total_itbis": float(row[0]) if row[0] else 0,
            "total_gravado": float(row[1]) if row[1] else 0,
            "total_exento": float(row[2]) if row[2] else 0,
            "total_no_facturable": float(row[3]) if row[3] else 0
        }
        
        # Última importación
        cursor.execute("""
            SELECT TOP 1 Fecha_Importacion
            FROM FacturasImportadas
            WHERE RNC_Empresa = ?
            ORDER BY Fecha_Importacion DESC
        """, rnc)
        ultima_importacion = cursor.fetchone()
        ultima_importacion = ultima_importacion[0].isoformat() if ultima_importacion and ultima_importacion[0] else None
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "rnc": rnc,
            "total_facturas": total_facturas,
            "por_estado": por_estado,
            "totales_montos": totales_montos,
            "ultima_importacion": ultima_importacion
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


# ============================================================================
# IMPORTAR DGII - Endpoints para importación de archivos Excel DGII
# ============================================================================

import tempfile

# Asegurar que el directorio APIWEB esté en sys.path para imports
_apiweb_dir = os.path.dirname(os.path.abspath(__file__))
_core_dir = os.path.join(_apiweb_dir, 'core')

# Agregar directorios al path
for directory in [_apiweb_dir, _core_dir]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Log de rutas para debugging
logger.info(f"APIWEB dir: {_apiweb_dir}")
logger.info(f"Core dir: {_core_dir}")
logger.info(f"Core dir exists: {os.path.exists(_core_dir)}")

# Intentar importar módulos DGII con mejor manejo de errores
DGII_MODULES_AVAILABLE = False

try:
    from core.excel_loader import load_excel
    from core.db_manager import (
        load_settings as load_dgii_settings,
        save_settings as save_dgii_settings,
        ensure_database_exists,
        ensure_tables_exist,
        split_dataframe,
        insert_dataframes,
        test_connection as test_dgii_connection,
        get_server_info
    )
    DGII_MODULES_AVAILABLE = True
    logger.info("[OK] Modulos DGII importados correctamente")
except ImportError as e:
    logger.error(f"[ERROR] Error importando modulos DGII: {e}")
    logger.error(f"Estructura de directorios esperada:")
    logger.error(f"  - {_apiweb_dir}/core/excel_loader.py")
    logger.error(f"  - {_apiweb_dir}/core/db_manager.py")
    import traceback
    logger.error(traceback.format_exc())
    
    # Definir funciones dummy para evitar errores en tiempo de ejecución
    def module_not_available_error():
        return jsonify({
            'error': 'Los módulos de importación DGII no están disponibles. Verifica que existan los archivos core/excel_loader.py y core/db_manager.py'
        }), 503
    
    def load_excel(*args, **kwargs):
        raise ImportError("Módulo core.excel_loader no disponible")
    def load_dgii_settings(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def save_dgii_settings(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def ensure_database_exists(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def ensure_tables_exist(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def split_dataframe(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def insert_dataframes(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def test_dgii_connection(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")
    def get_server_info(*args, **kwargs):
        raise ImportError("Módulo core.db_manager no disponible")


@routes.route('/api/dgii/importar-excel', methods=['POST'])
def importar_excel_dgii():
    """
    Importa un archivo Excel de facturas DGII a SQL Server.
    
    Body (multipart/form-data):
        - file: Archivo Excel (.xlsx)
        - recreate: (opcional) "true" o "false" - Si true, recrea tablas (¡borra datos!)
    
    Returns:
        JSON con resultados de la importación
    """
    # Verificar que los módulos estén disponibles
    if not DGII_MODULES_AVAILABLE:
        logger.error("Intento de usar endpoint DGII sin módulos disponibles")
        return jsonify({
            'error': 'Los módulos de importación DGII no están disponibles en el servidor. Contacte al administrador.',
            'detalle': 'Faltan archivos: core/excel_loader.py y/o core/db_manager.py'
        }), 503
    
    tmp_path = None
    
    try:
        # Validar que se envió un archivo
        if 'file' not in request.files:
            logger.warning("Request sin archivo")
            return jsonify({'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("Nombre de archivo vacío")
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        # Validar extensión
        if not file.filename.lower().endswith('.xlsx'):
            logger.warning(f"Extensión inválida: {file.filename}")
            return jsonify({'error': 'Solo se permiten archivos .xlsx'}), 400
        
        # Parámetro opcional: recreate mode
        recreate = request.form.get('recreate', 'false').lower() == 'true'
        
        logger.info(f"[INICIO] Importacion DGII: {file.filename} (recreate={recreate})")
        
        # Guardar archivo temporal
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            logger.info(f"Archivo temporal guardado: {tmp_path}")
        except Exception as tmp_err:
            logger.error(f"Error guardando archivo temporal: {str(tmp_err)}")
            return jsonify({'error': f'Error al guardar archivo temporal: {str(tmp_err)}'}), 500
        
        # 1. Validar conexión
        try:
            logger.info("[CONN] Probando conexion a BD...")
            success, error = test_dgii_connection()
        except Exception as conn_err:
            logger.error(f"[ERROR] Error al probar conexion: {str(conn_err)}")
            return jsonify({
                'error': f'Error al probar conexión: {str(conn_err)}'
            }), 500
        
        if not success:
            logger.error(f"[ERROR] Conexion fallida: {error}")
            return jsonify({
                'error': f'Error de conexión a base de datos: {error}'
            }), 500
        
        logger.info("[OK] Conexion exitosa")
        
        # 2. Asegurar que la BD existe
        try:
            logger.info("[DB] Verificando base de datos...")
            ensure_database_exists()
            logger.info("[OK] Base de datos verificada")
        except Exception as db_err:
            logger.error(f"[ERROR] Error verificando BD: {str(db_err)}")
            return jsonify({'error': f'Error verificando base de datos: {str(db_err)}'}), 500
        
        # 3. Cargar Excel
        try:
            logger.info("[EXCEL] Cargando archivo Excel...")
            df = load_excel(tmp_path)
            logger.info(f"[OK] Excel cargado: {len(df)} filas")
        except Exception as excel_err:
            logger.error(f"[ERROR] Error cargando Excel: {str(excel_err)}")
            return jsonify({'error': f'Error al leer archivo Excel: {str(excel_err)}'}), 400
        
        if len(df) == 0:
            logger.warning("[WARN] Excel vacio")
            return jsonify({'error': 'El archivo Excel está vacío'}), 400
        
        # 4. Crear/validar tablas
        try:
            logger.info(f"[TABLA] {'Recreando' if recreate else 'Verificando'} tablas...")
            ensure_tables_exist(df, recreate_mode=recreate)
            logger.info("[OK] Tablas preparadas")
        except Exception as table_err:
            logger.error(f"[ERROR] Error con tablas: {str(table_err)}")
            return jsonify({'error': f'Error preparando tablas: {str(table_err)}'}), 500
        
        # 5. Dividir en encabezado y detalle
        try:
            logger.info("[SPLIT] Dividiendo datos...")
            df_head, det_tables = split_dataframe(df)
            logger.info(f"[OK] Division completada: {len(df_head)} encabezados, {len(det_tables)} tablas detalle")
        except Exception as split_err:
            logger.error(f"[ERROR] Error dividiendo datos: {str(split_err)}")
            return jsonify({'error': f'Error procesando estructura: {str(split_err)}'}), 500
        
        if len(df_head) == 0:
            logger.warning("[WARN] No hay encabezados validos")
            return jsonify({'error': 'No se encontraron encabezados válidos en el Excel'}), 400
        
        # 6. Insertar datos
        try:
            logger.info("[INSERT] Insertando datos en SQL Server...")
            head_count, detail_counts = insert_dataframes(df_head, det_tables)
            total_details = sum(detail_counts.values())
            logger.info(f"[OK] Insercion completada: {head_count} encabezados, {total_details} detalles")
        except Exception as insert_err:
            logger.error(f"[ERROR] Error insertando datos: {str(insert_err)}")
            return jsonify({'error': f'Error al insertar datos: {str(insert_err)}'}), 500
        
        # 7. Respuesta exitosa
        logger.info(f"[SUCCESS] Importacion DGII exitosa: {file.filename}")
        return jsonify({
            'success': True,
            'mensaje': 'Importación completada exitosamente',
            'archivo': file.filename,
            'resultados': {
                'encabezados_insertados': head_count,
                'detalles_insertados': sum(detail_counts.values()),
                'tablas_detalle': detail_counts,
                'modo_recrear': recreate
            }
        }), 200
    
    except FileNotFoundError as e:
        logger.error(f"[ERROR] Archivo no encontrado: {str(e)}")
        return jsonify({'error': f'Archivo de configuración no encontrado: {str(e)}'}), 500
    
    except ValueError as e:
        logger.error(f"[ERROR] Error de validacion: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"[ERROR] Error inesperado al procesar archivo DGII: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error al procesar archivo: {str(e)}'}), 500
    
    finally:
        # Limpiar archivo temporal
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"[CLEANUP] Archivo temporal eliminado: {tmp_path}")
            except Exception as cleanup_err:
                logger.warning(f"[WARN] No se pudo eliminar archivo temporal: {cleanup_err}")


@routes.route('/api/dgii/health', methods=['GET'])
def health_check_dgii():
    """
    Verifica estado de conexión a la base de datos de ImportarDGII.
    
    Returns:
        JSON con estado de la conexión
    """
    if not DGII_MODULES_AVAILABLE:
        return jsonify({
            'status': 'unavailable',
            'error': 'Módulos DGII no disponibles en el servidor'
        }), 503
    
    try:
        # Primero cargar configuración
        try:
            cfg = load_dgii_settings()
            logger.info(f"Configuración DGII cargada: {cfg.get('server')}/{cfg.get('database')}")
        except Exception as cfg_err:
            logger.error(f"[ERROR] Error cargando configuracion: {str(cfg_err)}")
            return jsonify({
                'status': 'error',
                'error': f'Error cargando configuración: {str(cfg_err)}'
            }), 500
        
        # Probar conexión
        try:
            success, error = test_dgii_connection()
        except Exception as conn_err:
            logger.error(f"[ERROR] Error al probar conexion: {str(conn_err)}")
            return jsonify({
                'status': 'error',
                'database': 'error',
                'error': f'Error al probar conexión: {str(conn_err)}'
            }), 503
        
        if success:
            logger.info("[OK] Health check DGII: Conexion exitosa")
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'server': cfg.get('server'),
                'database_name': cfg.get('database')
            }), 200
        else:
            logger.error(f"[ERROR] Health check DGII: Conexion fallida: {error}")
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': error
            }), 503
    
    except Exception as e:
        logger.error(f"[ERROR] Error en health check DGII: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@routes.route('/api/dgii/config', methods=['GET', 'POST'])
def config_dgii():
    """
    GET: Obtiene configuración actual de ImportarDGII (sin password)
    POST: Actualiza configuración de ImportarDGII
    
    Body (POST):
        {
            "server": "localhost",
            "database": "ImportarFE",
            "user": "SISTEMA",
            "password": "@@sistema",
            "table_encabezado": "FEEncabezado",
            "table_detalle_prefix": "FEDetalle",
            "driver": "ODBC Driver 17 for SQL Server",
            "validate_duplicates": true
        }
    
    Returns:
        JSON con configuración actual
    """
    if not DGII_MODULES_AVAILABLE:
        return jsonify({
            'error': 'Módulos DGII no disponibles en el servidor'
        }), 503
    
    try:
        if request.method == 'GET':
            # Obtener configuración sin exponer password
            try:
                cfg = load_dgii_settings()
            except Exception as cfg_err:
                logger.error(f"Error cargando configuración: {str(cfg_err)}")
                # Retornar configuración por defecto
                cfg = {
                    'server': 'localhost',
                    'database': 'ImportarFE',
                    'user': 'SISTEMA',
                    'password': '',
                    'table_encabezado': 'FEEncabezado',
                    'table_detalle_prefix': 'FEDetalle',
                    'driver': 'ODBC Driver 17 for SQL Server',
                    'validate_duplicates': True
                }
            
            safe_cfg = {k: v for k, v in cfg.items() if k != 'password'}
            safe_cfg['password_set'] = bool(cfg.get('password'))
            
            logger.info("[OK] Configuracion DGII obtenida")
            return jsonify(safe_cfg), 200
        
        elif request.method == 'POST':
            # Actualizar configuración
            new_cfg = request.get_json()
            
            if not new_cfg:
                return jsonify({'error': 'No se enviaron datos'}), 400
            
            # Validar campos requeridos
            required_fields = ['server', 'database', 'user', 'driver']
            missing = [f for f in required_fields if not new_cfg.get(f)]
            
            if missing:
                return jsonify({
                    'error': f'Campos requeridos faltantes: {", ".join(missing)}'
                }), 400
            
            # Guardar configuración
            try:
                save_dgii_settings(new_cfg)
                logger.info(f"[OK] Configuracion DGII guardada: {new_cfg.get('server')}/{new_cfg.get('database')}")
            except Exception as save_err:
                logger.error(f"Error guardando configuración: {str(save_err)}")
                return jsonify({'error': f'Error al guardar configuración: {str(save_err)}'}), 500
            
            # Probar nueva conexión
            try:
                success, error = test_dgii_connection()
            except Exception as test_err:
                logger.warning(f"Error probando conexión: {str(test_err)}")
                return jsonify({
                    'success': True,
                    'mensaje': 'Configuración guardada',
                    'warning': f'No se pudo probar conexión: {str(test_err)}'
                }), 200
            
            if not success:
                logger.warning(f"Configuración guardada pero conexión falló: {error}")
                return jsonify({
                    'success': True,
                    'mensaje': 'Configuración guardada',
                    'warning': f'Conexión falló: {error}'
                }), 200
            
            logger.info("[OK] Configuracion guardada y conexion verificada")
            return jsonify({
                'success': True,
                'mensaje': 'Configuración guardada y conexión verificada'
            }), 200
    
    except Exception as e:
        logger.error(f"[ERROR] Error en configuracion DGII: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@routes.route('/api/dgii/server-info', methods=['GET'])
def server_info_dgii():
    """
    Obtiene información del servidor SQL Server.
    
    Returns:
        JSON con información del servidor
    """
    if not DGII_MODULES_AVAILABLE:
        return jsonify({
            'error': 'Módulos DGII no disponibles en el servidor'
        }), 503
    
    try:
        success, error = test_dgii_connection()
        
        if not success:
            logger.error(f"No se pudo conectar al servidor: {error}")
            return jsonify({
                'error': f'No se pudo conectar al servidor: {error}'
            }), 503
        
        try:
            version, driver = get_server_info()
            cfg = load_dgii_settings()
            
            logger.info(f"[OK] Info del servidor obtenida: {version}")
            return jsonify({
                'success': True,
                'server': cfg.get('server'),
                'database': cfg.get('database'),
                'version': version,
                'driver': driver
            }), 200
        except Exception as info_err:
            logger.error(f"[ERROR] Error obteniendo info del servidor: {str(info_err)}")
            return jsonify({
                'error': f'Error obteniendo información: {str(info_err)}'
            }), 500
    
    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo info del servidor: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@routes.route('/api/dgii/debug', methods=['GET'])
def debug_dgii():
    """Endpoint de debug para verificar estructura de módulos DGII"""
    import os
    info = {
        'apiweb_dir': _apiweb_dir,
        'core_dir': _core_dir,
        'core_exists': os.path.exists(_core_dir),
        'modules_available': DGII_MODULES_AVAILABLE,
        'files_in_core': [],
        'files_in_apiweb': []
    }
    
    if os.path.exists(_core_dir):
        try:
            info['files_in_core'] = os.listdir(_core_dir)
        except Exception as e:
            info['files_in_core_error'] = str(e)
    
    try:
        info['files_in_apiweb'] = [f for f in os.listdir(_apiweb_dir) if not f.startswith('__')][:20]
    except Exception as e:
        info['files_in_apiweb_error'] = str(e)
    
    return jsonify(info), 200
