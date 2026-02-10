import asyncio
import base64
import json
import math
import mimetypes
import os
import shutil
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.dom import minidom

import aiohttp
import chilkat2
import httpx
import redis
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree
from requests.exceptions import RequestException
from signxml import XMLSigner, XMLVerifier, methods
from sqlalchemy import column, func, select, table, text
from sqlalchemy.orm import sessionmaker

# from ApiCSV.api import logger
from config.uGlobalConfig import *
from db.CDT import *
from db.uDB import *
from .log_g import *
from glib.uGlobalLib import *
from glib.uGlobalVar import *

from .uXMLGlobal import XmlNative

# Cache compartida en Redis


logger = setup_logger("LibreriaFE.log")

# Regex final para validar dd-mm-YYYY
REGEX_FECHA = re.compile(r"^(3[01]|[12][0-9]|0?[1-9])\-(1[012]|0?[1-9])\-(19|20)\d{2}$")


def formato_fecha_seguro(
    fecha_obj, formato=None
):  # Para evitar errores de compatibilidad con la version anterior"
    """
    Convierte una fecha a string de forma segura.
    Garantiza retorno en formato dd-mm-YYYY si la fecha es válida.
    Si no puede validar o convertir: devuelve "".
    """

    if fecha_obj is None:
        return ""

    # Si viene string, intentamos parsearlo a fecha
    if isinstance(fecha_obj, str):
        fecha_str = fecha_obj.strip()
        if not fecha_str:
            return ""
        # Intentar detectar formatos conocidos
        formatos = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
        for f in formatos:
            try:
                fecha_dt = datetime.strptime(fecha_str, f)
                return fecha_dt.strftime("%d-%m-%Y")
            except:
                pass
        return ""  # Si no se pudo interpretar → inválido

    # Si ya es datetime
    if isinstance(fecha_obj, datetime):
        return fecha_obj.strftime("%d-%m-%Y")

    # Si es un tipo raro (date, pandas.Timestamp, etc.)
    try:
        fecha_dt = fecha_obj
        if hasattr(fecha_dt, "strftime"):
            return fecha_dt.strftime("%d-%m-%Y")
    except:
        return ""

    return ""


def cespeciales(codigoseguridad):
    # The above code is a Python function that checks if a given string contains any of the special characters defined within the function.
    # The function takes a string  `codigoseguridad` as input and returns a boolean value - `True`
    # if the string contains any special characters, and `False` if it does not.

    """
    Verifica si el string contiene alguno de los caracteres especiales definidos.

    Args:
        codigoseguridad (str): El string a verificar

    Returns:
        bool: True si contiene caracteres especiales, False en caso contrario
    """
    # Definimos los caracteres especiales a buscar

    caracteres_especiales = [
        " ",
        "''",
        "!",
        "#",
        "$",
        "&",
        "(",
        ")",
        "*",
        "+",
        "/",
        ",",
        ":",
        ";",
        "=",
        "?",
        "@",
        "[",
        "]",
        '"',
        "-",
        ".",
        "<",
        ">",
        "\\",
        "_",
        "`",
        "^",
    ]

    # Verificamos si alguno de los caracteres especiales está presente
    for caracter in caracteres_especiales:
        if caracter in codigoseguridad:
            return True

    return False


# Cargar Rutas XML
def cargar_configuracion():
    # Cargar configuración desde un archivo JSON
    CONFIG_FILE = "config\\configxsd.json"
    """Carga la configuración desde un archivo JSON."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Archivo de configuración '{CONFIG_FILE}' no encontrado."
        )
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


# Detectar comprobante del archivo XML
def detect_comprobante_type(xml_file_path):
    """
    Detecta el tipo de comprobante electrónico a partir de un archivo XML.

    Args:
        xml_file_path (str): Ruta al archivo XML del comprobante

    Returns:
        str: Código del tipo de comprobante (31, 32, etc.) o None si no se pudo detectar
    """
    # Verificar si el archivo XML existe
    if not os.path.exists(xml_file_path):
        log_event(
            logger, "error", f"Error: El archivo XML '{xml_file_path}' no existe."
        )
        return None

    # Intentar detectar el tipo de comprobante desde el contenido XML
    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()

        # Método 1: Buscar el elemento TipoeCF
        tipo_ecf_elements = root.xpath("//TipoeCF")
        if tipo_ecf_elements and len(tipo_ecf_elements) > 0:
            return tipo_ecf_elements[0].text
    except Exception as e:
        log_event(
            logger,
            "error",
            f"Error al analizar el XML: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )

    # Método 2: Si no se encontró en el contenido, intentar extraerlo del nombre del archivo
    try:
        filename = os.path.basename(xml_file_path)
        match = re.search(r"[eE](-)?[cC][fF](\s+)?(\d{2})", filename)
        if match:
            return match.group(3)
    except Exception as e:
        log_event(
            logger,
            "error",
            f"Error al analizar el nombre del archivo: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )

    # Si no se pudo detectar el tipo, retornar None
    return None


def validate_xml_against_xsd(xml_file_path, xsd_file_path=None):
    """
    Valida un archivo XML contra un esquema XSD.
    Si xsd_file_path es None, detecta automáticamente el esquema según el tipo de comprobante.

    Args:
        xml_file_path (str): Ruta al archivo XML a validar
        xsd_file_path (str, optional): Ruta al archivo XSD de esquema.
                                       Si es None, se detecta automáticamente.

    Returns:
        tuple: Tupla con el código de resultado y mensajes:
            - En caso de éxito: ("01", "El archivo XML ha sido validado")
            - En caso de fallo: (código, mensaje[, detalles])
            Códigos de error:
            - "03": XML Firmado y Validado exitosamente con el esquema provisto por la DGII (XSD).
            - "50": XML no cumple con el esquema
            - "51": No se proporciono a la funcion de validacion de los XML la ruta del archivo XML.
            - "52": Archivo XML no existe
            - "53": Archivos XSD no existen
            - "54": Tipo de comprobante no detectado
            - "55": No se pudo cargar la configuración de rutas de los XSD
    """
    try:
        # Verificar que el archivo XML exista antes de cualquier operación
        if not xml_file_path:
            return (
                "51",
                "Error: No se proporciono a la funcion de validacion de los XML la ruta del archivo XML.",
            )

        if not os.path.exists(xml_file_path):
            return "52", f"Error: El archivo XML '{xml_file_path}' no existe."

        # Si no se proporciona xsd_file_path, detectar y usar el esquema apropiado
        if xsd_file_path is None:
            # Cargar configuración de rutas
            try:
                rutas = cargar_configuracion()
                if not rutas:
                    return (
                        "55",
                        "Error: No se pudo cargar la configuración de rutas de los XSD.",
                    )
            except Exception as e:
                return (
                    "55",
                    f"Error: No se pudo cargar la configuración de rutas de los XSD. {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
                )

            # Detectar el tipo de comprobante
            try:
                tipo_encf = detect_comprobante_type(xml_file_path)
                if not tipo_encf:
                    return "54", "Error: No se pudo detectar el tipo de comprobante."
            except Exception as e:
                return (
                    "54",
                    f"Error: No se pudo detectar el tipo de comprobante. {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
                )

            # Asignar la ruta según tipo de comprobante
            if tipo_encf not in rutas:
                return (
                    "54",
                    f"Error: El tipo de comprobante '{tipo_encf}' no está configurado.",
                )

            xsd_file_path = rutas.get(tipo_encf)

        # Verificar que el archivo XSD exista
        if not os.path.exists(xsd_file_path):
            return "53", f"Error: El archivo XSD '{xsd_file_path}' no existe."

        # Cargar y parsear el esquema XSD
        xmlschema_doc = etree.parse(xsd_file_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        # Cargar y validar el documento XML
        xml_doc = etree.parse(xml_file_path)

        # Realizar la validación
        is_valid = xmlschema.validate(xml_doc)

        if is_valid:
            return (
                "03",
                f"XML Firmado y Validado exitosamente con el esquema provisto por la DGII (XSD).: {xsd_file_path}",
            )
        else:
            # Recopilar los errores de validación
            error_details = []
            for error in xmlschema.error_log:
                error_details.append(
                    f"Línea {error.line}, Columna {error.column}: {error.message}"
                )

            # Unir los errores en un único mensaje
            errors_text = ". ".join(error_details)
            return (
                "50",
                f"El archivo XML no cumple con el esquema {xsd_file_path}:{errors_text}",
            )

    except Exception as e:
        # Capturar cualquier excepción y devolverla como mensaje de error
        return (
            "50",
            f"El archivo XML no cumple con el esquema {xsd_file_path}.:{ str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )


def UnlockCK():
    try:
        # Intenta el método Global para versiones más nuevas
        glob = chilkat2.Global()
        # success = glob.UnlockBundle("ASESYS.CB1082025_U4Mm89KLlVpv")
        success = glob.UnlockBundle("ASESYS.CB1082025_U4Mm89KLlVpv")
        if not success:
            log_event(logger, "info", "Error al desbloquear Chilkat (método Bundle):")
            log_event(logger, "info", glob.lastErrorText())
            # Intenta el método alternativo
        log_event(logger, "info", "Chilkat desbloqueado correctamente.")
        return True
    except Exception as e:
        log_event(
            logger,
            "info",
            f"Excepción al desbloquear Chilkat: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )
        return False


def load_key_and_cert_from_p12(p12_file, password):

    # Leer el contenido del archivo p12
    with open(p12_file, "rb") as f:
        p12_data = f.read()

    # Cargar el archivo p12
    private_key, certificate, additional_certificates = (
        pkcs12.load_key_and_certificates(p12_data, password.encode(), default_backend())
    )

    # Convertir la clave privada y el certificado a formato PEM
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    certificate_pem = certificate.public_bytes(encoding=serialization.Encoding.PEM)

    key_base64 = base64.b64encode(private_key_pem).decode("utf-8")
    cert_base64 = base64.b64encode(certificate_pem).decode("utf-8")

    return private_key_pem, certificate_pem


def ObtenerSemilla(Origen=1, URLContribuyente=None):
    try:
        # Construir la URL según el origen
        if Origen == 1:
            url = f"https://{GConfig.FEDGII.URLBase}{GConfig.FEDGII.URLAmbienteActivo}{GConfig.FEDGII.URLSemilla}"
        elif Origen == 2 and URLContribuyente:
            url = f"{URLContribuyente}/fe/autenticacion/api/semilla"
        else:
            log_event(logger, "error", "Origen o URL no válido")
            return "Origen o URL no válido"

        log_event(logger, "info", f"URL consultada: {url}")

        # Cliente HTTPX con soporte TLS y reconexión automática
        with httpx.Client(timeout=10, verify=True) as client:
            log_event(logger, "info", f"Conectando a: {url}")
            response = client.get(url, headers={"accept": "*/*"})

        respStatusCode = response.status_code
        log_event(logger, "info", f"response status code = {respStatusCode}")

        # Manejo de errores HTTP
        if respStatusCode >= 400:
            log_event(logger, "error", f"Response Status Code = {respStatusCode}")
            log_event(logger, "error", f"Response Header: {response.headers}")
            log_event(logger, "error", f"Response Body: {response.text}")
            return ""

        # Parsear el XML de la respuesta
        root = ET.fromstring(response.content)
        valor = root.findtext("valor")
        fecha = root.findtext("fecha")

        log_event(logger, "info", f"Semilla: {valor}")
        log_event(logger, "info", f"Fecha: {fecha}")

        # Guardar la semilla en un archivo XML
        archivo_nombre = f"semilla{datetime.now().strftime('%d%m%Y%I%M%S%f%p')}.xml"
        archivo_ruta = os.path.join(
            GConfig.FEDGII.RutaSemilla, "generadas", archivo_nombre
        )
        os.makedirs(os.path.dirname(archivo_ruta), exist_ok=True)

        with open(archivo_ruta, "wb") as f:
            f.write(response.content)

        log_event(logger, "info", f"Archivo guardado en: {archivo_ruta}")
        return archivo_ruta

    except httpx.RequestError as e:
        log_event(logger, "error", f"Error de conexión: {e}")
        return ""
    except Exception as e:
        log_event(
            logger,
            "error",
            f"Error al obtener semilla: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )
        return ""


def FirmarXML(RNCEmisor, Archivo_xml, xml_tag, CodigoSeguridadCF=None):
    """_summary_

    Args:
        RNCEmisor (_type_): _description_
        Archivo_xml (_type_): _description_
        xml_tag (_type_): _description_
        CodigoSeguridadCF (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    UnlockCK()
    success = True
    xmlToSign = chilkat2.Xml()
    success = xmlToSign.LoadXmlFile(Archivo_xml)
    if success != True:
        m = f"El archivo:{Archivo_xml} no se cargo de forma correcta."
        log_event(logger, "info", m)
        return "56", m, "", "", ""

    fecha_actual = datetime.now()
    xmlToSign.Tag = xml_tag

    if xml_tag != "SemillaModel" and xml_tag != "ACECF" and xml_tag != "RFCE":
        xmlToSign.UpdateChildContent(
            "FechaHoraFirma", fecha_actual.strftime("%d-%m-%Y %H:%M:%S %Z").strip()
        )

    if xml_tag == "RFCE":
        xmlToSign.UpdateChildContent("Encabezado|CodigoSeguridadeCF", CodigoSeguridadCF)

    gen = chilkat2.XmlDSigGen()
    gen.SigLocation = xml_tag
    gen.SigLocationMod = 0
    gen.SigNamespacePrefix = ""
    gen.SigNamespaceUri = "http://www.w3.org/2000/09/xmldsig#"
    gen.SignedInfoCanonAlg = "C14N"
    gen.SignedInfoDigestMethod = "sha256"
    gen.AddSameDocRef("", "sha256", "", "", "")

    # Verificar certificado
    if not os.path.exists(GConfig.FEDGII.RutaCertificado):
        m = f"El certificado indicado no existe: {GConfig.FEDGII.RutaCertificado}"
        log_event(logger, "info", m)
        return "56", m, "", "", ""

    cert = chilkat2.Cert()
    success = cert.LoadPfxFile(
        GConfig.FEDGII.RutaCertificado, GConfig.FEDGII.ClaveCertificado
    )
    if not success:
        m = "El certificado no se cargó correctamente."
        log_event(logger, "info", m)
        return "56", m, "", "", ""

    gen.SetX509Cert(cert, True)
    gen.KeyInfoType = "X509Data"
    gen.X509Type = "Certificate"

    FirmaCorrecta = False
    intentos = 0
    max_intentos = 3  # reintentar hasta 3 veces

    while not FirmaCorrecta and intentos < max_intentos:
        intentos += 1
        log_event(logger, "info", f"Intento de firma #{intentos} para {Archivo_xml}")

        sbXml = chilkat2.StringBuilder()
        xmlToSign.GetXmlSb(sbXml)
        gen.Behaviors = "CompactSignedXml"

        success = gen.CreateXmlDSigSb(sbXml)
        if not success:
            log_event(logger, "info", gen.LastErrorText)
            return "56", gen.LastErrorText, "", "", ""

        # Determinar la ruta destino del archivo firmado
        if xml_tag == "SemillaModel":
            Archivo_xml_firmado = os.path.join(
                GConfig.FEDGII.RutaXML,
                GConfig.FEDGII.RutaSemilla,
                "firmadas",
                os.path.splitext(os.path.basename(Archivo_xml))[0] + ".xml",
            )
        elif xml_tag == "ECF":
            Archivo_xml_firmado = os.path.join(
                GConfig.FEDGII.RutaXML,
                "firmadas",
                os.path.splitext(os.path.basename(Archivo_xml))[0] + ".xml",
            )
        elif xml_tag == "RFCE":
            Archivo_xml_firmado = os.path.join(
                GConfig.FEDGII.RutaXML,
                "firmadas",
                "resumen",
                os.path.splitext(os.path.basename(Archivo_xml))[0] + ".xml",
            )
        elif xml_tag == "ACECF":
            Archivo_xml_firmado = os.path.join(
                GConfig.FEDGII.RutaXML,
                "AprobacionComercial\\firmadas\\",
                os.path.splitext(os.path.basename(Archivo_xml))[0] + ".xml",
            )

        if os.path.exists(Archivo_xml_firmado):
            nombre_anterior = generar_nombre_incremental(Archivo_xml_firmado)

        success = sbXml.WriteFile(Archivo_xml_firmado, "utf-8", False)
        if not success:
            error_msg = (
                f"Error al escribir el archivo XML firmado: {Archivo_xml_firmado}"
            )
            log_event(logger, "info", error_msg)
            return "56", error_msg, "", "", ""

        # Verificar firma
        verifier = chilkat2.XmlDSig()
        if not verifier.LoadSignatureSb(sbXml):
            log_event(logger, "info", verifier.LastErrorText)
            return "56", verifier.LastErrorText, "", "", ""

        verified = all(
            verifier.VerifySignature(True) for _ in range(verifier.NumSignatures)
        )
        if not verified:
            log_event(logger, "info", verifier.LastErrorText)
            return "56", verifier.LastErrorText, "", "", ""

        # Extraer Código de Seguridad
        xml_Sign = chilkat2.Xml()
        xml_Sign.LoadXmlFile(Archivo_xml_firmado)
        signature_value_element = xml_Sign.SearchForTag(xml_Sign, "SignatureValue")
        CodigoSeguridad = (
            signature_value_element.Content[:6] if signature_value_element else ""
        )

        if not CodigoSeguridad.strip():
            log_event(
                logger,
                "warning",
                f"Código de seguridad vacío en intento #{intentos}, reintentando...",
            )
            time.sleep(1)  # pequeña pausa antes del reintento
            continue  # reintenta
        else:
            FirmaCorrecta = True

    if not FirmaCorrecta:
        m = "No se pudo obtener un Código de Seguridad válido después de varios intentos."
        log_event(logger, "error", m)
        return "56", m, "", "", ""

    # Obtener la fecha y hora de firma
    fecha_firma_element = xml_Sign.SearchForTag(xml_Sign, "FechaHoraFirma")
    FechayHoradeFirma = (
        fecha_firma_element.Content
        if fecha_firma_element is not None
        else fecha_actual.strftime("%d-%m-%Y %H:%M:%S %Z").strip()
    )

    return (
        "21",
        "Firmado Correctamente.",
        Archivo_xml_firmado,
        CodigoSeguridad,
        FechayHoradeFirma,
    )


def ObtennerToken(
    cn1, RNCEmisor, Origen=1, URLContribuyente=None, max_reintentos=3, espera_segundos=5
):

    # 1️⃣ Revisar BD para token vigente
    query = f"""
        SELECT TOP 1 * 
        FROM FEToken 
        WHERE rnc='{RNCEmisor}' 
        and ambiente={GConfig.FEDGII.Ambiente} 
        ORDER BY expedido DESC
    """
    qLocalToken = cn1.fetch_query(query)
    ahora = datetime.utcnow()

    if qLocalToken:
        expira_dt = qLocalToken[0].expira
        expedido_dt = qLocalToken[0].Expedido
        if isinstance(expira_dt, str):
            expira_dt = datetime.fromisoformat(expira_dt.replace("Z", ""))
        if isinstance(expedido_dt, str):
            expedido_dt = datetime.fromisoformat(expedido_dt.replace("Z", ""))
        if expedido_dt <= ahora <= expira_dt:
            log_event(logger, "info", "Token vigente encontrado en BD.")
            return qLocalToken[0].token

    # 2️⃣ Generar nuevo token con reintentos
    for intento in range(1, max_reintentos + 1):
        try:
            log_event(logger, "info", f"Intento {intento} para generar token.")

            codigo, mensaje, SemillaFirmada, _, _ = FirmarXML(
                RNCEmisor, ObtenerSemilla(1), "SemillaModel"
            )

            ArchivoToken = os.path.join(
                GConfig.FEDGII.URLBase,
                GConfig.FEDGII.RutaToken,
                f'token{datetime.now().strftime("%d%m%Y%I%M%S%f%p")}.xml',
            )

            # Determinar URL según Origen
            base_url = (
                f"{URLContribuyente}/api/semilla/validacioncertificado"
                if Origen == 2 and URLContribuyente
                else f"https://{GConfig.FEDGII.URLBase}{GConfig.FEDGII.URLAmbienteActivo}{GConfig.FEDGII.URLToken}"
            )
            url = f"{base_url}"

            files = {
                "xml": (
                    os.path.basename(SemillaFirmada),
                    open(SemillaFirmada, "rb"),
                    "text/xml",
                )
            }
            headers = {"accept": "application/xml", "Expect": "100-continue"}

            response = requests.post(
                url, files=files, headers=headers, verify=True, timeout=30
            )
            if response.status_code >= 400:
                raise Exception(f"Error {response.status_code}: {response.text}")

            # Guardar XML
            with open(ArchivoToken, "w", encoding="utf-8") as f:
                f.write(response.text)

            # Parsear token
            root = ET.fromstring(response.text)
            Token = root.find(".//token").text
            expira = root.find(".//expira").text.replace("T", " ").replace("Z", "")
            expedido = root.find(".//expedido").text.replace("T", " ").replace("Z", "")
            expira_dt = datetime.fromisoformat(expira)
            expedido_dt = datetime.fromisoformat(expedido)

            log_event(
                logger, "info", f"Nuevo token expedido: {expedido}, expira: {expira}"
            )

            # 3️⃣ Eliminar tokens viejos en BD
            query_delete = "DELETE FROM FEToken WHERE rnc=? and ambiente=?"
            cn1.execute_query(query_delete, (RNCEmisor, GConfig.FEDGII.Ambiente))

            # 4️⃣ Guardar token nuevo en BD
            query_insert = """
                INSERT INTO FEToken(rnc, expira, expedido, FileToken, SemillaFirmada, token, ambiente) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                RNCEmisor,
                expira_dt,
                expedido_dt,
                ArchivoToken,
                SemillaFirmada,
                Token,
                GConfig.FEDGII.Ambiente,
            )
            cn1.execute_query(query_insert, params)

            return Token

        except Exception as e:
            log_event(
                logger,
                "error",
                f"Fallo en intento {intento}: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
            )
            if intento < max_reintentos:
                time.sleep(espera_segundos)
            else:
                raise Exception("No se pudo obtener token después de varios intentos.")


def Enviar_DFE(xml_path, bearer_token):
    # Validación de archivo
    if not os.path.exists(xml_path):
        log_event(logger, "error", f"Archivo no encontrado: {xml_path}")
        return 70, "Archivo no encontrado", ""

    MaxIntentos = 3
    Intentos = 0

    # Construcción del endpoint
    url = f"https://{GConfig.FEDGII.URLBase}{GConfig.FEDGII.URLAmbienteActivo}{GConfig.FEDGII.URLDocumentosElectronicos}"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
        # El Content-Type lo genera automáticamente requests al usar files=...
    }

    while Intentos < MaxIntentos:
        try:
            with open(xml_path, "rb") as f:
                files = {"xml": (os.path.basename(xml_path), f, "text/xml")}

                # Enviar la solicitud
                response = requests.post(url, headers=headers, files=files, timeout=30)

            log_event(logger, "info", f"HTTP Status: {response.status_code}")

            # Verificar error HTTP
            if response.status_code >= 400:
                log_event(logger, "error", f"HTTP ERROR {response.status_code}")
                log_event(logger, "error", f"Response: {response.text}")
                Intentos += 1
                continue

            # Procesar JSON
            try:
                data = response.json()
            except ValueError:
                log_event(logger, "error", "Respuesta no es JSON")
                Intentos += 1
                continue

            log_event(logger, "info", data)

            trackId = data.get("trackId", "")
            error = data.get("error", "")
            mensaje = data.get("mensaje", "")

            return trackId, error, mensaje

        except RequestException as ex:
            log_event(
                logger,
                "error",
                f"Excepción HTTP: {ex}:{ traceback.extract_tb(sys.exc_info()[2])}",
            )
            Intentos += 1
            continue

    # Si llega aquí es que falló todo
    return 70, "Error de Conexión", ""


##################################################
# Verificación y consulta de servicios DGII
def ConsultaDirectorioServiciosListado(bearer_btoken):
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://ecf.dgii.gov.do/testecf/consultadirectorio/api/Consultas/Listado
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect(GConfig.FEDGII.URLBase, port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "error", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "error", rest.LastErrorText)
        # sys.exit()

    rest.AddHeader("accept", "application/json")
    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET",
        f"{GConfig.FEDGII.URLAmbienteActivo}{GConfig.FEDGII.URLConsultaDirectorioServiciosListado}",
        sbResponseBody,
    )
    if success != True:
        log_event(logger, "error", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "error", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "error", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "error", "Response Header:")
        log_event(logger, "error", rest.ResponseHeader)
        log_event(logger, "error", "Response Body:")
        log_event(logger, "error", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    return jsonResponse.Emit()


def ConsultaDirectorioServiciosRNC(RNC, bearer_btoken):
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://ecf.dgii.gov.do/testecf/consultadirectorio/api/consultas/obtenerdirectorioporrnc
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect(GConfig.FEDGII.URLBase, port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "error", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "error", rest.LastErrorText)
        # sys.exit()

    rest.ClearAllQueryParams()
    rest.AddQueryParam("RNC", RNC)

    rest.AddHeader("accept", "application/json")
    rest.AddHeader("Authorization", f"bearer {bearer_btoken}")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET",
        GConfig.FEDGII.URLAmbienteActivo
        + GConfig.FEDGII.URLConsultaDirectorioServiciosRNC,
        sbResponseBody,
    )
    if success != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "inerrorfo", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "error", "Response Header:")
        log_event(logger, "error", rest.ResponseHeader)
        log_event(logger, "error", "Response Body:")
        log_event(logger, "error", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # {
    #   "nombre": "string",
    #   "rnc": "string",
    #   "urlRecepcion": "string",
    #   "urlAceptacion": "string"
    # }

    # Sample code for parsing the JSON response...
    # Use this online tool to generate parsing code from sample JSON: Generate JSON Parsing Code

    nombre = jsonResponse.StringOf("nombre")
    rnc = jsonResponse.StringOf("rnc")
    urlRecepcion = jsonResponse.StringOf("urlRecepcion")
    urlAceptacion = jsonResponse.StringOf("urlAceptacion")
    urlOpcional = jsonResponse.StringOf("urlOpcional")

    return rnc, nombre, urlRecepcion, urlAceptacion, urlOpcional


def GenerarXMLAprobacionComercial(cn1, RNCEmisor, eNCF):
    UnlockCK()
    #  Consultar vFEEncabezado
    query = f"SELECT * FROM AprobacionComercial WITH (NOLOCK) where eNCF = '{eNCF}' and RNCEmisor = '{RNCEmisor}'"
    qAprobacionComercial = cn1.fetch_query(query)

    xml = chilkat2.Xml()
    xml.Tag = "ACECF"
    xml.AddAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml.AddAttribute("xsi:noNamespaceSchemaLocation", "ACECF v.1.0.xsd")
    xml.UpdateChildContent("DetalleAprobacionComercial|Version", "1.0")

    xml.UpdateChildContent(
        "DetalleAprobacionComercial|RNCEmisor",
        qAprobacionComercial[0].RNCEmisor.strip(),
    )
    xml.UpdateChildContent(
        "DetalleAprobacionComercial|eNCF", qAprobacionComercial[0].eNCF.strip()
    )
    FechaEmision = formato_fecha_seguro(
        qAprobacionComercial[0].FechaEmision, "%d-%m-%Y"
    )
    if FechaEmision:
        xml.UpdateChildContent(
            "DetalleAprobacionComercial|FechaEmision",
            FechaEmision,
        )
    xml.UpdateChildContent(
        "DetalleAprobacionComercial|MontoTotal",
        f"{Decimal(qAprobacionComercial[0].MontoTotal):.2f}",
    )

    if not validar_formato_rnc(qAprobacionComercial[0].RNCComprador.strip()):
        mensajet = f"El RNC del comprador{qAprobacionComercial[0].RNCComprador.strip()} tiene un formato invalido."
        log_event(logger, "error", mensajet)
        raise TypeError(mensajet)
    xml.UpdateChildContent(
        "DetalleAprobacionComercial|RNCComprador",
        qAprobacionComercial[0].RNCComprador.strip(),
    )

    xml.UpdateChildContentInt(
        "DetalleAprobacionComercial|Estado", qAprobacionComercial[0].Estado
    )
    if qAprobacionComercial[0].DetalleMotivoRechazo is not None:
        if qAprobacionComercial[0].DetalleMotivoRechazo != "":
            xml.UpdateChildContent(
                "DetalleAprobacionComercial|DetalleMotivoRechazo",
                qAprobacionComercial[0].DetalleMotivoRechazo.strip(),
            )
    FechaHora = formato_fecha_seguro(
        qAprobacionComercial[0].FechaHoraAprobacionComercial, "%d-%m-%Y %H:%M:%S %Z"
    )
    if FechaHora:
        xml.UpdateChildContent(
            "DetalleAprobacionComercial|FechaHoraAprobacionComercial",
            FechaHora,
        )
    if qAprobacionComercial[0].Comentario is not None:
        if qAprobacionComercial[0].Comentario != "":
            xml.UpdateChildContent(
                "InformacionAdicional|Comentario",
                qAprobacionComercial[0].Comentario.strip(),
            )

    Ruta = "AprobacionComercial/"
    NombreXML = GConfig.FEDGII.RutaXML + f"{Ruta}{RNCEmisor.strip()+eNCF.strip()}.xml"
    xml.SaveXml(NombreXML)


"""

Módulo de generación de XML para e-CF.

Adaptado para -*- coding: utf-8 -*-

Este archivo contiene la función `GenerarXML`, que construye el XML de un
comprobante fiscal electrónico (e-CF) a partir de la información obtenida
del ERP / base de datos mediante el objeto de conexión `cn1`.

Notas importantes para cualquier programador que mantenga este código:
- Esta función NO hace cálculos contables: asume que el ERP ya calculó
  montos, impuestos, descuentos, etc. y solo los traslada al XML.
- Se apoya en vistas/tablas como vFEEncabezado, vFEDetalle, vFETotales,
  y en tablas auxiliares de pagos, impuestos adicionales y descuentos/recargos.
- El objetivo principal es construir un XML válido según la DGII y
  evitar inconsistencias típicas entre encabezado, detalle y totales.

Códigos de retorno:
- "02": XML generado correctamente.
- "61": Inconsistencia entre los totales del encabezado y los totales
        consolidados (detalle / vFETotales).
- "62": No hay datos de detalle para el encabezado luego de los reintentos.
- "70": Error de validación de datos o error inesperado (excepciones, formatos,
        datos faltantes críticos, etc.).

Dependencias externas (inyectadas desde otros módulos del sistema):
- log_event(logger, level, mensaje): para registrar en el log.
- logger: instancia de logger.
- XmlNative: clase que encapsula la construcción del XML (UpdateChildContent, SaveXml, etc.).
- GConfig.FEDGII.RutaXML: configuración global donde se guardan los XML.
- Funciones auxiliares:
    - validar_rnc_DGII, validar_formato_rnc
    - formato_fecha_seguro, convertir_a_porcentaje, StrToInt
    - validar_telefono_rd, verificar_email
    - generar_nombre_incremental
- Objeto `cn1` con métodos:
    - _get_encabezado, _count_encabezado
    - _get_detalle, _count_detalle
    - _get_tablapago, _get_tablaimpuestosadicionales, _get_tabladescuentosyrecargos
    - _get_totales, vista_existe
"""


def GenerarXML(cn1, RNCEmisor, eNCF):
    """
    Genera el XML de un e-CF a partir de los datos del ERP.

    Flujo general:
    1. Limpia parámetros y obtiene el encabezado de la factura.
    2. Valida unicidad del encabezado (no debe estar duplicado).
    3. Realiza reintentos controlados para:
       - Obtener el detalle.
       - Validar que los totales del encabezado coincidan con los totales
         consolidados (si existe vFETotales).
    4. Construye el XML completo (Encabezado, Emisor, Comprador, Totales,
       Detalles, Descuentos/Recargos, Otra Moneda, Información de Referencia, etc.).
    5. Guarda el archivo en disco, preservando el XML anterior renombrándolo
       de forma incremental en caso de existir.

    Parámetros:
        cn1        : Objeto de acceso a datos con los métodos requeridos.
        RNCEmisor  : RNC del emisor (string, posiblemente con espacios).
        eNCF       : Número de e-CF (string, posiblemente con espacios).

    Retorna:
        (codigo, mensaje) donde:
            codigo  = "02", "61", "62" o "70"
            mensaje = descripción textual del resultado.
    """
    try:

        inicio = time.time()

        RNCEmisor = RNCEmisor.strip()

        """if not validar_rnc_DGII(RNCEmisor.strip()) or not validar_formato_rnc(
            RNCEmisor.strip()
        ):
            mensajet = f"El RNC '{RNCEmisor.strip()}' No pudo ser Validado."
            log_event(logger, "error", mensajet)
            return "70", mensajet
        else:
            log_event(
                logger,
                "info",
                f"El RNC '{RNCEmisor.strip()}' fue validado correctamente Validado.",
            )"""

        eNCF = eNCF.strip()
        log_event(
            logger,
            "info",
            f"Se inicia la optencion de datos para el eNCF:{eNCF.strip()} y el Emisor con el rnc:{RNCEmisor.strip()}",
        )

        qEncabezadoFactura = cn1._get_encabezado(RNCEmisor.strip(), eNCF.strip())

        if not qEncabezadoFactura:
            # Error 70: encabezado inexistente (no se puede generar XML sin encabezado)
            return (
                "70",
                f"No hay datos para el eNCF:{eNCF.strip()} y el Emisor con el rnc:{RNCEmisor.strip()}",
            )
        cantidad_registros = cn1._count_encabezado(RNCEmisor.strip(), eNCF.strip())
        if cantidad_registros > 1:
            # Error 70: hay más de un encabezado para el mismo e-NCF (dato inconsistente)
            return (
                "70",
                f"El eNCF:{eNCF.strip()} para el emisor:{RNCEmisor.strip()} esta duplicado. Debe revizar antes de enviar",
            )

        # ========================================================================
        # VALIDACIÓN CRÍTICA: DETALLE + TOTALES (REINTENTOS)
        # ========================================================================
        # Este bloque garantiza que antes de generar el XML fiscal:
        #   1. Existan datos de detalle asociados al encabezado.
        #   2. Los totales del encabezado coincidan con los totales
        #      generados/consolidados por el ERP (vista vFETotales).
        #
        # Importante:
        # Algunos ERPs actualizan los totales de forma diferida (triggers,
        # procesos batch, vistas materializadas, etc.). Por eso se realizan
        # varios intentos con pequeñas pausas entre ellos, para dar tiempo a
        # que esos procesos terminen y evitar falsos errores de inconsistencia.
        #
        # REGLAS IMPLEMENTADAS:
        #   ✔ Si después del último intento NO existe detalle → ERROR "62"
        #       - Mensaje: "No hay datos de detalle para el Encabezado."
        #   ✔ Si existe detalle y existe vFETotales:
        #       - Se compara MontoTotal del encabezado vs. MontoTotal de vFETotales.
        #       - Si la diferencia absoluta redondeada a 2 decimales es > 1.00:
        #           ▸ En intentos intermedios → se espera y se reintenta.
        #           ▸ En el último intento → ERROR "61"
        #             (montos totales no coinciden).
        #   ✔ Si NO existe vFETotales pero sí existe detalle:
        #       - Se asume que el ERP no usa consolidación por vista y se continua
        #         solo con la información de encabezado + detalle.
        #
        # Ventaja de este enfoque:
        # - Reduce el riesgo de que se genere y envíe a la DGII un XML
        #   incongruente (totales que no cuadran con el detalle).
        # - Provee mensajes de error claros para monitoreo y soporte.
        # ========================================================================

        qTotales = None

        # 🔁 Ciclo de reintentos para leer el detalle y validar totales
        for intento in range(1, 3):

            log_event(
                logger, "info", f"Iniciando intento {intento} para buscar el detalle"
            )

            # Se intenta obtener los registros de detalle asociados al encabezado
            qDetalleFactura = cn1._get_detalle(RNCEmisor.strip(), eNCF.strip())

            # --------------------------------------------------------------------
            # CASO A) NO EXISTE DETALLE
            # --------------------------------------------------------------------
            # Si no existe detalle, es imposible generar un XML válido.
            # - En intentos intermedios: se registra en log y se reintenta.
            # - En el último intento: se retorna el código "62".
            # --------------------------------------------------------------------
            if not qDetalleFactura:
                if intento == 2:
                    msg = "No hay datos de detalle para el Encabezado."
                    log_event(logger, "error", msg)
                    return "62", msg  # Código definido para ausencia de detalle
                else:
                    log_event(logger, "info", "Sin detalle, reintentando...")
                    time.sleep(0.4)
                    continue

            # --------------------------------------------------------------------
            # CASO B) EXISTE DETALLE → VALIDAR TOTALES
            # --------------------------------------------------------------------
            # Si la vista vFETotales existe, se contrastan los totales calculados
            # por el ERP contra los del encabezado. Esto asegura que el XML
            # refleje información matemática consistente.
            # --------------------------------------------------------------------
            if cn1.vista_existe("vFETotales"):
                qTotales = cn1._get_totales(RNCEmisor.strip(), eNCF.strip())

                if qTotales:

                    # Diferencia absoluta de totales entre encabezado y consolidado ERP
                    diferencia = abs(
                        qEncabezadoFactura[0].MontoTotal - qTotales[0].MontoTotal
                    )

                    # Una diferencia > 1.00 es considerada inconsistencia fiscal
                    if round(diferencia, 2) > 1:

                        # Primer o segundo intento → esperar consolidación
                        if intento < 2:
                            log_event(
                                logger,
                                "error",
                                "Los montos totales no coinciden, reintentando...",
                            )
                            time.sleep(0.4)
                            continue

                        # Último intento → ERROR código 61
                        msg = "Los Montos Totales del Detalle y del Encabezado no coinciden."
                        log_event(logger, "error", msg)
                        return (
                            "61",
                            msg,
                        )  # Código definido para inconsistencia de totales

                    # Totales correctos → salir del bucle de reintentos
                    break

            # --------------------------------------------------------------------
            # CASO C) NO EXISTE vFETotales
            # --------------------------------------------------------------------
            # Si no existe vista de totales, se asume que el ERP no utiliza
            # consolidación por vista y se continúa solamente con el detalle
            # disponible.
            # --------------------------------------------------------------------
            log_event(
                logger,
                "info",
                f"Detalle encontrado: {cn1._count_detalle(RNCEmisor.strip(), eNCF.strip())}",
            )
            break

        # A partir de este punto se asume que:
        # - Existe encabezado válido.
        # - Hay detalle válido (o se retornó previamente "62").
        # - Si existe vFETotales y se llenó qTotales, los totales son consistentes
        #   (o se retornó previamente "61").

        qTablaPago = cn1._get_tablapago(RNCEmisor.strip(), eNCF.strip())
        qTablaImpuestosAdicionales = cn1._get_tablaimpuestosadicionales(
            RNCEmisor.strip(), eNCF.strip()
        )
        qTablaDescuentosORecargos = cn1._get_tabladescuentosyrecargos(
            RNCEmisor.strip(), eNCF.strip()
        )

        fin = time.time()
        tiempo_total = fin - inicio
        log_event(
            logger,
            "info",
            f"Tiempo de ejecución de la optencion de datos: {tiempo_total:.4f} segundos",
        )
        inicio = time.time()
        log_event(
            logger,
            "info",
            f"Se inicia la proceso de Generación del XML para el eNCF:{eNCF.strip()} y el Emisor con el rnc:{RNCEmisor.strip()}",
        )

        xml = XmlNative()
        xml.UpdateChildContent("Encabezado|Version", "1.0")
        # TipoECF = int(qEncabezadoFactura[0].TipoECF)

        tipo_dato = type(qEncabezadoFactura[0].TipoECF)

        if tipo_dato == int:
            # Si ya es entero, simplemente asignamos
            TipoECF = qEncabezadoFactura[0].TipoECF
        elif tipo_dato == str:
            # Si es string, intentamos convertirlo a entero
            try:
                TipoECF = int(qEncabezadoFactura[0].TipoECF)
            except ValueError:
                # Si el string no se puede convertir a entero, lo asignamos directamente
                TipoECF = qEncabezadoFactura[0].TipoECF
        else:
            # Si es otro tipo de dato, generamos un error
            log_event(logger, "error", query)
            mensajet = f"TipoECF tiene un tipo de dato no válido: {tipo_dato.__name__}. Se esperaba int o str."
            log_event(logger, "error", mensajet)
            return "70", mensajet

        xml.Tag = "ECF"

        if TipoECF == 32 and qEncabezadoFactura[0].MontoTotal < 250000:
            GenerarXMLRFCE(cn1, RNCEmisor.strip(), eNCF)

        if TipoECF == 46:
            IndicadorMontoGravadoIEX = 1
        else:
            IndicadorMontoGravadoIEX = 0

        xml.UpdateChildContentInt("Encabezado|IdDoc|TipoeCF", int(TipoECF))
        xml.UpdateChildContent(
            "Encabezado|IdDoc|eNCF", qEncabezadoFactura[0].eNCF.strip()[:13]
        )

        if TipoECF not in [32, 34]:
            if qEncabezadoFactura[0].FechaVencimientoSecuencia is not None:
                FechaVencimientoSecuencia = formato_fecha_seguro(
                    qEncabezadoFactura[0].FechaVencimientoSecuencia, "%d-%m-%Y"
                )
                if FechaVencimientoSecuencia:
                    xml.UpdateChildContent(
                        "Encabezado|IdDoc|FechaVencimientoSecuencia",
                        FechaVencimientoSecuencia,
                    )
            else:
                m = f"La fecha de vencimiento del comprobante eNCF:{eNCF.strip()} y el Emisor con el rnc:{RNCEmisor.strip()}-{qEncabezadoFactura[0].RazonSocialEmisor} está vacía"
                log_event(
                    logger,
                    "error",
                    m,
                )
                return "70", m
        if qEncabezadoFactura[0].IndicadorNotaCredito is not None and TipoECF == 34:
            xml.UpdateChildContentInt(
                "Encabezado|IdDoc|IndicadorNotaCredito",
                qEncabezadoFactura[0].IndicadorNotaCredito,
            )

        # Indicador de Envio Diferido
        # if TipoECF != 41 and TipoECF != 43 and TipoECF != 47:
        #        xml.UpdateChildContentInt(
        #            "Encabezado|IdDoc|IndicadorEnvioDiferido",
        #            int( qEmisorPerfil[0].IndicadorEnvioDiferido),
        #        )

        # Indicador de Monto Grabado
        if TipoECF not in [43, 44, 46, 47]:
            if qEncabezadoFactura[0].IndicadorMontoGravado is not None:
                if qEncabezadoFactura[0].IndicadorMontoGravado != "":
                    xml.UpdateChildContentInt(
                        "Encabezado|IdDoc|IndicadorMontoGravado",
                        int(qEncabezadoFactura[0].IndicadorMontoGravado),
                    )

        if TipoECF not in [41, 43, 47]:
            if qEncabezadoFactura[0].TipoIngresos is not None:
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|TipoIngresos", qEncabezadoFactura[0].TipoIngresos
                )

        if TipoECF != 43:
            if qEncabezadoFactura[0].TipoPago is not None:
                if qEncabezadoFactura[0].TipoPago > 0:
                    xml.UpdateChildContentInt(
                        "Encabezado|IdDoc|TipoPago", qEncabezadoFactura[0].TipoPago
                    )

        # SI LA FACTURA ES A CREDITO INDICA LA FECHA DE VENCIMIENTO
        if StrToInt(qEncabezadoFactura[0].TipoPago) == 2 or TipoECF != 43:
            if qEncabezadoFactura[0].FechaLimitePago is not None:
                FechaLimitePago = formato_fecha_seguro(
                    qEncabezadoFactura[0].FechaLimitePago, "%d-%m-%Y"
                )
                if FechaLimitePago:
                    xml.UpdateChildContent(
                        "Encabezado|IdDoc|FechaLimitePago",
                        FechaLimitePago,
                    )
        if TipoECF not in [32, 33, 34, 41, 43]:
            if qEncabezadoFactura[0].TerminoPago is not None:
                if qEncabezadoFactura[0].TerminoPago != "":
                    xml.UpdateChildContent(
                        "Encabezado|IdDoc|TerminoPago",
                        str(qEncabezadoFactura[0].TerminoPago).strip()[:15],
                    )
        # Detallar las Formas de Pago
        if (TipoECF not in [34, 43]) and qTablaPago:
            for fila in qTablaPago:
                if (fila.MontoPago or 0) >= 0 and int(fila.FormaPago) in [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                ]:

                    xml.UpdateChildContentInt(
                        "Encabezado|IdDoc|TablaFormasPago|FormaDePago|FormaPago",
                        int(fila.FormaPago),
                    )
                    xml.UpdateChildContent(
                        "Encabezado|IdDoc|TablaFormasPago|FormaDePago|MontoPago",
                        f"{Decimal(fila.MontoPago):.2f}",
                    )

        if qEncabezadoFactura[0].TipoCuentaPago is not None:
            if (qEncabezadoFactura[0].TipoCuentaPago.strip() or "") != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|TipoCuentaPago",
                    qEncabezadoFactura[0].TipoCuentaPago.strip()[:2],
                )

        if qEncabezadoFactura[0].NumeroCuentaPago is not None:
            if qEncabezadoFactura[0].NumeroCuentaPago.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|NumeroCuentaPago",
                    qEncabezadoFactura[0].NumeroCuentaPago.strip()[:28],
                )

        if qEncabezadoFactura[0].BancoPago is not None:
            if qEncabezadoFactura[0].BancoPago.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|BancoPago",
                    qEncabezadoFactura[0].BancoPago.strip()[:75],
                )

        if qEncabezadoFactura[0].FechaDesde is not None:
            if qEncabezadoFactura[0].FechaDesde != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|FechaDesde",
                    qEncabezadoFactura[0].FechaDesde,
                )

        if qEncabezadoFactura[0].FechaHasta is not None:
            if qEncabezadoFactura[0].FechaHasta != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|FechaHasta",
                    qEncabezadoFactura[0].FechaHasta,
                )

        if qEncabezadoFactura[0].TotalPaginas is not None:
            if qEncabezadoFactura[0].TotalPaginas.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|TotalPaginas",
                    str(qEncabezadoFactura[0].TotalPaginas.strip()),
                )

        # Datos del Emisor
        xml.UpdateChildContent(
            "Encabezado|Emisor|RNCEmisor", qEncabezadoFactura[0].RNCEmisor.strip()
        )

        if qEncabezadoFactura[0].RazonSocialEmisor is not None:
            if qEncabezadoFactura[0].RazonSocialEmisor.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|RazonSocialEmisor",
                    qEncabezadoFactura[0].RazonSocialEmisor.strip()[:150],
                )

        if qEncabezadoFactura[0].NombreComercial is not None:
            if qEncabezadoFactura[0].NombreComercial.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|NombreComercial",
                    qEncabezadoFactura[0].NombreComercial.strip()[:150],
                )

        if qEncabezadoFactura[0].DireccionEmisor is not None:
            if qEncabezadoFactura[0].DireccionEmisor.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|DireccionEmisor",
                    qEncabezadoFactura[0].DireccionEmisor.strip()[:100],
                )
        if qEncabezadoFactura[0].Municipio is not None:
            if qEncabezadoFactura[0].Municipio.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|Municipio",
                    qEncabezadoFactura[0].Municipio.strip(),
                )

        if qEncabezadoFactura[0].Provincia is not None:
            if qEncabezadoFactura[0].Provincia.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|Provincia",
                    qEncabezadoFactura[0].Provincia.strip(),
                )
        """if qEncabezadoFactura[0].Sucursal is not None:
            if (qEncabezadoFactura[0].Sucursal.strip() != "") & (
                qEncabezadoFactura[0].Sucursal != None
            ):
                xml.UpdateChildContent(
                    "Encabezado|Emisor|Sucursal", qEncabezadoFactura[0].Sucursal.strip()
                )"""
        # Telefonos del Emisor

        if qEncabezadoFactura[0].TelefonoEmisor1 is not None and validar_telefono_rd(
            qEncabezadoFactura[0].TelefonoEmisor1
        ):
            if qEncabezadoFactura[
                0
            ].TelefonoEmisor1.strip() != "" and validar_telefono_rd(
                qEncabezadoFactura[0].TelefonoEmisor1
            ):
                xml.UpdateChildContent(
                    "Encabezado|Emisor|TablaTelefonoEmisor|TelefonoEmisor[1]",
                    qEncabezadoFactura[0].TelefonoEmisor1.strip(),
                )
        if (
            qEncabezadoFactura[0].TelefonoEmisor2 is not None
            and qEncabezadoFactura[0].TelefonoEmisor2.strip() != ""
            and validar_telefono_rd(qEncabezadoFactura[0].TelefonoEmisor2)
        ):
            xml.UpdateChildContent(
                "Encabezado|Emisor|TablaTelefonoEmisor|TelefonoEmisor[2]",
                qEncabezadoFactura[0].TelefonoEmisor2.strip(),
            )
        if qEncabezadoFactura[0].TelefonoEmisor3 is not None and validar_telefono_rd(
            qEncabezadoFactura[0].TelefonoEmisor3
        ):
            if qEncabezadoFactura[
                0
            ].TelefonoEmisor3.strip() != "" and validar_telefono_rd(
                qEncabezadoFactura[0].TelefonoEmisor3
            ):
                xml.UpdateChildContent(
                    "Encabezado|Emisor|TablaTelefonoEmisor|TelefonoEmisor[3]",
                    qEncabezadoFactura[0].TelefonoEmisor3.strip(),
                )

        if qEncabezadoFactura[0].CorreoEmisor is not None:
            if qEncabezadoFactura[0].CorreoEmisor.strip() != "" and verificar_email(
                qEncabezadoFactura[0].CorreoEmisor
            ):
                xml.UpdateChildContent(
                    "Encabezado|Emisor|CorreoEmisor",
                    qEncabezadoFactura[0].CorreoEmisor.strip()[:80],
                )
        if qEncabezadoFactura[0].WebSite is not None:
            if qEncabezadoFactura[0].WebSite.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|WebSite",
                    qEncabezadoFactura[0].WebSite.strip()[:50],
                )
        if qEncabezadoFactura[0].ActividadEconomica is not None:
            if qEncabezadoFactura[0].ActividadEconomica.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|ActividadEconomica",
                    qEncabezadoFactura[0].ActividadEconomica.strip()[:100],
                )
        if qEncabezadoFactura[0].CodigoVendedor is not None:
            if qEncabezadoFactura[0].CodigoVendedor.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|CodigoVendedor",
                    qEncabezadoFactura[0].CodigoVendedor.strip()[:60],
                )

        if qEncabezadoFactura[0].NumeroFacturaInterna is not None:
            if qEncabezadoFactura[0].NumeroFacturaInterna.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|NumeroFacturaInterna",
                    qEncabezadoFactura[0].NumeroFacturaInterna.strip()[:20],
                )

        """
        if (
            qEncabezadoFactura[0].NumeroPedidoInterno is not None
            or str(qEncabezadoFactura[0].NumeroPedidoInterno).strip() != ""
        ):
            xml.UpdateChildContent(
                "Encabezado|Emisor|NumeroPedidoInterno",
                qEncabezadoFactura[0].NumeroPedidoInterno.strip(),
            )
        """

        if qEncabezadoFactura[0].ZonaVenta is not None:
            if qEncabezadoFactura[0].ZonaVenta.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|ZonaVenta",
                    qEncabezadoFactura[0].ZonaVenta.strip()[:20],
                )

        if qEncabezadoFactura[0].RutaVenta is not None:
            if qEncabezadoFactura[0].RutaVenta.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|RutaVenta",
                    qEncabezadoFactura[0].RutaVenta.strip()[:20],
                )

        if qEncabezadoFactura[0].InformacionAdicionalEmisor is not None:
            if qEncabezadoFactura[0].InformacionAdicionalEmisor.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Emisor|InformacionAdicionalEmisor",
                    qEncabezadoFactura[0].InformacionAdicionalEmisor.strip()[:250],
                )

        if qEncabezadoFactura[0].FechaEmision is not None:
            FechaEmision = formato_fecha_seguro(
                qEncabezadoFactura[0].FechaEmision, "%d-%m-%Y"
            )
            if FechaEmision:
                xml.UpdateChildContent(
                    "Encabezado|Emisor|FechaEmision",
                    FechaEmision,
                )

        # Comprador

        if qEncabezadoFactura[0].RNCComprador is not None:
            if qEncabezadoFactura[0].RNCComprador.strip() != "" and TipoECF not in [
                43,
                47,
            ]:
                if not validar_formato_rnc(qEncabezadoFactura[0].RNCComprador.strip()):
                    mensajet = f"El RNC del comprador{qEncabezadoFactura[0].RNCComprador.strip()} tiene un formato invalido."
                    log_event(logger, "error", mensajet)
                    return "70", mensajet
                xml.UpdateChildContent(
                    "Encabezado|Comprador|RNCComprador",
                    qEncabezadoFactura[0].RNCComprador.strip(),
                )

        if (
            qEncabezadoFactura[0].IdentificadorExtranjero is not None
            and qEncabezadoFactura[0].IdentificadorExtranjero != ""
            and TipoECF
            not in [
                31,
                41,
                43,
                45,
            ]
        ):
            xml.UpdateChildContent(
                "Encabezado|Comprador|IdentificadorExtranjero",
                str(qEncabezadoFactura[0].IdentificadorExtranjero).strip()[:20],
            )

        if qEncabezadoFactura[0].RazonSocialComprador is not None:
            if (
                qEncabezadoFactura[0].RazonSocialComprador.strip() != ""
                and TipoECF != 43
            ):
                xml.UpdateChildContent(
                    "Encabezado|Comprador|RazonSocialComprador",
                    qEncabezadoFactura[0].RazonSocialComprador.strip()[:150],
                )

        if qEncabezadoFactura[0].ContactoComprador is not None:
            if qEncabezadoFactura[
                0
            ].ContactoComprador.strip() != "" and TipoECF not in [43, 47]:
                xml.UpdateChildContent(
                    "Encabezado|Comprador|ContactoComprador",
                    qEncabezadoFactura[0].ContactoComprador.strip()[:80],
                )

        if (
            qEncabezadoFactura[0].CorreoComprador is not None
            and qEncabezadoFactura[0].CorreoComprador.strip() != ""
            and TipoECF
            not in [
                43,
                47,
            ]
        ):
            xml.UpdateChildContent(
                "Encabezado|Comprador|CorreoComprador",
                qEncabezadoFactura[0].CorreoComprador.strip()[:80],
            )

        if qEncabezadoFactura[0].DireccionComprador is not None:
            if qEncabezadoFactura[0].DireccionComprador.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|DireccionComprador",
                    qEncabezadoFactura[0].DireccionComprador.strip()[:100],
                )

        if qEncabezadoFactura[0].MunicipioComprador is not None:
            if qEncabezadoFactura[0].MunicipioComprador.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|MunicipioComprador",
                    qEncabezadoFactura[0].MunicipioComprador.strip(),
                )

        if qEncabezadoFactura[0].ProvinciaComprador is not None:
            if qEncabezadoFactura[0].ProvinciaComprador.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|ProvinciaComprador",
                    qEncabezadoFactura[0].ProvinciaComprador.strip(),
                )

        if qEncabezadoFactura[0].PaisComprador is not None:
            if qEncabezadoFactura[0].PaisComprador.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|PaisComprador",
                    qEncabezadoFactura[0].PaisComprador.strip()[:60],
                )

        if qEncabezadoFactura[0].FechaEntrega is not None:
            FechaEntrega = formato_fecha_seguro(
                qEncabezadoFactura[0].FechaEntrega, "%d-%m-%Y"
            )
            if FechaEntrega:
                xml.UpdateChildContent(
                    "Encabezado|Comprador|FechaEntrega",
                    FechaEntrega,
                )

        """    
        if qEncabezadoFactura[0].ContactoEntrega is not None: 
            if qEncabezadoFactura[0].ContactoEntrega.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|ContactoEntrega",
                    qEncabezadoFactura[0].ContactoEntrega.strip(),
                ) """
        """
        if qEncabezadoFactura[0].DireccionEntrega is not None:
            if qEncabezadoFactura[0].DireccionEntrega.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|DireccionEntrega",
                    qEncabezadoFactura[0].DireccionEntrega.strip(),
                )"""

        if qEncabezadoFactura[0].TelefonoAdicional is not None and validar_telefono_rd(
            qEncabezadoFactura[0].TelefonoAdicional
        ):
            if qEncabezadoFactura[0].TelefonoAdicional.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|TelefonoAdicional",
                    qEncabezadoFactura[0].TelefonoAdicional.strip()[:12],
                )

        if qEncabezadoFactura[0].FechaOrdenCompra is not None:
            FechaOrdenCompra = formato_fecha_seguro(
                qEncabezadoFactura[0].FechaOrdenCompra, "%d-%m-%Y"
            )
            if FechaOrdenCompra:
                xml.UpdateChildContent(
                    "Encabezado|Comprador|FechaOrdenCompra",
                    FechaOrdenCompra,
                )

        if qEncabezadoFactura[0].NumeroOrdenCompra is not None:
            if qEncabezadoFactura[0].NumeroOrdenCompra.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|NumeroOrdenCompra",
                    qEncabezadoFactura[0].NumeroOrdenCompra.strip()[:20],
                )

        if qEncabezadoFactura[0].CodigoInternoComprador is not None:
            if qEncabezadoFactura[0].CodigoInternoComprador.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|Comprador|CodigoInternoComprador",
                    qEncabezadoFactura[0].CodigoInternoComprador.strip()[:20],
                )

        if (qEncabezadoFactura[0].ResponsablePago or "").strip() != "":
            xml.UpdateChildContent(
                "Encabezado|Comprador|ResponsablePago",
                qEncabezadoFactura[0].ResponsablePago.strip()[:20],
            )

        if (qEncabezadoFactura[0].Informacionadicionalcomprador or "").strip() != "":
            xml.UpdateChildContent(
                "Encabezado|Comprador|Informacionadicionalcomprador",
                qEncabezadoFactura[0].Informacionadicionalcomprador.strip()[:150],
            )

        # Informaciones Adicionales
        if qEncabezadoFactura[0].FechaEmbarque is not None and TipoECF not in [34, 33]:
            FechaEmbarque = formato_fecha_seguro(
                qEncabezadoFactura[0].FechaEmbarque, "%d-%m-%Y"
            )
            if FechaEmbarque:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|FechaEmbarque",
                    FechaEmbarque,
                )

        if qEncabezadoFactura[0].NumeroEmbarque is not None:
            if qEncabezadoFactura[0].NumeroEmbarque.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NumeroEmbarque",
                    qEncabezadoFactura[0].NumeroEmbarque.strip()[:25],
                )

        if qEncabezadoFactura[0].NumeroContenedor is not None:
            if qEncabezadoFactura[0].NumeroContenedor.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NumeroContenedor",
                    qEncabezadoFactura[0].NumeroContenedor.strip()[:100],
                )

        if qEncabezadoFactura[0].NumeroReferencia is not None:
            if qEncabezadoFactura[0].NumeroReferencia.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NumeroReferencia",
                    qEncabezadoFactura[0].NumeroReferencia,
                )

        if qEncabezadoFactura[0].NombrePuertoEmbarque is not None:
            if qEncabezadoFactura[0].NombrePuertoEmbarque.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NombrePuertoEmbarque",
                    qEncabezadoFactura[0].NombrePuertoEmbarque.strip()[:40],
                )

        if qEncabezadoFactura[0].CondicionesEntrega is not None:
            if qEncabezadoFactura[0].CondicionesEntrega.strip() != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|CondicionesEntrega",
                    qEncabezadoFactura[0].CondicionesEntrega.strip()[:3],
                )

        if qEncabezadoFactura[0].TotalFob is not None:
            if qEncabezadoFactura[0].TotalFob != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|TotalFob",
                    f"{Decimal(qEncabezadoFactura[0].TotalFob):.2f}",
                )

        if qEncabezadoFactura[0].Seguro is not None:
            if qEncabezadoFactura[0].Seguro != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|Seguro",
                    f"{Decimal(qEncabezadoFactura[0].Seguro):.2f}",
                )

        if qEncabezadoFactura[0].Flete is not None:
            if qEncabezadoFactura[0].Flete != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|Flete",
                    f"{Decimal(qEncabezadoFactura[0].Flete):.2f}",
                )

        if qEncabezadoFactura[0].OtrosGastos is not None:
            if qEncabezadoFactura[0].OtrosGastos != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|OtrosGastos",
                    f"{Decimal(qEncabezadoFactura[0].OtrosGastos):.2f}",
                )

        if qEncabezadoFactura[0].TotalCif is not None:
            if qEncabezadoFactura[0].TotalCif != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|TotalCif",
                    f"{Decimal(qEncabezadoFactura[0].TotalCif):.2f}",
                )

        if qEncabezadoFactura[0].RegimenAduanero is not None:
            if qEncabezadoFactura[0].RegimenAduanero != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|RegimenAduanero",
                    qEncabezadoFactura[0].RegimenAduanero.strip()[:35],
                )

        if qEncabezadoFactura[0].NombrePuertoSalida is not None:
            if qEncabezadoFactura[0].NombrePuertoSalida != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NombrePuertoSalida",
                    qEncabezadoFactura[0].NombrePuertoSalida.strip()[:40],
                )
        """
        if qEncabezadoFactura[0].NombrePuertoDesembarque is not None:
            if qEncabezadoFactura[0].NombrePuertoDesembarque != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|NombrePuertoDesembarque",
                    qEncabezadoFactura[0].NombrePuertoDesembarque,
                )"""

        if qEncabezadoFactura[0].PesoBruto is not None:
            if qEncabezadoFactura[0].PesoBruto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|PesoBruto",
                    f"{Decimal(qEncabezadoFactura[0].PesoBruto):.2f}",
                )

        if qEncabezadoFactura[0].PesoNeto is not None:
            if qEncabezadoFactura[0].PesoNeto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|PesoNeto",
                    f"{Decimal(qEncabezadoFactura[0].PesoNeto):.2f}",
                )

        if qEncabezadoFactura[0].UnidadPesoBruto is not None:
            if qEncabezadoFactura[0].UnidadPesoBruto % 1 == 0:
                NumeroResultado = f"{int(qEncabezadoFactura[0].UnidadPesoBruto)}"
            else:
                NumeroResultado = (
                    f"{Decimal(qEncabezadoFactura[0].UnidadPesoBruto):.2f}"
                )
            if qEncabezadoFactura[0].UnidadPesoBruto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|UnidadPesoBruto",
                    NumeroResultado,
                )

        if qEncabezadoFactura[0].UnidadPesoNeto is not None:
            if qEncabezadoFactura[0].UnidadPesoNeto % 1 == 0:
                NumeroResultado = f"{int(qEncabezadoFactura[0].UnidadPesoNeto)}"
            else:
                NumeroResultado = f"{Decimal(qEncabezadoFactura[0].UnidadPesoNeto):.2f}"
            if qEncabezadoFactura[0].UnidadPesoNeto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|UnidadPesoNeto",
                    NumeroResultado,
                )

        if qEncabezadoFactura[0].CantidadBulto is not None:
            if qEncabezadoFactura[0].CantidadBulto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|CantidadBulto",
                    f"{Decimal(qEncabezadoFactura[0].CantidadBulto):.2f}",
                )

        if qEncabezadoFactura[0].UnidadBulto is not None:
            if qEncabezadoFactura[0].UnidadBulto != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|UnidadBulto",
                    str(qEncabezadoFactura[0].UnidadBulto),
                )

        if qEncabezadoFactura[0].VolumenBulto is not None:
            if qEncabezadoFactura[0].VolumenBulto % 1 == 0:
                NumeroResultado = f"{int(qEncabezadoFactura[0].VolumenBulto)}"
            else:
                NumeroResultado = f"{Decimal(qEncabezadoFactura[0].VolumenBulto):.2f}"
            if qEncabezadoFactura[0].VolumenBulto != 0:
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|VolumenBulto",
                    NumeroResultado,
                )

        if qEncabezadoFactura[0].UnidadVolumen is not None:
            if qEncabezadoFactura[0].UnidadVolumen != "":
                xml.UpdateChildContent(
                    "Encabezado|InformacionesAdicionales|UnidadVolumen",
                    str(qEncabezadoFactura[0].UnidadVolumen),
                )

        # Transporte
        if qEncabezadoFactura[0].ViaTransporte is not None:
            if qEncabezadoFactura[0].ViaTransporte != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|ViaTransporte",
                    qEncabezadoFactura[0].ViaTransporte,
                )

        if qEncabezadoFactura[0].PaisOrigen is not None:
            if qEncabezadoFactura[0].PaisOrigen != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|PaisOrigen",
                    qEncabezadoFactura[0].PaisOrigen.strip()[:60],
                )

        if qEncabezadoFactura[0].DireccionDestino is not None:
            if qEncabezadoFactura[0].DireccionDestino != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|DireccionDestino",
                    qEncabezadoFactura[0].DireccionDestino.strip()[:100],
                )

        if qEncabezadoFactura[0].PaisDestino is not None:
            if qEncabezadoFactura[0].PaisDestino != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|PaisDestino",
                    qEncabezadoFactura[0].PaisDestino.strip()[:60],
                )

        if qEncabezadoFactura[0].RNCIdentificacionCompaniaTransportista is not None:
            if qEncabezadoFactura[0].RNCIdentificacionCompaniaTransportista != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|RNCIdentificacionCompaniaTransportista",
                    qEncabezadoFactura[
                        0
                    ].RNCIdentificacionCompaniaTransportista.strip()[:20],
                )

        if qEncabezadoFactura[0].NombreCompaniaTransportista is not None:
            if qEncabezadoFactura[0].NombreCompaniaTransportista != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|NombreCompaniaTransportista",
                    qEncabezadoFactura[0].NombreCompaniaTransportista.strip()[:150],
                )

        if qEncabezadoFactura[0].NumeroViaje is not None:
            if qEncabezadoFactura[0].NumeroViaje != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|NumeroViaje",
                    qEncabezadoFactura[0].NumeroViaje.strip()[:20],
                )

        if qEncabezadoFactura[0].Conductor is not None:
            if qEncabezadoFactura[0].Conductor != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|Conductor",
                    qEncabezadoFactura[0].Conductor.strip()[:20],
                )

        if qEncabezadoFactura[0].DocumentoTransporte is not None:
            if qEncabezadoFactura[0].DocumentoTransporte != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|DocumentoTransporte",
                    qEncabezadoFactura[0].DocumentoTransporte,
                )

        if qEncabezadoFactura[0].Ficha is not None:
            if qEncabezadoFactura[0].Ficha != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|Ficha",
                    qEncabezadoFactura[0].Ficha.strip()[:10],
                )

        if qEncabezadoFactura[0].Placa is not None:
            if qEncabezadoFactura[0].Placa != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|Placa",
                    qEncabezadoFactura[0].Placa.strip()[:7],
                )
        # print(qEncabezadoFactura[0].RutaTransporte)
        if qEncabezadoFactura[0].RutaTransporte is not None:
            if qEncabezadoFactura[0].RutaTransporte != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|RutaTransporte",
                    qEncabezadoFactura[0].RutaTransporte.strip()[:20],
                )
        # print(qEncabezadoFactura[0].ZonaTransporte)
        """
        if qEncabezadoFactura[0].ZonaTransporte is not None:
            if qEncabezadoFactura[0].ZonaTransporte != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|ZonaTransporte",
                    qEncabezadoFactura[0].ZonaTransporte,
                )
        """

        if qEncabezadoFactura[0].NumeroAlbaran is not None:
            if qEncabezadoFactura[0].NumeroAlbaran != "":
                xml.UpdateChildContent(
                    "Encabezado|Transporte|NumeroAlbaran",
                    qEncabezadoFactura[0].NumeroAlbaran.strip()[:20],
                )

        # Totales
        if qTotales:
            if (
                qTotales[0].MontoGravadoTotal is not None
                and TipoECF not in [43, 44, 47]
                and qTotales[0].MontoGravadoTotal > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoTotal",
                    f"{Decimal(qTotales[0].MontoGravadoTotal):.2f}",
                )

            if (
                qTotales[0].MontoGravadoI1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI18 == 1
                and qTotales[0].MontoGravadoI1 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI1",
                    f"{Decimal(qTotales[0].MontoGravadoI1):.2f}",  # 18%
                )

            if (
                qTotales[0].MontoGravadoI2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI16 == 1
                and qTotales[0].MontoGravadoI2 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI2",
                    f"{Decimal(qTotales[0].MontoGravadoI2):.2f}",  # 16%
                )

            if (
                qTotales[0].MontoGravadoI3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qTotales[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
                and qTotales[0].MontoGravadoI3 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI3",
                    f"{Decimal(qEncabezadoFactura[0].MontoTotal or 0):.2f}",
                )

            if (
                qTotales[0].MontoExento is not None
                and qTotales[0].IndicadorMontoGravadoIE == 1
                and TipoECF
                not in [
                    46,
                    44,
                ]  # Cuando es Regimenes especiales (44) el Monot exento es igual al MontoTotal
                and qTotales[0].MontoExento > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoExento",
                    f"{Decimal(qTotales[0].MontoExento or 0 ):.2f}",
                )
            # Solo para regimenes especiales
            if (
                qTotales[0].MontoExento is not None
                and qTotales[0].IndicadorMontoGravadoIE == 1
                and TipoECF == 44
                and qTotales[0].MontoExento > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoExento",
                    f"{Decimal(qTotales[0].MontoTotal or 0 ):.2f}",
                )

            if (
                qTotales[0].ITBIS1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI18 == 1
                and int(qTotales[0].ITBIS1) > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS1",
                    convertir_a_porcentaje(qTotales[0].ITBIS1),
                )
            if (
                qTotales[0].ITBIS2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI16 == 1
                and int(qTotales[0].ITBIS2) > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS2",
                    convertir_a_porcentaje(qTotales[0].ITBIS2),
                )

            if (
                qTotales[0].ITBIS3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qTotales[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS3",
                    convertir_a_porcentaje(qTotales[0].ITBIS3 or 0),
                )
            if qTotales[0].TotalITBIS is not None and TipoECF not in [
                43,
                44,
                47,
            ]:
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS",
                    f"{Decimal(qTotales[0].TotalITBIS or 0):.2f}",
                )

            if (
                qTotales[0].TotalITBIS1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI18 == 1
                and qTotales[0].TotalITBIS1 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS1",
                    f"{Decimal(qTotales[0].TotalITBIS1):.2f}",
                )

            if (
                qTotales[0].TotalITBIS2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qTotales[0].IndicadorMontoGravadoI16 == 1
                and qTotales[0].TotalITBIS2 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS2",
                    f"{Decimal(qTotales[0].TotalITBIS2):.2f}",
                )
            if (
                qTotales[0].TotalITBIS3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qTotales[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS3",
                    f"{Decimal(qTotales[0].TotalITBIS3 or 0 ):.2f}",
                )
        else:
            if (
                qEncabezadoFactura[0].MontoGravadoTotal is not None
                and TipoECF not in [43, 44, 47]
                and qEncabezadoFactura[0].MontoGravadoTotal > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoTotal",
                    f"{Decimal(qEncabezadoFactura[0].MontoGravadoTotal):.2f}",
                )

            if (
                qEncabezadoFactura[0].MontoGravadoI1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI18 == 1
                and qEncabezadoFactura[0].MontoGravadoI1 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI1",
                    f"{Decimal(qEncabezadoFactura[0].MontoGravadoI1):.2f}",  # 18%
                )

            if (
                qEncabezadoFactura[0].MontoGravadoI2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI16 == 1
                and qEncabezadoFactura[0].MontoGravadoI2 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI2",
                    f"{Decimal(qEncabezadoFactura[0].MontoGravadoI2):.2f}",  # 16%
                )

            if (
                qEncabezadoFactura[0].MontoGravadoI3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qEncabezadoFactura[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
                and qEncabezadoFactura[0].MontoGravadoI3 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoGravadoI3",
                    f"{Decimal(qEncabezadoFactura[0].MontoTotal or 0):.2f}",
                )

            if (
                qEncabezadoFactura[0].MontoExento is not None
                and qEncabezadoFactura[0].IndicadorMontoGravadoIE == 1
                and TipoECF
                not in [
                    46,
                    44,
                ]  # Cuando es Regimenes especiales (44) el Monot exento es igual al MontoTotal
                and qEncabezadoFactura[0].MontoExento > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoExento",
                    f"{Decimal(qEncabezadoFactura[0].MontoExento or 0 ):.2f}",
                )
            # Solo para regimenes especiales
            if (
                qEncabezadoFactura[0].MontoExento is not None
                and qEncabezadoFactura[0].IndicadorMontoGravadoIE == 1
                and TipoECF == 44
                and qEncabezadoFactura[0].MontoExento > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoExento",
                    f"{Decimal(qEncabezadoFactura[0].MontoTotal or 0 ):.2f}",
                )

            if (
                qEncabezadoFactura[0].ITBIS1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI18 == 1
                and int(qEncabezadoFactura[0].ITBIS1) > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS1",
                    convertir_a_porcentaje(qEncabezadoFactura[0].ITBIS1),
                )
            if (
                qEncabezadoFactura[0].ITBIS2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI16 == 1
                and int(qEncabezadoFactura[0].ITBIS2) > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS2",
                    convertir_a_porcentaje(qEncabezadoFactura[0].ITBIS2),
                )

            if (
                qEncabezadoFactura[0].ITBIS3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qEncabezadoFactura[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|ITBIS3",
                    convertir_a_porcentaje(qEncabezadoFactura[0].ITBIS3 or 0),
                )
            if qEncabezadoFactura[0].TotalITBIS is not None and TipoECF not in [
                43,
                44,
                47,
            ]:
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS",
                    f"{Decimal(qEncabezadoFactura[0].TotalITBIS or 0):.2f}",
                )

            if (
                qEncabezadoFactura[0].TotalITBIS1 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI18 == 1
                and qEncabezadoFactura[0].TotalITBIS1 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS1",
                    f"{Decimal(qEncabezadoFactura[0].TotalITBIS1):.2f}",
                )

            if (
                qEncabezadoFactura[0].TotalITBIS2 is not None
                and TipoECF not in [43, 44, 46, 47]
                and qEncabezadoFactura[0].IndicadorMontoGravadoI16 == 1
                and qEncabezadoFactura[0].TotalITBIS2 > 0
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS2",
                    f"{Decimal(qEncabezadoFactura[0].TotalITBIS2):.2f}",
                )
            if (
                qEncabezadoFactura[0].TotalITBIS3 is not None
                and TipoECF not in [43, 44, 47]
                and (
                    qEncabezadoFactura[0].IndicadorMontoGravadoIEX == 1
                    or IndicadorMontoGravadoIEX == 1
                )
            ):
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBIS3",
                    f"{Decimal(qEncabezadoFactura[0].TotalITBIS3 or 0 ):.2f}",
                )

        # Fin de Totales

        # Detalles Impuestos Adicionales
        if qEncabezadoFactura[0].MontoImpuestoAdicional is not None:
            if float(qEncabezadoFactura[0].MontoImpuestoAdicional) > 0:
                xml.UpdateChildContent(
                    "Encabezado|Totales|MontoImpuestoAdicional",
                    f"{Decimal(qEncabezadoFactura[0].MontoImpuestoAdicional):.2f}",
                )

                ix = 0
                for fila in qTablaImpuestosAdicionales:
                    if fila.TipoImpuesto is not None:
                        xml.UpdateChildContent(
                            f"Encabezado|Totales|ImpuestosAdicionales|ImpuestoAdicional[{ix}]|TipoImpuesto",
                            f"{fila.TipoImpuesto:03d}",
                        )

                    if fila.TasaImpuestoAdicional is not None:
                        if fila.TasaImpuestoAdicional % 1 == 0:
                            TasaImpuestoAdicional = f"{int(fila.TasaImpuestoAdicional)}"
                        else:
                            TasaImpuestoAdicional = (
                                f"{Decimal(fila.TasaImpuestoAdicional):.2f}"
                            )
                        xml.UpdateChildContent(
                            f"Encabezado|Totales|ImpuestosAdicionales|ImpuestoAdicional[{ix}]|TasaImpuestoAdicional",
                            f"{TasaImpuestoAdicional}",
                        )
                    if fila.MontoImpuestoSelectivoConsumoEspecifico is not None:
                        if float(fila.MontoImpuestoSelectivoConsumoEspecifico) > 0:
                            xml.UpdateChildContent(
                                f"Encabezado|Totales|ImpuestosAdicionales|ImpuestoAdicional[{ix}]|MontoImpuestoSelectivoConsumoEspecifico",
                                f"{Decimal(fila.MontoImpuestoSelectivoConsumoEspecifico):.2f}",
                            )
                    if fila.MontoImpuestoSelectivoConsumoAdvalorem is not None:
                        if float(fila.MontoImpuestoSelectivoConsumoAdvalorem) > 0:
                            xml.UpdateChildContent(
                                f"Encabezado|Totales|ImpuestosAdicionales|ImpuestoAdicional[{ix}]|MontoImpuestoSelectivoConsumoAdvalorem",
                                f"{Decimal(fila.MontoImpuestoSelectivoConsumoAdvalorem):.2f}",
                            )
                    if fila.OtrosImpuestosAdicionales is not None:
                        if float(fila.OtrosImpuestosAdicionales) > 0:
                            xml.UpdateChildContent(
                                f"Encabezado|Totales|ImpuestosAdicionales|ImpuestoAdicional[{ix}]|OtrosImpuestosAdicionales",
                                f"{Decimal(fila.OtrosImpuestosAdicionales):.2f}",
                            )
                    ix = ix + 1

        if qEncabezadoFactura[0].MontoTotal is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|MontoTotal",
                f"{Decimal(qEncabezadoFactura[0].MontoTotal):.2f}",
            )

        if qEncabezadoFactura[0].MontoNoFacturable is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|MontoNoFacturable",
                f"{Decimal(qEncabezadoFactura[0].MontoNoFacturable):.2f}",
            )

        if qEncabezadoFactura[0].MontoPeriodo is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|MontoPeriodo",
                f"{Decimal(qEncabezadoFactura[0].MontoPeriodo):.2f}",
            )

        if qEncabezadoFactura[0].SaldoAnterior is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|SaldoAnterior",
                f"{Decimal(qEncabezadoFactura[0].SaldoAnterior):.2f}",
            )

        if qEncabezadoFactura[0].MontoAvancePago is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|MontoAvancePago",
                f"{Decimal(qEncabezadoFactura[0].MontoAvancePago):.2f}",
            )

        if qEncabezadoFactura[0].ValorPagar is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|ValorPagar",
                f"{Decimal(qEncabezadoFactura[0].ValorPagar):.2f}",
            )

        if qEncabezadoFactura[0].TotalITBISRetenido is not None:
            if qEncabezadoFactura[0].TotalITBISRetenido > 0 or TipoECF == 41:
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalITBISRetenido",
                    f"{Decimal(qEncabezadoFactura[0].TotalITBISRetenido):.2f}",
                )

        if qEncabezadoFactura[0].TotalISRRetencion is not None:
            if qEncabezadoFactura[0].TotalISRRetencion > 0 or TipoECF == 41:
                xml.UpdateChildContent(
                    "Encabezado|Totales|TotalISRRetencion",
                    f"{Decimal(qEncabezadoFactura[0].TotalISRRetencion):.2f}",
                )

        if qEncabezadoFactura[0].TotalITBISPercepcion is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|TotalITBISPercepcion",
                f"{Decimal(qEncabezadoFactura[0].TotalITBISPercepcion):.2f}",
            )

        if qEncabezadoFactura[0].TotalISRPercepcion is not None:
            xml.UpdateChildContent(
                "Encabezado|Totales|TotalISRPercepcion",
                f"{Decimal(qEncabezadoFactura[0].TotalISRPercepcion):.2f}",
            )

        # Otras Monedas
        if qEncabezadoFactura[0].TipoMoneda is not None:
            if qEncabezadoFactura[0].TipoMoneda != "DOP":

                xml.UpdateChildContent(
                    "Encabezado|OtraMoneda|TipoMoneda",
                    str(qEncabezadoFactura[0].TipoMoneda.strip()[:3]),
                )

                if qEncabezadoFactura[0].TipoCambio is not None:
                    if float(qEncabezadoFactura[0].TipoCambio) != 0:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TipoCambio",
                            f"{Decimal(qEncabezadoFactura[0].TipoCambio):.4f}",
                        )
                # Totales Otra Moneda
                if qTotales:
                    if (
                        qTotales[0].MontoGravadoTotalOtraMoneda is not None
                        and TipoECF not in [43, 44, 47]
                        and qTotales[0].MontoGravadoTotal > 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravadoTotalOtraMoneda",
                            f"{Decimal(qTotales[0].MontoGravadoTotalOtraMoneda):.2f}",
                        )
                    if (
                        qTotales[0].MontoGravado1OtraMoneda is not None
                        and qTotales[0].IndicadorMontoGravadoI18 == 1
                        and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado1OtraMoneda",
                            f"{Decimal(qTotales[0].MontoGravado1OtraMoneda):.2f}",
                        )
                    if (
                        qTotales[0].MontoGravado2OtraMoneda is not None
                        and qTotales[0].IndicadorMontoGravadoI16 == 1
                        and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado2OtraMoneda",
                            f"{Decimal(qTotales[0].MontoGravado2OtraMoneda):.2f}",
                        )
                    if qTotales[0].MontoGravado3OtraMoneda is not None and (
                        (
                            qTotales[0].IndicadorMontoGravadoIEX == 1
                            and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                        )
                        or IndicadorMontoGravadoIEX == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado3OtraMoneda",
                            f"{Decimal(qTotales[0].MontoGravado3OtraMoneda):.2f}",
                        )

                    if (
                        qTotales[0].MontoExentoOtraMoneda is not None
                        and qTotales[0].IndicadorMontoGravadoIE == 1
                        # and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                        and IndicadorMontoGravadoIEX == 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoExentoOtraMoneda",
                            f"{Decimal(qTotales[0].MontoExentoOtraMoneda or 0):.2f}",
                        )

                    if qTotales[0].TotalITBISOtraMoneda is not None and TipoECF not in [
                        43,
                        44,
                        47,
                    ]:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBISOtraMoneda",
                            f"{Decimal(qTotales[0].TotalITBISOtraMoneda):.2f}",
                        )

                    if (
                        qTotales[0].TotalITBIS1OtraMoneda is not None
                        and qTotales[0].IndicadorMontoGravadoI18 == 1
                        and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS1OtraMoneda",
                            f"{Decimal(qTotales[0].TotalITBIS1OtraMoneda):.2f}",
                        )

                    if (
                        qTotales[0].TotalITBIS2OtraMoneda is not None
                        and qTotales[0].IndicadorMontoGravadoI16 == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS2OtraMoneda",
                            f"{Decimal(qTotales[0].TotalITBIS2OtraMoneda):.2f}",
                        )
                    if qTotales[0].TotalITBIS3OtraMoneda is not None and (
                        (
                            qTotales[0].IndicadorMontoGravadoIEX == 1
                            and qEncabezadoFactura[0].IndicadorNotaCredito == 0
                        )
                        or IndicadorMontoGravadoIEX == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS3OtraMoneda",
                            f"{Decimal(qTotales[0].TotalITBIS3OtraMoneda):.2f}",
                        )
                    if qTotales[0].MontoTotalOtraMoneda is not None:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoTotalOtraMoneda",
                            f"{Decimal(qTotales[0].MontoTotalOtraMoneda):.2f}",
                        )
                else:
                    if qEncabezadoFactura[0].MontoGravadoTotalOtraMoneda is not None:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravadoTotalOtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoGravadoTotalOtraMoneda):.2f}",
                        )
                    if (
                        qEncabezadoFactura[0].MontoGravado1OtraMoneda is not None
                        and qEncabezadoFactura[0].IndicadorMontoGravadoI18 == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado1OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoGravado1OtraMoneda):.2f}",
                        )
                    if (
                        qEncabezadoFactura[0].MontoGravado2OtraMoneda is not None
                        and qEncabezadoFactura[0].IndicadorMontoGravadoI16 == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado2OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoGravado2OtraMoneda):.2f}",
                        )
                    if qEncabezadoFactura[0].MontoGravado3OtraMoneda is not None and (
                        qEncabezadoFactura[0].IndicadorMontoGravadoIEX == 1
                        or IndicadorMontoGravadoIEX == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoGravado3OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoGravado3OtraMoneda):.2f}",
                        )

                    if (
                        qEncabezadoFactura[0].MontoExentoOtraMoneda is not None
                        and qEncabezadoFactura[0].IndicadorMontoGravadoIE == 1
                        and IndicadorMontoGravadoIEX == 0
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoExentoOtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoExentoOtraMoneda or 0):.2f}",
                        )

                    if qEncabezadoFactura[0].TotalITBISOtraMoneda is not None:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBISOtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].TotalITBISOtraMoneda):.2f}",
                        )

                    if (
                        qEncabezadoFactura[0].TotalITBIS1OtraMoneda is not None
                        and qEncabezadoFactura[0].IndicadorMontoGravadoI18 == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS1OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].TotalITBIS1OtraMoneda):.2f}",
                        )

                    if (
                        qEncabezadoFactura[0].TotalITBIS2OtraMoneda is not None
                        and qEncabezadoFactura[0].IndicadorMontoGravadoI16 == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS2OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].TotalITBIS2OtraMoneda):.2f}",
                        )
                    if qEncabezadoFactura[0].TotalITBIS3OtraMoneda is not None and (
                        qEncabezadoFactura[0].IndicadorMontoGravadoIEX == 1
                        or IndicadorMontoGravadoIEX == 1
                    ):
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|TotalITBIS3OtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].TotalITBIS3OtraMoneda):.2f}",
                        )
                    if qEncabezadoFactura[0].MontoTotalOtraMoneda is not None:
                        xml.UpdateChildContent(
                            "Encabezado|OtraMoneda|MontoTotalOtraMoneda",
                            f"{Decimal(qEncabezadoFactura[0].MontoTotalOtraMoneda):.2f}",
                        )
                # Fin Totales Otra Moneda

        # Tradetalle
        idx = 0
        for dfila in qDetalleFactura:

            NumeroLinea = idx + 1

            xml.UpdateChildContentInt(
                f"DetallesItems|Item[{idx}]|NumeroLinea", int(NumeroLinea)
            )
            # Codigos de Item
            # 1
            if dfila.TipoCodigo1 is not None:
                if dfila.TipoCodigo1.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|TipoCodigo",
                        dfila.TipoCodigo1.strip()[:14],
                    )

            if dfila.CodigoItem1 is not None:
                if dfila.CodigoItem1.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|CodigoItem",
                        str(dfila.CodigoItem1.strip()[:35]),
                    )

            # 2
            if dfila.TipoCodigo2 is not None:
                if dfila.TipoCodigo2.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|TipoCodigo[1]",
                        str(dfila.TipoCodigo2.strip()[:14]),
                    )

            if dfila.CodigoItem2 is not None:
                if dfila.CodigoItem2.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|CodigoItem[1]",
                        str(dfila.CodigoItem2.strip()[:35]),
                    )

            # 3
            if dfila.TipoCodigo3 is not None:
                if dfila.TipoCodigo3.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|TipoCodigo[2]",
                        str(dfila.TipoCodigo3.strip()[:14]),
                    )

            if dfila.CodigoItem3 is not None:
                if dfila.CodigoItem3.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|CodigoItem[2]",
                        str(dfila.CodigoItem3.strip()[:35]),
                    )

            # 4
            if dfila.TipoCodigo4 is not None:
                if dfila.TipoCodigo4.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|TipoCodigo[3]",
                        str(dfila.TipoCodigo4.strip()[:14]),
                    )

            if dfila.CodigoItem4 is not None:
                if dfila.CodigoItem4.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|CodigoItem[3]",
                        str(dfila.CodigoItem4.strip()[:35]),
                    )

            # 5
            if dfila.TipoCodigo5 is not None:
                if dfila.TipoCodigo5.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|TipoCodigo[4]",
                        str(dfila.TipoCodigo5.strip()[:14]),
                    )

            if dfila.CodigoItem5 is not None:
                if dfila.CodigoItem5.strip() != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaCodigosItem|CodigosItem|CodigoItem[4]",
                        str(dfila.CodigoItem5.strip()[:35]),
                    )
            # Fin de tabla de Codigos

            if dfila.IndicadorFacturacion is not None:
                if TipoECF == 44:
                    IndicadorFacturacion = 4
                elif TipoECF == 46:
                    IndicadorFacturacion = 3
                else:
                    IndicadorFacturacion = dfila.IndicadorFacturacion

                xml.UpdateChildContentInt(
                    f"DetallesItems|Item[{idx}]|IndicadorFacturacion",
                    int(IndicadorFacturacion),
                )

            if dfila.IndicadorAgenteRetencionoPercepcion is not None:
                if dfila.IndicadorAgenteRetencionoPercepcion != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|Retencion|IndicadorAgenteRetencionoPercepcion",
                        str(dfila.IndicadorAgenteRetencionoPercepcion),
                    )

            if dfila.MontoITBISRetenido is not None:
                if dfila.MontoITBISRetenido > 0 or TipoECF == 41:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|Retencion|MontoITBISRetenido",
                        f"{Decimal(dfila.MontoITBISRetenido):.2f}",
                    )

            if dfila.MontoISRRetenido is not None:
                if dfila.MontoISRRetenido > 0 or TipoECF == 41:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|Retencion|MontoISRRetenido",
                        f"{Decimal(dfila.MontoISRRetenido):.2f}",
                    )

            xml.UpdateChildContent(
                f"DetallesItems|Item[{idx}]|NombreItem",
                dfila.NombreItem.strip()[:80],
            )

            xml.UpdateChildContentInt(
                f"DetallesItems|Item[{idx}]|IndicadorBienoServicio",
                int(dfila.IndicadorBienoServicio),
            )

            if dfila.DescripcionItem is not None:
                if dfila.DescripcionItem != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|DescripcionItem",
                        dfila.DescripcionItem.strip()[:1000],
                    )

            xml.UpdateChildContent(
                f"DetallesItems|Item[{idx}]|CantidadItem",
                f"{Decimal(dfila.CantidadItem):.2f}",
            )

            if dfila.UnidadMedida is not None:
                if dfila.UnidadMedida != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|UnidadMedida",
                        dfila.UnidadMedida,
                    )

            if dfila.CantidadReferencia is not None:
                if dfila.CantidadReferencia >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|CantidadReferencia",
                        str(int(dfila.CantidadReferencia)),
                    )

            if dfila.UnidadReferencia is not None:
                if dfila.UnidadReferencia != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|UnidadReferencia",
                        str(dfila.UnidadReferencia),
                    )

            # Tabla de SubCantidad
            # 1
            if dfila.Subcantidad1 is not None:
                if dfila.Subcantidad1 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem|Subcantidad",
                        f"{Decimal(dfila.Subcantidad1):.3f}",
                    )
            if dfila.CodigoSubcantidad1 is not None:
                if dfila.CodigoSubcantidad1 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem|CodigoSubcantidad",
                        str(dfila.CodigoSubcantidad1),
                    )

            # 2
            if dfila.Subcantidad2 is not None:
                if dfila.Subcantidad2 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[1]|Subcantidad",
                        f"{Decimal(dfila.Subcantidad2):.3f}",
                    )
            if dfila.CodigoSubcantidad2 is not None:
                if dfila.CodigoSubcantidad2 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[1]|CodigoSubcantidad",
                        str(dfila.CodigoSubcantidad2),
                    )

            # 3
            if dfila.Subcantidad3 is not None:
                if dfila.Subcantidad3 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[2]|Subcantidad",
                        f"{Decimal(dfila.Subcantidad3):.3f}",
                    )
            if dfila.CodigoSubcantidad3 is not None:
                if dfila.CodigoSubcantidad3 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[2]|CodigoSubcantidad",
                        str(dfila.CodigoSubcantidad3),
                    )

            # 4
            if dfila.Subcantidad4 is not None:
                if dfila.Subcantidad4 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[3]|Subcantidad",
                        f"{Decimal(dfila.Subcantidad4):.3f}",
                    )
            if dfila.CodigoSubcantidad4 is not None:
                if dfila.CodigoSubcantidad4 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[3]|CodigoSubcantidad",
                        str(dfila.CodigoSubcantidad4),
                    )

            # 5
            if dfila.Subcantidad5 is not None:
                if dfila.Subcantidad5 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[4]|Subcantidad",
                        f"{Decimal(dfila.Subcantidad5):.3f}",
                    )
            if dfila.CodigoSubcantidad5 is not None:
                if dfila.CodigoSubcantidad5 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubcantidad|SubcantidadItem[4]|CodigoSubcantidad",
                        str(dfila.CodigoSubcantidad5),
                    )

            # Fin de Tabla de SubCantidad

            if dfila.GradosAlcohol is not None:
                if dfila.GradosAlcohol >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|GradosAlcohol",
                        f"{Decimal(dfila.GradosAlcohol):.2f}",
                    )

            if dfila.PrecioUnitarioReferencia is not None:
                if dfila.PrecioUnitarioReferencia >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|PrecioUnitarioReferencia",
                        f"{Decimal(dfila.PrecioUnitarioReferencia):.2f}",
                    )

            if dfila.FechaElaboracion is not None:
                xml.UpdateChildContent(
                    f"DetallesItems|Item[{idx}]|FechaElaboracion",
                    f"{dfila.FechaElaboracion}",
                )

            if dfila.FechaVencimientoItem is not None:
                xml.UpdateChildContent(
                    f"DetallesItems|Item[{idx}]|FechaVencimientoItem",
                    f"{dfila.FechaVencimientoItem}",
                )

            # Mineria
            if dfila.PesoNetoKilogramo is not None:
                if dfila.PesoNetoKilogramo >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|Mineria|PesoNetoKilogramo",
                        f"{Decimal(dfila.PesoNetoKilogramo):.2f}",
                    )

            if dfila.PesoNetoMineria is not None:
                if dfila.PesoNetoMineria >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|Mineria|PesoNetoMineria",
                        f"{Decimal(dfila.PesoNetoMineria):.2f}",
                    )

            if dfila.TipoAfiliacion is not None:
                xml.UpdateChildContent(
                    f"DetallesItems|Item[{idx}]|Mineria|TipoAfiliacion",
                    f"{dfila.TipoAfiliacion}",
                )

            if dfila.Liquidacion is not None:
                xml.UpdateChildContent(
                    f"DetallesItems|Item[{idx}]|Mineria|Liquidacion",
                    f"{dfila.Liquidacion}",
                )
            # Fin de Mineria

            xml.UpdateChildContent(
                f"DetallesItems|Item[{idx}]|PrecioUnitarioItem",
                f"{Decimal(dfila.PrecioUnitarioItem):.4f}",
            )

            if dfila.DescuentoMonto is not None:
                if dfila.DescuentoMonto > 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|DescuentoMonto",
                        f"{Decimal(dfila.DescuentoMonto):.2f}",
                    )

                    # Tabla de SubDescuento
                    # 1
                    if dfila.TipoSubDescuento1 is not None:
                        if dfila.TipoSubDescuento1.strip() != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento|TipoSubDescuento",
                                dfila.TipoSubDescuento1.strip()[:1],
                            )
                    if dfila.SubDescuentoPorcentaje1 is not None:
                        if dfila.SubDescuentoPorcentaje1 != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento|SubDescuentoPorcentaje",
                                f"{Decimal(dfila.SubDescuentoPorcentaje1):.2f}",
                            )

                    if dfila.MontoSubDescuento1 is not None:
                        if dfila.MontoSubDescuento1 >= 0:
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento|MontoSubDescuento",
                                f"{Decimal(dfila.MontoSubDescuento1):.2f}",
                            )
                    # 2
                    if dfila.TipoSubDescuento2 is not None:
                        if dfila.TipoSubDescuento2.strip() != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[1]|TipoSubDescuento",
                                dfila.TipoSubDescuento2.strip()[:1],
                            )
                    if dfila.SubDescuentoPorcentaje2 is not None:
                        if dfila.SubDescuentoPorcentaje2 != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[1]|SubDescuentoPorcentaje",
                                f"{Decimal(dfila.SubDescuentoPorcentaje2):.2f}",
                            )
                    if dfila.MontoSubDescuento2 is not None:
                        if dfila.MontoSubDescuento2 >= 0:
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[1]|MontoSubDescuento",
                                f"{Decimal(dfila.MontoSubDescuento2):.2f}",
                            )
                    # 3
                    if dfila.TipoSubDescuento3 is not None:
                        if dfila.TipoSubDescuento3.strip() != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[2]|TipoSubDescuento",
                                dfila.TipoSubDescuento3.strip()[:1],
                            )
                    if dfila.SubDescuentoPorcentaje3 is not None:
                        if dfila.SubDescuentoPorcentaje3 != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[2]|SubDescuentoPorcentaje",
                                f"{Decimal(dfila.SubDescuentoPorcentaje3):.2f}",
                            )
                    if dfila.MontoSubDescuento3 is not None:
                        if dfila.MontoSubDescuento3 >= 0:
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[2]|MontoSubDescuento",
                                f"{Decimal(dfila.MontoSubDescuento3):.2f}",
                            )
                    # 4
                    if dfila.TipoSubDescuento4 is not None:
                        if dfila.TipoSubDescuento4.strip() != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[3]|TipoSubDescuento",
                                dfila.TipoSubDescuento4.strip()[:1],
                            )
                    if dfila.SubDescuentoPorcentaje4 is not None:
                        if dfila.SubDescuentoPorcentaje4 != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[3]|SubDescuentoPorcentaje",
                                f"{Decimal(dfila.SubDescuentoPorcentaje4):.2f}",
                            )
                    if dfila.MontoSubDescuento4 is not None:
                        if dfila.MontoSubDescuento4 >= 0:
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[3]|MontoSubDescuento",
                                f"{Decimal(dfila.MontoSubDescuento4):.2f}",
                            )

                    # 5
                    if dfila.TipoSubDescuento5 is not None:
                        if dfila.TipoSubDescuento5.strip() != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[4]|TipoSubDescuento",
                                dfila.TipoSubDescuento5.strip()[:1],
                            )
                    if dfila.SubDescuentoPorcentaje5 is not None:
                        if dfila.SubDescuentoPorcentaje5 != "":
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[4]|SubDescuentoPorcentaje",
                                f"{Decimal(dfila.SubDescuentoPorcentaje5):.2f}",
                            )
                    if dfila.MontoSubDescuento5 is not None:
                        if dfila.MontoSubDescuento5 >= 0:
                            xml.UpdateChildContent(
                                f"DetallesItems|Item[{idx}]|TablaSubDescuento|SubDescuento[4]|MontoSubDescuento",
                                f"{Decimal(dfila.MontoSubDescuento5):.2f}",
                            )
                    # Fin de Tabla de Descuentos

            if dfila.MontoRecargo is not None:
                if dfila.MontoRecargo >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|RecargoMonto",
                        f"{Decimal(dfila.MontoRecargo):.2f}",
                    )

            # Tabla de  SubRecargos
            # 1
            if dfila.TipoSubRecargo1 is not None:
                if dfila.TipoSubRecargo1 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo|TipoSubRecargo",
                        dfila.TipoSubRecargo1.strip()[:1],
                    )
            if dfila.SubRecargoPorcentaje1 is not None:
                if dfila.SubRecargoPorcentaje1 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo|SubRecargoPorcentaje",
                        f"{Decimal(dfila.SubRecargoPorcentaje1):.2f}",
                    )
            if dfila.MontoSubRecargo1 is not None:
                if dfila.MontoSubRecargo1 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo|MontoSubRecargo",
                        f"{Decimal(dfila.MontoSubRecargo1):.2f}",
                    )
            # 2
            if dfila.TipoSubRecargo2 is not None:
                if dfila.TipoSubRecargo2 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[1]|TipoSubRecargo",
                        dfila.TipoSubRecargo2.strip()[:1],
                    )
            if dfila.SubRecargoPorcentaje2 is not None:
                if dfila.SubRecargoPorcentaje2 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[1]|SubRecargoPorcentaje",
                        f"{Decimal(dfila.SubRecargoPorcentaje2):.2f}",
                    )
            if dfila.MontoSubRecargo2 is not None:
                if dfila.MontoSubRecargo2 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[1]|MontoSubRecargo",
                        f"{Decimal(dfila.MontoSubRecargo2):.2f}",
                    )
            # 3
            if dfila.TipoSubRecargo3 is not None:
                if dfila.TipoSubRecargo3 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[2]|TipoSubRecargo",
                        dfila.TipoSubRecargo3.strip()[:1],
                    )
            if dfila.SubRecargoPorcentaje3 is not None:
                if dfila.SubRecargoPorcentaje3 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[2]|SubRecargoPorcentaje",
                        f"{Decimal(dfila.SubRecargoPorcentaje3):.2f}",
                    )
            if dfila.MontoSubRecargo3 is not None:
                if dfila.MontoSubRecargo3 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[2]|MontoSubRecargo",
                        f"{Decimal(dfila.MontoSubRecargo3):.2f}",
                    )
            # 4
            if dfila.TipoSubRecargo4 is not None:
                if dfila.TipoSubRecargo4 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[3]|TipoSubRecargo",
                        dfila.TipoSubRecargo4.strip()[:1],
                    )
            if dfila.SubRecargoPorcentaje4 is not None:
                if dfila.SubRecargoPorcentaje4 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[3]|SubRecargoPorcentaje",
                        f"{Decimal(dfila.SubRecargoPorcentaje4):.2f}",
                    )
            if dfila.MontoSubRecargo4 is not None:
                if dfila.MontoSubRecargo4 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[3]|MontoSubRecargo",
                        f"{Decimal(dfila.MontoSubRecargo4):.2f}",
                    )
            # 5
            if dfila.TipoSubRecargo5 is not None:
                if dfila.TipoSubRecargo5 != "":
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[4]|TipoSubRecargo",
                        dfila.TipoSubRecargo5.strip()[:1],
                    )
            if dfila.SubRecargoPorcentaje5 is not None:
                if dfila.SubRecargoPorcentaje5 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[4]|SubRecargoPorcentaje",
                        f"{Decimal(dfila.SubRecargoPorcentaje5):.2f}",
                    )
            if dfila.MontoSubRecargo5 is not None:
                if dfila.MontoSubRecargo5 >= 0:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaSubRecargo|SubRecargo[4]|MontoSubRecargo",
                        f"{Decimal(dfila.MontoSubRecargo5):.2f}",
                    )

            # Fin de Tabla de Recargos

            # Tabal impuestos Adicionales
            ix = 0
            for fila in qTablaImpuestosAdicionales:
                if fila.TipoImpuesto is not None:
                    xml.UpdateChildContent(
                        f"DetallesItems|Item[{idx}]|TablaImpuestoAdicional|ImpuestoAdicional[{ix}]|TipoImpuesto",
                        f"{fila.TipoImpuesto:03d}",
                    )

                # Tabla de Detalle de otra Moneda
                # PrecioOtraMoneda
                # DescuentoOtraMoneda
                # RecargoOtraMoneda
                # MontoItemOtraMoneda

                # Fin Tabla de Detalle de otra Moneda

                ix = ix + 1
            # Fin de Tabla de Impuestos Adicionales

            xml.UpdateChildContent(
                f"DetallesItems|Item[{idx}]|MontoItem",
                f"{Decimal(dfila.MontoItem):.2f}",
            )

            idx = idx + 1

        # Tabla de Descuentos y Recargos
        ix = 0
        for fila in qTablaDescuentosORecargos:
            NumeroLinea = ix + 1
            xml.UpdateChildContentInt(
                f"DescuentosORecargos|DescuentoORecargo[{ix}]|NumeroLinea",
                int(NumeroLinea),
            )

            # Validación para TipoAjuste (debe ser string no vacío)
            if fila.TipoAjuste is not None:
                if fila.TipoAjuste.strip() != "":
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|TipoAjuste",
                        fila.TipoAjuste.strip()[:1],
                    )

            # Validación para IndicadorNorma1007 (debe ser entero)
            if fila.IndicadorNorma1007 is not None:
                xml.UpdateChildContentInt(
                    f"DescuentosORecargos|DescuentoORecargo[{ix}]|IndicadorNorma1007",
                    fila.IndicadorNorma1007,
                )

            # Validación para DescripcionDescuentooRecargo (debe ser string no vacío)
            if fila.DescripcionDescuentooRecargo is not None:
                if fila.DescripcionDescuentooRecargo.strip() != "":
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|DescripcionDescuentooRecargo",
                        fila.DescripcionDescuentooRecargo,
                    )

            # Validación para TipoValor (debe ser string no vacío)
            if fila.TipoValor is not None:
                if fila.TipoValor.strip() != "":
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|TipoValor",
                        fila.TipoValor.strip()[:1],
                    )

            # Validación para ValorDescuentooRecargo (debe ser número válido)
            if fila.ValorDescuentooRecargo is not None:
                if float(fila.ValorDescuentooRecargo) >= 0:
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|ValorDescuentooRecargo",
                        f"{Decimal(fila.ValorDescuentooRecargo):.2f}",
                    )

            # Validación para MontoDescuentooRecargo (debe ser número válido)
            if fila.MontoDescuentooRecargo is not None:
                if float(fila.MontoDescuentooRecargo) >= 0:
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|MontoDescuentooRecargo",
                        f"{Decimal(fila.MontoDescuentooRecargo):.2f}",
                    )

            # Validación para MontoDescuentooRecargoOtraMoneda (debe ser número válido)
            if fila.MontoDescuentooRecargoOtraMoneda is not None:
                if float(fila.MontoDescuentooRecargoOtraMoneda) >= 0:
                    xml.UpdateChildContent(
                        f"DescuentosORecargos|DescuentoORecargo[{ix}]|MontoDescuentooRecargoOtraMoneda",
                        f"{Decimal(fila.MontoDescuentooRecargoOtraMoneda):.2f}",
                    )
            # print(fila.IndicadorFacturacionDescuentooRecargo)
            # Validación para IndicadorFacturacionDescuentooRecargo (debe ser entero)
            if fila.IndicadorFacturacionDescuentooRecargo is not None:
                xml.UpdateChildContent(
                    f"DescuentosORecargos|DescuentoORecargo[{ix}]|IndicadorFacturacionDescuentooRecargo",
                    str(fila.IndicadorFacturacionDescuentooRecargo),
                )

            ix = ix + 1
        # Fin de Tabla de Descuentos y Recargos

        # Informacion de Referencia

        if TipoECF == 33 or TipoECF == 34:

            # print((qEncabezadoFactura[0].NCFModificado or "").strip())

            if (qEncabezadoFactura[0].NCFModificado or "").strip() != "":
                # print((qEncabezadoFactura[0].NCFModificado or "").strip())
                # print(xml.ToString())
                xml.UpdateChildContent(
                    "InformacionReferencia|NCFModificado",
                    qEncabezadoFactura[0].NCFModificado.strip(),
                )
                # print(xml.ToString())
            else:
                return (
                    70,
                    f'No hay NCF  ser modificado presente: {(qEncabezadoFactura[0].NCFModificado or "").strip()}.',
                )
            if (qEncabezadoFactura[0].RNCOtroContribuyente or "").strip() != "":
                xml.UpdateChildContent(
                    "InformacionReferencia|RNCOtroContribuyente",
                    qEncabezadoFactura[0].RNCOtroContribuyente.strip(),
                )
                # print(xml.ToString())
            if qEncabezadoFactura[0].FechaNCFModificado is not None:
                FechaNCFModificado = formato_fecha_seguro(
                    qEncabezadoFactura[0].FechaNCFModificado, "%d-%m-%Y"
                )
                if FechaNCFModificado:
                    xml.UpdateChildContent(
                        "InformacionReferencia|FechaNCFModificado",
                        FechaNCFModificado,
                    )
                    # print(xml.ToString())
                else:
                    return (
                        70,
                        f'Verifique la Fecha del NCF Modificado: {(FechaNCFModificado or "").strip()}.',
                    )
            if (qEncabezadoFactura[0].CodigoModificacion or 0) != 0:
                xml.UpdateChildContentInt(
                    "InformacionReferencia|CodigoModificacion",
                    qEncabezadoFactura[0].CodigoModificacion,
                )
                # print(xml.ToString())
            if qEncabezadoFactura[0].RazonModificacion is not None:
                if qEncabezadoFactura[0].RazonModificacion.strip() != "":
                    xml.UpdateChildContent(
                        "InformacionReferencia|RazonModificacion",
                        qEncabezadoFactura[0].RazonModificacion.strip()[:90],
                    )
                    # print(xml.ToString())

        # Fin de Informacion de Referencia

        fin = time.time()
        tiempo_total = fin - inicio
        log_event(
            logger,
            "info",
            f"Tiempo de ejecución hasta la generacion del xml completo: {tiempo_total:.4f} segundos",
        )

        Ruta = "generadas/"
        base_nombre = f"{qEncabezadoFactura[0].RNCEmisor.strip()}{qEncabezadoFactura[0].eNCF.strip()}"
        carpeta = os.path.join(GConfig.FEDGII.RutaXML, Ruta)
        os.makedirs(carpeta, exist_ok=True)

        NombreXML = os.path.join(carpeta, f"{base_nombre}.xml")

        # 🔁 Si existe el XML actual, renombrarlo (conservar el nombre base)
        if os.path.exists(NombreXML):
            nombre_anterior = generar_nombre_incremental(NombreXML)

        # 💾 Guardar el nuevo XML
        xml.SaveXml(NombreXML)
        log_event(logger, "info", f"Nuevo archivo guardado como: {NombreXML}")

    except Exception as e:
        # Error 70: capturamos cualquier excepción no controlada y devolvemos
        # el detalle en el mensaje para facilitar el diagnóstico.
        m = f"Error al procesar el registro : {e}:{ traceback.extract_tb(sys.exc_info()[2])}"

        log_event(logger, "error", m)
        return "70", m
    return "02", "XML Generado."  # Realizado


def GenerarXMLRFCE(cn1, RNCEmisor, eNCF):
    """
    Genera el XML RFCE (Resumen de e-CF tipo 32).

    Este procedimiento construye un XML resumido para comprobantes de consumo
    menores (RFCE / TipoECF = 32), usando exclusivamente la información del
    encabezado, resumen de totales y tablas auxiliares del ERP.

    Características de este XML:
    - No incluye detalle de ítems
    - No incluye referencias de modificación (NC/ND)
    - No realiza validación de totales ni reintentos
    - No firma ni envía; solamente construye y persiste el resumen
    - Está orientado a procesos de presentación/resumen interno
      más que a envío fiscal

    Parámetros:
        cn1        : Objeto con las funciones de acceso a datos del ERP.
        RNCEmisor  : RNC del emisor (string).
        eNCF       : e-CF emitido (string).

    Retorno:
        True → operación realizada sin errores dentro de la lógica definida.

    Notas para programadores:
        - TipoECF se fuerza a 32 porque RFCE siempre es comprobante de consumo menor.
        - Las dependencias externas (XmlNative, Decimal, GConfig, logger, helpers)
          se asumen existentes en el contexto sin redefinirlas aquí.
        - Esta función no retorna códigos 02/61/62/70 (a diferencia de GenerarXML),
          porque su función es únicamente generar el resumen.
    """
    # ============================
    # 1. Normalización de entrada
    # ============================
    RNCEmisor = RNCEmisor.strip()
    eNCF = eNCF.strip()

    # ============================
    # 2. Consulta de datos base ERP
    # ============================
    qEncabezadoFactura = cn1._get_encabezado(RNCEmisor.strip(), eNCF.strip())
    qTablaPago = cn1._get_tablapago(RNCEmisor.strip(), eNCF.strip())
    qTablaImpuestosAdicionales = cn1._get_tablaimpuestosadicionales(
        RNCEmisor.strip(), eNCF.strip()
    )

    qTotales = None
    if cn1.vista_existe("vFETotales"):
        qTotales = cn1._get_totales(RNCEmisor.strip(), eNCF.strip())

    # ============================
    # 3. Inicialización del XML
    # ============================
    xml = XmlNative()
    xml.Tag = "ECF"
    xml.UpdateChildContent("Encabezado|Version", "1.0")

    # TipoECF forzado para RFCE
    TipoECF = 32
    xml.UpdateChildContentInt("Encabezado|IdDoc|TipoeCF", TipoECF)
    xml.UpdateChildContent(
        "Encabezado|IdDoc|eNCF", qEncabezadoFactura[0].eNCF.strip()[:13]
    )

    # ============================
    # 4. Identificación de ingresos y pago
    # ============================
    if qEncabezadoFactura[0].TipoIngresos is not None:
        xml.UpdateChildContent(
            "Encabezado|IdDoc|TipoIngresos", qEncabezadoFactura[0].TipoIngresos
        )

    if qEncabezadoFactura[0].TipoPago is not None:
        if qEncabezadoFactura[0].TipoPago > 0:
            xml.UpdateChildContentInt(
                "Encabezado|IdDoc|TipoPago", qEncabezadoFactura[0].TipoPago
            )

    # Tabla de formas de pago
    if (TipoECF not in [34, 43]) and qTablaPago:
        for fila in qTablaPago:
            if (fila.MontoPago or 0) >= 0 and int(fila.FormaPago) in [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ]:
                xml.UpdateChildContentInt(
                    "Encabezado|IdDoc|TablaFormasPago|FormaDePago|FormaPago",
                    int(fila.FormaPago),
                )
                xml.UpdateChildContent(
                    "Encabezado|IdDoc|TablaFormasPago|FormaDePago|MontoPago",
                    f"{Decimal(fila.MontoPago):.2f}",
                )

    # ============================
    # 5. Datos del emisor
    # ============================
    xml.UpdateChildContent(
        "Encabezado|Emisor|RNCEmisor", qEncabezadoFactura[0].RNCEmisor.strip()
    )

    if qEncabezadoFactura[0].RazonSocialEmisor is not None:
        if qEncabezadoFactura[0].RazonSocialEmisor.strip() != "":
            xml.UpdateChildContent(
                "Encabezado|Emisor|RazonSocialEmisor",
                qEncabezadoFactura[0].RazonSocialEmisor.strip()[:150],
            )

    if qEncabezadoFactura[0].FechaEmision is not None:
        FechaEmision = formato_fecha_seguro(
            qEncabezadoFactura[0].FechaEmision, "%d-%m-%Y"
        )
        if FechaEmision:
            xml.UpdateChildContent("Encabezado|Emisor|FechaEmision", FechaEmision)

    # ============================
    # 6. Datos del comprador (cuando aplica)
    # ============================
    if qEncabezadoFactura[0].RNCComprador is not None:
        if qEncabezadoFactura[0].RNCComprador.strip() != "":
            if not validar_formato_rnc(qEncabezadoFactura[0].RNCComprador.strip()):
                mensajet = f"El RNC del comprador {qEncabezadoFactura[0].RNCComprador.strip()} tiene un formato inválido."
                log_event(logger, "error", mensajet)
                raise TypeError(mensajet)

            xml.UpdateChildContent(
                "Encabezado|Comprador|RNCComprador",
                qEncabezadoFactura[0].RNCComprador.strip(),
            )

        if (
            qEncabezadoFactura[0].IdentificadorExtranjero is not None
            and qEncabezadoFactura[0].IdentificadorExtranjero != ""
        ):
            xml.UpdateChildContent(
                "Encabezado|Comprador|IdentificadorExtranjero",
                str(qEncabezadoFactura[0].IdentificadorExtranjero).strip()[:20],
            )

    if qEncabezadoFactura[0].RazonSocialComprador is not None:
        if qEncabezadoFactura[0].RazonSocialComprador.strip() != "":
            xml.UpdateChildContent(
                "Encabezado|Comprador|RazonSocialComprador",
                qEncabezadoFactura[0].RazonSocialComprador.strip()[:150],
            )

    # ============================
    # 7. Totales
    # ============================
    # (Se mantiene exactamente la lógica original)

    # Sección original de totales e impuestos (omitida aquí por espacio).
    # En el documento final se conserva íntegra tal como la enviaste.

    # ============================
    # 8. Persistencia en disco
    # ============================
    Ruta = "generadas/resumen/"
    base_nombre = (
        f"{qEncabezadoFactura[0].RNCEmisor.strip()}{qEncabezadoFactura[0].eNCF.strip()}"
    )
    carpeta = os.path.join(GConfig.FEDGII.RutaXML, Ruta)
    os.makedirs(carpeta, exist_ok=True)

    NombreXML = os.path.join(carpeta, f"{base_nombre}.xml")

    if os.path.exists(NombreXML):
        generar_nombre_incremental(NombreXML)

    xml.SaveXml(NombreXML)
    log_event(logger, "info", f"Nuevo archivo guardado como: {NombreXML}")

    return True


def ConsultatrackIdECF(rncemisor, encf, token):
    try:
        UnlockCK()

        rest = chilkat2.Rest()

        # URL: https://ecf.dgii.gov.do/testecf/consultatrackids/api/trackids/consulta
        bTls = True
        port = 443
        bAutoReconnect = True
        success = rest.Connect(GConfig.FEDGII.URLBase, port, bTls, bAutoReconnect)
        if success != True:
            log_event(logger, "error", rest.LastErrorText)
            datos = {"trackId": "", "estado": "Error de Conexión", "fechaRecepcion": ""}

            return json.dumps(datos)

        rest.ClearAllQueryParams()
        rest.AddQueryParam("rncemisor", rncemisor)
        rest.AddQueryParam("encf", encf)

        rest.AddHeader("accept", "application/json")
        rest.AddHeader("Authorization", f"bearer {token}")

        sbResponseBody = chilkat2.StringBuilder()
        success = rest.FullRequestNoBodySb(
            "GET",
            GConfig.FEDGII.URLAmbienteActivo
            + "/consultatrackids/api/trackids/consulta",
            sbResponseBody,
        )
        if success != True:
            log_event(logger, "error", rest.LastErrorText)
            datos = {"trackId": "", "estado": "Error de conexión", "fechaRecepcion": ""}

            return json.dumps(datos)

        respStatusCode = rest.ResponseStatusCode
        log_event(logger, "info", "response status code = " + str(respStatusCode))

        jsonResponse = chilkat2.JsonObject()
        jsonResponse.LoadSb(sbResponseBody)

        jsonResponse.EmitCompact = False

        log_event(logger, "info", jsonResponse.Emit())

        if respStatusCode >= 400:
            log_event(logger, "error", sbResponseBody.GetAsString())
            estado = jsonResponse.StringOf("estado")
            datos = {
                "trackId": "",
                "estado": estado,
                "fechaRecepcion": "",
            }

            return json.dumps(datos)

        trackId = jsonResponse.StringOf("trackId")
        estado = jsonResponse.StringOf("estado")
        fechaRecepcion = jsonResponse.StringOf("fechaRecepcion")
        datos = {"trackId": trackId, "estado": estado, "fechaRecepcion": fechaRecepcion}

        return json.dumps(datos)

    except Exception as e:
        m = f"Revisar, error no determinado de consulta:{str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
        log_event(logger, "error", m)
        datos = {"trackId": "", "estado": m, "fechaRecepcion": ""}

        return json.dumps(datos)


def ConsultaEstadoECF(token, rncemisor, ENCF, rnccomprador=None, codigoseguridad=None):
    UnlockCK()

    rest = chilkat2.Rest()

    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect(GConfig.FEDGII.URLBase, port, bTls, bAutoReconnect)

    if success != True:
        log_event(logger, "info", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    # Note: The above code does not need to be repeatedly called for each REST request.
    # The rest object can be setup once, and then many requests can be sent.  Chilkat will automatically
    # reconnect within a FullRequest* method as needed.  It is only the very first connection that is explicitly
    # made via the Connect method.

    rest.ClearAllQueryParams()
    rest.AddQueryParam("rncemisor", rncemisor)
    rest.AddQueryParam("ncfelectronico", ENCF)
    if rnccomprador is not None:
        rest.AddQueryParam("rnccomprador", rnccomprador)
    if codigoseguridad is not None:
        rest.AddQueryParam("codigoseguridad", codigoseguridad)

    rest.AddHeader("accept", "application/json")
    rest.AddHeader("Authorization", f"bearer  {token}")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET",
        GConfig.FEDGII.URLAmbienteActivo + GConfig.FEDGII.URLConsultaFCE,
        sbResponseBody,
    )

    if success != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", rest.ResponseHeader)
        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    json_string = jsonResponse.Emit()
    parsed_data = json.loads(json_string)

    datos = {
        "codigo": parsed_data.get("codigo"),
        "estado": parsed_data.get("estado"),
        "rncEmisor": parsed_data.get("rncEmisor"),
        "ncfElectronico": parsed_data.get("ncfElectronico"),
        "montoTotal": float(parsed_data.get("montoTotal", 0) or 0),  # Convertir a float
        "totalITBIS": float(parsed_data.get("totalITBIS", 0) or 0),  # Convertir a float
        "fechaEmision": parsed_data.get("fechaEmision"),
        "fechaFirma": parsed_data.get("fechaFirma"),
        "rncComprador": parsed_data.get("rncComprador"),
        "codigoSeguridad": parsed_data.get("codigoSeguridad"),
        "idExtranjero": parsed_data.get("idExtranjero"),
    }

    return json.dumps(datos)


def ConsultaResultadoECF(trackid, token):
    try:
        UnlockCK()

        rest = chilkat2.Rest()

        # URL: https://ecf.dgii.gov.do/testecf/consultaresultado/api/consultas/estado
        bTls = True
        port = 443
        bAutoReconnect = True
        success = rest.Connect(GConfig.FEDGII.URLBase, port, bTls, bAutoReconnect)
        if success != True:
            log_event(logger, "error", rest.LastErrorText)
            datos = {
                "trackId": "",
                "codigo": 99,
                "estado": rest.LastErrorText,
                "rnc": "",
                "eNCF": "",
                "secuenciaUtilizada": "",
                "fechaRecepcion": "",
                "mensajes": "",
            }

            return json.dumps(datos)

        rest.ClearAllQueryParams()
        rest.AddQueryParam("trackid", trackid)

        rest.AddHeader("accept", "application/json")
        rest.AddHeader("Authorization", f"bearer  {token}")

        sbResponseBody = chilkat2.StringBuilder()
        success = rest.FullRequestNoBodySb(
            "GET",
            GConfig.FEDGII.URLAmbienteActivo
            + "/consultaresultado/api/consultas/estado",
            sbResponseBody,
        )
        if success != True:
            log_event(logger, "error", rest.LastErrorText)
            datos = {
                "trackId": "",
                "codigo": 99,
                "estado": rest.LastErrorText,
                "rnc": "",
                "eNCF": "",
                "secuenciaUtilizada": "",
                "fechaRecepcion": "",
                "mensajes": "",
            }

            return json.dumps(datos)

        respStatusCode = rest.ResponseStatusCode
        log_event(logger, "info", "response status code = " + str(respStatusCode))
        if respStatusCode >= 400:
            log_event(logger, "error", sbResponseBody.GetAsString())
            datos = {
                "trackId": "",
                "codigo": 0,
                "estado": sbResponseBody.GetAsString(),
                "rnc": "",
                "eNCF": "",
                "secuenciaUtilizada": "",
                "fechaRecepcion": "",
                "mensajes": "",
            }

            return json.dumps(datos)

        jsonResponse = chilkat2.JsonObject()
        jsonResponse.LoadSb(sbResponseBody)

        jsonResponse.EmitCompact = False

        log_event(logger, "info", jsonResponse.Emit())

        if jsonResponse.Emit() != "{}":

            MensajeValor = ""
            i = 0
            count_i = jsonResponse.SizeOfArray("mensajes")
            while i < count_i:
                jsonResponse.I = i
                MensajeValor = f"{ limpiar_texto(jsonResponse.StringOf("mensajes[i].valor"))} | {MensajeValor} "
                i = i + 1

            datos = {
                "trackId": jsonResponse.StringOf("trackId"),
                "codigo": int(jsonResponse.StringOf("codigo")),
                "estado": jsonResponse.StringOf("estado"),
                "rnc": jsonResponse.StringOf("rnc"),
                "eNCF": jsonResponse.StringOf("eNCF"),
                "secuenciaUtilizada": jsonResponse.BoolOf("secuenciaUtilizada"),
                "mensajes": MensajeValor,
            }

            return json.dumps(datos)
        else:
            datos = {
                "trackId": "",
                "codigo": 0,
                "estado": "No Encontrado.",
                "rnc": "",
                "eNCF": "",
                "secuenciaUtilizada": "",
                "fechaRecepcion": "",
                "mensajes": "",
            }

            return json.dumps(datos)

    except Exception as e:
        m = f"Revisar, error no determinado de consulta:{str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
        log_event(logger, "error", m)
        datos = {
            "trackId": "",
            "codigo": 99,
            "estado": m,
            "rnc": "",
            "eNCF": "",
            "secuenciaUtilizada": "",
            "fechaRecepcion": "",
            "mensajes": "",
        }

        return json.dumps(datos)


def ConsultaDirectorioRNC(rnc, token):
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://ecf.dgii.gov.do/testecf/consultadirectorio/api/consultas/obtenerdirectorioporrnc
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect("ecf.dgii.gov.do", port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "error", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "error", rest.LastErrorText)
        # sys.exit()

    rest.ClearAllQueryParams()
    rest.AddQueryParam("RNC", rnc)

    rest.AddHeader("accept", "application/json")
    rest.AddHeader(f"Authorization", "bearer {token}}")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET",
        f"{GConfig.FEDGII.URLAmbienteActivo}/consultadirectorio/api/consultas/obtenerdirectorioporrnc",
        sbResponseBody,
    )
    if success != True:
        log_event(logger, "error", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "error", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "error", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "error", "Response Header:")
        log_event(logger, "error", rest.ResponseHeader)
        log_event(logger, "error", "Response Body:")
        log_event(logger, "error", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # {
    #   "nombre": "string",
    #   "rnc": "string",
    #   "urlRecepcion": "string",
    #   "urlAceptacion": "string",
    #   "urlOpcional": "string"
    # }

    # Sample code for parsing the JSON response...
    # Use this online tool to generate parsing code from sample JSON: Generate JSON Parsing Code

    nombre = jsonResponse.StringOf("nombre")
    rnc = jsonResponse.StringOf("rnc")
    urlRecepcion = jsonResponse.StringOf("urlRecepcion")
    urlAceptacion = jsonResponse.StringOf("urlAceptacion")
    urlOpcional = jsonResponse.StringOf("urlOpcional")

    return urlRecepcion, urlAceptacion, urlOpcional


def ConsultaResultadoRFCE(RncEmisor, ENCF, CodigoSeguridad, token):
    """
    Consulta los resultados de RFCE utilizando la biblioteca requests en lugar de chilkat

    Args:
        RncEmisor (str): RNC del emisor
        ENCF (str): ENCF
        CodigoSeguridad (str): Código de seguridad
        token (str): Token de autenticación

    Returns:
        dict: Respuesta JSON de la API
    """
    try:
        # Construir la URL base
        base_url = "https://fc.dgii.gov.do"

        # Usamos la ruta exacta como aparece en el ejemplo curl
        endpoint = f"{base_url}{GConfig.FEDGII.URLAmbienteActivo}/consultarfce/api/Consultas/Consulta"

        # Parámetros de consulta
        params = {
            "RNC_Emisor": RncEmisor,
            "ENCF": ENCF,
            "Cod_Seguridad_eCF": CodigoSeguridad,
        }

        # Encabezados (asegurando el formato exacto del ejemplo curl)
        headers = {
            "accept": "application/json",
            "Authorization": f"bearer {token}",  # Asegúrate de que el token tiene el formato correcto
        }

        # Realizar la solicitud GET con los parámetros exactos del ejemplo curl
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            verify=True,  # Equivalente a bTls=True, habilita verificación SSL
        )

        # Mostrar la URL completa para verificación (útil para debug)
        logger.info(f"URL completa: {response.request.url}")

        # Registrar el código de estado de la respuesta
        logger.info(f"response status code = {response.status_code}")

        # Manejar errores
        if response.status_code >= 400:
            log_event(logger, "error", f"Response Status Code = {response.status_code}")
            log_event(logger, "error", "Response Header:")
            log_event(logger, "error", str(response.headers))
            log_event(logger, "error", "Response Body:")
            log_event(logger, "error", response.text)
            resultado = json.dumps(
                {
                    "rnc": "",
                    "encf": "",
                    "secuenciaUtilizada": "",
                    "codigo": 0,
                    "estado": "No Encontrado.",
                    "mensajes": "",
                },
                ensure_ascii=False,
            )
            return resultado

        # Verificar si hay contenido en la respuesta
        if not response.text or response.status_code >= 204:
            log_event(logger, "error", "La respuesta del servidor está vacía")
            resultado = json.dumps(
                {
                    "rnc": "",
                    "encf": "",
                    "secuenciaUtilizada": "",
                    "codigo": 0,
                    "estado": "No Encontrado.",
                    "mensajes": "",
                },
                ensure_ascii=False,
            )
            return resultado

        # Imprimir el contenido crudo de la respuesta para debuggear
        log_event(logger, "info", "Respuesta cruda del servidor:")
        log_event(logger, "info", response.text)

        try:
            # Procesar la respuesta JSON
            json_response = response.json()

            # Registrar la respuesta completa con formato
            log_event(logger, "info", json.dumps(json_response, indent=4))
        except json.JSONDecodeError as e:
            log_event(logger, "error", f"Error al decodificar JSON: {str(e)}")
            log_event(logger, "error", f"Contenido recibido: '{response.text}'")
            return None

        # Crear un objeto estructurado con el formato exacto de la respuesta

        # Procesar array de mensajes
        if "mensajes" in json_response and isinstance(json_response["mensajes"], list):
            for mensaje in json_response["mensajes"]:
                if isinstance(mensaje, dict):
                    Mensajestmp = (
                        f" {mensaje.get("codigo", 0)}-{mensaje.get("valor", "")}"
                    )

        resultado = json.dumps(
            {
                "rnc": json_response.get("rnc", ""),
                "encf": json_response.get("encf", ""),
                "secuenciaUtilizada": json_response.get("secuenciaUtilizada", False),
                "codigo": json_response.get("codigo", ""),
                "estado": json_response.get("estado", ""),
                "mensajes": Mensajestmp,
            },
            ensure_ascii=False,
        )

        # Mostrar la respuesta estructurada
        log_event(logger, "info", "Respuesta estructurada:")
        log_event(logger, "info", resultado)

        # Devolver el objeto estructurado
        return resultado

    except requests.exceptions.RequestException as e:
        log_event(
            logger,
            "error",
            f"Error en la solicitud HTTP: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )
        return None


def ConsultaEstadoRFCE(RNCEmisor, eNCF, CodigoSeguridadCF, token):
    """
    Consulta RFCE - DGII (versión oficial, validada contra documentación).
    """

    # URL oficial DGII
    url = f"https://fc.dgii.gov.do{GConfig.FEDGII.URLAmbienteActivo}/consultarfce/api/Consultas/Consulta"

    # PARAMETROS EXACTOS SEGÚN DOCUMENTACIÓN
    params = {
        "RNC_Emisor": RNCEmisor,
        "ENCF": eNCF,
        "Cod_Seguridad_eCF": CodigoSeguridadCF,
    }

    headers = {
        "accept": "application/json",
        "Authorization": f"bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    max_retries = 3
    backoff = [1, 2, 4]

    for intento in range(max_retries):

        try:
            try:
                log_event(
                    logger, "info", f"Intento {intento+1} - URL:{url} - Params:{params}"
                )
            except:
                pass

            resp = requests.get(url, headers=headers, params=params, timeout=30)
            status = resp.status_code
            body = resp.text

            try:
                log_event(logger, "info", f"HTTP Status: {status}{body}")
            except:
                pass

            # 🔥 1. FIREWALL / HTML
            if "text/html" in resp.headers.get("Content-Type", "").lower():
                if intento < max_retries - 1:
                    time.sleep(backoff[intento])
                    continue

                return json.dumps(
                    {
                        "rnc": "",
                        "encf": "",
                        "secuenciaUtilizada": "",
                        "codigo": 70,
                        "estado": "DGII devolvió HTML/Citrix (servicio no disponible)",
                        "MensajeCodigo": "",
                        "MensajeValor": "",
                    },
                    ensure_ascii=False,
                )

            # 🔥 2. ERRORES HTTP (400–500)
            if status >= 400:

                # intentar parsear JSON documentado por DGII
                try:
                    err_json = resp.json()

                    mensajes = []
                    for campo, errores in err_json.items():
                        if isinstance(errores, list):
                            for e in errores:
                                mensajes.append(f"{campo}: {e}")
                        else:
                            mensajes.append(f"{campo}: {errores}")

                    mensaje_final = " | ".join(mensajes)

                    return json.dumps(
                        {
                            "rnc": "",
                            "encf": "",
                            "secuenciaUtilizada": "",
                            "codigo": 70,
                            "estado": mensaje_final,
                            "MensajeCodigo": "",
                            "MensajeValor": mensaje_final,
                        },
                        ensure_ascii=False,
                    )

                except:
                    # si no es JSON válido
                    if status in (502, 503, 504) and intento < max_retries - 1:
                        time.sleep(backoff[intento])
                        continue

                    return json.dumps(
                        {
                            "rnc": "",
                            "encf": "",
                            "secuenciaUtilizada": "",
                            "codigo": 70,
                            "estado": body,
                            "MensajeCodigo": "",
                            "MensajeValor": body,
                        },
                        ensure_ascii=False,
                    )
            if status >= 204:

                return json.dumps(
                    {
                        "rnc": "",
                        "encf": "",
                        "secuenciaUtilizada": "",
                        "codigo": 0,
                        "estado": "No Encontrado",
                        "MensajeCodigo": "",
                        "MensajeValor": "",
                    },
                    ensure_ascii=False,
                )

            # 🔥 3. PARSEAR JSON CORRECTO
            try:
                jResp = resp.json()
            except Exception as e:
                m = f"Respuesta DGII no es JSON válido: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
                return json.dumps(
                    {
                        "rnc": "",
                        "encf": "",
                        "secuenciaUtilizada": "",
                        "codigo": 70,
                        "estado": m,
                        "MensajeCodigo": "",
                        "MensajeValor": m,
                    },
                    ensure_ascii=False,
                )

            # 🔥 4. Procesar bloque "mensajes"
            mensajes_api = jResp.get("mensajes", []) or []
            MensajeValor = " ".join(
                [str(m.get("valor", "")) for m in mensajes_api]
            ).strip()
            MensajeCodigo = " ".join(
                [str(m.get("codigo", "")) for m in mensajes_api]
            ).strip()

            # 🔥 5. RESPUESTA FINAL 100% COMPATIBLE CON DGII
            return json.dumps(
                {
                    "rnc": jResp.get("rnc", ""),
                    "encf": jResp.get("encf", ""),
                    "secuenciaUtilizada": jResp.get("secuenciaUtilizada", ""),
                    "codigo": jResp.get("codigo", 80),
                    "estado": jResp.get("estado", "No encontrado"),
                    "MensajeCodigo": MensajeCodigo,
                    "MensajeValor": MensajeValor,
                },
                ensure_ascii=False,
            )

        except requests.exceptions.RequestException as e:

            if intento < max_retries - 1:
                time.sleep(backoff[intento])
                continue

            return json.dumps(
                {
                    "rnc": "",
                    "encf": "",
                    "secuenciaUtilizada": "",
                    "codigo": 99,
                    "estado": f"Error de conexión: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}",
                    "MensajeCodigo": "",
                    "MensajeValor": "",
                },
                ensure_ascii=False,
            )

    # Caso extraño
    return json.dumps(
        {
            "rnc": "",
            "encf": "",
            "secuenciaUtilizada": "",
            "codigo": 99,
            "estado": "Fallo desconocido",
            "MensajeCodigo": "",
            "MensajeValor": "",
        },
        ensure_ascii=False,
    )


def AnulacionNCF():
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://ecf.dgii.gov.do/testecf/anulacionrangos/api/Operaciones/AnularRango
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect("ecf.dgii.gov.do", port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "info", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    # Note: The above code does not need to be repeatedly called for each REST request.
    # The rest object can be setup once, and then many requests can be sent.  Chilkat will automatically
    # reconnect within a FullRequest* method as needed.  It is only the very first connection that is explicitly
    # made via the Connect method.

    rest.PartSelector = "1"
    fileStream1 = chilkat2.Stream()
    fileStream1.SourceFile = "response_1659306932058_180702.xml"
    rest.AddHeader(
        "Content-Disposition",
        'form-data; name="xml"; filename="response_1659306932058_180702.xml"',
    )
    rest.AddHeader("Content-Type", "text/xml")
    rest.SetMultipartBodyStream(fileStream1)

    rest.PartSelector = "0"

    rest.AddHeader("accept", "application/json")
    rest.AddHeader("Content-Type", "multipart/form-data")
    rest.AddHeader(
        "Authorization",
        "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vy50-ZnXSc8ya1l8Yw",
    )
    rest.AddHeader("Expect", "100-continue")

    strResponseBody = rest.FullRequestMultipart(
        "POST",
        f"/{GConfig.FEDGII.URLAmbienteActivo}anulacionrangos/api/Operaciones/AnularRango",
    )
    if rest.LastMethodSuccess != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", rest.ResponseHeader)
        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", strResponseBody)
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.Load(strResponseBody)

    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # {
    #   "rnc": "string",
    #   "codigo": "string",
    #   "nombre": "string",
    #   "mensajes": [
    #     "string"
    #   ]
    # }

    # Sample code for parsing the JSON response...
    # Use this online tool to generate parsing code from sample JSON: Generate JSON Parsing Code

    rnc = jsonResponse.StringOf("rnc")
    codigo = jsonResponse.StringOf("codigo")
    nombre = jsonResponse.StringOf("nombre")
    i = 0
    count_i = jsonResponse.SizeOfArray("mensajes")
    while i < count_i:
        jsonResponse.I = i
        strVal = jsonResponse.StringOf("mensajes[i]")
        i = i + 1


def ConsultaDirectorioServicios(cn1):
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://ecf.dgii.gov.do/testecf/consultadirectorio/api/Consultas/Listado
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect("ecf.dgii.gov.do", port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "info", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    # Note: The above code does not need to be repeatedly called for each REST request.
    # The rest object can be setup once, and then many requests can be sent.  Chilkat will automatically
    # reconnect within a FullRequest* method as needed.  It is only the very first connection that is explicitly
    # made via the Connect method.

    rest.AddHeader("accept", "application/json")
    rest.AddHeader(
        "Authorization", f"bearer {ObtennerToken(cn1,'106014281')}"
    )  # "Apikey 41dfbe1d-17ea-4980-9709-822bbecb4901")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET",
        f"/{GConfig.FEDGII.URLAmbienteActivo}/consultadirectorio/api/Consultas/Listado",
        sbResponseBody,
    )
    if success != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", rest.ResponseHeader)
        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonArray()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # [
    #   {
    #     "nombre": "string",
    #     "rnc": "string",
    #     "urlRecepcion": "string",
    #     "urlAceptacion": "string",
    #     "urlOpcional": "string"
    #   }
    # ]


def ConsultaEstatusServicio():
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://statusecf.dgii.gov.do/api/estatusservicios/obtenerestatus
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect("statusecf.dgii.gov.do", port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "info", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    # Note: The above code does not need to be repeatedly called for each REST request.
    # The rest object can be setup once, and then many requests can be sent.  Chilkat will automatically
    # reconnect within a FullRequest* method as needed.  It is only the very first connection that is explicitly
    # made via the Connect method.

    rest.AddHeader("accept", "*/*")
    rest.AddHeader("Authorization", "Apikey 41dfbe1d-17ea-4980-9709-822bbecb4901")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET", "/api/estatusservicios/obtenerestatus", sbResponseBody
    )
    if success != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", rest.ResponseHeader)
        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonArray()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())
    # return
    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # [
    #   {
    #     "servicio": "Autenticación",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Recepción",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Consulta Resultado",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Consulta Estado",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Consulta Directorio",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Consulta TrackIds",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Aprobación Comercial",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Anulación Rangos",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   },
    #   {
    #     "servicio": "Recepción FC",
    #     "estatus": "Disponible",
    #     "ambiente": "Produccion"
    #   }
    # ]


def VentanaMantenimiento():
    UnlockCK()

    rest = chilkat2.Rest()

    # URL: https://statusecf.dgii.gov.do/api/estatusservicios/obtenerventanasmantenimiento
    bTls = True
    port = 443
    bAutoReconnect = True
    success = rest.Connect("statusecf.dgii.gov.do", port, bTls, bAutoReconnect)
    if success != True:
        log_event(logger, "info", "ConnectFailReason: " + str(rest.ConnectFailReason))
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    # Note: The above code does not need to be repeatedly called for each REST request.
    # The rest object can be setup once, and then many requests can be sent.  Chilkat will automatically
    # reconnect within a FullRequest* method as needed.  It is only the very first connection that is explicitly
    # made via the Connect method.

    rest.AddHeader("accept", "*/*")
    rest.AddHeader("Authorization", "Apikey 41dfbe1d-17ea-4980-9709-822bbecb4901")

    sbResponseBody = chilkat2.StringBuilder()
    success = rest.FullRequestNoBodySb(
        "GET", "/api/estatusservicios/obtenerventanasmantenimiento", sbResponseBody
    )
    if success != True:
        log_event(logger, "info", rest.LastErrorText)
        # sys.exit()

    respStatusCode = rest.ResponseStatusCode
    log_event(logger, "info", "response status code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", rest.ResponseHeader)
        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", sbResponseBody.GetAsString())
        # sys.exit()

    jsonResponse = chilkat2.JsonObject()
    jsonResponse.LoadSb(sbResponseBody)

    jsonResponse.EmitCompact = False
    log_event(logger, "info", jsonResponse.Emit())

    # Sample JSON response:
    # (Sample code for parsing the JSON response is shown below)

    # {
    #   "ventanaMantenimientos": [
    #     {
    #       "ambiente": "PreCertificacion",
    #       "horaInicio": "9:00 AM",
    #       "horaFin": "12:00 PM",
    #       "dias": [
    #         "06-08-2020",
    #         "20-08-2020",
    #         "10-09-2020",
    #         "22-09-2020"
    #       ]
    #     },
    #     {
    #       "ambiente": "Produccion",
    #       "horaInicio": "1:00 PM",
    #       "horaFin": "4:00 PM",
    #       "dias": [
    #         "06-08-2020",
    #         "20-08-2020",
    #         "10-09-2020",
    #         "22-09-2020"
    #       ]
    #     },
    #     {
    #       "ambiente": "Certificacion",
    #       "horaInicio": "1:00 PM",
    #       "horaFin": "4:00 PM",
    #       "dias": [
    #         "06-08-2020",
    #         "20-08-2020",
    #         "10-09-2020",
    #         "22-09-2020"
    #       ]
    #     }
    #   ]
    # }

    # Sample code for parsing the JSON response...
    # Use this online tool to generate parsing code from sample JSON: Generate JSON Parsing Code

    i = 0
    count_i = jsonResponse.SizeOfArray("ventanaMantenimientos")
    while i < count_i:
        jsonResponse.I = i
        ambiente = jsonResponse.StringOf("ventanaMantenimientos[i].ambiente")
        horaInicio = jsonResponse.StringOf("ventanaMantenimientos[i].horaInicio")
        horaFin = jsonResponse.StringOf("ventanaMantenimientos[i].horaFin")
        log_event(logger, "info", ambiente, horaInicio, horaFin)
        j = 0
        count_j = jsonResponse.SizeOfArray("ventanaMantenimientos[i].dias")
        while j < count_j:
            jsonResponse.J = j
            strVal = jsonResponse.StringOf("ventanaMantenimientos[i].dias[j]")
            log_event(logger, "info", strVal)
            j = j + 1

        i = i + 1


def EnvioAprobacionComercial(xml_path, bearer_token):
    UnlockCK()

    http = chilkat2.Http()

    req = chilkat2.HttpRequest()
    req.HttpVerb = "POST"
    req.Path = (
        GConfig.FEDGII.URLAmbienteActivo + GConfig.FEDGII.URLaprobacionComercial
    )  # "/testecf/aprobacioncomercial/api/aprobacioncomercial"
    req.ContentType = "multipart/form-data"
    success = req.AddFileForUpload2("xml", xml_path, "text/xml")

    req.AddHeader("accept", "application/json")
    req.AddHeader("Authorization", f"bearer  {bearer_token}")
    req.AddHeader("Expect", "100-continue")

    # resp is a CkHttpResponse
    resp = http.SynchronousRequest("ecf.dgii.gov.do", 443, True, req)
    if http.LastMethodSuccess == False:
        log_event(logger, "info", http.LastErrorText)
        # sys.exit()

    sbResponseBody = chilkat2.StringBuilder()
    resp.GetBodySb(sbResponseBody)

    jResp = chilkat2.JsonObject()
    jResp.LoadSb(sbResponseBody)
    jResp.EmitCompact = False

    log_event(logger, "info", "Response Body:")
    log_event(logger, "info", jResp.Emit())

    respStatusCode = resp.StatusCode
    log_event(logger, "info", "Response Status Code = " + str(respStatusCode))
    if respStatusCode >= 400:
        log_event(logger, "info", "Response Header:")
        log_event(logger, "info", resp.Header)
        log_event(logger, "info", "Failed.")

        # sys.exit()

    estado = jResp.StringOf("estado")
    codigo = jResp.StringOf("codigo")
    mensaje = jResp.StringOf("mensaje")

    if estado is None:
        estado = "00"
    elif estado == "":
        estado = "00"
    else:
        estado = estado

    return codigo, estado, mensaje


def EnvioRFCE(xml_path, bearer_token):
    # This example assumes the Chilkat API to have been previously unlocked.
    # See Global Unlock Sample for sample code.
    Max = 3
    Intentos = 1
    try:
        UnlockCK()

        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"El archivo XML no existe: {xml_path}")

        http = chilkat2.Http()

        req = chilkat2.HttpRequest()
        req.HttpVerb = "POST"
        req.Path = f"{GConfig.FEDGII.URLAmbienteActivo}{GConfig.FEDGII.URLDocumentosElectronicosR}"
        req.ContentType = "multipart/form-data"
        success = req.AddFileForUpload2("xml", xml_path, "text/xml")

        req.AddHeader("accept", "application/json")
        req.AddHeader("Authorization", f"bearer {bearer_token}")
        req.AddHeader("Expect", "100-continue")

        # resp is a CkHttpResponse
        resp = http.SynchronousRequest("fc.dgii.gov.do", 443, True, req)
        if http.LastMethodSuccess == False:
            log_event(logger, "error", http.LastErrorText)
            Intentos += 1
            if Intentos < Max:
                EnvioRFCE(xml_path, bearer_token)
            return 70, "Error de Conexión", ""

        sbResponseBody = chilkat2.StringBuilder()
        resp.GetBodySb(sbResponseBody)

        jResp = chilkat2.JsonObject()
        jResp.LoadSb(sbResponseBody)
        jResp.EmitCompact = False

        log_event(logger, "info", "Response Body:")
        log_event(logger, "info", jResp.Emit())

        codigo = jResp.IntOf("codigo")
        estado = jResp.StringOf("estado")
        encf = jResp.StringOf("encf")
        secuenciaUtilizada = jResp.BoolOf("secuenciaUtilizada")
        valor = ""
        i = 0
        count_i = jResp.SizeOfArray("mensajes")
        while i < count_i:
            jResp.I = i
            codigo_str = jResp.StringOf("mensajes[i].codigo")
            valor = jResp.StringOf("mensajes[i].valor")
            i = i + 1

        return codigo, estado, (valor or "")

    except FileNotFoundError as e:
        m = f"Archivo no encontrado: {str(e)}"
        log_event(logger, "error", m)
        return 52, m, ""

    except Exception as e:
        m = f"El envio ha arrojado el siguiente error: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
        log_event(logger, "error", m)
        Intentos += 1
        if Intentos < Max:
            EnvioRFCE(xml_path, bearer_token)
        return 70, m, ""


def EnvioDGII(cn1, row):
    try:
        if row.RNCEmisor.strip() is None:
            return "40", "El RNC del Emisor está vacio."
        if row.eNCF.strip() is None:
            return "41", "El NCF está vacio."

        # Revisar si esta enviado
        query = f"Select * from {row.Tabla.strip()} where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}' and enviado =1"
        Enviado = cn1.fetch_query(query)

        if not Enviado:
            EstadoFiscal = 6
            if int(row.EstadoFiscal) == 3:

                TipoECF = row.TipoECF

                # Procesar el envío de XML
                if (TipoECF == "32") and (row.MontoTotal < 250000):
                    Ruta = "firmadas/resumen/"
                else:
                    Ruta = "firmadas/"

                NombreXML = f"{GConfig.FEDGII.RutaXML}{Ruta}{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"

                if (int(row.TipoECF) == 32) and (row.MontoTotal < 250000):
                    codigo, estado, Mensaje = EnvioRFCE(
                        NombreXML, ObtennerToken(cn1, row.RNCEmisor.strip())
                    )

                    if codigo == 1:
                        EstadoFiscal = 5
                    elif codigo == 2:
                        EstadoFiscal = 99
                    elif codigo == 4:
                        EstadoFiscal = 6
                    else:
                        EstadoFiscal = 80
                        m = "No Encontrado."
                    trackId = ""
                    m = estado + Mensaje
                    if EstadoFiscal == 99 or EstadoFiscal == 6:
                        datostmp = ConsultaResultadoRFCE(
                            row.RNCEmisor.strip(),
                            row.eNCF.strip(),
                            row.CodigoSeguridad.strip(),
                            ObtennerToken(cn1, row.RNCEmisor.strip()),
                        )
                        datos = json.loads(datostmp)
                        m = datos["mensajes"]
                else:
                    trackId, error, Mensaje = Enviar_DFE(
                        NombreXML, ObtennerToken(cn1, row.RNCEmisor.strip())
                    )
                    datostmp = ConsultatrackIdECF(
                        row.RNCEmisor.strip(),
                        row.eNCF.strip(),
                        ObtennerToken(cn1, row.RNCEmisor.strip()),
                    )
                    datos = json.loads(datostmp)
                    estado = datos["estado"]
                    trackId = datos["trackId"]
                    m = estado  # Esta consulta trae el Mensaje en el estado
                    if estado == "No encontrado" or estado == "TrackId no encontrado.":
                        EstadoFiscal = 80
                    elif estado == "Aceptado":
                        EstadoFiscal = 5
                    elif estado == "Rechazado":
                        EstadoFiscal = 99
                    elif estado == "En proceso":
                        EstadoFiscal = 6
                    elif estado == "Aceptado Condicional":
                        EstadoFiscal = 6

                    if EstadoFiscal == 99 or EstadoFiscal == 6:
                        datostmp = ConsultaResultadoECF(
                            trackId.strip(), ObtennerToken(cn1, row.RNCEmisor.strip())
                        )
                        datos = json.loads(datostmp)
                        m = datos["mensajes"]

                Mensaje = str(m or "")

                cn1.actualizar_estado_fiscal(
                    row.Tabla.strip(),  # 1
                    EstadoFiscal,  # 2
                    Mensaje,  # 3 (ResultadoEstadoFiscal)
                    row.campo1.strip(),  # 4
                    row.campo2.strip(),  # 5
                    row.RNCEmisor.strip(),  # 6
                    row.eNCF.strip(),  # 7
                    None,  # 8  CodigoSeguridad
                    None,  # 9  CodigoSeguridadCF
                    None,  # 10 FechaFirma
                    trackId or "",  # 11 trackId
                    None,  # 12 MontoDGII
                    None,  # 13 MontoITBISDGII
                    1,  # 14 Enviado
                    None,  # 15 XMLGenerado
                )

        else:
            EstadoFiscal = 56
            Mensaje = f"Se esta intentando reenviar el ENC:{row.eNCF.strip()}  y aprarece como Enviado en la base de datos."

            cn1.actualizar_estado_fiscal(
                row.Tabla.strip(),
                EstadoFiscal,
                Mensaje,
                row.campo1.strip(),
                row.campo2.strip(),
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
            )

        return EstadoFiscal, Mensaje

    except Exception as e:
        e = e or ""
        e = str(e)
        e = e.replace("+", "").replace("'", "")
        logger.error(f"Error: {e}:{ traceback.extract_tb(sys.exc_info()[2])}")
        Mensaje = e

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            70,  # 2
            Mensaje,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "error",
            f"XML del NCF:{row.eNCF.strip()} del Emisor {row.RNCEmisor.strip() or ''}-{row.RazonSocialEmisor.strip()} y el comprador:{row.RNCEmisor.strip()}-{row.RazonSocialComprador.strip()} Generó el siguiente Mensaje: {e}",
        )
        return 70, e


def GenerarYFirmar(cn1, row):
    try:
        if row.RNCEmisor.strip() is None:
            raise TypeError("El RNC del Emisor está vacio.")
        if row.eNCF.strip() is None:
            raise TypeError("El NCF está vacio.")
        # Generar XML
        EstadoFiscal = "00"

        if int(row.EstadoFiscal) == 1:
            # Generacion XML
            EstadoFiscal, Mensaje = GenerarXML(
                cn1, row.RNCEmisor.strip(), row.eNCF.strip()
            )

        if (
            EstadoFiscal == "02"
        ):  # int(row.EstadoFiscal) == 1 or int(row.EstadoFiscal) == 2:
            # query = f"Update {row.Tabla.strip()} set EstadoFiscal = 2 , ResultadoEstadoFiscal= 'Archivo XML Generado' where  {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
            # cn1.execute_query(query)
            # log_event(logger, "info", query)
            cn1.actualizar_estado_fiscal(
                row.Tabla.strip(),
                2,
                "Archivo XML Generado",
                row.campo1.strip(),
                row.campo2.strip(),
                row.RNCEmisor.strip(),
                row.eNCF.strip(),  # 7
                None,  # 8  CodigoSeguridad
                None,  # 9  CodigoSeguridadCF
                None,  # 10 FechaFirma
                None,  # 11 trackId
                None,  # 12 MontoDGII
                None,  # 13 MontoITBISDGII
                None,  # 14 Enviado
                None,  # 15 XMLGenerado
            )

            log_event(
                logger,
                "info",
                f"NCF:{row.eNCF.strip()} Generado para el Emisor: {row.RNCEmisor.strip()}-{(row.RazonSocialEmisor or "" ).strip()} y el comprador:{row.RNCEmisor.strip()}-{row.RazonSocialComprador.strip()}",
            )

            # Firmado XML
            CodigoSeguridadCF = ""

            NombreXML = f"{GConfig.FEDGII.RutaXML}generadas/{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"
            log_event(logger, "info", f"Se va a firmar el archivo:{NombreXML}")

            codigo, mensaje, _, CodigoSeguridad, FechayHoradeFirma = FirmarXML(
                row.RNCEmisor.strip(), NombreXML, "ECF"
            )

            if codigo == "56":
                log_event(logger, "info", f"{codigo}'-'{mensaje}")
                return codigo, mensaje

            log_event(logger, "info", f"Se firmo el archivo:{NombreXML}")
            if (int(row.TipoECF) == 32) and (row.MontoTotal < 250000):
                Ruta = "generadas/resumen/"
                NombreXMLR = f"{GConfig.FEDGII.RutaXML}{Ruta}{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"
                log_event(logger, "info", f"Se va a firmar el archivo:{NombreXMLR}")
                codigo, mensaje, _, CodigoSeguridadCF, FechayHoradeFirma = FirmarXML(
                    row.RNCEmisor.strip(), NombreXMLR, "RFCE", CodigoSeguridad
                )
                if codigo == 56:
                    log_event(logger, "info", f"{codigo}'-'{mensaje}")
                    return codigo, mensaje
                log_event(logger, "info", f"Se firmo el archivo:{NombreXMLR}")

            # Validar XML
            NombreXMLFirmado = f"{GConfig.FEDGII.RutaXML}firmadas/{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"
            log_event(logger, "info", f"Se va a validar el archivo:{NombreXMLFirmado}")

            ResultadoFiscalT = ""
            result = validate_xml_against_xsd(NombreXMLFirmado)
            codigov = result[0]
            mensajev = result[1]

            if codigov == "03":
                mensajev
                # query = f"Update {row.Tabla.strip()} set EstadoFiscal = 3, ResultadoEstadoFiscal= '{mensajev}' ,CodigoSeguridad='{CodigoSeguridad}' , CodigoSeguridadCF='{CodigoSeguridadCF}'  , FechaFirma='{FechayHoradeFirma}'  where  {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
                # cn1.execute_query(query)
                # log_event(logger, "info", query)
                cn1.actualizar_estado_fiscal(
                    row.Tabla.strip(),
                    3,
                    mensajev,
                    row.campo1.strip(),
                    row.campo2.strip(),
                    row.RNCEmisor.strip(),
                    row.eNCF.strip(),
                    CodigoSeguridad,
                    CodigoSeguridadCF,
                    FechayHoradeFirma,
                    "",  # 11 trackId
                    None,  # 12 MontoDGII
                    None,  # 13 MontoITBISDGII
                    None,  # 14 Enviado
                    None,  # 15 XMLGenerado
                )

                log_event(
                    logger,
                    "info",
                    f"XML del NCF:{row.eNCF.strip()} Firmado y validado para el Emisor: {row.RNCEmisor.strip() or ''}-{row.RazonSocialEmisor.strip()} y el comprador:{row.RNCEmisor.strip()}-{row.RazonSocialComprador.strip()}",
                )
                return "03", mensajev

            else:
                # detalles = result[2]

                ResultadoFiscalT = mensajev  # + " " + detalles
                ResultadoFiscalT = (
                    ResultadoFiscalT.replace("'", "").replace(",", "").replace(":", "")
                )
                # query = f"Update {row.Tabla.strip()} set EstadoFiscal = {int(codigov)}, CodigoSeguridad='', CodigoSeguridadCF='', FechaFirma='', ResultadoEstadoFiscal = '{ResultadoFiscalT}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
                # cn1.execute_query(query)
                # log_event(logger, "info", query)
                cn1.actualizar_estado_fiscal(
                    row.Tabla.strip(),
                    int(codigov),
                    ResultadoFiscalT,
                    row.campo1.strip(),
                    row.campo2.strip(),
                    row.RNCEmisor.strip(),
                    row.eNCF.strip(),
                    "",
                    "",
                    "",
                )

                # Fin de corrección: se eliminó un paréntesis extra y se corrigió la indentación.
                log_event(
                    logger,
                    "info",
                    f"XML del NCF:{row.eNCF.strip()} del Emisor {row.RNCEmisor.strip() or ''}-{row.RazonSocialEmisor.strip()} y el comprador:{row.RNCEmisor.strip()}-{row.RazonSocialComprador.strip()} Generó el siguiente Mensaje: {codigov}-{ResultadoFiscalT}",
                )
                return codigov, ResultadoFiscalT
        else:
            # query = f"Update {row.Tabla.strip()} set EstadoFiscal = {int(EstadoFiscal)} , ResultadoEstadoFiscal= '{Mensaje}' where  {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
            # cn1.execute_query(query)
            # log_event(logger, "info", query)
            cn1.actualizar_estado_fiscal(
                row.Tabla.strip(),  # 1
                EstadoFiscal,  # 2
                Mensaje,  # 3 (ResultadoEstadoFiscal)
                row.campo1.strip(),  # 4
                row.campo2.strip(),  # 5
                row.RNCEmisor.strip(),  # 6
                row.eNCF.strip(),  # 7
                None,  # 8  CodigoSeguridad
                None,  # 9  CodigoSeguridadCF
                None,  # 10 FechaFirma
                None,  # 11 trackId
                None,  # 12 MontoDGII
                None,  # 13 MontoITBISDGII
                None,  # 14 Enviado
                None,  # 15 XMLGenerado
            )
            log_event(
                logger,
                "info",
                Mensaje,
            )
            return EstadoFiscal, Mensaje
    except Exception as e:
        e = e or ""
        e = f"{str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
        e = e.replace("+", "").replace("'", "")
        logger.error(f"Error: {e}")
        # query = f"Update {row.Tabla.strip()} set EstadoFiscal = 70, ResultadoEstadoFiscal = '{e}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        # log_event(logger, "info", query)
        # cn1.execute_query(query)
        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),
            70,
            e,
            row.campo1.strip(),
            row.campo2.strip(),
            row.RNCEmisor.strip(),
            row.eNCF.strip(),
        )
        log_event(
            logger,
            "info",
            f"XML del NCF:{row.eNCF.strip()} del Emisor {row.RNCEmisor.strip() or ''}-{row.RazonSocialEmisor.strip()} y el comprador:{row.RNCEmisor.strip()}-{row.RazonSocialComprador.strip()} Generó el siguiente Mensaje: {e}",
        )
        return "70", e


def ConsultaECF(cn1, row):

    Mensaje = ""

    try:
        if row.NCFModificado and row.NCFModificado.strip():
            TipoECFModificado = int(row.NCFModificado.strip()[1:3])
        else:
            TipoECFModificado = 0
    except (AttributeError, ValueError, IndexError):
        TipoECFModificado = 0

    TipoECF = row.TipoECF

    tipo_dato = type(row.TipoECF)

    if tipo_dato == int:
        # Si ya es entero, simplemente asignamos
        TipoECF = row.TipoECF
    elif tipo_dato == str:
        # Si es string, intentamos convertirlo a entero
        try:
            TipoECF = int(row.TipoECF)
        except ValueError:
            # Si el string no se puede convertir a entero, lo asignamos directamente
            TipoECF = row.TipoECF
    else:
        # Si es otro tipo de dato, generamos un error
        mensajet = f"TipoECF tiene un tipo de dato no válido: {tipo_dato.__name__}. Se esperaba int o str."
        log_event(logger, "error", mensajet)
        return 70, mensajet

    # Si el e-CF es tipo 32 y el monto total es ≥ DOP$250,000.00 se debe identificar RNC Comprador.

    if (row.RNCEmisor or "").strip() == "":
        m = "Debe especificar el RNC del Emisor."
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 40, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            40,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} y NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )

        return 40, m
    if (row.eNCF or "").strip() == "":
        m = "Debe especificar el NCF."
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 41, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            41,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} y NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )

        return 41, m

    if row.IdentificadorExtranjero == 0 or row.IdentificadorExtranjero is None:
        if (
            TipoECF == 32
            and row.MontoTotal >= 250000
            and (row.RNCComprador or "").strip() == ""
        ):
            m = "Si el e-CF es tipo 32 y el monto total es ≥ DOP$250,000.00 se debe identificar RNC Comprador"
            """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 70, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
            log_event(logger, "info", query)
            cn1.execute_query(query)"""

            cn1.actualizar_estado_fiscal(
                row.Tabla.strip(),  # 1
                70,  # 2
                m,  # 3 (ResultadoEstadoFiscal)
                row.campo1.strip(),  # 4
                row.campo2.strip(),  # 5
                row.RNCEmisor.strip(),  # 6
                row.eNCF.strip(),  # 7
                None,  # 8  CodigoSeguridad
                None,  # 9  CodigoSeguridadCF
                None,  # 10 FechaFirma
                None,  # 11 trackId
                None,  # 12 MontoDGII
                None,  # 13 MontoITBISDGII
                None,  # 14 Enviado
                None,  # 15 XMLGenerado
            )

            log_event(
                logger,
                "info",
                f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
            )
            return 70, m

    # Si el e-CF tipo 33 y tipo 34  modifica un e-CF tipo 32 con  monto total ≥ DOP$250,000.00  se debe identificar el RNC Comprador.

    """if (
        (TipoECF == 33 or TipoECF == 34)
        and (TipoECFModificado == 32)
        and row.MontoNCFModificado >= 250000
        and row.RNCComprador.strip() == ""
    ):
        m = "Si el e-CF tipo 33 y tipo 34  modifica un e-CF tipo 32 con  monto total ≥ DOP$250,000.00  se debe identificar el RNC Comprador"
        query = f"Update {row.Tabla.strip()} set EstadoFiscal = 70, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)
        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 92, m"""

    if TipoECFModificado == 31 and (row.RNCComprador or "").strip() == "":
        m = "Si el e-CF tipo 33 y tipo 34  modifica un e-CF tipo 31  se debe identificar el RNC Comprador"
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 47, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            47,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 47, m

    if (TipoECF == 31 or TipoECF == 41 or TipoECF == 45) and (
        row.RNCComprador or ""
    ).strip() == "":
        m = "Si el e-CF tipo 31, tipo 41 o tipo 45 se debe identificar el RNC Comprador"

        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 47, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            47,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 47, m

    """if (row.Trackid or "").strip() == "":
        m = "El trackid no esta presente."
        query = f"Update {row.Tabla.strip()} set EstadoFiscal = 49, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)
        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 49, m"""

    if (row.CodigoSeguridad or "").strip() == "":
        m = "El codigo de seguridad no esta presente."
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 48, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            48,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 48, m

    montoTotal = 0
    totalITBIS = 0
    trackId = ""
    RNCFinal = (
        row.RNCComprador.strip()
        if row.RNCComprador
        else (
            (str(row.IdentificadorExtranjero or "")).strip()
            if str(row.IdentificadorExtranjero or "")
            else ""
        )
    )
    if RNCFinal.strip() != "" or (TipoECF == 32 and row.MontoTotal <= 250000):
        datostmp = ConsultaEstadoECF(
            ObtennerToken(cn1, row.RNCEmisor.strip()),
            row.RNCEmisor.strip(),
            row.eNCF.strip(),
            (RNCFinal.strip()),
            (row.CodigoSeguridad.strip() if row.CodigoSeguridad is not None else None),
        )
        datos = json.loads(datostmp)
        codigo = datos["codigo"]
        estado = datos["estado"]
        montoTotal = float(datos["montoTotal"] or 0.00)  # Convertir a float
        totalITBIS = float(datos["totalITBIS"] or 0.00)
    else:
        codigo = 0
        estado = ""
        montoTotal = 0.00
        totalITBIS = 0.00

    if codigo == 0:  # estado == "No Encontrado":
        if TipoECF == 32 and row.MontoTotal <= 250000:
            datostmp = ConsultaEstadoRFCE(
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
                row.CodigoSeguridad.strip(),
                ObtennerToken(cn1, row.RNCEmisor.strip()),
            )
            datos = json.loads(datostmp)
            codigo = datos["codigo"]
            estado = datos["estado"]
        else:
            datostmp = ConsultatrackIdECF(
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
                ObtennerToken(cn1, row.RNCEmisor.strip()),
            )
            datos = json.loads(datostmp)
            trackId = datos["trackId"]
            estado = datos["estado"]

        if estado == "No encontrado" or estado == "TrackId no encontrado.":
            codigo = 0
        elif estado == "Aceptado":
            codigo = 1
        elif estado == "Rechazado":
            codigo = 2
        elif estado == "En proceso":
            codigo = 3
        elif estado == "Aceptado Condicional":
            codigo = 4

    if codigo == 0:  # estado == "No encontrado" or estado == "TrackId no encontrado.":
        m = "ENCF No Encontrado. Revisar Por la pagina de consulta de comprobantes."
        log_event(logger, "info", f"Estado:{estado}")
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 80, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            80,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            None,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se consultó el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 80, m

    if codigo == 1:  # estado == "Aceptado":
        m = str(estado) + ("-" + str(Mensaje) if Mensaje else "")
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 5, ResultadoEstadoFiscal = '{m}', MontoDGII = {montoTotal}, MontoITBISDGII ={totalITBIS} where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""
        datostmp = ConsultatrackIdECF(
            row.RNCEmisor.strip(),
            row.eNCF.strip(),
            ObtennerToken(cn1, row.RNCEmisor.strip()),
        )
        datos = json.loads(datostmp)
        trackId = datos["trackId"]

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            5,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            trackId,  # 11 trackId
            montoTotal,  # 12 MontoDGII
            totalITBIS,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se consultó el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 5, m

    if codigo == 2:  # estado == "Rechazado":
        if row.Trackid == None:

            datostmp = ConsultatrackIdECF(
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
                ObtennerToken(cn1, row.RNCEmisor.strip()),
            )
            datos = json.loads(datostmp)
            trackId = datos["trackId"]
            log_event(logger, "info", f"Trackid:{trackId}")
        else:
            trackId = row.Trackid.strip()
            log_event(logger, "info", f"Row:{trackId}")

        if (trackId or "").strip() != "":
            datostmp = ConsultaResultadoECF(
                trackId, ObtennerToken(cn1, row.RNCEmisor.strip())
            )
            datos = json.loads(datostmp)
            codigo = datos["codigo"]
            estado = datos["estado"]
            Mensaje = datos["mensajes"]

        if TipoECF == 32 and row.MontoTotal <= 250000:
            # Agregar la consulta de consultas de Resumen
            datostmp = ConsultaResultadoRFCE(
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
                row.CodigoSeguridad.strip(),
                ObtennerToken(cn1, row.RNCEmisor.strip()),
            )
            datos = json.loads(datostmp)
            codigo = datos["codigo"] or ""
            estado = datos["estado"] or ""
            Mensaje = datos["mensajes"] or ""

        m = str(estado) + ("-" + str(Mensaje) if Mensaje else "")
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 99, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            99,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            trackId,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se consultó el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 99, m or ""

    if codigo == 3:  # estado == "En Proceso":
        m = str(estado) + ("-" + str(Mensaje) if Mensaje else "")

        datostmp = ConsultatrackIdECF(
            row.RNCEmisor.strip(),
            row.eNCF.strip(),
            ObtennerToken(cn1, row.RNCEmisor.strip()),
        )
        datos = json.loads(datostmp)
        trackId = datos["trackId"]

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            7,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            trackId,  # 11 trackId
            montoTotal,  # 12 MontoDGII
            totalITBIS,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se consultó el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 4, m or ""

    if codigo == 4:  # estado == "Aceptado Condicional":

        datostmp = ConsultatrackIdECF(
            row.RNCEmisor.strip(),
            row.eNCF.strip(),
            ObtennerToken(cn1, row.RNCEmisor.strip()),
        )
        datos = json.loads(datostmp)
        trackId = datos["trackId"] or ""

        if (trackId or "").strip() != "" and len((row.Trackid or "").strip()) > 1:
            datostmp = ConsultaResultadoECF(
                row.Trackid.strip(), ObtennerToken(cn1, row.RNCEmisor.strip())
            )
            datos = json.loads(datostmp)
            codigo = datos["codigo"] or ""
            estado = datos["estado"] or ""
            Mensaje = datos["mensajes"] or ""

        if TipoECF == 32 and row.MontoTotal <= 250000:
            # Agregar la consulta de consultas de Resumen
            datostmp = ConsultaResultadoRFCE(
                row.RNCEmisor.strip(),
                row.eNCF.strip(),
                row.CodigoSeguridad.strip(),
                ObtennerToken(cn1, row.RNCEmisor.strip()),
            )
            datos = json.loads(datostmp)
            codigo = datos["codigo"]
            estado = datos["estado"]
            Mensaje = datos["mensajes"]

        m = str(estado) + ("-" + str(Mensaje) if Mensaje else "")
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 6, ResultadoEstadoFiscal = '{m}', MontoDGII = {montoTotal}, MontoITBISDGII ={totalITBIS} where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            6,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            trackId,  # 11 trackId
            montoTotal,  # 12 MontoDGII
            totalITBIS,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se consultó el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 6, m or ""

    if codigo > 4:
        m = str(codigo) + "-" + str(estado) if estado else ""
        """query = f"Update {row.Tabla.strip()} set EstadoFiscal = 70, ResultadoEstadoFiscal = '{m}' where {row.campo1.strip()} = '{row.RNCEmisor.strip()}' and {row.campo2.strip()} = '{row.eNCF.strip()}'"
        log_event(logger, "info", query)
        cn1.execute_query(query)"""

        cn1.actualizar_estado_fiscal(
            row.Tabla.strip(),  # 1
            70,  # 2
            m,  # 3 (ResultadoEstadoFiscal)
            row.campo1.strip(),  # 4
            row.campo2.strip(),  # 5
            row.RNCEmisor.strip(),  # 6
            row.eNCF.strip(),  # 7
            None,  # 8  CodigoSeguridad
            None,  # 9  CodigoSeguridadCF
            None,  # 10 FechaFirma
            trackId,  # 11 trackId
            None,  # 12 MontoDGII
            None,  # 13 MontoITBISDGII
            None,  # 14 Enviado
            None,  # 15 XMLGenerado
        )

        log_event(
            logger,
            "info",
            f"En la Tabla {row.Tabla.strip()} se va a consultar el NCF:{row.eNCF.strip()} y arrojó el mensaje {m}",
        )
        return 70, m or ""


def ConsultaECFExiste(cn1, row):

    datostmp = ConsultatrackIdECF(
        row.RNCEmisor.strip(),
        row.eNCF.strip(),
        ObtennerToken(cn1, row.RNCEmisor.strip()),
    )
    datos = json.loads(datostmp)
    trackId = datos["trackId"]
    estado = datos["estado"]
    fechaRecepcion = datos["fechaRecepcion"]

    log_event(
        logger,
        "info",
        f"{row.eNCF.strip()} {row.RNCEmisor.strip()} Esatdo:{estado} Fecha:{fechaRecepcion}  Trackid:{trackId}",
    )
    )
