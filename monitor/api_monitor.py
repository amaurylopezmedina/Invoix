import json
import logging
from datetime import datetime

import pyodbc
from database import get_db_connection
from flask import Response, abort, jsonify, request

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

logger = logging.getLogger(__name__)


def test_database_connection():
    """
    Prueba la conexión a la base de datos y retorna el estado
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return "Conectado correctamente"
    except Exception as e:
        return f"Error de conexión: {str(e)}"


def format_number(number):
    """Formatea números con separador de miles y 2 decimales"""
    return "{:,.2f}".format(number)


def get_estados_fiscales():
    """
    Obtiene los estados fiscales de facturación electrónica con filtros opcionales.
    
    Parámetros de query:
    - fecha_inicio: Fecha de inicio (formato: YYYY-MM-DD) - OPCIONAL
    - fecha_fin: Fecha de fin (formato: YYYY-MM-DD) - OPCIONAL
    - caja: Filtro por caja (default: TODAS)
    - estado_fiscal: Filtro por estado fiscal, puede ser múltiple separado por coma (ej: "1,2,3") - PRIORITARIO
    - rncemisor: Filtro por RNC emisor (default: TODOS)
    - tipo_ecf: Filtro por tipo de eCF (default: TODOS)
    - order_field: Campo de ordenamiento (default: FechaEmision)
    - order_dir: Dirección de ordenamiento ASC/DESC (default: DESC)
    """
    conn = None
    cursor = None
    try:
        # Obtener parámetros de la request - soportar múltiples nombres por compatibilidad
        fecha_inicio = request.args.get("fecha_inicio") or request.args.get("dateFrom", "")
        fecha_fin = request.args.get("fecha_fin") or request.args.get("dateTo", "")
        caja = request.args.get("caja", "TODAS")
        estado_fiscal = request.args.get("estado_fiscal", "TODOS")
        rncemisor = request.args.get("rncemisor", "TODOS")
        tipo_ecf = request.args.get("tipo_ecf", "TODOS")
        order_field = request.args.get("order_field", "FechaEmision")
        order_dir = request.args.get("order_dir", "DESC")

        # Las fechas ahora son OPCIONALES
        fecha_inicio_dt = None
        fecha_fin_dt = None
        
        # Validar formato de fechas solo si están presentes
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La fecha_inicio debe tener el formato 'YYYY-MM-DD'")
        
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La fecha_fin debe tener el formato 'YYYY-MM-DD'")
        
        # Logging para búsquedas sin filtro de fecha
        if not fecha_inicio and not fecha_fin:
            logger.info(f'Búsqueda sin filtro de fecha - rncemisor: {rncemisor}, estado_fiscal: {estado_fiscal}, caja: {caja}, timestamp: {datetime.now()}')

        # Construir query SQL con TODOS los campos necesarios incluyendo los del link DGII
        # Usar vista vFEEncabezado que tiene el URLQR correctamente calculado
        query = """
            SELECT 
                f.NumeroFacturaInterna AS Factura,
                CASE 
                    WHEN f.TipoPago = 1 THEN 'CONTADO'
                    WHEN f.TipoPago = 2 THEN 'CREDITO'
                    ELSE 'N/A'
                END AS TipoVenta, 
                f.TipoECF, 
                f.eNCF AS encf, 
                f.EstadoFiscal, 
                ef.Descripcion AS DescripcionEstadoFiscal,
                f.ResultadoEstadoFiscal,
                f.MontoTotal AS MontoFacturado, 
                f.TotalITBIS AS ITBISFacturado, 
                f.MontoDGII, 
                f.MontoITBISDGII,
                f.RNCEmisor,
                f.RNCComprador,
                CONVERT(VARCHAR(10), f.FechaEmision, 105) AS FechaEmision,
                CONVERT(VARCHAR(10), f.FechaFirma, 105) + ' ' + CONVERT(VARCHAR(8), f.FechaFirma, 108) AS FechaFirma,
                f.CodigoSeguridad,
                f.URLQR AS URLC,
                LEFT(f.NumeroFacturaInterna, 1) AS Caja
            FROM dbo.vFEEncabezado AS f
            LEFT OUTER JOIN dbo.EstadoFiscal AS ef ON f.EstadoFiscal = ef.estado
            WHERE 1=1
        """
        params = []

        # Filtros de fecha - OPCIONALES
        if fecha_inicio_dt:
            query += " AND CONVERT(date, f.FechaEmision) >= ?"
            params.append(fecha_inicio_dt)
        
        if fecha_fin_dt:
            query += " AND CONVERT(date, f.FechaEmision) <= ?"
            params.append(fecha_fin_dt)

        # Agregar filtros opcionales
        if caja != "TODAS":
            query += " AND LEFT(f.NumeroFacturaInterna, 1) = ?"
            params.append(caja)

        # Filtro de Estado Fiscal - PRIORITARIO - Soporta múltiples valores separados por coma
        if estado_fiscal and estado_fiscal != "TODOS":
            # Procesar múltiples estados fiscales separados por coma
            estados_list = [e.strip() for e in estado_fiscal.split(',') if e.strip()]
            if estados_list:
                placeholders = ','.join(['?' for _ in estados_list])
                query += f" AND f.EstadoFiscal IN ({placeholders})"
                params.extend(estados_list)

        if rncemisor and rncemisor != "TODOS":
            query += " AND f.RNCEmisor = ?"
            params.append(rncemisor)
            
        if tipo_ecf and tipo_ecf != "TODOS":
            query += " AND f.TipoECF = ?"
            params.append(tipo_ecf)
        
        # Validar y agregar ordenamiento
        order_mapping = {
            "FechaEmision": "f.FechaEmision",
            "Factura": "f.NumeroFacturaInterna"
        }
        order_field_sql = order_mapping.get(order_field, "f.FechaEmision")
        if order_dir not in ("ASC", "DESC"):
            order_dir = "DESC"
        
        query += f" ORDER BY {order_field_sql} {order_dir}"

        # Ejecutar query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        
        # Implementar límite de 1000 registros para búsquedas sin fecha
        LIMITE_REGISTROS = 1000
        limite_alcanzado = False
        
        # Usar fetchmany para verificar si hay más registros que el límite
        if not fecha_inicio and not fecha_fin:
            results = cursor.fetchmany(LIMITE_REGISTROS + 1)
            if len(results) > LIMITE_REGISTROS:
                limite_alcanzado = True
                results = results[:LIMITE_REGISTROS]
        else:
            results = cursor.fetchall()

        if not results:
            # Si no hay resultados, retornar estructura vacía
            response = Response(
                json.dumps({
                    "resultados": [],
                    "total_registros": 0,
                    "totales": {
                        "monto_facturado": 0.00,
                        "itbis_facturado": 0.00,
                        "monto_dgii": 0.00,
                        "itbis_dgii": 0.00,
                        "diferencia_monto": 0.00,
                        "diferencia_itbis": 0.00
                    }
                }, ensure_ascii=False),
                mimetype="application/json",
            )
            return response

        # Inicializar acumuladores para totales
        total_monto_facturado = 0.0
        total_itbis_facturado = 0.0
        total_monto_dgii = 0.0
        total_itbis_dgii = 0.0

        # Formatear resultados
        datos = []
        for row in results:
            # Convertir valores numéricos
            monto_facturado = float(row[7] or 0.0)
            itbis_facturado = float(row[8] or 0.0)
            monto_dgii = float(row[9] or 0.0)
            itbis_dgii = float(row[10] or 0.0)
            
            # Calcular diferencias
            dif_monto = monto_facturado - monto_dgii
            dif_itbis = itbis_facturado - itbis_dgii
            
            # Acumular totales
            total_monto_facturado += monto_facturado
            total_itbis_facturado += itbis_facturado
            total_monto_dgii += monto_dgii
            total_itbis_dgii += itbis_dgii
            
            datos.append({
                "factura": str(row[0] or "").strip(),
                "tipo_venta": str(row[1] or "N/A").strip(),
                "tipo_ecf": str(row[2] or "").strip(),
                "encf": str(row[3] or "").strip(),
                "estado_fiscal": int(row[4]) if row[4] is not None else 0,
                "estado_fiscal_descripcion": str(row[5] or "").strip(),
                "resultado_estado_fiscal": str(row[6] or "").strip(),
                "monto_facturado": round(monto_facturado, 2),
                "itbis_facturado": round(itbis_facturado, 2),
                "monto_dgii": round(monto_dgii, 2),
                "itbis_dgii": round(itbis_dgii, 2),
                "dif_monto": round(dif_monto, 2),
                "dif_itbis": round(dif_itbis, 2),
                "rncemisor": str(row[11] or "").strip(),
                "rnccomprador": str(row[12] or "").strip(),
                "fecha_emision": str(row[13] or "").strip(),  # Ya formateada: DD-MM-YYYY
                "fecha_firma": str(row[14] or "").strip(),     # Ya formateada: DD-MM-YYYY HH:MM:SS
                "codigo_seguridad": str(row[15] or "").strip(),
                "urlc": str(row[16] or "").strip(),
                "caja": str(row[17] or "").strip()
            })

        # Calcular totales y diferencias
        total_dif_monto = total_monto_facturado - total_monto_dgii
        total_dif_itbis = total_itbis_facturado - total_itbis_dgii

        # Retornar respuesta JSON con resultados y totales
        response_data = {
            "resultados": datos,
            "total_registros": len(datos),
            "totales": {
                "monto_facturado": round(total_monto_facturado, 2),
                "itbis_facturado": round(total_itbis_facturado, 2),
                "monto_dgii": round(total_monto_dgii, 2),
                "itbis_dgii": round(total_itbis_dgii, 2),
                "diferencia_monto": round(total_dif_monto, 2),
                "diferencia_itbis": round(total_dif_itbis, 2)
            }
        }
        
        # Agregar información de límite alcanzado si aplica
        if limite_alcanzado:
            response_data["limite_alcanzado"] = True
            response_data["mensaje"] = f"Se alcanzó el límite de {LIMITE_REGISTROS} registros. Por favor, refine su búsqueda usando filtros de fecha."
            logger.warning(f"Límite de {LIMITE_REGISTROS} registros alcanzado en búsqueda sin fecha - rncemisor: {rncemisor}, estado_fiscal: {estado_fiscal}")
        
        response = Response(
            json.dumps(response_data, ensure_ascii=False),
            mimetype="application/json",
        )
        return response

    except pyodbc.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        abort(500, description=f"Error de base de datos: {str(e)}")
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        abort(400, description=str(e))
    except Exception as e:
        logger.error(f"Error del servidor: {str(e)}")
        abort(500, description=f"Error del servidor: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_estado_fiscal():
    """
    Actualiza el estado fiscal de un comprobante electrónico.
    
    Parámetros de query:
    - rnc: RNC del emisor - Obligatorio
    - ncf: Número de comprobante fiscal (eNCF) - Obligatorio
    """
    conn = None
    cursor = None
    try:
        rnc = request.args.get("rnc", "").strip()
        ncf = request.args.get("ncf", "").strip()

        if not rnc or not ncf:
            raise ValueError("Los parámetros rnc y ncf son obligatorios")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Actualizar estado fiscal a 4 (Anulado)
        query = """
            UPDATE FEEncabezado
            SET estadofiscal = 4
            WHERE RNCEmisor = ? AND eNCF = ?
        """
        cursor.execute(query, (rnc, ncf))
        conn.commit()

        if cursor.rowcount == 0:
            raise ValueError("No se actualizó ningún registro. Verifique el RNC y NCF.")

        response = Response(
            json.dumps({"mensaje": "Actualización exitosa", "rnc": rnc, "ncf": ncf}, ensure_ascii=False),
            mimetype="application/json",
        )
        return response

    except pyodbc.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        abort(500, description=f"Error de base de datos: {str(e)}")
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        abort(400, description=str(e))
    except Exception as e:
        logger.error(f"Error del servidor: {str(e)}")
        abort(500, description=f"Error del servidor: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_empresa_rnc():
    """
    Obtiene el RNC y nombre de la empresa desde la tabla Empresa.
    
    Retorna el primer RNC y nombre encontrado en la tabla Empresa.
    Estos valores se usan como predeterminados en el frontend.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consultar el RNC y nombre de la tabla Empresa
        query = "SELECT TOP 1 rnc, nombre FROM Empresa"
        cursor.execute(query)
        resultado = cursor.fetchone()
        
        if resultado and resultado[0]:
            rnc = str(resultado[0]).strip()
            nombre = str(resultado[1]).strip() if resultado[1] else ""
            response = Response(
                json.dumps({"rnc": rnc, "nombre": nombre}, ensure_ascii=False),
                mimetype="application/json",
            )
            return response
        else:
            # Si no hay empresa configurada, retornar error 404
            abort(404, description="No se encontró empresa configurada en la base de datos")
    
    except pyodbc.Error as e:
        logger.error(f"Error de base de datos al obtener RNC empresa: {str(e)}")
        abort(500, description=f"Error de base de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener RNC empresa: {str(e)}")
        abort(500, description=f"Error del servidor: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
