# configuracion.py
# Archivo de configuración para la importación de Excel a SQL Server

# Configuración de rutas y conexión
RUTA_ARCHIVO_EXCEL = "C:/Users/amaur/Downloads/106011932-21032025114338.xlsx"  # Ruta al archivo Excel
SERVIDOR_SQL = "127.0.0.1"  # Nombre del servidor SQL Server
BASE_DATOS_SQL = "FECertASESYS"  # Nombre de la base de datos
USUARIO_SQL ='sistema'  # Usuario SQL Server (None para Windows Authentication)
PASSWORD_SQL = '@@sistema'  # Contraseña SQL Server (None para Windows Authentication)
TRUSTED_CONNECTION = False  # True para usar Windows Authentication

# Configuración de hojas Excel
NOMBRE_HOJA = "ECF"  # Nombre de la hoja en el archivo Excel

# Configuración de columnas clave
COLUMNA_FIN_ENCABEZADO = "MontoTotalOtraMoneda"  # Columna donde termina el encabezado
COLUMNA_INICIO_DETALLE = "NumeroLinea[1]"  # Columna donde comienza el detalle
NUMERO_MAXIMO_DETALLES = 62  # Número máximo de líneas de detalle por registro

# Configuración de valores especiales
VALOR_NULO = "#e"  # Valor que se considerará como NULL en la base de datos