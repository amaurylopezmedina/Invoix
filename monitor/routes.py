from flask import Blueprint
from api_monitor import get_estados_fiscales, update_estado_fiscal, get_empresa_rnc
from api_pdf import generar_pdf_representacion

# Crear blueprint para las rutas del monitor
routes = Blueprint("monitor", __name__)


@routes.route("/estados-fiscales", methods=["GET"])
def obtener_estados_fiscales():
    """
    Endpoint para obtener estados fiscales de comprobantes electrónicos.
    
    GET /estados-fiscales?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
    
    Parámetros opcionales:
    - caja: Filtro por caja
    - estado_fiscal: Filtro por estado fiscal
    - rncemisor: Filtro por RNC emisor
    - tipo_ecf: Filtro por tipo de eCF
    - order_field: Campo de ordenamiento
    - order_dir: Dirección de ordenamiento (ASC/DESC)
    """
    return get_estados_fiscales()

@routes.route("/empresa-rnc", methods=["GET"])
def obtener_empresa_rnc():
    """
    Endpoint para obtener el RNC y nombre de la empresa configurada.
    
    GET /empresa-rnc
    
    Retorna: {"rnc": "102003491", "nombre": "MI EMPRESA S.A."}
    """
    return get_empresa_rnc()

@routes.route("/actualizar-estado-fiscal", methods=["PUT"])
def actualizar_estado_fiscal():
    """
    Endpoint para actualizar el estado fiscal de un comprobante.
    
    PUT /actualizar-estado-fiscal
    Body/Query: {"rnc": "131695312", "encf": "E310000000001", "nuevo_estado": 5}
    
    Retorna: Confirmación de la actualización
    """
    return update_estado_fiscal()

@routes.route("/generar-pdf", methods=["POST", "GET"])
def endpoint_generar_pdf():
    """
    Endpoint para generar PDF de representación impresa.
    Genera un PDF con el formato oficial de la DGII según el tipo de comprobante.
    
    POST/GET /generar-pdf
    Body/Query: {"rnc": "131695312", "encf": "E310000000001"}
    
    Retorna: Archivo PDF descargable con la representación impresa
    """
    return generar_pdf_representacion()

@routes.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint para verificar el estado del servicio Monitor.
    
    GET /health
    
    Retorna: Estado del servicio y conexión a base de datos
    """
    from flask import jsonify
    from datetime import datetime
    from api_monitor import test_database_connection
    
    try:
        db_status = test_database_connection()
        status = "OK" if "Conectado correctamente" in db_status else "WARNING"
        
        return jsonify({
            "status": status,
            "service": "Monitor API",
            "timestamp": datetime.now().isoformat(),
            "port": 8002,
            "database": db_status,
            "version": "1.0"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "service": "Monitor API",
            "timestamp": datetime.now().isoformat(),
            "port": 8002,
            "error": str(e),
            "version": "1.0"
        }), 500

