import csv
import json
import os
import sys
import time

import portalocker
import pyodbc
import requests
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

# Cambiar al directorio root para que las cargas relativas funcionen (configs, DB paths, etc.)
os.chdir(project_root)

from config.uGlobalConfig import *
from config.uGlobalConfig import GConfig
from db.uDB import *
from glib.Servicios import *
from glib.ufe import *
from glib.uGlobalLib import *

# Cargar configuración desde un archivo JSON


def get_config_path():
    # Si se ejecuta como .exe, usar _MEIPASS; si no, usar el directorio del script
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    # Buscar primero en el directorio actual, luego en base_path
    local_config = os.path.join(os.getcwd(), "config.json")
    if os.path.exists(local_config):
        return local_config
    return os.path.join(base_path, "config.json")


CONFIG_FILE = get_config_path()


def cargar_configuracion():
    """Carga la configuración desde un archivo JSON."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Archivo de configuración '{CONFIG_FILE}' no encontrado."
        )
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


# Obtener la ruta de guardado y la URL de la API desde la configuración
try:
    configuracion = cargar_configuracion()
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    RUTA_GUARDADO = configuracion.get("ruta_guardado", ruta_actual)
    RUTA_GUARDADO_2 = configuracion.get("ruta_guardado_2", ruta_actual)
    API_URL = configuracion.get("api_url", "https://127.0.0.1:8001/upload-csv")
    API_URL_2 = configuracion.get("api_url_2", "https://127.0.0.1:8001/FGE")
    API_KEY = configuracion.get("api_key", "")  # Agregamos la extracción del API key
except Exception as e:
    print(f"Error al cargar la configuración: {e}")
    sys.exit(1)

# Crear los directorios si no existehgbgfghn
if not os.path.exists(RUTA_GUARDADO):
    os.makedirs(RUTA_GUARDADO)
if not os.path.exists(RUTA_GUARDADO_2):
    os.makedirs(RUTA_GUARDADO_2)


def consumir_api_post(rnc, encf, file_path=None, url=None):
    """
    Envía una solicitud POST a la API y maneja las respuestas según las especificaciones del endpoint.

    :param rnc: Valor del campo 'rnc'.
    :param encf: Valor del campo 'encf'.
    :param file_path: Ruta del archivo CSV a enviar (opcional).
    :param url: URL de la API a utilizar (opcional).
    :return: Respuesta de la API en formato JSON.
    """
    if url is None:
        url = API_URL
    headers = (
        {"x-api-key": API_KEY} if API_KEY else {}  # Cambiamos el formato del header
    )

    data = {"rnc": rnc, "encf": encf}
    files = None
    if file_path:
        with open(file_path, "rb") as file:
            files = {"file": file}
            try:
                response = requests.post(
                    url, data=data, files=files, headers=headers, verify=False
                )
                return response.json()
            except requests.exceptions.HTTPError:
                try:
                    return response.json()
                except ValueError:
                    return {"codigo": "00", "message": "Error HTTP sin respuesta JSON."}
            except Exception as e:
                return {"codigo": "00", "message": f"Error inesperado: {e}"}
    else:
        try:
            response = requests.post(url, data=data, headers=headers, verify=False)
            return response.json()
        except requests.exceptions.HTTPError:
            try:
                return response.json()
            except ValueError:
                return {"codigo": "00", "message": "Error HTTP sin respuesta JSON."}
        except Exception as e:
            return {"codigo": "00", "message": f"Error inesperado: {e}"}


def crear_nombre_archivo(rnc, encf):
    """Crea el nombre del archivo según el formato R{rnc}{encf}.csv"""
    return f"R{rnc}{encf}.csv"


def guardar_respuesta_csv(nombre_archivo, respuesta, ruta_guardado):
    """Guarda la respuesta en un archivo CSV en la ruta especificada. Maneja cualquier estructura JSON"""
    ruta_completa = os.path.join(ruta_guardado, nombre_archivo)

    # Convertir todos los valores a string y unirlos con comas
    valores_csv = ",".join(str(valor) for valor in respuesta.values())

    with open(ruta_completa, "w", newline="") as csvfile:
        csvfile.write(valores_csv)
    return ruta_completa


def main():
    print("Inserte parámetros en el siguiente formato:")
    print("<rnc> <encf> [ruta_archivo] or <rnc> <encf> GyF")

    try:
        # Verificar si se pasaron argumentos desde la línea de comandos
        if len(sys.argv) == 4:
            rnc, encf, third_arg = sys.argv[1:4]
            if third_arg.upper() == "GYF":
                ejecutar_generar_y_firmar(rnc, encf, third_arg)
                sys.exit(0)  # Salir después de ejecutar la función
            else:
                # Si el tercer argumento no es "GyF", se asume que es la ruta del archivo
                file_path = third_arg
                if not os.path.isfile(file_path):
                    print(f"Error: El archivo especificado no existe: {file_path}")
                    sys.exit(1)
                # Convertir la ruta a absoluta para evitar problemas en el entorno del ejecutable
                file_path = os.path.abspath(file_path)
                respuesta = consumir_api_post(rnc, encf, file_path, url=API_URL)
                ruta_guardado = RUTA_GUARDADO
        elif len(sys.argv) == 3:
            rnc, encf = sys.argv[1:3]
            respuesta = consumir_api_post(rnc, encf, file_path=None, url=API_URL_2)
            ruta_guardado = RUTA_GUARDADO_2
        else:
            # Solicitar entrada al usuario si no se pasaron argumentos
            entrada = input().strip()
            parametros = entrada.split()

            if len(parametros) == 3:
                rnc, encf, third_arg = parametros
                if third_arg.upper() == "GYF":
                    ejecutar_generar_y_firmar(rnc, encf, third_arg)
                    sys.exit(0)  # Salir después de ejecutar la función
                else:
                    file_path = third_arg
                    if not os.path.isfile(file_path):
                        print(f"Error: El archivo especificado no existe: {file_path}")
                        sys.exit(1)
                    file_path = os.path.abspath(file_path)
                    respuesta = consumir_api_post(rnc, encf, file_path, url=API_URL)
                    ruta_guardado = RUTA_GUARDADO
            elif len(parametros) == 2:
                rnc, encf = parametros
                respuesta = consumir_api_post(rnc, encf, file_path=None, url=API_URL_2)
                ruta_guardado = RUTA_GUARDADO_2
            else:
                print("Error: Debe proporcionar 2 o 3 parámetros")
                sys.exit(1)

        print(json.dumps(respuesta, indent=2))

        # Guardar respuesta en CSV
        nombre_archivo = crear_nombre_archivo(rnc, encf)
        ruta_guardada = guardar_respuesta_csv(nombre_archivo, respuesta, ruta_guardado)
        print(f"Respuesta guardada en {ruta_guardada}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def ejecutar_generar_y_firmar(rnc, encf, GyF):
    """Ejecuta la función GenerarYFirmar con los parámetros dados."""
    try:
        UnlockCK()
        GConfig.cargar(1)

        # Conexión a la base de datos
        cn1 = ConectarDB()

        # Agrega esta línea para inicializar completamente GConfig desde la DB
        mostrarConfiguracion(GConfig, cn1)

        try:
            query = f"Select * from vFEEncabezado with (nolock) where EstadoFiscal =1 and Trackid is null and  TipoECFL = 'E' and RNCEmisor = '{rnc}' and ENCF = '{encf}'"
            vFEEncabezado = cn1.fetch_query(query)
            for row in vFEEncabezado:
                GenerarYFirmar(cn1, row)
        except Exception as e:
            print(f"Error: {e}")

    except Exception as e:
        print(f"Error al ejecutar GenerarYFirmar: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
