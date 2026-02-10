import io
import logging
from datetime import datetime
from database import get_db_connection
from flask import abort, jsonify, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import qrcode
from PIL import Image

logger = logging.getLogger(__name__)


def to_float(val, default=0.0):
    """Convierte de forma segura a float, devolviendo default si falla."""
    try:
        if val is None:
            return default
        # Normalizar a string y eliminar espacios y comas
        s = str(val).strip()
        if not s:
            return default
        s = s.replace(',', '')
        return float(s)
    except Exception:
        return default


def generar_pdf_representacion():
    """
    Genera un PDF de representación impresa de un comprobante electrónico.
    
    POST /api/monitor/generar-pdf
    Body: {"rnc": "131695312", "encf": "E310000000001"}
    
    Retorna: PDF con la representación impresa del comprobante
    """
    conn = None
    cursor = None
    try:
        # Obtener parámetros
        if request.is_json:
            data = request.get_json()
            rnc = data.get("rnc", "").strip()
            encf = data.get("encf", "").strip()
        else:
            rnc = request.args.get("rnc", "").strip()
            encf = request.args.get("encf", "").strip()

        if not rnc or not encf:
            raise ValueError("Los parámetros rnc y encf son obligatorios")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar datos del encabezado usando la vista vFEEncabezado
        query_encabezado = """
            SELECT 
                e.RNCEmisor,
                e.RazonSocialEmisor,
                e.NombreComercial,
                e.DireccionEmisor,
                e.eNCF,
                e.TipoECF,
                e.FechaEmision,
                e.RNCComprador,
                e.RazonSocialComprador,
                e.TipoPago,
                e.MontoTotal,
                e.TotalITBIS,
                e.CodigoSeguridad,
                e.URLQR,
                e.FechaFirma,
                e.NumeroFacturaInterna
            FROM dbo.vFEEncabezado e
            WHERE e.RNCEmisor = ? AND e.eNCF = ?
        """
        cursor.execute(query_encabezado, (rnc, encf))
        row = cursor.fetchone()

        if not row:
            raise ValueError("No se encontró el comprobante especificado")
        
        # Convertir fila a diccionario
        encabezado_dict = {}
        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                col_name = col_desc[0]
                encabezado_dict[col_name] = row[i]
        
        encabezado = encabezado_dict
        
        # Debug: verificar URLQR
        logger.info(f"Datos encabezado obtenidos: RNC={rnc}, eNCF={encf}")
        logger.info(f"URLQR del encabezado: '{encabezado.get('URLQR')}'")
        logger.info(f"Campos disponibles: {list(encabezado.keys())}")

        # Consultar detalles del comprobante - usar SELECT * para obtener todas las columnas
        query_detalle = """
            SELECT * FROM dbo.vFEDetalle d
            WHERE d.RNCEmisor = ? AND d.ENCF = ?
            ORDER BY d.NumeroLinea
        """
        cursor.execute(query_detalle, (rnc, encf))
        cursor.description  # Asegurar que tenemos los nombres de columnas
        detalles = []
        for row in cursor.fetchall():
            # Convertir cada fila a un diccionario
            detalle_dict = {}
            if cursor.description:
                for i, col_desc in enumerate(cursor.description):
                    col_name = col_desc[0]
                    try:
                        detalle_dict[col_name] = row[i]
                    except:
                        detalle_dict[col_name] = None
            detalles.append(detalle_dict)

        # Generar PDF
        buffer = io.BytesIO()
        pdf = generar_pdf_factura(buffer, encabezado, detalles)
        buffer.seek(0)

        logger.info(f"PDF generado para: {encf}, RNC: {rnc}")

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Factura_{encf}.pdf'
        )

    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        abort(400, description=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def generar_pdf_factura(buffer, encabezado, detalles):
    """
    Genera el PDF con el formato de representación impresa de la DGII.
    """
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Paleta de colores para un diseño más marcado
    primary = colors.HexColor("#0B3C5D")
    secondary = colors.HexColor("#328CC1")
    light_gray = colors.HexColor("#F2F4F7")

    # Márgenes
    margen_izq = 0.75 * inch
    margen_top = height - 0.75 * inch
    y = margen_top

    # Obtener valores del encabezado de forma segura
    rnc_emisor = str(encabezado.get('RNCEmisor', ''))
    razon_social = str(encabezado.get('RazonSocialEmisor', ''))
    nombre_comercial = str(encabezado.get('NombreComercial', ''))
    direccion = str(encabezado.get('DireccionEmisor', ''))
    encf = str(encabezado.get('eNCF', encabezado.get('ENCF', '')))
    tipo_ecf = str(encabezado.get('TipoECF', ''))
    fecha_emision = encabezado.get('FechaEmision')
    rnc_comprador = str(encabezado.get('RNCComprador', ''))
    razon_social_comprador = str(encabezado.get('RazonSocialComprador', ''))
    # URL para QR: priorizar la proveniente del backend (URLQR / URLC / urlc)
    url_qr_raw = encabezado.get('URLQR') or encabezado.get('URLC') or encabezado.get('urlc') or ""
    url_qr = str(url_qr_raw).strip() if url_qr_raw else ""
    
    # Debug: imprimir URL para diagnóstico
    logger.info(f"=== DEBUG QR ===")
    logger.info(f"URLQR raw: '{url_qr_raw}' (tipo: {type(url_qr_raw)})")
    logger.info(f"URLQR procesada: '{url_qr}'")
    logger.info(f"Longitud URL: {len(url_qr) if url_qr else 0}")
    logger.info(f"Campos en encabezado: {list(encabezado.keys())}")
    logger.info(f"=== FIN DEBUG ===")
    
    fecha_firma = encabezado.get('FechaFirma')
    codigo_seguridad = str(encabezado.get('CodigoSeguridad', ''))

    # --- ENCABEZADO ---
    # Datos del emisor en la izquierda
    c.setFont("Helvetica-Bold", 11)
    nombre_mostrar = nombre_comercial if nombre_comercial else razon_social
    c.drawString(margen_izq, y, nombre_mostrar)
    y -= 0.18 * inch

    c.setFont("Helvetica", 9)
    c.drawString(margen_izq, y, f"RNC {rnc_emisor}")
    y -= 0.15 * inch
    
    # Dirección del emisor
    if direccion:
        c.setFont("Helvetica", 8)
        c.drawString(margen_izq, y, direccion)
        y -= 0.15 * inch

    # Fecha de emisión
    if fecha_emision:
        try:
            fecha_str = fecha_emision.strftime('%d-%m-%Y')
        except:
            fecha_str = str(fecha_emision)
        c.setFont("Helvetica", 9)
        c.drawString(margen_izq, y, f"Fecha Emisión: {fecha_str}")
    y -= 0.3 * inch

    # --- TIPO DE COMPROBANTE Y NCF (En la derecha, como el ejemplo) ---
    # Guardar posición Y para el bloque derecho
    y_comprobante = margen_top
    
    c.setFont("Helvetica-Bold", 11)
    tipo_nombre = obtener_nombre_tipo_ecf(tipo_ecf)
    
    # Bloque de comprobante en la derecha con borde
    block_width = 3.2 * inch
    block_height = 0.85 * inch
    block_x = width - margen_izq - block_width
    
    c.setStrokeColor(primary)
    c.setLineWidth(1.5)
    c.rect(block_x, y_comprobante - block_height, block_width, block_height, stroke=1, fill=0)
    
    # Texto del tipo de comprobante
    c.setFont("Helvetica-Bold", 10)
    # Dividir el texto en líneas si es muy largo
    if len(tipo_nombre) > 40:
        c.drawString(block_x + 0.1 * inch, y_comprobante - 0.25 * inch, tipo_nombre[:40])
        c.drawString(block_x + 0.1 * inch, y_comprobante - 0.42 * inch, tipo_nombre[40:])
    else:
        c.drawString(block_x + 0.1 * inch, y_comprobante - 0.3 * inch, tipo_nombre)
    
    c.setFont("Helvetica", 9)
    c.drawString(block_x + 0.1 * inch, y_comprobante - 0.65 * inch, f"e-NCF: {encf}")
    
    # Fecha de vencimiento si existe
    if fecha_emision:
        try:
            fecha_str = fecha_emision.strftime('%d-%m-%Y')
        except:
            fecha_str = str(fecha_emision)
        c.setFont("Helvetica", 8)
        c.drawString(block_x + 0.1 * inch, y_comprobante - 0.8 * inch, f"Fecha Vencimiento: {fecha_str}")

    # Ajustar y para estar debajo del bloque de comprobante antes de la línea
    # El bloque tiene 0.85 inch de altura, así que la línea debe ir después
    y_after_block = y_comprobante - block_height - 0.15 * inch
    # Siempre usar la posición después del bloque para la línea
    y = y_after_block
    
    # Línea separadora horizontal (después del bloque)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(margen_izq, y, width - margen_izq, y)
    y -= 0.25 * inch
    
    # --- DATOS DEL CLIENTE ---
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margen_izq, y, "Razón Social Cliente:")
    c.setFont("Helvetica", 8)
    c.drawString(margen_izq + 1.5 * inch, y, razon_social_comprador)
    y -= 0.18 * inch
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margen_izq, y, "RNC Cliente:")
    c.setFont("Helvetica", 8)
    c.drawString(margen_izq + 1.5 * inch, y, rnc_comprador)
    y -= 0.3 * inch

    # --- TABLA DE DETALLES ---
    # Encabezado de tabla con fondo de color
    table_width = 6.5 * inch
    c.setFillColor(primary)
    c.rect(margen_izq, y - 0.05 * inch, table_width, 0.22 * inch, stroke=0, fill=1)
    
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.white)
    c.drawString(margen_izq + 0.05 * inch, y + 0.02 * inch, "Cantidad")
    c.drawString(margen_izq + 0.75 * inch, y + 0.02 * inch, "Descripción")
    c.drawString(margen_izq + 3.0 * inch, y + 0.02 * inch, "Unidad")
    c.drawString(margen_izq + 3.8 * inch, y + 0.02 * inch, "Precio")
    c.drawString(margen_izq + 4.75 * inch, y + 0.02 * inch, "ITBIS")
    c.drawString(margen_izq + 5.7 * inch, y + 0.02 * inch, "Valor")
    c.setFillColor(colors.black)
    y -= 0.25 * inch

    # Detalles de items
    c.setFont("Helvetica", 8)
    for detalle in detalles:
        # detalle es ahora un diccionario
        
        # Obtener cantidad
        cantidad = 0.0
        for col_name in ['CantidadItem', 'Cantidad', 'cantidad']:
            if col_name in detalle:
                cantidad = to_float(detalle.get(col_name))
                break
        
        # Obtener descripción
        descripcion = ""
        for col_name in ['DescripcionItem', 'Descripcion', 'descripcion', 'NombreItem']:
            if col_name in detalle and detalle[col_name] is not None:
                try:
                    descripcion = str(detalle[col_name]).strip()
                    if descripcion:
                        break
                except (AttributeError, TypeError):
                    pass
        
        # Obtener unidad de medida
        unidad = ""
        for col_name in ['UnidadMedida', 'unidad', 'UnidadReferencia']:
            if col_name in detalle and detalle[col_name] is not None:
                try:
                    unidad = str(detalle[col_name]).strip()
                    if unidad:
                        break
                except (AttributeError, TypeError):
                    pass
        
        # Obtener precio unitario
        precio = 0.0
        for col_name in ['PrecioUnitarioItem', 'PrecioUnitario', 'precio']:
            if col_name in detalle:
                precio = to_float(detalle.get(col_name))
                break
        
        # Obtener valor/monto
        valor = 0.0
        for col_name in ['MontoItem', 'Monto', 'valor', 'total']:
            if col_name in detalle:
                valor = to_float(detalle.get(col_name))
                break
        
        # ITBIS - obtener del campo MontoITBIS o MontoImpuesto de la base de datos
        itbis = 0.0
        for col_name in ['MontoITBIS', 'MontoImpuesto', 'ITBIS', 'itbis']:
            if col_name in detalle:
                itbis = to_float(detalle.get(col_name))
                break

        c.drawString(margen_izq + 0.05 * inch, y, f"{cantidad:.0f}")
        
        # Descripción con wrap si es muy larga
        if len(descripcion) > 45:
            descripcion = descripcion[:42] + "..."
        c.drawString(margen_izq + 0.75 * inch, y, descripcion)
        
        c.drawString(margen_izq + 3.0 * inch, y, unidad)
        c.drawRightString(margen_izq + 4.6 * inch, y, f"{precio:,.2f}")
        c.drawRightString(margen_izq + 5.5 * inch, y, f"{itbis:,.2f}")
        c.drawRightString(margen_izq + 6.85 * inch, y, f"{valor:,.2f}")

        y -= 0.2 * inch
        
        if y < 2 * inch:  # Nueva página si no hay espacio
            c.showPage()
            y = margen_top

    # --- TOTALES ---
    y -= 0.25 * inch

    # Obtener montos del encabezado de forma segura
    monto_total = to_float(encabezado.get('MontoTotal'))
    total_itbis = to_float(encabezado.get('TotalITBIS'))
    subtotal = monto_total - total_itbis
    total = monto_total

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(margen_izq + 5.5 * inch, y, "Subtotal Gravado:")
    c.setFont("Helvetica", 9)
    c.drawRightString(margen_izq + 6.85 * inch, y, f"{subtotal:,.2f}")
    y -= 0.18 * inch

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(margen_izq + 5.5 * inch, y, "Total ITBIS:")
    c.setFont("Helvetica", 9)
    c.drawRightString(margen_izq + 6.85 * inch, y, f"{total_itbis:,.2f}")
    y -= 0.18 * inch

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(margen_izq + 5.5 * inch, y, "Total:")
    c.setFont("Helvetica", 9)
    c.drawRightString(margen_izq + 6.85 * inch, y, f"{total:,.2f}")
    y -= 0.4 * inch

    # --- QR CODE Y CÓDIGO DE SEGURIDAD ---
    qr_size = 1.3 * inch
    if url_qr and len(url_qr) > 10:  # Verificar que sea una URL válida
        try:
            # Generar QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(url_qr)
            qr.make(fit=True)
            
            # Crear imagen PIL
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar en buffer como PNG
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Dibujar QR en el PDF (parte inferior izquierda)
            c.drawImage(qr_buffer, margen_izq, y - qr_size, width=qr_size, height=qr_size, preserveAspectRatio=True, mask='auto')
            
            logger.info(f"QR code generado exitosamente desde URL: {url_qr[:50]}...")
        except Exception as e:
            logger.error(f"Error generando QR con URL '{url_qr}': {str(e)}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            logger.error(f"Stack trace:", exc_info=True)
            # Dibujar un cuadro en su lugar indicando error
            c.setStrokeColor(colors.red)
            c.rect(margen_izq, y - qr_size, qr_size, qr_size)
            c.setFont("Helvetica", 7)
            c.drawString(margen_izq + 0.1 * inch, y - qr_size/2, "Error QR")
    else:
        logger.warning(f"URL QR no válida o vacía: '{url_qr}'")
        # Dibujar un cuadro indicando que no hay URL
        c.setStrokeColor(colors.gray)
        c.rect(margen_izq, y - qr_size, qr_size, qr_size)
        c.setFont("Helvetica", 7)
        c.drawString(margen_izq + 0.1 * inch, y - qr_size/2, "Sin URL QR")

    # Código de seguridad y fecha de firma (a la derecha del QR)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    text_x = margen_izq + qr_size + 0.3 * inch
    c.drawString(text_x, y - 0.5 * inch, f"Código de Seguridad: {codigo_seguridad}")
    
    if fecha_firma:
        try:
            fecha_firma_str = fecha_firma.strftime('%d-%m-%Y %H:%M:%S')
        except:
            fecha_firma_str = str(fecha_firma)
        c.drawString(text_x, y - 0.7 * inch, f"Fecha Firma: {fecha_firma_str}")

    # Nota legal
    y -= 1.6 * inch
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(colors.grey)
    c.drawString(margen_izq, y, "*Este modelo de RI es exclusivo para fines ilustrativos.")
    c.setFillColor(colors.black)

    c.save()
    return buffer


def obtener_nombre_tipo_ecf(tipo_ecf):
    """Retorna el nombre completo del tipo de eCF"""
    tipos = {
        "31": "Factura de Crédito Fiscal Electrónica",
        "32": "Factura de Consumo Electrónica",
        "33": "Nota de Débito Electrónica",
        "34": "Nota de Crédito Electrónica",
        "41": "Compras Electrónicas",
        "43": "Gastos Menores Electrónicos",
        "44": "Regímenes Especiales Electrónicos",
        "45": "Gubernamental Electrónico",
        "46": "Exportaciones Electrónicas",
        "47": "Pagos al Exterior Electrónicos"
    }
    return tipos.get(tipo_ecf, f"Comprobante Fiscal Electrónico e-{tipo_ecf}")
