import os
import sys
from configparser import ConfigParser

import pyodbc


def get_db_connection():
    # Detectar si se ejecuta como .exe (frozen) o como script Python
    if getattr(sys, "frozen", False):
        # Ejecutándose como .exe - usar la carpeta donde está el ejecutable
        base_path = os.path.dirname(sys.executable)
    else:
        # Ejecutándose como script Python
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Especificar que 'cn.ini' está en la carpeta 'config'
    config_path = os.path.join(base_path, "config", "cn.ini")

    # Leer el archivo cn.ini
    config = ConfigParser()
    config.read(config_path)

    # Obtener el connection_string desde el archivo de configuración
    connection_string = config.get("database", "connection_string", fallback=None)

    if connection_string is None:
        raise ValueError(
            "El connection_string no está configurado correctamente en el archivo cn.ini"
        )

    # Limpiar saltos de línea y espacios extras de la cadena de conexión
    connection_string = connection_string.replace("\n", "").replace("\r", "")
    connection_string = " ".join(connection_string.split())

    return pyodbc.connect(connection_string)
