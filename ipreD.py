import traceback
import os
import sys
import threading
import time

import pyodbc
import pystray
import requests
import win32print  # Asegúrate de que este módulo esté importado
from PIL import Image, ImageDraw
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap  # <--- Corrección aquí
from PyQt5.QtWidgets import QSpinBox  # Añadido para selección dinámica de copias
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.CDT import ensure_table
from db.database import *
from db.database import fetch_invoice_data
from db.uDB import *
from glib.ufe import *
from glib.ufe import GConfig
from logG import log_event, setup_logger

# from glib.ufe import GConfig
from print.impresion import *
from print.pdf_generator import PDFGenerator

logger = setup_logger("FEImpresionASESYS.log")

PConfig = load_printer_config()


def create_image():
    """Crear el ícono para la bandeja del sistema"""
    image = Image.new("RGB", (64, 64), color=(0, 128, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=(255, 255, 0))
    return image


def mostrar_info(icon, item):
    """Mostrar información del estado del programa"""
    icon.notify("ASESYS Impresión", "Proceso de impresión activo")


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
        QtCore.Qt.Window
        | QtCore.Qt.WindowTitleHint
        | QtCore.Qt.CustomizeWindowHint
        | QtCore.Qt.WindowStaysOnTopHint
    )

    # Estilo moderno
    dialog.setStyleSheet(
        """
        QDialog {
            background-color: #f7f7f7;
            border-radius: 15px;
        }
        QLabel {
            color: #333;
            font-size: 16px;
        }
        QComboBox, QSpinBox {
            font-size: 15px;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #ccc;
            background-color: white;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            font-size: 16px;
            padding: 12px 25px;
            border-radius: 10px;
            border: none;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QFrame#line {
            background-color: #ddd;
            height: 1px;
            margin: 10px 0;
        }
    """
    )

    layout = QVBoxLayout()
    layout.setContentsMargins(30, 30, 30, 30)

    # Título con icono
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

    # Línea separadora
    line = QFrame()
    line.setObjectName("line")
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    layout.addWidget(line)

    # Datos de factura/comprobante
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
        info_label.setTextFormat(QtCore.Qt.RichText)
        layout.addWidget(info_label)

        # Línea separadora
        line2 = QFrame()
        line2.setObjectName("line")
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

    # Impresora principal
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
        log_event(
            logger,
            "info",
            f"Error al obtener la lista de impresoras: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
        )
        impresoras_disponibles = []
    combo_impresora1.addItems(impresoras_disponibles)
    combo_impresora1.setCurrentText(config.get("printer_name", ""))
    layout.addWidget(label_impresora1)
    layout.addWidget(combo_impresora1)

    # Número de copias dinámico
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

    # Espaciador
    layout.addStretch()

    # Botones
    button_layout = QHBoxLayout()
    btn_guardar = QPushButton("Aceptar")
    btn_guardar.clicked.connect(dialog.accept)
    btn_cancelar = QPushButton("Cancelar")
    btn_cancelar.clicked.connect(dialog.reject)
    button_layout.addWidget(btn_cancelar)
    button_layout.addWidget(btn_guardar)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    # Centrar la ventana en la pantalla
    screen_geometry = app.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    log_event(logger, "info", "Mostrando diálogo de selección de impresoras...")
    dialog.exec_()

    # Actualizar configuración si se guardó
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
    """
    Función que recibe un string, lo convierte a mayúsculas,
    lo divide en caracteres individuales y crea una condición
    de filtro para cada carácter.
    """
    filtrocaja = ""
    if caja is not None:
        caja = caja.upper()
        # Dividir el string en caracteres individuales
        caracteres = list(caja)

        # Crear filtro para cada carácter
        condiciones = []
        for caracter in caracteres:
            condicion = f"SUBSTRING(NumeroFacturaInterna, 1, 1)='{caracter}'"
            condiciones.append(condicion)

        # Unir todas las condiciones con OR
        if condiciones:
            filtrocaja = " AND (" + " OR ".join(condiciones) + ")"

    return filtrocaja

    # Evitar que el programa se ejecute mas de una vez
    ################################################################################################
    lock_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "FEImpresionASESYS.lock"
    )

    # Abrir el archivo para bloqueo
    lock_file = open(lock_file_path, "w")
    try:
        # Intentar bloquear el archivo de forma exclusiva y no bloqueante
        portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)

        # Si llegamos aquí, tenemos el bloqueo

        # Escribir el PID para identificación
        lock_file.write(f"{os.getpid()}")
        lock_file.flush()
    except portalocker.LockException:
        print("¡Ya hay otra instancia del programa en ejecución!")
        sys.exit(1)
    ################################################################################################


def registrar_actividad_log(
    rnc_emisor, encf, tipo_actividad, fecha_actividad, equipo, ruta_impresion, impresora
):
    """
    Inserta un registro en la tabla LogActividadesFE.
    """
    try:
        from datetime import datetime  # Aseguramos la importación

        cn1 = ConectarDB()

        # Protección: si es None, usar ahora
        if fecha_actividad is None:
            fecha_actividad = datetime.now()

        # Si es datetime, convertir a string
        if isinstance(fecha_actividad, datetime):
            fecha_actividad_str = fecha_actividad.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Asegurar que sea string y no None
            fecha_actividad_str = (
                str(fecha_actividad)
                if fecha_actividad is not None
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Usar parámetros nombrados (que es lo que funciona)
        named_params = {
            "rnc_emisor": str(rnc_emisor) if rnc_emisor is not None else "",
            "encf": str(encf) if encf is not None else "",
            "tipo_actividad": str(tipo_actividad) if tipo_actividad is not None else "",
            "fecha_actividad": fecha_actividad_str,
            "equipo": str(equipo) if equipo is not None else "",
            "ruta_impresion": str(ruta_impresion) if ruta_impresion is not None else "",
            "impresora": str(impresora) if impresora is not None else "",
        }

        # Query con parámetros nombrados
        named_query = (
            "INSERT INTO LogActividadesFE (RncEmisor, encf, TipoActividad, FechaActividad, Equipo, RutaImpresion, impresora) "
            "VALUES (:rnc_emisor, :encf, :tipo_actividad, :fecha_actividad, :equipo, :ruta_impresion, :impresora)"
        )

        cn1.execute_query(named_query, named_params)
        print("Actividad registrada en LogActividadesFE.")

    except Exception as e:
        print(
            f"Error al registrar actividad en LogActividadesFE: {e}:{ traceback.extract_tb(sys.exc_info()[2])}"
        )
        print(
            f"Parámetros: rnc_emisor={rnc_emisor}, encf={encf}, tipo_actividad={tipo_actividad}, "
            f"fecha_actividad={fecha_actividad}, equipo={equipo}, ruta_impresion={ruta_impresion}, impresora={impresora}"
        )


def proceso_principal():
    # Variables globales necesarias
    global caja, imprimir_sin_caja, Impresion_grande, impresion_pdv, sinpdf, EquipoImpresion
    global tipo_pago_grande, tipo_pago_pdv, con_pantalla, config_path, check_interval
    global cn1, logger

    while True:
        try:
            filtrocaja = ""
            if caja is not None:
                # caja = caja.upper() #filtrocaja = f" AND SUBSTRING(NumeroFacturaInterna, 1, 1)='{caja}' "
                filtrocaja = crear_filtro_caja(caja)
            filtrosincaja = ""
            if imprimir_sin_caja:
                filtrosincaja = (
                    " OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]' "
                )
            filtroequipo = ""
            if EquipoImpresion is not None:
                if isinstance(EquipoImpresion, list):
                    # Si es una lista, crear condiciones OR para cada valor
                    condiciones = [
                        f"EquipoImpresion = '{equipo}'" for equipo in EquipoImpresion
                    ]
                    filtroequipo = " AND (" + " OR ".join(condiciones) + ")"
                else:
                    # Si es un solo valor, mantener el comportamiento actual
                    filtroequipo = f" AND EquipoImpresion = '{EquipoImpresion}'"
            # Obtener estados de impresión desde la configuración
            estados_impresion = PConfig.get("estadosimpresion", [3, 5, 6])
            estados_impresion_str = ",".join(str(e) for e in estados_impresion)
            query = (
                "SELECT top 5 FROM vFEEncabezado WITH (NOLOCK) "
                f"WHERE EstadoFiscal in ({estados_impresion_str}) AND codigoseguridad is not null AND EstadoImpresion in(1,3)"
                + filtrocaja
                + filtrosincaja
                + filtroequipo
                + "AND TipoECFL = 'E'"
                + " ORDER BY FechaCreacion"
            )
            # log_event(logger, "info", query)

            cursor = cn1.connection.cursor()

            # Evitar quedarnos esperando bloqueos largos
            cursor.execute("SET LOCK_TIMEOUT 3000;")  # 3 segundos
            cursor.execute(query)

            row = cursor.fetchone()
            # vFEEncabezado = cn1.fetch_query(query)

            # for row in vFEEncabezado:
            while row:
                if row.EstadoFiscal >= 3 and (
                    row.EstadoImpresion == 1 or row.EstadoImpresion == 3
                ):
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
                        Ruta = PConfig.get("ruta_ri", "C:\\XMLValidar\\RI\\")
                        extension = ".pdf"

                        # Crear nombre completo del archivo
                        nombre_archivo = os.path.join(Ruta, f"{NombrePDF}{extension}")

                        # Si existe, crear un nombre único
                        contador = 1
                        while os.path.exists(nombre_archivo):
                            nombre_archivo = os.path.join(
                                Ruta, f"{NombrePDF}_{contador}{extension}"
                            )
                            contador += 1

                        if con_pantalla == 1:
                            log_event(
                                logger,
                                "info",
                                "Mostrando pantalla de selección de impresoras...",
                            )
                            # --- NUEVO: Preparar datos solo para mostrar ---
                            datos_factura = {
                                "numero_factura": invoice_data.get("numero", ""),
                                "comprobante": invoice_data.get("ncf", ""),
                                "tipo_comprobante": "",  # Se calcula abajo
                                "rnc_emisor": company_data.get("rnc", ""),
                                "nombre_emisor": company_data.get("nombre_empresa", ""),
                                "rnc_comprador": invoice_data.get("cedula", ""),
                                "nombre_comprador": invoice_data.get(
                                    "nombre_cliente", ""
                                ),
                            }
                            tipoecf = invoice_data.get("tipoecf", "")
                            tipo_doc = invoice_data.get("tipo", "").strip()
                            if tipoecf == "34" and tipo_doc == "02":
                                datos_factura["tipo_comprobante"] = "Nota de Crédito"
                            elif tipoecf == "33":
                                datos_factura["tipo_comprobante"] = "Nota de Débito"
                            elif tipoecf in ["31", "32", "44", "45", "46", "41", "47"]:
                                datos_factura["tipo_comprobante"] = "Factura"
                            elif tipoecf == "43":
                                datos_factura["tipo_comprobante"] = "Caja Chica"
                            else:
                                datos_factura["tipo_comprobante"] = tipoecf

                            # Solo mostrar, no guardar en config
                            printer_name, printer_name2, copies = (
                                seleccionar_impresoras_y_copias(
                                    config_path, datos_factura
                                )
                            )
                            log_event(
                                logger,
                                "info",
                                f"Impresora principal: {printer_name}, Impresora secundaria: {printer_name2}, Copias: {copies}",
                            )

                        if tipo_pago_grande == "CO" and Impresion_grande == 1:

                            if row.TipoPago == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_grande == "CR" and Impresion_grande == 1:

                            if row.TipoPago == 2 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 2 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 2 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CO" and impresion_pdv == 1:

                            if row.TipoPago == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Nota de débito
                            if row.TipoPago == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Otros tipos de documentos
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Caja chica
                            elif (
                                row.TipoPago == 1
                                and impresion_pdv == 1
                                and row.TipoECF == "43"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CR" and impresion_pdv == 1:

                            if row.TipoPago == 2 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Nota de débito
                            if row.TipoPago == 2 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Otros tipos de documentos
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Caja chica
                            elif (
                                row.TipoPago == 2
                                and impresion_pdv == 1
                                and row.TipoECF == "43"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CRCO" or tipo_pago_grande == "CRCO":
                            # Generar el PDF según el tipo de documento
                            if Impresion_grande == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                            elif impresion_pdv == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                            # Nota de débito
                            elif Impresion_grande == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                Impresion_grande == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                            elif (
                                impresion_pdv == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                Impresion_grande == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                            elif (
                                impresion_pdv == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                            # Caja chica
                            elif Impresion_grande == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        query = (
                            f"UPDATE {row.Tabla.strip()} "
                            f"SET EstadoImpresion = 2 "
                            f"WHERE {row.campo1.strip()} = '{row.RNCEmisor.strip()}' "
                            f"AND {row.campo2.strip()} = '{row.eNCF.strip()}'"
                        )
                        cn1.execute_query(query)
                        imp = ""
                        if Impresion_grande == 1:
                            imp = PConfig.get("printer_name", "")
                        elif impresion_pdv == 1:
                            imp = PConfig.get("printer_name2", "")

                        registrar_actividad_log(
                            row.RNCEmisor.strip() if row.RNCEmisor else "",
                            row.eNCF.strip() if row.eNCF else "",
                            "Impresión",
                            datetime.now(),
                            EquipoImpresion or "",
                            Ruta or "",
                            imp or "",
                        )

                    except Exception as e:
                        log_event(
                            logger,
                            "info",
                            f"Error procesando documento {row.eNCF.strip()}: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
                        )
                row = cursor.fetchone()

            cursor.close()

        except Exception as e:
            log_event(
                logger,
                "info",
                f"Error en el bucle principal: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
            )
        time.sleep(check_interval)


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
        if not self.thread.is_alive():
            self.thread.start()

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


def proceso_principal_controlado(signals):
    global pausado, detener, check_interval
    while not detener:
        if pausado:
            time.sleep(1)
            continue
        try:
            filtrocaja = ""
            if caja is not None:
                # caja = caja.upper() #                filtrocaja = f" AND SUBSTRING(NumeroFacturaInterna, 1, 1)='{caja}' "
                filtrocaja = crear_filtro_caja(caja)
            filtrosincaja = ""
            if imprimir_sin_caja:
                filtrosincaja = (
                    " OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]' "
                )
            filtroequipo = ""
            if EquipoImpresion is not None:
                EquipoImpresion = EquipoImpresion.upper()
                filtroequipo = f" AND EquipoImpresion= '{EquipoImpresion}'  "
            query = (
                "SELECT * FROM vFEEncabezado "
                "WHERE EstadoFiscal >= 3 AND EstadoFiscal < 90 AND EstadoImpresion in(1,3) "
                + filtrocaja
                + filtrosincaja
                + filtroequipo
                + " ORDER BY FechaCreacion"
            )
            # log_event(logger, "info", query)
            vFEEncabezado = cn1.fetch_query(query)

            for row in vFEEncabezado:
                if row.EstadoFiscal >= 3 and (
                    row.EstadoImpresion == 1 or row.EstadoImpresion == 3
                ):
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
                            company_data, invoice_data, products, forms
                        )

                        NombrePDF = f"{row.RNCEmisor.strip()}{row.eNCF.strip()}"
                        Ruta = "C:\\XMLValidar\\RI\\"
                        extension = ".pdf"

                        # Crear nombre completo del archivo
                        nombre_archivo = os.path.join(Ruta, f"{NombrePDF}{extension}")

                        # Si existe, crear un nombre único
                        contador = 1
                        while os.path.exists(nombre_archivo):
                            nombre_archivo = os.path.join(
                                Ruta, f"{NombrePDF}_{contador}{extension}"
                            )
                            contador += 1

                        if con_pantalla == 1:
                            log_event(
                                logger,
                                "info",
                                "Mostrando pantalla de selección de impresoras...",
                            )
                            # --- NUEVO: Preparar datos solo para mostrar ---
                            datos_factura = {
                                "numero_factura": invoice_data.get("numero", ""),
                                "comprobante": invoice_data.get("ncf", ""),
                                "tipo_comprobante": "",  # Se calcula abajo
                                "rnc_emisor": company_data.get("rnc", ""),
                                "nombre_emisor": company_data.get("nombre_empresa", ""),
                                "rnc_comprador": invoice_data.get("cedula", ""),
                                "nombre_comprador": invoice_data.get(
                                    "nombre_cliente", ""
                                ),
                            }
                            tipoecf = invoice_data.get("tipoecf", "")
                            tipo_doc = invoice_data.get("tipo", "").strip()
                            if tipoecf == "34" and tipo_doc == "02":
                                datos_factura["tipo_comprobante"] = "Nota de Crédito"
                            elif tipoecf == "33":
                                datos_factura["tipo_comprobante"] = "Nota de Débito"
                            elif tipoecf in ["31", "32", "44", "45", "46", "41", "47"]:
                                datos_factura["tipo_comprobante"] = "Factura"
                            elif tipoecf == "43":
                                datos_factura["tipo_comprobante"] = "Caja Chica"
                            else:
                                datos_factura["tipo_comprobante"] = tipoecf

                            # Solo mostrar, no guardar en config
                            printer_name, printer_name2, copies = (
                                seleccionar_impresoras_y_copias(
                                    config_path, datos_factura
                                )
                            )
                            log_event(
                                logger,
                                "info",
                                f"Impresora principal: {printer_name}, Impresora secundaria: {printer_name2}, Copias: {copies}",
                            )

                        if tipo_pago_grande == "CO" and Impresion_grande == 1:

                            if row.TipoPago == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_grande == "CR" and Impresion_grande == 1:

                            if row.TipoPago == 2 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 2 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 2 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CO" and impresion_pdv == 1:

                            if row.TipoPago == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Nota de débito
                            if row.TipoPago == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Otros tipos de documentos
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Caja chica
                            elif (
                                row.TipoPago == 1
                                and impresion_pdv == 1
                                and row.TipoECF == "43"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CR" and impresion_pdv == 1:

                            if row.TipoPago == 2 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Nota de débito
                            if row.TipoPago == 2 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Otros tipos de documentos
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                    # Caja chica
                            elif (
                                row.TipoPago == 2
                                and impresion_pdv == 1
                                and row.TipoECF == "43"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        if tipo_pago_pdv == "CRCO" or tipo_pago_grande == "CRCO":
                            # Generar el PDF según el tipo de documento
                            if Impresion_grande == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                            elif impresion_pdv == 1 and row.TipoECF in [
                                "31",
                                "32",
                                "44",
                                "45",
                                "46",
                                "41",
                                "47",
                            ]:
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                            # Nota de débito
                            elif Impresion_grande == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                Impresion_grande == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                            elif (
                                impresion_pdv == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_creditospdf(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                Impresion_grande == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                            elif (
                                impresion_pdv == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_factura(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                            # Caja chica
                            elif Impresion_grande == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        query = (
                            f"UPDATE {row.Tabla.strip()} "
                            f"SET EstadoImpresion = 2 "
                            f"WHERE {row.campo1.strip()} = '{row.RNCEmisor.strip()}' "
                            f"AND {row.campo2.strip()} = '{row.eNCF.strip()}'"
                        )
                        cn1.execute_query(query)

                    except Exception as e:
                        log_event(
                            logger,
                            "info",
                            f"Error procesando documento {row.eNCF.strip()}: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
                        )

            # Pequeña pausa opcional para no saturar
            # time.sleep(5)

        except Exception as e:
            log_event(
                logger,
                "info",
                f"Error en el bucle principal: {e}:{ traceback.extract_tb(sys.exc_info()[2])}",
            )
        time.sleep(check_interval)


# Ensure GConfig has a method named cargar
# If not, define it in the appropriate module

if __name__ == "__main__":
    UnlockCK()
    # Check if GConfig.cargar exists and is correctly implemented
    try:
        GConfig.cargar(1)  # Cargar la configuración de impresoras con GConfig.cargar(1)
        log_event(logger, "info", "Configuracion Cargada")
    except AttributeError as e:
        log_event(logger, "info", f"Error: {e}")
        # Handle the error or define the method if missing

    # Conexión a la base de datos J
    cn1 = ConectarDB()
    mostrarConfiguracion(GConfig, cn1)
    # Asegurar la tabla de log de actividades
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

    # Crear y configurar el icono del system tray
    icon = pystray.Icon("ASESYS", icon=create_image(), title="ASESYS Impresión")

    # Configurar menú simple
    icon.menu = pystray.Menu(pystray.MenuItem("Estado", mostrar_info, default=True))

    # Iniciar el proceso principal en un hilo separado
    thread_principal = threading.Thread(target=proceso_principal, daemon=True)
    thread_principal.start()

    # Ejecutar el icono en la bandeja del sistema
    log_event(logger, "info", "Iniciando aplicación en la bandeja del sistema")
    icon.run()

    signals = ControlSignals()

    def on_pause():
        global pausado
        pausado = True

    def on_resume():
        global pausado
        pausado = False

    def on_stop():
        global detener
        detener = True

    def on_restart():
        global pausado, detener
        pausado = False
        detener = False

    signals.pause.connect(on_pause)
    signals.resume.connect(on_resume)
    signals.stop.connect(on_stop)
    signals.restart.connect(on_restart)

    thread_principal = threading.Thread(
        target=proceso_principal_controlado, args=(signals,), daemon=True
    )

    app = QtWidgets.QApplication(sys.argv)
    control_dialog = ControlDialog(thread_principal, signals)
    control_dialog.show()
    sys.exit(app.exec_())
    pausado = True

    def on_resume():
        global pausado
        pausado = False

    def on_stop():
        global detener
        detener = True

    def on_restart():
        global pausado, detener
        pausado = False
        detener = False

    signals.pause.connect(on_pause)
    signals.resume.connect(on_resume)
    signals.stop.connect(on_stop)
    signals.restart.connect(on_restart)

    thread_principal = threading.Thread(
        target=proceso_principal_controlado, args=(signals,), daemon=True
    )

    app = QtWidgets.QApplication(sys.argv)
    control_dialog = ControlDialog(thread_principal, signals)
    control_dialog.show()
    sys.exit(app.exec_())
    sys.exit(app.exec_())
    pausado = True

    def on_resume():
        global pausado
        pausado = False

    def on_stop():
        global detener
        detener = True

    def on_restart():
        global pausado, detener
        pausado = False
        detener = False

    signals.pause.connect(on_pause)
    signals.resume.connect(on_resume)
    signals.stop.connect(on_stop)
    signals.restart.connect(on_restart)

    thread_principal = threading.Thread(
        target=proceso_principal_controlado, args=(signals,), daemon=True
    )

    app = QtWidgets.QApplication(sys.argv)
    control_dialog = ControlDialog(thread_principal, signals)
    control_dialog.show()
    sys.exit(app.exec_())
    app = QtWidgets.QApplication(sys.argv)
    control_dialog = ControlDialog(thread_principal, signals)
    control_dialog.show()
    sys.exit(app.exec_())
