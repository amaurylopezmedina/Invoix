import json
import os

# Ruta del archivo de configuración
CONFIG_FILE = 'config.json'

# Configuración por defecto
DEFAULT_CONFIG = {
    "RUTA_ARCHIVO_EXCEL": "",
    "SERVIDOR_SQL": "127.0.0.1",
    "BASE_DATOS_SQL": "FECertASESYS",
    "USUARIO_SQL": "sistema",
    "PASSWORD_SQL": "@@sistema",
    "TRUSTED_CONNECTION": False,
    "NOMBRE_HOJA": "ECF",
    "COLUMNA_FIN_ENCABEZADO": "MontoTotalOtraMoneda",
    "COLUMNA_INICIO_DETALLE": "NumeroLinea[1]",
    "NUMERO_MAXIMO_DETALLES": 62,
    "VALOR_NULO": "#e"
}

def load_config():
    """
    Carga la configuración desde el archivo JSON.
    Si el archivo no existe, crea uno con la configuración por defecto.
    
    Returns:
        dict: Configuración cargada
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Asegurar que todas las claves existan
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        else:
            # Crear archivo de configuración por defecto
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Error al cargar la configuración: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config):
    """
    Guarda la configuración en el archivo JSON.
    
    Args:
        config (dict): Configuración a guardar
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"Configuración guardada en {CONFIG_FILE}")
    except Exception as e:
        print(f"Error al guardar la configuración: {str(e)}")

# Para compatibilidad con el código existente
# Cargar la configuración al importar el módulo
config = load_config()

# Exponer variables para ser compatibles con el código existente
RUTA_ARCHIVO_EXCEL = config["RUTA_ARCHIVO_EXCEL"]
SERVIDOR_SQL = config["SERVIDOR_SQL"]
BASE_DATOS_SQL = config["BASE_DATOS_SQL"]
USUARIO_SQL = config["USUARIO_SQL"]
PASSWORD_SQL = config["PASSWORD_SQL"]
TRUSTED_CONNECTION = config["TRUSTED_CONNECTION"]
NOMBRE_HOJA = config["NOMBRE_HOJA"]
COLUMNA_FIN_ENCABEZADO = config["COLUMNA_FIN_ENCABEZADO"]
COLUMNA_INICIO_DETALLE = config["COLUMNA_INICIO_DETALLE"]
NUMERO_MAXIMO_DETALLES = config["NUMERO_MAXIMO_DETALLES"]
VALOR_NULO = config["VALOR_NULO"]

def update_config_variables():
    """
    Actualiza las variables globales con los valores del archivo de configuración.
    """
    global RUTA_ARCHIVO_EXCEL, SERVIDOR_SQL, BASE_DATOS_SQL, USUARIO_SQL, PASSWORD_SQL
    global TRUSTED_CONNECTION, NOMBRE_HOJA, COLUMNA_FIN_ENCABEZADO, COLUMNA_INICIO_DETALLE
    global NUMERO_MAXIMO_DETALLES, VALOR_NULO
    
    config = load_config()
    
    RUTA_ARCHIVO_EXCEL = config["RUTA_ARCHIVO_EXCEL"]
    SERVIDOR_SQL = config["SERVIDOR_SQL"]
    BASE_DATOS_SQL = config["BASE_DATOS_SQL"]
    USUARIO_SQL = config["USUARIO_SQL"]
    PASSWORD_SQL = config["PASSWORD_SQL"]
    TRUSTED_CONNECTION = config["TRUSTED_CONNECTION"]
    NOMBRE_HOJA = config["NOMBRE_HOJA"]
    COLUMNA_FIN_ENCABEZADO = config["COLUMNA_FIN_ENCABEZADO"]
    COLUMNA_INICIO_DETALLE = config["COLUMNA_INICIO_DETALLE"]
    NUMERO_MAXIMO_DETALLES = config["NUMERO_MAXIMO_DETALLES"]
    VALOR_NULO = config["VALOR_NULO"]