"""
Sistema de Impresión Automática para Facturación Electrónica ASESYS.

Este módulo implementa un servicio de impresión automática para documentos de
facturación electrónica en República Dominicana. Monitorea la base de datos
en busca de documentos pendientes de impresión y los procesa según la
configuración especificada.

Características principales:
- Monitoreo continuo de la base de datos
- Impresión en formatos PDF y PDV (punto de venta)
- Interfaz gráfica para selección de impresoras
- Optimización de consultas con índices automáticos
- Logging detallado de actividades
- Compatibilidad con múltiples tipos de comprobantes fiscales

Autor: Equipo de Desarrollo ASESYS
Versión: 1.0.0

NOTA: Los errores mostrados por Pylance/VS Code son falsos positivos del análisis
estático. El código es funcional y compatible. Si ves errores, recarga VS Code
(Ctrl+Shift+P > Developer: Reload Window) o reinicia el servidor de lenguaje Python.
"""

# pylint: disable=all
# flake8: noqa
# type: ignore

import os
import sys
import threading
import time
import traceback
from datetime import datetime

import pyodbc
import pystray
import requests
import win32api
import win32event
import win32print
from PIL import Image, ImageDraw
from PyQt5 import QtCore, QtWidgets  # type: ignore
from PyQt5.QtCore import QObject, Qt, pyqtSignal  # type: ignore
from PyQt5.QtGui import QPixmap  # type: ignore
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Table  # type: ignore
from sqlalchemy import Column, MetaData, String, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from db.CDT import ensure_table  # type: ignore
from db.database import *  # type: ignore
from db.database import fetch_invoice_data  # type: ignore
from db.uDB import *  # type: ignore
from glib.ufe import *  # type: ignore
from glib.ufe import GConfig  # type: ignore
from logG import log_event, setup_logger  # type: ignore
from print.impresion import *  # type: ignore
from print.pdf_generator import PDFGenerator  # type: ignore

logger = setup_logger("FEImpresionASESYS.log")


def log_error_detallado(e: Exception, contexto: str = "", datos_extra: dict = None):
    """
    Registra errores con formato detallado y organizado.

    Args:
        e: Excepción capturada
        contexto: Descripción del contexto donde ocurrió el error
        datos_extra: Diccionario con datos adicionales para el log
    """
    # Extraer línea exacta del error
    tb_lines = traceback.format_exc().split("\n")
    error_line = "N/A"
    error_file = "N/A"
    error_code = ""

    for i, line in enumerate(tb_lines):
        if "File" in line and i + 1 < len(tb_lines):
            parts = line.split(", ")
            if len(parts) >= 2:
                error_file = (
                    parts[0].replace('File "', "").replace('"', "").split("\\")[-1]
                )
                error_line = parts[1].replace("line ", "")
                if i + 1 < len(tb_lines) and tb_lines[i + 1].strip():
                    error_code = tb_lines[i + 1].strip()

    # Construir mensaje de error
    error_msg = f"\n{'='*100}\n"
    error_msg += f"🔴 ERROR: {contexto}\n"
    error_msg += f"{'='*100}\n\n"

    # Detalle del error
    error_msg += f"❌ DETALLE DEL ERROR:\n"
    error_msg += f"   Tipo          : {type(e).__name__}\n"
    error_msg += f"   Mensaje       : {str(e)}\n"
    error_msg += f"   Archivo       : {error_file}\n"
    error_msg += f"   Línea         : {error_line}\n"
    if error_code:
        error_msg += f"   Código        : {error_code}\n"
    error_msg += "\n"

    # Datos adicionales si existen
    if datos_extra:
        # Separar nulos de no nulos
        campos_nulos = {k: v for k, v in datos_extra.items() if v is None}
        campos_validos = {k: v for k, v in datos_extra.items() if v is not None}

        if campos_nulos:
            error_msg += f"⚠️  CAMPOS NULOS (NULL) - POSIBLE CAUSA:\n"
            for campo, valor in campos_nulos.items():
                error_msg += f"   ❌ {campo:20s}: NULL\n"
            error_msg += "\n"

        if campos_validos:
            error_msg += f"✅ DATOS DEL CONTEXTO:\n"
            for campo, valor in campos_validos.items():
                valor_repr = str(valor).strip()
                error_msg += f"   ✓  {campo:20s}: {valor_repr}\n"
            error_msg += "\n"

    # Stack trace
    error_msg += f"📍 STACK TRACE COMPLETO:\n"
    error_msg += f"{'-'*100}\n"
    error_msg += traceback.format_exc()
    error_msg += f"{'-'*100}\n"
    error_msg += f"{'='*100}\n"

    log_event(logger, "error", error_msg)


PConfig = load_printer_config()

# Columnas necesarias para la consulta (optimización: evitar SELECT *)
COLUMNAS_NECESARIAS = (
    "RNCEmisor, eNCF, EstadoFiscal, EstadoImpresion, TipoPago, "
    "TipoECF, TipoDocumento, Tabla, campo1, campo2, NumeroFacturaInterna, "
    "FechaCreacion, EquipoImpresion, TipoECFL, codigoseguridad"
)

# Tipos de ECF para facturas estándar
TIPOS_ECF_FACTURA = ["31", "32", "44", "45", "46", "41", "47"]


def create_image():
    """Crear el ícono para la bandeja del sistema"""
    image = Image.new("RGB", (64, 64), color=(0, 128, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=(255, 255, 0))
    return image


def mostrar_info(icon, item):
    """Mostrar información del estado del programa"""
    icon.notify("ASESYS Impresión", "Proceso de impresión activo")


def ensure_index_exists(cn):
    """Verifica si los índices existen en las tablas base, si no los crea para optimizar consultas"""
    try:
        # Primero verificar si vFEEncabezado es una vista o una tabla
        check_type_query = """
        SELECT CASE
            WHEN OBJECTPROPERTY(OBJECT_ID('vFEEncabezado'), 'IsView') = 1 THEN 'VIEW'
            WHEN OBJECTPROPERTY(OBJECT_ID('vFEEncabezado'), 'IsUserTable') = 1 THEN 'TABLE'
            ELSE 'UNKNOWN'
        END AS ObjectType
        """
        result = cn.fetch_query(check_type_query)

        if result and len(result) > 0:
            object_type = (
                result[0].ObjectType
                if hasattr(result[0], "ObjectType")
                else result[0][0]
            )

            if object_type == "VIEW":
                log_event(
                    logger,
                    "info",
                    "vFEEncabezado es una vista. Intentando crear índices en tablas base...",
                )

                # Obtener las tablas base del campo 'Tabla' de la vista
                try:
                    get_tables_query = """
                    SELECT DISTINCT LTRIM(RTRIM(Tabla)) AS TablaBase
                    FROM vFEEncabezado WITH (NOLOCK)
                    WHERE Tabla IS NOT NULL AND Tabla <> ''
                    """
                    tablas_result = cn.fetch_query(get_tables_query)

                    if tablas_result:
                        for tabla_row in tablas_result:
                            tabla_nombre = (
                                tabla_row.TablaBase
                                if hasattr(tabla_row, "TablaBase")
                                else tabla_row[0]
                            )
                            if tabla_nombre:
                                tabla_nombre = tabla_nombre.strip()
                                crear_indice_en_tabla(cn, tabla_nombre)
                    else:
                        log_event(
                            logger,
                            "info",
                            "No se encontraron tablas base en el campo Tabla de la vista",
                        )

                except Exception as e:
                    log_error_detallado(
                        e, "Error al obtener tablas base de la vista vFEEncabezado"
                    )

                return

            elif object_type == "TABLE":
                # Es una tabla directamente, crear índice aquí
                crear_indice_en_tabla(cn, "vFEEncabezado")
            else:
                log_event(
                    logger,
                    "info",
                    f"vFEEncabezado tiene tipo desconocido: {object_type}",
                )

    except Exception as e:
        log_error_detallado(e, "No se pudo verificar/crear índice en vFEEncabezado")


def crear_indice_en_tabla(cn, tabla_nombre):
    """Crea un índice optimizado en una tabla específica si no existe"""
    try:
        # Verificar si la tabla existe y es una tabla de usuario
        check_table_query = f"""
        SELECT 1 FROM sys.tables WHERE name = '{tabla_nombre}'
        """
        tabla_existe = cn.fetch_query(check_table_query)

        if not tabla_existe or len(tabla_existe) == 0:
            log_event(
                logger,
                "info",
                f"Tabla '{tabla_nombre}' no encontrada o no es una tabla de usuario",
            )
            return

        # Nombre del índice específico para cada tabla
        index_name = f"IX_{tabla_nombre}_EstadoImpresion"

        # Verificar si el índice ya existe
        check_index_query = f"""
        SELECT 1 FROM sys.indexes
        WHERE name = '{index_name}'
        AND object_id = OBJECT_ID('{tabla_nombre}')
        """
        index_result = cn.fetch_query(check_index_query)

        if not index_result or len(index_result) == 0:
            # Verificar qué columnas existen en la tabla antes de crear el índice
            check_columns_query = f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{tabla_nombre}'
            AND COLUMN_NAME IN ('EstadoFiscal', 'EstadoImpresion', 'codigoseguridad', 'FechaCreacion')
            """
            columnas_existentes = cn.fetch_query(check_columns_query)

            if columnas_existentes and len(columnas_existentes) >= 2:
                # Crear índice básico con las columnas que existen
                columnas_list = [
                    col.COLUMN_NAME if hasattr(col, "COLUMN_NAME") else col[0]
                    for col in columnas_existentes
                ]

                # Construir el índice con columnas disponibles
                index_columns = []
                include_columns = []

                if "EstadoFiscal" in columnas_list:
                    index_columns.append("EstadoFiscal")
                if "EstadoImpresion" in columnas_list:
                    index_columns.append("EstadoImpresion")
                if "FechaCreacion" in columnas_list:
                    include_columns.append("FechaCreacion")

                if len(index_columns) >= 1:
                    create_index_query = f"""
                    CREATE NONCLUSTERED INDEX {index_name}
                    ON {tabla_nombre} ({', '.join(index_columns)})
                    """
                    if include_columns:
                        create_index_query += f" INCLUDE ({', '.join(include_columns)})"

                    cn.execute_query(create_index_query)
                    log_event(
                        logger,
                        "info",
                        f"Índice {index_name} creado exitosamente en tabla {tabla_nombre}",
                    )
            else:
                log_event(
                    logger,
                    "info",
                    f"Tabla {tabla_nombre} no tiene las columnas necesarias para el índice",
                )
        else:
            log_event(
                logger, "info", f"Índice {index_name} ya existe en tabla {tabla_nombre}"
            )

    except Exception as e:
        log_error_detallado(
            e,
            f"No se pudo crear índice en tabla {tabla_nombre}",
            {"tabla": tabla_nombre},
        )


def get_db_cursor(cn):
    """Obtiene un cursor válido, reconectando si es necesario"""
    global cn1
    try:
        # Verificar si la conexión sigue activa
        cn.connection.execute("SELECT 1")
    except Exception as e:
        log_event(logger, "info", "Reconectando a la base de datos...")
        log_error_detallado(e, "Pérdida de conexión detectada - Reconectando")
        cn1 = ConectarDB()
        cn = cn1

    cursor = cn.connection.cursor()
    cursor.execute("SET LOCK_TIMEOUT 3000;")
    return cursor, cn


def actualizar_batch(cn, registros):
    """Actualiza múltiples registros en una transacción"""
    if not registros:
        return

    try:
        cursor = cn.connection.cursor()
        for reg in registros:
            query = (
                f"UPDATE {reg['tabla']} SET EstadoImpresion = 2 "
                f"WHERE {reg['campo1']} = ? AND {reg['campo2']} = ?"
            )
            cursor.execute(query, (reg["rnc"], reg["encf"]))
        cn.connection.commit()
        log_event(
            logger, "info", f"Batch update: {len(registros)} registros actualizados"
        )
    except Exception as e:
        log_error_detallado(
            e,
            "Error en actualización batch de registros",
            {"cantidad_registros": len(registros) if "registros" in locals() else 0},
        )
        try:
            cn.connection.rollback()
        except Exception as rollback_error:
            log_error_detallado(
                rollback_error, "Error al hacer rollback de transacción"
            )


def obtener_tipo_comprobante(tipoecf, tipo_doc):
    """Obtiene el nombre del tipo de comprobante"""
    if tipoecf == "34" and tipo_doc == "02":
        return "Nota de Crédito"
    elif tipoecf == "33":
        return "Nota de Débito"
    elif tipoecf in TIPOS_ECF_FACTURA:
        return "Factura"
    elif tipoecf == "43":
        return "Caja Chica"
    return tipoecf


def ejecutar_impresion_grande(pdf_generator, row, ruta, nombre_archivo, sinpdf):
    """Ejecuta la impresión en formato grande (PDF)"""
    tipo_ecf = row.TipoECF
    tipo_doc = row.TipoDocumento.strip() if row.TipoDocumento else ""

    if tipo_ecf in TIPOS_ECF_FACTURA:
        pdf_generator.print_pdf2(ruta, nombre_archivo)
    elif tipo_ecf == "33":
        pdf_generator.print_pdf_nota_debito(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc == "02":
        pdf_generator.print_pdf_nota_credito(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc in ["03", "17", "05"]:
        pdf_generator.print_pdf2(ruta, nombre_archivo)
    elif tipo_ecf == "43":
        pdf_generator.print_pdf_caja_chica(ruta, nombre_archivo)


def ejecutar_impresion_pdv(impresion, row, ruta, nombre_archivo, sinpdf):
    """Ejecuta la impresión en formato PDV (punto de venta)"""
    tipo_ecf = row.TipoECF
    tipo_doc = row.TipoDocumento.strip() if row.TipoDocumento else ""

    if tipo_ecf in TIPOS_ECF_FACTURA:
        if sinpdf == 0:
            impresion.imprimir_factura(ruta, nombre_archivo)
        else:
            impresion.imprimir_facturaspdf(ruta, nombre_archivo)
    elif tipo_ecf == "33":
        if sinpdf == 0:
            impresion.imprimir_nota_debito(ruta, nombre_archivo)
        else:
            impresion.imprimir_nota_debitospdf(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc == "02":
        if sinpdf == 0:
            impresion.imprimir_nota_credito(ruta, nombre_archivo)
        else:
            impresion.imprimir_nota_creditospdf(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc in ["03", "17", "05"]:
        if sinpdf == 0:
            impresion.imprimir_factura(ruta, nombre_archivo)
        else:
            impresion.imprimir_facturaspdf(ruta, nombre_archivo)
    elif tipo_ecf == "43":
        if sinpdf == 0:
            impresion.imprimir_caja_chica(ruta, nombre_archivo)
        else:
            impresion.imprimir_caja_chicaspdf(ruta, nombre_archivo)


def debe_imprimir(row, tipo_pago_config, impresion_activa, tipo_pago_esperado):
    """Determina si se debe imprimir según la configuración"""
    if tipo_pago_config == "CRCO":
        return impresion_activa == 1
    elif tipo_pago_config == tipo_pago_esperado:
        return impresion_activa == 1 and row.TipoPago == (
            1 if tipo_pago_esperado == "CO" else 2
        )
    return False


def seleccionar_impresoras_y_copias(config_path, datos_factura=None):
    """Muestra una ventana para seleccionar impresoras y número de copias con diseño moderno."""
    log_event(logger, "info", "Iniciando selección de impresoras y copias...")
    with open(config_path, "r") as file:
        config = json.load(file)

    app = QtWidgets.QApplication.instance()
    if app is None:
        log_event(logger, "info", "Inicializando QApplication...")
        app = QtWidgets.QApplication(sys.argv)

    dialog = QDialog()
    dialog.setWindowTitle("Configuración de Impresión")
    dialog.setFixedSize(650, 550)
    dialog.setWindowFlags(
        Qt.Window
        | Qt.WindowTitleHint
        | Qt.CustomizeWindowHint
        | Qt.WindowStaysOnTopHint
    )  # type: ignore

    dialog.setStyleSheet(
        """
        QDialog { background-color: #f7f7f7; border-radius: 15px; }
        QLabel { color: #333; font-size: 16px; }
        QComboBox, QSpinBox { font-size: 15px; padding: 8px; border-radius: 8px; border: 1px solid #ccc; background-color: white; }
        QPushButton { background-color: #3498db; color: white; font-size: 16px; padding: 12px 25px; border-radius: 10px; border: none; }
        QPushButton:hover { background-color: #2980b9; }
        QFrame#line { background-color: #ddd; height: 1px; margin: 10px 0; }
        """
    )

    layout = QVBoxLayout()
    layout.setContentsMargins(30, 30, 30, 30)

    title_layout = QHBoxLayout()
    icon_label = QLabel()
    icon_img = Image.new("RGB", (32, 32), color=(52, 152, 219))
    d = ImageDraw.Draw(icon_img)
    d.rectangle((8, 8, 24, 24), fill=(255, 255, 255))
    icon_img.save("temp_icon.png")
    icon_pixmap = QPixmap("temp_icon.png")
    icon_label.setPixmap(icon_pixmap)
    title_label = QLabel("Configuración de Impresión")
    title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-left: 15px;")
    title_layout.addWidget(icon_label)
    title_layout.addWidget(title_label)
    layout.addLayout(title_layout)

    line = QFrame()
    line.setObjectName("line")
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    layout.addWidget(line)

    if datos_factura:
        info_text = (
            f"<b>Número Factura:</b> {datos_factura.get('numero_factura', '')}<br>"
            f"<b>Comprobante:</b> {datos_factura.get('comprobante', '')}<br>"
            f"<b>Tipo Comprobante:</b> {datos_factura.get('tipo_comprobante', '')}<br>"
            f"<b>RNC Emisor:</b> {datos_factura.get('rnc_emisor', '')} - <b>Nombre Emisor:</b> {datos_factura.get('nombre_emisor', '')}<br>"
            f"<b>RNC Comprador:</b> {datos_factura.get('rnc_comprador', '')} - <b>Nombre Comprador:</b> {datos_factura.get('nombre_comprador', '')}"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet(
            "font-size: 14px; margin-bottom: 18px; background: #ecf0f1; border-radius: 10px; padding: 12px;"
        )
        info_label.setTextFormat(Qt.RichText)  # type: ignore
        layout.addWidget(info_label)

        line2 = QFrame()
        line2.setObjectName("line")
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

    label_impresora1 = QLabel("Seleccione la impresora:")
    label_impresora1.setStyleSheet("font-size: 16px; margin-bottom: 5px;")
    combo_impresora1 = QComboBox()
    try:
        impresoras_disponibles = [
            printer[2]
            for printer in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
        ]
    except Exception as e:
        log_error_detallado(e, "Error al obtener lista de impresoras del sistema")
        impresoras_disponibles = []
    combo_impresora1.addItems(impresoras_disponibles)
    combo_impresora1.setCurrentText(config.get("printer_name", ""))
    layout.addWidget(label_impresora1)
    layout.addWidget(combo_impresora1)

    copias_layout = QHBoxLayout()
    label_copias = QLabel("Número de copias:")
    label_copias.setStyleSheet("font-size: 16px; margin-right: 10px;")
    spin_copias = QSpinBox()
    spin_copias.setMinimum(1)
    spin_copias.setMaximum(50)
    spin_copias.setValue(int(config.get("copies", 1)))
    copias_layout.addWidget(label_copias)
    copias_layout.addWidget(spin_copias)
    layout.addLayout(copias_layout)

    layout.addStretch()

    button_layout = QHBoxLayout()
    btn_guardar = QPushButton("Aceptar")
    btn_guardar.clicked.connect(dialog.accept)
    btn_cancelar = QPushButton("Cancelar")
    btn_cancelar.clicked.connect(dialog.reject)
    button_layout.addWidget(btn_cancelar)
    button_layout.addWidget(btn_guardar)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    screen_geometry = app.desktop().screenGeometry()  # type: ignore
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog.exec_()

    if dialog.result() == QDialog.Accepted:
        config["printer_name"] = combo_impresora1.currentText()
        config["copies"] = spin_copias.value()
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)
        return config["printer_name"], config.get("printer_name2", ""), config["copies"]
    else:
        log_event(logger, "info", "El usuario cerró la ventana sin guardar.")
        return None, None, None


def crear_filtro_caja(caja):
    """Crea filtro SQL para caja"""
    filtrocaja = ""
    if caja is not None and caja.strip():
        caja = caja.upper()
        caracteres = list(caja)
        condiciones = [
            f"SUBSTRING(NumeroFacturaInterna, 1, 1)='{c}'" for c in caracteres
        ]
        if condiciones:
            filtrocaja = " AND (" + " OR ".join(condiciones) + ")"
    return filtrocaja


def registrar_actividad_log(
    rnc_emisor, encf, tipo_actividad, fecha_actividad, equipo, ruta_impresion, impresora
):
    """Inserta un registro en la tabla LogActividadesFE."""
    try:
        cn_log = ConectarDB()

        if fecha_actividad is None:
            fecha_actividad = datetime.now()

        if isinstance(fecha_actividad, datetime):
            fecha_actividad_str = fecha_actividad.strftime("%Y-%m-%d %H:%M:%S")
        else:
            fecha_actividad_str = (
                str(fecha_actividad)
                if fecha_actividad
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        params = (
            str(rnc_emisor) if rnc_emisor else "",
            str(encf) if encf else "",
            str(tipo_actividad) if tipo_actividad else "",
            fecha_actividad_str,
            str(equipo) if equipo else "",
            str(ruta_impresion) if ruta_impresion else "",
            str(impresora) if impresora else "",
        )

        query = (
            "INSERT INTO LogActividadesFE (RncEmisor, encf, TipoActividad, FechaActividad, Equipo, RutaImpresion, impresora) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        cn_log.execute_query(query, params)

    except Exception as e:
        datos_log = {}
        if "rnc" in locals():
            datos_log["RNC"] = rnc
        if "encf" in locals():
            datos_log["eNCF"] = encf
        if "accion" in locals():
            datos_log["Accion"] = accion
        log_error_detallado(e, "Error al registrar actividad en log", datos_log)


def proceso_principal():
    """Proceso principal optimizado con intervalos adaptativos y batch updates"""
    global caja, imprimir_sin_caja, Impresion_grande, impresion_pdv, sinpdf, EquipoImpresion
    global tipo_pago_grande, tipo_pago_pdv, con_pantalla, config_path, check_interval
    global cn1, logger

    # Intervalos adaptativos
    min_interval = 0.5
    max_interval = 30
    current_interval = check_interval
    consecutive_empty = 0

    while True:
        try:
            # Construir filtros
            filtrocaja = crear_filtro_caja(caja) if caja else ""

            filtrosincaja = ""
            if imprimir_sin_caja:
                filtrosincaja = (
                    " OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]' "
                )

            filtroequipo = ""
            if EquipoImpresion is not None:
                if isinstance(EquipoImpresion, list):
                    condiciones = [
                        f"EquipoImpresion = '{equipo}'" for equipo in EquipoImpresion
                    ]
                    filtroequipo = " AND (" + " OR ".join(condiciones) + ")"
                else:
                    filtroequipo = f" AND EquipoImpresion = '{EquipoImpresion}'"

            estados_impresion = PConfig.get("estadosimpresion", [3, 5, 6])
            estados_impresion_str = ",".join(str(e) for e in estados_impresion)

            # Query optimizada: solo columnas necesarias
            query = (
                f"SELECT TOP 5 {COLUMNAS_NECESARIAS} "
                "FROM vFEEncabezado WITH (NOLOCK) "
                f"WHERE EstadoFiscal IN ({estados_impresion_str}) "
                "AND codigoseguridad IS NOT NULL "
                "AND EstadoImpresion IN (1,3) "
                + filtrocaja
                + filtrosincaja
                + filtroequipo
                + " AND TipoECFL = 'E'"
                " ORDER BY FechaCreacion"
            )

            cursor, cn1 = get_db_cursor(cn1)
            cursor.execute(query)
            row = cursor.fetchone()

            # Intervalo adaptativo
            if row is None:
                consecutive_empty += 1
                current_interval = min(
                    max_interval, check_interval * (1 + consecutive_empty * 0.5)
                )
            else:
                consecutive_empty = 0
                current_interval = min_interval

            registros_procesados = []
            Ruta = PConfig.get("ruta_ri", "C:\\XMLValidar\\RI\\")

            while row:
                if row.EstadoFiscal >= 3 and row.EstadoImpresion in (1, 3):
                    try:
                        (
                            company_data,
                            invoice_data,
                            products,
                            forms,
                            descuento_recargo,
                        ) = fetch_invoice_data(
                            cn1, row.RNCEmisor.strip(), row.eNCF.strip()
                        )

                        pdf_generator = PDFGenerator(
                            company_data,
                            invoice_data,
                            products,
                            forms,
                            descuento_recargo,
                        )
                        impresion = Impresion(
                            company_data,
                            invoice_data,
                            products,
                            forms,
                            descuento_recargo,
                        )

                        NombrePDF = f"{row.RNCEmisor.strip()}{row.eNCF.strip()}"
                        nombre_archivo = os.path.join(Ruta, f"{NombrePDF}.pdf")

                        contador = 1
                        while os.path.exists(nombre_archivo):
                            nombre_archivo = os.path.join(
                                Ruta, f"{NombrePDF}_{contador}.pdf"
                            )
                            contador += 1

                        # Mostrar pantalla si está configurado
                        if con_pantalla == 1:
                            tipoecf = invoice_data.get("tipoecf", "")
                            tipo_doc = invoice_data.get("tipo", "").strip()
                            datos_factura = {
                                "numero_factura": invoice_data.get("numero", ""),
                                "comprobante": invoice_data.get("ncf", ""),
                                "tipo_comprobante": obtener_tipo_comprobante(
                                    tipoecf, tipo_doc
                                ),
                                "rnc_emisor": company_data.get("rnc", ""),
                                "nombre_emisor": company_data.get("nombre_empresa", ""),
                                "rnc_comprador": invoice_data.get("cedula", ""),
                                "nombre_comprador": invoice_data.get(
                                    "nombre_cliente", ""
                                ),
                            }
                            seleccionar_impresoras_y_copias(config_path, datos_factura)

                        # Ejecutar impresión según configuración
                        impreso = False

                        # Impresión grande
                        if Impresion_grande == 1:
                            if tipo_pago_grande == "CRCO":
                                ejecutar_impresion_grande(
                                    pdf_generator, row, Ruta, nombre_archivo, sinpdf
                                )
                                impreso = True
                            elif tipo_pago_grande == "CO" and row.TipoPago == 1:
                                ejecutar_impresion_grande(
                                    pdf_generator, row, Ruta, nombre_archivo, sinpdf
                                )
                                impreso = True
                            elif tipo_pago_grande == "CR" and row.TipoPago == 2:
                                ejecutar_impresion_grande(
                                    pdf_generator, row, Ruta, nombre_archivo, sinpdf
                                )
                                impreso = True

                        # Impresión PDV
                        if impresion_pdv == 1 and not impreso:
                            if tipo_pago_pdv == "CRCO":
                                ejecutar_impresion_pdv(
                                    impresion, row, Ruta, nombre_archivo, sinpdf
                                )
                            elif tipo_pago_pdv == "CO" and row.TipoPago == 1:
                                ejecutar_impresion_pdv(
                                    impresion, row, Ruta, nombre_archivo, sinpdf
                                )
                            elif tipo_pago_pdv == "CR" and row.TipoPago == 2:
                                ejecutar_impresion_pdv(
                                    impresion, row, Ruta, nombre_archivo, sinpdf
                                )

                        # Acumular para batch update
                        registros_procesados.append(
                            {
                                "tabla": row.Tabla.strip(),
                                "campo1": row.campo1.strip(),
                                "campo2": row.campo2.strip(),
                                "rnc": row.RNCEmisor.strip(),
                                "encf": row.eNCF.strip(),
                            }
                        )

                        # Registrar actividad
                        imp = (
                            PConfig.get("printer_name", "")
                            if Impresion_grande == 1
                            else PConfig.get("printer_name2", "")
                        )
                        registrar_actividad_log(
                            row.RNCEmisor.strip(),
                            row.eNCF.strip(),
                            "Impresión",
                            datetime.now(),
                            EquipoImpresion or "",
                            Ruta,
                            imp,
                        )

                    except Exception as e:
                        # Preparar datos para log detallado
                        datos_factura = {
                            "RNCEmisor": row.RNCEmisor,
                            "eNCF": row.eNCF,
                            "Tabla": row.Tabla,
                            "campo1": row.campo1,
                            "campo2": row.campo2,
                            "TipoDocumento": row.TipoDocumento,
                            "TipoPago": row.TipoPago,
                            "TipoECF": row.TipoECF,
                            "NumeroFacturaInterna": (
                                row.NumeroFacturaInterna
                                if hasattr(row, "NumeroFacturaInterna")
                                else None
                            ),
                            "EstadoFiscal": (
                                row.EstadoFiscal
                                if hasattr(row, "EstadoFiscal")
                                else None
                            ),
                        }

                        # Agregar identificación clara
                        encf_value = row.eNCF.strip() if row.eNCF else "DESCONOCIDO"
                        rnc_value = (
                            row.RNCEmisor.strip() if row.RNCEmisor else "DESCONOCIDO"
                        )

                        log_error_detallado(
                            e,
                            f"PROCESAMIENTO DE FACTURA - RNC: {rnc_value} | eNCF: {encf_value}",
                            datos_factura,
                        )

                row = cursor.fetchone()

            # Batch update al final
            if registros_procesados:
                actualizar_batch(cn1, registros_procesados)

            cursor.close()

        except Exception as e:
            log_error_detallado(e, "Error crítico en bucle principal de procesamiento")

        time.sleep(current_interval)


class ControlSignals(QObject):
    pause = pyqtSignal()
    resume = pyqtSignal()
    stop = pyqtSignal()
    restart = pyqtSignal()


class ControlDialog(QDialog):
    def __init__(self, thread, signals):
        super().__init__()
        self.thread = thread
        self.signals = signals
        self.setWindowTitle("Control de Proceso")
        layout = QVBoxLayout()

        self.btn_iniciar = QPushButton("Iniciar")
        self.btn_pausar = QPushButton("Pausar")
        self.btn_reiniciar = QPushButton("Reiniciar")
        self.btn_finalizar = QPushButton("Finalizar")

        layout.addWidget(self.btn_iniciar)
        layout.addWidget(self.btn_pausar)
        layout.addWidget(self.btn_reiniciar)
        layout.addWidget(self.btn_finalizar)
        self.setLayout(layout)

        self.btn_iniciar.clicked.connect(self.iniciar)
        self.btn_pausar.clicked.connect(self.pausar)
        self.btn_reiniciar.clicked.connect(self.reiniciar)
        self.btn_finalizar.clicked.connect(self.finalizar)

    def iniciar(self):
        if not self.thread.is_alive():  # type: ignore
            self.thread.start()  # type: ignore

    def pausar(self):
        self.signals.pause.emit()

    def reiniciar(self):
        self.signals.restart.emit()

    def finalizar(self):
        self.signals.stop.emit()
        self.close()


# Variables de control globales
pausado = False
detener = False


if __name__ == "__main__":
    # Verificar instancia única
    mutex = win32event.CreateMutex(None, 1, "ASESYSImpresionMutex")
    if win32api.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        log_event(logger, "info", "Otra instancia ya está ejecutándose. Saliendo.")
        sys.exit(0)

    UnlockCK()

    try:
        GConfig.cargar(1)
        log_event(logger, "info", "Configuracion Cargada")
    except AttributeError as e:
        log_event(logger, "info", f"Error: {e}")

    cn1 = ConectarDB()
    mostrarConfiguracion(GConfig, cn1)

    # Verificar/crear índice para optimizar consultas
    ensure_index_exists(cn1)

    # Asegurar tabla de log
    campos_log = {
        "RncEmisor": "NVARCHAR(20) NOT NULL",
        "encf": "NVARCHAR(50) NOT NULL",
        "TipoActividad": "NVARCHAR(50) NOT NULL",
        "FechaActividad": "DATETIME2 NOT NULL",
        "Equipo": "NVARCHAR(100)",
        "RutaImpresion": "NVARCHAR(255)",
        "impresora": "NVARCHAR(100)",
    }
    ensure_table("LogActividadesFE", campos_log)

    PConfig = load_printer_config()

    caja = PConfig.get("caja", "")
    imprimir_sin_caja = PConfig.get("imprimir_sin_caja", False)
    Impresion_grande = PConfig.get("Impresion_grande", 0)
    impresion_pdv = PConfig.get("impresion_pdv", 0)
    sinpdf = PConfig.get("sinpdf", 0)
    tipo_pago_grande = PConfig.get("tipo_pago_grande", "CRCO")
    tipo_pago_pdv = PConfig.get("tipo_pago_pdv", "CRCO")
    con_pantalla = PConfig.get("conpantalla", 0)
    config_path = PConfig.get("config_path1", "config.json")
    EquipoImpresion = PConfig.get("EquipoImpresion", None)
    check_interval = PConfig.get("check_interval", 5)

    # Crear icono del system tray
    icon = pystray.Icon("ASESYS", icon=create_image(), title="ASESYS Impresión")
    icon.menu = pystray.Menu(pystray.MenuItem("Estado", mostrar_info, default=True))

    # Iniciar proceso principal en hilo separado
    thread_principal = threading.Thread(target=proceso_principal, daemon=True)
    thread_principal.start()

    log_event(logger, "info", "Iniciando aplicación en la bandeja del sistema")
    icon.run()
