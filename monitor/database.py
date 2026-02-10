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
        # Ejecutándose como script Python - carpeta padre de MONITOR
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Usar CN.ini en la carpeta config del proyecto base
    config_path = os.path.join(base_path, "config", "CN.ini")

    # Leer el archivo CN.ini
    config = ConfigParser()
    config.read(config_path, encoding="utf-8")

    # Obtener el connection_string desde el archivo de configuración
    connection_string = config.get("database", "connection_string", fallback=None)

    if connection_string is None:
        raise ValueError(
            "El connection_string no está configurado correctamente en el archivo cn.ini"
        )

    # Limpiar saltos de línea y espacios extras de la cadena de conexión
    # Mantener la estructura pero sin espacios innecesarios
    connection_string = " ".join(
        line.strip() for line in connection_string.splitlines() if line.strip()
    )

    return pyodbc.connect(connection_string)
