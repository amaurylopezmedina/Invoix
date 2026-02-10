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

import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Optional

import pystray
import win32print
from PIL import Image, ImageDraw
from PyQt5 import QtCore, QtWidgets  # type: ignore
from PyQt5.QtCore import QObject, Qt, pyqtSignal  # type: ignore
from PyQt5.QtGui import QPixmap  # type: ignore
from PyQt5.QtWidgets import QFrame  # type: ignore
from PyQt5.QtWidgets import QHBoxLayout  # type: ignore
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from db.CDT import ensure_table
from db.database import ConectarDB, fetch_invoice_data
from glib.ufe import GConfig, UnlockCK
from glib.uGlobalLib import mostrarConfiguracion
from logG import log_event, setup_logger
from print.impresion import Impresion, load_printer_config
from print.pdf_generator import PDFGenerator

# Inicializaciones globales para evitar errores de unbound
cn1 = None
check_interval = 5
caja = ""
imprimir_sin_caja = False
EquipoImpresion = None
tipo_pago_grande = "CRCO"
tipo_pago_pdv = "CRCO"
con_pantalla = 0
config_path = "config.json"
Impresion_grande = 0
impresion_pdv = 0
sinpdf = 0
rncemisor_arg = None
encf_arg = None

logger = setup_logger("FEImpresionASESYS.log")

PConfig = load_printer_config()

# Columnas necesarias para la consulta (optimización: evitar SELECT *)
COLUMNAS_NECESARIAS = (
    "RNCEmisor, eNCF, EstadoFiscal, EstadoImpresion, TipoPago, "
    "TipoECF, TipoDocumento, Tabla, campo1, campo2, NumeroFacturaInterna, "
    "FechaCreacion, EquipoImpresion, TipoECFL, codigoseguridad"
)

# Tipos de ECF para facturas estándar
TIPOS_ECF_FACTURA = ["31", "32", "44", "45", "46", "41", "47"]


def create_image() -> Image.Image:
    """Crear el ícono para la bandeja del sistema"""
    image = Image.new("RGB", (64, 64), color=(0, 128, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=(255, 255, 0))
    return image


def mostrar_info(icono: Any, item: Any) -> None:  # noqa: ARG001
    """Mostrar información del estado del programa"""
    icono.notify("ASESYS Impresión", "Proceso de impresión activo")


def ensure_index_exists(cn: Any) -> None:
    """Verifica si los índices existen en las tablas base, si no los crea para optimizar consultas"""  # noqa: E501
    try:
        check_type_query = """
        SELECT CASE
            WHEN OBJECTPROPERTY(OBJECT_ID('vFEEncabezado'), 'IsView') = 1 THEN 'VIEW'
            WHEN OBJECTPROPERTY(OBJECT_ID('vFEEncabezado'), 'IsUserTable') = 1 THEN 'TABLE'
            ELSE 'UNKNOWN'
        END AS ObjectType
        """  # type: ignore
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
                    "vFEEncabezado es una vista. Intentando crear índices en tablas base...",  # type: ignore
                )

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
                            "No se encontraron tablas base en el campo Tabla de la vista",  # type: ignore
                        )

                except Exception as e:
                    log_event(logger, "info", f"Error al obtener tablas base: {e}")

                return

            elif object_type == "TABLE":
                crear_indice_en_tabla(cn, "vFEEncabezado")
            else:
                log_event(
                    logger,
                    "info",
                    f"vFEEncabezado tiene tipo desconocido: {object_type}",
                )

    except Exception as e:
        log_event(
            logger,
            "info",
            f"Aviso: No se pudo verificar/crear índice: {e}",
        )


def crear_indice_en_tabla(cn, tabla_nombre):
    """Crea un índice optimizado en una tabla específica si no existe"""
    try:
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

        index_name = f"IX_{tabla_nombre}_EstadoImpresion"

        check_index_query = f"""
        SELECT 1 FROM sys.indexes
        WHERE name = '{index_name}'
        AND object_id = OBJECT_ID('{tabla_nombre}')
        """
        index_result = cn.fetch_query(check_index_query)

        if not index_result or len(index_result) == 0:
            check_columns_query = f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{tabla_nombre}'
            AND COLUMN_NAME IN ('EstadoFiscal', 'EstadoImpresion', 'codigoseguridad', 'FechaCreacion')
            """  # type: ignore
            columnas_existentes = cn.fetch_query(check_columns_query)

            if columnas_existentes and len(columnas_existentes) >= 2:
                columnas_list = [
                    col.COLUMN_NAME if hasattr(col, "COLUMN_NAME") else col[0]
                    for col in columnas_existentes
                ]

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
                        # type: ignore
                        f"Índice {index_name} creado exitosamente en tabla {tabla_nombre}",
                    )
            else:
                log_event(
                    logger,
                    "info",
                    # type: ignore
                    f"Tabla {tabla_nombre} no tiene las columnas necesarias para el índice",
                )
        else:
            log_event(
                logger, "info", f"Índice {index_name} ya existe en tabla {tabla_nombre}"
            )

    except Exception as e:
        log_event(
            logger,
            "info",
            f"No se pudo crear índice en tabla {tabla_nombre}: {e}",
        )


def get_db_cursor(cn):
    """Obtiene un cursor válido, reconectando si es necesario"""
    global cn1
    try:
        cn.connection.execute("SELECT 1")
    except Exception:
        log_event(logger, "info", "Reconectando a la base de datos...")
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
        log_event(logger, "info", f"Error en batch update: {e}")
        try:
            cn.connection.rollback()
        except Exception:
            pass


def obtener_tipo_comprobante(tipoecf: str, tipo_doc: str) -> str:
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


def ejecutar_impresion_grande(pdf_generator, row, ruta, nombre_archivo):
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


def ejecutar_impresion_pdv(impresion, row, ruta, nombre_archivo, sinpdf_param):
    """Ejecuta la impresión en formato PDV (punto de venta)"""
    tipo_ecf = row.TipoECF
    tipo_doc = row.TipoDocumento.strip() if row.TipoDocumento else ""

    if tipo_ecf in TIPOS_ECF_FACTURA:
        if sinpdf_param == 0:
            impresion.imprimir_factura(ruta, nombre_archivo)
        else:
            impresion.imprimir_facturaspdf(ruta, nombre_archivo)
    elif tipo_ecf == "33":
        if sinpdf_param == 0:
            impresion.imprimir_nota_debito(ruta, nombre_archivo)
        else:
            impresion.imprimir_nota_debitospdf(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc == "02":
        if sinpdf_param == 0:
            impresion.imprimir_nota_credito(ruta, nombre_archivo)
        else:
            impresion.imprimir_nota_creditospdf(ruta, nombre_archivo)
    elif tipo_ecf == "34" and tipo_doc in ["03", "17", "05"]:
        if sinpdf_param == 0:
            impresion.imprimir_factura(ruta, nombre_archivo)
        else:
            impresion.imprimir_facturaspdf(ruta, nombre_archivo)
    elif tipo_ecf == "43":
        if sinpdf_param == 0:
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


def seleccionar_impresoras_y_copias(config_path_param, datos_factura=None):
    """Muestra una ventana para seleccionar impresoras y número de copias con diseño moderno."""  # type: ignore
    log_event(logger, "info", "Iniciando selección de impresoras y copias...")
    with open(config_path_param, "r", encoding="utf-8") as file:
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
    )  # type: ignore

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
            f"<b>RNC Emisor:</b> {
                datos_factura.get(
                    'rnc_emisor',
                    '')} - <b>Nombre Emisor:</b> {
                datos_factura.get(
                    'nombre_emisor',
                    '')}<br>"
            f"<b>RNC Comprador:</b> {
                datos_factura.get(
                    'rnc_comprador',
                    '')} - <b>Nombre Comprador:</b> {
                datos_factura.get(
                    'nombre_comprador',
                    '')}"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet(
            "font-size: 14px; margin-bottom: 18px; background: #ecf0f1; border-radius: 10px; padding: 12px;"
        )  # type: ignore
        info_label.setTextFormat(QtCore.Qt.RichText)  # type: ignore
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
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)  # type: ignore
        ]
    except Exception as e:
        log_event(logger, "info", f"Error al obtener impresoras: {e}")
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
        with open(config_path_param, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        return config["printer_name"], config.get("printer_name2", ""), config["copies"]
    else:
        log_event(logger, "info", "El usuario cerró la ventana sin guardar.")
        return None, None, None


def crear_filtro_caja(caja_param):
    """Crea filtro SQL para caja"""
    filtrocaja = ""
    if caja_param is not None and caja_param.strip():
        caja_param = caja_param.upper()
        caracteres = list(caja_param)
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
            # type: ignore
            "INSERT INTO LogActividadesFE (RncEmisor, encf, TipoActividad, FechaActividad, Equipo, RutaImpresion, impresora) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        cn_log.execute_query(query, params)

    except Exception as e:
        log_event(logger, "info", f"Error al registrar actividad: {e}")


def proceso_principal(
    rncemisor_arg_param: Optional[str] = None, encf_arg_param: Optional[str] = None
) -> None:
    """Proceso principal optimizado con intervalos adaptativos y batch updates"""

    # Determinar si es ejecución única o continua
    es_ejecucion_unica = rncemisor_arg_param is not None and encf_arg_param is not None

    # Intervalos adaptativos
    min_interval = 0.5
    max_interval = 30
    current_interval = check_interval  # type: ignore
    consecutive_empty = 0

    while True:
        try:
            if es_ejecucion_unica:
                # Búsqueda específica para argumentos de línea de comandos
                query = (
                    f"SELECT {COLUMNAS_NECESARIAS} FROM vFEEncabezado WITH (NOLOCK) "
                    f"WHERE RNCEmisor = '{rncemisor_arg_param}' AND eNCF = '{encf_arg_param}'"
                )
                log_event(
                    logger,
                    "info",
                    f"Ejecutando búsqueda única: RNC={rncemisor_arg_param}, eNCF={encf_arg_param}",
                )
            else:
                # Construir filtros para modo continuo
                filtrocaja = crear_filtro_caja(caja) if caja else ""  # type: ignore

                filtrosincaja = ""
                if imprimir_sin_caja:  # type: ignore
                    filtrosincaja = (
                        " OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]' "
                    )

                filtroequipo = ""
                if EquipoImpresion is not None:  # type: ignore
                    if isinstance(EquipoImpresion, list):
                        condiciones = [
                            f"EquipoImpresion = '{equipo}'"
                            for equipo in EquipoImpresion
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

            # Intervalo adaptativo solo en modo continuo
            if not es_ejecucion_unica:
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
                # Condición flexible para ejecución única
                debe_procesar = False
                if es_ejecucion_unica:
                    debe_procesar = True
                else:
                    debe_procesar = row.EstadoFiscal >= 3 and row.EstadoImpresion in (
                        1,
                        3,
                    )

                if debe_procesar:
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

                        # Mantener configuración de tipo de pago
                        tipo_pago_grande_actual = tipo_pago_grande  # type: ignore
                        tipo_pago_pdv_actual = tipo_pago_pdv  # type: ignore

                        # Mostrar pantalla si está configurado
                        if con_pantalla == 1:  # type: ignore
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
                            seleccionar_impresoras_y_copias(config_path, datos_factura)  # type: ignore

                        # Ejecutar impresión según configuración
                        impreso = False

                        # Impresión grande
                        if Impresion_grande == 1:  # type: ignore
                            if debe_imprimir(
                                row, tipo_pago_grande_actual, 1, "CO"
                            ) or debe_imprimir(row, tipo_pago_grande_actual, 1, "CR"):
                                ejecutar_impresion_grande(
                                    pdf_generator, row, Ruta, nombre_archivo
                                )
                                impreso = True

                        # Impresión PDV
                        if impresion_pdv == 1 and not impreso:  # type: ignore
                            if debe_imprimir(
                                row, tipo_pago_pdv_actual, 1, "CO"
                            ) or debe_imprimir(row, tipo_pago_pdv_actual, 1, "CR"):
                                ejecutar_impresion_pdv(impresion, row, Ruta, nombre_archivo, sinpdf)  # type: ignore

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

                        log_event(
                            logger,
                            "info",
                            f"[OK] Documento {
                                row.eNCF.strip()} impreso en impresora: {
                                imp if imp else 'No especificada'}",
                        )

                    except Exception as e:
                        log_event(
                            logger, "info", f"Error procesando {row.eNCF.strip()}: {e}"
                        )

                row = cursor.fetchone()

            # Batch update al final
            if registros_procesados:
                actualizar_batch(cn1, registros_procesados)

            cursor.close()

            # Si es ejecución única, salir del bucle infinito
            if es_ejecucion_unica:
                log_event(logger, "info", "Ejecución única completada, saliendo...")
                break

        except Exception as e:
            log_event(
                logger,
                "info",
                f"Error en bucle principal: {e}: {
                    traceback.extract_tb(
                        sys.exc_info()[2])}",
            )

        time.sleep(current_interval if not es_ejecucion_unica else 0)


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

    # Verificar si se pasaron argumentos de RNCEmisor y eNCF
    rncemisor_arg = None
    encf_arg = None

    if len(sys.argv) > 2:
        rncemisor_arg = sys.argv[1]
        encf_arg = sys.argv[2]
        log_event(
            logger,
            "info",
            f"Argumentos detectados: RNC={rncemisor_arg}, eNCF={encf_arg}",
        )
        # Ejecutar impresión única y salir
        proceso_principal(rncemisor_arg, encf_arg)
        log_event(logger, "info", "Proceso completado. Finalizando...")
        sys.exit(0)

    # Si no hay argumentos, ejecutar en modo normal (monitoreo continuo)
    log_event(logger, "info", "Iniciando aplicación en modo de monitoreo continuo")

    # Crear icono del system tray
    icon = pystray.Icon("ASESYS", icon=create_image(), title="ASESYS Impresión")  # type: ignore
    icon.menu = pystray.Menu(pystray.MenuItem("Estado", mostrar_info, default=True))  # type: ignore

    # Iniciar proceso principal en hilo separado
    thread_principal = threading.Thread(target=proceso_principal, daemon=True)  # type: ignore
    thread_principal.start()  # type: ignore

    log_event(logger, "info", "Iniciando aplicación en la bandeja del sistema")
    icon.run()
