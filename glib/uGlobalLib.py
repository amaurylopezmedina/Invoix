import inspect
import json
import logging
import os
import re
import time
import warnings
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from xml.dom import minidom
from xml.etree import ElementTree as ET

import requests
from lxml import etree

# Es buena práctica importar la excepción específica si se va a usar directamente.
from urllib3.exceptions import InsecureRequestWarning

# Funciones Propias
from config.uGlobalConfig import *
from db.uDB import *

from .log_g import log_event, setup_logger

logger = setup_logger("LogGeneral.log")


def generar_nombre_incremental(ruta_archivo):
    """
    Renombra el archivo existente agregando _1, _2, etc.
    SOLO si el archivo existe.
    """
    if not os.path.exists(ruta_archivo):
        return None

    base, ext = os.path.splitext(ruta_archivo)
    contador = 1

    while True:
        nuevo_nombre = f"{base}_{contador}{ext}"
        if not os.path.exists(nuevo_nombre):
            os.rename(ruta_archivo, nuevo_nombre)
            return nuevo_nombre
        contador += 1


def generar_nombre_unico(ruta_archivo):
    """
    Genera un nombre único para un nuevo archivo, agregando _1, _2, etc.
    si el nombre base ya existe.
    """
    if not os.path.exists(ruta_archivo):
        return ruta_archivo

    base, ext = os.path.splitext(ruta_archivo)
    contador = 1

    while True:
        nuevo_nombre = f"{base}_{contador}{ext}"
        if not os.path.exists(nuevo_nombre):
            return nuevo_nombre
        contador += 1


def validaurl(texto):
    # Expresión regular para URL (http, https, www)
    patron_url = re.compile(
        r"((http|https):\/\/)?"  # Protocolo opcional
        r"(www\.)?"  # "www." opcional
        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"  # Dominio
        r"(\:[0-9]{1,5})?"  # Puerto opcional
        r"(\/\S*)?"  # Ruta opcional
    )

    # Buscar en el texto
    coincidencia = patron_url.search(texto)

    # Verifica que no sea algo vacío y que cumpla formato
    return bool(coincidencia and coincidencia.group().strip())


def rellenaceros(valor, tamano=2):
    # Si el valor es un string, lo convertimos a entero
    if isinstance(valor, str):
        valor = int(valor)

    # Aplicamos el formato con ceros a la izquierda
    return f"{valor:0{tamano}}"


def validar_encf(value):
    """
    Valida un string según las especificaciones del tipo eNCFValidationType.

    Args:
        value (str): El string a validar

    Returns:
        tuple: (bool, str) - (Validado, Mensaje)
               - Validado: True si es válido, False si no
               - Mensaje: Mensaje de error (múltiples errores separados por .)
    """
    errors = []

    if not isinstance(value, str):
        errors.append("El valor debe ser un string")
        return False, ". ".join(errors)

    # Verificar longitud
    if len(value) != 13:
        errors.append(f"Longitud del eNCF incorrecta: {len(value)} (debe ser 13)")

    # Verificar caracteres válidos
    invalid_chars = [char for char in value if not char.isalnum()]
    if invalid_chars:
        errors.append(f"Caracteres inválidos encontrados en el eNCF: {invalid_chars}")

    # Si no hay errores, es válido
    if not errors:
        return True, "Válido"

    return False, ". ".join(errors)


def validar_formato_rnc(rnc):
    """
    Valida un RNC (Registro Nacional del Contribuyente) según el patrón XML especificado.

    Acepta:
    - 11 dígitos consecutivos
    - 9 dígitos consecutivos

    Args:
        rnc (str): El RNC a validar

    Returns:
        bool: True si el RNC es válido, False en caso contrario
    """
    if not isinstance(rnc, str):
        return False

    # Patrón que acepta exactamente 11 dígitos o exactamente 9 dígitos
    pattern = r"^([0-9]{11}|[0-9]{9})$"

    return bool(re.match(pattern, rnc))


def validar_rnc_DGII(rnc: str) -> bool:
    """
    Valida si un RNC existe consultando una API externa.

    Args:
        rnc: El número de RNC (como cadena de texto) a validar.

    Returns:
        True si el RNC existe según la API, False si no existe,
        o si ocurre un error durante la consulta.
    """
    api_url = "https://rnc.asesysfe.com:8077/rnc_data"
    params = {"rnc": rnc}

    # Es importante notar que 'verify=False' deshabilita la verificación del certificado SSL.
    # Esto puede ser un riesgo de seguridad en entornos de producción si el certificado
    # del servidor no es de confianza. Para producción, se recomienda usar certificados válidos.

    # Opción 1: Usar warnings.catch_warnings con la ruta correcta (como en tu código original)
    # with warnings.catch_warnings():
    #     warnings.simplefilter("ignore", InsecureRequestWarning) # Usamos la excepción importada
    #     try:
    #         response = requests.get(api_url, params=params, timeout=10, verify=False)
    #         # ... (resto del bloque try)
    #     except requests.exceptions.Timeout:
    #         # ... (resto de los bloques except)

    # Opción 2: Una forma más común y directa de suprimir esta advertencia específica de urllib3
    # es usar requests.urllib3.disable_warnings(). Esto se hace una vez.
    requests.urllib3.disable_warnings(InsecureRequestWarning)

    try:
        response = requests.get(api_url, params=params, timeout=10, verify=False)

        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            print(
                f"Respuesta inesperada de la API: Código {response.status_code} para RNC {rnc}"
            )
            return False
    except requests.exceptions.Timeout:
        print(f"Error: Timeout al intentar conectar con la API para el RNC {rnc}.")
        return False
    except requests.exceptions.ConnectionError:
        print(
            f"Error: No se pudo conectar con la API para el RNC {rnc}. "
            "Verifica tu conexión o la disponibilidad del servidor."
        )
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API para el RNC {rnc}: {e}")
        return False


def asegurar_fecha(fecha_input):
    if isinstance(fecha_input, date) and not isinstance(fecha_input, datetime):
        # Ya es un date (pero no datetime), lo devolvemos tal cual
        return fecha_input
    elif isinstance(fecha_input, datetime):
        # Si es datetime, extraemos la fecha
        return fecha_input.date()
    elif isinstance(fecha_input, str):
        # Intenta convertir desde varios formatos comunes
        formatos = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_input, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha no reconocido: {fecha_input}")
    else:
        raise TypeError(f"Tipo de dato no válido para fecha: {type(fecha_input)}")


class XMLSchemaValidator:
    """XML Schema validation handler"""

    def __init__(self, schema_path: str):
        try:
            self.schema = etree.XMLSchema(file=schema_path)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise

    def validate(
        self, xml_doc: Union[str, bytes, etree._Element]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate XML against schema
        Returns (is_valid, error_message)
        """
        try:
            if isinstance(xml_doc, str):
                # Remove encoding declaration
                xml_doc = re.sub(r"<\?xml.*\?>", "", xml_doc)
                xml_doc = xml_doc.encode("utf-8")
            elif isinstance(xml_doc, bytes):
                # Remove encoding declaration
                xml_doc = re.sub(rb"<\?xml.*\?>", b"", xml_doc)

            if isinstance(xml_doc, (str, bytes)):
                xml_doc = etree.fromstring(xml_doc)

            self.schema.assertValid(xml_doc)
            return True, None
        except etree.DocumentInvalid as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# Crear carpetas si no existen
def Crear_Directorios():
    # Directorios Generales
    if not os.path.exists(GConfig.CargaArchivo.directorio_Log):
        os.makedirs(GConfig.CargaArchivo.directorio_Log, exist_ok=True)

    # Directorios de Facturacion electonica
    if not os.path.exists(GConfig.FacturacionElectronica.RutaCertificado):
        os.makedirs(GConfig.FacturacionElectronica.RutaCertificado, exist_ok=True)

    if not os.path.exists(GConfig.FacturacionElectronica.RutaFactura):
        os.makedirs(GConfig.FacturacionElectronica.RutaFactura, exist_ok=True)

    if not os.path.exists(GConfig.FacturacionElectronica.RutaToken):
        os.makedirs(GConfig.FacturacionElectronica.RutaToken, exist_ok=True)

    if not os.path.exists(GConfig.FacturacionElectronica.RutaSemilla):
        os.makedirs(GConfig.FacturacionElectronica.RutaSemilla, exist_ok=True)

    if not os.path.exists(GConfig.FacturacionElectronica.RutaSemilla):
        os.makedirs(
            GConfig.FacturacionElectronica.RutaSemilla + "/generadas", exist_ok=True
        )

    if not os.path.exists(GConfig.FacturacionElectronica.RutaSemilla):
        os.makedirs(
            GConfig.FacturacionElectronica.RutaSemilla + "/firmadas", exist_ok=True
        )

    # Directorios de Revision y carga de archivos
    if not os.path.exists(GConfig.CargaArchivo.directorio_origen):
        os.makedirs(GConfig.CargaArchivo.directorio_origen, exist_ok=True)

    if not os.path.exists(GConfig.CargaArchivo.directorio_procesados):
        os.makedirs(GConfig.CargaArchivo.directorio_procesados, exist_ok=True)

    if not os.path.exists(GConfig.CargaArchivo.directorio_noprocesados):
        os.makedirs(GConfig.CargaArchivo.directorio_noprocesados, exist_ok=True)

    if not os.path.exists(GConfig.CargaArchivo.directorio_noaplica):
        os.makedirs(GConfig.CargaArchivo.directorio_noaplica, exist_ok=True)


def configurar_logging():
    fecha = time.strftime("%Y-%m-%d")
    logging.basicConfig(
        filename=GConfig.CargaArchivo.directorio_Log + "/" + f"Log_{fecha}.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Mapeo de columnas


def leer_mapeo():
    with open("datadef.json", "r") as f:
        return json.load(f)


def StrToInt(tipo_pago: str) -> int:
    # Si es None o está en blanco, devolver 0
    if tipo_pago is None or not str(tipo_pago).strip():
        return 0

    try:
        # Intenta convertir a entero
        return int(tipo_pago)
    except ValueError:
        # Si no se puede convertir, devolver 0
        return 0


def validar_telefono_rd(telefono):
    """
    Valida si un teléfono cumple el formato RD: 999-999-9999
    y tiene un prefijo válido de República Dominicana.

    Args:
        telefono (str): Teléfono a validar

    Returns:
        bool: True si es válido, False si no
    """
    if not telefono:
        return False

    patron = r"^(809|829|849)-\d{3}-\d{4}$"
    return bool(re.match(patron, telefono))


def verificar_email(email):
    patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(patron, email) is not None


def convertir_a_porcentaje(numero):
    try:
        # Primero convertimos a float para manejar decimales y strings
        valor = float(str(numero).replace(",", "."))
        # Convertimos a entero
        porcentaje = int(valor)
        return str(porcentaje)
    except (ValueError, TypeError):
        return "0"


def limpiar_texto(texto):
    """
    Limpia un texto eliminando saltos de línea, espacios extras y comillas.

    Args:
        texto (str): El texto a limpiar

    Returns:
        str: Texto limpio sin saltos de línea, espacios extras ni comillas
    """
    # Primero eliminamos las comillas
    texto_sin_comillas = texto.replace('"', "").replace("'", "")

    # Luego limpiamos espacios y saltos de línea
    return " ".join(texto_sin_comillas.split())


def obtener_valor_connstring(Ustring: str, clave: str) -> str:
    """
    Extrae el valor de una clave dentro de un connection string separado por ';'.

    Args:
        conn_string (str): Cadena de conexión completa.
        clave (str): Nombre de la clave a buscar (ej: SERVER, DATABASE, UID, PWD).

    Returns:
        str: Valor asociado a la clave o None si no existe.
    """
    partes = Ustring.split(";")
    clave = clave.upper().strip()

    for parte in partes:
        if "=" in parte:
            k, v = parte.split("=", 1)
            if k.strip().upper() == clave:
                return v.strip()

    return None


def mostrarConfiguracion(GConfig1, cn1, archivo=None):
    # fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(archivo))

    # log_event(logger, "info", f"Archivo ejecutándose: {archivo}")
    # log_event(logger, "info", f"Fecha de modificación: {fecha_modificacion}")

    log_event(logger, "info", "Configuraciones de Base de datos:")
    log_event(
        logger,
        "info",
        f"Servidor:{obtener_valor_connstring(cn1._load_connection_string(), "SERVER")}",
    )
    log_event(
        logger,
        "info",
        f"Base de Datos:{obtener_valor_connstring(cn1._load_connection_string(), "DATABASE")}",
    )
    log_event(
        logger,
        "info",
        f"Usuario:{obtener_valor_connstring(cn1._load_connection_string(), "UID")}",
    )

    log_event(logger, "info", "Configuraciones ambiente de Facturación Electrónica:")
    query = "SELECT top 1 * FROM FE_Empresas"
    qFEConfig = cn1.fetch_query(query)
    ADGII = {0: "Prueba", 1: "Certificación", 2: "Productivo"}.get(
        GConfig1.FEDGII.Ambiente, ""
    )
    log_event(logger, "info", f"Ambiente de Envio A DGII:{ADGII}")
    log_event(logger, "info", f"FE Estado:{qFEConfig[0].fe or ''}")
    ADB = {0: "Prueba", 1: "Certificación", 2: "Productivo"}.get(
        qFEConfig[0].Ambiente, ""
    )
    log_event(logger, "info", f"Ambiente en la DB: {ADB}")


def renombrar_archivo_si_existe(ruta_archivo):
    """
    Verifica si un archivo existe y lo renombra con un número secuencial
    si ya existe otro archivo con el mismo nombre.
    """
    # Verificar si el archivo existe
    if os.path.exists(ruta_archivo):
        # Separar el directorio, nombre y extensión
        directorio = os.path.dirname(ruta_archivo)
        nombre_completo = os.path.basename(ruta_archivo)
        nombre, extension = os.path.splitext(nombre_completo)

        contador = 1
        nueva_ruta = ruta_archivo

        # Buscar un nombre disponible
        while os.path.exists(nueva_ruta):
            nuevo_nombre = f"{nombre}_{contador}{extension}"
            nueva_ruta = os.path.join(directorio, nuevo_nombre)
            contador += 1

        # Renombrar el archivo existente
        os.rename(ruta_archivo, nueva_ruta)
        print(f"Archivo renombrado: {ruta_archivo} -> {nueva_ruta}")
        return nueva_ruta
    else:
        print(f"El archivo {ruta_archivo} no existe")
        return None


_INDEX_RE = re.compile(r"^(?P<tag>[^\[\]]+?)(?:\[(?P<idx>\d+)\])?$")


class Xml:
    """
    Reemplazo nativo para chilkat2.Xml.
    Métodos compatibles:
      - Tag (propiedad)
      - UpdateChildContent(path, text)
      - UpdateChildContentInt(path, number)
      - SaveXml(file_path)
    Soporta rutas con '|' y sufijos [n] (1-based).
    """

    def __init__(self, root_tag: str = "root"):
        self._root = ET.Element(root_tag)

    # --- Propiedad Tag ---
    @property
    def Tag(self) -> str:
        return self._root.tag

    @Tag.setter
    def Tag(self, value: str) -> None:
        self._root.tag = value

    # --- API pública ---
    def UpdateChildContent(self, path: str, text) -> None:
        elem = self._get_or_create(path)
        elem.text = "" if text is None else str(text)

    def UpdateChildContentInt(self, path: str, number: int) -> None:
        self.UpdateChildContent(path, str(int(number)))

    def SaveXml(self, file_path: str, encoding: str = "utf-8") -> None:
        xml_bytes = self._to_pretty_xml_bytes(encoding)
        with open(file_path, "wb") as f:
            f.write(xml_bytes)

    # --- Internos ---
    def _parse_part(self, token: str):
        m = _INDEX_RE.match(token)
        tag = m.group("tag")
        idx_str = m.group("idx")
        if idx_str is None:
            return tag, None
        return tag, int(idx_str)  # 1-based → índice real

    def _get_or_create(self, path: str) -> ET.Element:
        parts = path.split("|")
        node = self._root
        for token in parts:
            tag, idx = self._parse_part(token)
            children = [c for c in list(node) if c.tag == tag]

            if idx is None:
                if children:
                    child = children[0]
                else:
                    child = ET.SubElement(node, tag)
            else:
                needed = idx + 1  # [1] = segundo
                while len(children) < needed:
                    ET.SubElement(node, tag)
                    children = [c for c in list(node) if c.tag == tag]
                child = children[idx]
            node = child
        return node

    def _to_pretty_xml_bytes(self, encoding="utf-8") -> bytes:
        rough = ET.tostring(self._root, encoding=encoding)
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding=encoding)


# _______________________________conecciones a los config_________________________________


def load_interval_config():
    """Carga la configuración de intervalo desde un archivo JSON."""
    # Obtener la ruta del ejecutable o script
    if getattr(sys, "frozen", False):
        # Si es un ejecutable compilado con PyInstaller
        base_path = os.path.dirname(sys.executable)
    else:
        # Si es un script de Python
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)

    # Ruta del archivo interval.json
    config_path = os.path.join(base_path, "config", "interval.json")

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        return {
            "check_interval_envio": config.get("check_interval_envio", 5),
            "check_interval_consulta": config.get("check_interval_consulta", 5),
            "check_interval_impresion": config.get("check_interval_impresion", 5),
            "check_interval_GyF": config.get("check_interval_GyF", 5),
        }
    except FileNotFoundError:
        print(
            f"Advertencia: No se encontró el archivo de configuración en {config_path}"
        )
        return {
            "check_interval_envio": 5,
            "check_interval_consulta": 5,
            "check_interval_impresion": 5,
            "check_interval_GyF": 5,
        }
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return {
            "check_interval_envio": 5,
            "check_interval_consulta": 5,
            "check_interval_impresion": 5,
            "check_interval_GyF": 5,
        }
